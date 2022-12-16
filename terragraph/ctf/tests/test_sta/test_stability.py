#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import time
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestStability(TestX86TGIgn):
    TEST_NAME = "Stability Test"
    DESCRIPTION = "8 hour test to test network stability"

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()

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

        steps.append(
            {
                "name": "Clear vpp interface",
                "function": self.interface_info,
                "function_args": (True,),
                "success_msg": "Cleared vpp interface",
                "continue_on_failure": True,
            },
        )

        for i in range(4):
            steps.extend(
                [
                    {
                        "name": f"Run Traffic {i}",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "iperf ran successfully",
                        "continue_on_failure": True,
                    },
                    {
                        "name": "sleep 30 sec",
                        "function": time.sleep,
                        "function_args": (30,),
                        "success_msg": "waited 20s",
                        "continue_on_failure": True,
                    },
                ]
            )

        steps.append(
            {
                "name": "vpp interface info",
                "function": self.interface_info,
                "function_args": (),
                "success_msg": "Dumped vpp interface info",
                "continue_on_failure": True,
            }
        )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
