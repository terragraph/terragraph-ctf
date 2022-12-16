#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgLOT3(TestX86TGIgn):
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
                    "name": "Run parallel UDP iperf of 100 Mbps on all 8 links",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                },
                {
                    "name": "Overload DUT-1 TO DUT-2 link with 1000Mbps link after 120 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link1"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 120,
                },
                {
                    "name": "Overload DUT-1 TO DUT-3 link with 1000Mbps link after 300 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link2"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 300,
                },
                {
                    "name": "Overload DUT-1 TO DUT-4 link with 1000Mbps link after 480 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link3"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 480,
                },
                {
                    "name": "Overload DUT-1 TO DUT-5 link with 1000Mbps link after 660 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link4"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 660,
                },
                {
                    "name": "Overload DUT-1 TO DUT-6 link with 1000Mbps link after 840 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link5"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 840,
                },
                {
                    "name": "Overload DUT-1 TO DUT-7 link with 1000Mbps link after 1020 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link6"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 1020,
                },
                {
                    "name": "Overload DUT-1 TO DUT-8 link with 1000Mbps link after 1200 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link7"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 1200,
                },
                {
                    "name": "Overload DUT-1 TO DUT-9 link with 1000Mbps link after 1380 seconds",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["parallel_udp_overload_link8"],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 1380,
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
