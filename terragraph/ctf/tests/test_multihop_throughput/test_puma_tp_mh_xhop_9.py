#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgTPMHXHop9(TestX86TGIgn):
    TEST_NAME = "PUMA_RF_TP-MH-XHop.9: Multihop throughput test"
    DESCRIPTION = "Test the Multi-Hop TPUT at MCS 9, packet size 1425(UDP), 1428(TCP)."

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        traffic_profile = self.test_data["traffic_profile"]
        ping_profile = self.test_data["ping_profile"]

        for ping_x_hop in ping_profile["x_hop"]:
            steps.append(
                {
                    "name": (
                        f"Ping from CPE device {ping_x_hop['from_device_id']} port {ping_x_hop['from_netns']}"
                        f" to CPE device {ping_x_hop['to_device_id']} port {ping_x_hop['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        ping_x_hop["from_device_id"],
                        ping_x_hop["to_device_id"],
                        ping_x_hop["from_netns"],
                        ping_x_hop["to_netns"],
                    ),
                    "success_msg": (
                        f"Ping from device {ping_x_hop['from_device_id']} port {ping_x_hop['from_netns']}"
                        f"to device {ping_x_hop['to_device_id']} port {ping_x_hop['to_netns']} is successful"
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
                    "name": "UDP Traffic",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["xhop_9_udp"],),
                    "success_msg": "Successfully executed UDP traffic",
                    "continue_on_failure": True,
                },
                {
                    "name": "vpp interface info",
                    "function": self.interface_info,
                    "function_args": (),
                    "success_msg": "Dumped vpp interface info",
                    "continue_on_failure": True,
                },
                {
                    "name": "TCP traffic",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["xhop_9_tcp"],),
                    "success_msg": "Successfully executed TCP traffic",
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
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
