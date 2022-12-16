#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceConfigError
from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgE2ENetworkUpInternal(PumaTgCtfTest):
    TEST_NAME = "PUMA: E2E Network Up (Internal Controller)"
    DESCRIPTION = "Bring up all links in a network using an internal E2E controller."
    LOG_FILES = ["/var/log/e2e_controller/current", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "e2e-internal-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgE2ENetworkUpInternal, TestTgE2ENetworkUpInternal
        ).test_params()
        test_params["ignition_timeout_s"] = {
            "desc": "How many seconds should we wait for the network to come up?",
            "default": 180.0,
            "convert": float,
        }
        test_params["remove_python"]["default"] = True
        return test_params

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        d: Dict = {
            i: {"lo": {"ip": f"{2000 + i}::1/128"}} for i in range(1, num_nodes + 1)
        }
        d[1]["node_config"] = {
            "kvstoreParams": {
                "e2e-ctrl-url": "tcp://[2001::1]:7007",
                "e2e-network-prefix": "2001::/56,64",
            }
        }
        return d

    def _get_controller_query_node(self) -> int:
        """Find a node_id with an "e2e_controller" field in the node data."""
        node_id = next(
            (k for k, v in self.nodes_data.items() if "e2e_controller" in v), None
        )
        if node_id is None:
            raise DeviceConfigError("Missing 'e2e_controller' field in node data")
        if "topology" not in self.nodes_data[node_id]["e2e_controller"]:
            raise DeviceConfigError(
                "Missing 'e2e_controller.topology' field in node data"
            )
        return int(node_id)

    def get_test_steps(self) -> List[Dict]:
        node_id = self._get_controller_query_node()
        e2e_configs = self.nodes_data[node_id]["e2e_controller"].get("configs", {})
        topology = self.nodes_data[node_id]["e2e_controller"]["topology"]

        ignition_timeout_s = self.test_args["ignition_timeout_s"]

        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["add_loopback_ipv6_addr"],
            {
                "name": f"Wipe E2E controller config files on node {node_id}",
                "function": self.wipe_controller_config_files,
                "function_args": (node_id,),
                "success_msg": "All controller config files deleted",
            },
            {
                "name": f"Copy E2E config files to node {node_id}",
                "function": self.set_e2e_config_files,
                "function_args": (node_id, e2e_configs),
                "success_msg": "E2E config file(s) were sent",
            },
            {
                "name": f"Copy E2E topology file to node {node_id}",
                "function": self.set_topology_file,
                "function_args": (node_id, topology),
                "success_msg": "Topology file was sent",
            },
            {
                "name": f"Start E2E controller on node {node_id}",
                "function": self.start_e2e_controller,
                "function_args": (node_id,),
                "success_msg": "E2E controller is running",
            },
            {
                "name": "Wait 5 seconds for controller to initialize",
                "function": sleep,
                "function_args": (5,),
                "success_msg": "Finished waiting",
            },
            {
                "name": "Check that the network is entirely up",
                "function": self.try_until_timeout,
                "function_args": (
                    self.controller_verify_topology_up,
                    (self.get_controller_topology,),
                    5,
                    ignition_timeout_s,
                ),
                "success_msg": "Network is up",
                "error_handler": self.get_common_error_handler(),
            },
        ]


class TestTgE2ENetworkUpExternal(PumaTgCtfTest):
    TEST_NAME = "PUMA: E2E Network Up (External Controller)"
    DESCRIPTION = "Bring up all links in a network using an external E2E controller."
    LOG_FILES = ["/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "e2e-external-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgE2ENetworkUpExternal, TestTgE2ENetworkUpExternal
        ).test_params()
        test_params["ignition_timeout_s"] = {
            "desc": (
                "How many seconds should we wait for the network to come up? "
                + "This may need to take into account the controller potentially "
                + "rebooting the nodes for a config update."
            ),
            "default": 600.0,
            "convert": float,
        }
        return test_params

    def get_test_steps(self) -> List[Dict]:
        if not any("e2e_controller" in v for v in self.nodes_data.values()):
            raise DeviceConfigError("Missing 'e2e_controller' field in node data")

        ignition_timeout_s = self.test_args["ignition_timeout_s"]

        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Check that the network is entirely up",
                "function": self.try_until_timeout,
                "function_args": (
                    self.controller_verify_topology_up,
                    (self.get_controller_topology,),
                    5,
                    ignition_timeout_s,
                ),
                "success_msg": "Network is up",
                "error_handler": self.get_common_error_handler(),
            },
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
