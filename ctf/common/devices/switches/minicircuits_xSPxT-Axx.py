# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# This file contains a driver for the MiniCircuits xSPxT-Axx line of switches
# Refer to xSPxT-Axx programming manual for more information or to add other commands
#
# Start by configuring the switch, then set parameters appropriate for measurement,
# and then read measurement
# Example:
#   rf_switch = Switch(name="SPDTA18_1", address="10.102.81.210")
#   if rf_switch.connect():
#       print(rf_switch.id)
#       print(rf_switch.switch_list)
#       print(rf_switch.temperature(sensor=1))
#       print(rf_switch.switch_counters(switches=['A']))
#       print(rf_switch.get_switches(switches=['A']))
#       print(rf_switch.set_switches(switch='A:2'))
#       rf_switch.close()


import telnetlib
import time

from ctf.api_server.utf.connections.telnet import TelnetConnection


SWITCH_LIST = ["A", "B", "C", "D", "E", "F", "G", "H"]
VALID_TYPES = ["SPDT", "SP6T"]


class Switch(TelnetConnection):
    _name: str
    _address: str
    _port: int
    _username: str
    _password: str
    _switch_list: []

    def __init__(
        self,
        name: str = "SPDTA18",
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
        self._switch_list = ["A"]
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
        return 30

    @property
    def switch_list(self) -> []:
        # sample model RC-8SPDT-A18, RC-2SP6T-A12
        # freq range A18, A12
        num = "0"
        mn = self.model.split("-")
        num = mn[1].split(self.type)
        return SWITCH_LIST[0 : int(num[0])]

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
        time.sleep(0.1)  # Need to wait before reading
        # Read back model eg. RC-8SPDT-A18
        return self.read().split("=")[1]

    @property
    def type(self) -> str:
        mn = self.model.split("-")
        for st in VALID_TYPES:
            if st in mn[1]:
                return st

        return ""

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
    def sw_ports(self) -> int:
        self.write("SWPORT?")  # Send get switch command
        sp = self.read()
        return int(sp)

    def temperature(self, sensor: int):  # -> float:
        # l Get Internal Temperature TEMP[sensor]?
        self.write(":TEMP" + str(sensor) + "?")
        t = "".join(self.read().split())  # Cleans up "+xx. x" return values
        return float(t)  # Read back Temperature

    def switch_bit(self, switch: str) -> int:
        return {
            "A": 0x01,
            "B": 0x02,
            "C": 0x04,
            "D": 0x08,
            "E": 0x10,
            "F": 0x20,
            "G": 0x40,
            "H": 0x80,
        }.get(
            switch, 0x00
        )  # 0x00 is default if x not found

    def switch_counters(self, switches: []) -> []:
        # Example: get_switch_counters(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])
        st = self.type
        counters = []
        for sw in switches:
            if st == VALID_TYPES[0]:  # SPDT
                self.write("SC" + sw + "?")  # Send get switch command
                counters.append(sw + ":" + self.read())  # Read back Switches
            elif st == VALID_TYPES[1]:  # SP6T
                self.write("SP6T" + sw + ":COUNTERS?")  # Send get switch command
                # SP6T[switch_name]:COUNTERS?
                counters.append(sw + ":" + self.read())  # Read back Switches
        return counters

    def get_switches(self, switches: []) -> []:
        # Example: get_switches(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])
        ports = self.sw_ports
        ret = []
        # Return switch states
        st = self.type
        for sw in switches:
            if st == VALID_TYPES[0]:  # SPDT
                if self.switch_bit(sw) & ports:
                    ret.append(sw + ":2")
                else:
                    ret.append(sw + ":1")
            elif st == VALID_TYPES[1]:  # SP6T
                self.write("SP6T" + sw + ":STATE?")  # Send get switch command
                state = self.read()
                ret.append(sw + ":" + state)

        return ret

    def set_switches(self, switches: []) -> int:
        # Example: set_switches(['A:1', 'B:2', 'C:1', 'D:2', 'E:1', 'F:2',
        #  'G:1', 'H:2'])
        # Format of list elements: 'Switch:Port'
        switch_mask = self.sw_ports
        st = self.type
        ret = False

        if st == VALID_TYPES[0]:  # SPDT
            for sw in switches:
                switch, p = sw.split(":")
                port = int(p) - 1
                switch_mask |= self.switch_bit(switch)
                if not port:  # turn off bit
                    switch_mask ^= self.switch_bit(switch)

            self.write("SETP=" + str(switch_mask))  # Send set switch command
            ret = self.read() == "1"

        elif st == VALID_TYPES[1]:  # SP6T
            ret = True
            for sw in switches:
                switch, p = sw.split(":")
                self.write("SP6T" + switch + ":STATE:" + p)  # Send set switch command
                time.sleep(0.25)  # Need to wait for switch before reading
                ret = ret and self.read() == "1"

        return ret

    def connect(self) -> bool:
        try:
            self._device = telnetlib.Telnet(
                host=self.address, port=self.port, timeout=self.timeout
            )
            self._connected = self._device is not None
        except Exception:
            self._connected = False

        return self._connected

    def write(self, cmd: str):
        assert self._connected, "Switch not connected"
        return self._device.write(cmd.encode("ascii") + b"\n")

    def read(self) -> str:
        assert self._connected, "Switch not connected"
        time.sleep(0.1)  # Need to wait before reading
        return self._device.read_eager().decode("ascii").strip()

    def close(self):
        self._device.close()
        self._connected = False
