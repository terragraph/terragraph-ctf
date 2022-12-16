# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

from ctf.common.plugins.BaseInterfaceClass import BaseInterfaceClass


logger = logging.getLogger(__name__)


class UeEmulatorInterface(BaseInterfaceClass):
    def __init__(self):
        super().__init__()
        self.callback_list = []

    # TODO: Update to add other test parameters
    # TODO: Format return value as an integer
    def run_test_case(self, test_case: str, timeout) -> str:
        cmd = "#$$DISCONNECT"
        self.connection.send_command(cmd, timeout=50)
        cmd = "#$$PORT %s 5001 5002 5003" % "192.168.10.10"
        self.connection.send_command(cmd, timeout=50)
        cmd = "#$$CONNECT"
        self.connection.send_command(cmd, timeout=50)
        cmd = "ABOT 0 0 0"
        self.connection.send_command(cmd, timeout=50)
        cmd = 'SCRIPT "%s" 1 1 -1 -1 -1 -1 1 0 0' % test_case
        result = self.connection.send_command(cmd, timeout)
        return result
