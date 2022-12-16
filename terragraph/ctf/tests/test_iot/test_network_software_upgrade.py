#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from time import sleep
from typing import Dict, List

from terragraph.ctf.tests.test_iot.test_node_software_upgrade import TestIotNSU1

LOG = logging.getLogger(__name__)


class TestNetworkIotNSU2(TestIotNSU1):
    TEST_NAME = "NetworkIOTv2-NSU-2"
    DESCRIPTION = "Upgrade network excluding specified link and node which are down using OEM's E2E controller with BitTorrent."

    def build_test_steps(self, fail_during_upgrade: bool = False) -> List[Dict]:
        """ """
        steps = []
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        upgrade_timeout_s = self.test_args["upgrade_timeout_s"]

        # read test data configs
        test_data = json.load(open(self.test_args["test_data"]))
        node_to_fail = test_data["fail_node"]
        link_to_fail = test_data["fail_link"]
        expected_offline_network = test_data["expected_offline_network"]
        skip_nodes = expected_offline_network["nodes"]
        skip_links = expected_offline_network["links"]
        if "wait_to_fail_time" in self.test_args.keys():
            wait_to_fail_time = self.test_args["wait_to_fail_time"]
        else:
            wait_to_fail_time = 0

        # upgrade controller if x86_image is given
        if self.test_args["x86_image_path"]:
            steps.append(
                {
                    "name": "Push x86 image",
                    "function": self.push_x86_image,
                    "function_args": (self.test_args["x86_image_path"],),
                    "success_msg": "x86 image was upgraded.",
                }
            )
        steps.extend(
            [
                self.get_common_test_steps()["check_software_versions"],
                self.get_common_x86_test_steps()["setup_x86_services"],
                # upload tg image to controller
                {
                    "name": "Push Puma image to x86 host",
                    "function": self.push_tg_image_to_x86,
                    "function_args": (
                        self.test_args["upload_image_path"],
                        "tg-image.bin",
                    ),
                    "success_msg": "Puma image was uploaded.",
                },
                # upload oem image to controller
                {
                    "name": "Push OEM image to x86 host",
                    "function": self.push_tg_image_to_x86,
                    "function_args": (
                        self.test_args["upload_oem_image_path"],
                        "oem-image.bin",
                    ),
                    "success_msg": "OEM image was uploaded.",
                },
                # start bitTorrent tracker service
                self.get_common_x86_test_steps()["start_x86_bt_tracker"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Verify PUMA image is seeding",
                    "function": self._verify_tg_image_seeding,
                    "function_args": (self.test_args["upload_image_path"],),
                    "success_msg": "E2E controller is seeding the Puma image.",
                },
                {
                    "name": "Check if network is ignited",
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
                {
                    "name": "Wait 60 seconds for last node to apply node config overrides changes",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after node overrides take effect",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        120,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
                # get tg nodes in network expected to be online for upgrading
                {
                    "name": "Get puma nodes in network expected to be online",
                    "function": self._get_puma_nodes,
                    "function_args": (skip_nodes,),
                    "success_msg": "retrieved puma nodes",
                },
                {
                    "name": f"fail tg link {link_to_fail['name']} and node {node_to_fail['name']} before upgrade",
                    "function": self.fail_link_and_node,
                    "function_args": (
                        link_to_fail,
                        node_to_fail,
                    ),
                    "concurrent": fail_during_upgrade,
                    "delay": wait_to_fail_time,
                    "success_msg": "sucesfully brought down tg link and node",
                },
                {
                    "name": "Start upgrade of online puma nodes in network",
                    "function": self._upgrade_nodes,
                    "function_args": (
                        upgrade_timeout_s,
                        self.puma_nodes,
                    ),
                    "concurrent": fail_during_upgrade,
                    "success_msg": "Upgrade request for puma nodes was sent.",
                },
                {
                    "name": "Check that all online puma nodes are upgraded",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self._check_nodes_upgrade_status,
                        ([self.puma_nodes]),
                        5,
                        upgrade_timeout_s,
                    ),
                    "success_msg": "Puma nodes upgraded successfully.",
                    "error_handler": self.get_common_error_handler(),
                },
                # upgrade oem node in network after puma nodes complete upgrade
                {
                    "name": "Verify OEM image is seeding",
                    "function": self._verify_tg_image_seeding,
                    "function_args": (self.test_args["upload_oem_image_path"],),
                    "success_msg": "E2E controller is seeding the OEM image.",
                },
                {
                    "name": "Start upgrade of oem node",
                    "function": self._upgrade_nodes,
                    "function_args": (
                        upgrade_timeout_s,
                        [self.test_args["oem_node_name"]],
                    ),
                    "success_msg": "Upgrade request was sent for OEM node",
                },
                {
                    "name": "Check that OEM node is upgraded",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self._check_nodes_upgrade_status,
                        ([self.test_args["oem_node_name"]]),
                        5,
                        upgrade_timeout_s,
                    ),
                    "success_msg": "OEM node is upgraded successfully",
                    "error_handler": self.get_common_error_handler(),
                },
                {
                    "name": "Check if expected nodes and links are up after upgrade",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (
                            self.api_service_request,
                            ["getTopology"],
                            skip_nodes,
                            skip_links,
                        ),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Expected nodes and links are up after upgrade",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )
        return steps

    def fail_link_and_node(self, link_to_fail: Dict, node_to_fail: Dict):
        """
        bring down link specified in link_to_fail.
        stop minion on node specified in node_to_fail
        """

        link_name = link_to_fail["name"]
        initiator_mac = link_to_fail["initiator_mac"]
        responder_mac = link_to_fail["responder_mac"]

        # disable auto ignition on link
        self.api_set_link_ignition_state(link_name, False)

        # dissoc link and wait 40s before checking link state in controller
        self.api_force_dissoc(initiator_mac, responder_mac)
        sleep(40)

        # check link is down
        self.api_check_link_state(link_name, False)

        # stop minion on node and wait 40s before checking node state in controller
        self.tg_restart_minion([node_to_fail["id"]], "stop")
        sleep(40)

        # check node is offline
        self.api_check_node_state(node_to_fail["name"], False)

    def get_test_steps(self) -> List[Dict]:

        # Get steps for software upgrade where node and link fail before upgrade begins
        steps = self.build_test_steps()
        return steps


class TestNetworkIotNSU3(TestNetworkIotNSU2):
    TEST_NAME = "NetworkIOTv2-NSU-3"
    DESCRIPTION = "Upgrade network while specified link and node are brought down, using OEM's E2E controller with BitTorrent."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestNetworkIotNSU3, TestNetworkIotNSU3
        ).test_params()
        test_params["wait_to_fail_time"] = {
            "desc": (
                "time to wait after upgrade is started before failing node and link in network"
            ),
            "convert": int,
            "default": 120,
        }
        return test_params

    def get_test_steps(self) -> List[Dict]:

        # Get steps for software upgrade when node and link fail during the upgrade process
        steps = self.build_test_steps(True)
        return steps
