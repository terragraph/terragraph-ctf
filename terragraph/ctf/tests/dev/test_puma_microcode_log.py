#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgMicrocodeLog(PumaTgCtfTest):
    TEST_NAME = "PUMA: Test retrieving microcode logs"
    DESCRIPTION = "Retrieve microcode logs from all devices using wil_fw_trace."

    def pre_run(self) -> None:
        self.log_to_ctf("No pre-run needed for this test")

    def get_test_steps(self) -> List[Dict]:
        return [
            {
                "name": f"Retrieve microcode logs from node {node_id}",
                "function": self._run,
                "function_args": (node_id,),
                "success_msg": (
                    f"Successfully retrieved microcode logs from node {node_id}"
                ),
            }
            for node_id in self.get_tg_devices()
        ]

    def _run(self, node_id: int) -> None:
        pci_ids = self.get_radio_pci_ids(node_id)
        for pci_id in pci_ids:
            LOG.info(f"Getting microcode logs for {pci_id} on node {node_id}")
            self.run_wil_fw_trace(node_id, pci_id, get_ucode_logs=True)


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
