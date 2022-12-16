# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ctf.common.constants import ActionTag, TOTAL_LOGS, TOTAL_LOGS_DIR_NAME

from ctf.common.logging_utils import log_call

from ctf.ctf_client.lib.ctf_apis import ActionTagsList, CtfApis

from ctf.ctf_client.lib.helper_functions import (
    check_if_test_setup_is_free as _check_if_test_setup_is_free,
    create_test_run_result as _create_test_run_result,
    delete_test_action_result_keyed_json_object as _delete_test_action_result_keyed_json_object,
    get_list_of_user_team_test_setups as _get_list_of_user_team_test_setups,
    get_list_of_user_team_test_suites as _get_list_of_user_team_test_suites,
    get_list_of_user_team_tests as _get_list_of_user_team_tests,
    get_list_of_user_teams as _get_list_of_user_teams,
    get_test_action_result_keyed_json_object as _get_test_action_result_keyed_json_object,
    get_test_setup_devices_and_connections as _get_test_setup_devices_and_connections,
    reserve_test_setup as _reserve_test_setup,
    run_test as _run_test,
    run_test_suite as _run_test_suite,
    save_action_log_file as _save_action_log_file,
    save_log_file as _save_log_file,
    save_test_action_result as _save_test_action_result,
    save_test_action_result_json_data as _save_test_action_result_json_data,
    save_test_action_result_keyed_json_object as _save_test_action_result_keyed_json_object,
    save_test_run_outcome as _save_test_run_outcome,
    schedule_test as _schedule_test,
    schedule_test_suite as _schedule_test_suite,
    set_test_setup_and_devices_busy as _set_test_setup_and_devices_busy,
    set_test_setup_and_devices_free as _set_test_setup_and_devices_free,
    tg_add_test_action_heatmap as _save_heatmap_files,
)

logger = logging.getLogger(__name__)


class ServerApi(CtfApis):
    """
    ServerApi stores the test results on the CTF instance.
    """

    def run_test(self, test_id: int, env: Optional[Dict] = None) -> {}:
        """
        Function called to run a test from terminal.
        :param test_id: contains test id which is to be run.
        :param env: contains arguments required by the test.
        :return: returns the error or success message received by api to run
        a test from terminal.
        """
        return _run_test(test_id=test_id, env=env)

    def run_test_suite(self, test_suite_id: int):
        """
        Function called to run a test suite from terminal.
        :param test_suite_id: contains test suite id which needs to be run.
        :return: returns response with error or success message that whether
        test suite is successfully run from terminal or not.
        """
        return _run_test_suite(test_suite_id=test_suite_id)

    def schedule_test(
        self, test_id: int, execution_date: datetime, repeat_interval: int = 0
    ) -> {}:
        """
        Function called to schedule a test from terminal.
        :param test_id: contains test id which is to be scheduled.
        :param execution_date: contains the execution date and time of the
        test.
        :param repeat_interval: contains the repeat interval for the test,
        means after how much interval the test should execute, values can be
        0=NEVER, -1=EVERYDAY, -2=EVERYWEEK, -3=EVERYMONTH
        :return: returns the response with error or success message that
        whether the test is successfully scheduled or not.
        """
        return _schedule_test(
            test_id=test_id,
            execution_date=execution_date,
            repeat_interval=repeat_interval,
        )

    def schedule_test_suite(
        self, test_suite_id: int, execution_date: datetime, repeat_interval: int = 0
    ) -> {}:
        """
        Function called to schedule a test suite from terminal.
        :param test_suite_id: contains test suite id which is to be scheduled.
        :param execution_date: contains the execution date and time of the
        test suite.
        :param repeat_interval: contains the repeat interval for the test suite,
        means after how much interval the test suite should execute, values
        can be 0=NEVER, -1=EVERYDAY, -2=EVERYWEEK, -3=EVERYMONTH
        :return: returns the response with error or success message that
        whether the test suite is successfully scheduled or not.
        """
        return _schedule_test_suite(
            test_suite_id=test_suite_id,
            execution_date=execution_date,
            repeat_interval=repeat_interval,
        )

    # check is busy/free, set busy, set free
    def check_if_test_setup_is_free(
        self, test_setup_id: int, team_id: int = None
    ) -> bool:
        """
        Function called from terminal to check if a given test setup id free or
        busy.
        :param test_setup_id: contains test setup id which is to be checked
        as free or busy.
        :return: returns a boolean response as True if given test setup is
        free else return False.
        """
        return _check_if_test_setup_is_free(
            test_setup_id=test_setup_id, team_id=team_id
        )

    def set_test_setup_and_devices_busy(
        self, test_setup_id: int, team_id: int = None
    ) -> bool:
        """
        Function called to set test setup and the devices included into it as
        busy.
        :param test_setup_id: contains test setup id which needs to be set to
        busy along with the devices included into the same test setup id.
        :return: returns response in boolean as True if the given test setup
        is set as busy else returns False.
        """
        return _set_test_setup_and_devices_busy(
            test_setup_id=test_setup_id, team_id=team_id
        )

    def set_test_setup_and_devices_free(
        self, test_setup_id: int, team_id: int = None
    ) -> bool:
        """
        Function called to set test setup and its devices as free.
        :param test_setup_id: contains test setup id which needs to be set as
        free along with the devices included into the same test setup.
        :return: returns the response in boolean as True if test setup and
        it's devices are set as free else returns False.
        """
        return _set_test_setup_and_devices_free(
            test_setup_id=test_setup_id, team_id=team_id
        )

    def get_test_setup_devices_and_connections(
        self, test_setup_id: int, team_id: int = None
    ) -> {}:
        """
        Function called to get the test setup device
        details and its connections.
        :param test_setup_id: contains test setup id of which the device
        details and connection needs to get.
        :return: returns the list of devices added into the given test setup
        along with their connections.
        """
        return _get_test_setup_devices_and_connections(
            test_setup_id=test_setup_id, team_id=team_id
        )

    def create_test_run_result(
        self,
        name: str,
        identifier: str,
        description: str,
        team_id: int = None,
        test_setup: int = None,
    ):
        """
        Function called to to create a test result from terminal.
        :param name: contains the name of test result.
        :param identifier: contains identifier value (a unique value) for the
        test result.
        :param description: contains description of the test result.
        :param team_id: contains the team id for which the test result needs
        to be created.
        :return: returns response with error or success message that whether
        the test result is successfully created or not.
        """
        return _create_test_run_result(
            name=name,
            identifier=identifier,
            description=description,
            team_id=team_id,
            test_setup=test_setup,
        )

    def save_test_action_result(
        self,
        test_run_id: int,
        description: str,
        outcome: int,
        logs: str,
        start_time: datetime.now(),
        end_time: datetime.now(),
        step_idx: int,
        tags: Union[ActionTagsList, List[ActionTag], None] = None,
    ):
        """
        Function called to save action result for test run from terminal.
        :param test_run_id: test run id for which the action results needs to
        be stored.
        :param description: contains the description of the action result.
        :param outcome: contains the outcome of the action result, such as
        pass, failed, etc...
        :param logs: contains the log of the action.
        :param data: contains the data of the action result.
        :param start_time: contains the start time of the action.
        :param end_time: contains the end time of the action.
        :return: returns response with error or success message that whether
        the action results are successfully saved or not.
        """
        return _save_test_action_result(
            test_run_id=test_run_id,
            description=description,
            outcome=outcome,
            logs=logs,
            start_time=start_time,
            end_time=end_time,
            step_idx=step_idx,
            tags=tags,
        )

    def save_test_action_result_json_data(
        self, test_action_result_id: int, ctf_json_data_all: str
    ):
        """
        Function called to save action result data for test run from terminal.
        :param test_action_result_id: test action result id for which the data comes from.
        :param data_source: contains the title of the data source that the data is associated with.
        :param data_list: contains the json list of key value pairs.
        :return: returns response with error or success message that whether
        the action results are successfully saved or not.
        """
        return _save_test_action_result_json_data(
            test_action_result_id=test_action_result_id,
            ctf_json_data_all=ctf_json_data_all,
        )

    def save_heatmap_files(
        self,
        test_exe_id: int,
        test_action_result_id: int,
        initiator_file_path: str,
        responder_file_path: str,
        description: str = "Heatmap",
    ):
        return _save_heatmap_files(
            test_exe_id=test_exe_id,
            test_action_result_id=test_action_result_id,
            initiator_file_path=initiator_file_path,
            responder_file_path=responder_file_path,
            description=description,
        )

    def save_action_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        test_action_result_id,
        data_processing_config_key: str = None,
    ):
        return _save_action_log_file(
            source_file_path=source_file_path,
            constructive_path=constructive_path,
            test_exe_id=test_exe_id,
            test_action_result_id=test_action_result_id,
            data_processing_config_key=data_processing_config_key,
        )

    def save_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        log_type: int = None,
        data_processing_config_key: str = None,
    ):
        # using ctf/api_server/core/file_server/api_manager.py as an example
        return _save_log_file(
            source_file_path=source_file_path,
            constructive_path=constructive_path,
            test_exe_id=test_exe_id,
            log_type=log_type,
        )

    @log_call
    def save_total_logs_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        data_processing_config_key: str = None,
    ):
        return self.save_log_file(
            source_file_path=source_file_path,
            constructive_path=TOTAL_LOGS_DIR_NAME,
            test_exe_id=test_exe_id,
            log_type=TOTAL_LOGS,
            data_processing_config_key=data_processing_config_key,
        )

    # TODO: This API needs some work too. The endpoint call never returns an exception.
    # This probably does not need to return a dictionary either since when successful we don't
    # do anything with the response. We should also consider how we want to handle when we
    # fix and do throw an exception. (team_test_run_results_view.py)
    def save_test_run_outcome(
        self,
        test_run_id: int,
        dashboard_details: List[Dict] = None,
        test_result_summary: List[Dict] = None,
        test_status: int = None,
    ) -> Dict:
        """
        Function called to save outcome of a test result from terminal.
        :param test_run_id: test run id for which the outcome needs to be saved.
        :return: returns the response with error or success message that
        whether the test result outcome is successfully saved or not.
        """
        return _save_test_run_outcome(
            test_run_id=test_run_id,
            dashboard_details=dashboard_details,
            test_result_summary=test_result_summary,
            test_status=test_status,
        )

    def get_list_of_user_teams(self):
        """
        Function called to get the list of logged in user.
        :return: returns the list of teams with their name, id and
        description of logged in user.
        """
        return _get_list_of_user_teams()

    def get_list_of_user_team_test_setups(self, team_id: int):
        """
        Function called to get the list of test setup(s) within the given
        team id from terminal.
        :param team_id: contains team id of which the list of test setup(s)
        needs to get.
        :return: returns response with the list of test setup(s) available
        within given team id with their details such as test setup id, name,
        description and status.
        """
        return _get_list_of_user_team_test_setups(team_id=team_id)

    def get_list_of_user_team_tests(self, team_id: int):
        """
        Function called to get the list of tests within given team.
        :param team_id: team id under which all the test(s) list needs to
        be fetched.
        :return: returns the list of all the test(s) associated with the
        given team id.
        """
        return _get_list_of_user_team_tests(team_id=team_id)

    def get_list_of_user_team_test_suites(self, team_id):
        """
        Function called to get the list of test suites within given team.
        :param team_id: team id under which all the test suite(s) list needs to
        be fetched.
        :return: returns the list of all the test suite(s) associated with the
        given team id.
        """
        return _get_list_of_user_team_test_suites(team_id)

    def reserve_test_setup(self, test_setup_id: int, team_id: int = None):
        """
        This function will attempt to reserve the test setup. It's meant
        to reduce the amount of boiler plate code when writing UTF scripts.
        :param int test_setup_id: id of the test setup
        :return: No return value, but exception is thrown if unable to reserve
        test set up.
        """
        return _reserve_test_setup(test_setup_id=test_setup_id, team_id=team_id)

    def save_test_action_result_keyed_json_object(
        self,
        test_exec_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
        *args,
        **kwargs,
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
        return _save_test_action_result_keyed_json_object(
            test_exec_id, test_action_result_id, key, json_object
        )

    def get_test_action_result_keyed_json_object(self, key: str, team_id: int):
        """
        Function called to Get action result keyed object.
        :param key: The unique identifier for this json object.
        :return: returns response with error or TestActionResultKeyedJsonObject.
        """
        return _get_test_action_result_keyed_json_object(key, team_id)

    def delete_test_action_result_keyed_json_object(self, key: str, team_id: int):
        """
        Function called to DELETE action result keyed object.
        :param test_action_result_id: test action result id for which the js object comes from.
        :param key: The unique identifier for this json object.
        :return: returns response with error or success message that whether
        the action json object is successfully deleted or not.
        """
        return _delete_test_action_result_keyed_json_object(key, team_id)
