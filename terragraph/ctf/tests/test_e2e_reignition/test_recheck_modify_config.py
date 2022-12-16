#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from argparse import Namespace
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestX86TGIgnModifyConfig(TestX86TGIgn):
    TEST_NAME = "E2E Ignition Recheck"
    DESCRIPTION = "Verify e2e network is still up after modifying node(s) config"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    def is_gps_enabled_in_all_nodes(
        self, skip_node_ids: Optional[List[int]] = None
    ) -> bool:
        for node_id in self.get_tg_devices():
            if skip_node_ids and (node_id in skip_node_ids):
                continue
            gpsVal = (
                self.nodes_data[node_id]["node_config"]
                .get("radioParamsBase", {})
                .get("fwParams", {})
                .get("forceGpsDisable", 0)
            )
            if "node_config" in self.nodes_data[node_id] and not gpsVal:
                continue
            else:
                return False
        return True

    def get_fw_params_verify_gps_state(
        self, node_ids: Optional[List[int]] = None, gps_disable: Optional[bool] = None
    ) -> None:
        futures: Dict = self.run_cmd(
            "/usr/sbin/tg2 minion fw_get_params -t node", node_ids
        )
        for result in self.wait_for_cmds(futures):
            try:
                if not result["success"]:
                    error_msg = (
                        f"Node {result['node_id']}: failed to get fw params: "
                        + f"{result['error']}"
                    )
                    raise DeviceCmdError(error_msg)
                else:
                    self.log_to_ctf(
                        f"fw_get_params in Node {result['node_id']}:\n{result['message']}"
                    )
                    if gps_disable:
                        run_time_fw_params = json.loads(result["message"])
                        gps_state = run_time_fw_params["optParams"]["forceGpsDisable"]
                        if gps_state != gps_disable:
                            raise TestFailed(
                                "Run time GPS state in FW didn't match with expected state"
                            )
            except DeviceCmdError as e:
                self.log_to_ctf(f"Exception DeviceCmdError:{e}", "error")

        return

    def steps_modify_node_overrides_verify_network_up(
        self,
        config_description: str,
        overrides: Dict,
        ignition_timeout_s: Optional[int] = 300,
        is_cont_on_fail: Optional[bool] = False,
        delay_recheck_network_up_s: Optional[int] = 0,
    ) -> List[Dict]:
        # start with empty list
        steps = []
        steps.extend(
            [
                {
                    "name": f"e2e rest API to Modify Node Overrides {config_description}",
                    "function": self.api_service_request,
                    "function_args": (
                        "modifyNodeOverridesConfig",
                        overrides,
                    ),
                    "success_msg": f"Called e2e rest API to Modify Node Overrides {config_description}",
                    "continue_on_failure": is_cont_on_fail,
                },
                {
                    "name": f"ReCheck that the network is entirely up after {delay_recheck_network_up_s} secs",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": is_cont_on_fail,
                    "delay": delay_recheck_network_up_s,
                },
            ]
        )
        if "change gps" in config_description:
            steps.append(
                {
                    "name": "Get FW params in the Node(s) and verify gps state",
                    "function": self.get_fw_params_verify_gps_state,
                    "function_args": (
                        None,
                        (config_description == "change gps to disable"),
                    ),
                    "success_msg": "Sent commnad to get FW params in the Node(s) and verify gps state",
                    "continue_on_failure": is_cont_on_fail,
                }
            )
        return steps

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        configs = self.test_options["configs"]
        config_gps_disable = self.test_options["config_gps_disable"]
        config_gps_enable = self.test_options["config_gps_enable"]
        for config in configs:
            steps.extend(
                self.steps_modify_node_overrides_verify_network_up(
                    config_description=config["description"],
                    overrides=self.create_node_overrides(config),
                    ignition_timeout_s=config["timeout_network_up_s"],
                    is_cont_on_fail=True,
                )
            )
        if self.is_gps_enabled_in_all_nodes():
            steps.extend(
                self.steps_modify_node_overrides_verify_network_up(
                    config_description=config_gps_disable["description"],
                    overrides=self.create_node_overrides(config_gps_disable),
                    ignition_timeout_s=config_gps_disable["timeout_network_up_s"],
                    is_cont_on_fail=False,
                    delay_recheck_network_up_s=180,
                )
                + self.steps_modify_node_overrides_verify_network_up(
                    config_description=config_gps_enable["description"],
                    overrides=self.create_node_overrides(config_gps_enable),
                    ignition_timeout_s=config_gps_enable["timeout_network_up_s"],
                    is_cont_on_fail=False,
                    delay_recheck_network_up_s=180,
                )
            )
        else:
            steps.extend(
                self.steps_modify_node_overrides_verify_network_up(
                    config_description=config_gps_enable["description"],
                    overrides=self.create_node_overrides(config_gps_enable),
                    ignition_timeout_s=config_gps_enable["timeout_network_up_s"],
                    is_cont_on_fail=False,
                    delay_recheck_network_up_s=180,
                )
                + self.steps_modify_node_overrides_verify_network_up(
                    config_description=config_gps_disable["description"],
                    overrides=self.create_node_overrides(config_gps_disable),
                    ignition_timeout_s=config_gps_disable["timeout_network_up_s"],
                    is_cont_on_fail=False,
                    delay_recheck_network_up_s=180,
                )
            )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
