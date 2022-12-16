# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

from ctf.common.plugins.BaseInterfaceClass import BaseInterfaceClass


logger = logging.getLogger(__name__)


SWITCH_LIST = ["A", "B", "C", "D", "E", "F", "G", "H"]
VALID_TYPES = ["SPDT", "SP6T"]


class SwitchInterface(BaseInterfaceClass):
    def __init__(self):
        super().__init__()
        self.callback_list = []

    def model(self, timeout) -> str:
        cmd = ":MN?"  # Send get model command
        result = self.connection.send_command(cmd, timeout)
        mr = result["message"]
        return mr.split("=")[1]

    def type(self, timeout) -> str:
        mn = self.model(timeout).split("-")
        for st in VALID_TYPES:
            if st in mn[1]:
                return st

        return ""

    def sw_ports(self, timeout) -> int:
        cmd = "SWPORT?"  # Send get switch command
        result = self.connection.send_command(cmd, timeout)
        sp = result["message"]
        return int(sp)

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

    def get_switches(self, switches: [], timeout) -> {}:
        # Example: get_switches(['A:1', 'B:2', 'C:1', 'D:2', 'E:1', 'F:2',
        # 'G:1', 'H:2'])
        # Format of list elements: 'Switch:Port'
        ports = self.sw_ports(timeout)
        ret = []
        result = {"error": 0}
        # Return switch states
        st = self.type(timeout)
        for sw in switches:
            switch = sw.split(":")[0]
            if st == VALID_TYPES[0]:  # SPDT
                if self.switch_bit(switch) & ports:
                    ret.append(switch + ":2")
                else:
                    ret.append(switch + ":1")
            elif st == VALID_TYPES[1]:  # SP6T
                cmd = "SP6T" + switch + ":STATE?"  # Send get switch command
                result = self.connection.send_command(cmd, timeout)
                state = result["message"]
                ret.append(switch + ":" + state)

        result["message"] = ret

        return result

    def set_switches(self, switches: [], timeout) -> {}:
        # Example: set_switches(['A:1', 'B:2', 'C:1', 'D:2', 'E:1', 'F:2',
        # 'G:1', 'H:2'])
        # Format of list elements: 'Switch:Port'
        switch_mask = self.sw_ports(timeout)
        st = self.type(timeout)
        ret = False
        result = {"error": 0, "message": 0}
        # Set switch states
        if st == VALID_TYPES[0]:  # SPDT
            for sw in switches:
                switch, p = sw.split(":")
                port = int(p) - 1
                switch_mask |= self.switch_bit(switch)
                if not port:  # turn off bit
                    switch_mask ^= self.switch_bit(switch)

            cmd = "SETP=" + str(switch_mask)  # Send set switch command
            result = self.connection.send_command(cmd, timeout)
            ret = result["message"] == "1"
        elif st == VALID_TYPES[1]:  # SP6T
            ret = True
            for sw in switches:
                switch, p = sw.split(":")
                cmd = "SP6T" + switch + ":STATE:" + p  # Send set switch command
                result = self.connection.send_command(cmd, timeout)
                ret = ret and result["message"] == "1"

        result["message"] = ret

        return result
