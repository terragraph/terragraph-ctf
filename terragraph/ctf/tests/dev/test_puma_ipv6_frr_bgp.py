#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaIpv6FrrBgp(PumaTgCtfTest):
    TEST_NAME = "PUMA: IPv6 BGP Routing in VPP mode using FRR"
    DESCRIPTION = "Bring up a POP-DN link and verify FRR BGP and Open/R operation."
    LOG_FILES = [
        "/var/log/fib_vpp/current",
        "/var/log/frr_bgp_healthcheck/current",
        "/var/log/frr_openr_sync/current",
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
                "name": "Check for learned BGP routes in FRR bgpd",
                "function": self.bgp_frr_bgpd_default_route_check,
                "function_args": (),
                "success_msg": "FRR bgpd has learned BGP default routes",
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


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
