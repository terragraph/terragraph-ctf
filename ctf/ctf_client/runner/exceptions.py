#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Test exceptions.
"""


class DeviceError(Exception):
    pass


class DeviceCmdError(DeviceError):
    """Running a command has failed."""

    pass


class DeviceConfigError(DeviceError):
    """Loading or manipulating a node config failed."""

    pass


class TestFailed(Exception):
    """A test produced an incorrect result."""

    pass


class TestUsageError(Exception):
    """Test usage is incorrect."""

    pass
