#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import copy
import logging
import math
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestStabilityBurst(TestX86TGIgn):
    TEST_NAME = "Stability with burst traffic"
    DESCRIPTION = (
        "Igniting network using external E2E controller and "
        + "running end to end traffic as stability with burst traffic"
    )

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
        stability_profile = self.test_data["stability_profile"]
        normal_traffic_iterations = (
            stability_profile["total_time"] / stability_profile["split_iperf_time"]
        )
        normal_traffic_iterations_rounded = math.ceil(normal_traffic_iterations)
        normal_traffic_step_delay = 0
        for i in range(normal_traffic_iterations_rounded):
            steps.append(
                {
                    "name": f"Run Traffic {i+1}",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile,),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                    "delay": normal_traffic_step_delay,
                    "concurrent": True,
                }
            )
            normal_traffic_step_delay += stability_profile["split_iperf_time"] + 20
        number_of_burst_iterations = (
            stability_profile["total_time"] / stability_profile["burst_mode_delay"]
        )
        burst_traffic_time = (
            number_of_burst_iterations * stability_profile["burst_mode_time"]
        )
        iterations_for_burst_time = (
            burst_traffic_time / stability_profile["burst_mode_delay"]
        )
        effective_burst_iterations = (
            number_of_burst_iterations - iterations_for_burst_time
        )
        effective_burst_iterations_rounded = math.ceil(effective_burst_iterations)
        burst_traffic_profile: list = copy.deepcopy(traffic_profile)
        for item in burst_traffic_profile:
            item["port"] = item["port"] + len(burst_traffic_profile) * 2
            item["bandwidth"] = stability_profile["burst_mode_bandwidth"]
            item["time"] = stability_profile["burst_mode_time"]
        burst_traffic_step_delay = 0
        for j in range(effective_burst_iterations_rounded):
            burst_traffic_step_delay += stability_profile["burst_mode_delay"]
            steps.append(
                {
                    "name": f"Burst Traffic {j+1}",
                    "function": self.run_traffic,
                    "function_args": (burst_traffic_profile,),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                    "delay": burst_traffic_step_delay,
                    "concurrent": True,
                }
            )
            burst_traffic_step_delay += stability_profile["burst_mode_time"] + 20

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
