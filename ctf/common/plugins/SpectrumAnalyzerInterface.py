# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

from ctf.common.plugins.BaseInterfaceClass import BaseInterfaceClass


logger = logging.getLogger(__name__)


class SpectrumAnalyzerInterface(BaseInterfaceClass):
    def __init__(self):
        super().__init__()
        self.callback_list = []

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_attenuation(self, timeout) -> {}:
        cmd = ":POW:ATT?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_attenuation(self, attenuation: int, timeout) -> {}:
        cmd = ":POW:ATT:AUTO OFF;:POW:ATT " + str(attenuation) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_attenuation_step(self, timeout) -> {}:
        cmd = ":POW:ATT:STEP?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_attenuation_step(self, attenuation_step: float, timeout) -> {}:
        cmd = ":POW:ATT:STEP " + str(attenuation_step) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_center_frequency(self, timeout) -> {}:
        cmd = ":FREQ:CENT?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_center_frequency(self, freq: float, timeout) -> {}:
        cmd = ":FREQ:CENT " + str(freq) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_correction_gain(self, timeout) -> {}:
        cmd = ":CORR:BTS:GAIN?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_correction_gain(self, gain: float, timeout) -> {}:
        cmd = ":CORR:MS:GAIN " + str(gain) + ";"
        result = self.connection.send_command(cmd, timeout)
        cmd = ":CORR:BTS:GAIN " + str(gain) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_integ_bw(self, meas, timeout) -> {}:
        if meas == "CHP":
            cmd = ":CHP:BAND:INT?"
        else:
            cmd = ":RAD:STAN:PRES?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_integ_bw(self, meas: str, bw: int, timeout) -> {}:
        if meas == "CHP":
            cmd = ":CHP:BAND:INT " + str(bw) + ";"
        else:
            cmd = ":RAD:STAN:PRES B" + str(bw) + "M;"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_span(self, timeout) -> float:
        cmd = ":FREQ:SPAN?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_span(self, span: float, timeout) -> {}:
        cmd = ":FREQ:SPAN " + str(span) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_start_frequency(self, timeout) -> float:
        cmd = ":FREQ:STAR?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_start_frequency(self, freq: float, timeout) -> {}:
        cmd = ":FREQ:STAR " + str(freq) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_stop_frequency(self, timeout) -> {}:
        cmd = ":FREQ:STOP?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_stop_frequency(self, freq: float, timeout) -> {}:
        cmd = ":FREQ:STOP " + str(freq) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    # TODO: Format return value as an integer
    def get_sweep(self, timeout) -> {}:

        cmd = ":INIT:CONT?"
        result = self.connection.send_command(cmd, timeout)
        return result

    # TODO: Put return type in function
    def set_sweep(self, sweep: int, timeout) -> {}:
        cmd = ":INIT:CONT " + str(sweep) + ";"
        result = self.connection.send_command(cmd, timeout)
        return result
