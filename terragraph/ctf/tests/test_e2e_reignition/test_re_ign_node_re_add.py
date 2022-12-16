#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Any, Dict, List, Optional

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestX86TGReIgnNodeReAdd(TestX86TGIgn):
    TEST_NAME = "E2E Re-ignition"
    DESCRIPTION = "Delete a node, its links and re-add them back before verifying re-ignition in fig8 network"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.action_data = self.test_options["action_data"]

    def return_step_show_topology_and_verify(
        self,
        add_step_name: str,
        apply_filter: Optional[str] = "",
        expected_num_nodes: Optional[int] = 0,
        expected_num_links: Optional[int] = 0,
        is_cont_on_fail: Optional[bool] = False,
        is_concurrent: Optional[bool] = False,
        start_delay: Optional[int] = 0,
    ) -> Dict:
        return {
            "name": f"Show topology {add_step_name}",
            "function": self.show_topology_and_verify,
            "function_args": (
                apply_filter,
                expected_num_nodes,
                expected_num_links,
            ),
            "success_msg": f"Showed topology {add_step_name}",
            "continue_on_failure": is_cont_on_fail,
            "concurrent": is_concurrent,
            "delay": start_delay,
        }

    def return_step_service_request_api(
        self,
        add_step_name: str,
        api_name: str,
        api_data: Optional[Dict[str, Any]] = None,
        is_cont_on_fail: Optional[bool] = False,
        is_concurrent: Optional[bool] = False,
        start_delay: Optional[int] = 0,
    ) -> Dict:
        return {
            "name": f"e2e rest API to {add_step_name}",
            "function": self.api_service_request,
            "function_args": (
                api_name,
                api_data,
            ),
            "success_msg": f"Called e2e rest API to {add_step_name}",
            "continue_on_failure": is_cont_on_fail,
            "concurrent": is_concurrent,
            "delay": start_delay,
        }

    def return_steps_re_add_node_action(
        self,
        data: Dict,
        e2e_ctrl_node_id: List[int],
        itr_str: str,
    ) -> List[Dict]:

        # retrieve link name from input test data
        link1_name = f"{data['delete_link1']['aNodeName']}<-->{data['delete_link1']['zNodeName']}"
        link2_name = f"{data['delete_link2']['aNodeName']}<-->{data['delete_link2']['zNodeName']}"
        node_name = data["delete_node"]["nodeName"]
        return [
            self.return_step_service_request_api(
                add_step_name=f"Disable auto ignition{itr_str}",
                api_name="setIgnitionState",
                api_data={"enable": False},
            ),
            self.return_step_service_request_api(
                add_step_name=f"link down {link1_name}{itr_str}",
                api_name="setLinkStatus",
                api_data=data["link1_down"],
            ),
            self.return_step_service_request_api(
                add_step_name=f"link down {link2_name}{itr_str}",
                api_name="setLinkStatus",
                api_data=data["link2_down"],
            ),
            self.return_step_show_topology_and_verify(
                add_step_name=f"{itr_str}",
            ),
            self.return_step_service_request_api(
                add_step_name=f"delete link {link1_name}{itr_str}",
                api_name="delLink",
                api_data=data["delete_link1"],
            ),
            self.return_step_service_request_api(
                add_step_name=f"delete link {link2_name}{itr_str}",
                api_name="delLink",
                api_data=data["delete_link2"],
            ),
            self.return_step_show_topology_and_verify(
                add_step_name=f"and verify expected links=5{itr_str}",
                apply_filter="links",
                expected_num_links=5,
            ),
            self.return_step_service_request_api(
                add_step_name=f"delete node{node_name}{itr_str}",
                api_name="delNode",
                api_data=data["delete_node"],
            ),
            self.return_step_show_topology_and_verify(
                add_step_name=f"and verify expected nodes=5 after 30 secs{itr_str}",
                apply_filter="nodes",
                expected_num_nodes=5,
                start_delay=30,
            ),
            self.return_step_service_request_api(
                add_step_name=f"add node {node_name}{itr_str}",
                api_name="addNode",
                api_data=data["add_node"],
            ),
            self.return_step_show_topology_and_verify(
                add_step_name=f"and verify expected nodes=6 after 30 secs{itr_str}",
                apply_filter="nodes",
                expected_num_nodes=6,
                start_delay=30,
            ),
            self.return_step_service_request_api(
                add_step_name=f"add link {link1_name}{itr_str}",
                api_name="addLink",
                api_data=data["add_link1"],
            ),
            self.return_step_service_request_api(
                add_step_name=f"add link {link2_name}{itr_str}",
                api_name="addLink",
                api_data=data["add_link2"],
            ),
            self.return_step_service_request_api(
                add_step_name=f"Enable auto ignition after 90 secs{itr_str}",
                api_name="setIgnitionState",
                api_data={"enable": True},
                start_delay=90,
            ),
            {
                "name": f"ReCheck that the network is entirely up after 120 secs{itr_str}",
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
                "delay": 120,
            },
        ]

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        e2e_ctrl_node_id = self.find_x86_tg_host_id()
        num_itrns = self.test_options["action_iterations"]
        for i in range(num_itrns):
            if num_itrns > 1:
                itr_str: str = f"(iteration {i + 1} of {num_itrns})"
            else:
                itr_str: str = ""

            steps.extend(
                self.return_steps_re_add_node_action(
                    data=self.action_data,
                    # pyre-fixme[6]: Expected `List[int]` for 2nd param but got `int`.
                    e2e_ctrl_node_id=e2e_ctrl_node_id,
                    itr_str=itr_str,
                )
            )
            steps.extend(
                self.steps_ping_lo_all_tg_nodes_from_src(
                    src_node_id=self.test_options["ping_all_src_node_id"],
                    skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                    is_cont_on_fail=True,
                    is_concurrent=True,
                    start_delay=120,
                )
            )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
