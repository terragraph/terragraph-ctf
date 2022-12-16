# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import logging
import os

import pytest
from ctf.ctf_client.tests.test_utils import TestUtils as Utils

TEST_DEF_FILE = "test_definitions/hello.json"

logger = logging.getLogger(__name__)

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"


pytestmark = pytest.mark.skipif(
    CTF_INTERNAL is True, reason="Disabling tests as they currently hit Production."
)


@pytest.mark.usefixtures("client_api", "test_api_utils")
class TestCtfClientApiTestSchedule:
    api = None
    utils = None
    team_id = None
    test_id = None

    @pytest.fixture(autouse=True)
    def test_fixture(self, client_api, test_api_utils):
        self.api = client_api
        self.test_api_utils = test_api_utils
        self.utils = Utils(test_api_utils.apiserver, test_api_utils.fileserver)
        self.utils.before_test_run()

        self.team_id = (
            self.utils.get_test_param("INTERNAL_TEST_TEAM_ID")
            if CTF_INTERNAL
            else test_api_utils.get_team_id()
        )
        container = None
        device_id = None

        if CTF_INTERNAL:
            self.test_id = self.utils.get_test_param("INTERNAL_TEST_ID")
        else:
            container, device_id = test_api_utils.create_device(
                self.team_id, "test_device"
            )
            self.test_setup = test_api_utils.create_testbed(
                "test_bed", self.team_id, [device_id]
            )
            self.test_id = test_api_utils.create_test(
                self.team_id, self.test_setup, TEST_DEF_FILE
            )
        yield
        if not CTF_INTERNAL:
            test_api_utils.remove_device(container, device_id)
            test_api_utils.remove_testbed(self.team_id, self.test_setup)
            # Removing testbed and devices automatically deletes the test,
            # not sure if this is desired.
            # test_api_utils.remove_test(self.team_id, self.test_id)
        self.utils.after_test_run()

    def test_valid_schedule_test(self):
        logger.info("\n------------test_valid_schedule_test-------------")
        result = self.api.schedule_test(self.test_id, datetime.datetime.now(), 0)
        assert result["error"] == 0
        assert "Test Scheduled successfully" in result["message"]

    def test_schedule_test_with_bad_date(self) -> None:
        logger.info("\n------------test_schedule_test_with_bad_date-------------")
        result = self.api.schedule_test(self.test_id, datetime.datetime, -3)
        assert result["error"] == 1
        assert "Datetime has wrong format" in result["message"]

    def test_schedule_test_with_invalid_id(self) -> None:
        logger.info("\n------------test_schedule_test_with_invalid_id-------------")
        schedule_result = self.api.schedule_test(0, datetime.datetime, 0)
        error_msg = "Test with id 0 not found."
        assert schedule_result["error"] == 1
        assert error_msg in schedule_result["message"]
        assert schedule_result is not None

    # This test requires an implementation change in order schedule a test suite
    # using a valid suite id.
    # Even if the test suite with the ID specified at `self.test_suite_id` exists,
    # it results in fail.
    # This test must be changed when the fix is in place.
    @pytest.mark.skip(reason="no way of currently testing this")
    def test_schedule_test_suite(self) -> None:
        test_suite_id = self.utils.get_test_param("INTERNAL_TEST_SUITE_ID")
        logger.info("\n------------test_schedule_test_suite-------------")
        result = self.api.schedule_test_suite(
            test_suite_id, datetime.datetime.now(), -3
        )
        assert f"Test suite with id {test_suite_id} not found" in result["message"]
        assert result["error"] == 1
