#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaVxlanL2(PumaTgCtfTest, x86TrafficGenCtfTest):
    TEST_NAME = "PUMA: VxLAN L2 tunneling in VPP mode"
    DESCRIPTION = (
        "Setup bi-directional POP-CN VxLAN tunnels and test IPv4 connectivity."
    )
    LOG_FILES = [
        "/var/log/fib_vpp/current",
        "/var/log/openr/current",
        "/var/log/vpp/vnet.log",
        "/var/log/e2e_minion/current",
        "/var/log/tunnel_monitor/current",
    ]
    NODES_DATA_FORMAT = "vxlan-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgPumaVxlanL2, TestTgPumaVxlanL2
        ).test_params()

        PumaTgCtfTest.merge_dict(test_params, x86TrafficGenCtfTest.test_params())
        return test_params

    def get_test_steps(self) -> List[Dict]:
        return [
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
            self.COMMON_TEST_STEPS["wait_for_loopback_ipv6_addr"],
            self.COMMON_TEST_STEPS["setup_l2_tunnels"],
            self.COMMON_TEST_STEPS["check_openr_adjacencies"],
            self.COMMON_TEST_STEPS["ping_all_nodes_link_local"],
            {
                "name": "Check VxLAN L2 tunnels in VPP",
                "function": self.vxlan_vpp_check,
                "function_args": (),
                "success_msg": "VxLAN L2 tunnels are enabled in VPP",
            },
            {
                "name": "Ping CPE to CPE across terra link",
                "function": self.cpe_ping,
                "function_args": (3, 4, "eth7", "eth6", "eth7", "eth6", False),
                "success_msg": "CPE to CPE ping successful",
            },
            self.COMMON_TEST_STEPS["disable_l2_tunnels"],
            {
                "name": "Ping CPE to CPE across terra link",
                "function": self.cpe_ping,
                "function_args": (3, 4, "eth7", "eth6", "eth7", "eth6", False),
                "success_msg": "CPE to CPE ping failed",
                "negate_result": True,
            },
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
