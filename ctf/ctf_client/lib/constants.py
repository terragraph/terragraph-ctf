# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from enum import IntEnum, unique


@unique
class TestActionStatusEnum(IntEnum):
    SUCCESS = 0
    FAILURE = 1
    WARNING = 16  # for "never_fail" steps (ex. log collection)
