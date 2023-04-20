#!/usr/bin/env fbpython

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json

import unittest.mock as mock

import pytest

from ctf.ctf_client.serverless_lib.exceptions import ServerlessConfigException

from ctf.ctf_client.serverless_lib.serverless_api import ServerlessApi


TEST_RESULT_DIR = "~/test_results_dir_mock"
TEST_SETUP_DIR = "~/test_setup_dir_mock"
CTF_CLIENT_APP_DATA = "~/ctf_client_app_data_mock"
VALID_SERVERLESS_CONFIG = {
    "test_results_dir": TEST_RESULT_DIR,
    "test_setups_dir": TEST_SETUP_DIR,
    "ctf_client_app_data": CTF_CLIENT_APP_DATA,
}

INVALID_SERVERLESS_CONFIG = ""

ERROR_MSG = "Missing or Malformed ~/.ctf_serverless_config file."


class TestSetServerlessVariables:
    def test_serverless_config_valid_json(self):
        # Arrange
        read_data = json.dumps(VALID_SERVERLESS_CONFIG)
        mock_open = mock.mock_open(read_data=read_data)
        # Act
        ctf_api = ServerlessApi()
        with mock.patch("builtins.open", mock_open):
            ctf_api.set_serverless_config()
        # Assert
        assert ctf_api._test_setups_dir_path == TEST_SETUP_DIR
        assert ctf_api._test_results_storage_path == TEST_RESULT_DIR

    def test_serverless_config_invalid_json(self):
        # Arrange
        read_data = json.dumps(INVALID_SERVERLESS_CONFIG)
        mock_open = mock.mock_open(read_data=read_data)
        # Act
        ctf_api = ServerlessApi()
        with mock.patch("builtins.open", mock_open):
            # Assert
            with pytest.raises(ServerlessConfigException) as ex:
                ctf_api.set_serverless_config()
        # Assert
        assert ERROR_MSG in str(ex)

    def test_serverless_config_missing(self):
        # Arrange
        mock_open = mock.mock_open()
        mock_open.side_effect = FileNotFoundError
        # Act
        ctf_api = ServerlessApi()
        with mock.patch("builtins.open", mock_open):
            # Assert
            with pytest.raises(FileNotFoundError) as _:
                ctf_api.set_serverless_config()
