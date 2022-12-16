# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import traceback

from ctf.common.plugins.BaseInterfaceClass import BaseInterfaceClass


logger = logging.getLogger(__name__)


class TerragraphTrafficGenInterface(BaseInterfaceClass):
    def __init__(self):
        super().__init__()

    def device_type(self):
        return "terragraph_traffic_gen"

    def action_custom_command(self, cmd, timeout=50) -> {}:
        return self.connection.send_command(cmd=cmd, timeout=timeout)


def log_traceback_info():

    # It will traceback and save line of exception in total logs
    traceback_info = traceback.format_exc()
    if traceback_info is not None:
        exec_line1 = "\n####Exception Traceback ####\n"
        exec_line2 = str(traceback_info)
        exec_line3 = "\n##################################\\n"
        saving_exception = exec_line1 + exec_line2 + exec_line3
        logger.error(saving_exception)
