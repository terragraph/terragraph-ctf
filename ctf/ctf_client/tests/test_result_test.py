# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
    isort:skip_file
"""
import logging
import os
import sys
import uuid

import pytest


sys.path.append("../../../")

from ctf.common import constants as common_constants
from ctf.ctf_client.lib.api_helper import LoginException
from ctf.ctf_client.lib.helper_functions import create_test_run_result
from ctf.ctf_client.tests.test_utils import TestUtils as Utils

logger = logging.getLogger(__name__)

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

pytestmark = pytest.mark.skipif(
    CTF_INTERNAL is True, reason="Disabling tests as they currently hit Production."
)


@pytest.mark.usefixtures("client_api", "test_api_utils")
class TestCtfClientApiTestResult:
    api = None
    utils = None
    test_api_utils = None
    team_id = None
    test_setup = None

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
            self.test_setup = self.utils.get_test_param("INTERNAL_TEST_SETUP_ID")
        else:
            container, device_id = test_api_utils.create_device(
                self.team_id, "test_device"
            )
            self.test_setup = test_api_utils.create_testbed(
                "test_bed", self.team_id, [device_id]
            )

        yield
        self.utils.after_test_run()
        if not CTF_INTERNAL:
            self.test_api_utils.remove_device(container, device_id)
            self.test_api_utils.remove_testbed(self.team_id, self.test_setup)

    def test_create_test_result(self) -> None:
        logger.info("\n------------test_create_test_result-------------")
        result = self.api.create_test_result(
            name="Create Test Result Test",
            identifier=str(uuid.uuid4),
            description="Check to make sure all basic APIs are working",
            team_id=self.team_id,
            test_setup=self.test_setup,
        )
        assert result is not None
        assert result["error"] == 0
        assert result["data"] is not None
        data = result["data"]
        result = self.api.save_test_result_outcome(data["id"])
        assert result is not None
        assert result["error"] == 0
        assert result["data"] is not None

    def test_create_test_result_without_test_setup(self) -> None:
        logger.info(
            "\n------------test_create_test_result_without_test_setup-------------"
        )
        result = self.api.create_test_result(
            name="Create Test Result Without Test Setup",
            identifier=str(uuid.uuid4),
            description="Check to make sure all basic APIs are working",
            team_id=self.team_id,
        )
        assert result["data"] is not None
        data = result["data"]
        result = self.api.save_test_result_outcome(data["id"])
        assert result is not None
        assert result["error"] == 0

    ## This scenario is expected to fail.
    # The test will fail if doesn't raises exception
    def test_create_test_result_without_team_id(self) -> None:
        logger.info(
            "\n------------test_create_test_result_without_team_id-------------"
        )
        with pytest.raises(Exception):
            result = self.api.create_test_result(
                name="Create Test Result Without Test Setup",
                identifier=str(uuid.uuid4),
                description="Check to make sure all basic APIs are working",
                test_setup=self.test_setup,
            )
            logging.info(f"This will never log {result}")

    def test_create_test_result_with_bad_login(self) -> None:
        logger.info("\n------------test_create_test_result_with_bad_login-------------")
        user = self.utils.get_param("CTF_BUCK_USER")
        api_server_url = self.utils.get_param("CTF_API_SERVER_URL")
        file_server_url = self.utils.get_param("CTF_FILE_SERVER_URL")
        os.environ["CTF_USER"] = user
        os.environ["CTF_PASSWORD"] = "WRONG_PASSWD"
        os.environ["CTF_API_SERVER_URL"] = api_server_url
        os.environ["CTF_FILE_SERVER_URL"] = file_server_url

        # delete auth token to make sure login is attempted
        self.api.token = None
        with pytest.raises(LoginException):
            self.api.create_test_result(
                name="Create Test Bad Login Run Test Result",
                identifier=str(uuid.uuid4),
                description="Check to make sure all basic APIs are working",
                team_id=self.team_id,
                test_setup=self.test_setup,
            )

    def test_create_test_result_with_worker_env(self) -> None:
        logger.info(
            "\n------------test_create_test_result_with_worker_env-------------"
        )
        os.environ[common_constants.CTF_CLIENT_TEST_EXE_ID] = self.utils.get_test_param(
            "TEST_EXE_ID"
        )
        result = create_test_run_result(
            name="Create Test Result Test",
            identifier=str(uuid.uuid4),
            description="Check to make sure all basic APIs are working",
            team_id=self.team_id,
            test_setup=self.test_setup,
        )
        assert result["data"] is not None
        assert result["data"]["id"] == self.utils.get_test_param("TEST_EXE_ID")
        del os.environ[common_constants.CTF_CLIENT_TEST_EXE_ID]

    def test_save_test_result_with_dashboard_details(self) -> None:
        logger.info(
            "\n------------test_save_test_result_with_dashboard_details-------------"
        )
        result = self.api.create_test_result(
            name="Save Test Result with dashboard details",
            identifier=str(uuid.uuid4),
            description="Check to make sure all basic APIs are working",
            team_id=self.team_id,
            test_setup=self.test_setup,
        )
        assert result["data"] is not None
        data = result["data"]
        dashboard_details = [
            {"label": "Valid data", "link": "https://grafana.com/grafana/dashboards"},
            {"label": "Dashboard", "link": "https://grafana.com/grafana/dashboards"},
        ]
        result = self.api.save_test_result_outcome(
            data["id"], dashboard_details=dashboard_details
        )
        assert result is not None
        assert result["error"] == 0

    ## This scenario is expected to fail.
    # The test will fail if doesn't raises exception
    def test_save_test_result_with_invalid_dashboard_details(self) -> None:
        logger.info(
            "\n------------test_save_test_result_with_invalid_dashboard_details-------------"
        )
        with pytest.raises(Exception):
            result = self.api.create_test_result(
                name="Save Test Result with invalid dashboard details",
                identifier=str(uuid.uuid4),
                description="Check to make sure all basic APIs are working",
                team_id=self.team_id,
                test_setup=self.test_setup,
            )
            assert result["data"] is not None
            data = result["data"]
            dashboard_details = [
                {"label": "Invalid key url expected link", "url": "http://somelink/"},
                {
                    "label": "Valid data",
                    "link": "https://grafana.com/grafana/dashboards",
                },
            ]
            result = self.api.save_test_result_outcome(
                data["id"], dashboard_details=dashboard_details
            )

    def test_save_test_result_with_test_result_summary(self) -> None:
        logger.info(
            "\n------------test_save_test_result_with_test_result_summary-------------"
        )
        result = self.api.create_test_result(
            name="Save Test Result with test_result_summary json",
            identifier=str(uuid.uuid4),
            description="Check to make sure all basic APIs are working",
            team_id=self.team_id,
            test_setup=self.test_setup,
        )
        assert result["data"] is not None
        data = result["data"]
        test_result_summary = [
            {
                "label": "Error",
                "message": "This is error message",
                "is_link": False,
                "level": "error",
            },
            {
                "label": "Warning",
                "message": "This is warning message",
                "is_link": False,
                "level": "warning",
            },
            {
                "label": "Link",
                "message": "fb.com",
                "is_link": True,
            },
        ]
        result = self.api.save_test_result_outcome(
            data["id"], test_result_summary=test_result_summary
        )
        assert result is not None
        assert result["error"] == 0

    # ## This scenario is expected to fail.
    # The test will fail if doesn't raises exception
    def test_save_test_result_with_invalid_test_result_summary(self) -> None:
        logger.info(
            "\n------------test_save_test_result_with_invalid_test_result_summary-------------"
        )
        with pytest.raises(Exception):
            result = self.api.create_test_result(
                name="Save Test Result with invalid test_result_summary json fields",
                identifier=str(uuid.uuid4),
                description="Check to make sure all basic APIs are working",
                team_id=self.team_id,
                test_setup=self.test_setup,
            )
            assert result["data"] is not None
            data = result["data"]
            test_result_summary = [
                {
                    "label": "Error",
                    "message": "This is error message",
                    "is_link": False,
                    "level": "emergency",
                    "test_detail": "Invalid severity level 'emergency'",
                },
                {
                    "label": "Warning",
                    "is_link": False,
                    "level": "warning",
                    "test_detail": "Missing 'message' field",
                },
            ]
            result = self.api.save_test_result_outcome(
                data["id"], test_result_summary=test_result_summary
            )
