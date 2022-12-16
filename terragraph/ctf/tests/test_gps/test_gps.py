#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgGps(TestX86TGIgn):
    def get_test_steps(self) -> List[Dict]:

        # ignite network using e2e controller
        steps = super().get_test_steps()

        flap_gps_order = self.test_data.get("flap_gps_order")

        for i, flap_gps_step in enumerate(flap_gps_order):
            step_name = flap_gps_step.get("step_name")
            steps.extend(
                [
                    {
                        "name": f"{i}: {step_name}",
                        "function": self.flap_gps,
                        "function_args": (flap_gps_step,),
                        "success_msg": "step ran successfully",
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Wait 20 seconds",
                        "function": sleep,
                        "function_args": (20,),
                        "success_msg": "Finished waiting",
                    },
                ]
            )

        return steps

    def flap_gps(
        self, flap_gps_info: Dict, continue_on_failure: Optional[bool] = False
    ) -> None:
        """
        expected flap_gps is each dict inside the flap_gps_order array.
        Expects the following data format:
        ```
        "<flap_gps_order>": [
            {
                "step_name": "<step_name>",
                "node_ids": [3,4]<node_ids>,
                "switch_state": false -> to be used in switch_gpsd method,
                "check_links": [
                    {
                        "expected_link": "all -> to check all links in the topology, otherwise link_name link_NodeA_NodeZ",
                        "expected_link_state": true for alive, false for link_down
                    }
                ]
            }
        ]
        ```
        """
        node_ids: List[int] = flap_gps_info.get("node_ids")
        switch_state: bool = flap_gps_info.get("switch_state")
        check_links: List[Dict] = flap_gps_info.get("check_links")

        for node_id in node_ids:
            self.switch_gpsd(node_id, switch_state)

        self.log_to_ctf("Sleep 45 sec for changes to take effect")
        sleep(45)
        for check_link in check_links:
            expected_link = check_link.get("expected_link")
            expected_link_state = check_link.get("expected_link_state")

            if expected_link == "all" and expected_link_state is True:
                self.log_to_ctf("ReChecking network after gps flap.")
                self.try_until_timeout(
                    self.controller_verify_topology_up,
                    (self.api_service_request, ["getTopology"]),
                    5,
                    100,
                )
                break

            self.log_to_ctf(
                f"Checking Topology to ensure that the link: {expected_link} actually went down."
            )
            try:
                self.api_check_link_state(expected_link, expected_link_state)
            except TestFailed:
                if continue_on_failure:
                    pass
                else:
                    raise DeviceCmdError(
                        f"Failed to verify Link State. {expected_link}"
                    )


class TestTgGpsStr(SitPumaTgCtfTest):
    def lo_ping(
        self,
        dn_initiator_id: int,
        dn_initiator_mac: str,
        dn_responder_mac: str,
        count: int = 10,
        timeout: int = 20,
    ) -> None:

        self.log_to_ctf(f"Verify link is up and get ifname. v5 TIMEOUT {timeout}")

        # Verify link is up and get ifname

        ifname: str = self.minion_get_link_interface(
            dn_initiator_id, dn_initiator_mac, dn_responder_mac
        )

        # ping lo
        self.verify_ll_ping(dn_initiator_id, ifname, count, timeout=timeout)


class TestTgGpsStr1(TestTgGpsStr):
    def get_test_steps(self) -> List[Dict]:
        test_details = self.test_data.get("test_details")
        dn_initiator_id = test_details.get("dn_initiator_id")
        dn_responder_id = test_details.get("dn_responder_id")
        dn_initiator_mac = test_details.get("dn_initiator_mac")
        dn_responder_mac = test_details.get("dn_responder_mac")

        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Enable GPS on DN-I but not on DN-R -> Disable GPS on DNR",
                "function": self.switch_gpsd,
                "function_args": (
                    dn_responder_id,
                    False,
                ),
                "success_msg": "gpsd service stopped",
            },
            {
                "name": "Wait 20 seconds",
                "function": sleep,
                "function_args": (20,),
                "success_msg": "Finished waiting",
            },
            self.COMMON_TEST_STEPS["assoc_terra_links"],
        ]
        steps.extend(
            [
                {
                    "name": "FIRST verify_ll_ping",
                    "function": self.lo_ping,
                    "function_args": (
                        dn_initiator_id,
                        dn_initiator_mac,
                        dn_responder_mac,
                    ),
                    "success_msg": "verified_ll_ping",
                },
                {
                    "name": "disassociate",
                    "function": self.minion_dissoc,
                    "function_args": (
                        dn_initiator_id,
                        dn_initiator_mac,
                        dn_responder_mac,
                    ),
                    "success_msg": "Dissociated",
                },
                {
                    "name": "Enable GPS on DN-R",
                    "function": self.switch_gpsd,
                    "function_args": (
                        dn_responder_id,
                        True,
                    ),
                    "success_msg": "gpsd service started",
                },
                self.COMMON_TEST_STEPS["assoc_terra_links"],
                {
                    "name": "SECOND verify_ll_ping, 60sec",
                    "function": self.lo_ping,
                    "function_args": (
                        dn_initiator_id,
                        dn_initiator_mac,
                        dn_responder_mac,
                        60,
                        65,
                    ),
                    "success_msg": "verified_ll_ping",
                },
                {
                    "name": "disassociate",
                    "function": self.minion_dissoc,
                    "function_args": (
                        dn_initiator_id,
                        dn_initiator_mac,
                        dn_responder_mac,
                    ),
                    "success_msg": "Dissociated",
                },
                {
                    "name": "Wait 20 seconds",
                    "function": sleep,
                    "function_args": (20,),
                    "success_msg": "Finished waiting",
                },
                self.COMMON_TEST_STEPS["assoc_terra_links"],
                {
                    "name": "THIRD verify_ll_ping 80 sec. in parallel",
                    "function": self.lo_ping,
                    "function_args": (
                        dn_initiator_id,
                        dn_initiator_mac,
                        dn_responder_mac,
                        80,
                        95,
                    ),
                    "success_msg": "verified_ll_ping",
                    "concurrent": True,
                },
                {
                    "name": "Disable GPS on DN-R.",
                    "function": self.switch_gpsd,
                    "function_args": (
                        dn_responder_id,
                        False,
                    ),
                    "success_msg": "gpsd service stopped",
                    "concurrent": True,
                    "delay": 10,
                },
                {
                    "name": "Enable GPS on DN-R.",
                    "function": self.switch_gpsd,
                    "function_args": (
                        dn_responder_id,
                        True,
                    ),
                    "success_msg": "gpsd service started",
                    "concurrent": True,
                    "delay": 50,
                },
            ]
        )

        return steps


class TestTgGpsStr2(TestTgGpsStr):
    def get_test_steps(self) -> List[Dict]:
        test_details = self.test_data.get("test_details")
        dn_initiator_id = test_details.get("dn_initiator_id")
        dn_responder_id = test_details.get("dn_responder_id")
        dn_initiator_mac = test_details.get("dn_initiator_mac")
        dn_responder_mac = test_details.get("dn_responder_mac")

        steps = [
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Enable GPS on DN-I but not on DN-R -> Disable GPS on DNR",
                "function": self.switch_gpsd,
                "function_args": (
                    dn_responder_id,
                    False,
                ),
                "success_msg": "gpsd service stopped",
            },
            {
                "name": "Wait 20 seconds",
                "function": sleep,
                "function_args": (20,),
                "success_msg": "Finished waiting",
            },
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            {
                "name": "FIRST verify_ll_ping",
                "function": self.lo_ping,
                "function_args": (
                    dn_initiator_id,
                    dn_initiator_mac,
                    dn_responder_mac,
                ),
                "success_msg": "verified_ll_ping",
            },
            {
                "name": "disassociate",
                "function": self.minion_dissoc,
                "function_args": (
                    dn_initiator_id,
                    dn_initiator_mac,
                    dn_responder_mac,
                ),
                "success_msg": "Dissociated",
            },
            {
                "name": "Enable GPS on DN-R",
                "function": self.switch_gpsd,
                "function_args": (
                    dn_responder_id,
                    True,
                ),
                "success_msg": "gpsd service started",
            },
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            {
                "name": "SECOND verify_ll_ping",
                "function": self.lo_ping,
                "function_args": (
                    dn_initiator_id,
                    dn_initiator_mac,
                    dn_responder_mac,
                    100,
                    120,
                ),
                "success_msg": "verified_ll_ping",
                "concurrent": True,
            },
        ]

        return steps


class TestTgGps_6_1(SitPumaTgCtfTest):
    def get_test_steps(self) -> List[Dict]:
        test_details = self.test_data.get("test_details")
        dn_initiator_id = test_details.get("dn_initiator_id")
        dn_responder_id = test_details.get("dn_responder_id")
        steps = [
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Bring Up Link DN-I <--> DN-R",
                "function": self.tg_assoc_links,
                "function_args": (dn_initiator_id,),
                "success_msg": "Link Up",
            },
            {
                "name": "Bring Up Link DN-R <--> CN-1",
                "function": self.tg_assoc_links,
                "function_args": (dn_responder_id,),
                "success_msg": "Link Up",
            },
        ]
        return steps


class TestTgGps_6_4(SitPumaTgCtfTest):
    def get_test_steps(self) -> List[Dict]:
        test_details = self.test_data.get("test_details")
        dn_initiator_id = test_details.get("dn_initiator_id")
        dn_responder_id = test_details.get("dn_responder_id")
        cn_id = test_details.get("cn_id")
        dn_responder_mac = test_details.get("dn_responder_mac")
        cn_mac = test_details.get("cn_mac")
        # dn_initiator_ping_stream = self.test_data.get("dn_initiator_ping_stream").get("")
        cn_ifname = "terra0"
        dn_initiator_ifname = "terra0"
        steps = [
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Bring Up Link DN-I <--> DN-R",
                "function": self.tg_assoc_links,
                "function_args": (dn_initiator_id,),
                "success_msg": "Link Up",
            },
            {
                "name": "Bring Up Link DN-R <--> CN-1",
                "function": self.tg_assoc_links,
                "function_args": (dn_responder_id,),
                "success_msg": "Link Up",
            },
            {
                "name": "Disable GPS on DNR; confirm that DN-I ↔ DNR link stays up; DNR ↔ CN1 link stays up, verify with pings",
                "function": self.switch_gpsd,
                "function_args": (
                    dn_responder_id,
                    False,
                ),
                "success_msg": "gpsd service stopped on DN-R",
            },
            {
                "name": "Disassociate CN1",
                "function": self.minion_dissoc,
                "function_args": (
                    dn_responder_id,
                    dn_responder_mac,
                    cn_mac,
                ),
                "success_msg": "CN1 Successfully Disassociated",
            },
            {
                "name": "Attempt association with CN1; assoc should pass (GPS is disabled on DNR)",
                "function": self.tg_assoc_links,
                "function_args": (dn_responder_id,),
                "success_msg": "Link Up",
            },
            {
                "name": "Disable GPS on DN-I",
                "function": self.switch_gpsd,
                "function_args": (
                    dn_initiator_id,
                    False,
                ),
                "success_msg": "gpsd service stopped on DN-I",
            },
            {
                "name": "CN1 should get dropped; ping should fail",
                "function": self.verify_ll_ping,
                "function_args": (cn_id, cn_ifname, 10),
                "success_msg": "verified_ll_ping",
                "continue_on_failure": True,
                "negate_result": True,
                "delay": 20,
            },
            {
                "name": "Link DN-I ↔ DNR should also get dropped; ping should fail",
                "function": self.verify_ll_ping,
                "function_args": (dn_initiator_id, dn_initiator_ifname, 10),
                "success_msg": "verified_ll_ping",
                "continue_on_failure": True,
                "negate_result": True,
            },
            {
                "name": "Attempt association with DNR; assoc should fail",
                "function": self.tg_assoc_links,
                "function_args": (dn_initiator_id,),
                "success_msg": "Link Up",
                "continue_on_failure": True,
                "negate_result": True,
            },
        ]
        return steps
