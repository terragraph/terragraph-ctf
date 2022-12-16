#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestX86TGIgnMultiPOP(TestX86TGIgn):
    TEST_NAME = "E2E ignition"
    DESCRIPTION = (
        "Igniting network using external E2E controller and "
        + "with multiple POPs with different or same BGP peers"
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    def show_kvstore_prefixes(
        self,
        node_ids: List[int],
    ) -> None:
        command_kvstore_prefix: str = "breeze kvstore prefixes"
        futures: Dict = self.run_cmd(command_kvstore_prefix, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_kvstore_prefix} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_kvstore_prefix} in Node {result['node_id']}:\n{result['message']}"
            )

    def show_bgp_neighbor_summary(
        self,
        node_ids: List[int],
    ) -> None:
        command_bgp_cli: str = "exabgpcli show neighbor summary"
        futures: Dict = self.run_cmd(command_bgp_cli, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_bgp_cli} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_bgp_cli} in Node {result['node_id']}:\n{result['message']}"
            )

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()

        steps.extend(
            [
                {
                    "name": "Show BGP Neighbor Summary in POP nodes",
                    "function": self.show_bgp_neighbor_summary,
                    "function_args": (self.test_options["pop_node_ids"],),
                    "success_msg": "Showed BGP Neighbor Summary Successfully ",
                    "continue_on_failure": True,
                },
                {
                    "name": "Show KV Store Prefixes in POP nodes",
                    "function": self.show_kvstore_prefixes,
                    "function_args": (self.test_options["pop_node_ids"],),
                    "success_msg": "Showed KV Store Prefixes Successfully ",
                    "continue_on_failure": True,
                },
            ]
        )

        steps.extend(
            self.steps_ping_lo_all_tg_nodes_from_src(
                src_node_id=self.test_options["ping_all_src_node_id"],
                skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                is_cont_on_fail=True,
                is_concurrent=False,
            )
        )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
