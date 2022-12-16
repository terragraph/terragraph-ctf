#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Test class to support OEM IOT testing.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest


LOG = logging.getLogger(__name__)

# Default node config file path
NODE_CONFIG_FILE = "/data/cfg/node_config.json"


class TestNodeIot(TestX86TGIgn, x86TrafficGenCtfTest):
    LOG_FILES = ["/var/log/e2e_minion/current", "/var/log/openr/current"]

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(TestNodeIot, TestNodeIot).test_params()
        # disable fw_logs, sysdump and fw_stats collection by default
        # only enabled while running test case in test-args if OEM device supports these
        TestNodeIot.merge_dict(test_params, TestX86TGIgn.test_params())
        TestNodeIot.merge_dict(test_params, x86TrafficGenCtfTest.test_params())
        test_params["save_sysdump"]["default"] = False
        test_params["enable_fw_logs"]["default"] = False
        test_params["enable_fw_stats"]["default"] = False
        test_params["test_data"]["required"] = False
        test_params["test_data"]["default"] = None
        test_params["allow_mixed_versions"]["default"] = True
        return test_params

    def generate_base_node_config(self, path: str = NODE_CONFIG_FILE) -> None:
        """
        Write the (layered) base configuration to a given path for both puma
        and Accton CN nodes.
        """

        puma_node_ids = []
        accton_cn_node_ids = []
        for node_id in self.get_tg_devices():
            info = self.device_info[node_id]
            self.log_to_ctf(info.metadata)
            if info.metadata["device_sub_type"] == "accton cn":
                accton_cn_node_ids.append(node_id)
            else:
                puma_node_ids.append(node_id)

        self.log_to_ctf(f"Writing base node configs to: {path}", "info")

        # copying base config to right location for accton CN nodes
        if accton_cn_node_ids:
            futures: Dict = self.run_cmd(
                f"cp /rom/data/cfg/node_config.json {path}", accton_cn_node_ids
            )

            for result in self.wait_for_cmds(futures):
                if result["success"]:
                    self.log_to_ctf(
                        f"Accton CN Node {result['node_id']} base node config was generated"
                    )
                else:
                    raise DeviceCmdError(
                        f"Accton CN Node {result['node_id']} failed to generate base node config"
                    )

        # generating base config for puma/accton DN nodes
        futures: Dict = self.run_cmd(f"/usr/sbin/config_get_base {path}", puma_node_ids)
        for result in self.wait_for_cmds(futures):
            if result["success"]:
                LOG.debug(
                    f"Puma node {result['node_id']} base node config was generated"
                )
            else:
                raise DeviceCmdError(
                    f"Puma node {result['node_id']} failed to generate base node config"
                )

    def get_ignition_step_idx(self, steps: List[Dict]) -> int:
        """
        return index of network ignition step in test steps
        """

        for step_idx, step in enumerate(steps):
            if step["name"] == "Check that the network is entirely up":
                return step_idx

        raise TestFailed("No ignition step found in test steps")

    # Use this on newer versions (post M60.8)
    def api_force_dissoc(self, initiator_mac: str, responder_mac: str):
        method: str = "forceDissoc"
        data: Optional[Dict[str, Any]] = {
            "initiatorMac": initiator_mac,
            "responderMac": responder_mac,
        }
        api_result = ""
        try:
            api_result = self.api_service_request(method=method, data=data)
        except (DeviceCmdError, AttributeError):
            api_result = "api_service_request returned and error and caught in try/except this message is coming from there. "
            pass

        self.log_to_ctf("api_result:\n" + str(api_result))

    def api_set_igntion_state(self, ignition_state: bool):
        """
        disable or enable auto ignition for entire network
        """

        method: str = "setIgnitionState"
        data: Optional[Dict[str, Any]] = {"enable": ignition_state}
        api_result = self.api_service_request(method=method, data=data)
        self.log_to_ctf(str(api_result))

    def api_set_link_ignition_state(self, link_name: str, ignition_state: bool = True):
        """
        disable or enable auto ignition on link `link_name` based on `ignition_state`
        """

        data = {
            "enable": True,
            "linkAutoIgnite": {link_name: ignition_state},
        }
        api_result = self.api_service_request(method="setIgnitionState", data=data)
        self.log_to_ctf(str(api_result))

    def api_check_link_state(
        self, link_name: str, expected_is_alive: Optional[bool] = True
    ) -> None:
        """
        check if link is up when {expected_is_alive} is True
        check if link is up when {expected_is_alive} is False
        """

        method: str = "getLink"
        data: Optional[Dict[str, Any]] = {
            "name": link_name,
        }

        api_result = self.api_service_request(method=method, data=data)
        self.log_to_ctf("api_result:\n" + str(api_result))

        is_alive = api_result.get("is_alive")
        self.log_to_ctf(f"link: {link_name} is {'Up' if is_alive else 'Down'}.")

        link_state = "Up" if is_alive else "Down"
        expected_link_state = "Up" if expected_is_alive else "Down"

        if is_alive != expected_is_alive:
            raise TestFailed(
                f"link: {link_name} state is {link_state}, expected value was {expected_link_state}."
            )

    def api_check_node_state(self, node_name, expected_is_online: bool = True):
        """
        check if node is online when {expected_is_online} is True
        check if node is offline when {expected_is_online} is False
        """
        NodeStatusType = {"OFFLINE": 1, "ONLINE": 2, "ONLINE_INITIATOR": 3}
        data = {"name": node_name}
        api_result = self.api_service_request(method="getNode", data=data)
        self.log_to_ctf(str(api_result))
        status = api_result.get("status")
        if status != NodeStatusType["OFFLINE"]:
            node_is_online = True
        else:
            node_is_online = False

        if expected_is_online != node_is_online:
            error_msg = (
                f"Node {node_name} is {'online' if node_is_online else 'offline'} "
                f"when the expected state is {'online' if expected_is_online else 'offline'}"
            )
            self.log_to_ctf(error_msg, "error")
            raise TestFailed(error_msg)

    def get_cpe_prefix(self, node_id: int):
        """
        Get cpe prefix info from nodes_data for a node
        """

        try:
            env_params = self.nodes_data[node_id]["node_config"]["envParams"]
            return (env_params["CPE_IFACE_IP_PREFIX"], env_params["CPE_INTERFACE"])
        except KeyError as e:
            self.log_to_ctf(
                f"Node {node_id} does not have cpe prefix configured in nodes data config: {str(e)}"
            )
            return None

    def add_accton_cpe_routes(self, node_id: int, node_type: str = "DN"):
        """
        Add required routes for routing cpe traffic with accton DN or CN node.
        """

        # Retrieve cpe info if configured in node config
        cpe_info = self.get_cpe_prefix(node_id)
        if cpe_info:
            cpe_prefix = cpe_info[0]
            cpe_interface = cpe_info[1]
            cpe_interface_ip = f"{cpe_prefix.split('/')[0]}1/64"
        else:
            self.log_to_ctf(f"Failed to add cpe routes to Accton node {node_id}")
            return

        # Configure CPE routes for accton CN and DN
        if node_type == "CN":
            cmd = f"ip -6 addr add {cpe_interface_ip} dev br-lan; puff prefixmgr advertise {cpe_prefix}"
        else:
            cmd = f"vppctl set interface l3 {cpe_interface}"

        cmd_success = self.device_info[node_id].action_custom_command(
            cmd, self.timeout - 1
        )
        if cmd_success["error"]:
            error_msg = f"'{cmd}' Failed: {cmd_success['message'].strip()}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

        self.log_to_ctf(
            f"'{cmd}' executed successfully. output: {cmd_success['message'].strip()}"
        )

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        steps = super().get_test_steps()

        # add cpe routes all any accton nodes present in the network
        for node_id in self.get_tg_devices():
            info = self.device_info[node_id]
            if info.metadata["device_sub_type"] == "accton dn":
                steps.append(
                    {
                        "name": f"Add cpe routes to accton DN node {node_id}",
                        "function": self.add_accton_cpe_routes,
                        "function_args": (node_id,),
                        "success_msg": "Completed",
                        "continue_on_failure": True,
                    }
                )
            if info.metadata["device_sub_type"] == "accton cn":
                steps.append(
                    {
                        "name": f"Add cpe routes to accton CN node {node_id}",
                        "function": self.add_accton_cpe_routes,
                        "function_args": (node_id, "CN"),
                        "success_msg": "Completed",
                        "continue_on_failure": True,
                    }
                )
        return steps


class TestNodeIotNLT1(TestNodeIot):
    TEST_NAME = "NodeIOTv2-NLT-1"
    DESCRIPTION = ""

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestNodeIotNLT1, TestNodeIotNLT1
        ).test_params()
        test_params["traffic_streams"] = {
            "desc": (
                "path to json file defining device id and ports of traffic generators "
                + "to run traffic"
            ),
            "required": True,
        }
        return test_params

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        steps = super().get_test_steps()

        # Run ping to check connectivity for each traffic stream defined
        # Run 500Mbps UDP Bidirectionl iperf for 10 mins for each traffic stream serially
        traffic_streams = json.load(open(self.test_args.get("traffic_streams", [])))
        for i, stream in enumerate(traffic_streams):
            stream.update(
                {
                    "bandwidth": 500,
                    "threshold": {"throughput": 0.99, "lost datagrams": 0.01},
                    "port": 5002 + i,
                    "traffic_type": "UDP",
                    "direction": "bi",
                    "packet_size": "1452",
                    "time": 120,
                }
            )
            steps.extend(
                [
                    {
                        "name": (
                            f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                            f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                        ),
                        "function": self.cpe_ping,
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
                    },
                    {
                        "name": "Run Traffic",
                        "function": self.run_traffic,
                        "function_args": ([stream],),
                        "success_msg": "iperf ran successfully",
                        "continue_on_failure": True,
                    },
                ]
            )
            i += 1
        return steps
