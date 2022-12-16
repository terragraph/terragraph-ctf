#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import TestFailed
from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest


LOG = logging.getLogger(__name__)


class TestTgLa2(SitPumaTgCtfTest, x86TrafficGenCtfTest):
    TEST_NAME = "PUMA: LA Test Case"
    DESCRIPTION = "Link Adaptation test"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    def attenuation_actions(self, action: str) -> None:
        cmd = self.test_options[action]["cmd"]
        node_ids = self.test_options[action]["node_ids"]
        self.log_to_ctf(cmd)

        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise TestFailed(f"Node {result['node_id']}: attenuation failed")
            self.log_to_ctf(result["message"])

    def get_test_steps(self) -> List[Dict]:
        traffic_profile = self.test_data.get("traffic_profile")
        test_details = self.test_data.get("test_details")
        attenuator_id: int = test_details.get("attenuator_id")
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
        ]

        if self.test_options.get("ramp_up", None):

            steps.extend(
                [
                    {
                        "name": "Run ramp_up script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("ramp_up",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run ramp_down script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("ramp_down",),
                        "success_msg": "attenuation level set successfully",
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "continue_on_failure": True,
                    },
                ]
            )

        if self.test_options.get("Toggle_Front_5s", None):

            steps.extend(
                [
                    {
                        "name": "Run Toggle_Front_5s script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("Toggle_Front_5s",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                ]
            )

        if self.test_options.get("Toggle_Front_2s", None):

            steps.extend(
                [
                    {
                        "name": "Run Toggle_Front_2s script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("Toggle_Front_2s",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                ]
            )
        if self.test_options.get("LA_4_ramp_up", None):

            steps.extend(
                [
                    {
                        "name": "Run LA_4_ramp_up script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("LA_4_ramp_up",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run LA_4_ramp_down script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("LA_4_ramp_down",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                ]
            )

        if self.test_options.get("LA_4_1", None):

            steps.extend(
                [
                    {
                        "name": "Run LA_4_1 script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("LA_4_1",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                ]
            )

        if self.test_options.get("LA_4_2", None):

            steps.extend(
                [
                    {
                        "name": "Run LA_4_2 script to set the attenuation level.",
                        "function": self.attenuation_actions,
                        "function_args": ("LA_4_2",),
                        "success_msg": "attenuation level set successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "concurrent": True,
                        "continue_on_failure": True,
                    },
                ]
            )

        return steps
