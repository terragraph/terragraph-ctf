#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from time import sleep
from typing import Dict, List

from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIot

LOG = logging.getLogger(__name__)


class TestNodeIotNWS1(TestNodeIot):
    TEST_NAME = "NodeIOTv2-NWS-1 (Node Wireless Security)"
    DESCRIPTION = "The purpose of this test is to validate that when the passphrase doesn’t match for some of the links, but matches for others, links with matching passphrase still come up correctly."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestNodeIotNWS1, TestNodeIotNWS1
        ).test_params()
        test_params["mismatch_node_id"] = {
            "desc": "Node ID of the wpa_passpharese mismatch",
            "required": True,
            "convert": int,
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

        mismatch_node_id = self.test_args["mismatch_node_id"]
        self.log_to_ctf(f"mismatch_node_id: {mismatch_node_id}")

        mismatch_nodes_data = {
            "node_config": {
                "radioParamsBase": {
                    "wsecParams": {
                        "wpaPskParams": {"wpa_passphrase": "mismatch_psk_test"}
                    }
                }
            }
        }

        # Amend for specific node_id!
        self.merge_dict(
            nodes_data_amend,
            {mismatch_node_id: mismatch_nodes_data},
        )

        return nodes_data_amend

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller

        # Configure matching passphrase (PSK) between DN and CN1 and mismatch configuration between DN and CN2.
        # Edit wpa_passphrase field in /etc/hostapd/hostapd_terraX.conf from “psk_test” to “mismatch_psk_test”.
        ignition_timeout_s = self.test_args["ignition_timeout_s"]

        steps = []
        if self.test_args["x86_image_path"]:
            steps.append(
                {
                    "name": "Push x86 image",
                    "function": self.push_x86_image,
                    "function_args": (self.test_args["x86_image_path"],),
                    "success_msg": "x86 image was upgraded.",
                }
            )
        steps.extend(
            [
                self.get_common_x86_test_steps()["setup_x86_services"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Check that the network is entirely up",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": True,
                    "negate_result": True,
                },
                {
                    "name": "Wait 60 seconds for last node to apply node config overrides changes",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after node overrides take effect",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": True,
                    "negate_result": True,
                },
            ]
        )

        traffic_streams = json.load(open(self.test_args.get("traffic_streams", {})))
        stream_pass = traffic_streams.get("stream_pass")
        stream_fail = traffic_streams.get("stream_fail")

        steps.extend(
            [
                # Run Ping from POP to both CNs. Expect One ping pass, one ping fail.
                {
                    "name": (
                        f"ping from CPE device {stream_pass['from_device_id']} port {stream_pass['from_netns']}"
                        f" to CPE device {stream_pass['to_device_id']} port {stream_pass['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream_pass["from_device_id"],
                        stream_pass["to_device_id"],
                        stream_pass["from_netns"],
                        stream_pass["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream_pass['from_device_id']} port {stream_pass['from_netns']}"
                        f"to device {stream_pass['to_device_id']} port {stream_pass['to_netns']} is successful"
                    ),
                    "concurrent": True,
                    "continue_on_failure": True,
                },
                {
                    "name": (
                        f"ping from CPE device {stream_fail['from_device_id']} port {stream_fail['from_netns']}"
                        f" to CPE device {stream_fail['to_device_id']} port {stream_fail['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream_fail["from_device_id"],
                        stream_fail["to_device_id"],
                        stream_fail["from_netns"],
                        stream_fail["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream_fail['from_device_id']} port {stream_fail['from_netns']}"
                        f"to device {stream_fail['to_device_id']} port {stream_fail['to_netns']} is successful"
                    ),
                    "concurrent": True,
                    "continue_on_failure": True,
                    "negate_result": True,
                },
            ]
        )
        return steps
