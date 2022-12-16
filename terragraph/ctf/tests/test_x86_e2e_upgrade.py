#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep, time
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import TestFailed
from terragraph.ctf.puma import PumaTgCtfTest
from terragraph.ctf.x86_tg import x86TgCtfTest


LOG = logging.getLogger(__name__)


class TestTgX86E2EUpgrade(PumaTgCtfTest, x86TgCtfTest):
    TEST_NAME = "TGX86: Test x86 Terragraph E2E Upgrade (BitTorrent)"
    DESCRIPTION = (
        "Upgrade Terragraph nodes using an x86 E2E controller over BitTorrent."
    )
    LOG_FILES = ["/var/log/e2e_controller/current", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "e2e-x86-nodes-data-setup-{SETUP_ID}.json"

    # used locally (these should be Optional, but getting other type errors...)
    upgradeImage: Dict = {}
    upgradeReqId: str = ""

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(  # type: ignore
            TestTgX86E2EUpgrade, TestTgX86E2EUpgrade
        ).test_params()
        test_params["upload_image_path"] = {
            "desc": (
                "Upgrade nodes to the given software image using the E2E controller"
            ),
            "required": True,
        }
        test_params["ignition_timeout_s"] = {
            "desc": (
                "How many seconds should we wait for the network to come up? "
                + "This may need to take into account the controller potentially "
                + "rebooting the nodes for a config update."
            ),
            "default": 600.0,
            "convert": float,
        }
        test_params["upgrade_timeout_s"] = {
            "desc": "Per-batch timeout for the upgrade operation (in seconds)",
            "default": 600,
            "convert": int,
        }
        PumaTgCtfTest.merge_dict(test_params, x86TgCtfTest.test_params())

        return test_params

    def pre_run(self) -> None:
        # Remove upgrade state cache before rebooting
        self.delete_upgrade_state_cache()

        super().pre_run()

    def _verify_tg_image_seeding(self, image_file_path: str) -> None:
        """Verify that the controller is seeding the given TG node image.

        Sets `self.upgradeImage` to the returned `UpgradeImage` structure.
        """
        # Read local version string
        local_version = self.get_image_version_from_build(image_file_path).strip()

        # Fetch controller's image list via API
        images = self.api_service_request("listUpgradeImages")

        # Find match
        for image in images.get("images", []):
            if image["name"] == local_version:
                self.log_to_ctf(f"E2E controller is seeding the given image: {image}")
                self.upgradeImage = image
                return
        raise TestFailed(
            f"E2E controller is not seeding the given image: {local_version}"
        )

    def _upgrade_network(self, timeout_s: int) -> None:
        """Upgrade all nodes in the network.

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
            "ugType": UpgradeGroupType["NETWORK"],
            "nodes": [],
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

    def _check_upgrade_status(self) -> None:
        """Check if all nodes in the network have finished upgrading.

        Depends on `self.upgradeImage` set in `_verify_tg_image_seeding()` and
        `self.upgradeReqId` set in `_upgrade_network()`.
        """
        # Fetch controller's node status dump
        statusDump = self.api_service_request("getCtrlStatusDump")

        # Fetch controller's upgrade state
        upgradeStateDump = self.api_service_request("getUpgradeState")

        # Check if our upgrade request is ongoing/pending
        reqs = []  # list of UpgradeGroupReq
        if len(upgradeStateDump.get("curReq", {})):
            reqs.append(upgradeStateDump["curReq"])
        if len(upgradeStateDump.get("pendingReqs", {})):
            reqs.extend(upgradeStateDump["pendingReqs"])
        for req in reqs:
            req_id = req.get("urReq", {}).get("upgradeReqId", None)
            if not req_id:
                continue  # probably uninitialized Thrift struct
            if req_id == self.upgradeReqId:
                err_msg = f"Upgrade is in progress (ID: {self.upgradeReqId})"
                self.log_to_ctf(err_msg, "error")
                raise TestFailed(err_msg)

        # Check all node versions
        nodes_not_upgraded = []
        for node_id, status_report in statusDump.get("statusReports", {}).items():
            if status_report["version"].strip() != self.upgradeImage["name"]:
                nodes_not_upgraded.append(node_id)
        if len(nodes_not_upgraded):
            err_msg = f"{len(nodes_not_upgraded)} node(s) have not upgraded"
            self.log_to_ctf(f"{err_msg}: {nodes_not_upgraded}", "error")
            raise TestFailed(err_msg)

    def get_test_steps(self) -> List[Dict]:
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        upgrade_timeout_s = self.test_args["upgrade_timeout_s"]

        step_wait_for_network_ignition = {
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
        }

        steps = []
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
                self.get_common_x86_test_steps()["setup_x86_services"],
                {
                    "name": "Push TG image to x86 host",
                    "function": self.push_tg_image_to_x86,
                    "function_args": (self.test_args["upload_image_path"],),
                    "success_msg": "TG image was uploaded.",
                },
                self.get_common_x86_test_steps()["start_x86_bt_tracker"],
                self.get_common_x86_test_steps()["start_x86_services"],
                {
                    "name": "Wait 5 seconds for controller to initialize",
                    "function": sleep,
                    "function_args": (5,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Verify TG image is seeding",
                    "function": self._verify_tg_image_seeding,
                    "function_args": (self.test_args["upload_image_path"],),
                    "success_msg": "E2E controller is seeding the TG image.",
                },
                step_wait_for_network_ignition,
                {
                    "name": "Start network upgrade",
                    "function": self._upgrade_network,
                    "function_args": (upgrade_timeout_s,),
                    "success_msg": "Upgrade request was sent (FULL_UPGRADE).",
                },
                {
                    "name": "Check that all nodes upgraded",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self._check_upgrade_status,
                        (),
                        5,
                        upgrade_timeout_s,
                    ),
                    "success_msg": "All nodes upgraded successfully.",
                    "error_handler": self.get_common_error_handler(),
                },
                step_wait_for_network_ignition,
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
