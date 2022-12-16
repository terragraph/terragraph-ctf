#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from concurrent.futures import as_completed
from time import sleep
from typing import Dict, List

import requests
from ctf.ctf_client.runner.exceptions import DeviceError
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgE2ERegBase(TestX86TGIgn):
    TEST_NAME = "E2E Re-Ignition"
    DESCRIPTION = "Re-Ignition control after power on any nodes or 10G Connection lost."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgE2ERegBase, TestTgE2ERegBase
        ).test_params()
        test_params["enable_fw_stats"]["default"] = False
        return test_params

    def raritan_pdu_control(self, pdu_list: Dict, switch_state: bool):
        """
        PDU SNMP control
        switch_state : False => Power Off
        switch_state : True => Power On
        """

        futures: Dict = {}
        for pdu in pdu_list:
            pdu_ip = pdu["ip"]
            pdu_outlet = pdu["outlet"]
            self.log_to_ctf(
                f"Sending powercycle to: Pdu {pdu_ip} and Outlet {pdu_outlet}"
            )
            futures[
                self.thread_pool.submit(
                    self._send_powercycle,
                    pdu["user"],
                    pdu["password"],
                    pdu["ip"],
                    pdu["outlet"],
                    pdu["wait_time"],
                    switch_state,
                )
            ] = pdu_ip

        failed_pdus = []
        for future in as_completed(futures.keys(), timeout=self.timeout):
            result = future.result()
            pdu_ip = futures[future]
            if result:
                self.log_to_ctf(f"PDU {pdu_ip} successfully updated!")
            else:
                failed_pdus.append(pdu_ip)
                self.log_to_ctf(f"Failed to powercycle {pdu_ip}")

        if failed_pdus:
            raise DeviceError(
                f"Errors were raised during PDU powercycle on {len(failed_pdus)} "
                + f"node(s): {sorted(failed_pdus)}"
            )

    def _send_powercycle(
        self,
        user: str,
        password: str,
        pdu_ip: str,
        outlet: int,
        wait_time: int,
        switch_state: bool,
    ):
        """
        Send a request to a Raritan PDU via JsonRPC in order to
        config the outlet state.
        """
        success: bool = True

        request_url = (
            f"https://{user}:{password}@{pdu_ip}/model/pdu/0/outlet/{outlet - 1}"
        )
        headers = {"content-type": "application/json"}
        power_state = (
            self._create_switch_state(1)
            if switch_state
            else self._create_switch_state(0)
        )

        response = requests.post(
            request_url,
            headers=headers,
            data=json.dumps(power_state),
            verify=False,
        )
        self.log_to_ctf(str(response))

        if response.status_code != 200:
            success = False

        return success

    def _create_switch_state(self, state):
        return {
            "jsonrpc": "2.0",
            "method": "setPowerState",
            "params": {"pstate": state},
            "id": 23,
        }


class TestTgE2EReg2(TestTgE2ERegBase):
    def get_test_steps(self) -> List[Dict]:
        # 1. Standard Ignition
        steps = super().get_test_steps()

        # 2. Get PDU List from test_data
        pdu_list = self.test_data.get("pdus", [])

        # 3. Power cycle Puma nodes or TrafficGens depending on the test_data
        steps.extend(
            [
                {
                    "name": "Run Power Off nodes",
                    "function": self.raritan_pdu_control,
                    "function_args": (
                        pdu_list,
                        False,
                    ),
                    "success_msg": "Powered OFF PDUs",
                },
                {
                    "name": "Wait 5 seconds",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Run Power ON nodes",
                    "function": self.raritan_pdu_control,
                    "function_args": (
                        pdu_list,
                        True,
                    ),
                    "success_msg": "Powered ON PDUs",
                },
                # 4. Check Network Recovery
                {
                    "name": "Wait 60 seconds for network recover",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after Power Cycle",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        self.test_args["ignition_timeout_s"],
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )

        return steps


class TestTgE2EReg3(TestTgE2ERegBase):
    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(TestTgE2EReg3, TestTgE2EReg3).test_params()
        test_params["down_pop_name"] = {
            "desc": (
                "POP Node name on topology which we want to switch off. "
                + "It must match one of the names on test-data.json pdus. "
            ),
            "required": True,
        }

        return test_params

    def get_test_steps(self) -> List[Dict]:
        # 1. Standard Ignition
        # Check network is ignited
        steps = super().get_test_steps()

        # 2. Get the Pop Node to be switched off
        down_pop_name = self.test_args["down_pop_name"]

        # 3. Get PDU List from test_data
        pdu_list = self.test_data.get("pdus", [])

        # 4. Select the Pop which will powered off from the pdus
        powercycle_pdu_list = []
        for pdu in pdu_list:
            if pdu.get("node_name") == down_pop_name:
                powercycle_pdu_list.append(pdu)

        # 5. switch off fiber port on ubiquiti switch connecting to one of the pops
        steps.extend(
            [
                {
                    "name": "Power Off selected Pop-Node",
                    "function": self.raritan_pdu_control,
                    "function_args": (
                        powercycle_pdu_list,
                        False,
                    ),
                    "success_msg": "Power Cycled PDUs",
                },
                {
                    "name": "Wait 40 seconds for other pop to set new routes",
                    "function": sleep,
                    "function_args": (40,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after new Routes",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        self.test_args["ignition_timeout_s"],
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
                {
                    "name": "Power ON the powered-off Pop-Node",
                    "function": self.raritan_pdu_control,
                    "function_args": (
                        powercycle_pdu_list,
                        True,
                    ),
                    "success_msg": "Power Cycled PDUs",
                },
                {
                    "name": "Wait 120 seconds for other pop to set new routes",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after new Routes",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        self.test_args["ignition_timeout_s"],
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )
        return steps


class TestTgE2EReg4(TestTgE2ERegBase):
    def get_test_steps(self) -> List[Dict]:
        # 1. Standard Ignition
        steps = super().get_test_steps()

        # 2. Get PDU List from test_data
        pdu_list = self.test_data.get("pdus", [])

        # 3. Power-Off Pop Puma node and check the network is down.
        steps.extend(
            [
                {
                    "name": "Run Power Off on POP Node",
                    "function": self.raritan_pdu_control,
                    "function_args": (
                        pdu_list,
                        False,
                    ),
                    "success_msg": "Powered OFF Pop Node via PDU",
                },
                {
                    "name": "Wait 35 seconds",
                    "function": sleep,
                    "function_args": (35,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after Powering off the Pop node, it should fail. No need to wait for default ignition_timeout_s",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        30,
                    ),
                    "success_msg": "Network is Down as expected",
                    "error_handler": self.get_common_error_handler(),
                    "negate_result": True,
                    "continue_on_failure": True,
                },
                {
                    "name": "Run Power back ON POP Node",
                    "function": self.raritan_pdu_control,
                    "function_args": (
                        pdu_list,
                        True,
                    ),
                    "success_msg": "Powered ON Pop Node via PDU",
                },
                {
                    "name": "Wait 35 seconds for pop node to come back up",
                    "function": sleep,
                    "function_args": (35,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after Powering On the Pop node, it should pass",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        self.test_args["ignition_timeout_s"],
                    ),
                    "success_msg": "Network is Back Up as expected",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
