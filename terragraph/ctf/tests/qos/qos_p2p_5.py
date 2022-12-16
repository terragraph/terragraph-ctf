#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.tests.qos.test_qos import TestTgQos

LOG = logging.getLogger(__name__)


class Qos_P2p_5(TestTgQos):
    TEST_NAME = "PUMA: Qos_P2p_5"
    DESCRIPTION = "This test checks the Basic priority service with congestion response"

    """
        This test consists of basically three iperf traffic
        1. DN0 to CN, tc0 green for 180 s
        2. DN0 to CN, tc3 green for 180 s
        3. DN0 to CN, tc3 yellow
          Repeat 5 iterations:
            a. 94 for 30 seconds, then
            b. 517 for 30 seconds

        The first iteration runs iperf 1,2 and 3 (a) known as stream 1 in code for 30 s and then runs
        iperf 1,2 and 3(b) known as stream 2 in code for 30s till it hits the total time of 180s (also known as phase1 time)

        The second iteration runs the iperf 3a ( known as stream3 in code ) and 3b ( also known as stream 4 in code ) for a remainder of 120s ( also known as phase2 time) after the first while loop is completed

    """

    def get_test_steps(self) -> List[Dict]:
        traffic_profile = self.test_data.get("traffic_profile", {})
        ping_profile = self.test_data.get("ping_profile", {})

        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
            {
                "name": "Print the node config on the 1 node",
                "function": self.show_current_node_config,
                "function_args": ([1],),
                "success_msg": "node config printed successfully",
            },
            {
                "name": "Print the node config on the 2 node",
                "function": self.show_current_node_config,
                "function_args": ([2],),
                "success_msg": "node config printed successfully",
            },
            {
                "name": "Print the policer info on CN node 1",
                "function": self.print_policerinfo,
                "function_args": ([1],),
                "success_msg": "policer info printed successfully",
            },
        ]

        for stream in ping_profile:
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
                    "continue_on_failure": True,
                }
            )

        phase1_time = 180
        stream = 1
        # This while loops runs the stream 1 for 30 s and then stream 2 for 30s till it hits the phase1_time
        while phase1_time > 0:
            steps.append(
                {
                    "name": f"Run traffic based on traffic profile stream {stream}",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile[str(stream)],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                }
            )
            phase1_time = phase1_time - 30
            if stream == 1:
                stream = 2
            else:
                stream = 1

        # the next phase of test time is 120s (300 - 180):
        phase2_time = 120
        stream = 3
        # This while loops runs the stream 3 for 30 s and then stream 4 for 30s till it hits the phase2_time
        while phase2_time > 0:
            steps.append(
                {
                    "name": f"Run traffic based on traffic profile stream {stream}",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile[str(stream)],),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                }
            )
            phase2_time = phase2_time - 30
            if stream == 3:
                stream = 4
            else:
                stream = 3

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
