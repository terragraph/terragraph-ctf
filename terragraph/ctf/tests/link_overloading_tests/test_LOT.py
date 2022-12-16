#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgLOT(TestX86TGIgn):
    TEST_NAME = "PUMA_RF_LOT: Link Overloading Tests"
    DESCRIPTION = "Test link overloading, packet size 1500(UDP) for 600 seconds."

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        traffic_profile = self.test_data["traffic_profile"]
        ping_profile = self.test_data["ping_profile"]

        for ping_link in ping_profile["link"]:
            steps.append(
                {
                    "name": (
                        f"Ping from CPE device {ping_link['from_device_id']} port {ping_link['from_netns']}"
                        f" to CPE device {ping_link['to_device_id']} port {ping_link['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        ping_link["from_device_id"],
                        ping_link["to_device_id"],
                        ping_link["from_netns"],
                        ping_link["to_netns"],
                    ),
                    "success_msg": (
                        f"Ping from device {ping_link['from_device_id']} port {ping_link['from_netns']}"
                        f"to device {ping_link['to_device_id']} port {ping_link['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                }
            )

        steps.extend(
            [
                {
                    "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                },
                {
                    "name": "Run parallel iperf overloading first link after 300 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 300,
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
