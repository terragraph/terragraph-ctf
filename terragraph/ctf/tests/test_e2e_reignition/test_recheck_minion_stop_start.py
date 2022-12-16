#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List, Optional

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestX86TGIgnMinionStop(TestX86TGIgn):
    TEST_NAME = "E2E Ignition Recheck"
    DESCRIPTION = "Verify that e2e network stays up after stopping and starting e2e minions on some nodes"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    def steps_e2e_minion_service_verify_topology(
        self,
        e2e_minion_sv: str,
        node_ids: List[int],
        delay_verify_topology_s: int = 180,
        expected_num_nodes_links: int = 0,
        is_cont_on_fail: Optional[bool] = False,
    ) -> List[Dict]:
        # start with empty list
        steps = []
        step_name_e2e_minion = (
            f"Start e2e minion in nodes: {node_ids}"
            if e2e_minion_sv == "start"
            else f"Stop e2e minion in nodes: {node_ids}"
        )

        steps.extend(
            [
                {
                    "name": f"{step_name_e2e_minion}",
                    "function": self.tg_restart_minion,
                    "function_args": (node_ids, e2e_minion_sv),
                    "success_msg": f"Successfuly issued {step_name_e2e_minion}",
                },
                {
                    "name": "Show topology with filter and verify expected nodes,links"
                    + f"={expected_num_nodes_links} after {delay_verify_topology_s} secs",
                    "function": self.show_topology_and_verify,
                    "function_args": (
                        "nodes_offline_links_down",
                        expected_num_nodes_links,
                        expected_num_nodes_links,
                    ),
                    "success_msg": "Showed topology and verified expected nodes,links",
                    "continue_on_failure": is_cont_on_fail,
                    "delay": delay_verify_topology_s,
                },
            ]
        )
        return steps

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        actions = self.test_options["actions"]
        recheck_network_up_timeout_s = self.test_options["recheck_network_up_timeout"]
        steps.extend(
            self.steps_ping_lo_all_tg_nodes_from_src(
                src_node_id=self.test_options["ping_all_src_node_id"],
                skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                is_cont_on_fail=True,
            )
        )
        steps.append(
            {
                "name": "Show topology without filter",
                "function": self.show_topology_and_verify,
                "function_args": (),
                "success_msg": "Showed topology without filter",
            },
        )
        for action in actions:
            steps.extend(
                self.steps_e2e_minion_service_verify_topology(
                    e2e_minion_sv=action["e2e_minion_sv"],
                    node_ids=action["node_ids"],
                    delay_verify_topology_s=action["delay_verify_topology_s"],
                    expected_num_nodes_links=action["expected_num_nodes_links"],
                    is_cont_on_fail=True,
                )
            )
        steps.append(
            {
                "name": "ReCheck that the network is entirely up",
                "function": self.try_until_timeout,
                "function_args": (
                    self.controller_verify_topology_up,
                    (self.api_service_request, ["getTopology"]),
                    5,
                    recheck_network_up_timeout_s,
                ),
                "success_msg": "Network is up",
                "error_handler": self.get_common_error_handler(),
                "continue_on_failure": True,
            }
        )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
