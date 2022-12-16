# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from enum import Enum, IntEnum, unique


CMD_END_MSG = "__CTF_COMMAND_HAS_FINISHED__"

DEFAULT_POLL_DELAY_SECONDS = 0.5
DEFAULT_READ_BYTES = 65535
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_TIMEOUT_CANCEL_SECONDS = 10.0
DEFAULT_TIMEOUT_TERMINATE_SECONDS = 10.0

LF = "\n"
RC_CANCEL = -1
RC_TIMEOUT = -2
RC_EXCEPTION = -3


@unique
class ConnectionTypeEnum(IntEnum):
    """
    Connection Type Enums since these are built-in types
    """

    SSH = 100
    TELNET = 101
    SERIAL = 102


@unique
class ShellFamilyName(str, Enum):
    BOURNE = "BOURNE"
    POWERSHELL = "POWERSHELL"


class ConnResultKey:
    ERROR_CODE = "error"
    MESSAGE = "message"
    LOGS = "logs"


@unique
class ConnErrorCode(IntEnum):
    SUCCESS = 0
    FAILURE = 1


@unique
class NetconfCommandType(str, Enum):
    GET_CONFIG = "get-config"
    EDIT_CONFIG = "edit-config"
    DELETE_CONFIG = "delete-config"
    REBOOT_MACHINE = "reboot-machine"
