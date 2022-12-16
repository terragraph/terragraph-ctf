#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgCtfTest(PumaTgCtfTest):
    TEST_NAME = "PUMA: SSH Connectivity"
    DESCRIPTION = "Test SSH connectivity to a CTF test setup."

    def pre_run(self) -> None:
        self.log_to_ctf("No pre-run needed for this test")

    def get_test_steps(self) -> List[Dict]:
        return [
            {
                "name": "Retrieve Terragraph versions",
                "function": self.get_tg_version,
                "function_args": (),
                "success_msg": "Successfully retrieved Terragraph versions",
            }
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
