#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep
from typing import Dict, List

from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.x86_tg import x86TgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest


LOG = logging.getLogger(__name__)


class TestX86TGIgn(SitPumaTgCtfTest, x86TgCtfTest, x86TrafficGenCtfTest):
    TEST_NAME = "E2E Ignition"
    DESCRIPTION = "Ignition using external E2E controller"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(TestX86TGIgn, TestX86TGIgn).test_params()
        test_params["ignition_timeout_s"] = {
            "desc": (
                "How many seconds should we wait for the network to come up? "
                + "This may need to take into account the controller potentially "
                + "rebooting the nodes for a config update."
            ),
            "default": 900.0,
            "convert": float,
        }
        SitPumaTgCtfTest.merge_dict(test_params, x86TgCtfTest.test_params())
        SitPumaTgCtfTest.merge_dict(test_params, x86TrafficGenCtfTest.test_params())

        return test_params

    def get_test_steps(self) -> List[Dict]:

        # Purpose of e2e_ignition_config is to determine parameters such as:
        # negate_result
        # continue_on_failure
        # ignition_timeout_sec
        # because on some ignition test cases we expect the failure to be the
        # expected result.
        # Also for a test with failing e2e_ignition expectation we don't need
        # to wait for 300+ seconds
        test_ignition_config = self.test_data.get("e2e_ignition_config", {})
        ignition_continue_on_failure = test_ignition_config.get(
            "continue_on_failure", False
        )
        ignition_negate_result = test_ignition_config.get("negate_result", False)
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        if test_ignition_config.get("ignition_timeout_s"):
            ignition_timeout_s = test_ignition_config.get("ignition_timeout_s")

        steps = []
        steps.append(self.COMMON_TEST_STEPS["check_software_versions"])

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
                    "name": "Check e2e controller software version",
                    "function": self.get_e2e_cntrl_version,
                    "function_args": (),
                    "success_msg": "Successfully checked e2e controller software version",
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
                    "continue_on_failure": ignition_continue_on_failure,
                    "negate_result": ignition_negate_result,
                },
                {
                    "name": "Wait 60 seconds for last node to apply node config overrides changes",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after node overrides take effect",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": ignition_continue_on_failure,
                    "negate_result": ignition_negate_result,
                },
                {
                    "name": "Set fw log level debug ",
                    "function": self.minion_set_fb_fw_log_config,
                    "function_args": (
                        None,
                        "debug",
                    ),
                    "success_msg": "fw log debug level set",
                },
            ]
        )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
