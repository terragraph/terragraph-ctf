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


class TestX86TGReIgnCntrSvc(TestX86TGIgn):
    TEST_NAME = "E2E Re-ignition"
    DESCRIPTION = "Verifies network is up when e2e controller service is restarted"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.action_data = self.test_options["action_data"]

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        e2e_ctrl_node_id = self.find_x86_tg_host_id()
        num_itrns = self.test_options["action_iterations"]
        for i in range(num_itrns):
            if num_itrns > 1:
                itr_str: str = f"(iteration {i + 1} of {num_itrns})"
            else:
                itr_str: str = ""

            steps.append(
                {
                    "name": f"Stop and kill e2e controller service {itr_str}",
                    "function": self._stop_x86_tg_service,
                    "function_args": (
                        e2e_ctrl_node_id,
                        "e2e_controller",
                    ),
                    "success_msg": f"Stopped e2e controller service {itr_str}",
                    "continue_on_failure": True,
                    "concurrent": True,
                }
            )
            steps.extend(
                self.steps_ping_lo_all_tg_nodes_from_src(
                    src_node_id=self.test_options["ping_all_src_node_id"],
                    skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                    is_cont_on_fail=True,
                    is_concurrent=True,
                    start_delay=60,
                )
            )
            steps.extend(
                [
                    {
                        "name": f"Start e2e controller service {itr_str}",
                        "function": self.start_x86_tg_services,
                        "function_args": (
                            e2e_ctrl_node_id,
                            self.action_data["iface_name"],
                            {"e2e_controller"},
                        ),
                        "success_msg": f"Started e2e controller service {itr_str}",
                        "continue_on_failure": True,
                        "concurrent": False,
                    },
                    {
                        "name": f"ReCheck that the network is entirely up{itr_str}",
                        "function": self.try_until_timeout,
                        "function_args": (
                            self.controller_verify_topology_up,
                            (self.api_service_request, ["getTopology"]),
                            5,
                            self.test_args["ignition_timeout_s"],
                        ),
                        "success_msg": "Network is up{itr_str}",
                        "error_handler": self.get_common_error_handler(),
                        "continue_on_failure": True,
                    },
                ]
            )
            steps.extend(
                self.steps_ping_lo_all_tg_nodes_from_src(
                    src_node_id=self.test_options["ping_all_src_node_id"],
                    skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                    is_cont_on_fail=True,
                    is_concurrent=True,
                    start_delay=60,
                )
            )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
