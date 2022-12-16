#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTg3Sector(TestX86TGIgn):
    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        traffic_profile = self.test_data["traffic_profile"]

        for stream in traffic_profile["3sec_udp"]:
            steps.append(
                {
                    "name": (
                        f"Ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
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
                        f"Ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
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
                    "name": "UDP Traffic - ps 1452",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["3sec_udp"],),
                    "success_msg": "CPE to CPE iperf successful",
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
                    "name": "TCP Traffic - ps 1428",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile["3sec_tcp"],),
                    "success_msg": "CPE to CPE iperf successful",
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
