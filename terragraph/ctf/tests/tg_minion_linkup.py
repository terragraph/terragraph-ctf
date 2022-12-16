#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest

LOG = logging.getLogger(__name__)


class TestTgMinionLinkUp(SitPumaTgCtfTest, x86TrafficGenCtfTest):
    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgMinionLinkUp, TestTgMinionLinkUp
        ).test_params()

        test_params["continue_cpe_ping"] = {
            "desc": "Continue on CPE ping failures",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        SitPumaTgCtfTest.merge_dict(test_params, x86TrafficGenCtfTest.test_params())
        return test_params

    def get_test_steps(self) -> List[Dict]:
        traffic_profile = self.test_data.get("traffic_profile", {})
        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
        ]
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
                    "continue_on_failure": self.test_args["continue_cpe_ping"],
                }
            )
        steps.append(
            {
                "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                "function": self.run_traffic,
                "function_args": (traffic_profile,),
                "success_msg": "Parallel iperf completed successfully",
            }
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
