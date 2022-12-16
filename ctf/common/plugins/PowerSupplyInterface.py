# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import time


logger = logging.getLogger(__name__)


class PowerSupplyInterface:
    def __init__(self):
        self.callback_list = []
        self.connection = None

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_voltage(self, timeout) -> float:
        cmd = ":INST:NSEL 1;:VOLT?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_voltage(self, voltage: float, timeout) -> {}:
        if voltage > 25:
            cmd = ":VOLT:RANG HIGH;:INST:NSEL 1;:VOLT " + str(voltage) + ";"
        else:
            cmd = ":VOLT:RANG LOW;:INST:NSEL 1;:VOLT " + str(voltage) + ";"
        result = self.connection.send_command(cmd, timeout)
        # Need to wait before sending other commands
        time.sleep(0.1)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_current(self, timeout) -> float:
        cmd = ":SYST:REM;:INST:NSEL 1;:MEAS:CURR?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_current(self, current: float, timeout) -> {}:
        cmd = ":INST:NSEL 1;:CURR " + str(current) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_output_enable(self, timeout) -> bool:
        cmd = ":OUTP?;"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_output_enable(self, output_enable: bool, timeout) -> {}:
        cmd = ":OUTP " + str(int(output_enable)) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    def custom_fun(self):
        logger.debug("hello from Power Supply Interface")
