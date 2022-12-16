#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaTopoScan(PumaTgCtfTest):
    TEST_NAME = "PUMA: Topology Scan"
    DESCRIPTION = "Run a topology scan and verify results."
    LOG_FILES = ["/var/log/vpp/vnet.log", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "link-up-nodes-data-setup-{SETUP_ID}.json"
    NODES_DATA_OPTIONAL = True

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgPumaTopoScan, TestTgPumaTopoScan
        ).test_params()
        test_params["initiator_id"] = {
            "desc": "Initiator node ID in the CTF setup (optional)",
            "default": None,
            "convert": int,
        }
        test_params["initiator_mac"] = {
            "desc": "Initiator MAC address (optional)",
            "default": None,
        }
        return test_params

    def get_test_steps(self) -> List[Dict]:
        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            {
                "name": "Run topology scan",
                "function": self.tg_run_topo_scan,
                "function_args": (
                    self.test_args["initiator_id"],
                    self.test_args["initiator_mac"],
                ),
                "success_msg": "Topology scan was successful",
                "error_handler": self.get_common_error_handler(),
            },
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
