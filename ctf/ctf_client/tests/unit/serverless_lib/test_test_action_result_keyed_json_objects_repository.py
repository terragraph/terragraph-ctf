#!/usr/bin/env fbpython

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from unittest.mock import call, mock

import pytest
from ctf.ctf_client.serverless_lib.exceptions import (
    DuplicateResourceException,
    ResourceNotFoundException,
)
from ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository import (
    ACTION_LOGS_DIRNAME,
    ACTION_LOGS_KEYED_JSON_OBJECTS_DIRNAME,
    KEYED_JSON_OBJECTS_INDEX_PATH,
    TestActionResultKeyedJsonObjectsRepository,
)

TestActionResultKeyedJsonObjectsRepository.__test__ = False

TEAM_ID = 1
TEST_EXEC_ID = "test_name_1"
TEST_ACTION_RESULT_ID = "action_name_1"
KEY = "unique_key"
JSON_OBJECT = {"key": {"nested_1_key": {" nested_2_key": "value_2"}}, "key_2": "hey"}
DEFAULT_TEST_RESULTS_LOGS_DIRECTORY = "user_defined_index_dirname"

TEST_ACTION_RESULT_KEYED_JSON_OBJECTS_DIRNAME = (
    f"{DEFAULT_TEST_RESULTS_LOGS_DIRECTORY}/"
    f"{TEST_EXEC_ID}/"
    f"{ACTION_LOGS_DIRNAME}/"
    f"{TEST_ACTION_RESULT_ID}/"
    f"{ACTION_LOGS_KEYED_JSON_OBJECTS_DIRNAME}"
)
KEYED_JSON_OBJECTS_INDEX_DIRNAME = (
    f"{DEFAULT_TEST_RESULTS_LOGS_DIRECTORY}/{KEYED_JSON_OBJECTS_INDEX_PATH}"
)
TEST_ACTION_RESULT_KEYED_JSON_OBJECT_PATH = (
    f"{TEST_ACTION_RESULT_KEYED_JSON_OBJECTS_DIRNAME}/{KEY}.json"
)
TEAM_INDEX_DIRNAME = f"{KEYED_JSON_OBJECTS_INDEX_DIRNAME}/{TEAM_ID}"
INDEXED_FILE_PATH = f"{KEYED_JSON_OBJECTS_INDEX_DIRNAME}/{TEAM_ID}/{KEY}"
STORED_JSON_OBJECT = {
    "json_object": JSON_OBJECT,
    "key": KEY,
}

INDEX_STORED_JSON_OBJECT_WITH_VERSION = {
    **STORED_JSON_OBJECT,
    "test_run_execution_id": TEST_EXEC_ID,
    "test_action_result_id": TEST_ACTION_RESULT_ID,
    "version": 1,
}


class TestTestActionResultKeyedJsonObjectsRepository:
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.mkdir"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.join"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.put_json_object"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.exists"
    )
    def test_save_success(
        self, mocked_exists, mocked_put_json_object, mocked_join, mocked_mkdir
    ) -> None:
        # Arrange
        keyed_json_objects_repo = TestActionResultKeyedJsonObjectsRepository(
            DEFAULT_TEST_RESULTS_LOGS_DIRECTORY, KEYED_JSON_OBJECTS_INDEX_PATH
        )
        mocked_exists.return_value = False
        mocked_join.side_effect = [
            TEST_ACTION_RESULT_KEYED_JSON_OBJECTS_DIRNAME,
            TEST_ACTION_RESULT_KEYED_JSON_OBJECT_PATH,
            KEYED_JSON_OBJECTS_INDEX_DIRNAME,
            TEAM_INDEX_DIRNAME,
            KEYED_JSON_OBJECTS_INDEX_DIRNAME,
            INDEXED_FILE_PATH,
            KEYED_JSON_OBJECTS_INDEX_DIRNAME,
            INDEXED_FILE_PATH,
        ]

        # Act
        actual_keyed_json_object = (
            keyed_json_objects_repo.save_test_action_result_keyed_json_object(
                TEAM_ID, TEST_EXEC_ID, TEST_ACTION_RESULT_ID, KEY, JSON_OBJECT
            )
        )

        # Assert
        assert actual_keyed_json_object == INDEX_STORED_JSON_OBJECT_WITH_VERSION
        assert mocked_put_json_object.call_count == 2
        mocked_put_json_object.assert_has_calls(
            [
                call(TEST_ACTION_RESULT_KEYED_JSON_OBJECT_PATH, STORED_JSON_OBJECT),
                call(INDEXED_FILE_PATH, INDEX_STORED_JSON_OBJECT_WITH_VERSION),
            ]
        )
        mocked_mkdir.assert_has_calls(
            [
                call(TEST_ACTION_RESULT_KEYED_JSON_OBJECTS_DIRNAME),
                call(TEAM_INDEX_DIRNAME),
            ]
        )

    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.get_json_object"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.join"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.exists"
    )
    def test_get_success(
        self, mocked_exists, mocked_join, mocked_get_json_object
    ) -> None:
        # Arrange
        keyed_json_objects_repo = TestActionResultKeyedJsonObjectsRepository(
            DEFAULT_TEST_RESULTS_LOGS_DIRECTORY, KEYED_JSON_OBJECTS_INDEX_PATH
        )
        mocked_exists.return_value = True
        mocked_get_json_object.return_value = STORED_JSON_OBJECT
        mocked_join.side_effect = [INDEXED_FILE_PATH, INDEXED_FILE_PATH]

        # Act
        actual_keyed_json_object = (
            keyed_json_objects_repo.get_test_action_result_keyed_json_object(
                KEY, TEAM_ID
            )
        )

        # Assert
        assert actual_keyed_json_object == STORED_JSON_OBJECT
        mocked_get_json_object.assert_called_with(INDEXED_FILE_PATH)

    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.get_json_object"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.join"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.exists"
    )
    def test_get_not_exists(
        self, mocked_exists, mocked_join, mocked_get_json_object
    ) -> None:
        # Arrange
        keyed_json_objects_repo = TestActionResultKeyedJsonObjectsRepository(
            DEFAULT_TEST_RESULTS_LOGS_DIRECTORY, KEYED_JSON_OBJECTS_INDEX_PATH
        )
        mocked_exists.return_value = False
        mocked_join.side_effect = [INDEXED_FILE_PATH, INDEXED_FILE_PATH]

        # Act
        with pytest.raises(ResourceNotFoundException) as rnf:
            keyed_json_objects_repo.get_test_action_result_keyed_json_object(
                KEY, TEAM_ID
            )

        # Assert
        assert f"{KEY} not found" in str(rnf)
        assert not mocked_get_json_object.called

    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.rm"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.get_json_object"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.join"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.exists"
    )
    def test_delete_success(
        self, mocked_exists, mocked_join, mocked_get_json_object, mocked_rm
    ) -> None:
        # Arrange
        keyed_json_objects_repo = TestActionResultKeyedJsonObjectsRepository(
            DEFAULT_TEST_RESULTS_LOGS_DIRECTORY, KEYED_JSON_OBJECTS_INDEX_PATH
        )
        mocked_exists.return_value = True
        mocked_get_json_object.return_value = STORED_JSON_OBJECT
        mocked_join.side_effect = [INDEXED_FILE_PATH, INDEXED_FILE_PATH]

        # Act
        keyed_json_objects_repo.delete_test_action_result_keyed_json_object(
            KEY, TEAM_ID
        )

        # Assert
        mocked_rm.assert_has_calls([call(INDEXED_FILE_PATH)])

    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.get_json_object"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.join"
    )
    @mock.patch(
        "ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository.exists"
    )
    def test_delete_not_exists(
        self, mocked_exists, mocked_join, mocked_get_json_object
    ) -> None:
        # Arrange
        keyed_json_objects_repo = TestActionResultKeyedJsonObjectsRepository(
            DEFAULT_TEST_RESULTS_LOGS_DIRECTORY, KEYED_JSON_OBJECTS_INDEX_PATH
        )
        mocked_exists.return_value = False
        mocked_join.side_effect = [INDEXED_FILE_PATH, INDEXED_FILE_PATH]

        # Act
        with pytest.raises(ResourceNotFoundException) as rnf:
            keyed_json_objects_repo.delete_test_action_result_keyed_json_object(
                KEY, TEAM_ID
            )

        # Assert
        assert f"{KEY} not found" in str(rnf)
