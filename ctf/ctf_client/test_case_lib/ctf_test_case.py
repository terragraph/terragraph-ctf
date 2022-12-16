#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import atexit
import datetime
import logging
import os
import sys
import traceback
import types
import uuid
from queue import Queue

import ctf.ctf_client.test_case_lib.config as cfg
from ctf.common import constants as common_constants
from ctf.ctf_client.lib.constants import TestActionStatusEnum
from ctf.ctf_client.lib.helper_functions import (
    create_test_run_result,
    get_test_setup_devices_and_connections,
    reserve_test_setup,
    save_log_file,
    save_test_action_result,
    save_test_run_outcome,
    set_test_setup_and_devices_free,
)

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter("[%(levelname)s]:%(message)s"))
out_hdlr.setLevel(cfg.LOG_LEVEL)
logger.addHandler(out_hdlr)
logger.setLevel(cfg.LOG_LEVEL)

# Global flag for disabling CTF logs
disable_ctf_log = False


def ctf_log(msg: str, log_type: str = "info"):
    global disable_ctf_log
    if not disable_ctf_log:
        if log_type == "debug":
            logger.debug(msg)
        if log_type == "error":
            logger.error(msg)
        else:
            logger.info(msg)


# Expected return value for action functions
class TestActionResult:
    __slots__ = ["outcome", "log", "output"]

    def __init__(
        self,
        outcome: TestActionStatusEnum,
        log: str,
        output: object = None,
    ):
        """
        TestActionResult constructor.

        parameters:
        outcome - enum of type TestActionStatusEnum
        log - log to associate to test action
        output - Users may populate this field if they need to pass
                output from this action to a future action in the queue.
        """
        self.outcome = outcome
        self.log = log
        self.output = output

    def succeeded(self):
        return (
            True
            if self.outcome == TestActionStatusEnum.SUCCESS
            or self.outcome == TestActionStatusEnum.WARNING
            else False
        )


class CtfTestCase:
    def __init__(
        self,
        name: str,
        description: str,
        team_id: int,
        test_setup_id: int,
        continue_on_failure: bool = False,
        disable_ctf_logs: bool = False,
    ):
        """
        CtfTestCase Constructor.

        parameters:
        name - name of the test
        description - description of test
        team_id - the id of the ctf team
        test_setup - the test setup to use for the test
        continue_on_failure - If set to True, will execute all test actions regardless of failure.
        """
        self.name = name
        self.description = description
        self.action_queue = Queue()
        self.action_results = []
        self.continue_on_failure = continue_on_failure
        global disable_ctf_log
        disable_ctf_log = disable_ctf_logs

        # private
        self.__devices = get_test_setup_devices_and_connections(test_setup_id)
        self.__team_id = team_id
        self.__test_setup_id = test_setup_id
        self.__is_submitted = False
        self.__reserved_test_setup = False
        self.__test_run_id = None
        self.__test_passed = True

    def get_devices_in_test_setup(self):
        """
        Returns list of devices in a test setup.
        """
        return self.__devices

    def send_command(self, device: object, cmd: str, timeout: int):
        return device.connection.send_command(cmd=cmd, timeout=timeout)

    def add_action(
        self,
        func: types.FunctionType,
        description: str,
        continue_on_failure: bool = False,
    ):
        """
        Adds a test action to the action queue.

        Note: your function MUST return TestActionResult or CTF will
        mark the action with a Warning action result.

        parameters:
        func - function pointer for the action to execute
        description - description of the test action
        continue_on_failure - Bool
        """
        action = _TestAction(
            func=func,
            description=description,
            continue_on_failure=continue_on_failure,
        )
        self.action_queue.put(action)

    def get_last_action_result(self):
        """
        This function will retrieve the TestActionResults of the previous action.
        If no action results are available, the function returns None.

        Note: Use this function if you want to access data from the previous action

        Returns:
        The last TestActionResult in the action_results list
        """
        return self.action_results[-1] if len(self.action_results) else None

    def get_action_result(self, action_index: int):
        """
        This function will retrieve the TestActionResult for given action index.

        Note: Will return None if index is invalid

        Parameters:
        action_index - Index of the action

        Returns:
        TestActionResult from action_results list for the given indexs.
        """
        return (
            self.action_results[action_index]
            if action_index >= 0 and action_index < len(self.action_results)
            else None
        )

    def run(self):
        """
        Executes test actions in the queue.
        """
        if self.__is_submitted:
            ctf_log(
                msg=f"Test run {self.__test_run_id} has already been executed.",
                log_type="error",
            )
            return

        try:
            self.test_run_result = create_test_run_result(
                name=self.name,
                identifier=str(uuid.uuid4),
                description=self.description,
                team_id=self.__team_id,
                test_setup=self.__test_setup_id,
            )
            self.__test_run_id = self.test_run_result["data"]["id"]

            ctf_log(
                msg=f"Test name: {self.name} assigned test run id: {self.__test_run_id}.",
                log_type="info",
            )

            # Handles ctrl-c case and all exceptions
            atexit.register(self.__clean_up)

            # Exception is thrown if unable to reserve test setup.
            reserve_test_setup(self.__test_setup_id)
            ctf_log(
                msg=f"Test setup {self.__test_setup_id} has been reserved.",
                log_type="info",
            )
            self.__reserved_test_setup = True

            ctf_log(
                msg=f"Starting test: {self.name} test_run_id: {self.__test_run_id}.",
                log_type="info",
            )

            # Run action queue
            sequence = 1
            while not self.action_queue.empty():
                action = self.action_queue.get()
                ctf_log(
                    msg=f"Running action #{sequence}: {action.description}",
                    log_type="info",
                )
                res = action.run(self.__test_run_id)
                self.action_results.append(res)
                ctf_log(
                    msg=f"Action #{sequence} outcome: {res.outcome.name}",
                    log_type="info",
                )
                # action failed
                if not res.succeeded():
                    ctf_log(
                        msg=f"Action #{sequence} failed. Error log: {res.log}",
                        log_type="error",
                    )
                    self.__test_passed = False
                    if not self.continue_on_failure or not action.continue_on_failure:
                        while not self.action_queue.empty():
                            action = self.action_queue.get()
                            action.do_not_execute(self.__test_run_id)
                self.__is_submitted = True
                sequence += 1
            test_result = "PASSED" if self.__test_passed else "FAILED"
            ctf_log(msg=f"Completed test: {self.name}: {test_result}.", log_type="info")
        except Exception as e:
            ctf_log(
                msg=f"CTF test: {self.name} exited with exception: {str(e)}",
                log_type="error",
            )
            ctf_log(msg=traceback.format_exc(), log_type="error")

    def save_logs(self, file_path: str, constructive_path="logs"):
        """
        Function to save logs/file to file server.

        Parameters:
        file_path: path to file
        constructive_path: folder to put the files in when zipped/dled by user from UI
        """
        try:
            save_log_file(
                source_file_path=file_path,
                constructive_path=constructive_path,
                test_exe_id=self.__test_run_id,
            )
        except Exception as e:
            ctf_log(msg=f"Exception when trying to save logs: {e}.", log_type="error")

    def _debug_dump(self):
        """
        Debug function that will dump properties of the class in a dictionary.
        """
        return {
            "name": self.name,
            "description": self.description,
            "action_queue": self.action_queue,
            "continue_on_failure": self.continue_on_failure,
            "devices": self.__devices,
            "team_id": self.__team_id,
            "test_setup_id": self.__test_setup_id,
        }

    def __clean_up(self):
        """
        Clean up function for the class. Will save the test outcome if
        a test run id has been allocated and free the test setup if this
        test reserved it.

        Note: Users can extend, but should always call the base function.
        """
        # if a test run id was allocated, save the outcome of the test.
        if self.__test_run_id:
            save_test_run_outcome(self.__test_run_id)
            ctf_ui = os.environ.get(common_constants.CTF_WEB_UI, "")
            if ctf_ui:
                ctf_log(
                    msg=f"CTF test results url: {ctf_ui}/team/{self.__team_id}/test-run-results/detail/{self.__test_run_id}",
                    log_type="info",
                )
        # if this test reserved the test setup, then free it
        if self.__reserved_test_setup:
            set_test_setup_and_devices_free(self.__test_setup_id)
            ctf_log(msg=f"Test setup {self.__test_setup_id} freed.", log_type="info")
            self.__reserved_test_setup = False


class _TestAction:
    def __init__(
        self,
        func: types.FunctionType,
        description: str,
        continue_on_failure: bool = False,
    ):
        """
        TestAction constructor.

        parameters:
        func - Function pointer for the action to execute
        description - description to associate to action
        continue_on_failure - Flag to determine if next action should be ran in failure case
        """
        self.description = description
        self.func = func
        self.continue_on_failure = continue_on_failure

    def run(self, test_run_id):
        """
        Runs the function passed to TestAction. If the function passed
        to the test action does not return a TestActionResult, a warning
        TestActionResult will be used to alert the user.

        returns: TestActionResult
        """
        self.__set_start_time()
        test_action_result = self.func()
        # if return type of action function is not of type TestActionResult,
        # then return a warning to alert the user.
        if not isinstance(test_action_result, TestActionResult):
            test_action_result = TestActionResult(
                outcome=TestActionStatusEnum.WARNING,
                log="Warning: action function does not return TestActionResult.",
            )
        self.__save(test_run_id, test_action_result)
        return test_action_result

    def do_not_execute(self, test_run_id):
        """
        This function is used when the action will not be executed due to a previous
        failure.
        """
        self.__set_start_time()
        test_action_result = TestActionResult(
            outcome=TestActionStatusEnum.WARNING,
            log="Action was not started due to previous failure.",
        )
        self.__save(test_run_id, test_action_result)
        ctf_log(
            msg=f"Action {self.description} was not executed due to previous failure.",
            log_type="info",
        )

    def __set_start_time(self):
        """
        Generic function to set start_time.
        """
        self.start_time = datetime.datetime.now()

    def __save(self, test_run_id: int, test_action_result: TestActionResult):
        """
        This function will save the test action result to CTF.

        parameters:
        test_action_result - TestActionResult of the action function
        """
        try:
            save_test_action_result(
                test_run_id=test_run_id,
                description=self.description,
                outcome=test_action_result.outcome,
                logs=test_action_result.log,
                start_time=self.start_time,
                end_time=datetime.datetime.now(),
            )
        except Exception as e:
            ctf_log(
                msg=f"Exception: {e} occurred when trying to save action result: {self.description}.",
                log_type="error",
            )
