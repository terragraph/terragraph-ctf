# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import json
import logging
import os
import sys
import uuid
from operator import itemgetter

import pytest


sys.path.append("../../../")

from ctf.ctf_client.tests.test_utils import TestUtils as Utils

logger = logging.getLogger(__name__)

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

pytestmark = pytest.mark.skipif(
    CTF_INTERNAL is True, reason="Disabling tests as they currently hit Production."
)

KEY = "UNIQUE_KEY"
NUMBER_OF_JSON_OBJECTS = 3


@pytest.mark.usefixtures("client_api", "test_api_utils")
class TestCtfClientApiTestTestActionResultKeyedJsonObject:
    api = None
    utils = None
    test_api_utils = None
    team_id = None
    test_setup = None
    test_action_result_id = None

    @pytest.fixture(autouse=True)
    def test_fixture(self, client_api, test_api_utils):
        self.api = client_api
        self.test_api_utils = test_api_utils
        self.utils = Utils(test_api_utils.apiserver, test_api_utils.fileserver)
        self.team_id = (
            self.utils.get_test_param("INTERNAL_TEST_TEAM_ID")
            if CTF_INTERNAL
            else test_api_utils.get_team_id()
        )

        test_run_result = self.api.create_test_result(
            name="Test Save Action Result Keyed JSON Object",
            identifier=str(uuid.uuid4),
            description="Save Json with key",
            team_id=self.team_id,
        )
        self.test_exec_id = test_run_result["data"]["id"]

        test_action_result = self.api.save_action_result(
            test_run_id=self.test_exec_id,
            description="Test Save Action Result Keyed JSON Object",
            outcome=1,
            logs="Logs",
            start_time=datetime.datetime.now(),
            end_time=datetime.datetime.now(),
            parent_action_id=None,
            tags=json.dumps([{"description": "HighWarning", "level": 20}]),
        )
        self.test_action_result_id = test_action_result["data"]["test_action_result_id"]

        self.utils.before_test_run()
        yield
        self.utils.after_test_run()

    def test_save_test_action_result_keyed_json_object_success(self):
        logger.info(
            "\n------------test_save_test_action_result_keyed_json_object_success-------------"
        )
        # Arrange
        expected_key = KEY
        expected_json_object = {"key": "value"}

        # Act
        saved_test_action_result_keyed_object = (
            self.api.save_test_action_result_keyed_json_object(
                self.test_exec_id,
                self.test_action_result_id,
                expected_key,
                expected_json_object,
            )
        )

        # Assert
        assert saved_test_action_result_keyed_object["team_id"] == self.team_id
        assert (
            saved_test_action_result_keyed_object["test_run_execution_id"]
            == self.test_exec_id
        )
        assert (
            saved_test_action_result_keyed_object["test_action_result_id"]
            == self.test_action_result_id
        )
        assert saved_test_action_result_keyed_object["key"] == expected_key
        assert (
            saved_test_action_result_keyed_object["json_object"] == expected_json_object
        )

        # Cleanup
        self.api.delete_test_action_result_keyed_json_object(expected_key, self.team_id)

    def test_save_test_action_result_keyed_json_replace_value(self):
        logger.info(
            "\n------------test_save_test_action_result_keyed_json_object_duplicated_key-------------"
        )
        # Arrange
        expected_key = KEY
        expected_json_object = {"key_2": "value_2"}
        self.api.save_test_action_result_keyed_json_object(
            self.test_exec_id,
            self.test_action_result_id,
            expected_key,
            {"key": "value"},
        )

        # Act
        actual_response = self.api.save_test_action_result_keyed_json_object(
            self.test_exec_id,
            self.test_action_result_id,
            expected_key,
            expected_json_object,
        )

        # Assert
        assert actual_response["json_object"] == expected_json_object

        # Cleanup
        self.api.delete_test_action_result_keyed_json_object(expected_key, self.team_id)

    def test_get_test_action_result_keyed_json_object_success(self):
        logger.info(
            "\n------------test_get_test_action_result_keyed_json_object_success-------------"
        )
        self.api.save_test_action_result_keyed_json_object(
            self.test_exec_id,
            self.test_action_result_id,
            KEY,
            {"key": "value"},
        )

        # Act
        actual_test_action_result_keyed_object = (
            self.api.get_test_action_result_keyed_json_object(KEY, self.team_id)
        )

        # Assert
        assert actual_test_action_result_keyed_object["key"] == KEY

    def test_get_test_action_result_keyed_json_object_not_found(self):
        logger.info(
            "\n------------test_save_test_action_result_keyed_json_object_not_found-------------"
        )
        # Act
        with pytest.raises(Exception) as e:
            self.api.get_test_action_result_keyed_json_object(
                "not_existent_key", self.team_id
            )

        # Assert
        assert "404" in str(e)

    def test_list_keyed_json_objects_for_test_action_result(self):
        logger.info(
            "\n------------test_list_keyed_json_objects_for_test_action_result-------------"
        )
        # Arrange
        self._create_test_action_result_keyed_json_objects_list()

        # Act
        actual_keyed_json_objects_for_test_action_result = (
            self.api.list_keyed_json_object_for_test_action_result(
                self.test_exec_id, self.test_action_result_id
            )
        )

        # Assert
        assert (
            self.keyed_json_objects
            == actual_keyed_json_objects_for_test_action_result["json_objects"]
        )

        # Cleanup
        self._delete_test_action_result_keyed_json_objects_list()

    def test_list_keyed_json_objects_for_test_action_result_page(self):
        logger.info(
            "\n------------test_list_keyed_json_objects_for_test_action_result_page-------------"
        )
        # Arrange
        self._create_test_action_result_keyed_json_objects_list()

        sorted_by_key = sorted(self.keyed_json_objects, key=itemgetter("key"))

        # Act
        for page, offset in [[1, 1], [2, 1], [3, 1], [1, 2], [2, 2]]:
            start_index = (page - 1) * offset
            end_index = start_index + offset
            expected_keyed_json_objects = sorted_by_key[start_index:end_index]
            actual_keyed_json_objects_for_test_action_result = (
                self.api.list_keyed_json_object_for_test_action_result(
                    self.test_exec_id, self.test_action_result_id, page, offset
                )
            )

            # Assert
            assert (
                actual_keyed_json_objects_for_test_action_result["json_objects"]
                == expected_keyed_json_objects
            )

        # Cleanup
        self._delete_test_action_result_keyed_json_objects_list()

    def test_list_keyed_json_objects_for_test_run_execution(self):
        logger.info(
            "\n------------test_list_keyed_json_objects_for_test_action_result-------------"
        )
        # Arrange
        self._create_test_action_result_keyed_json_objects_list()

        # Act
        actual_keyed_json_objects_for_test_run_execution_result = (
            self.api.list_keyed_json_object_for_test_run_execution(self.test_exec_id)
        )

        # Assert
        assert (
            self.keyed_json_objects
            == actual_keyed_json_objects_for_test_run_execution_result["json_objects"]
        )

        # Cleanup
        self._delete_test_action_result_keyed_json_objects_list()

    def _create_test_action_result_keyed_json_objects_list(self):
        self.keyed_json_objects = []
        start = 3
        for i in range(start, start + NUMBER_OF_JSON_OBJECTS):
            keyed_json_object = self.api.save_test_action_result_keyed_json_object(
                self.test_exec_id,
                self.test_action_result_id,
                f"key_{i}",
                {f"json_key_{i}": f"json_value_{i}"},
            )
            self.keyed_json_objects.append(keyed_json_object)

    def _delete_test_action_result_keyed_json_objects_list(self):
        for keyed_json_object in self.keyed_json_objects:
            self.api.delete_test_action_result_keyed_json_object(
                keyed_json_object["key"], self.team_id
            )
        self.keyed_json_objects = []
