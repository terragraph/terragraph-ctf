# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import base64
import codecs
import hashlib
import json
import os
import time

import serial
from ctf.common.connections.SSHConnection import SSHConnection
from scp import SCPClient


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
        is_jump_host=False,
        ip=None,
        user=None,
        password=None,
        # serial api
        serial_api_version="serial_api_v1",
        destination_path="~/Documents/",
    ):
        """
        Serial connection class use for connecting serial port and sending
        command
        :param in_port: port fd , Example /dev/ttyUSB0
        :param in_baud: Baud-rate
        :param in_parity: Parity
        :param in_data_bits: Data bits
        :param in_stop_bits: stop bits
        :param in_hw_ctrl: Flag for hardware flow control
        :param in_sw_ctrl: Flag for software flow control
        :param in_timeout:  Timeout for connection
        :param termination: termination character for command
        :param is_jump_host: flag for jump host
        :param ip: ip of jump host
        :param user: user of jump host
        :param password: password for jump host
        :param serial_api_version: api version
        :param destination_path: destination path where we copy the serial api
        """
        super().__init__()
        self.port = in_port
        self.baud = in_baud
        self.parity = in_parity
        self.data_bits = in_data_bits
        self.stop_bits = in_stop_bits
        self.timeout = in_timeout
        self.rtscts = in_hw_ctrl
        self.xonxoff = in_sw_ctrl
        self.termination = termination.encode().decode("unicode_escape")
        # jump-host parameters
        self.is_jump_host = is_jump_host
        self.ip = ip
        self.user = user
        self.password = password
        self.serial_api_version = serial_api_version
        self.destination_path = destination_path
        self.host_destination_path = None
        self.local_serial_api_path = None
        self.ssh_obj = None
        self.serial_api_host_path = None
        self.cmd_read_wait = 0.1
        self.cmd_timeout = 1
        self.child = None
        self.logs = []

    def is_serial_api_directory_present(self):
        """
        check for serial api directory present or not
        :return: True/False
        """
        is_present = False
        cmd = "cd " + self.destination_path + " && " + "ls"
        output = self.ssh_obj.send_command(cmd)
        if "serial_api_v1" in output["message"]:
            is_present = True
        else:
            cmd = "mkdir -p " + os.path.join(
                self.destination_path, self.serial_api_version
            )
            self.ssh_obj.send_command(cmd)
        return is_present

    def generate_paths(self):
        """
        Generate paths
        :return: None
        """
        cwd = os.path.realpath(__file__)
        cwd = os.path.dirname(cwd)
        source_path = os.path.join(cwd, "serial_jumphost_api", self.serial_api_version)
        self.host_destination_path = os.path.join(
            self.destination_path, self.serial_api_version
        )
        self.local_serial_api_path = os.path.join(
            source_path, "SerialConnection_api.py"
        )
        self.serial_api_host_path = os.path.join(
            self.destination_path, self.serial_api_version, "SerialConnection_api.py"
        )

    def scp_api_package_to_host(self):
        """
        scp the serial api package to destination
        :return:None
        """
        scp_client = SCPClient(self.ssh_obj.child.get_transport())
        scp_client.put(
            self.local_serial_api_path,
            self.host_destination_path,
        )

    def check_md5(self):
        """
        check md5 of serial api with local and remote.
        :return: True/False
        """
        is_md5_same = False
        with open(self.local_serial_api_path, "rb") as f:
            bytes_data = f.read()  # read file as bytes
            md5_local = str(hashlib.md5(bytes_data).hexdigest())
        # considering only Linux if Mac we always copy the file
        cmd = "md5sum " + self.serial_api_host_path
        md5_remote_result = self.ssh_obj.send_command(cmd)
        if md5_remote_result["error"] == 0:
            output = md5_remote_result["message"]
            output = output.split(" ")
            md5_remote = output[0]
            if md5_remote == md5_local:
                is_md5_same = True
        return is_md5_same

    def connect(self):
        """
        Connect to serial port or Jump host
        :return: result dictionary
        """
        result_dict = {"error": 0, "message": ""}
        try:
            if self.is_jump_host:
                self.ssh_obj = SSHConnection(
                    in_ip_address=self.ip,
                    in_user=self.user,
                    in_password=self.password,
                    login_timeout=60,
                    is_jump_host=True,
                )
                result = self.ssh_obj.connect()
                if result["error"] == 0:
                    self.generate_paths()
                    if not self.is_serial_api_directory_present():
                        self.scp_api_package_to_host()
                    elif not self.check_md5():
                        self.scp_api_package_to_host()
                else:
                    result_dict["error"] = 1
                    result_dict["message"] = "child is None"
                    self.logs.append("Not able to ssh to Jump host")
            else:
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
            result_dict["message"] = str(e)
            self.logs.append(str(e))
        return result_dict

    def disconnect(self):
        """
        Disconnect from serial port
        :return:None
        """
        if self.is_jump_host:
            self.ssh_obj.disconnect()
        else:
            if self.child:
                self.child.close()

    def send_command_device(self, cmd):
        """
        send command to device
        :param cmd:command
        :return:result dictionary
        """
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

    def set_parity(self):
        """
        return parity value for serial api
        :return: int 0/1/2
        """
        parity = 0
        if self.parity == serial.PARITY_NONE:
            parity = 0
        elif self.parity == serial.PARITY_ODD:
            parity = 1
        elif self.parity == serial.PARITY_EVEN:
            parity = 2
        return parity

    def send_command_jump_host(self, cmd):
        """
        send command to jump host where serial device is connected
        :param cmd: command
        :return: result dictionary
        """
        result_dict_serial = {"error": 0}
        api_cmd = "python3 " + self.serial_api_host_path + " "
        hexnumber = codecs.encode(self.termination.encode(), "hex")
        hex_string = hexnumber.decode()

        arg_dict = {
            "port": self.port,
            "baud": self.baud,
            "parity": self.set_parity(),
            "data_bits": self.data_bits,
            "stop_bits": self.stop_bits,
            "rtscts": self.rtscts,
            "xonxoff": self.xonxoff,
            "termination": hex_string,
            "cmd": cmd,
            "timeout": self.cmd_timeout,
        }

        arg_string = json.dumps(arg_dict)
        arg_string_bytes = arg_string.encode("ascii")
        base64_bytes = base64.b64encode(arg_string_bytes)
        base64_message = base64_bytes.decode("ascii")
        result_dict = self.ssh_obj.send_command(api_cmd + base64_message)
        if result_dict["error"] == 0:
            message_string = result_dict["message"]
            message_string = message_string.replace("\r", "")
            message_string = message_string.replace("\n", "")
            message = message_string
            result_dict_serial["message"] = message
        else:
            result_dict_serial["error"] = 1
            result_dict_serial["message"] = result_dict["message"]
        return result_dict_serial

    def send_command(self, cmd, timeout=30):
        """
        wrapper for send_command_device function
        :param cmd: command
        :param timeout:cmd read timeout
        :return: result dictionary
        """
        result_dict = {"error": 0}
        try:
            self.cmd_timeout = timeout
            result_dict = self.connect()
            if result_dict["error"] == 0:
                if self.is_jump_host:
                    result_dict = self.send_command_jump_host(cmd)
                else:
                    result_dict = self.send_command_device(cmd)

                if type(result_dict["message"]) == list:
                    result_dict["message"] = "".join(result_dict["message"])
                    self.logs.append(result_dict["message"])
            self.disconnect()
        except Exception as e:
            result_dict["error"] = 1
            result_dict["message"] = str(e)
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
    """
    Get parity value
    :param in_parity:int
    :return: according to serial module return parity constant
    """
    parity = None
    if in_parity == 0:
        parity = serial.PARITY_NONE
    elif in_parity == 1:
        parity = serial.PARITY_ODD
    elif in_parity == 2:
        parity = serial.PARITY_EVEN
    return parity


# # Jump host
# ip_j = "2001::1"
# user_j = "alice"
# pwd_j = "password1"
# #
# if __name__ == "__main__":
#     # without jump host
#     conn = SerialConnection(in_port='/dev/ttyUSB0', in_baud=115200,
#                             in_parity=serial.PARITY_NONE, in_data_bits=8,
#                             in_stop_bits=1,
#                             in_hw_ctrl=None,
#                             in_sw_ctrl=None,
#                             termination="\r")
#     result = conn.send_command('echo_pwd')
#     print(result['message'])
#     result = conn.send_command('ls')
#     print(result['message'])
#     # with jump host
#     conn = SerialConnection(in_port='/dev/ttyUSB0', in_baud=115200,
#                             in_parity=serial.PARITY_NONE, in_data_bits=8,
#                             in_stop_bits=1,
#                             in_hw_ctrl=None,
#                             in_sw_ctrl=None,
#                             is_jump_host=True,
#                             ip=ip_j,
#                             user=user_j,
#                             password=pwd_j)
#     result = conn.send_command('echo_pwd')
#     print(result['message'])
#     result = conn.send_command('ls')
#     print(result['message'])
