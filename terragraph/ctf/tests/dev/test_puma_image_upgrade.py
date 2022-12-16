#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)
TG_IMAGE_BIN_FILE = "/tmp/tg-update-qoriq.bin"


class TestTgPumaImageUpgrade(PumaTgCtfTest):
    TEST_NAME = "PUMA: Image Upgrade"
    DESCRIPTION = "Download, upgrade, and verify a TG software image."

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgPumaImageUpgrade, TestTgPumaImageUpgrade
        ).test_params()
        test_params["image_path"]["required"] = True
        return test_params

    def pre_run(self) -> None:
        # pre_run would also try to do an image upgrade
        self.log_to_ctf("No pre-run needed for this test")

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
                "name": "Upgrade and verify TG images on all nodes",
                "function": self.upgrade_and_verify_tg_images,
                "function_args": (TG_IMAGE_BIN_FILE, node_ids),
                "success_msg": "Successfully upgraded/verified images on all nodes",
            },
            self.COMMON_TEST_STEPS["check_software_versions"],
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
