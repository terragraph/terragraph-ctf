#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import time
from argparse import Namespace
from typing import Dict, List

from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest

LOG = logging.getLogger(__name__)


class TestTgPumaP2PGolay(SitPumaTgCtfTest, x86TrafficGenCtfTest):
    TEST_NAME = "Puma RF golay"
    DESCRIPTION = "Verify golay on p2p link."

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgPumaP2PGolay, TestTgPumaP2PGolay
        ).test_params()
        SitPumaTgCtfTest.merge_dict(test_params, x86TrafficGenCtfTest.test_params())

        return test_params

    def get_test_steps(self) -> List[Dict]:
        traffic_profile = self.test_data.get("traffic_profile", {})
        traffic_stream_0 = traffic_profile[0]
        selected_link = self.test_options["selected_link"]
        initiator_id = selected_link["initiator_id"]
        responder_id = selected_link["responder_id"]
        responder_mac = selected_link["responder_mac"]
        initiator_mac = selected_link["initiator_mac"]
        respNodeType = selected_link["respNodeType"]
        golays = selected_link["golays"]

        steps = [
            {
                "name": "Diff Node config",
                "function": self.log_node_config_diff,
                "function_args": (),
                "success_msg": "Dumped Node config diff",
            },
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
        ]

        for golay in golays:
            link_str = f"[Node:{initiator_id}]{initiator_mac} -> [Node:{responder_id}]{responder_mac}"
            golay_str = f'rx/txGolay {golay["rxGolayIdx"]} - {golay["txGolayIdx"]}'
            steps.extend(
                [
                    {
                        "name": f"Bring up link {link_str} {golay_str}",
                        "function": self.minion_assoc,
                        "function_args": (
                            initiator_id,
                            initiator_mac,
                            responder_mac,
                            respNodeType,
                            None,
                            None,
                            golay["txGolayIdx"],
                            golay["rxGolayIdx"],
                            True,
                        ),
                        "success_msg": f"Successfully associated terra link(s) {golay_str}",
                        "error_handler": self.get_common_error_handler(),
                        "continue_on_failure": True,
                    }
                ]
            )

            responder_golay: Dict[str, int] = {
                "rxGolayIdx": golay["txGolayIdx"],
                "txGolayIdx": golay["rxGolayIdx"],
            }
            initiator_golay: Dict[str, int] = {
                "rxGolayIdx": golay["rxGolayIdx"],
                "txGolayIdx": golay["txGolayIdx"],
            }
            steps.extend(
                [
                    {
                        "name": f"Verify link golay on responder {golay_str}",
                        "function": self.verify_golay,
                        "function_args": (responder_id, initiator_mac, responder_golay),
                        "success_msg": "Link golay dumped",
                        "continue_on_failure": True,
                    },
                    {
                        "name": f"Verify link golay on initiator {golay_str}",
                        "function": self.verify_golay,
                        "function_args": (initiator_id, responder_mac, initiator_golay),
                        "success_msg": "Link golay dumped",
                        "continue_on_failure": True,
                    },
                    {
                        "name": (
                            f"ping from CPE device {traffic_stream_0['from_device_id']} port {traffic_stream_0['from_netns']}"
                            f" to CPE device {traffic_stream_0['to_device_id']} port {traffic_stream_0['to_netns']}"
                        ),
                        "function": self.cpe_ping,
                        "function_args": (
                            traffic_stream_0["from_device_id"],
                            traffic_stream_0["to_device_id"],
                            traffic_stream_0["from_netns"],
                            traffic_stream_0["to_netns"],
                        ),
                        "success_msg": (
                            f"ping from device {traffic_stream_0['from_device_id']} port {traffic_stream_0['from_netns']}"
                            f"to device {traffic_stream_0['to_device_id']} port {traffic_stream_0['to_netns']} is successful"
                        ),
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Run parallel iperf on p2mp setup based on given traffic profile",
                        "function": self.run_traffic,
                        "function_args": (traffic_profile,),
                        "success_msg": "Parallel iperf completed successfully",
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Dissoc",
                        "function": self.minion_dissoc,
                        "function_args": (
                            initiator_id,
                            initiator_mac,
                            responder_mac,
                        ),
                        "success_msg": "Dissoc succeeded",
                        "error_handler": self.get_common_error_handler(),
                        "continue_on_failure": True,
                    },
                    {
                        "name": "sleep 10 sec",
                        "function": time.sleep,
                        "function_args": (10,),
                        "success_msg": "waited 10s",
                        "continue_on_failure": True,
                    },
                ]
            )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
