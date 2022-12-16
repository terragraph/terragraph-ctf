# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# This file contains a driver for the MiniCircuits RC4DAT line of attenuators
# Refer to RC4DAT programming manual for more information or to add other commands
#
# Start by configuring the attenuator, then set parameters appropriate for
# measurement, and then read measurement
# Example:
#   attenuator = RC4DAT(name="RC4DAT_1", address="10.102.81.211")
#   if attenuator.connect():
#       print(attenuator.id)
#       print(attenuator.att_values)
#       print(attenuator.set_attenuators(attenuators=['1:1.25', '2:2.5',
#                                                   '3:3.75', '4:4']))
#       print(attenuator.get_attenuators(attenuators=['1', '2', '3', '4']))
#       print(attenuator.set_attenuators(attenuators=['4:3.50', '2:3.0',
#                                                   '3:0.50']))
#       print(attenuator.get_attenuators(attenuators=['4', '2', '3']))
#       attenuator.close()

import telnetlib
import time

from common.telnet import TelnetConnection


class RC4DAT(TelnetConnection):
    _name: str
    _address: str
    _port: int
    _username: str
    _password: str

    def __init__(
        self,
        name: str = "RC4DAT",
        address: str = "",
        port: int = 23,
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
        mn = self.model
        sn = self.serial
        hw = self.hardware
        fw = self.firmware

        if len(mn) and len(sn) and len(hw) and len(fw):
            ret_str = "Mini Circuits," + mn + "," + sn + "," + hw + "," + fw
        else:
            ret_str = "Device not connected!"

        return ret_str

    @property
    def model(self) -> str:
        # Send get model command
        self.write(":MN?")
        # Read back model
        return self.read().split("=")[1]

    @property
    def serial(self) -> str:
        # Send get serial number command
        self.write(":SN?")
        # Read back serial number
        return self.read().split("=")[1]  # Read back Serial

    @property
    def hardware(self) -> str:
        return "N/A"

    @property
    def firmware(self) -> str:
        self.write(":FIRMWARE?")
        return self.read()  # Read back Firmware

    @property
    def att_values(self) -> []:
        self.write("ATT?")  # Send get attenuators command
        return self.read().split("  ")

    def get_attenuators(self, attenuators: []) -> []:
        # Example: get_attenuators(['1', '2', '3', '4'])
        values = self.att_values
        ret = []
        # Return attenuator states
        for att in attenuators:  # loops from 0 to 3
            ret.append(str(att) + ":" + values[int(att) - 1])

        return ret

    def set_attenuators(self, attenuators: []) -> int:
        # Example: set_att_per_chan(['1:1.25', '2:2.5', '3:3.75', '4:4'])
        # Format of list elements: 'Channel:Attenuation'
        cmd = ":SetAttPerChan"
        for sw in range(len(attenuators)):
            cmd += ": " + attenuators[sw]

        self.write(cmd)  # Send set attenuation per channel command
        return len(self.read()) > 0  # Command char is compared to return in read

    def connect(self) -> bool:
        try:
            self._device = telnetlib.Telnet(
                host=self.address, port=self.port, timeout=self.timeout
            )
            self._connected = self._device is not None
        except Exception:
            self._connected = False

        return self._connected

    def write(self, cmd: str) -> str:
        assert self._connected, "Attenuator not connected"
        return self._device.write(cmd.encode("ascii") + b"\n")

    def read(self) -> str:
        assert self._connected, "Attenuator not connected"
        time.sleep(0.1)  # Need to wait before reading
        return self._device.read_eager().decode("ascii").strip()

    def close(self):
        self._device.close()
        self._connected = False
