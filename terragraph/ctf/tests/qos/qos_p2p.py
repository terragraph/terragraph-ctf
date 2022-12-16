#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.tests.qos.test_qos import TestTgQos

LOG = logging.getLogger(__name__)


class Qos_P2p(TestTgQos):
    TEST_NAME = "Qos_P2P"
    DESCRIPTION = "Puma QoS point to point test"

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
        steps.extend(
            [
                {
                    "name": "Run parallel iperf on setup based on given traffic profile",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile,),
                    "success_msg": "Parallel iperf completed successfully",
                    "continue_on_failure": True,
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
