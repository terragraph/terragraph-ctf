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


class TestX86TGReIgnCntrIf(TestX86TGIgn):
    TEST_NAME = "E2E Re-ignition"
    DESCRIPTION = (
        "Verifies network is up after controller's network interface is toggled"
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.action_data = self.test_options["action_data"]

    def send_ifconfig_command(
        self,
        node_ids: List[int],
        net_name_space: Optional[str] = "",
        is_controller_node: Optional[bool] = False,
        interface: Optional[str] = "",
        action: Optional[str] = "",
    ) -> None:

        command_ifconfig: str = f"ifconfig {interface} {action}"
        if net_name_space:
            nm_spc: str = f"ip netns exec {net_name_space}"
            command_ifconfig = f"{nm_spc} {command_ifconfig}"
        if is_controller_node:
            command_ifconfig = self._chroot_cmd(command_ifconfig)

        futures: Dict = self.run_cmd(command_ifconfig, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_ifconfig} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_ifconfig} in Node {result['node_id']}:\n{result['message']}"
            )

    def toggle_network_iface(
        self,
        node_ids: List[int],
        net_name_space: Optional[str] = "",
        is_controller_node: Optional[bool] = False,
        interface: Optional[str] = "",
        toggle_delay_s: Optional[int] = 300,
    ) -> None:
        """
        toggle the interface with one shot command with delay and interface up included.
        otherwise vNIC will go down first and thereafter not reachable remotely to bring
        the interface up again.
        """
        command_toggle: str = f"ifconfig {interface} down; sleep {toggle_delay_s}; ifconfig {interface} up;"
        if net_name_space:
            nm_spc: str = f"ip netns exec {net_name_space}"
            command_toggle = f"{nm_spc} {command_toggle}"
        if is_controller_node:
            command_toggle = self._chroot_cmd(command_toggle)

        futures: Dict = self.run_cmd(command_toggle, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_toggle} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_toggle} in Node {result['node_id']}:\n{result['message']}"
            )

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        iface_name = self.action_data["iface_name"]
        num_itrns = self.test_options["action_iterations"]
        e2e_ctrl_node_id = self.find_x86_tg_host_id()
        for i in range(num_itrns):
            if num_itrns > 1:
                itr_str: str = f"(iteration {i + 1} of {num_itrns})"
            else:
                itr_str: str = ""

            steps.extend(
                [
                    {
                        "name": f"Check ifconfig in e2e controller {itr_str}",
                        "function": self.send_ifconfig_command,
                        "function_args": (
                            [e2e_ctrl_node_id],
                            "",
                            False,
                            iface_name,
                        ),
                        "success_msg": f"returned ifconfig info. {itr_str}",
                        "continue_on_failure": True,
                    },
                    {
                        "name": f"Toggle network interface in e2e controller with down for 300 secs{itr_str}",
                        "function": self.toggle_network_iface,
                        "function_args": (
                            [e2e_ctrl_node_id],
                            "",
                            False,
                            iface_name,
                        ),
                        "success_msg": f"Successfully toggled network interface in e2e controller{itr_str}",
                        "continue_on_failure": True,
                        "concurrent": True,
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
            steps.append(
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
                }
            )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
