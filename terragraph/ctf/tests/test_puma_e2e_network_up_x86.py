#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest
from terragraph.ctf.x86_tg import x86TgCtfTest

LOG = logging.getLogger(__name__)


class TestTgE2ENetworkUpExternalX86(PumaTgCtfTest, x86TgCtfTest):
    TEST_NAME = "PUMA: E2E Network Up (x86 Controller)"
    DESCRIPTION = "Bring up all links in a network using an x86 E2E controller."
    LOG_FILES = ["/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "e2e-x86-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgE2ENetworkUpExternalX86, TestTgE2ENetworkUpExternalX86
        ).test_params()
        test_params["ignition_timeout_s"] = {
            "desc": (
                "How many seconds should we wait for the network to come up? "
                + "This may need to take into account the controller potentially "
                + "rebooting the nodes for a config update."
            ),
            "default": 600.0,
            "convert": float,
        }
        PumaTgCtfTest.merge_dict(test_params, x86TgCtfTest.test_params())
        test_params["managed_config"]["default"] = False

        return test_params

    def get_test_steps(self) -> List[Dict]:
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
        ]
        if self.test_args["x86_image_path"]:
            steps.append(
                {
                    "name": "Push x86 image",
                    "function": self.push_x86_image,
                    "function_args": (self.test_args["x86_image_path"],),
                    "success_msg": "x86 image was upgraded.",
                }
            )
        steps.extend(
            [
                self.get_common_x86_test_steps()["setup_x86_services"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Check that the network is entirely up",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
