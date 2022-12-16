# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# This file contains a driver for the Keysight E3634A DC Power Supply
# Refer to E3634A programming manual for more information or to add other
# commands
#
# Start by connecting, then set parameters appropriate for powering device,
# and then enable output
# Example:
#   ps = PsuE3634A(name="E3634A_1", com_port="COM5")
#   if ps.connect():
#       ps.reset()
#       print(ps.id)
#       ps.voltage = 1.1
#       ps.current = 0.05
#       ps.output_enable = True
#       ps.close()
#


import time

import serial
from ctf.api_server.utf.connections.SerialConnectionserial import SerialConnection


class PsuE3634A(SerialConnection):
    _name: str
    _com_port: str
    _baud_rate: int

    def __init__(
        self, name: str = "E3634A", com_port: str = "COM1", baud_rate: int = 9600
    ):
        self._name = name
        self._com_port = com_port
        self._baud_rate = baud_rate
        self._device = None
        self._connected = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def data_bits(self) -> int:
        return 8

    @property
    def parity(self) -> str:
        return "N"

    @property
    def baud_rate(self) -> int:
        return self._baud_rate

    @property
    def stop_bits(self) -> int:
        return 1

    @property
    def com_port(self) -> str:
        return self._com_port

    @property
    def timeout(self) -> int:
        return 1

    @property
    def xonxoff(self) -> int:
        return 0

    @property
    def rtscts(self) -> int:
        return 0

    @property
    def id(self) -> str:
        # Send get ID command
        self.write(":SYST:REM;*IDN?")
        # Read back ID
        return self.read()

    @property
    def errors(self) -> str:
        # Send get error command
        self.write("SYST:ERR?")
        # Read back get error
        return self.read()

    @property
    def voltage(self) -> float:
        # Send get voltage command
        self.write(":INST:NSEL 1;:VOLT?")
        # Read back voltage
        return float(self.read())

    @voltage.setter
    def voltage(self, voltage: float) -> None:
        if voltage > 25:
            # Send set voltage range high command
            self.write(":VOLT:RANG HIGH;")
        else:
            # Send set voltage range low command
            self.write(":VOLT:RANG LOW;")

        # Send set voltage command in Volts
        self.write(":INST:NSEL 1;:VOLT %.3f;" % voltage)
        # Need to wait before sending other commands
        time.sleep(0.1)

    @property
    def current(self) -> float:
        # Send get current command
        self.write(":INST:NSEL 1;:MEAS:CURR?")
        # Read back current
        return float(self.read())

    @current.setter
    def current(self, current: float) -> None:
        # Send set current command in Amps
        self.write(":INST:NSEL 1;:CURR %.3f;" % current)

    @property
    def output_enable(self) -> bool:
        # Send get output enable command
        # self.write(":OUTP?;")
        super().send_command_device(":OUTP?;")
        # Read back output enable
        return bool(self.read())

    @output_enable.setter
    def output_enable(self, enable: bool) -> None:
        # Send enable output command
        self.write(":OUTP %i;" % enable)

    def connect(self) -> bool:
        try:
            self._device = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                bytesize=self.data_bits,
                parity=self.parity,
                stopbits=self.stop_bits,
                timeout=self.timeout,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts,
            )
            self._connected = self._device.isOpen()
            self.write(":SYST:REM;")  # Send Remote command
        except serial.SerialException:
            self._connected = False
        return self._connected

    def reset(self) -> None:
        # Send reset command
        self.write("*RST")

    def write(self, cmd: str = "") -> str:
        assert self._connected, "PSU not connected"
        return self._device.write(cmd.encode("ascii") + b"\r\n")

    def read(self) -> str:
        assert self._connected, "PSU not connected"
        time.sleep(0.1)  # Need to wait before reading
        return self._device.read(100).decode("ascii").strip()

    def close(self) -> None:
        self.write(":SYST:LOC;")  # Send local command
        self._device.close()
        self._connected = False
