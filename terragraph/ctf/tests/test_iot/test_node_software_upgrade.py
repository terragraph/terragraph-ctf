#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from time import sleep, time
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import TestFailed
from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIot
from terragraph.ctf.tests.test_x86_e2e_upgrade import TestTgX86E2EUpgrade

LOG = logging.getLogger(__name__)


class TestIotNSU1(TestNodeIot, TestTgX86E2EUpgrade):
    TEST_NAME = "NodeIOTv2-NSU-1, NetworkIOTv2-NSU-1"
    DESCRIPTION = "Upgrade network containing Puma and OEM radios using a Facebook x86 E2E controller with BitTorrent."

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.puma_nodes = []

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(  # type: ignore
            TestIotNSU1, TestIotNSU1
        ).test_params()

        test_params["upload_oem_image_path"] = {
            "desc": (
                "oem software image required to upgrade"
                " software on oem nodes in network"
            ),
            "required": True,
        }
        test_params["oem_node_name"] = {
            "desc": "node name of oem node in network",
            "required": True,
        }
        TestIotNSU1.merge_dict(test_params, TestNodeIot.test_params())
        TestIotNSU1.merge_dict(test_params, TestTgX86E2EUpgrade.test_params())
        return test_params

    def _get_puma_nodes(self, skip_nodes: Optional[List] = None):
        """sets `self.puma_nodes` to the `List[str]` of puma nodes

        in the network, excluding the OEM node and nodes specified in `skip_nodes`

        OEM node name is given as test-args input

        `test_params["oem_node_name"]`
        """

        # get topoology info from controller
        topology = self.api_service_request("getTopology")

        # read puma nodes names
        for node in topology["nodes"]:
            if node["name"] == self.test_args["oem_node_name"]:
                continue
            if skip_nodes:
                if node["name"] in skip_nodes:
                    continue
            self.puma_nodes.append(node["name"])

    def _upgrade_nodes(self, timeout_s: int, nodes: List[str]):
        """Upgrade image on list of nodes.

        Depends on `self.upgradeImage` set in `_verify_tg_image_seeding()`.

        Sets `self.upgradeReqId` to the generated upgrade request ID.
        """
        self.upgradeReqId = f"ctf-{int(time())}"

        # from thrift
        UpgradeGroupType = {"NODES": 10, "NETWORK": 20}
        UpgradeReqType = {
            "PREPARE_UPGRADE": 10,
            "COMMIT_UPGRADE": 20,
            "RESET_STATUS": 30,
            "FULL_UPGRADE": 40,
        }

        # send UpgradeGroupReq
        req = {
            "ugType": UpgradeGroupType["NODES"],
            "nodes": nodes,
            "excludeNodes": [],
            "urReq": {
                "urType": UpgradeReqType["FULL_UPGRADE"],
                "upgradeReqId": self.upgradeReqId,
                "md5": self.upgradeImage["md5"],
                "imageUrl": self.upgradeImage["magnetUri"],
                "scheduleToCommit": 0,
                "torrentParams": {
                    "downloadTimeout": timeout_s,
                },
                "hardwareBoardIds": self.upgradeImage["hardwareBoardIds"],
            },
            "timeout": timeout_s,
            "skipFailure": False,
            "skipPopFailure": False,
            "version": "",
            "skipLinks": [],
            "limit": 0,  # staged unlimited
            "retryLimit": 1,
        }
        res = self.api_service_request("sendUpgradeRequest", req)
        if not res.get("success", False):
            raise TestFailed("Upgrade request failed")

        self.upgradeReqId = f"ctf-{int(time())}"

    def _check_nodes_upgrade_status(self, nodes: List[str]) -> None:
        """Check if all nodes listed in `nodes` have finished upgrading.

        Depends on `self.upgradeImage` set in `_verify_tg_image_seeding()` and

        `self.upgradeReqId` set in `_upgrade_nodes()`.
        """
        # Fetch controller's node status dump
        statusDump = self.api_service_request("getCtrlStatusDump")

        # Fetch controller's upgrade state
        upgradeStateDump = self.api_service_request("getUpgradeState")

        # Fetch controller's topology dump
        topologyDump = self.api_service_request("getTopology")
        # map node names with node_ids in status dump
        nodes_status_report = statusDump.get("statusReports", {})
        for node in topologyDump["nodes"]:
            for node_id, status_report in nodes_status_report.items():
                if node["mac_addr"] == node_id:
                    status_report["name"] = node["name"]

        # Check if our upgrade request is ongoing/pending
        reqs = []
        if len(upgradeStateDump.get("curReq", {})):
            reqs.append(upgradeStateDump["curReq"])
        if len(upgradeStateDump.get("pendingReqs", {})):
            reqs.extend(upgradeStateDump["pendingReqs"])
        for req in reqs:
            req_id = req.get("urReq", {}).get("upgradeReqId", None)
            if not req_id:
                continue
            if req_id == self.upgradeReqId:
                err_msg = f"Upgrade is in progress (ID: {self.upgradeReqId})"
                self.log_to_ctf(err_msg, "error")
                raise TestFailed(err_msg)

        # Check image version for nodes upgraded
        nodes_not_upgraded = []
        for node_id, status_report in nodes_status_report.items():
            # if node not is nodes list skip version check
            if status_report["name"] not in nodes:
                continue
            if status_report["version"].strip() != self.upgradeImage["name"]:
                self.log_to_ctf(
                    f"Node {status_report['name']} software version is {status_report['version']}"
                )
                nodes_not_upgraded.append(node_id)
        # if any nodes are not upgraded raise failure
        if len(nodes_not_upgraded):
            err_msg = f"{len(nodes_not_upgraded)} node(s) have not upgraded"
            self.log_to_ctf(f"{err_msg}: {nodes_not_upgraded}", "error")
            raise TestFailed(err_msg)

    def get_test_steps(self) -> List[Dict]:
        steps = []
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        upgrade_timeout_s = self.test_args["upgrade_timeout_s"]

        # upgrade controller if x86_image is given
        if self.test_args["x86_image_path"]:
            steps.append(
                {
                    "name": "Push x86 image",
                    "function": self.push_x86_image,
                    "function_args": (self.test_args["x86_image_path"],),
                    "success_msg": "x86 image was upgraded.",
                }
            )

        steps.extend(
            [
                self.get_common_test_steps()["check_software_versions"],
                self.get_common_x86_test_steps()["setup_x86_services"],
                # upload tg image to controller
                {
                    "name": "Push Puma image to x86 host",
                    "function": self.push_tg_image_to_x86,
                    "function_args": (
                        self.test_args["upload_image_path"],
                        "tg-image.bin",
                    ),
                    "success_msg": "Puma image was uploaded.",
                },
                # upload oem image to controller
                {
                    "name": "Push OEM image to x86 host",
                    "function": self.push_tg_image_to_x86,
                    "function_args": (
                        self.test_args["upload_oem_image_path"],
                        "oem-image.bin",
                    ),
                    "success_msg": "OEM image was uploaded.",
                },
                # start bitTorrent tracker service
                self.get_common_x86_test_steps()["start_x86_bt_tracker"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Verify PUMA image is seeding",
                    "function": self._verify_tg_image_seeding,
                    "function_args": (self.test_args["upload_image_path"],),
                    "success_msg": "E2E controller is seeding the Puma image.",
                },
                {
                    "name": "Check if network is ignited",
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
                        120,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
                # get tg nodes in network excluding oem node to upgrade
                {
                    "name": "Get puma nodes in network",
                    "function": self._get_puma_nodes,
                    "function_args": (),
                    "success_msg": "retrieved puma nodes",
                },
                {
                    "name": "Start upgrade of puma nodes in network",
                    "function": self._upgrade_nodes,
                    "function_args": (
                        upgrade_timeout_s,
                        self.puma_nodes,
                    ),
                    "success_msg": "Upgrade request for puma nodes was sent.",
                },
                {
                    "name": "Check that all puma nodes are upgraded",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self._check_nodes_upgrade_status,
                        ([self.puma_nodes]),
                        5,
                        upgrade_timeout_s,
                    ),
                    "success_msg": "Puma nodes upgraded successfully.",
                    "error_handler": self.get_common_error_handler(),
                },
                # upgrade oem node in network after puma nodes complete upgrade
                {
                    "name": "Verify OEM image is seeding",
                    "function": self._verify_tg_image_seeding,
                    "function_args": (self.test_args["upload_oem_image_path"],),
                    "success_msg": "E2E controller is seeding the OEM image.",
                },
                {
                    "name": "Start upgrade of oem node",
                    "function": self._upgrade_nodes,
                    "function_args": (
                        upgrade_timeout_s,
                        [self.test_args["oem_node_name"]],
                    ),
                    "success_msg": "Upgrade request was sent for OEM node",
                },
                {
                    "name": "Check that OEM node is upgraded",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self._check_nodes_upgrade_status,
                        ([self.test_args["oem_node_name"]]),
                        5,
                        upgrade_timeout_s,
                    ),
                    "success_msg": "OEM node is upgraded successfully.",
                    "error_handler": self.get_common_error_handler(),
                },
                {
                    "name": "Check if network is back up after upgrade",
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
        return steps


class TestNodeIotNSU2(TestIotNSU1):
    TEST_NAME = "NodeIOTv2-NSU-2"
    DESCRIPTION = "Upgrade the OEM node in network using a Facebook x86 E2E controller with BitTorrent."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestNodeIotNSU2, TestNodeIotNSU2
        ).test_params()
        test_params["upload_image_path"]["required"] = False
        return test_params

    def get_test_steps(self) -> List[Dict]:
        steps = []
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        upgrade_timeout_s = self.test_args["upgrade_timeout_s"]

        # upgrade controller if x86_image is given
        if self.test_args["x86_image_path"]:
            steps.append(
                {
                    "name": "Push x86 image",
                    "function": self.push_x86_image,
                    "function_args": (self.test_args["x86_image_path"],),
                    "success_msg": "x86 image was upgraded.",
                }
            )

        steps.extend(
            [
                self.get_common_test_steps()["check_software_versions"],
                self.get_common_x86_test_steps()["setup_x86_services"],
                # upload oem image to controller
                {
                    "name": "Push OEM image to x86 host",
                    "function": self.push_tg_image_to_x86,
                    "function_args": (
                        self.test_args["upload_oem_image_path"],
                        "oem-image.bin",
                    ),
                    "success_msg": "OEM image was uploaded.",
                },
                # start bitTorrent tracker service
                self.get_common_x86_test_steps()["start_x86_bt_tracker"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Verify OEM image is seeding",
                    "function": self._verify_tg_image_seeding,
                    "function_args": (self.test_args["upload_oem_image_path"],),
                    "success_msg": "E2E controller is seeding the OEM image.",
                },
                {
                    "name": "Check if network is ignited",
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
                # upgrade OEM node, validate update and check network state
                {
                    "name": "Start upgrade of oem node",
                    "function": self._upgrade_nodes,
                    "function_args": (
                        upgrade_timeout_s,
                        [self.test_args["oem_node_name"]],
                    ),
                    "success_msg": "Upgrade request was sent for OEM node",
                },
                {
                    "name": "Check that OEM node is upgraded",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self._check_nodes_upgrade_status,
                        ([self.test_args["oem_node_name"]]),
                        5,
                        upgrade_timeout_s,
                    ),
                    "success_msg": "OEM node is upgraded successfully.",
                    "error_handler": self.get_common_error_handler(),
                },
                {
                    "name": "Check if network is back up after upgrade",
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
        return steps
