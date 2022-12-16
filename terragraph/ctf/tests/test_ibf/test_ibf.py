#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep
from typing import Any, Dict, List, Optional

from ctf.ctf_client.runner.exceptions import TestFailed
from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn


LOG = logging.getLogger(__name__)


class TestTgIbfBase(SitPumaTgCtfTest):
    def collecting_fw_stats_for_ibf(
        self, flag: bool, grep_key: str = "", node_ids: Optional[List[int]] = None
    ):
        """
        The purpose of this funtion is to start/stop the fw_stat collection on stdout into a file.
        Later, this file will be read to analyze the key/value pairs defined under 'grep_key'
        flag : True : Start
        flag : False : Stop
        """
        stats_cmd = "tg2 stats"
        if flag:
            cmd = f"/usr/sbin/{stats_cmd} -t 90 driver-if | grep -i {grep_key};"  #  > /tmp/fw_stat_{grep_key} & "
            # cmd = "sleep 90; echo 'FINISHED WAITING SLEEP DEBUG!'"  #  > /tmp/fw_stat_{grep_key} & "
            self.log_to_ctf(cmd)
        else:
            cmd = f"pkill -f '{stats_cmd}'"

        self.log_to_ctf(f"SELF.TIMEOUT: {self.timeout}")
        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures, self.timeout):
            self.log_to_ctf(str(result))
            if not result["success"]:
                # proceed anyway (don't raise exception)
                self.log_to_ctf(
                    f"Node {result['node_id']}: {cmd} failed : {result}", "error"
                )

    def cat_fw_stat(self, grep_key: str, node_ids: Optional[List[int]] = None):
        cmd = f"cat /tmp/fw_stat_{grep_key}"
        self.log_to_ctf(f"cat /tmp/fw_stat_{grep_key}")
        futures: Dict = self.run_cmd(cmd, node_ids)
        results: List[str] = []
        for result in self.wait_for_cmds(futures):
            self.log_to_ctf(f"\n{result['message']}")
            results.append(result["message"])

        for result in results:
            if result.strip() == "":
                self.analyze_fw_stats(result.strip())
            else:
                self.log_to_ctf(f"{grep_key} not found in stats dump")

    def repetitive_assoc_dissoc(
        self, initiator_id: int, initiator_mac: str, responder_mac: str
    ):
        for i in range(2):
            self.log_to_ctf(f"Repetition {i}")
            self.minion_assoc(initiator_id, initiator_mac, responder_mac)
            sleep(15)
            self.minion_dissoc(initiator_id, initiator_mac, responder_mac)
            sleep(15)

    def analyze_fw_stats(self, fw_stat_message: str):
        """
        * This function checks that if the pktRssi value is the same
        accross multiple assoc, dissocs. It should be max in +-1 difference.
        * It runs on node
        * input file_name: custom_fw_stats filtered to pktRssi values only!
        * output result: "PASS/FAIL"
        """
        result = "PASS"
        fw_stat_message_list = fw_stat_message.split("\n")
        self.log_to_ctf(f"fw_stat_message.split('\\n'):\n{fw_stat_message}")
        init_val = 0
        for i, line in enumerate(fw_stat_message_list):
            val = int(line.split(", ")[2])
            if i == 0:
                init_val = val
                self.log_to_ctf(f"Initial pktRssi Val: {init_val}")
            else:
                if (val > init_val + 1) or (val < init_val - 1):
                    result = "FAIL"
                    raise TestFailed(
                        f"pktRssi value {val} was not with expected bounds of { init_val + 1} to {init_val - 1}"
                    )

        return result


class TestTgIbf_Minion(TestTgIbfBase):
    def get_test_steps(self) -> List[Dict]:
        test_details = self.test_data.get("test_details")
        dn_initiator_id = test_details.get("dn_initiator_id")
        dn_initiator_mac = test_details.get("dn_initiator_mac")
        dn_responder_mac = test_details.get("dn_responder_mac")
        grep_key: str = test_details.get("grep_key")
        node_ids: List[int] = test_details.get("node_ids", None)

        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            {
                "name": "Start Collecting FW Stats under /tmp",
                "function": self.collecting_fw_stats_for_ibf,
                "function_args": (
                    True,
                    grep_key,
                    node_ids,
                ),
                "success_msg": f"Started Collecting FW Stats for {grep_key}",
                "concurrent": True,
            },
            {
                "name": "Repeat Assoc and Dissoc",
                "function": self.repetitive_assoc_dissoc,
                "function_args": (
                    dn_initiator_id,
                    dn_initiator_mac,
                    dn_responder_mac,
                ),
                "success_msg": "Finished repeating assoc and dissoc.",
                "concurrent": True,
                "delay": 5,
            },
        ]

        return steps


class TestTgIbf_AttenuationEffect(TestTgIbfBase, TestX86TGIgn):
    def flap_attenuation_and_check_topology(
        self,
        repeat: int,
        attenuator_id: int,
        attenuation_sequence: List[Dict[str, Any]],
        ignition_timeout_s: int,
    ):
        """
        The purpose of this function to adjust the attenuation into desired level.
        repeat: number of times to repeat the sequence.
        attenuator_id: device_id in the test_setup
        attenuation_sequence: attenuation levels to be set in each iteration.
        ignition_timeoiut_s: number of seconds to check the network state.
        """
        for i in range(repeat):
            self.log_to_ctf(f"Repetation {i}")
            for attenuation_config in attenuation_sequence:
                attenuation_level: int = attenuation_config.get("attenuation_level")
                expected_ignition_state: bool = attenuation_config.get(
                    "expected_ignition_state"
                )
                negate_result: bool = not expected_ignition_state
                self.log_to_ctf(f"expected_ignition_state: {expected_ignition_state}")
                self.log_to_ctf(f"negate_result: {negate_result}")

                self.log_to_ctf(f"Set {attenuation_level} dB attenuation on the link.")
                self.set_attenuation_x_db(attenuator_id, attenuation_level)

                self.log_to_ctf("Wait 60 seconds for attenuation to take place")
                sleep(60)

                self.log_to_ctf("ReCheck network after adjusting the attenuation level")
                try:
                    self.try_until_timeout(
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    )
                except Exception:
                    self.log_to_ctf(
                        "ReCheck network after adjusting the attenuation level raised an error"
                    )

    def get_test_steps(self) -> List[Dict]:
        test_details = self.test_data.get("test_details")
        grep_key: List[str] = test_details.get("grep_key")
        attenuator_id: int = test_details.get("attenuator_id")
        repeat: int = test_details.get("repeat")
        attenuation_sequence: List[Dict[str, Any]] = test_details.get(
            "attenuation_sequence"
        )
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        node_ids: List[int] = test_details.get("node_ids", None)
        test_ignition_config = self.test_data.get("e2e_ignition_config", {})
        if test_ignition_config.get("ignition_timeout_s"):
            ignition_timeout_s = test_ignition_config.get("ignition_timeout_s")

        self.log_to_ctf(f"GET TEST STEPS\nattenuator_id: {attenuator_id}")
        # Set 0 dB attenuation on the link to start and check ignition is passing.
        steps: List[Dict] = [
            {
                "name": "Set 0 dB attenuation on the link to start and check ignition is passing.",
                "function": self.set_attenuation_x_db,
                "function_args": (
                    attenuator_id,
                    0,
                ),
                "success_msg": "Set Attenuation to 0 dB",
            },
            {
                "name": "Wait 60 seconds for attenuation to take place",
                "function": sleep,
                "function_args": (60,),
                "success_msg": "Finished waiting",
            },
        ]
        if self.test_args["x86_image_path"]:
            steps.append(
                {
                    "name": "Push x86 image",
                    "function": self.push_x86_image,
                    "function_args": (self.test_args["x86_image_path"],),
                    "success_msg": "x86 image was upgraded.",
                }
            )
        # Start Collecting FW Logs
        steps.extend(
            [
                {
                    "name": "Start Collecting FW Stats under /tmp",
                    "function": self.collecting_fw_stats_for_ibf,
                    "function_args": (
                        True,
                        grep_key,
                        node_ids,
                    ),
                    "success_msg": f"Started Collecting FW Stats for {grep_key}",
                    "concurrent": True,
                },
                self.get_common_x86_test_steps()["setup_x86_services"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Check that the network is entirely up",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": False,
                    "negate_result": False,
                },
                {
                    "name": "Wait 60 seconds for last node to apply node config overrides changes",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "ReCheck network after node overrides take effect",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": False,
                    "negate_result": False,
                },
                {
                    "name": "Set fw log level debug ",
                    "function": self.minion_set_fb_fw_log_config,
                    "function_args": (
                        None,
                        "debug",
                    ),
                    "success_msg": "fw log debug level set",
                },
                {
                    "name": "Wait 60 seconds for before acutal testing starts",
                    "function": sleep,
                    "function_args": (60,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Repeatedly flapping attenuation level and checking topology",
                    "function": self.flap_attenuation_and_check_topology,
                    "function_args": (
                        repeat,
                        attenuator_id,
                        attenuation_sequence,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Finished repeatedly flapping attenuation levels.",
                },
                {
                    "name": "Stop Collecting FW Stats under /tmp",
                    "function": self.collecting_fw_stats_for_ibf,
                    "function_args": (
                        False,
                        grep_key,
                    ),
                    "success_msg": "Finished waiting",
                },
            ]
        )

        return steps
