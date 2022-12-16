#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from argparse import Namespace
from time import sleep
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgMinionRestart(TestX86TGIgn):
    TEST_NAME = "E2E Reignition"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgMinionRestart, TestTgMinionRestart
        ).test_params()

        test_params["minion_restart_iteration"] = {
            "desc": "How many times should we reginite with minion restart?",
            "default": 5,
            "convert": int,
        }

        return test_params

    def add_traffic_step(self, steps: List) -> None:
        traffic_profile = self.test_data["traffic_profile"]

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
        steps.extend(
            [
                {
                    "name": "Clear vpp interface",
                    "function": self.interface_info,
                    "function_args": (True,),
                    "success_msg": "Cleared vpp interface",
                    "continue_on_failure": True,
                },
                {
                    "name": "Run Traffic",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile,),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                },
                {
                    "name": "vpp interface info",
                    "function": self.interface_info,
                    "function_args": (),
                    "success_msg": "Dumped vpp interface info",
                    "continue_on_failure": True,
                },
            ]
        )

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()

        self.add_traffic_step(steps)

        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        repeat_count = self.test_args["minion_restart_iteration"]
        for _ in range(repeat_count):
            steps.extend(
                [
                    {
                        "name": "Disable auto ignition",
                        "function": self.api_service_request,
                        "function_args": (
                            "setIgnitionState",
                            {"enable": False},
                        ),
                        "success_msg": "Auto ignition disbaled",
                    },
                    {
                        "name": "Restart minion",
                        "function": self.tg_restart_minion,
                        "function_args": (),
                        "success_msg": "Minion restart complete",
                    },
                    {
                        "name": "Enable auto ignition",
                        "function": self.api_service_request,
                        "function_args": (
                            "setIgnitionState",
                            {"enable": True},
                        ),
                        "success_msg": "Auto ignition enabled",
                    },
                    {
                        "name": "Wait 60 seconds",
                        "function": sleep,
                        "function_args": (60,),
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
                    },
                ]
            )
            self.add_traffic_step(steps)

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
