# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# This file contains a driver for the Keysight N5172B Signal Generator
# Refer to N5172B programming manual for more information or to add other
# commands
#
# Start by setting parameters appropriate for measurement, and then enable output
# Example:
#   sg = SigGen845(name="N5172B_1", address="10.102.81.201")
#   if sg.connect():
#       sg.reset()
#       print(sg.id)
#       sg.center_freq = 1E7
#       sg.pow = 11.1
#       sg.output_enable = True
#       sg.close()
#


import telnetlib
import time

from ctf.api_server.utf.connections.telnet import TelnetConnection


class SigGenN5172B(TelnetConnection):
    _name: str
    _address: str
    _port: int
    _username: str
    _password: str

    def __init__(
        self,
        name: str = "N5172B",
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
    def start_freq(self) -> float:
        # Send get start freq command
        return float(self.write(":FREQ:STAR?"))

    @start_freq.setter
    def start_freq(self, start_freq: float) -> None:
        # Send set start freq command
        self.write(":FREQ:STAR %.6f;" % start_freq)

    @property
    def stop_freq(self) -> float:
        # Send get stop freq command
        return float(self.write(":FREQ:STOP?"))

    @stop_freq.setter
    def stop_freq(self, stop_freq: float) -> None:
        # Send set stop freq command
        self.write(":FREQ:STOP %.6f;" % stop_freq)

    @property
    def cw_freq(self) -> float:
        # Send get cw freq command
        return float(self.write(":FREQ:CW?"))

    @cw_freq.setter
    def cw_freq(self, cw_freq: float) -> None:
        # Send set cw freq command
        self.write(":FREQ:CW %.6f;" % cw_freq)

    @property
    def power(self) -> float:
        # Send get power command
        return float(self.write(":POW?"))

    @power.setter
    def power(self, power: float) -> None:
        # Send set power command
        self.write(":POW %.2f;" % power)

    @property
    def output_enable(self) -> bool:
        # Send get output enable command
        return self.write(":OUTP?;") == "1"

    @output_enable.setter
    def output_enable(self, enable: bool) -> None:
        # Send enable output command
        self.write(":OUTP %i;" % enable)

    @property
    def mod_file(self) -> str:
        # Send get output enable command
        return self.write(":RAD:ARB:WAV?;")

    @mod_file.setter
    def mod_file(self, file: str) -> None:
        # Send enable output command
        self.write(":RAD:ARB:WAV '%s';" % file)

    @property
    def arb(self) -> bool:
        # Send get arb enable command
        return self.write(":RAD:ARB:STAT?;") == "1"

    @arb.setter
    def arb(self, enable: bool) -> None:
        # Send enable arb command
        self.write(":RAD:ARB:STAT %i;" % enable)

    @property
    def mod_enable(self) -> bool:
        # Send get output enable command
        return self.write(":OUTP:MOD?;") == "1"

    @mod_enable.setter
    def mod_enable(self, enable: bool) -> None:
        # Send enable output command
        self.write(":OUTP:MOD %i;" % enable)

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

    def write(self, cmd) -> str:
        assert self._connected, "SigGen not connected"
        # print(cmd)
        self._device.write(cmd.encode("ascii") + b"\r\n")
        return self.read()

    def read(self) -> str:
        assert self._connected, "SigGen not connected"
        # Need to wait before reading
        time.sleep(0.1)
        ret = (
            self._device.read_until(b"SCPI> ").decode("ascii").rstrip("SCPI> ").strip()
        )
        if ret == "<Device Clear>":
            ret = (
                self._device.read_until(b"SCPI> ")
                .decode("ascii")
                .rstrip("SCPI> ")
                .strip()
            )

        return ret

    def close(self) -> None:
        self._device.close()
        self._connected = False
