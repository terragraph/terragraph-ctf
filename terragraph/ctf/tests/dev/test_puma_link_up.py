#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaLinkUp(PumaTgCtfTest):
    TEST_NAME = "PUMA: Link Up"
    DESCRIPTION = "Bring up Terragraph links."
    LOG_FILES = ["/var/log/vpp/vnet.log", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "link-up-nodes-data-setup-{SETUP_ID}.json"

    def get_test_steps(self) -> List[Dict]:
        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
        ]


class TestTgPumaLinkUpKernel(TestTgPumaLinkUp):
    TEST_NAME = "PUMA: Link Up (Kernel)"
    DESCRIPTION = "Bring up DN-to-DN links with the kernel driver."

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        nodes_data_amend = super().nodes_data_amend(num_nodes)
        self.merge_dict(
            nodes_data_amend,
            {
                i: {"node_config": {"envParams": {"DPDK_ENABLED": "0"}}}
                for i in range(1, num_nodes + 1)
            },
        )
        return nodes_data_amend


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
