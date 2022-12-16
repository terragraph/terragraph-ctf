# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from enum import Enum, EnumMeta, IntEnum, unique


class GenericEnumMeta(EnumMeta):
    def choices(self):
        return tuple((i.value, i.name) for i in self)

    def __contains__(self, item):
        try:
            self(item)
        except ValueError:
            return False
        else:
            return True


@unique
class DeviceTypeEnum(IntEnum):
    """
    Device Type Enums since these are built-in types
    """

    GENERIC = 99
    ATTENUATOR = 100
    POWER_METER = 101
    POWER_SUPPLY = 102
    SIGNAL_GENERATOR = 103
    SPECTRUM_ANALYZER = 104
    RAN = 105
    SWITCH = 106
    TERRAGRAPH = 107
    UE_EMULATOR = 108
    TERRAGRAPH_CONTROLLER = 109
    TERRAGRAPH_TRAFFIC_GEN = 110


@unique
class DeploymentEnvironment(IntEnum):
    """
    File Server deployment
    """

    # FB Infra prod environment (Tupperware) or devserver
    INTERNAL = 0
    # AWS or Single host deployement or docker dev environment
    EXTERNAL = 1


# TODO: Change all references to use this ResponseCode enum and
# delete the one in api_server/core/helpers/constants.py (T89885099)
@unique
class ResponseCode(IntEnum):
    """
    Http Response Code List
    """

    SUCCESS = 0
    VALIDATION_ERROR = 1
    EXCEPTION = 2
    UNAUTHORIZED = 3
    INCORRECT_REQUEST_DATA = 4
    DATA_ERROR = 5
    USER_NOT_MEMBER_OF_TEAM = 6
    USER_CAN_NOT_BE_DEACTIVATED = 7
    USER_CREDENTIALS_DEACTIVATED = 8
    INCORRECT_USER_CREDENTIALS = 9
    TEAM_NAME_ALREADY_EXIST = 10
    FAILED_TO_CONNECT_TO_DEVICE = 11
    NO_CONNECTION_SPECIFIED = 12
    TEST_SETUP_NAME_ALREADY_EXIST = 13
    TEST_SETUP_BUSY = 14
    USER_CAN_NOT_BE_REMOVED = 15
    TEST_SETUP_RESERVED = 16
    TEST_SETUP_GROUP_NAME_ALREADY_EXIST = 17
    TEST_SETUP_METADATA_EXCEED_TEXT_LIMIT = 18
    TEST_SETUP_UNAVAILABLE = 19


# TODO: Change all references to use this TestSetupStatusEnum enum and
# delete the one in api_server/core/helpers/constants.py (T89885099)
@unique
class TestSetupStatusEnum(IntEnum):
    """
    Test setup status enums code list
    """

    IDLE = 0
    DIRTY = 1
    BUSY = 2
    INSTA_STOP = 3


@unique
class TagLevel(Enum, metaclass=GenericEnumMeta):
    """
    Priority levels for tags
    """

    # Referenced by web-ui/src/app/shared/test-constants.ts
    CRITICAL = 10
    HIGH = 20
    MEDIUM = 30
    LOW = 40
    INFO = 50

    # lower number = higher priority
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
