# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import os

import pytest
from ctf.ctf_client.tests.test_utils import TestUtils as Utils

logger = logging.getLogger(__name__)

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

pytestmark = pytest.mark.skipif(
    CTF_INTERNAL is True, reason="Disabling tests as they currently hit Production."
)


@pytest.mark.usefixtures("client_api", "test_api_utils")
class TestCtfClientApiUserTeam:
    api = None
    test_api_utils = None
    utils = None
    team_id = None

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

        yield
        self.utils.after_test_run()

    def test_get_list_of_user_team_tests_not_none(self) -> None:
        logger.info(
            "\n------------test_get_list_of_user_team_tests_not_none-------------"
        )
        team_tests = self.api.get_list_of_user_team_tests(self.team_id)
        assert team_tests is not None

    def test_get_list_of_user_team_test_suites_not_none(self) -> None:
        logger.info(
            "\n------------test_get_list_of_user_team_test_suites_not_none-------------"
        )
        test_suites = self.api.get_list_of_user_team_test_suites(self.team_id)
        assert test_suites is not None

    def test_get_list_of_user_teams(self) -> None:
        logger.info("\n------------test_get_list_of_user_teams-------------")
        test_teams = self.api.get_list_of_user_teams()
        assert test_teams is not None
        if test_teams["data"]:
            data = test_teams["data"]
            assert len(data) > 0

    def test_get_list_of_user_team_test_setups_not_none_response(self) -> None:
        logger.info(
            "\n------------test_get_list_of_user_team_test_setups_not_none_response-------------"
        )
        tests_setup = self.api.get_list_of_user_team_test_setups(self.team_id)
        assert tests_setup is not None
        assert tests_setup["error"] == 0
        assert tests_setup["data"] is not None
        setup_data = tests_setup["data"]
        assert len(setup_data) >= 0
