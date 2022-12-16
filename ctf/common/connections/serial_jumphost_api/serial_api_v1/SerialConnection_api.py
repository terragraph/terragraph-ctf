# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import base64
import json
import sys
import time

import serial


class SerialConnection(object):
    def __init__(
        self,
        in_port,
        in_baud,
        in_parity,
        in_data_bits,
        in_stop_bits,
        in_hw_ctrl,
        in_sw_ctrl,
        in_timeout=60,
        termination="\r\n",
    ):
        super().__init__()
        self.port = in_port
        self.baud = in_baud
        self.parity = get_parity_value(in_parity)
        self.data_bits = in_data_bits
        self.stop_bits = in_stop_bits
        self.timeout = in_timeout
        self.rtscts = in_hw_ctrl
        self.xonxoff = in_sw_ctrl
        self.termination = termination
        self.cmd_read_wait = 0.1
        self.cmd_timeout = 1
        self.child = None
        self.logs = []

    def connect(self):
        result_dict = {"error": 0, "message": ""}
        try:
            self.child = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                bytesize=self.data_bits,
                parity=self.parity,
                stopbits=self.stop_bits,
                timeout=self.timeout,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts,
            )
            if self.child:
                result_dict["child"] = self
                return_value = self.child.isOpen()
                if return_value:
                    self.child.flushInput()
                    self.child.flushOutput()

            else:
                result_dict["error"] = 1
                result_dict["message"] = "child is None"
                self.logs.append("Cannot open the serial connection to the device")
        except Exception as e:
            result_dict["error"] = 1
            result_dict["message"] = e
            self.logs.append(str(e))
        return result_dict

    def disconnect(self):
        if self.child:
            self.child.close()

    def send_command_device(self, cmd):
        result_dict = {"error": 0}
        try:
            if self.child and self.child.isOpen():
                cmd_write = cmd.encode("ascii") + self.termination.encode("ascii")
                self.child.write(cmd_write)
                # Read the output and send it back
                msg = self.read()
            else:
                result_dict["error"] = 1
                msg = "The port is not open"
                self.logs.append("Failed to open the port")
        except Exception as e:
            result_dict["error"] = 1
            msg = "An Exception occurred while writing to port " + self.port
            print(str(e))
            self.logs.append(str(e))

        result_dict["message"] = msg

        return result_dict

    def send_command(self, cmd, timeout=30):
        self.cmd_timeout = timeout
        result_dict = self.connect()
        if result_dict["error"] == 0:
            result_dict = self.send_command_device(cmd)
            self.disconnect()

        return result_dict

    def read(self):
        """
        read data from serial port
        :return: read data
        """
        time.sleep(self.cmd_read_wait)  # Need to wait before reading
        output = []
        self.child.timeout = 1
        length = 1
        # Timeout
        time_spent_so_far = 0.0
        start_time = time.time()
        while length != 0 and time_spent_so_far <= self.cmd_timeout:
            msg = self.child.readline().decode("ascii").strip()
            output.append(msg)
            length = len(msg)
            delta = time.time() - start_time
            time_spent_so_far = delta
        return output


# Static methods
def get_parity_value(in_parity):
    parity = None
    if in_parity == 0:
        parity = serial.PARITY_NONE
    elif in_parity == 1:
        parity = serial.PARITY_ODD
    elif in_parity == 2:
        parity = serial.PARITY_EVEN
    return parity


if __name__ == "__main__":
    arg_jsn_string = sys.argv[1]
    base64_bytes = arg_jsn_string.encode("ascii")
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode("ascii")
    arg_dict = json.loads(message)

    hex_string_termination = arg_dict["termination"]
    in_pck_termination = ""
    i = 0
    while (len(hex_string_termination)) > i:
        hex_data = hex_string_termination[i : i + 2]
        hex_data = int(hex_data, 16)
        hex_data = chr(hex_data)
        in_pck_termination += hex_data
        i += 2
    # cmd
    conn = SerialConnection(
        in_port=arg_dict["port"],
        in_baud=arg_dict["baud"],
        in_parity=arg_dict["parity"],
        in_data_bits=arg_dict["data_bits"],
        in_stop_bits=arg_dict["stop_bits"],
        in_hw_ctrl=arg_dict["rtscts"],
        in_sw_ctrl=arg_dict["xonxoff"],
        termination=in_pck_termination,
    )
    result = conn.send_command(arg_dict["cmd"], arg_dict["timeout"])
    print(result["message"])
