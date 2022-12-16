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


class TestX86TGReIgnLink(TestX86TGIgn):
    TEST_NAME = "E2E Re-ignition"
    DESCRIPTION = "Brings the link(s) down and verifies re-ignition"

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
                        "name": f"ReCheck that the network is entirely up{itr_str}",
                        "function": self.try_until_timeout,
                        "function_args": (
                            self.controller_verify_topology_up,
                            (self.api_service_request, ["getTopology"]),
                            5,
                            self.test_args["ignition_timeout_s"],
                        ),
                        "success_msg": f"Network is up{itr_str}",
                        "error_handler": self.get_common_error_handler(),
                        "continue_on_failure": True,
                        "concurrent": True,
                    },
                    {
                        "name": f"Call e2e rest API to bring link(s) down after 150 secs delay{itr_str}",
                        "function": self.api_service_request,
                        "function_args": (
                            "setLinkStatus",
                            self.action_data,
                        ),
                        "success_msg": f"Called e2e rest API to bring link(s) down{itr_str}",
                        "continue_on_failure": True,
                        "concurrent": True,
                        "delay": 150,
                    },
                    {
                        "name": f"ReCheck that the network is entirely up after 60 secs delay{itr_str}",
                        "function": self.try_until_timeout,
                        "function_args": (
                            self.controller_verify_topology_up,
                            (self.api_service_request, ["getTopology"]),
                            5,
                            self.test_args["ignition_timeout_s"],
                        ),
                        "success_msg": f"Network is up{itr_str}",
                        "error_handler": self.get_common_error_handler(),
                        "continue_on_failure": True,
                        "delay": 60,
                    },
                ]
            )
            steps.extend(
                self.steps_ping_lo_all_tg_nodes_from_src(
                    src_node_id=self.test_options["ping_all_src_node_id"],
                    skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                    is_cont_on_fail=True,
                    is_concurrent=True,
                )
            )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
