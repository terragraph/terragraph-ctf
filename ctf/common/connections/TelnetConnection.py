# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import telnetlib
import time

import pexpect


# Constants
KEY_OUTCOME = "error"
KEY_OUTPUT = "message"


class TelnetConnection(object):
    def __init__(
        self,
        in_ip_address,
        in_user,
        in_password,
        in_port,
        in_prompt,
        in_timeout=60,
        is_jump_host=False,
        inj_user=None,
        inj_ipj_address=None,
        inj_password=None,
        inj_prompt=None,
        jum_host_ports=None,
    ):
        """
        Telnet connection class use for connecting node using Telnet protocol.
        It have methods to send command to remote end And also have capability
        Jump-host
        :param in_ip_address: ip address of remote node
        :param in_user: user od remote node
        :param in_password: password of remote node
        :param in_port: port number
        :param in_prompt: prompt of remote node
        :param in_timeout: timeout to connect remote node
        :param is_jump_host: flag for jump host
        :param inj_user: user for jump host
        :param inj_ipj_address: ip address for jump host
        :param inj_password: password for jump host
        :param inj_prompt: prompt for jump host
        :param jum_host_ports: jup host port list
        """
        super().__init__()
        self.ip_address = in_ip_address.strip()
        self.user = in_user
        self.password = in_password
        self.port = in_port
        self.prompt = in_prompt
        self.timeout = in_timeout
        self.is_jump_host = is_jump_host
        self.inj_user = inj_user
        self.inj_ipj_address = inj_ipj_address
        self.inj_password = inj_password
        self.inj_prompt = inj_prompt
        self.available_ports = jum_host_ports
        self.ip_address_backup = None
        self.port_backup = None
        self.local_port = None
        self.child = None
        self.child_jump_host = None
        self.logs = []

    # look for is tunnel created or not
    def is_tunnel_created(self, timeout):
        """
        look for is tunnel created
        :param timeout: timeout
        :return: True/False
        """
        # Send the password
        result = False
        error_string = "Address already in use"
        self.child_jump_host.sendline(self.inj_password)
        prompt = self.inj_prompt.rstrip()
        prompt = prompt[-1]
        if prompt == "$":
            prompt = r"\$"
        i = self.child_jump_host.expect(
            [prompt, error_string, pexpect.TIMEOUT, pexpect.EOF], timeout=timeout
        )
        if i == 0:
            result = True
        if i == 1:
            print("Port already used by other device.")
            self.logs.append("Port already used by other device.")
        return result

    # Function for creating tunnel for jump host
    def create_tunnel(self):
        """
        Create tunnel
        :return: True/False
        """
        timeout = 10
        result = False

        cnt = 0
        while cnt < len(self.available_ports) and not result:
            try:
                # Get the port
                self.local_port = self.available_ports[cnt]

                args = [
                    self.inj_user + "@" + self.inj_ipj_address,
                    "-L "
                    + self.local_port
                    + ":["
                    + self.ip_address
                    + "]:"
                    + str(self.port),
                ]
                command = "ssh"
                self.child_jump_host = pexpect.spawn(command=command, args=args)
                self.child_jump_host.delaybeforesend = 0.0
                p = self.child_jump_host.expect(
                    ["[P/p]assword:", "(yes/no)", pexpect.TIMEOUT, pexpect.EOF],
                    timeout=timeout,
                )
                # If password is asked
                if p == 0:
                    result = self.is_tunnel_created(timeout)
                # If received yes/no confirmation
                elif p == 1:
                    # Send yes
                    self.child_jump_host.sendline("yes")
                    k = self.child_jump_host.expect(
                        ["[P/p]assword:", pexpect.TIMEOUT, pexpect.EOF], timeout=timeout
                    )
                    # If received password
                    if k == 0:
                        result = self.is_tunnel_created(timeout)
                else:
                    result = False
            except Exception as e:
                print(e)
                result = False
                self.logs.append(str(e))

            # Increment the count
            cnt += 1

        return result

    def connect(self):
        """
        Connect to remote node using Telnet protocol
        :return: result dictionary
        """
        result = {"error": 0, "message": ""}
        try:
            if self.is_jump_host:
                if self.create_tunnel():
                    # change credentials
                    self.ip_address_backup = self.ip_address
                    self.port_backup = self.port
                    self.ip_address = "127.0.0.1"
                    self.port = self.local_port
                # else:
                #     is_tunnel_ready = False

            self.child = telnetlib.Telnet(
                host=self.ip_address, port=self.port, timeout=self.timeout
            )

            if self.child:
                # Read to clear anything in buffer before login
                value = self.__read(self.prompt)
                # Append to logs
                self.logs.append(value)
                if "login:" in value:
                    result_dict = self.__send_command_until(self.user, "Password:")
                    is_outcome = KEY_OUTCOME in result_dict
                    if is_outcome and result_dict[KEY_OUTCOME] == 0:
                        result_dict = self.__send_command_until(
                            self.password, "Last login:"
                        )
                        if is_outcome and result_dict[KEY_OUTCOME] == 0:
                            # Read to clear anything in buffer after login
                            self.__read(self.prompt)
                else:
                    result["error"] = 0
            else:
                result["error"] = 1
                self.logs.append("Failed to create the telnet connection")
        except Exception as e:
            result["error"] = 1
            result["message"] = str(e)
            self.logs.append(str(e))

        return result

    def disconnect(self):
        """
        Disconnect from remote node
        :return: None
        """
        if self.is_jump_host:
            # change credential to orignal param
            self.ip_address = self.ip_address_backup
            self.port = self.port_backup
        # close child
        if self.child:
            self.child.close()
        # close tunnel if it is open
        if self.child_jump_host:
            self.child_jump_host.close()

    def send_command(
        self, cmd, timeout=None, expected_output: str = None, read_delay: float = 0.1
    ):
        """
        Send command to remote node
        :param cmd: command
        :param timeout: timeout for command
        :return: result dictionary
        """
        result_dict = {}
        if not expected_output:
            expected_output = self.prompt
        result = False
        # is_tunnel_ready = True
        try:
            result = self.connect()
            if "error" in result and result["error"] == 0:
                if self.child:
                    # Add command to logs
                    self.logs.append(cmd)
                    self.child.write(cmd.encode("ascii") + b"\r\n")

                    try:
                        message = self.__read(expected_output, timeout, read_delay)
                        # Add the received output in logs
                        self.logs.append(message)
                        if (
                            expected_output in message
                            or expected_output == "*"
                            or expected_output == " "
                        ):
                            result = True
                        else:
                            message = "Expected output not found"
                    except EOFError as e:
                        result = False
                        message = str(e)
                        self.logs.append(message)
                else:
                    message = (
                        "No Telnet session found to write the command for "
                        + self.ip_address
                    )
                    self.logs.append("Failed to write to Telnet")
            else:
                message = "Telnet connection failed for " + self.ip_address
                self.logs.append("Telnet connection failed for " + self.ip_address)

        except Exception as e:
            message = (
                "=================Exception On=====================\n"
                + "Cmd => "
                + cmd
                + "\nIp => "
                + self.ip_address
                + "\nError => "
                + str(e)
                + "\n================================================"
            )
            self.logs.append(message)

            # disconnect
        finally:
            self.disconnect()

        if result:
            result_dict[KEY_OUTCOME] = 0
            result_dict[KEY_OUTPUT] = message
        else:
            result_dict[KEY_OUTCOME] = 1
            result_dict[KEY_OUTPUT] = message

        return result_dict

    def __send_command_until(self, cmd, expected_output, timeout=None):
        """
        used in connect
        :param cmd: command
        :param expected_output: expected
        :param timeout: timeout for command
        :return: result dictionary
        """
        result_dict = {}
        result = False
        try:
            if self.child:
                self.child.write(cmd.encode("ascii") + b"\r\n")
                try:
                    message = self.__read(expected_output, timeout)
                    if expected_output in message:
                        result = True
                    else:
                        message = "Expected output not found"
                except EOFError as e:
                    result = False
                    message = str(e)
            else:
                message = (
                    "No Telnet session found to write the command for "
                    + self.ip_address
                )
        except Exception as e:
            message = (
                "=================Exception On=====================\n"
                + "CTF Cmd => "
                + cmd
                + "\nCTF Ip => "
                + self.ip_address
                + "\nCTF Error => "
                + str(e)
                + "\n================================================"
            )
        if result:
            result_dict[KEY_OUTCOME] = 0
            result_dict[KEY_OUTPUT] = message
        else:
            result_dict[KEY_OUTCOME] = 1
            result_dict[KEY_OUTPUT] = message
        return result_dict

    def __read(self, expected, timeout=None, read_delay: float = 0.1):
        """
        read from remote end
        :param expected: expected output
        :param timeout: timeout
        :return: output of read
        """
        if self.child:
            # Need to wait before reading output
            time.sleep(read_delay)
            enc_expected = expected.encode("ascii")
            cmd_timeout = 10
            if timeout:
                cmd_timeout = timeout
            if expected == "*":
                output = self.child.read_eager().decode("ascii").rstrip().strip()
            else:
                output = (
                    self.child.read_until(enc_expected, timeout=cmd_timeout)
                    .decode("ascii")
                    .rstrip()
                    .strip()
                )
        else:
            output = "No Telnet session found to write the command for "
            output += self.ip_address
        return output


# # Target
# ip_address = "2001::1"
# user = ""
# password = ""
# port = "5023"
# prompt = "SCPI>"
# timeout = 60
#
# # jump host
# j_user = "root"
# j_ip_address = "2001::2"
# j_password = "password1"
# j_prompt = "#"
#
# # local port
# local_port = ["2222"]

# # Target
# ip_address = "2001::3"
# user = "alice"
# password = "password2"
# port = "23"
# prompt = "$"
# timeout = 60
#
# # jump host
# j_user = "bob"
# j_ip_address = "2001::4"
# j_password = "password3"
# j_prompt = "$"
#
# # local port
# local_port = ["2222"]
#
# # Sample test code
# if __name__ == "__main__":
#     print("--------------Telnet TEST ------------------------")
#     # Telnet test without jump host
#     tel_obj = TelnetConnection(
#         ip_address, user, password, port, prompt, timeout)
#     output = tel_obj.send_command("ls")
#     print(output["message"])
#     output = tel_obj.send_command("pwd")
#     print(output["message"])
#     # Telnet test with jump host
#     tel_obj = TelnetConnection(
#         ip_address, user, password, port, prompt, timeout, True, j_user,
#         j_ip_address, j_password, j_prompt, local_port)
#     output = tel_obj.send_command("ls")
#     print(output["message"])
#     output = tel_obj.send_command("pwd")
#     print(output["message"])
