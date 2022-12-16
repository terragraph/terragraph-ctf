#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List

from terragraph.ctf.tests.routing.routing_helper import RoutingUtils
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn


LOG = logging.getLogger(__name__)


class TestTgRouteLinkDown(RoutingUtils, TestX86TGIgn):
    TEST_NAME = "Routing"
    DESCRIPTION = "Link down re-route convergence time test"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        attenuator_setup_steps: List[Dict] = [
            {
                "name": "Disable attenuation in all attenuators with value 0",
                "function": self.attenuator_odroid_set_value,
                "function_args": (self.test_options["attenuator_all_nodes"], 0),
                "success_msg": "Disabled attenuation in all odroid attenuator nodes",
                "continue_on_failure": True,
            },
            {
                "name": "Stop attenuator service in all attenuators",
                "function": self.attenuator_odroid_service,
                "function_args": (
                    self.test_options["attenuator_all_nodes"],
                    "stop",
                ),
                "success_msg": "Stopped attenuator service in all odroid attenuator nodes",
                "continue_on_failure": True,
            },
            {
                "name": "Verify for matching date timestamps in host and attenuator device",
                "function": self.verify_date_time_in_attenuator_odroid,
                "function_args": (self.test_options["attenuator_action_nodes"],),
                "success_msg": "Verified for matching date timestamps in host and attenuator device",
                "continue_on_failure": True,
            },
        ]
        steps = attenuator_setup_steps + steps
        steps.extend(
            self.steps_ping_lo_all_tg_nodes_from_src(
                src_node_id=self.test_options["ping_all_src_node_id"],
                skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                is_cont_on_fail=True,
                is_concurrent=True,
            )
        )
        action_ping_duration_s = self.test_options["action"]["ping_duration_s"]
        action_ping_interval_s = self.test_options["action"]["ping_interval_s"]
        steps.extend(
            [
                {
                    "name": f"Ping Over lo link from node {self.test_options['action']['node_names'][0]}"
                    + f" to {self.test_options['action']['node_names'][1]}",
                    "function": self.ping_nodes,
                    "function_args": (
                        self.test_options["action"]["nodes"][0],
                        self.test_options["action"]["nodes"][1],
                        "lo",
                        "global",
                        int(action_ping_duration_s / action_ping_interval_s),
                        1,
                        action_ping_interval_s,
                    ),
                    "success_msg": "Ping Over lo link from src node to dest node  succeeded",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": True,
                    "concurrent": True,
                },
                {
                    "name": f"Set attenuation value to {self.test_options['attenuation_value']} "
                    + f"in attenuator node(s) {self.test_options['attenuator_action_nodes']} after delay 120 secs",
                    "function": self.attenuator_odroid_set_value,
                    "function_args": (
                        self.test_options["attenuator_action_nodes"],
                        self.test_options["attenuation_value"],
                    ),
                    "success_msg": "successfully set attenuation value in attenuator nodes",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 120,
                },
                {
                    "name": "Show topology after delay 150 secs",
                    "function": self.show_topology_and_verify,
                    "function_args": (),
                    "success_msg": "Showed topology",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 150,
                },
                {
                    "name": f"Disable attenuation value in attenuator node(s) {self.test_options['attenuator_action_nodes']}",
                    "function": self.attenuator_odroid_set_value,
                    "function_args": (
                        self.test_options["attenuator_action_nodes"],
                        0,
                    ),
                    "success_msg": "successfully disabled attenuation in attenuator nodes",
                    "continue_on_failure": True,
                },
                {
                    "name": "Verify route convergence time",
                    "function": self.verify_route_test_results,
                    "function_args": (
                        self.test_options["action"]["event"],
                        self.test_options["setup_tg_nodes_fig8"],
                        self.test_options["action"]["nodes"],
                        self.test_options["action"]["re_route_finish_time_s"],
                    ),
                    "success_msg": "Verified route convergence time",
                    "continue_on_failure": True,
                },
                {
                    "name": "ReCheck network is up",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        600,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": True,
                },
                {
                    "name": "Show e2e controller service log",
                    "function": self.get_service_logs,
                    "function_args": ("e2e_controller",),
                    "success_msg": "Showed e2e controller service log",
                },
                {
                    "name": "Show open-R current logs",
                    "function": self.show_openr_current_logs,
                    "function_args": (),
                    "success_msg": "Showed open-R current log",
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
