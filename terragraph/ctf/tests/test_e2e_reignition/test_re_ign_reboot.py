#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestX86TGReIgnReboot(TestX86TGIgn):
    TEST_NAME = "E2E Re-ignition"
    DESCRIPTION = "Reboot the terragraph node(s) either by API or command before verifying re-ignition"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.action_data = self.test_options["action_data"]

    def print_uptime(self, node_ids: List[int]) -> None:
        command_uptime: str = "uptime -p"
        futures: Dict = self.run_cmd(command_uptime, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_uptime} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(f"uptime in Node {result['node_id']}:\n{result['message']}")

    def return_steps_reboot_action(
        self,
        test_options: Dict,
        itr_str: str,
        is_rest_api_reboot: Optional[bool] = False,
    ) -> List[Dict]:
        return [
            {
                "name": f"Get uptime before reboot {itr_str}",
                "function": self.print_uptime,
                "function_args": (test_options["action_node_ids"],),
                "success_msg": f"returned uptime before reboot {itr_str}",
                "continue_on_failure": True,
            },
            (
                {
                    "name": f"Call e2e rest API to reboot node(s){itr_str}",
                    "function": self.api_service_request,
                    "function_args": (
                        "rebootNode",
                        self.action_data,
                    ),
                    "success_msg": f"Called e2e rest API to reboot node(s){itr_str}",
                    "continue_on_failure": True,
                }
                if is_rest_api_reboot
                else {
                    "name": f"Regular Reboot of node(s) without API {itr_str}",
                    "function": self.reboot_and_wait,
                    "function_args": (
                        self.device_info,
                        0.0,
                        "terragraph",
                        test_options["action_node_ids"],
                    ),
                    "success_msg": f"Issued regular reboot {itr_str}",
                    "continue_on_failure": True,
                }
            ),
            {
                "name": f"Get uptime after reboot and 300 secs delay{itr_str}",
                "function": self.print_uptime,
                "function_args": (test_options["action_node_ids"],),
                "success_msg": f"returned uptime after reboot {itr_str}",
                "continue_on_failure": True,
                "delay": 300,
            },
            {
                "name": f"ReCheck that the network is entirely up after 300 secs{itr_str}",
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
                "delay": 300,
            },
        ]

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        num_itrns = self.test_options["action_iterations"]
        for i in range(num_itrns):
            if num_itrns > 1:
                itr_str: str = f"(iteration {i + 1} of {num_itrns})"
            else:
                itr_str: str = ""
            steps.extend(
                self.return_steps_reboot_action(
                    test_options=self.test_options,
                    itr_str=itr_str,
                    is_rest_api_reboot=(
                        self.test_options["action"] == "rest_api_reboot_node"
                    ),
                )
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
