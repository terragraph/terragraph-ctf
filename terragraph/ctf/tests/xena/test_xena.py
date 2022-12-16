#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError
from terragraph.ctf.sit import SitPumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgXenaLinkUp(SitPumaTgCtfTest):
    TEST_NAME = "Xena Link Up"
    DESCRIPTION = "Bring up links for running xena traffic and for RFC 2544 compliance"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.selected_links = self.test_data["selected_links"]

    def bring_up_link(self, sel_link: Dict) -> None:

        self.minion_assoc(
            sel_link["initiator_id"],
            sel_link["initiator_mac"],
            sel_link["responder_mac"],
        )
        # Verify link is up and get ifname
        ifname: str = self.minion_get_link_interface(
            sel_link["initiator_id"],
            sel_link["initiator_mac"],
            sel_link["responder_mac"],
        )
        self.verify_ll_ping(sel_link["initiator_id"], ifname, 25)

    def show_vpp_interface_address(self, node_ids: List[int]) -> None:

        command_vpp_iface_address: str = "vppctl show int addr"

        futures: Dict = self.run_cmd(command_vpp_iface_address, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_vpp_iface_address} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_vpp_iface_address} in Node {result['node_id']}:\n{result['message']}"
            )

    def get_test_steps(self) -> List[Dict]:
        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
        ]
        for link_idx, link in enumerate(self.selected_links):
            initiator_id = link["initiator_id"]
            initiator_mac = link["initiator_mac"]
            responder_id = link["responder_id"]
            responder_mac = link["responder_mac"]
            link_str = f"link #{link_idx + 1}: {initiator_mac} -> {responder_mac}"
            steps.append(
                {
                    "name": f"Assoc, node {initiator_id} -> {responder_id}, {link_str}",
                    "function": self.bring_up_link,
                    "function_args": (link,),
                    "success_msg": "Assoc succeeded",
                    "continue_on_failure": True,
                    "error_handler": self.get_common_error_handler(),
                }
            )
        steps.append(
            {
                "name": f"Run lo ping from node {self.test_options['ping_src_node_id']}"
                + f" to {self.test_options['ping_dst_node_id']}",
                "function": self.ping_nodes,
                "function_args": (
                    self.test_options["ping_src_node_id"],
                    self.test_options["ping_dst_node_id"],
                ),
                "success_msg": "lo ping ran successfully",
            }
        )
        for node_id in self.test_options["action_node_ids"]:
            steps.append(
                {
                    "name": f"Show VPP interface address in node {node_id}",
                    "function": self.show_vpp_interface_address,
                    "function_args": ([node_id],),
                    "success_msg": "Showed VPP interface address",
                }
            )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
