#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import time
from typing import Dict, List

from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaChrony(PumaTgCtfTest):
    TEST_NAME = "PUMA: Chrony"
    DESCRIPTION = "Verify that chrony has synced time."
    LOG_FILES = ["/var/log/chrony/chrony.log"]

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        return {
            i: {
                "node_config": {
                    "sysParams": {
                        "ntpServers": {
                            "1": "time1.facebook.com",
                            "2": "time2.facebook.com",
                            "3": "time3.facebook.com",
                        }
                    }
                }
            }
            for i in range(1, num_nodes + 1)
        }

    def get_test_steps(self) -> List[Dict]:
        return [
            {
                "name": "Wait for chrony to sync time",
                "function": time.sleep,
                "function_args": (30,),
                "success_msg": "Finished waiting",
            },
            {
                "name": "Check that chrony has synced time properly",
                "function": self.verify_chrony_sync,
                "function_args": (1,),
                "success_msg": "Chrony synced time successfully",
            },
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
