#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Dict, List

from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIot

LOG = logging.getLogger(__name__)


class TestIotNodeThroughput(TestNodeIot):
    TEST_NAME = "NodeIOTv2-TP-1"
    DESCRIPTION = "Throughput test between POP DN and TG5 via TG4 (OEM DN DUT)."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestIotNodeThroughput, TestIotNodeThroughput
        ).test_params()
        test_params["initiator_mac"] = {
            "desc": (
                "Provide initiator mac that the link will be disabled/enabled during the test run."
            ),
            "required": True,
        }
        test_params["responder_mac"] = {
            "desc": (
                "Provide responder mac that the link will be disabled/enabled during the test run."
            ),
            "required": True,
        }
        test_params["traffic_streams"] = {
            "desc": (
                "path to json file defining device id and ports of traffic generators "
                + "to run traffic"
            ),
            "required": True,
        }

        return test_params

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        nodes_data_amend = super().nodes_data_amend(num_nodes)

        # Force maximum link adaptation to MSC-12;
        # expect to achieve MCS11 or MCS12 on each link
        laMaxMcs_node_config_json = {
            "node_config": {
                "linkParamsBase": {
                    "fwParams": {"laMaxMcs": 12},
                }
            }
        }

        # Amend for All Terragraph Nodes!
        self.merge_dict(
            nodes_data_amend,
            {i: laMaxMcs_node_config_json for i in range(1, num_nodes + 1)},
        )

        return nodes_data_amend

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        steps = super().get_test_steps()

        initiator_mac = self.test_args["initiator_mac"]
        responder_mac = self.test_args["responder_mac"]

        traffic_streams = json.load(open(self.test_args.get("traffic_streams", [])))
        ping_stream = traffic_streams.get("ping_stream")
        udp_traffic = traffic_streams.get("udp_traffic")
        tcp_traffic = traffic_streams.get("tcp_traffic")

        steps.extend(
            [
                {
                    "name": "Disable auto ignition on controller",
                    "function": self.api_set_igntion_state,
                    "function_args": (False,),
                    "success_msg": "Successfully disabled auto igntion on controller",
                },
                {
                    "name": "Disable Link between DN and CN",
                    "function": self.api_force_dissoc,
                    "function_args": (
                        initiator_mac,
                        responder_mac,
                    ),
                    "success_msg": f"Link between {initiator_mac} and {responder_mac} is disassociated!",
                    "continue_on_failure": True,
                },
                {
                    "name": "ReCheck network after disabling the link. It should fail.",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        10,
                    ),
                    "success_msg": "Link is disabled",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": True,
                    "negate_result": True,
                },
                {
                    "name": (
                        f"ping from CPE device {ping_stream['from_device_id']} port {ping_stream['from_netns']}"
                        f" to CPE device {ping_stream['to_device_id']} port {ping_stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        ping_stream["from_device_id"],
                        ping_stream["to_device_id"],
                        ping_stream["from_netns"],
                        ping_stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {ping_stream['from_device_id']} port {ping_stream['from_netns']}"
                        f"to device {ping_stream['to_device_id']} port {ping_stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                    "negate_result": True,
                },
                {
                    "name": "Run UDP Traffic",
                    "function": self.run_traffic,
                    "function_args": ([udp_traffic],),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                },
                {
                    "name": "Enable auto ignition on controller",
                    "function": self.api_set_igntion_state,
                    "function_args": (True,),
                    "success_msg": "Successfully enabled auto igntion on controller",
                },
                {
                    "name": "ReCheck network after enabling the auto igntion. All links should be up!",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        100,
                    ),
                    "success_msg": "Network is up!",
                    "error_handler": self.get_common_error_handler(),
                },
                {
                    "name": "Run TCP Traffic",
                    "function": self.run_traffic,
                    "function_args": ([tcp_traffic],),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                },
            ]
        )

        return steps
