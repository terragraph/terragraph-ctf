#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import json
import logging
import shutil
from os import makedirs, path
from typing import Any, Dict, List, Optional, Union

from ctf.ctf_client.lib.connections_helper import get_devices_and_connections
from ctf.ctf_client.lib.constants import TestActionStatusEnum

from ctf.ctf_client.serverless_lib.exceptions import (
    DuplicateResourceException,
    ResourceNotFoundException,
)

from ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository import (
    TestActionResultKeyedJsonObjectsRepository,
)


ACTION_LOGS_DIR = "action_logs"
TEST_LOGS_DIR = "uploaded_logs"

logger = logging.getLogger(__name__)


DEFAULT_TEST_RUN_RESULT_PATH = "/tmp/ctf/"


def check_if_test_setup_is_free(test_setup_id: int, team_id: int = None):
    """
    Noop for serverless
    """
    return True


def set_test_setup_and_devices_busy(test_setup_id: int, team_id: int = None):
    """
    Noop for serverless
    """
    return True


# TODO: Making team_id optional. Will push all changes to client at once.
def set_test_setup_and_devices_free(test_setup_id: int, team_id: int = None):
    """
    Noop for serverless
    """
    return True


def get_test_setup_devices_and_connections(
    test_setup_id: int, team_id: int = None, test_setup_dir_path: str = None
):
    """
    Returns list of all the devices used in the given test setup and their connections objects
    """
    try:
        test_setup_json = path.join(test_setup_dir_path, f"{test_setup_id}.json")
        with open(test_setup_json) as f:
            result_dict = json.load(f)

        return get_devices_and_connections(result_dict)
    except Exception as e:
        logger.exception(str(e))
        raise


def create_test_run_result(
    name: str,
    identifier: str,
    description: str,
    team_id: int = None,
    test_setup: int = None,
    local_test_result_storage_path: str = "/tmp/ctf/",
):
    """
    Creates test result dir with format <test_name>_<setup_id>_<datetime>
    returns {
        "data":{
            "id" : <test_result_dir>,
            "test_result_dir_path": <path>
        }
    }
    """
    try:
        name = name.replace(" ", "_")
        test_result_dir = f"{name}_{test_setup}_{datetime.datetime.now().strftime('%Y_%m_%d_%I_%M_%S_%f')}"
        test_result_dir_path = path.join(
            local_test_result_storage_path, test_result_dir
        )
        makedirs(test_result_dir_path)
        logger.info(f"Created test result dir at {test_result_dir_path}")
        result: Dict = {
            "data": {
                "id": test_result_dir,
                "test_result_dir_path": test_result_dir_path,
            }
        }
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


def save_test_action_result(
    test_run_id: int,
    description: str,
    outcome: int,
    logs: str,
    start_time: datetime.datetime.now(),
    end_time: datetime.datetime.now(),
    step_idx: int = None,
    tags: List[str] = None,
    test_result_dir_path=None,
):
    """
    TODO further scoping on need for tags
    Test action result directory {step_idx}_{description}_{status}_{datetime}
    """
    description = description.replace(" ", "_")
    if outcome == TestActionStatusEnum.SUCCESS:
        status = "passed"
    elif outcome == TestActionStatusEnum.FAILURE:
        status = "failed"
    else:
        status = "warning"
    if step_idx is None:
        step_idx = ""
    test_result_dir = f"{step_idx}_{description}_{status}_{datetime.datetime.now().strftime('%Y_%m_%d_%I_%M_%S_%f')}"
    local_test_action_result_storage_path = path.join(
        test_result_dir_path, ACTION_LOGS_DIR, test_result_dir
    )
    makedirs(local_test_action_result_storage_path)
    logger.info(
        f"Test action result dir created at {local_test_action_result_storage_path}"
    )
    result: Dict = {"data": {"test_action_result_id": test_result_dir}}
    return result


def save_test_action_result_json_data(
    test_action_result_id: int,
    ctf_json_data_all: str,
):
    """
    save json file
    """


def save_action_log_file(
    source_file_path,
    constructive_path,
    test_exe_id,
    test_action_result_id,
    test_result_dir_path=None,
):
    """
    Saves the action log file under <test_result_dir_path>/<ACTION_LOGS_DIR>/<test_action_result_id>/<constructive_path>
    """
    try:
        local_test_action_result_storage_path = path.join(
            test_result_dir_path,
            ACTION_LOGS_DIR,
            test_action_result_id,
            constructive_path,
        )
        makedirs(local_test_action_result_storage_path)
        shutil.copy(source_file_path, local_test_action_result_storage_path)
        logger.info(
            f"Logs saved for test action {test_action_result_id} at {local_test_action_result_storage_path}"
        )
        result: Dict = {"success": True}
        return result
    except Exception as e:
        # TODO TBD Do we want to exit here or continue even on failure
        logger.exception(str(e))
        raise


def save_log_file(
    source_file_path, constructive_path, test_exe_id, test_result_dir_path=None
):
    """
    Saves the log file under <test_result_dir_path>/<TEST_LOGS_DIR>/<constructive_path>
    """
    try:
        local_test_result_storage_path = path.join(
            test_result_dir_path, TEST_LOGS_DIR, constructive_path
        )
        makedirs(local_test_result_storage_path)
        shutil.copy(source_file_path, local_test_result_storage_path)
        logger.info(
            f"Logs saved for test {test_exe_id} at {local_test_result_storage_path}"
        )
        result: Dict = {"success": True}
        return result
    except Exception as e:
        # TODO TBD Do we want to exit here or continue even on failure
        logger.exception(str(e))
        raise


def save_test_run_outcome(
    test_run_id: int,
    dashboard_details: List[Dict] = None,
    test_result_summary: List[Dict] = None,
    test_status: int = None,
    test_result_dir_path: str = None,
):
    """
    TODO further scoping
    Saves the test status in result file under <test_result_dir_path>/
    """
    try:
        result = path.join(test_result_dir_path, "result.txt")
        s = "Test Passed"
        # test_status is 0 for pass else it is the failed step id
        if test_status != 0:
            s = f"Test failed at step {test_status}"
        with open(result, "w") as f:
            f.write(s)
        msg = f"Test run outcome saved to {test_result_dir_path}/result.txt"
        result: Dict = {"message": msg}
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


def get_list_of_user_team_test_setups(team_id: int):
    """
    TODO: Return a json with list of test setup info
    """
    return []
