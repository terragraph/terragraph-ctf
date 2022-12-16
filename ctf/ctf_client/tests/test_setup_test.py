# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import os

import pytest
from ctf.common import constants as common_constants
from ctf.ctf_client.lib.helper_functions import (
    check_if_test_setup_is_free,
    set_test_setup_and_devices_busy,
    set_test_setup_and_devices_free,
)
from ctf.ctf_client.tests.test_utils import TestUtils as Utils

logger = logging.getLogger(__name__)
CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

pytestmark = pytest.mark.skipif(
    CTF_INTERNAL is True, reason="Disabling tests as they currently hit Production."
)


@pytest.mark.usefixtures("client_api", "test_api_utils")
class TestCtfClientApiTestSetup:
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
        if check_if_test_setup_is_free(self.test_setup):
            set_test_setup_and_devices_free(self.team_id, self.test_setup)
        self.utils.after_test_run()

        if not CTF_INTERNAL:
            test_api_utils.remove_device(container, device_id)
            test_api_utils.remove_testbed(self.team_id, self.test_setup)

    def test_get_test_setup_devices_and_connections(self) -> None:
        logger.info(
            "\n------------test_get_test_setup_devices_and_connections-------------"
        )
        setup_and_connections = self.api.get_test_setup_devices_and_connections(
            self.team_id, self.test_setup
        )
        print(setup_and_connections)
        assert setup_and_connections is not None

    def test_get_test_setup_devices_and_connections_with_invalid_id(self) -> None:
        logger.info(
            "\n------------test_get_test_setup_devices_and_connections_with_invalid_id-------------"
        )
        setup_and_connections = self.api.get_test_setup_devices_and_connections(
            self.team_id, "INVALID_ID"
        )
        assert setup_and_connections is not None
        assert bool(setup_and_connections) is False

    def test_check_if_setup_is_free_with_valid_id(self) -> None:
        logger.info(
            "\n------------test_check_if_setup_is_free_with_valid_id-------------"
        )
        is_free = self.api.check_if_test_setup_is_free(self.team_id, self.test_setup)
        assert is_free is not None

    def test_check_if_setup_is_free_with_id_zero(self) -> None:
        logger.info(
            "\n------------test_check_if_setup_is_free_with_id_zero-------------"
        )
        is_free = self.api.check_if_test_setup_is_free(self.team_id, 0)
        assert is_free is not None
        assert is_free is False

    def test_check_if_setup_is_free_with_negative_id(self) -> None:
        logger.info(
            "\n------------test_check_if_setup_is_free_with_negative_id-------------"
        )
        is_free = self.api.check_if_test_setup_is_free(self.team_id, -1)
        assert is_free is not None
        assert is_free is False

    # TODO: This test needs to be fixed. If the setup is busy, it auto passes
    def test_set_test_setup_and_devices_busy(self) -> None:
        logger.info("\n------------test_set_test_setup_and_devices_busy-------------")
        is_test_free_now = self.api.check_if_test_setup_is_free(
            self.team_id, self.test_setup
        )
        if is_test_free_now:
            set_device_busy_result = self.api.set_test_setup_and_devices_busy(
                self.team_id, self.test_setup
            )
            assert set_device_busy_result is True
            test_is_free = self.api.check_if_test_setup_is_free(
                self.team_id, self.test_setup
            )
            assert test_is_free is False
            set_device_free_result = self.api.set_test_setup_and_devices_free(
                self.team_id, self.test_setup
            )
            assert set_device_free_result is True

    # TODO: Need to re-write this as well.
    def test_set_test_setup_and_devices_busy_with_worker_env(self) -> None:
        logger.info(
            "\n------------test_set_test_setup_and_devices_busy_with_worker_env-------------"
        )
        is_test_setup_free = check_if_test_setup_is_free(self.test_setup)
        assert is_test_setup_free is True
        assert set_test_setup_and_devices_busy(self.test_setup) is True
        # if this env variable is set, then the test setup reservation
        # is managed by the worker.
        os.environ[common_constants.CTF_CLIENT_TEST_SETUP_ID] = str(self.test_setup)

        assert check_if_test_setup_is_free(self.test_setup) is True
        assert set_test_setup_and_devices_free(self.test_setup) is True
        del os.environ[common_constants.CTF_CLIENT_TEST_SETUP_ID]

        assert check_if_test_setup_is_free(self.test_setup) is False
        set_test_setup_and_devices_free(self.test_setup)
        assert check_if_test_setup_is_free(self.test_setup) is True
