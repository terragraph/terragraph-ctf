#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from time import sleep
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import TestFailed
from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIot

LOG = logging.getLogger(__name__)


class TestNetworkIotNIT1NIT2(TestNodeIot):
    TEST_NAME = "Network Ignition Test"
    DESCRIPTION = "Tests if OEM controller ignites topology described in setup json"

    def get_test_steps(self) -> List[Dict]:

        # read test data configs
        test_data = json.load(open(self.test_args["test_data"]))
        pop_node_id = test_data["ping_profile"]["pop_node_id"]
        nodes_ids = test_data["ping_profile"]["network_node_ids"]

        # ignite network using e2e controller
        steps = super().get_test_steps()

        # Run ping from POP node to all other nodes
        steps.extend(self.steps_ping_nodes_from_src(pop_node_id, nodes_ids))
        return steps


class TestNetworkIotNIT3(TestNodeIot):
    TEST_NAME = "Network Ignition Test with link failure"
    DESCRIPTION = "Tests if OEM controller ignites topology while links are brought down during ignition"

    def dissoc_links(self, links: List[Dict]):

        if not links:
            raise TestFailed(
                "No links defined in test_data to dissoc during network ignition"
            )

        # check if link is alive and then bring down link
        for link in links:
            link_name = link["link_name"]
            # wait till links are ignited
            self.try_until_timeout(self.api_check_link_state, (link_name,), 5, 300)

            # disable auto ignition on link
            self.api_set_link_ignition_state(link_name, False)
            sleep(2)

            # bring down link
            self.api_force_dissoc(link["initiator_mac"], link["responder_mac"])
            sleep(60)

            # check if link is down
            self.api_check_link_state(link_name, False)

            # enable auto ignition on link
            self.api_set_link_ignition_state(link_name)

    def get_test_steps(self) -> List[Dict]:

        # read test data configs
        test_data = json.load(open(self.test_args["test_data"]))
        links_to_dissoc = test_data["dissoc_links"]
        pop_node_id = test_data["ping_profile"]["pop_node_id"]
        nodes_ids = test_data["ping_profile"]["network_node_ids"]

        # ignite network using e2e controller
        steps = super().get_test_steps()

        # get ignition step index
        ignition_step_idx = self.get_ignition_step_idx(steps)

        # add step to check and dissoc links in before checking network state
        steps.insert(
            ignition_step_idx,
            {
                "name": "dissoc links during ignition",
                "function": self.dissoc_links,
                "function_args": (links_to_dissoc,),
                "success_msg": "Finished flapping the links.",
            },
        )

        # Run ping from POP node to all other nodes
        steps.extend(self.steps_ping_nodes_from_src(pop_node_id, nodes_ids))

        return steps


class TestNetworkIotNIT4(TestNodeIot):
    TEST_NAME = "Network Ignition Test with node failure"
    DESCRIPTION = (
        "Tests if OEM controller ignites topology while nodes are down during ignition"
    )

    def fail_nodes_during_ignition(self, nodes: List[dict]):

        if not nodes:
            raise TestFailed(
                "No nodes defined in test_data to fail during network ignition"
            )

        for node in nodes:
            node_name = node["node_name"]
            node_id = node["node_id"]

            # wait till node is online
            self.try_until_timeout(self.api_check_node_state, (node_name,), 5, 300)

            # bring down node by stopping e2e_minion
            self.tg_restart_minion([node_id], "stop")
            sleep(30)

            # check if node is offline
            self.api_check_node_state(node_name, False)

            # start e2e_minion on node
            self.tg_restart_minion([node_id], "start")

    def get_test_steps(self) -> List[Dict]:

        # read test data configs
        test_data = json.load(open(self.test_args["test_data"]))
        nodes_to_fail = test_data["nodes_to_fail"]
        pop_node_id = test_data["ping_profile"]["pop_node_id"]
        nodes_ids = test_data["ping_profile"]["network_node_ids"]

        # ignite network using e2e controller
        steps = super().get_test_steps()

        # get ignition step index
        ignition_step_idx = self.get_ignition_step_idx(steps)

        # add step to fail nodes before checking network state
        steps.insert(
            ignition_step_idx,
            {
                "name": "fail nodes during ignition",
                "function": self.fail_nodes_during_ignition,
                "function_args": (nodes_to_fail,),
                "success_msg": "Finished flapping nodes.",
            },
        )

        # Run ping from POP node to all other nodes
        steps.extend(self.steps_ping_nodes_from_src(pop_node_id, nodes_ids))

        return steps


class TestNetworkIotNIT5(TestNodeIot):
    TEST_NAME = "Network Ignition test with node failure after ignition"
    DESCRIPTION = (
        "Tests if OEM controller ignites topology followed"
        " by node failure to verify if controller recovers the nodes"
    )

    def fail_nodes_after_ignition(self, nodes: List[dict]):

        if not nodes:
            raise TestFailed(
                "No nodes defined in test_data to fail after network ignition"
            )

        for node in nodes:
            node_name = node["node_name"]
            node_id = node["node_id"]

            # check if node is online
            self.api_check_node_state(node_name)

            # bring down node by stopping e2e_minion
            self.tg_restart_minion([node_id], "stop")
            self.log_to_ctf("waiting 30s before check node state")
            sleep(30)

            # check if node is offline
            self.api_check_node_state(node_name, False)

            # start e2e_minion on node
            self.tg_restart_minion([node_id], "start")

    def get_test_steps(self) -> List[Dict]:

        # read test data configs
        test_data = json.load(open(self.test_args["test_data"]))
        nodes_to_fail = test_data["nodes_to_fail"]
        pop_node_id = test_data["ping_profile"]["pop_node_id"]
        nodes_ids = test_data["ping_profile"]["network_node_ids"]
        ignition_timeout_s = self.test_args["ignition_timeout_s"]

        # ignite network using e2e controller
        steps = super().get_test_steps()

        # fail nodes and check if they reignite
        steps.extend(
            [
                {
                    "name": "fail nodes after network is ignited",
                    "function": self.fail_nodes_after_ignition,
                    "function_args": (nodes_to_fail,),
                    "success_msg": "Finished flapping nodes.",
                },
                {
                    "name": "Check if network is ignited after node failure",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )

        # Run ping from POP node to all other nodes
        steps.extend(self.steps_ping_nodes_from_src(pop_node_id, nodes_ids))

        return steps
