#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import TestFailed
from ctf.ctf_client.runner.lib import BaseCtfTest

LOG = logging.getLogger(__name__)


class TestHello(BaseCtfTest):
    TEST_NAME = "CTF: Hello"
    DESCRIPTION = "Test CTF CTF framework sanity"

    def _get_date(self) -> None:
        cmd: str = "date"
        futures: Dict = self.run_cmd(cmd, node_ids=[1])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise TestFailed(f"Node {result['node_id']} failed to run {cmd}")
            self.log_to_ctf(f'The date on the DU is "{result["message"]}"', "info")

    def get_test_steps(self) -> List[Dict]:
        return [
            {
                "name": "Fetch the date from the DU",
                "function": self._get_date,
                "function_args": (),
                "success_msg": "Got date from DU",
            }
        ]


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
