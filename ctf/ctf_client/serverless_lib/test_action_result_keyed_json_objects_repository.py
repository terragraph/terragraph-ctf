#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Any, Dict, Optional, Union

from ctf.ctf_client.serverless_lib.ctf_file_system import (
    exists,
    get_json_object,
    join,
    mkdir,
    put_json_object,
    rm,
)

from ctf.ctf_client.serverless_lib.exceptions import ResourceNotFoundException

DEFAULT_INDEX_DIRECTORY = "/tmp/ctf"
ACTION_LOGS_DIRNAME = "step_logs"
ACTION_LOGS_KEYED_JSON_OBJECTS_DIRNAME = "test_action_result_keyed_json_objects"
KEYED_JSON_OBJECTS_INDEX_PATH = "ctf_keyed_json_objects_index"

logger = logging.getLogger(__name__)


class TestActionResultKeyedJsonObjectsRepository:
    test_results_base_path: str
    keyed_json_objects_index_dirname = None

    def __init__(
        self,
        test_results_base_path: str,
        test_action_results_keys_index: str,
    ) -> None:
        self.test_results_base_path = test_results_base_path
        if not test_action_results_keys_index:
            self.keyed_json_objects_index_dirname = DEFAULT_INDEX_DIRECTORY
        else:
            self.keyed_json_objects_index_dirname = test_action_results_keys_index

    def save_test_action_result_keyed_json_object(
        self,
        team_id: str,
        test_exe_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
    ):
        if not self._isascii(key):
            raise ValueError(f"Key {key} should be ascii string.")

        test_action_result_keyed_json_objects_dirname = (
            self._build_test_action_result_keyed_json_objects_dirname(
                test_exe_id, test_action_result_id
            )
        )

        self._save_to_test_action_result_dir(
            test_exe_id,
            test_action_result_id,
            key,
            json_object,
            test_action_result_keyed_json_objects_dirname,
        )

        saved_object = self._save_to_index_dir(
            team_id, test_exe_id, test_action_result_id, key, json_object
        )

        return saved_object

    def get_test_action_result_keyed_json_object(self, key: str, team_id: int):
        team_id = str(team_id)
        keyed_json_object_path = join(
            self._get_keyed_json_objects_index_dirname(), team_id, key
        )
        if not exists(keyed_json_object_path):
            raise ResourceNotFoundException(f"Json Object with key {key} not found.")

        return get_json_object(keyed_json_object_path)

    def delete_test_action_result_keyed_json_object(self, key: str, team_id: int):
        keyed_json_object_path = join(
            self._get_keyed_json_objects_index_dirname(), str(team_id), key
        )
        if not exists(keyed_json_object_path):
            raise ResourceNotFoundException(f"Json Object with key {key} not found.")

        rm(keyed_json_object_path)

    def _save_to_test_action_result_dir(
        self,
        test_exe_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
        test_action_result_keyed_json_objects_dirname: str,
    ):
        json_object = {
            "json_object": json_object,
            "key": key,
        }
        self._create_test_action_result_keyed_json_objects_dir(
            test_action_result_keyed_json_objects_dirname,
        )

        test_action_result_keyed_json_object_path = join(
            test_action_result_keyed_json_objects_dirname, f"{key}.json"
        )

        put_json_object(test_action_result_keyed_json_object_path, json_object)
        logger.debug(
            f"Saved Test Action Result Keyed Json Object {key} to output directory {test_action_result_keyed_json_object_path}"
        )

    def _save_to_index_dir(
        self,
        team_id: int,
        test_exe_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
    ):
        team_id = str(team_id)
        self._create_keyed_json_objects_index_dir(team_id)
        indexed_file_path = join(
            self._get_keyed_json_objects_index_dirname(), team_id, key
        )
        indexed_json_object = self._build_index_json_object(
            test_exe_id,
            test_action_result_id,
            key,
            json_object,
            self._get_keyed_json_object_version(key, team_id) + 1,
        )
        put_json_object(indexed_file_path, indexed_json_object)
        logger.debug("Created Test Action Result Keyed Json Object index directory")
        return indexed_json_object

    def _create_test_action_result_keyed_json_objects_dir(
        self,
        test_action_result_keyed_json_objects_dirname: str,
    ):
        if not exists(test_action_result_keyed_json_objects_dirname):
            mkdir(test_action_result_keyed_json_objects_dirname)
            logger.debug(
                f"Created Test Action Result Keyed Json Object output directory at {test_action_result_keyed_json_objects_dirname}"
            )
        return test_action_result_keyed_json_objects_dirname

    def _create_keyed_json_objects_index_dir(self, team_id: str):
        keyed_json_objects_index_dirname = self._get_keyed_json_objects_index_dirname()
        path = join(keyed_json_objects_index_dirname, team_id)
        if not exists(path):
            mkdir(path)
            logger.debug(
                f"Created Test Action Result Keyed Json Object index directory at {path}"
            )

    def _get_keyed_json_object_version(self, key: str, team_id: str):
        try:
            keyed_json_object = self.get_test_action_result_keyed_json_object(
                key, int(team_id)
            )
            return keyed_json_object["version"]
        except ResourceNotFoundException:
            return 0

    def _build_index_json_object(
        self,
        test_exe_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
        version: int,
    ):
        return {
            "test_run_execution_id": test_exe_id,
            "test_action_result_id": test_action_result_id,
            "json_object": json_object,
            "key": key,
            "version": version,
        }

    def _build_test_action_result_keyed_json_objects_dirname(
        self, test_exe_id: str, test_action_result_id: str
    ):
        return join(
            self.test_results_base_path,
            test_exe_id,
            ACTION_LOGS_DIRNAME,
            test_action_result_id,
            ACTION_LOGS_KEYED_JSON_OBJECTS_DIRNAME,
        )

    def _get_keyed_json_objects_index_dirname(self):
        return join(
            self.keyed_json_objects_index_dirname, KEYED_JSON_OBJECTS_INDEX_PATH
        )

    def _isascii(self, s: str):
        return s.isascii() and s.isprintable()
