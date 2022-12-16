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


class TestTgRouteMCSChange(RoutingUtils, TestX86TGIgn):
    TEST_NAME = "Routing"
    DESCRIPTION = "MCS change re-route convergence time test"

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
        ]
        steps = attenuator_setup_steps + steps

        for config in self.test_options["configs"]:
            test_overrides = self.create_node_overrides(
                config,
                node_names=self.test_options["action"]["node_names"],
            )
            steps.append(
                {
                    "name": f"e2e rest API to Modify Node Overrides {config['description']}",
                    "function": self.api_service_request,
                    "function_args": (
                        "modifyNodeOverridesConfig",
                        test_overrides,
                    ),
                    "success_msg": "Called e2e rest API to Modify Node Overrides",
                    "continue_on_failure": True,
                }
            )
        steps.append(
            {
                "name": "ReCheck that network is up",
                "function": self.try_until_timeout,
                "function_args": (
                    self.controller_verify_topology_up,
                    (self.api_service_request, ["getTopology"]),
                    5,
                    300,
                ),
                "success_msg": "Network is up",
                "error_handler": self.get_common_error_handler(),
                "continue_on_failure": True,
                "delay": 120,
            }
        )
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
        steps.append(
            {
                "name": f"Ping Over lo link from node {self.test_options['action']['node_names'][0]}"
                + f" to {self.test_options['action']['node_names'][1]} after delay 30 secs",
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
            }
        )
        for index, link_config in enumerate(self.test_options["link_configs"]):
            test_overrides = self.create_node_overrides(
                link_config,
                node_names=[self.test_options["action"]["node_names"][index]],
            )
            steps.append(
                {
                    "name": f"e2e rest API to Modify Node Overrides {self.test_options['link_configs'][index]['description']}",
                    "function": self.api_service_request,
                    "function_args": (
                        "modifyNodeOverridesConfig",
                        test_overrides,
                    ),
                    "success_msg": "Called e2e rest API to Modify Node Overrides",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 90,
                },
            )
        steps.append(
            {
                "name": "Record host time after MCS config override on action node links",
                "function": self.record_host_time,
                "function_args": (),
                "success_msg": "Recorded host time",
                "continue_on_failure": True,
                "concurrent": True,
                "delay": 95,
            },
        )
        steps.extend(
            [
                {
                    "name": f"Show node config in nodes {(self.test_options['action']['nodes'])}"
                    + " after delay 300 secs",
                    "function": self.show_current_node_config,
                    "function_args": (
                        self.test_options["action"]["nodes"],
                        self.test_options["node_cfg_file_path"],
                    ),
                    "success_msg": "Issued command to show node config in nodes",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 300,
                },
                {
                    "name": "Show topology after delay 300 secs",
                    "function": self.show_topology_and_verify,
                    "function_args": (),
                    "success_msg": "Showed topology",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 300,
                },
                {
                    "name": "Verify route convergence time",
                    "function": self.verify_route_test_results,
                    "function_args": (
                        self.test_options["action"]["event"],
                        self.test_options["setup_tg_nodes_fig8"],
                        self.test_options["action"]["nodes"],
                        # not used in case of MCS_COST event
                        self.test_options["action"]["re_route_finish_time_s"],
                        # link metric config value of mcs 4 to 8
                        self.test_options["configs"][0]["value"],
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
