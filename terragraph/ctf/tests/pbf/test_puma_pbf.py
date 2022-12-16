#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import json
import logging
import os
from argparse import Namespace
from time import sleep
from typing import Any, Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestPBF(TestX86TGIgn):
    TEST_NAME = "Periodic Beam Forming test for P2P link"
    DESCRIPTION = (
        "Igniting network using external E2E controller and "
        + "running end to end traffic in parallel to the PBF scan"
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

    def api_start_scan(self, data: Dict[str, Any]):
        data["startTime"] = int(datetime.datetime.now().timestamp() + 10)
        api_result = self.api_service_request("startScan", data=data)
        self.log_to_ctf(str(api_result))

    def api_status_scan(
        self,
        controller_node_id: int,
    ):
        api_status = self.api_service_request(
            "getScanStatus",
        )
        api_status_json_encoded = json.dumps(api_status)
        with open("/tmp/api_status.json", "w") as file:
            file.write(api_status_json_encoded)

        status_tg_scan_to_file: str = "mkdir -p /tmp/e2e_custom_logs; touch /tmp/e2e_custom_logs/scan_logs_full.json"
        futures: Dict = self.run_cmd(status_tg_scan_to_file, [controller_node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {status_tg_scan_to_file} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{status_tg_scan_to_file} in Controller {result['node_id']}:\n{result['message']}"
            )

        device = self.device_info[controller_node_id]
        if not self.push_file(
            device.connection,
            "/tmp/api_status.json",
            "/tmp/e2e_custom_logs/scan_logs_full.json",
            recursive=False,
        ):
            error_msg = f"Failed to push api_status.json file to {controller_node_id}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

    def run_python_script(
        self,
        controller_node_id: int,
    ):
        script_result: str = f"python3 {self.test_data['file_paths']['target_path']}/{self.test_data['file_paths']['script_file_name']} /tmp/e2e_custom_logs/scan_logs_full.json --rf"
        futures: Dict = self.run_cmd(script_result, [controller_node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {script_result} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{script_result} in Controller {result['node_id']}:\n{result['message']}"
            )
            if "PASS" not in result["message"]:
                raise TestFailed("PASS not found in the result")
            if "FAIL" in result["message"]:
                raise TestFailed("FAIL found in the result")

    def copy_script_to_controller(
        self, input_file_name: str, remote_file_path: str, controller_node_id: int
    ):
        current_dir_path = "./"
        scan_verify_file_path = os.path.join(current_dir_path, input_file_name)
        if os.path.isfile(scan_verify_file_path):
            device = self.device_info[controller_node_id]
            if not self.push_file(
                device.connection,
                scan_verify_file_path,
                remote_file_path,
                recursive=False,
            ):
                error_msg = f"Failed to push script to {controller_node_id}: {scan_verify_file_path}"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
        else:
            raise TestFailed(f"file {input_file_name} doesn't exist")

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        e2e_ctrl_node_id = self.find_x86_tg_host_id()
        traffic_profile = self.test_data["traffic_profile"]
        for stream in traffic_profile:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "continue_on_failure": True,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                }
            )
        steps.append(
            {
                "name": "Run Traffic",
                "function": self.run_traffic,
                "function_args": (traffic_profile,),
                "success_msg": "iperf ran successfully",
                "continue_on_failure": True,
                "concurrent": True,
            }
        )
        for idx, scan_profile in enumerate(self.test_data["scan_profiles"]):
            steps.append(
                {
                    "name": "TG Scan",
                    "function": self.api_start_scan,
                    "function_args": (scan_profile,),
                    "success_msg": "Scan complete",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 30 * idx + 30,
                }
            )
        steps.extend(
            [
                {
                    "name": "Recheck that the network is entirely up",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        self.test_args["ignition_timeout_s"],
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
                {
                    "name": "Wait 30 seconds",
                    "function": sleep,
                    "function_args": (30,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "TG Scan Status",
                    "function": self.api_status_scan,
                    "function_args": (e2e_ctrl_node_id,),
                    "success_msg": "Scan Status",
                    "continue_on_failure": True,
                },
                {
                    "name": "Copy script to controller",
                    "function": self.copy_script_to_controller,
                    "function_args": (
                        self.test_data["file_paths"]["script_file_name"],
                        self.test_data["file_paths"]["target_path"],
                        e2e_ctrl_node_id,
                    ),
                    "success_msg": "Successfully copied the script to the controller",
                    "continue_on_failure": True,
                },
                {
                    "name": "Running Python script on Scan result",
                    "function": self.run_python_script,
                    "function_args": (e2e_ctrl_node_id,),
                    "success_msg": "Successfully ran the python script on scan results",
                    "continue_on_failure": True,
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
