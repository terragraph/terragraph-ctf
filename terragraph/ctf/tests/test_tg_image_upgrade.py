#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)
TG_IMAGE_BIN_FILE = "/tmp/tg-update-qoriq.bin"


class TestTgImageUpgrade(PumaTgCtfTest):
    TEST_NAME = "PUMA: Image Upgrade"
    DESCRIPTION = "Download, upgrade, and verify a TG software image."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgImageUpgrade, TestTgImageUpgrade
        ).test_params()
        test_params["image_path"]["required"] = True
        return test_params

    def pre_run(self) -> None:
        # pre_run would also try to do an image upgrade
        self.log_to_ctf("No pre-run needed for this test")

    def upgrade_tg_images(
        self,
        image_file_path: str,
        node_ids: Optional[List[int]] = None,
        timeout: int = 600,
    ) -> None:
        """Flash/upgrade a TG image on selected nodes. This performs the
        following steps in sequence:

        1) Assuming the image is already downloaded in the given path, verify
           the checksum.

        2) Flash/upgrade the image and wait for reboot.

        3) Post-reboot, match the running image version with the
           downloaded image version from step 1 (pre-upgrade).
        """

        # Ensure exec permission, and verify the checksum of the
        # downloaded image
        futures: Dict = self.run_cmd(
            f"chmod a+x {image_file_path};{image_file_path} -cm", node_ids
        )

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"Node {result['node_id']} read metadata failure"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            if "Checksum ok" not in result["message"]:
                error_msg = f"Node {result['node_id']} checksum failed"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(f"Node {result['node_id']} checksum OK", "info")

        # Upgrade images and wait for reboot
        self.upgrade_and_reboot_tg_images(
            image_file_path, node_ids=node_ids, max_upgrade_timeout=timeout
        )

    def get_test_steps(self) -> List[Dict]:
        node_ids: List[int] = self.get_tg_devices()
        return [
            {
                "name": "Download TG images to all nodes",
                "function": self.copy_files_parallel,
                "function_args": (
                    self.test_args["image_path"],
                    TG_IMAGE_BIN_FILE,
                    node_ids,
                ),
                "success_msg": "Successfully downloaded images to all nodes",
            },
            {
                "name": "Upgrade and reboot TG images on all nodes",
                "function": self.upgrade_tg_images,
                "function_args": (TG_IMAGE_BIN_FILE, node_ids),
                "success_msg": "Successfully upgraded images on all nodes and rebooted",
            },
            self.COMMON_TEST_STEPS["check_software_versions"],
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
