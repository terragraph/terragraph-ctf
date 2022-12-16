#!/usr/bin/env fbpython

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from ctf.ctf_client.serverless_lib.serverless_api import ServerlessApi

TEAM_ID = "1"
TEST_EXEC_ID = "test_name_1"
TEST_ACTION_RESULT_ID = "action_name_1"
KEY = "unique_key"
JSON_OBJECT = {"key": {"nested_1_key": {" nested_2_key": "value_2"}}, "key_2": "hey"}
JSON_OBJECT_2 = {"key": "value"}


class TestTestActionResultKeyedJsonObjects:
    def test_save_test_action_result_keyed_json_object_lifecycle(self) -> None:
        # Create
        serverless_api = ServerlessApi()
        serverless_api.override_serverless_config(
            "./",
            "./",
        )
        saved_keyed_json_object = (
            serverless_api.save_test_action_result_keyed_json_object(
                TEST_EXEC_ID, TEST_ACTION_RESULT_ID, KEY, JSON_OBJECT, team_id=TEAM_ID
            )
        )

        # Get
        json_object = serverless_api.get_test_action_result_keyed_json_object(
            KEY, TEAM_ID
        )

        assert json_object == saved_keyed_json_object

        # Save duplicated, replaces
        serverless_api.save_test_action_result_keyed_json_object(
            TEST_EXEC_ID, TEST_ACTION_RESULT_ID, KEY, JSON_OBJECT_2, team_id=TEAM_ID
        )

        # Delete
        test_action_result_keyed_json_object = (
            serverless_api.delete_test_action_result_keyed_json_object(KEY, TEAM_ID)
        )

        # Get deleted not found
        test_action_result_keyed_json_object = (
            serverless_api.get_test_action_result_keyed_json_object(KEY, TEAM_ID)
        )
        assert test_action_result_keyed_json_object is None

        # Delete not found
        test_action_result_keyed_json_object = (
            serverless_api.delete_test_action_result_keyed_json_object(KEY, TEAM_ID)
        )
        assert test_action_result_keyed_json_object is None
