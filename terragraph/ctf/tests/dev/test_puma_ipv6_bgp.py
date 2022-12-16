#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaIpv6BGP(PumaTgCtfTest):
    TEST_NAME = "PUMA: IPv6 BGP Routing in VPP mode"
    DESCRIPTION = "Bring up a POP-DN link and verify BGP and Open/R operation."
    LOG_FILES = [
        "/var/log/fib_vpp/current",
        "/var/log/exabgp/current",
        "/var/log/openr/current",
        "/var/log/vpp/vnet.log",
        "/var/log/e2e_minion/current",
    ]
    NODES_DATA_FORMAT = "pop-nodes-data-setup-{SETUP_ID}.json"

    def get_test_steps(self) -> List[Dict]:
        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Check POP config",
                "function": self.verify_pop_bgp_config,
                "function_args": (),
                "success_msg": "Found a valid POP with BGP config",
            },
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
            self.COMMON_TEST_STEPS["add_loopback_ipv6_addr"],
            self.COMMON_TEST_STEPS["wait_for_loopback_ipv6_addr"],
            self.COMMON_TEST_STEPS["check_openr_adjacencies"],
            self.COMMON_TEST_STEPS["ping_all_nodes_link_local"],
            {
                "name": "Check for learned BGP routes in ExaBGP",
                "function": self.bgp_exabgp_default_route_check,
                "function_args": (),
                "success_msg": "ExaBGP has learned BGP default routes",
            },
            {
                "name": "Check for learned BGP routes in Open/R",
                "function": self.bgp_openr_default_route_check,
                "function_args": (),
                "success_msg": "Open/R has learned BGP default routes",
            },
            {
                "name": "Check VPP or Linux FIB for valid next hops",
                "function": self.bgp_default_route_check,
                "function_args": (),
                "success_msg": "VPP or LinuxFIB has valid next hops",
            },
            {
                "name": "Ping upstream GW and Router",
                "function": self.verify_ping_upstream,
                "function_args": (),
                "success_msg": "All nodes can ping GW and router",
            },
        ]


class TestTgPumaIpv6BGPKernel(TestTgPumaIpv6BGP):
    TEST_NAME = "PUMA: IPv6 BGP Routing in Kernel Mode"
    DESCRIPTION = "Bring up a POP-DN link and verify BGP and Open/R operation."
    LOG_FILES = [
        "/var/log/fib_linux/current",
        "/var/log/exabgp/current",
        "/var/log/openr/current",
        "/var/log/e2e_minion/current",
    ]

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        nodes_data_amend = super().nodes_data_amend(num_nodes)
        self.merge_dict(
            nodes_data_amend,
            {
                i: {
                    "node_config": {
                        "envParams": {"DPDK_ENABLED": "0", "OPENR_USE_FIB_VPP": "0"}
                    }
                }
                for i in range(1, num_nodes + 1)
            },
        )
        self.merge_dict(
            nodes_data_amend, {1: {"node_config": {"popParams": {"POP_IFACE": "nic1"}}}}
        )
        return nodes_data_amend


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
