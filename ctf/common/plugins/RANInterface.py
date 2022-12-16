# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

from ctf.common.plugins.BaseInterfaceClass import BaseInterfaceClass


logger = logging.getLogger(__name__)


class RANInterface(BaseInterfaceClass):
    def __init__(self):
        super().__init__()
        self.callback_list = []

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_tx_frequency(self, timeout) -> float:
        cmd = "etm-settxfreq"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_tx_frequency(self, freq: float, timeout) -> {}:
        cmd = "etm-settxfreq " + str(freq) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result
