#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import collections.abc as collections
import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ctf.common import constants as common_constants
from ctf.common.constants import ActionTag
from ctf.ctf_client.lib.api_helper import UTFApis
from ctf.ctf_client.lib.ctf_apis import ActionTagsList
from prettytable import PrettyTable

# TODO: We should probably raise specific exceptions instead of generic ones.
# This will allow us to define an exception handler function so we can handle
# each exception differently.

logger = logging.getLogger(__name__)


def run_test(test_id: int, env: Optional[Dict] = None):
    """
    Function to run a test from terminal.
    :param int test_id: test id which is to be executed.
    :param Optional env: this will update the env used by the test.
    :return: returns the response whether the test is executed or not with
    error or success message and a test result url where use can get the
    test results.
    """
    try:
        # Call function to run a test test from terminal
        api = UTFApis()
        result = api.run_test(test_id, env)
        logger.debug(result["message"])

    except Exception as e:
        logger.exception(str(e))
        raise


def run_test_suite(test_suite_id: int):
    """
    Function used to run a test suite from terminal
    :param int test_suite_id: test suite if which is to be executed from
    terminal.
    :return: returns the response with error or success message that whether
    the test suite is successfully executed or not.
    """
    try:
        # calls function to run a test suite
        api = UTFApis()
        result = api.run_test_suite(test_suite_id)
        print(result["message"])

    except Exception as e:
        logger.exception(str(e))
        raise


def schedule_test(test_id: int, execution_date: datetime, repeat_interval: int = 0):
    """
    Function to schedule a test from terminal.
    :param int test_id: test id which is to be scheduled.
    :param date execution_date: date and time on which the test should be
    executed.
    :param int repeat_interval: repeat interval for test like when the test
    suite should automatically scheduled. Values can be 0=NEVER, -1=EVERYDAY,
    -2=EVERYWEEK, -3=EVERYMONTH
    :return: returns the response with error or success message that whether
    the given test id is successfully scheduled or not.
    """
    try:
        # Calls function to schedule a test from terminal
        api = UTFApis()
        if not execution_date:
            execution_date = datetime.datetime.now()
        result = api.schedule_test(test_id, execution_date, repeat_interval)
        logger.debug(result["message"])

    except Exception as e:
        logger.exception(str(e))
        raise


def schedule_test_suite(
    test_suite_id: int, execution_date: datetime, repeat_interval: int = 0
):
    """
    Function to schedule a test suite from terminal.
    :param int test_suite_id: test suite id which is to be scheduled.
    :param date execution_date: date and time on which the test suite should be
    executed.
    :param int repeat_interval: repeat interval for test suite like when the
    test suite should automatically scheduled. Values can be 0=NEVER,
    -1=EVERYDAY, -2=EVERYWEEK, -3=EVERYMONTH
    :return: returns the response with error or success message that whether
    the given test suite id is successfully scheduled or not.
    """
    try:
        # Calls function to schedule a test suite from terminal
        api = UTFApis()
        if not execution_date:
            execution_date = datetime.datetime.now()
        result = api.schedule_test_suite(test_suite_id, execution_date, repeat_interval)
        logger.debug(result["message"])

    except Exception as e:
        logger.exception(str(e))
        raise


# TODO: Making team_id optional. Will push all changes to client at once.
def check_if_test_setup_is_free(test_setup_id: int, team_id: int = None):
    """
    Function to check if given test setup is free or not.
    :param int test_setup_id: test setup id which is to be checked whether is
    that free or busy.
    :return: returns the response with true or false that whether the test
    setup is busy or not. If its true, then the given test setup is free
    else it's busy.
    """

    if os.environ.get(common_constants.CTF_CLIENT_TEST_SETUP_ID) is not None:
        return True

    try:
        # calls function to check if given test setup is busy or free
        api = UTFApis()
        result = api.check_if_test_setup_is_free(team_id, test_setup_id)
        if result:
            logger.debug("Test setup " + str(test_setup_id) + " is Free")
        else:
            logger.debug("Test setup " + str(test_setup_id) + " is not free")

        return result
    except Exception as e:
        logger.exception(str(e))
        raise


# TODO: Making team_id optional. Will push all changes to client at once.
def set_test_setup_and_devices_busy(test_setup_id: int, team_id: int = None):
    """
    Function to set the test setup status to busy.
    :param int test_setup_id: test setup id which is to be marked as busy.
    :return: returns the response with true or false that whether the test
    setup id marked as busy or not. If its true then the test setup is marked
    as busy else test setup if free or used by other test/user.
    """
    if os.environ.get(common_constants.CTF_CLIENT_TEST_SETUP_ID) is not None:
        return True

    try:
        # calls function to set given test setup as busy
        api = UTFApis()
        result = api.set_test_setup_and_devices_busy(
            team_id=team_id, test_setup_id=test_setup_id
        )
        logger.debug(
            "Test setup " + str(test_setup_id) + " marked as busy = " + str(result)
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


# TODO: Making team_id optional. Will push all changes to client at once.
def set_test_setup_and_devices_free(test_setup_id: int, team_id: int = None):
    """
    Function to set the test setup status to free.
    :param int test_setup_id: test setup id which is to be marked as free.
    :return: returns the response with true or false that whether the test
    setup id marked as free or not. If its true then the test setup is marked
    as free else test setup if busy or used by other test/user.
    """
    if os.environ.get(common_constants.CTF_CLIENT_TEST_SETUP_ID) is not None:
        return True

    try:
        # calls function to set given test setup as free
        api = UTFApis()
        result = api.set_test_setup_and_devices_free(
            team_id=team_id, test_setup_id=test_setup_id
        )
        logger.debug(
            "Test setup " + str(test_setup_id) + " marked as free = " + str(result)
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


# TODO: Making team_id optional. Will push all changes to client at once.
def get_test_setup_devices_and_connections(
    test_setup_id: int, team_id: int = None, test_setup_dir_path: str = None
):
    """
    Function to get the test setup devices and its connection details.
    :param int test_setup_id: test setup id of which all the details of devices
    and its connection needs to be fetched.
    :return: returns the objects of connections  and list of all the devices
    used in the given test setup.
    """
    try:
        # calls function to get devices and connection details of test setup
        api = UTFApis()
        return api.get_test_setup_devices_and_connections(
            team_id=team_id, test_setup_id=test_setup_id
        )
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
    Function to create a test run result from terminal.
    :param str name: name which is to be set for test run result.
    :param str identifier: unique string or uuid to be set as identifier for
    test run result.
    :param str description: description of the test run result.
    :param int team_id: id of team to which the test result should be added
    :return: returns the response with error or success message that whether
    the test run result is successfully created or not.
    """
    ctf_client_test_exe_id = os.environ.get(common_constants.CTF_CLIENT_TEST_EXE_ID)
    # TODO: Add an API call that verifies that the ctf_client_test_exe_id
    # is valid for the team and the user so that the user cannot spoof the team.
    if ctf_client_test_exe_id is not None:
        data = {"id": ctf_client_test_exe_id}
        result = {
            "error": "",
            "message": "",
            "data": data,
        }
        return result
    try:
        # calls function to create a test run result
        api = UTFApis()
        result = api.create_test_result(
            name=name,
            identifier=identifier,
            description=description,
            team_id=team_id,
            test_setup=test_setup,
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


# TODO: This should not return a dictionary. The endpoint returns 400/500 error
# when something goes wrong in the backend call, which will cause an exception.
# We can then handle the error in the exception. This should be fixed in the UTF
# refactor/design. (code is in team_test_run_results_view.py)
def save_test_action_result(
    test_run_id: int,
    description: str,
    outcome: int,
    logs: str,
    start_time: datetime.datetime.now(),
    end_time: datetime.datetime.now(),
    step_idx: int = None,
    tags: Union[ActionTagsList, List[ActionTag], None] = None,
    test_result_dir_path=None,
):
    """
    Function to save test action result.
    :param int test_run_id: test run id for which the action results needs to be
    saved.
    :param str description: description of the action.
    :param int outcome: outcome value of the action that whether is action is
    passed or failed.
    :param str logs: action result logs.
    :param date_time start_time: execution start time of the action.
    :param date_time end_time: execution end time of the action.
    :return: returns the response with error or success message that whether
    the action results are successfully saved or not.
    """
    parent_action_id = os.environ.get(common_constants.CTF_CLIENT_TEST_PARENT_ACTION_ID)

    try:
        # calls function to save a test action result

        tags_list = tags.get_list() if isinstance(tags, ActionTagsList) else tags
        if tags_list:
            for tag in tags_list:
                tag["level"] = tag["level"].value
        tags_json = json.dumps(tags_list)
        api = UTFApis()
        logs = logs.replace("\x00", "")
        result = api.save_action_result(
            test_run_id,
            description,
            outcome,
            logs,
            start_time,
            end_time,
            parent_action_id,
            tags_json,
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


def save_test_action_result_json_data(
    test_action_result_id: int,
    ctf_json_data_all: str,
):
    """
    Function called to save action result data for test run from terminal.
    :param test_action_result_id: test action result id for which the data comes from.
    :param data_source: contains the title of the data source that the data is associated with.
    :param data_list: contains the json list of key value pairs.
    :return: returns response with error or success message that whether
    the action results are successfully saved or not.
    """
    try:
        # calls function to save a test action result
        api = UTFApis()
        result = api.save_action_result_json_data(
            test_action_result_id=test_action_result_id,
            ctf_json_data_all=ctf_json_data_all,
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


def tg_add_test_action_heatmap(
    test_exe_id: int,
    test_action_result_id: int,
    initiator_file_path: str,
    responder_file_path: str,
    description: str,
):
    api = UTFApis()
    result = api.save_heatmap_files(
        test_exe_id,
        test_action_result_id,
        initiator_file_path,
        responder_file_path,
        description,
    )
    return result


def save_test_action_result_keyed_json_object(
    test_exec_id: Union[str, int],
    test_action_result_id: Union[str, int],
    key: str,
    json_object: Dict[str, Optional[Any]],
):
    """
    Function called to save action result keyed object.
    :param test_exec_id
    :param test_action_result_id: test action result id for which the js object comes from.
    :param key: The unique identifier for this json object.
    :param json_object: The json object to store.
    :return: returns response with error or success message that whether
    the action json object is successfully saved or not.
    """
    try:
        api = UTFApis()
        result = api.save_test_action_result_keyed_json_object(
            test_exec_id, test_action_result_id, key, json_object
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise e


def get_test_action_result_keyed_json_object(key: str, team_id: int):
    """
    Function called to Get action result keyed object.
    :param key: The unique identifier for this json object.
    :return: returns response with error or TestActionResultKeyedJsonObject.
    """
    try:
        api = UTFApis()
        result = api.get_test_action_result_keyed_json_object(key, team_id)
        return result
    except Exception as e:
        logger.debug(str(e))
        return None


def list_keyed_json_object_for_test_action_result(
    test_exec_id: int,
    test_action_result_id: int,
    page: int = 1,
    offset: int = 10,
):
    """
    Function called to List Test Action Result Keyed Objects associated with a TestActionResult.
    :param test_exec_id
    :param test_action_result_id: test action result id for which the json object comes from.
    :param key: The unique identifier for this json object.
    :return: returns response with error or TestActionResultKeyedJsonObject.
    """
    try:
        api = UTFApis()
        result = api.list_keyed_json_object_for_test_action_result(
            test_exec_id, test_action_result_id, page, offset
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise e


def list_keyed_json_object_for_test_run_execution(
    test_exec_id: int,
    page: int = 1,
    offset: int = 10,
):
    """
    Function called to List Test Action Result Keyed Objects associated with a TestRunExecution.
    :param test_exec_id
    :param key: The unique identifier for this json object.
    :return: returns response with error or TestActionResultKeyedJsonObject.
    """
    try:
        api = UTFApis()
        result = api.list_keyed_json_object_for_test_run_execution(
            test_exec_id, page, offset
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise e


def delete_test_action_result_keyed_json_object(key: str, team_id: int):
    """
    Function called to DELETE action result keyed object.
    :param test_action_result_id: test action result id for which the js object comes from.
    :param key: The unique identifier for this json object.
    :return: returns response with error or success message that whether
    the action json object is successfully deleted or not.
    """
    try:
        api = UTFApis()
        result = api.delete(key, team_id)
        return result
    except Exception as e:
        logger.debug(str(e))
        return None


def save_action_log_file(
    source_file_path,
    constructive_path,
    test_exe_id,
    test_action_result_id,
    test_result_dir_path=None,
    data_processing_config_key: str = None,
):
    try:
        # calls function to set given test setup as free
        api = UTFApis()
        result = api.save_action_log_file(
            source_file_path,
            constructive_path,
            test_exe_id,
            test_action_result_id,
            data_processing_config_key=data_processing_config_key,
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


def save_log_file(
    source_file_path,
    constructive_path,
    test_exe_id,
    test_result_dir_path=None,
    log_type: int = None,
    data_processing_config_key: str = None,
):
    try:
        # calls function to set given test setup as free
        api = UTFApis()
        result = api.save_log_file(
            source_file_path,
            constructive_path,
            test_exe_id,
            log_type=log_type,
            data_processing_config_key=data_processing_config_key,
        )
        logger.debug("Logs saved for test " + str(test_exe_id))
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


# TODO: This API needs some work too. The endpoint call never returns an exception.
# This probably does not need to return a dictionary either since when successful we don't
# do anything with the response. We should also consider how we want to handle when we
# fix and do throw an exception. (team_test_run_results_view.py)
def save_test_run_outcome(
    test_run_id: int,
    dashboard_details: List[Dict] = None,
    test_result_summary: List[Dict] = None,
    test_status: int = None,
    test_result_dir_path: str = None,
):
    """
    Function used to save test run outcome.
    :param int test_run_id: test run id for which test run outcome to be saved.
    :return: returns the test run outcome result that whether the test is
    passed or failed.
    """
    try:
        # calls function to save test action result outcome
        api = UTFApis()
        result = api.save_test_result_outcome(
            test_run_id, dashboard_details, test_result_summary
        )
        return result
    except Exception as e:
        logger.exception(str(e))
        raise


def get_list_of_user_teams():
    """
    Function called to get the current logged in user's team(s).
    :return: returns the list of logged in user's teams with details such as
    team name, description, team id, etc...
    """
    try:
        # calls function to get list of teams associated with logged in user
        api = UTFApis()
        result = api.get_list_of_user_teams()
        return result["data"]
    except Exception as e:
        logger.exception(str(e))
        raise


def get_list_of_user_team_test_setups(team_id: int):
    """
    Function to get the list of all the test setup(s) created under the given
    team id.
    :param int team_id: team id under which all the test setup(s) list needs to
    be fetched.
    :return: returns the list of all the test setup(s) associated with the
    given team id.
    """
    try:
        # calls function to get list of test setups within given team id
        api = UTFApis()
        result = api.get_list_of_user_team_test_setups(team_id)
        return result["data"]["test_setup"]
    except Exception as e:
        logger.exception(str(e))
        raise


def get_list_of_user_team_tests(team_id: int):
    """
    Function to get the list of all the test(s) created under the given
    team id.
    :param int team_id: team id under which all the test(s) list needs to
    be fetched.
    :return: returns the list of all the test(s) associated with the
    given team id.
    """
    try:
        # calls function to get list of tests within given team id
        api = UTFApis()
        result = api.get_list_of_user_team_tests(team_id)
        return result["data"]["test_data"]
    except Exception as e:
        logger.exception(str(e))
        raise


def get_list_of_user_team_test_suites(team_id: int):
    """
    Function to get the list of all the test suite(s) created under the given
    team id.
    :param int team_id: team id under which all the test suite(s) list needs to
    be fetched.
    :return: returns the list of all the test suite(s) associated with the
    given team id.
    """

    try:
        # calls function to get list of tests within given team id
        api = UTFApis()
        result = api.get_list_of_user_team_test_suites(team_id)
        return result["data"]["test_suite_data"]
    except Exception as e:
        logger.exception(str(e))
        raise


def reserve_test_setup(test_setup_id: int, team_id: int = None):
    """
    This function will attempt to reserve the test setup. It's meant
    to reduce the amount of boiler plate code when writing UTF scripts.
    :param int test_setup_id: id of the test setup
    :return: No return value, but exception is thrown if unable to reserve
    test set up.
    """
    if check_if_test_setup_is_free(team_id=team_id, test_setup_id=test_setup_id):
        if not set_test_setup_and_devices_busy(
            team_id=team_id, test_setup_id=test_setup_id
        ):
            raise Exception(f"Unable to set test setup id: {test_setup_id} to busy.")
    else:
        raise Exception(f"Test setup id: {test_setup_id} is not free.")


def api_help():
    """
    Function to get help for all the functions from helper_functions.
    :return: displays the help for all the functions with their name,
    description, parameters, etc...
    """
    try:
        functions_list = [
            reserve_test_setup,
            run_test,
            run_test_suite,
            schedule_test,
            schedule_test_suite,
            check_if_test_setup_is_free,
            set_test_setup_and_devices_busy,
            set_test_setup_and_devices_free,
            get_test_setup_devices_and_connections,
            create_test_run_result,
            save_test_action_result,
            save_test_run_outcome,
            get_list_of_user_teams,
            get_list_of_user_team_test_setups,
            get_list_of_user_team_tests,
            get_list_of_user_team_test_suites,
            api_help,
            save_test_action_result_keyed_json_object,
            get_test_action_result_keyed_json_object,
            delete_test_action_result_keyed_json_object,
        ]
        api = UTFApis()
        api.get_help_for_all_function(functions_list)
    except Exception as e:
        logger.exception(str(e))
        raise


def dict_to_pretty_table(
    dict_list: List[Dict], columns: Union[List, Dict] = None
) -> PrettyTable:
    """
    Generates a human readable table representation of a
    list of dicts that can be printed to the console or logs

    Args:
        dict_list (List[Dict]): the dicts to be represented
        columns (Generic[List, Dict], optional): Which columns/keys from the dicts
            to include in the table.
            Use a list to filter to certain keys.
            Use a dict to map new names for the table. Defaults to None.

    Raises:
        ValueError: If anything other than None, List, Dict is passed for "columns"

    Returns:
        PrettyTable:
    """
    if isinstance(columns, collections.Mapping):
        dict_keys = columns.keys()
        table_keys = columns.values()
    elif isinstance(columns, collections.Iterable) and not isinstance(columns, str):
        dict_keys = table_keys = columns
    elif not columns:
        dict_keys = table_keys = dict_list[0].keys() if dict_list else []
    else:
        raise ValueError("columns parameter is not of types [None, List, Dict]")

    table = PrettyTable(table_keys)
    for _dict in dict_list:
        table.add_row([_dict[key] for key in dict_keys])
    return table
