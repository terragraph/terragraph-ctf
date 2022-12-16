#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceConfigError, TestFailed
from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgDistributedIgnition(PumaTgCtfTest):
    TEST_NAME = "PUMA: Distributed Ignition"
    DESCRIPTION = "Bring up all links using the distributed ignition algorithm."
    LOG_FILES = ["/var/log/vpp/vnet.log", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "distributed-link-up-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgDistributedIgnition, TestTgDistributedIgnition
        ).test_params()
        test_params["ignition_timeout_s"] = {
            "desc": "How many seconds should we wait for links to come up?",
            "default": 180.0,
            "convert": float,
        }
        test_params["min_mcs"] = {
            "desc": "The minimum expected MCS level on healthy links without traffic",
            "default": 9,
            "convert": int,
        }
        test_params["mcs_timeout_s"] = {
            "desc": "How many seconds should we wait for links to settle on min_mcs?",
            "default": 60.0,
            "convert": float,
        }
        return test_params

    def _validate_nodes_data(self) -> None:
        """Make sure required config exists for distributed ignition."""
        for node_id in self.get_tg_devices():
            if node_id not in self.nodes_data:
                raise DeviceConfigError(f"Missing node data for node {node_id}")
            if "node_config" not in self.nodes_data[node_id]:
                raise DeviceConfigError(f"Missing node_config for node {node_id}")
            if "topologyInfo" not in self.nodes_data[node_id]["node_config"]:
                raise DeviceConfigError(f"Missing topologyInfo for node {node_id}")

    def _verify_distributed_ignition_links_up(self, node_ids: List[int]) -> None:
        """Verify that all links configured for distributed ignition (in
        'topologyInfo.neighborInfo') are actually up for the given nodes.
        """
        dumps = self.minion_get_link_status_dumps(node_ids)
        failed_links: int = 0
        for node_id, d in self.nodes_data.items():
            dump = dumps[node_id] or {}
            topology_info = d["node_config"]["topologyInfo"]
            node_name = topology_info["nodeName"]
            nbr_info = topology_info["neighborInfo"]
            for resp_mac, nbr_info in nbr_info.items():
                radio_mac = nbr_info["initiatorMac"]
                LOG.debug(
                    f"Node {node_id} ({node_name}): "
                    + f"Checking link: {radio_mac} -> {resp_mac}"
                )
                if (
                    resp_mac not in dump
                    or dump[resp_mac]["radioMac"] != radio_mac
                    or dump[resp_mac]["linkStatusType"] != 1  # LinkStatusType.LINK_UP
                ):
                    failed_links += 1
                    self.log_to_ctf(
                        f"Node {node_id} ({node_name}): "
                        + f"Expected link not up: {radio_mac} -> {resp_mac}",
                        "error",
                    )

        if failed_links > 0:
            raise TestFailed(f"{failed_links} link(s) are not up")

    def _verify_distributed_ignition_min_mcs(self, min_mcs: int) -> None:
        """Verify that all links configured for distributed ignition (in
        'topologyInfo.neighborInfo') meet a minimum MCS level.
        """
        node_to_resp_macs = {}
        for node_id, d in self.nodes_data.items():
            nbr_info = d["node_config"]["topologyInfo"]["neighborInfo"]
            node_to_resp_macs[node_id] = list(nbr_info.keys())

        node_to_mcs = self.tg_get_mcs(node_to_resp_macs)
        failed_links: int = 0
        for node_id, resp_to_mcs in node_to_mcs.items():
            node_name = self.nodes_data[node_id]["node_config"]["topologyInfo"][
                "nodeName"
            ]
            for resp_mac, mcs in resp_to_mcs.items():
                if mcs < min_mcs:
                    failed_links += 1
                    self.log_to_ctf(
                        f"Node {node_id} ({node_name}): "
                        + f"found low MCS to {resp_mac}: {mcs}",
                        "error",
                    )

        if failed_links > 0:
            raise TestFailed(f"{failed_links} link(s) do not meet MCS requirements")

    def get_test_steps(self) -> List[Dict]:
        self._validate_nodes_data()

        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        min_mcs = self.test_args["min_mcs"]
        mcs_timeout_s = self.test_args["mcs_timeout_s"]

        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Check that all links are up",
                "function": self.try_until_timeout,
                "function_args": (
                    self._verify_distributed_ignition_links_up,
                    (self.get_tg_devices(),),
                    5,
                    ignition_timeout_s,
                ),
                "success_msg": "All links are up",
                "error_handler": self.get_common_error_handler(),
            },
            self.COMMON_TEST_STEPS["check_openr_adjacencies"],
            {
                "name": f"Check that MCS on all links >= {min_mcs}",
                "function": self.try_until_timeout,
                "function_args": (
                    self._verify_distributed_ignition_min_mcs,
                    (min_mcs,),
                    5,
                    mcs_timeout_s,
                ),
                "success_msg": "All links have acceptable MCS",
            },
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
