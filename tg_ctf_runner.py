#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
CLI for running Terragraph CTF tests.
"""

from ctf.ctf_client.runner.ctf_runner import CtfRunner

from terragraph.ctf.tg_ctf_tests import TG_CTF_TEST_SUITES, TG_CTF_TESTS

TG_CTF_TEAM_ID = 4
ctf_runner = CtfRunner(
    team_id=TG_CTF_TEAM_ID, tests=TG_CTF_TESTS, test_suites=TG_CTF_TEST_SUITES
)
ctf_runner.run()
