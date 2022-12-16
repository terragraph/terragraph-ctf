#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from terragraph.ctf.tests.tg_minion_linkup import TestTgMinionLinkUp


class TestTgLLS(TestTgMinionLinkUp):
    TEST_NAME = "PUMA: LLS Test Case"
    DESCRIPTION = "Link Level Scheduler test"
