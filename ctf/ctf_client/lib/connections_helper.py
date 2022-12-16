# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import tempfile

from ctf.common.connections import (
    SerialConnection as SERIAL,
    SSHConnection as SSH,
    TelnetConnection as TELNET,
)
from ctf.common.connections.constants import ConnectionTypeEnum
from ctf.common.helper_functions import b64_decode_and_write_file, get_driver_class_obj
from ctf.common.plugins import plugin_manager
from prettytable import PrettyTable

logger = logging.getLogger(__name__)


class JumpHostConnectionClass:
    def __init__(self):
        self.ip_address = None
        self.username = None
        self.password = None
        self.private_ip_address = None
        self.prompt = None
        self.available_ports = None
        self.private_key = None


class SSHConnectionClass:
    def __init__(self):
        self.ip_address = None
        self.username = None
        self.password = None
        self.prompt = None
        self.timeout = None
        self.custom_channel_processing = None
        self.shell_family_name = None
        self.jump_host = None
        self.private_key = None


class SerialConnectionClass:
    def __init__(self):
        self.port_name = None
        self.baud_rate = None
        self.parity = None
        self.data_bits = None
        self.stop_bits = None
        self.request_to_send = None
        self.transmit_on = None
        self.timeout = None
        self.jump_host = None
        self.termination = None


class TelnetConnectionClass:
    def __init__(self):
        self.username = None
        self.password = None
        self.host = None
        self.port = None
        self.prompt = None
        self.timeout = None
        self.jump_host = None


def check_plugin_availability(class_name, function_name):
    pm = plugin_manager.PluginManager()
    return pm.load_plugin_function(class_name, function_name)


def create_ssh_connection(ssh_conn_db_obj) -> ():
    # Get the required parameters from ssh connection db obj
    ssh_obj = SSH.SSHConnection(
        in_ip_address=ssh_conn_db_obj.ip_address,
        port=ssh_conn_db_obj.port,
        in_user=ssh_conn_db_obj.username,
        in_password=ssh_conn_db_obj.password,
        in_prompt=ssh_conn_db_obj.prompt,
        login_timeout=ssh_conn_db_obj.timeout,
        custom_channel_processing=ssh_conn_db_obj.custom_channel_processing,
        shell_family_name=ssh_conn_db_obj.shell_family_name,
        available_ports=ssh_conn_db_obj.jump_host.available_ports
        if ssh_conn_db_obj.jump_host
        else 22,
        in_private_key=ssh_conn_db_obj.private_key,
    )

    # Check if this connection in behind the jumphost
    if ssh_conn_db_obj.jump_host:
        # Get the jump host details
        jumphost = ssh_conn_db_obj.jump_host
        ssh_obj.inj_user = jumphost.username
        ssh_obj.inj_ipj_public_address = jumphost.ip_address
        ssh_obj.inj_password = jumphost.password
        ssh_obj.inj_ipj_private_address = jumphost.private_ip_address
        ssh_obj.is_jump_host = True
        ssh_obj.inj_private_key = jumphost.private_key

    # Try to connect
    result = ssh_obj.connect()
    return result, ssh_obj


def create_serial_connection(serial_conn_db_obj) -> ():
    # Get the required parameters from serial connection obj
    serial_obj = SERIAL.SerialConnection(
        in_port=serial_conn_db_obj.port_name,
        in_baud=serial_conn_db_obj.baud_rate,
        in_parity=SERIAL.get_parity_value(serial_conn_db_obj.parity),
        in_data_bits=serial_conn_db_obj.data_bits,
        in_stop_bits=serial_conn_db_obj.stop_bits,
        in_hw_ctrl=serial_conn_db_obj.request_to_send,
        in_sw_ctrl=serial_conn_db_obj.transmit_on,
        in_timeout=serial_conn_db_obj.timeout,
        termination=serial_conn_db_obj.termination,
    )
    if serial_conn_db_obj.jump_host:
        # Get the jump host details
        jumphost = serial_conn_db_obj.jump_host
        serial_obj.user = jumphost.username
        serial_obj.ip = jumphost.ip_address
        serial_obj.password = jumphost.password
        serial_obj.is_jump_host = True
    result = serial_obj.connect()
    return result, serial_obj


def create_telnet_connection(telnet_conn_db_obj) -> ():
    telnet_obj = TELNET.TelnetConnection(
        in_user=telnet_conn_db_obj.username,
        in_password=telnet_conn_db_obj.password,
        in_ip_address=telnet_conn_db_obj.host,
        in_port=telnet_conn_db_obj.port,
        in_prompt=telnet_conn_db_obj.prompt,
        in_timeout=telnet_conn_db_obj.timeout,
    )
    # Check if this connection in behind the jumphost
    if telnet_conn_db_obj.jump_host:
        # Get the jump host details
        jumphost = telnet_conn_db_obj.jump_host
        telnet_obj.inj_user = jumphost.username
        telnet_obj.inj_ipj_address = jumphost.ip_address
        telnet_obj.inj_password = jumphost.password
        telnet_obj.inj_prompt = jumphost.prompt
        telnet_obj.is_jump_host = True
        # Get the available ports
        available_ports_str = jumphost.available_ports
        port_list = available_ports_str.split(",")
        telnet_obj.available_ports = port_list
        # Query the model and get the next available port

    result = telnet_obj.connect()
    return result, telnet_obj


def get_ssh_connection_class(connection):
    obj = SSHConnectionClass()
    obj.ip_address = connection["ip_address"]
    obj.username = connection["username"]
    obj.password = connection["password"]
    obj.prompt = connection["prompt"]
    obj.port = connection["port"]
    obj.timeout = connection["timeout"]
    obj.custom_channel_processing = connection["custom_channel_processing"]
    obj.shell_family_name = (
        connection["shell_family"]["name"] if connection["shell_family"] else None
    )
    obj.private_key = connection.get("private_key", None)
    if connection["jump_host"]:
        jump_host_obj = JumpHostConnectionClass()
        jump_host_obj.username = connection["jump_host"]["username"]
        jump_host_obj.password = connection["jump_host"]["password"]
        jump_host_obj.ip_address = connection["jump_host"]["ip_address"]
        jump_host_obj.private_ip_address = connection["jump_host"]["private_ip_address"]
        jump_host_obj.available_ports = connection["jump_host"]["available_ports"]
        jump_host_obj.private_key = connection["jump_host"].get("private_key", None)
        obj.jump_host = jump_host_obj

    return obj


def get_serial_connection_class(connection):
    obj = SerialConnectionClass()
    obj.port_name = connection["port_name"]
    obj.baud_rate = connection["baud_rate"]
    obj.parity = connection["parity"]
    obj.data_bits = connection["data_bits"]
    obj.stop_bits = connection["stop_bits"]
    obj.request_to_send = connection["request_to_send"]
    obj.transmit_on = connection["transmit_on"]
    obj.timeout = connection["timeout"]
    obj.termination = connection["termination_character"]
    if connection["jump_host"]:
        jump_host_obj = JumpHostConnectionClass()
        jump_host_obj.username = connection["jump_host"]["username"]
        jump_host_obj.password = connection["jump_host"]["password"]
        jump_host_obj.ip_address = connection["jump_host"]["ip_address"]
        jump_host_obj.private_key = connection.get("private_key", None)
        obj.jump_host = jump_host_obj
    return obj


def get_telnet_connection_class(connection):
    obj = TelnetConnectionClass()
    obj.username = connection["username"]
    obj.password = connection["password"]
    obj.host = connection["host"]
    obj.port = connection["port"]
    obj.prompt = connection["prompt"]
    obj.timeout = connection["timeout"]
    if connection["jump_host"]:
        jump_host_obj = JumpHostConnectionClass()
        jump_host_obj.username = connection["jump_host"]["username"]
        jump_host_obj.password = connection["jump_host"]["password"]
        jump_host_obj.ip_address = connection["jump_host"]["ip_address"]
        jump_host_obj.available_ports = connection["jump_host"]["available_ports"]
        jump_host_obj.prompt = connection["jump_host"]["prompt"]
        jump_host_obj.private_key = connection.get("private_key", None)
        obj.jump_host = jump_host_obj

    return obj


def load_connections_of_devices(db_connection_objs) -> []:
    """
    Function called to load the connections of given devices.
    :param db_connection_objs: contains the list of devices along with their
    connection details to load.
    :return: returns the list of all loaded device connections.
    """
    device_connections = []
    for each_obj in db_connection_objs:
        device_connection = None
        conn_type = each_obj["connection_type"]
        # ssh connection
        if conn_type == ConnectionTypeEnum.SSH:
            obj = get_ssh_connection_class(each_obj)
            _, device_connection = create_ssh_connection(obj)
        # telnet
        elif conn_type == ConnectionTypeEnum.TELNET:
            obj = get_telnet_connection_class(each_obj)
            _, device_connection = create_telnet_connection(obj)
        # serial
        elif conn_type == ConnectionTypeEnum.SERIAL:
            obj = get_serial_connection_class(each_obj)
            _, device_connection = create_serial_connection(obj)
        if device_connection:
            device_connections.append(device_connection)

    # Return connections
    return device_connections


def get_device_module(function_class, device_class, connections_list):
    """
    Function to get initialized instance of connection of given class.
    :param function_class: contains function name which is to be checked
    that is it available or not in given device class name.
    :param device_class: contains class name in which function name needs
    to be checked.
    :param connections_list: contains the list of connections.
    :return: returns the initialized instance of connection module for
    given class.
    """
    module = None
    try:

        # Create module object for the given class and function
        class_module = check_plugin_availability(device_class, function_class)
        module = class_module()
        if module:
            device_connections = load_connections_of_devices(connections_list)
            # TODO pass in connection type for multiple connection devices
            if len(device_connections) > 0:
                module.connection = device_connections[0]

    except Exception as e:
        raise Exception(str(e))

    return module


def get_devices_and_connections(result_dict):
    t = PrettyTable(["Node Number", "Device Name", "Device Type"])

    devices_and_connections = {}
    for result in result_dict:

        device_type = result["device_type_data"]
        module = get_device_module(
            "custom_fun", device_type["device_class_name"], result["connections"]
        )
        if module:
            t.add_row(
                [
                    str(result["node_number"]),
                    result["name"],
                    device_type["device_type_name"],
                ]
            )
            if "driver_file" in result:
                with tempfile.TemporaryDirectory() as temp_dir:
                    driver_file_name = (
                        f"{result['device_id']}_{result['driver_file_name']}"
                    )
                    b64_decode_and_write_file(
                        temp_dir, driver_file_name, result["driver_file"]
                    )
                    driver_class_obj = get_driver_class_obj(temp_dir, driver_file_name)
                    driver_instance = driver_class_obj(module=module)
                    module.set_driver(driver_instance)
            module.metadata = result
            devices_and_connections[result["node_number"]] = module

    logger.info(t)

    return devices_and_connections
