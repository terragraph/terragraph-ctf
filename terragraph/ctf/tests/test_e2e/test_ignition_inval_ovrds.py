#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestX86TGIgnInvalOvrds(TestX86TGIgn):
    TEST_NAME = "E2E Ignition"
    DESCRIPTION = "Verify that controller throws errors when invalid configs are pushed"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.action_data = self.test_options["action_data"]

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()

        num_itrns = self.test_options["action_iterations"]
        for i in range(num_itrns):
            if num_itrns > 1:
                itr_str: str = f"(iteration {i + 1} of {num_itrns})"
            else:
                itr_str: str = ""
            steps.extend(
                [
                    {
                        "name": f"Call e2e rest API to modify node overrides(gps disable){itr_str}",
                        "function": self.api_service_request,
                        "function_args": (
                            "modifyNodeOverridesConfig",
                            self.action_data["override1"],
                        ),
                        "success_msg": f"Called e2e rest API to modify node overrides(gps disable){itr_str}",
                        "continue_on_failure": True,
                    },
                    {
                        "name": f"Call e2e rest API to modify node overrides(oob_interface){itr_str}",
                        "function": self.api_service_request,
                        "function_args": (
                            "modifyNodeOverridesConfig",
                            self.action_data["override2"],
                        ),
                        "success_msg": f"Called e2e rest API to modify node overrides(oob_interface){itr_str}",
                        "continue_on_failure": True,
                    },
                    {
                        "name": f"Call e2e rest API to modify node overrides(laMaxMcs){itr_str}",
                        "function": self.api_service_request,
                        "function_args": (
                            "modifyNodeOverridesConfig",
                            self.action_data["override3"],
                        ),
                        "success_msg": f"Called e2e rest API to modify node overrides(laMaxMcs){itr_str}",
                        "continue_on_failure": True,
                    },
                    {
                        "name": f"Call e2e rest API to get node overrides{itr_str}",
                        "function": self.api_service_request,
                        "function_args": (
                            "getNodeOverridesConfig",
                            self.action_data["node"],
                        ),
                        "success_msg": f"Called e2e rest API to get node overrides{itr_str}",
                        "continue_on_failure": True,
                    },
                ]
            )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
