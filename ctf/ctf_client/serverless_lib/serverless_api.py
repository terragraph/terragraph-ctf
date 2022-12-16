# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import glob
import json
import logging
import re
import shutil
from os import makedirs, path
from typing import Any, Dict, List, Optional, Union

from ctf.common.logging_utils import log_call
from ctf.ctf_client.lib.connections_helper import get_devices_and_connections
from ctf.ctf_client.lib.constants import TestActionStatusEnum

from ctf.ctf_client.lib.ctf_apis import CtfApis

from ctf.ctf_client.serverless_lib.exceptions import (
    ResourceNotFoundException,
    ServerlessConfigException,
)

from ctf.ctf_client.serverless_lib.test_action_result_keyed_json_objects_repository import (
    TestActionResultKeyedJsonObjectsRepository,
)

ACTION_LOGS_DIR = "step_logs"
TEST_LOGS_DIR = "collected_device_logs"
ACTION_LOG_FILE = "log.txt"
ACTION_INFO_FILE = "step_info.json"
DESC_MAX_CHAR = 32
ZERO_PADDING = 3
# This is an inverse pattern regex, which negates alphnumeric, underscore and hypen
INVALID_CHAR_REGEX = "[^a-zA-Z0-9_-]"

logger = logging.getLogger(__name__)


class ServerlessApi(CtfApis):
    """
    ServerlessApi stores the test results locally on your machine.
    """

    def __init__(self) -> None:
        # Use _test_results_storage_path to store logs to given path
        self._test_results_storage_path: str = None
        # Provide full path to your local test setups directory
        self._test_setups_dir_path: str = None
        # Logs for given test run are stored under <_test_results_storage_path>/<_test_result_dir_path>
        self._test_result_dir_path: str = None
        # Absolute path to store files and data unique to ctf.
        self._ctf_client_app_data = None

    def set_serverless_config(self):
        """This will setup serverless variables using ~/.ctf_serverless_config file
        {
            "test_setups_dir": "Provide absolute path to test setup directory",
            "test_results_dir": "Provide absolute path to the results directory where logs need to be saved",
            "ctf_client_app_data": "Provide absolute path for CTF to use to store files and data unique to ctf."
        }
        ###
        """
        logger.debug("Setup serverless variables using ~/.ctf_serverless_config file")
        json_format = json.dumps(
            {
                "test_setups_dir": "Provide absolute path to test setup directory",
                "test_results_dir": "Provide absolute path to the results directory where logs need to be saved",
                "ctf_client_app_data": "Provide absolute path for CTF to use to store files and data unique to ctf.",
            }
        )

        error_msg = (
            "Missing or Malformed ~/.ctf_serverless_config file. "
            + "Create a ~/.ctf_serverless_config file with following json data "
            + json_format
        )
        # Serverless config file path
        file_path = path.join(path.expanduser("~"), ".ctf_serverless_config")

        try:
            with open(file_path, "r") as f:
                content = f.read()
                config = json.loads(content)
                self._test_setups_dir_path = config.get("test_setups_dir", None)
                self._test_results_storage_path = config.get("test_results_dir", None)
                self._ctf_client_app_data = config.get("ctf_client_app_data", None)
                if (
                    not self._test_results_storage_path
                    or not self._test_setups_dir_path
                    or not self._ctf_client_app_data
                ):
                    raise ServerlessConfigException(error_msg)

                logger.debug(
                    f"Setup information will be pulled from {self._test_setups_dir_path}"
                )
                logger.debug(
                    f"Logs will be stored at {self._test_results_storage_path}"
                )
        except IOError as e:
            logger.exception(e)
            raise e
        except Exception as e:
            logger.exception(e)
            raise ServerlessConfigException(error_msg)

    def override_serverless_config(
        self,
        test_setups_dir: str,
        test_results_dir: str,
        ctf_client_app_data: str = None,
    ):
        """
        This will override serverless variables set from ~/.ctf_serverless_config file
        """
        logger.debug("Overriding serverless variables")
        self._test_setups_dir_path = test_setups_dir
        self._test_results_storage_path = test_results_dir
        if ctf_client_app_data:
            self._ctf_client_app_data = ctf_client_app_data

    def check_if_test_setup_is_free(self, test_setup_id: int, team_id: int = None):
        """
        Noop for serverless
        """
        return True

    def set_test_setup_and_devices_busy(self, test_setup_id: int, team_id: int = None):
        """
        Noop for serverless
        """
        return True

    # TODO: Making team_id optional. Will push all changes to client at once.
    def set_test_setup_and_devices_free(self, test_setup_id: int, team_id: int = None):
        """
        Noop for serverless
        """
        return True

    def get_test_setup_devices_and_connections(
        self, test_setup_id: int, team_id: int = None
    ):
        """
        Returns list of all the devices used in the given test setup and their connections objects
        """
        try:
            test_setup_json = path.join(
                self._test_setups_dir_path, f"{test_setup_id}.json"
            )
            with open(test_setup_json) as f:
                result_dict = json.load(f)

            devices = result_dict["devices"]
            return get_devices_and_connections(devices)
        except Exception as e:
            logger.exception(str(e))
            raise

    def create_test_run_result(
        self,
        name: str,
        identifier: str,
        description: str,
        team_id: int = None,
        test_setup: int = None,
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
            self._test_result_dir_path = path.join(
                self._test_results_storage_path, test_result_dir
            )
            makedirs(self._test_result_dir_path)
            logger.info(f"Created test result dir at {self._test_result_dir_path}")
            result: Dict = {
                "data": {
                    "id": test_result_dir,
                    "test_result_dir_path": self._test_result_dir_path,
                }
            }
            return result
        except Exception as e:
            logger.exception(str(e))
            raise

    def save_test_action_result(
        self,
        test_run_id: int,
        description: str,
        outcome: int,
        logs: str,
        start_time: datetime.datetime.now(),
        end_time: datetime.datetime.now(),
        step_idx: int,
        tags: List[str] = None,
    ):
        """
        TODO further scoping on need for tags
        Creates Test action result directory {step_idx}_{description}_{status}_{datetime} and
        saves the terminal logs passed with logs param to action_log.txt file under the directory
        """
        try:
            description = description.replace(" ", "_")
            if outcome == TestActionStatusEnum.SUCCESS:
                status = "OK"
            elif outcome == TestActionStatusEnum.FAILURE:
                status = "FAIL"
            else:
                status = "WARN"

            step_idx = f"{step_idx}".zfill(ZERO_PADDING)
            desc = (
                description
                if len(description) < DESC_MAX_CHAR
                else f"{description[:DESC_MAX_CHAR]}..."
            )
            # replace special char in desc.
            # desc can have only alphanumeric or underscore or hypen
            desc = re.sub(f"{INVALID_CHAR_REGEX}", "", desc)
            test_result_dir = f"{step_idx}_{status}_{desc}_{start_time.strftime('%Y_%m_%d_%I_%M_%S_%f')}"
            local_test_action_result_storage_path = path.join(
                self._test_result_dir_path, ACTION_LOGS_DIR, test_result_dir
            )
            makedirs(local_test_action_result_storage_path)
            logger.info(
                f"Test action result dir created at {local_test_action_result_storage_path}"
            )

            # create and dump step info
            step_info = {}
            step_info["name"] = description
            step_info["start_time"] = str(start_time)
            step_info["end_time"] = str(end_time)
            step_info_path = path.join(
                local_test_action_result_storage_path, ACTION_INFO_FILE
            )
            with open(step_info_path, "w") as f:
                f.write(json.dumps(step_info))

            # dump action logs to ACTION_LOG_FILE file
            action_log_path = path.join(
                local_test_action_result_storage_path, ACTION_LOG_FILE
            )
            with open(action_log_path, "w") as f:
                f.write(logs)

            # return test_result_dir info
            result: Dict = {"data": {"test_action_result_id": test_result_dir}}

            return result
        except Exception as e:
            logger.exception(str(e))
            raise

    def save_test_action_result_json_data(
        self,
        test_action_result_id: int,
        ctf_json_data_all: str,
    ):
        """
        save json file
        """

    def save_action_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        test_action_result_id,
    ):
        """
        Saves the action log file under <_test_result_dir_path>/<ACTION_LOGS_DIR>/<test_action_result_id>/<constructive_path>
        """
        try:
            local_test_action_result_storage_path = path.join(
                self._test_result_dir_path,
                ACTION_LOGS_DIR,
                test_action_result_id,
                constructive_path,
            )
            makedirs(local_test_action_result_storage_path, exist_ok=True)
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

    def save_log_file(self, source_file_path, constructive_path, test_exe_id):
        """
        Saves the log file under <_test_result_dir_path>/<TEST_LOGS_DIR>/<constructive_path>
        """
        try:
            _test_results_storage_path = path.join(
                self._test_result_dir_path, TEST_LOGS_DIR, constructive_path
            )
            makedirs(_test_results_storage_path, exist_ok=True)
            shutil.copy(source_file_path, _test_results_storage_path)
            logger.info(
                f"Logs saved for test {test_exe_id} at {_test_results_storage_path}"
            )
            result: Dict = {"success": True}
            return result
        except Exception as e:
            # TODO TBD Do we want to exit here or continue even on failure
            logger.exception(str(e))
            raise

    @log_call
    def save_total_logs_file(self, source_file_path, constructive_path, test_exe_id):
        """
        Saves the total log file under <_test_result_dir_path>/<TEST_LOGS_DIR>
        """
        if self._test_result_dir_path:
            destination_dir = path.join(self._test_result_dir_path, constructive_path)
            result = self._copy_save_file(
                source_file_path,
                destination_dir,
            )
            logger.info(f"Total Logs saved for test {test_exe_id} at {destination_dir}")
            return result

        logger.info("result dir is not yet set, unable to save total logs.")

    def _copy_save_file(
        self, source_file_path, destination_dir, destination_file_name=None
    ):
        """
        Generic file saver code. Specify a destination_file_name to rename the file as well.
        """
        destination_path = destination_dir

        if destination_file_name:
            destination_path = path.join(destination_path, destination_file_name)

        try:
            makedirs(destination_dir, exist_ok=True)
            shutil.copy(source_file_path, destination_path)

            result: Dict = {"success": True}
            return result
        except Exception as e:
            # TODO TBD Do we want to exit here or continue even on failure
            logger.exception(str(e))
            raise

    def save_test_run_outcome(
        self,
        test_run_id: int,
        dashboard_details: List[Dict] = None,
        test_result_summary: List[Dict] = None,
        test_status: int = None,
    ):
        """
        TODO further scoping
        Saves the test status in result file under <test_result_dir_path>/
        """
        try:
            s = "Test Passed"
            status = "OK"
            # test_status is 0 for pass else it is the failed step id
            if test_status != 0:
                s = f"Test failed at step {test_status}"
                status = "FAIL"
            result = path.join(self._test_result_dir_path, f"result_{status}.txt")
            with open(result, "w") as f:
                f.write(s)
            msg = f"Test run outcome saved to {result}"
            result: Dict = {"message": msg}
            return result
        except Exception as e:
            logger.exception(str(e))
            raise

    @log_call(result=False)
    def get_list_of_user_team_test_setups(self, team_id: int):
        """
        Function called to get the list of test setup(s) within the test_setups_dir
        :param team_id: irrelevant (exists as part of api, but unused here)
        :return: returns response with the list of test setup(s) available
        with their details such as test setup id, name, and description.
        """
        test_setup_list = []
        # find all "*.json" files in the test_setups_sir
        test_setup_json_path = path.join(self._test_setups_dir_path, "*.json")
        test_setup_json_files = glob.glob(test_setup_json_path)
        # extract the json dict from each json file
        for setup_file in test_setup_json_files:
            with open(setup_file) as f:
                test_setup_dict = json.load(f)
                test_setup_list.append(test_setup_dict)

        return test_setup_list

    def save_test_action_result_keyed_json_object(
        self,
        test_exe_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
        *args,
        **kwargs,
    ) -> Dict:
        """
        Saves a JSON Object identified by a unique key
        related to the test_exe_id and test_action_result_id
        :param test_exe_id: Test run identifier.
        :param test_action_result_id: Test Action Result identifier.
        :param key: Key identifier.
        :return: returns Stored Dict with JSON Object Data and related Test Run information
        {
            "test_run_execution_id": "test_name_1",
            "test_action_result_id": "action_name_1",
            "json_object": {
                "key": {
                    "nested_1_key": {
                        " nested_2_key": "value_2"
                    }
                }
            },
            "key": "unique_key",
            "version: 1
        }
        """
        try:
            keyed_json_objects_respository = TestActionResultKeyedJsonObjectsRepository(
                self._test_results_storage_path, self._ctf_client_app_data
            )
            if "team_id" not in kwargs:
                raise ValueError("team_id, is required")

            team_id = kwargs.pop("team_id")
            return keyed_json_objects_respository.save_test_action_result_keyed_json_object(
                team_id,
                test_exe_id,
                test_action_result_id,
                key,
                json_object,
            )
        except Exception as e:
            logger.exception("Exception: {e}")
            raise e

    def get_test_action_result_keyed_json_object(
        self,
        key: str,
        team_id: int,
    ):
        """
        Retrieves a JSON Object with its unique key identifier.

        :param key: JSON Object key identifier.
        :param test_action_result_id: Test Action Result identifier.
        :return: returns Dict with JSON Object Data
        :return: returns Stored Dict with JSON Object Data and related Test Run information
        {
            "test_run_execution_id": "test_name_1",
            "test_action_result_id": "action_name_1",
            "json_object": {
                "key": {
                    "nested_1_key": {
                        " nested_2_key": "value_2"
                    }
                }
            },
            "key": "unique_key",
            "version: 1
        }
        """
        test_action_result_keyed_json = None
        try:
            keyed_json_objects_respository = TestActionResultKeyedJsonObjectsRepository(
                self._test_results_storage_path, self._ctf_client_app_data
            )

            test_action_result_keyed_json = (
                keyed_json_objects_respository.get_test_action_result_keyed_json_object(
                    key, team_id
                )
            )
        except ResourceNotFoundException as e:
            logger.debug(f"ResourceNotFoundException: {e}")

        return test_action_result_keyed_json

    def delete_test_action_result_keyed_json_object(
        self,
        key: str,
        team_id: int,
    ):
        """
        Deletes the specified JSON Object via the unique key identifier.
        :param key: JSON OBject key identifier.
        :raises ResourceNotFoundException if the specified key does not exist
        """
        test_action_result_keyed_json = None
        try:
            keyed_json_objects_respository = TestActionResultKeyedJsonObjectsRepository(
                self._test_results_storage_path, self._ctf_client_app_data
            )
            test_action_result_keyed_json = keyed_json_objects_respository.delete_test_action_result_keyed_json_object(
                key, team_id
            )
        except ResourceNotFoundException as e:
            logger.debug(f"ResourceNotFoundException: {e}")

        return test_action_result_keyed_json

    def save_heatmap_files(
        self,
        test_exe_id: int,
        test_action_result_id: int,
        initiator_file_path: str,
        responder_file_path: str,
        description: str = "Heatmap",
    ):
        """Not implemented for serverless"""
        return {}
