#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.x86_tg import x86TgCtfTest


LOG = logging.getLogger(__name__)


class TestTgX86Setup(x86TgCtfTest):
    TEST_NAME = "TGX86: Test x86 Terragraph services"
    DESCRIPTION = "Set up and test basic functionality of Terragraph services on x86."
    NODES_DATA_FORMAT = "e2e-x86-nodes-data-setup-{SETUP_ID}.json"

    def pre_run(self) -> None:
        self.log_to_ctf("No pre-run needed for this test")

    def get_test_steps(self) -> List[Dict]:
        steps = []
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
                    "name": "Fetch E2E controller topology via api_service",
                    "function": self.api_service_request,
                    "function_args": ("getTopology",),
                    "success_msg": "api_service request succeeded.",
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
