#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaIpv6Up(PumaTgCtfTest):
    TEST_NAME = "PUMA: IPv6 Up"
    DESCRIPTION = "Bring up a Terragraph link and verify IPv6 connectivity."
    LOG_FILES = ["/var/log/vpp/vnet.log", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "link-up-nodes-data-setup-{SETUP_ID}.json"

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        return {
            1: {"lo": {"ip": "69::1/128"}},
            2: {"lo": {"ip": "70::1/128"}},
        }

    def get_test_steps(self) -> List[Dict]:
        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
            self.COMMON_TEST_STEPS["add_loopback_ipv6_addr"],
            self.COMMON_TEST_STEPS["wait_for_loopback_ipv6_addr"],
            self.COMMON_TEST_STEPS["check_openr_adjacencies"],
            self.COMMON_TEST_STEPS["ping_all_nodes_link_local"],
        ]


class TestTgPumaIpv6UpKernel(TestTgPumaIpv6Up):
    TEST_NAME = "PUMA: IPv6 Up (Kernel)"
    DESCRIPTION = (
        "Bring up a DN-to-DN link and verify IPv6 connectivity with the Linux driver."
    )
    LOG_FILES = ["/var/log/e2e_minion/current"]

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
        return nodes_data_amend


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
