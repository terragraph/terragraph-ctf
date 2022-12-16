# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# This file contains a driver for the Keysight N9030B Spectrum Analyzer
# Refer to N9030B programming manual for more information or to add other
# commands
#
# Start by configuring the measurement, then set parameters appropriate for
# measurement, and then read measurement
# Example:
#   sa = SpecAnN9030B(name="N9030B_1", address="10.102.81.200")
#   if sa.connect():
#       sa.reset()
#       print(sa.id)
#       sa.mode = "SA"
#       sa.conf = "CHP"
#       sa.center_freq = 1E7
#       sa.atten = 20
#       print(sa.chp)
#       sa.close()
#
#  Todo: RBW, VBW, MKR->, TRG


import telnetlib
import time

from ctf.api_server.utf.connections.telnet import TelnetConnection


VALID_MODE = {"SA", "BASIC", "NFIGURE", "LTE", "LTETDD"}
VALID_MEAS = {"SAN", "CHP", "OBW", "ACP", "SPUR", "SEM", "CEVM"}


class SpecAnN9030B(TelnetConnection):
    _name: str
    _address: str
    _port: int
    _username: str
    _password: str

    def __init__(
        self,
        name: str = "N9030B",
        address: str = "",
        port: int = 5023,
        username: str = "",
        password: str = "",
    ):
        self._name = name
        self._address = address
        self._port = port
        self._username = username
        self._password = password
        self._device = None
        self._connected = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    @property
    def port(self) -> int:
        return self._port

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def timeout(self) -> int:
        return 1

    @property
    def id(self) -> str:
        # Send get ID command
        return self.write("*IDN?")

    @property
    def errors(self) -> str:
        # Send get error command
        return self.write(":SYST:ERR?")

    @property
    def inst(self) -> str:
        # Send get inst command
        return self.write(":INST:SEL?")

    @inst.setter
    def inst(self, sel: str) -> None:
        # Send set conf command
        if sel in VALID_MODE:
            self.write(":INST:SEL %s;" % sel)
        else:
            raise ValueError("inst: sel must be one of %r." % VALID_MODE)

    @property
    def config(self) -> str:
        # Send get conf command
        return self.write(":CONF?")

    @config.setter
    def config(self, meas: str) -> None:
        # Send set conf command
        if meas in VALID_MEAS:
            self.write(":CONF:%s;" % meas)
        else:
            raise ValueError("conf: meas must be one of %r." % VALID_MEAS)

    @property
    def chp(self) -> str:
        # Send get channel power command
        # Returns channel_power,spectral_power_density
        return self.write(":READ:CHP?")

    @property
    def obw(self) -> str:
        # Send get channel power command
        # Returns occupied bw, freq error, and other related items
        return self.write(":READ:OBW?")

    @property
    def acp(self) -> str:
        # Send get adjacent channel power command
        # Returns total_carrier_power,acp_lower,acp_upper
        return self.write(":READ:ACP?")

    @property
    def spur(self) -> str:
        # Send get spurious emissions command
        # Returns spurious emission zones
        return self.write(":READ:SPUR?")

    @property
    def sem(self) -> str:
        # Send get spurious emissions mask command
        # Returns spurious emission mask zones
        return self.write(":READ:SEM?")

    @property
    def cevm(self) -> str:
        # Send get carrier error vector magnitude command
        # Returns evm and other related items
        return self.write(":READ:CEVM?")

    @property
    def start_freq(self) -> float:
        # Send get start freq command
        return float(self.write(":FREQ:STAR?"))

    @start_freq.setter
    def start_freq(self, start_freq: float) -> None:
        # Send set start freq command in MHz
        self.write(":FREQ:STAR %.6f;" % start_freq)

    @property
    def stop_freq(self) -> float:
        # Send get stop freq command
        return float(self.write(":FREQ:STOP?"))

    @stop_freq.setter
    def stop_freq(self, stop_freq: float) -> None:
        # Send set stop freq command in MHz
        self.write(":FREQ:STOP %.6f;" % stop_freq)

    @property
    def center_freq(self) -> float:
        # Send get center freq command
        return float(self.write(":FREQ:CENT?"))

    @center_freq.setter
    def center_freq(self, center_freq: float) -> None:
        # Send set center freq command in MHz
        self.write(":FREQ:CENT %.6f;" % center_freq)

    @property
    def span(self) -> float:
        # Send get span command
        return float(self.write(":FREQ:SPAN?"))

    @span.setter
    def span(self, span: float) -> None:
        # Send set span command in MHz
        self.write(":FREQ:SPAN %.6f;" % span)

    @property
    def corr_gain(self) -> float:
        # Send get corr gain command
        return float(self.write(":CORR:BTS:GAIN?"))

    @corr_gain.setter
    def corr_gain(self, corr_gain: float) -> None:
        # Send set corr gain command in dB
        self.write(":CORR:MS:GAIN %.2f;" % corr_gain)
        self.write(":CORR:BTS:GAIN %.2f;" % corr_gain)

    @property
    def ref_level(self) -> float:
        # Send get ref level command
        return float(self.write(":DISP:WIND:TRAC:Y:RLEV?"))

    @ref_level.setter
    def ref_level(self, ref_level: float) -> None:
        # Send set ref level command
        self.write(":DISP:WIND:TRAC:Y:RLEV %.2f;" % ref_level)

    @property
    def atten(self) -> int:
        # Send get atten command
        return int(self.write(":POW:ATT?"))

    @atten.setter
    def atten(self, atten: int) -> None:
        # Send set atten command in dB
        self.write(":POW:ATT:AUTO OFF;")
        self.write(":POW:ATT %d;" % atten)

    @property
    def atten_step(self) -> float:
        # Send get atten step command
        return float(self.write(":POW:ATT:STEP?"))

    @atten_step.setter
    def atten_step(self, atten_step: float) -> None:
        # Send set atten step command in dB
        self.write(":POW:ATT:STEP %.2f;" % atten_step)

    @property
    def sweep_auto(self) -> str:
        # Send get sweep auto command, will return 0 for off, and 1 for on
        return self.write(":INIT:CONT?")

    @sweep_auto.setter
    def sweep_auto(self, sweep_auto: str) -> None:
        # Send set sweep auto command
        self.write(":INIT:CONT %s;" % sweep_auto)

    @property
    def integ_bw(self) -> str:
        # Get inst mode
        inst = self.inst
        # Send get integ bw command
        if inst == "SA":
            return self.write(":CHP:BAND:INT?")
        else:
            return self.write(":RAD:STAN:PRES?")

    @integ_bw.setter
    def integ_bw(self, bw: int) -> None:
        # Get inst mode
        inst = self.inst
        # Send set integ bw command in MHz
        if inst == "SA":
            self.write(":CHP:BAND:INT %d" % bw)
        else:
            self.write(":RAD:STAN:PRES B%dM;" % bw)

    def marker_max(self) -> None:
        # Send marker peak command
        self.write(":CALC:MARK:MAX")

    @property
    def marker_x(self) -> float:
        # Send get marker x command
        return float(self.write(":CALC:MARK:X?"))

    @marker_x.setter
    def marker_x(self, marker_x: float) -> None:
        # Send set marker x command
        self.write(":CALC:MARK:X %.6f;" % marker_x)

    @property
    def marker_y(self) -> float:
        # Send get marker y command
        return float(self.write(":CALC:MARK:Y?"))

    @marker_y.setter
    def marker_y(self, marker_y: float) -> None:
        # Send set marker y command
        self.write(":CALC:MARK:Y %.2f;" % marker_y)

    def connect(self) -> bool:
        try:
            self._device = telnetlib.Telnet(
                host=self.address, port=self.port, timeout=self.timeout
            )
            self._connected = self._device is not None
            # Clear buffer
            self.read()
        except Exception:
            self._connected = False

        return self._connected

    def reset(self) -> None:
        # Send reset command
        self.write("*RST")

    def write(self, cmd: str) -> str:
        assert self._connected, "SpecAn not connected"
        self._device.write(cmd.encode("ascii") + b"\r\n")
        return self.read()

    def read(self) -> str:
        assert self._connected, "SpecAn not connected"
        # Need to wait before reading
        time.sleep(0.1)
        return (
            self._device.read_until(b"SCPI> ").decode("ascii").rstrip("SCPI> ").strip()
        )

    def close(self) -> None:
        # self.write(":SYST:LOC;")  # Send local command
        self._device.close()
        self._connected = False
