#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import random
from argparse import Namespace
from time import sleep
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError

from terragraph.ctf.consts import TgCtfConsts
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn


LOG = logging.getLogger(__name__)


class TestTg8021x(TestX86TGIgn):
    TEST_NAME = "PUMA: 802.1X Test Cases"
    DESCRIPTION = "802.1X Security Test Cases"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

        self.security_configuration = self.test_data.get("8021x_configuration", {})

    def create_backup_directory(self, node_id: int):
        cmd = "mkdir -p /data/secure_backup; ls -la /data; cat /data/cfg/node_config.json | grep wsec -A15;"

        futures: Dict = self.run_cmd(cmd, node_ids=[node_id])
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to run cmd: "
                    + f"{cmd}\n{output}\n{result['error']}"
                )
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{output}")

    def move_file_from_to_backups(self, file_name: str, direction: str, node_id: int):
        # Check if file_name is valid
        expected_file_names = ["ca.pem", "client.key", "client.pem"]
        if file_name not in expected_file_names:
            error_msg = (
                f"Node {node_id}: failed to run cmd: "
                + "\nPlease provide one of 'ca.pem','client.key','client.pem'"
            )
            raise DeviceCmdError(error_msg)

        if direction == "from":
            # Move file from backups folder
            # cmd = f"mv /data/secure/keys/ca.pem /data/secure_backup/"
            cmd = f"mv /data/secure_backup/{file_name} /data/secure/keys/; ls -la /data/secure/keys; ls -la /data/secure_backup;"

        elif direction == "to":
            # Move file to backups folder
            cmd = f"mv /data/secure/keys/{file_name} /data/secure_backup/; ls -la /data/secure/keys; ls -la /data/secure_backup;"
        else:
            # IF direction is not one of these raise exception!
            error_msg = (
                f"Node {node_id}: failed to run cmd: "
                + "\nPlease provide one of 'to' or 'from'"
            )
            raise DeviceCmdError(error_msg)

        futures: Dict = self.run_cmd(cmd, node_ids=[node_id])
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to run cmd: "
                    + f"{cmd}\n{output}\n{result['error']}"
                )
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{output}")

    def get_default_8021x_node_config(self):
        node_config_json = {
            "node_config": {
                "radioParamsBase": {
                    "fwParams": {"wsecEnable": 2},
                },
                "eapolParams": {
                    "ca_cert_path": "/data/secure/keys/ca.pem",
                    "client_cert_path": "/data/secure/keys/client.pem",
                    "private_key_path": "/data/secure/keys/client.key",
                    "radius_server_ip": "2001::1",
                    "radius_server_port": 1812,
                    "radius_user_identity": "tg",
                    "secrets": {
                        "private_key_password": "terragraph",
                        "radius_server_shared_secret": "tgsharedsecret",
                        "radius_user_password": "terragraph",
                    },
                },
            }
        }

        return node_config_json

    def check_if_security_keys_exists(self):
        expected_output = "4"
        node_ids = self.get_tg_devices()
        futures: Dict = self.run_cmd("ls /data/secure/keys | wc -w", node_ids)

        for result in self.wait_for_cmds(futures):
            if not result["success"] or result["message"] == expected_output:
                raise DeviceCmdError(
                    f"Failed to read /data/secure/keys from node {result['node_id']}"
                )

            output = result["message"]
            self.log_to_ctf(f"Node {result['node_id']} output: {output.strip()}")

    def get_traffic_steps(self):
        traffic_profile = self.test_data.get("traffic_profile", None)
        steps = []
        if traffic_profile:
            for stream in traffic_profile:
                steps.append(
                    {
                        "name": (
                            f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                            f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                        ),
                        "function": self.cpe_ping,
                        "function_args": (
                            stream["from_device_id"],
                            stream["to_device_id"],
                            stream["from_netns"],
                            stream["to_netns"],
                        ),
                        "success_msg": (
                            f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                            f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                        ),
                    }
                )
            steps.append(
                {
                    "name": "Run traffic",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile,),
                    "success_msg": "CPE to CPE iperf successful",
                },
            )
        return steps


class TestTg8021xIgnition(TestTg8021x):
    def nodes_data_amend(self, num_nodes: int) -> Dict:
        nodes_data_amend = super().nodes_data_amend(num_nodes)

        # By doing this I am getting rid of the neccessity to add
        # this default nodes_data_amend information into all test-data-8021x-X.json files manually!
        security_nodes_data_amend = self.get_default_8021x_node_config()

        # Amend for All Terragraph Nodes!
        self.merge_dict(
            nodes_data_amend,
            {i: security_nodes_data_amend for i in range(1, num_nodes + 1)},
        )

        return nodes_data_amend


class TestTg8021xIgniteAndTraffic(TestTg8021xIgnition):
    def get_test_steps(self):
        steps = super().get_test_steps()

        # If traffic profile exists, run traffic
        traffic_profile = self.test_data.get("traffic_profile", None)
        if traffic_profile:
            steps.extend(self.get_traffic_steps())

        return steps


class TestTg8021xIgnition16(TestTg8021xIgnition):
    def get_test_steps(self) -> List[Dict]:
        ignition_timeout_s = self.test_args["ignition_timeout_s"]

        steps = super().get_test_steps()

        # Randomly select a responder pair
        responder_nodes = self.test_data.get("responder_nodes", None)
        random_node_id = random.choice(responder_nodes)
        # Restart the e2e_minion on randomly selected pair
        # Wait 30 Sec
        # Check that the network is still entirely up
        steps.extend(
            [
                {
                    "name": "Restart the E2E Minion Service on the randomly selected pier",
                    "function": self.tg_restart_minion,
                    "function_args": (
                        [
                            random_node_id,
                        ],
                    ),
                    "success_msg": f"e2e_minion restarted on {random_node_id}.",
                },
                {
                    "name": "Wait 30 seconds for e2e_minion to come back up, and controller to recognize responder",
                    "function": sleep,
                    "function_args": (30,),
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
                },
            ]
        )
        # If traffic profile exists, run traffic
        traffic_profile = self.test_data.get("traffic_profile", None)
        if traffic_profile:
            steps.extend(self.get_traffic_steps())

        return steps


class TestTg8021xMissingCredentials(TestTg8021xIgnition):
    # Ignition should fail and then negate result!
    def get_test_steps(self) -> List[Dict]:
        steps = []

        missing_file_name = self.security_configuration.get("missing_file_name", None)
        responder_node = self.security_configuration.get("responder_node_id", None)
        steps.extend(
            [
                {
                    "name": "Create backup directory /data/secure_backup/ location",
                    "function": self.create_backup_directory,
                    "function_args": (responder_node,),
                    "success_msg": "Backup Directory Created",
                },
                {
                    "name": "Move File From /data/secure/keys to /data/secure_backup/ location",
                    "function": self.move_file_from_to_backups,
                    "function_args": (
                        missing_file_name,
                        "to",
                        responder_node,
                    ),
                    "success_msg": f"Moved {missing_file_name} to backups",
                },
            ]
        )
        steps.extend(super().get_test_steps())
        steps.append(
            {
                "name": "Move File Back to /data/secure/keys from /data/secure_backup/ location",
                "function": self.move_file_from_to_backups,
                "function_args": (
                    missing_file_name,
                    "from",
                    responder_node,
                ),
                "success_msg": f"Moved {missing_file_name} back from backup",
            }
        )

        return steps


class TestTg8021xInvalidCredentials(TestTg8021x):
    """
    # This class has to inherit from TestTg8021x!
    # Because if it inherits from TestTg8021xIgnition, then:
    # nodes_data_amend DOESN'T override TestTg8021xIgnition.nodes_data_amend
    # and it uses wrong node_config.json
    # By inheriting from TestTg8021x, i allow it to override BaseCtfTest.nodes_data_amend
    # and use the node_config.json that is proivded in the test-data-setup-id.json.
    # But as a result, I need to add the test steps (get_test_steps).
    """

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        nodes_data_amend = super().nodes_data_amend(num_nodes)

        amend_data = self.security_configuration.get("nodes_data_amend", {})
        initiator_node_id = self.security_configuration.get("initiator_node_id", None)
        initiator_amend_data = amend_data.get(str(initiator_node_id), {})
        responder_node_id = self.security_configuration.get("responder_node_id", None)
        responder_amend_data = amend_data.get(str(responder_node_id), {})

        self.merge_dict(
            nodes_data_amend,
            {
                initiator_node_id: initiator_amend_data,
                responder_node_id: responder_amend_data,
            },
        )

        return nodes_data_amend


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
