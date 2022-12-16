# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

from ctf.common.plugins.BaseInterfaceClass import BaseInterfaceClass

logger = logging.getLogger(__name__)


class TerragraphInterface(BaseInterfaceClass):
    def __init__(self):
        super().__init__()
        self.callback_list = []

    def device_type(self):
        return "terragraph"

    def action_custom_command(self, cmd, timeout=60) -> {}:
        return self.connection.send_command(cmd=cmd, timeout=timeout)
