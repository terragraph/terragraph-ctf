#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaIperfVpp(PumaTgCtfTest):
    TEST_NAME = "PUMA: iperf3 vpp"
    DESCRIPTION = "Test throughput with iperf3 over vpp."
    LOG_FILES = [
        "/var/log/vpp/vnet.log",
        "/var/log/e2e_minion/current",
        "/var/run/vpp/startup.conf",
    ]
    NODES_DATA_FORMAT = "link-up-nodes-data-setup-{SETUP_ID}.json"
    ULA_TEST_PREFIX = "fd00:face:b00c::{}/64"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(  # type: ignore
            TestTgPumaIperfVpp, TestTgPumaIperfVpp
        ).test_params()
        test_params["min_iperf_tput_bps"] = {
            "desc": "Minimum throughput required to pass this test in bits per second",
            "default": 1.4e9,
            "convert": float,
        }
        test_params["iperf_duration_s"] = {
            "desc": "iperf duration (in seconds)",
            "default": 60,
            "convert": int,
        }
        return test_params

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        return {
            i: {
                "node_config": {
                    "envParams": {
                        "VPP_ULA_TEST_PREFIX": self.ULA_TEST_PREFIX.format("")
                    },
                }
            }
            for i in range(1, num_nodes + 1)
        }

    def get_test_steps(self) -> List[Dict]:
        # derive unique test IPv6 addresses for each test node from node_id
        ula_test_addresses = {
            node_id: self.ULA_TEST_PREFIX.format(str(node_id))
            for node_id in self.get_tg_devices()
        }

        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            {
                "name": "Assign IP addresses in ULA prefix",
                "function": self.add_vpp_interface_addr,
                "function_args": (ula_test_addresses,),
                "success_msg": "Successfully assigned addresses in ULA prefix",
            },
            {
                "name": "Ping from within VPP",
                "function": self.vpp_ping,
                "function_args": (ula_test_addresses,),
                "success_msg": "Successfully pinged from VPP to VPP",
            },
            {
                "name": "Run iperf3",
                "function": self.run_iperf_vpp_to_vpp,
                "function_args": (
                    ula_test_addresses,
                    self.test_args["min_iperf_tput_bps"],
                    self.test_args["iperf_duration_s"],
                ),
                "success_msg": "Successfully run iperf3",
            },
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
