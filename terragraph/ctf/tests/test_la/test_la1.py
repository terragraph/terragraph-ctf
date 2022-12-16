#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError
from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest


LOG = logging.getLogger(__name__)


class TestTgLa(SitPumaTgCtfTest, x86TrafficGenCtfTest):
    TEST_NAME = "PUMA: LA Test Case"
    DESCRIPTION = "Link Adaptation test"

    def enable_link_adaptation(
        self,
        node_ids: List[int],
        mcs_value: int,
        mac_address: str,
    ) -> None:

        command_set_mcs: str = (
            f"tg2 minion fw_set_params -r {mac_address} mcs {mcs_value}"
        )

        futures: Dict = self.run_cmd(command_set_mcs, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_set_mcs} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_set_mcs} in Node {result['node_id']}:\n{result['message']}"
            )

    def get_test_steps(self) -> List[Dict]:
        test_options = self.test_data["test_options"]
        # self.node_ids = self.test_options["node_ids"]
        node_info = self.test_data["node_info"]
        traffic_profile = self.test_data.get("traffic_profile", {})
        test_details = self.test_data.get("test_details")
        attenuator_id: int = test_details.get("attenuator_id")
        attenuation_level: int = test_details.get("attenuation_level")
        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Set Attenuation Level to 0db",
                "function": self.set_attenuation_x_db,
                "function_args": (
                    attenuator_id,
                    0,
                ),
                "success_msg": "Attenuation level set to 0db",
            },
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
            {
                "name": f"Set Attenuation Level to {attenuation_level}db",
                "function": self.set_attenuation_x_db,
                "function_args": (
                    attenuator_id,
                    attenuation_level,
                ),
                "success_msg": f"Attenuation level set to {attenuation_level}db",
            },
        ]

        steps.extend(
            [
                {
                    "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile,),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                },
                {
                    "name": "Disassociate the first link",
                    "function": self.minion_dissoc,
                    "function_args": (
                        node_info["initiator_id"],
                        node_info["initiator_mac"],
                        node_info["responder_mac_1"],
                    ),
                    "success_msg": "links are disassosiated successfully",
                    "continue_on_failure": True,
                    "error_handler": self.get_common_error_handler(),
                    "delay": 30,
                },
                {
                    "name": "Disassociate the  second link",
                    "function": self.minion_dissoc,
                    "function_args": (
                        node_info["initiator_id"],
                        node_info["initiator_mac"],
                        node_info["responder_mac_2"],
                    ),
                    "success_msg": "links are disassosiated successfully",
                    "continue_on_failure": True,
                    "error_handler": self.get_common_error_handler(),
                    "delay": 30,
                },
                self.COMMON_TEST_STEPS["assoc_terra_links"],
                self.COMMON_TEST_STEPS["check_timing_sync"],
                {
                    "name": "Enable Link_Adaptaion on second link",
                    "function": self.enable_link_adaptation,
                    "function_args": (
                        test_options["node_id_1"],
                        test_options["mcs_value"],
                        test_options["responder_mac_1"],
                    ),
                    "success_msg": "Link Adaptaion is enabled successfully",
                    "continue_on_failure": True,
                    "delay": 30,
                },
                {
                    "name": "Enable Link_Adaptaion on third link",
                    "function": self.enable_link_adaptation,
                    "function_args": (
                        test_options["node_id_1"],
                        test_options["mcs_value"],
                        test_options["responder_mac_2"],
                    ),
                    "success_msg": "Link Adaptaion is enabled successfully",
                    "continue_on_failure": True,
                    "delay": 30,
                },
                {
                    "name": "Enable Link_Adaptaion on first link",
                    "function": self.enable_link_adaptation,
                    "function_args": (
                        test_options["node_id_2"],
                        test_options["mcs_value"],
                        test_options["initiator_mac"],
                    ),
                    "success_msg": "Link Adaptaion is enabled successfully",
                    "continue_on_failure": True,
                    "delay": 30,
                },
                {
                    "name": "Enable Link_Adaptaion on first link",
                    "function": self.enable_link_adaptation,
                    "function_args": (
                        test_options["node_id_3"],
                        test_options["mcs_value"],
                        test_options["initiator_mac"],
                    ),
                    "success_msg": "Link Adaptaion is enabled successfully",
                    "continue_on_failure": True,
                    "delay": 30,
                },
            ]
        )

        for stream in traffic_profile:
            steps.append(
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
                }
            )

        steps.append(
            {
                "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                "function": self.run_traffic,
                "function_args": (traffic_profile,),
                "success_msg": "Parallel iperf completed successfully",
                "continue_on_failure": True,
            }
        )

        return steps
