# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from ctf.ctf_client.serverless_lib.serverless_api import ServerlessApi
from mock import patch


@pytest.mark.parametrize(
    "jsons, print_val",
    [
        ([{"a": 1}, {"b": 2}], "ABC"),
        ([{"abc": 123}, {"xyz": 789}], "XYZ"),
    ],
)
@patch(
    "ctf.ctf_client.serverless_lib.serverless_api.glob.glob",
    return_value=["a.x", "b.x"],
)
@patch("ctf.ctf_client.serverless_lib.serverless_api.open")
@patch("ctf.ctf_client.serverless_lib.serverless_api.json.loads")
def test_get_list_of_user_team_test_setups(
    mock_loads, mock_open, mock_glob, jsons, print_val
):
    # assign the returns and effects for the mocks from the parametrized values
    mock_loads.side_effect = jsons

    serverless_api = ServerlessApi()
    serverless_api._test_setups_dir_path = "abc"

    result_list = serverless_api.get_list_of_user_team_test_setups(team_id=None)
    # the return value should be the result of all the json loads into a list
    assert result_list == jsons
