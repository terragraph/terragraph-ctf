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


class TestP2PTraffic(PumaTgCtfTest, x86TrafficGenCtfTest):
    TEST_NAME = "PUMA: Test Puma P2P association with traffic run"
    DESCRIPTION = (
        "Test puma RF point to point link association and run "
        "traffic from x86 traffic generator (CPE device) "
        "over the wireless link."
    )
    LOG_FILES = [
        "/var/log/vpp/vnet.log",
        "/var/log/e2e_minion/current",
        "/var/log/openr/current",
        "/var/log/fib_vpp/current",
    ]
    NODES_DATA_FORMAT = "p2p-traffic-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestP2PTraffic, TestP2PTraffic
        ).test_params()

        PumaTgCtfTest.merge_dict(test_params, x86TrafficGenCtfTest.test_params())
        return test_params

    def post_test_init(self) -> None:
        super().post_test_init()
        self.read_traffic_gen_info()

    def get_test_steps(self) -> List[Dict]:
        return [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["ping_all_nodes_link_local"],
            {
                "name": "Ping CPE to CPE across terra link",
                "function": self.cpe_ping,
                "function_args": (3, 4, "eth7", "eth6"),
                "success_msg": "CPE to CPE ping successful",
            },
            {
                "name": "Run traffic",
                "function": self.run_traffic,
                "function_args": (
                    [
                        {
                            "from_device_id": 3,
                            "to_device_id": 4,
                            "from_netns": "eth7",
                            "to_netns": "eth6",
                            "bandwidth": 1000,
                            "threshold": {"throughput": 0.9, "lost datagrams": 0.01},
                            "port": 5002,
                            "traffic_type": "UDP",
                            "direction": "bi",
                            "packet_size": "1452",
                            "time": 60,
                        }
                    ]
                ),
                "success_msg": "CPE to CPE iperf successful",
            },
        ]


class TestP2PTrafficJumboFrame(TestP2PTraffic):
    TEST_NAME = "PUMA: Test Puma P2P association with jumbo frame traffic run"
    DESCRIPTION = (
        "Test puma RF point to point link association and run "
        "jumbo frame traffic from x86 traffic generator (CPE device) "
        "over the wireless link."
    )

    def get_test_steps(self) -> List[Dict]:
        test_steps = super().get_test_steps()[:-1]
        test_steps.extend(
            [
                {
                    "name": "Set CPE interfaces MTU",
                    "function": self.cpe_set_all_interfaces_mtu,
                    "function_args": (10000,),
                    "success_msg": "CPE interfaces set MTU successful",
                },
                {
                    "name": "Run jumbo frame traffic",
                    "function": self.run_traffic,
                    "function_args": (
                        [
                            {
                                "from_device_id": 6,
                                "to_device_id": 7,
                                "from_netns": "eth43",
                                "to_netns": "eth45",
                                "bandwidth": 10,
                                "threshold": {
                                    "throughput": 0.9,
                                    "lost datagrams": 0.01,
                                },
                                "port": 5002,
                                "traffic_type": "UDP",
                                "direction": "uni",
                                "packet_size": "9600",
                                "time": 10,
                            }
                        ]
                    ),
                    "success_msg": "CPE to CPE iperf successful",
                },
            ]
        )
        return test_steps

    def post_run(self) -> None:
        super().post_run()

        # Reset traffic generator interface MTUs
        self.cpe_set_all_interfaces_mtu(1500)


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
