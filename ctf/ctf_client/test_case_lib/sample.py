# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import sys

sys.path.append("../../../")

import ctf.ctf_client.test_case_lib.config as cfg
from ctf.ctf_client.lib.constants import TestActionStatusEnum
from ctf_test_case import CtfTestCase, TestActionResult


def send_ls(device):
    output = device.action_custom_command(cmd="ls", timeout=600)
    outcome = (
        TestActionStatusEnum.SUCCESS
        if output["error"] == 0
        else TestActionStatusEnum.FAILURE
    )
    return TestActionResult(outcome=outcome, log=str(output["message"]))


sample_test = CtfTestCase(
    name="Test connectivity to rasp pi.",
    description="Sample test for CTF Client.",
    team_id=cfg.CTF_TEAM_ID,
    test_setup_id=cfg.CTF_TEST_SETUP_ID,
)

devices = sample_test.get_devices_in_test_setup()

sample_test.add_action(
    func=lambda: send_ls(devices[1]), description="Send ls to docker device."
)
