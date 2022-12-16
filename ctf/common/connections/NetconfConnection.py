# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import traceback
from enum import Enum

import lxml.etree as etree
from ctf.common.connections.constants import ConnErrorCode, ConnResultKey
from django.utils import timezone
from ncclient import manager

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARNING"
    ERROR = "ERROR"


def log(msg: str, level: LogLevel = LogLevel.INFO):
    return f"[{timezone.now()}] [{level.value}] NetconfConnection: {msg}"


def exception_message(action, ex):
    return f"Exception of type {type(ex).__name__} occured during {action}: {str(ex)}\n\n{traceback.format_exc()}"


def pretty_xml_format(element):
    try:
        # Netconf reply returns actual return data with a tag '<data></data>'
        data = list(element.data)
        items = len(data)
        log = ""
        for idx, value in enumerate(data):
            if idx > 0 and idx < items:
                log += "\n"
            log += etree.tostring(value, pretty_print=True).decode("utf-8")
        log += "\n"
        return {
            ConnResultKey.ERROR_CODE: ConnErrorCode.SUCCESS,
            ConnResultKey.MESSAGE: log,
        }
        return log
    except Exception as e:
        logger.error(exception_message(action="XML parsing", ex=e))
        return {
            ConnResultKey.ERROR_CODE: ConnErrorCode.FAILURE,
            ConnResultKey.MESSAGE: element.data_xml,
        }


class NetconfConnection(object):
    def __init__(
        self,
        ip_address,
        user,
        password,
        port=830,
        device_name="default",
        conn_timeout=30,
    ):
        super().__init__()
        self.ip_address = ip_address
        self.user = user
        self.password = password
        self.port = port

    def connect(self):
        result = {
            ConnResultKey.ERROR_CODE: ConnErrorCode.FAILURE,
            ConnResultKey.MESSAGE: "Unknown error occured while establishing NETCONF connection",
        }
        logs = []
        try:
            logs.append(log(f"Connecting to host {self.ip_address}"))
            self.manager = manager.connect(
                host=self.ip_address,
                port=self.port,
                username=self.user,
                password=self.password,
                hostkey_verify=False,
                unknown_host_cb="allowUnknownHosts",
                device_params={"name": "default"},
                timeout=30,
            )
            if not self.manager.connected:
                msg = "Failed to connect to NETCONF server"
                result[ConnResultKey.MESSAGE] = msg
                logs.append(log(msg, LogLevel.ERROR))
                return result
            msg = f"Successfully established NETCONF connection to NETCONF server with session id: {self.manager.session_id}"
            result = {
                ConnResultKey.ERROR_CODE: ConnErrorCode.SUCCESS,
                ConnResultKey.MESSAGE: msg,
            }
            logs.append(log(msg))
        except Exception as e:
            ex_msg = exception_message(action="NETCONF connection", ex=e)
            result[ConnResultKey.MESSAGE] = ex_msg
            logs.append(log(ex_msg))
        finally:
            result[ConnResultKey.LOGS] = logs
        return result

    def get_config(self, source, filter=None):
        result = {
            ConnResultKey.ERROR_CODE: ConnErrorCode.FAILURE,
            ConnResultKey.MESSAGE: "Unknown error occured while retrieving NETCONF config",
        }
        logs = []
        try:
            logs.append(log("Requesting 'GetConfig' from host"))
            config = self.manager.get_config(source=source, filter=filter)
            logs.append(log("Received message from host. Config received:"))
            pretty_config_dict = pretty_xml_format(config)
            if pretty_config_dict[ConnResultKey.ERROR_CODE] == ConnErrorCode.FAILURE:
                logs.append(
                    log("CTF encountered error while parsing XML", LogLevel.WARN)
                )
            logs.append(pretty_config_dict[ConnResultKey.MESSAGE])
            result = {
                ConnResultKey.ERROR_CODE: ConnErrorCode.SUCCESS,
                ConnResultKey.MESSAGE: "Successfully retrieved NETCONF config",
            }
        except Exception as e:
            ex_msg = exception_message(action="get-config", ex=e)
            result[ConnResultKey.MESSAGE] = exception_message(action="get-config", ex=e)
            logs.append(log(ex_msg))
        finally:
            result[ConnResultKey.LOGS] = logs
        return result

    def edit_config(
        self,
        config,
        format="xml",
        target="candidate",
        default_operation=None,
        test_option=None,
        error_option=None,
    ):
        result = {
            ConnResultKey.ERROR_CODE: ConnErrorCode.FAILURE,
            ConnResultKey.MESSAGE: "Unknown error ocurred while editing NETCONF config",
        }
        logs = []
        try:
            logs.append(log("Sending config to host"))
            reply = self.manager.edit_config(
                target=target,
                config=config,
                test_option=test_option,
                default_operation=default_operation,
                error_option=error_option,
            )
            result[ConnResultKey.MESSAGE] = f"Edit Config Status is: {reply.ok}"
            logs.append(log(f"Host responded with OK status: {reply.ok}"))
            if reply.ok:
                logs.append(log("Requesting 'Commit' from host"))
                self.manager.commit()
                logs.append(log("Configuration has been committed successfully"))
                result = {
                    ConnResultKey.ERROR_CODE: ConnErrorCode.SUCCESS,
                    ConnResultKey.MESSAGE: "Successfully edited configuration",
                }
        except Exception as e:
            result[ConnResultKey.ERROR_CODE] = ConnErrorCode.FAILURE
            ex_msg = exception_message(action="edit-config", ex=e)
            result[ConnResultKey.MESSAGE] = ex_msg
            logs.append(log(ex_msg))
        finally:
            result[ConnResultKey.LOGS] = logs
        return result

    def delete_config(self, target):
        result = {
            ConnResultKey.ERROR_CODE: ConnErrorCode.FAILURE,
            ConnResultKey.MESSAGE: "Unknown error occured while deleting NETCONF config",
        }
        logs = []
        try:
            reply = self.manager.delete_config(target=target)
            result[ConnResultKey.MESSAGE] = f"Delete Config Status is: {reply.ok}"
            logs.append((f"Device responded with reply OK status: {reply.ok}"))
            if reply.ok:
                result[ConnResultKey.ERROR_CODE] = ConnErrorCode.SUCCESS
        except Exception as e:
            result[ConnResultKey.ERROR_CODE] = ConnErrorCode.FAILURE
            ex_msg = exception_message(action="delete-config", ex=e)
            result[ConnResultKey.MESSAGE] = ex_msg
            logs.append(log(ex_msg))
        finally:
            result[ConnResultKey.LOGS] = logs
        return result

    def reboot_machine(self):
        result = {
            ConnResultKey.ERROR_CODE: ConnErrorCode.FAILURE,
            ConnResultKey.MESSAGE: "Unknown error occured while sending NETCONF reboot",
        }
        logs = []
        try:
            reply = self.manager.reboot_machine()
            result[ConnResultKey.MESSAGE] = f"Reboot Status is: {reply.ok}"
            logs.append((f"Device responded with reply OK status: {reply.ok}"))
            if reply.ok:
                result[ConnResultKey.ERROR_CODE] = ConnErrorCode.SUCCESS
        except Exception as e:
            result[ConnResultKey.ERROR_CODE] = ConnErrorCode.FAILURE
            ex_msg = exception_message(action="reboot-machine", ex=e)
            result[ConnResultKey.MESSAGE] = ex_msg
            logs.append(log(ex_msg))
        finally:
            result[ConnResultKey.LOGS] = logs
        return result

    def disconnect(self):
        result = {
            ConnResultKey.ERROR_CODE: ConnErrorCode.SUCCESS,
            ConnResultKey.MESSAGE: "",
        }
        logs = []
        try:
            logs.append(
                log(f"Closing session {self.manager.session_id} with NETCONF server")
            )
            self.manager.close_session()
            msg = "Successfully closed NETCONF session.\n"
            logs.append(log(msg))
            result[ConnResultKey.MESSAGE] = msg
        except Exception as e:
            result[ConnResultKey.ERROR_CODE] = ConnErrorCode.FAILURE
            ex_msg = exception_message(action="close-session", ex=e)
            result[ConnResultKey.MESSAGE] = ex_msg
            logs.append(log(ex_msg))
        finally:
            result[ConnResultKey.LOGS] = logs
        return result
