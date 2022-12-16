#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from ctf.ctf_client.runner.ctf_runner import CtfRunner
from ctf.ctf_client.samples.test_hello import TestHello

TESTS = {TestHello.__name__: TestHello}
TEST_SUITES = {
    "CTFTestSuite": [
        TestHello,
        TestHello,
        TestHello,
    ]
}


ctf_runner = CtfRunner(team_id=1, tests=TESTS, test_suites=TEST_SUITES)
ctf_runner.run()
