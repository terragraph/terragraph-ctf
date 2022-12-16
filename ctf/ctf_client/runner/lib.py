#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Library containing CTF test utilities.
"""

import datetime
import json
import logging
import re
import sys
import threading
import time
import warnings
from argparse import Namespace
from collections.abc import Mapping
from concurrent.futures import as_completed, ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from distutils.util import strtobool
from os import makedirs, path
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, cast, Dict, Generator, List, Optional, Sequence, Set, Tuple

from ctf.common.connections.SSHConnection import SSHConnection
from ctf.common.constants import (
    ActionTag as _ActionTag,
    TOTAL_LOGS_DIR_NAME,
    TOTAL_LOGS_FILE_NAME,
)
from ctf.common.enums import TagLevel as _TagLevel
from ctf.common.logging_utils import log_call

# To avoid lint warning of unused imports
ActionTag = _ActionTag
TagLevel = _TagLevel

from ctf.ctf_client.lib.connections_helper import (
    create_ssh_connection as _create_ssh_connection,
    get_ssh_connection_class as _get_ssh_connection_class,
)
from ctf.ctf_client.lib.constants import TestActionStatusEnum
from ctf.ctf_client.server_gateway.api_gateway import get_ctf_api

# To avoid lint warning of unused import
get_ssh_connection_class = _get_ssh_connection_class
create_ssh_connection = _create_ssh_connection

from .exceptions import DeviceCmdError, DeviceConfigError, TestUsageError

logger = logging.getLogger(__name__)

# Silence this warning, as some versions of paramiko will raise
# ResourceWarnings when connections are opened/closed.
warnings.simplefilter("ignore", ResourceWarning)


class ThreadLocal(threading.local):
    """
    Thread local data for ctf logs and json data.

    Enables test step specific logging and json data creation from
    concurrent test steps.

    Any thread that calls log_to_ctf() or save_ctf_json_data()
    must explicitly initialize ThreadLocal on startup - see init().

    Thread specific attributes:
        step_idx: int  # the 1-based index of the current test step

    References:
        https://docs.python.org/3/library/threading.html?highlight=local#thread-local-data
        https://github.com/python/cpython/blob/master/Lib/_threading_local.py

    Note:
        It is possible to keep ctf logs and json data in ThreadLocal.

        Pro: Eliminates the mutexes that protect the ctf log and the json data
        dictionaries.

        Con: Harder to maintain. Threads need to dispose of their logging data
        before exiting by returning it (or possibly pushing it to CTF). Thread-creators
        need to handle the logging data of their child threads.
    """

    DEFAULT_INVALID_STEP_IDX: int = -1  # Valid step indecies are positive
    initialized = False  # ThreadLocal has been explicitly initialized at least once.

    def init(self, step_idx: int):
        """Initialize thread local data.

        Pooled threads must call `init()` explicitly on start up,
        because `__init__()` is only called automatically the first
        time a thread accesses ThreadLocal.
        """
        self.step_idx = step_idx
        ThreadLocal.initialized = True

    @log_call(params=False, returned=False, result=False)
    def clear(self):
        ThreadLocal.initialized = False

    def __init__(self, step_idx: Optional[int] = None):
        """Initialize the thread specific dictionary

        Invoked automatically once per thread the first time it accesses ThreadLocal.
        """

        if step_idx:
            self.step_idx = step_idx
            ThreadLocal.initialized = True
        else:
            self.step_idx = self.DEFAULT_INVALID_STEP_IDX


class BaseCtfTest:
    """Base class for CTF tests.

    Encapsulates a typical test sequence using the CTF API.
    """

    # Name of the test
    TEST_NAME: str = ""
    # Description of the test
    DESCRIPTION: str = ""

    # Template string holding default node data filename for this test (used
    # when not passed in as a CLI argument).
    #
    # Variable substitutions:
    #  - SETUP_ID => self.test_setup_id
    NODES_DATA_FORMAT: str = ""

    # If `self.NODES_DATA_FORMAT` is set, is it optional?
    NODES_DATA_OPTIONAL: bool = False

    def __init__(self, args: Namespace) -> None:
        #### Task execution ####
        # Number of thread pool workers
        self.max_workers: int = int(args.max_workers)
        # Thread pool for submitting concurrent tasks *within* a test step
        # (e.g. to execute commands on multiple test devices simultaneously)
        self.thread_pool = ThreadPoolExecutor(
            thread_name_prefix="NodeWorkers", max_workers=self.max_workers
        )

        # CTF run mode flag. Running in serverless mode or CTF server APIs
        self.serverless = (
            False if not args.serverless else bool(strtobool(args.serverless))
        )
        logger.info(f"Running in serverless mode = {self.serverless}")

        # Run with or without ctf server
        self.ctf_api = get_ctf_api(serverless=self.serverless)  #

        # Configure serverless variables
        if self.serverless:
            self.ctf_api.set_serverless_config()

        # Default timeout period to use for each test step (in seconds)
        self.timeout: int = args.timeout
        # Default timeout period for the log file collection step (in seconds)
        self.log_collect_timeout: int = args.log_collect_timeout
        # Default timeout period to use for scp commands (in seconds)
        self.scp_timeout: int = args.scp_timeout
        # Steps to skip
        self.skip_steps: Sequence[str] = args.skip or [] if "skip" in args else []
        # Enable verbose ssh debug logs
        self.ssh_debug: bool = args.debug and (not args.no_ssh_debug)
        # test case config json overlay/update from the CTF UI
        self.json_args: str = args.json_args
        # Logs will be stored locally (default /tmp/ctf_logs/) in addition to CTF server. User will manage the local logs.
        self.store_logs_locally = args.store_logs_locally

        # Parse test-specific arguments (K=V pairs) into a Dict
        self.test_args: Dict[str, Any] = self._build_test_args(
            args.test_args if "test_args" in args else {}
        )
        logger.debug(f"Using test arguments: {self.test_args}")

        # Is this test run via Sandcastle (Facebook CI)?
        self.run_sandcastle: bool = args.run_sandcastle

        #### CTF-specific ####
        # CTF team ID
        self.team_id: int = args.team_id
        # CTF test setup ID
        self.test_setup_id: int = int(args.test_setup_id)
        # Have we acquired/reserved this test setup?
        self.setup_reserved: bool = False
        # This instance's CTF test execution ID (a.k.a. test run ID)
        self.test_exe_id: int = 0
        # Start time of the test
        self.test_start_time = int(time.time())
        # Test device information, initialized during `self.init_test_run()`
        self.device_info: Dict = {}

        # Map from test step index to a list of log lines
        self.ctf_logs: Dict[int, List[str]] = {}
        # Lock for thread safe logging
        # Protects: ctf_logs
        self.ctf_log_lock = threading.Lock()

        # Map from test step index to json data to visualize
        self.ctf_json_data: Dict[int, Dict] = {}
        # Lock for thread safe json data update
        # Protects: ctf_json_data
        self.ctf_json_data_lock = threading.Lock()

        # Map from test step index to keyed json object test action result objects
        self.ctf_keyed_json_objects: Dict[int, List[Dict]] = {}

        # Lock for thread safe keyed json objects update
        # Protects: ctf_keyed_json_objects
        self.ctf_keyed_json_objects_lock = threading.Lock()

        # Lock for thread safe data push to CTF
        # Protects
        #   save_test_action_result()
        #   save_test_action_result_json_data()
        self.ctf_push_lock = threading.Lock()

        # Thread-local data. See ThreadLocal for details.
        self.thread_local = ThreadLocal()

        # Logs to collect from nodes of each particular device type after each test run
        self.logfiles: Dict[str, List[str]] = {}

        # Safe tempdir which is available in all test steps
        # Initialized in run_test()
        self.tempdir = None

        # Node data for this test, holding a combination of setup-specific and
        # test-specific configuration.
        #
        # This is a map of integer node IDs (matching `self.device_info` from
        # the CTF database) to configuration objects.
        #
        # Validate some basic things early in this constructor since
        # self.nodes_data isn't loaded until after CTF test data is initialized.
        self.nodes_data: Dict = {}
        self.nodes_data_file: str = ""
        if args.nodes_data:
            self.nodes_data_file = args.nodes_data
        elif args.nodes_data_dir and self.NODES_DATA_FORMAT:
            f = self.NODES_DATA_FORMAT.format(SETUP_ID=self.test_setup_id)
            self.nodes_data_file = path.join(args.nodes_data_dir, f)
        if (
            not self.nodes_data_file
            and self.NODES_DATA_FORMAT
            and not self.NODES_DATA_OPTIONAL
        ):
            f = self.NODES_DATA_FORMAT.format(SETUP_ID=self.test_setup_id)
            raise TestUsageError(f"Required node data file is missing: {f}")
        if self.nodes_data_file and not path.isfile(self.nodes_data_file):
            err = f"Node data file not found: {self.nodes_data_file}"
            if self.NODES_DATA_OPTIONAL:
                logger.warning(err)
                self.nodes_data_file = ""
            else:
                raise FileNotFoundError(err)

    def cleanupThreadPool(self, pool: ThreadPoolExecutor) -> None:
        if pool:
            # error: "ThreadPoolExecutor" has no attribute "_threads"
            for pool_thread in pool._threads:
                try:
                    # pyre-fixme[16]: `Thread` has no attribute `_tstate_lock`.
                    if pool_thread._tstate_lock:
                        pool_thread._tstate_lock.release()
                except Exception as e:
                    logger.debug(f"Problem with releasing a thread: {e}")
                    pass
            pool.shutdown(wait=False)

    def __del__(self) -> None:
        self.cleanupThreadPool(self.thread_pool)

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        """Return any test-specific parameter definitions.

        This is a map of parameter names to object values as follows:
        ```
        {
            "desc": "<param description>",
            "required": <bool, default False>,
            "default": <default value, implicitly None>,
            "convert": <optional argument conversion function, default type str>
        }
        ```
        """
        return {}

    def _build_test_args(self, args: Dict) -> Dict[str, Any]:
        """Build a map of test-specific arguments."""
        test_args: Dict[str, Any] = {}
        test_params: Dict[str, Dict] = self.test_params()

        # Parse CLI args
        for arg in args:
            k, v = arg.split("=")
            if k not in test_params:
                raise TestUsageError(f"Unknown test argument '{k}'")
            test_args[k] = v

        # Process test param definitions
        for k, v in test_params.items():
            if k in test_args:
                if "convert" in v:
                    test_args[k] = v["convert"](test_args[k])
            else:
                if "required" in v and v["required"]:
                    raise TestUsageError(f"Missing required test argument '{k}'")
                test_args[k] = v["default"] if "default" in v else None

        return test_args

    def execute(self, acquire: bool = True) -> int:
        """Execute the test.

        Return zero upon success, or a non-zero value upon failure.
        """
        with self._test_manager():
            test_methods = [self.init_test_run, self.run_test]
            if acquire:
                # pyre-fixme[6]: Expected `Union[BoundMethod[typing.Callable(BaseCtfTest....
                test_methods.insert(0, self.acquire_test_setup)
            for method in test_methods:
                # pyre-fixme[16]: Callable `init_test_run` has no attribute `__name__`.
                logger.debug(f"[[ Running method: '{method.__name__}' ]]")
                error = method()
                if error:
                    return int(error)

        return 0

    def _run_test(self) -> int:
        """Run all test steps, e.g. run_test_steps() surrounded by pre_run()
        and post_run(), among other functions.
        """
        steps = [
            {
                "name": "[ Test info ]",
                "function": self.log_test_info,
                "function_args": (),
                "success_msg": "",
            },
            (
                {
                    "name": "[ Pre-run ]",
                    "function": lambda *a, **k: None,
                    "function_args": (),
                    "success_msg": "Pre-run was skipped",
                }
                if "pre_run" in self.skip_steps
                else {
                    "name": "[ Pre-run ]",
                    "function": self.pre_run,
                    "function_args": (),
                    "success_msg": "Pre-run finished",
                }
            ),
            *self.get_test_steps(),
            (
                {
                    "name": "[ Post-run ]",
                    "function": lambda *a, **k: None,
                    "function_args": (),
                    "success_msg": "Post-run was skipped",
                }
                if "post_run" in self.skip_steps
                else {
                    "name": "[ Post-run ]",
                    "function": self.post_run,
                    "function_args": (),
                    "success_msg": "Post-run finished",
                    "continue_on_failure": True,
                }
            ),
            {
                "name": "[ Collect logs ]",
                "function": self._collect_logfiles_wrapper,
                "function_args": (),
                "success_msg": "Log collection finished",
                "continue_on_failure": True,
                "never_fail": True,
            },
        ]
        post_run_idx = len(steps) - 2  # post_run(), collect_logfiles()
        ret: int = self.run_test_steps(steps, post_run_idx)
        self.finish_test_run(ret)
        return ret

    def run_test(self) -> int:
        """Run all test steps with a default temporary directory"""
        ret = 1
        with TemporaryDirectory(prefix="ctf_") as tmpdir:
            self.tempdir = tmpdir
            ret = self._run_test()
        return ret

    def log_test_info(self) -> None:
        """Log some information specific to this test run to CTF."""
        device_list = []
        for device_id, device in self.device_info.items():
            device_list.append(
                f"[{device_id}] {device.connection.ip_address.lower()} "
                + f"({device.device_type().capitalize()})"
            )
        devices = "\n".join(device_list)

        self.log_to_ctf(f"Test command:\n{' '.join(sys.argv)}")
        self.log_to_ctf(f"Devices:\n{devices}")

    def pre_run(self) -> None:
        """Function to run before all test steps."""
        pass

    def post_run(self) -> None:
        """Function to run after all test steps."""
        pass

    def acquire_test_setup(self, wait_time: float = 30.0) -> int:
        """Acquire the test setup, busy-waiting if unavailable."""
        # TODO: This polling should move to CTF itself - we should join a queue
        done = False
        while not done:
            try:
                done = self.ctf_api.set_test_setup_and_devices_busy(self.test_setup_id)
            except Exception as e:
                logger.info(
                    f"acquire_test_setup | ignoring {str(e)} raised by set_test_setup_and_devices_busy"
                )
            if not done:
                logger.info(
                    f"Test Setup {self.test_setup_id} is not available. "
                    + f" Sleeping {wait_time}s"
                )
                time.sleep(wait_time)
                continue

        self.setup_reserved = True
        logger.debug(f"Acquired test setup {self.test_setup_id}")
        return 0

    def free_test_setup(self) -> None:
        """Release the test setup."""
        if self.setup_reserved:
            self.ctf_api.set_test_setup_and_devices_free(self.test_setup_id)
            self.setup_reserved = False

    def resource_cleanup(self) -> None:
        """Test resource cleanup"""
        # Free the test setup if needed
        if self.setup_reserved:
            self.free_test_setup()

    def init_test_run(self) -> int:
        """Set up the CTF run.

        Returns a non-zero integer upon error.
        """
        # Get the configuration
        self.device_info = self.ctf_api.get_test_setup_devices_and_connections(
            test_setup_id=self.test_setup_id,
        )
        if not self.device_info:
            logger.error(
                f"Unable to get device info for test setup {self.test_setup_id}"
            )
            return 10
        logger.debug(f"device_info: {self.device_info}")

        # Set ssh logging verbosity and disable sftp
        for device in self.device_info.values():
            if isinstance(device.connection, SSHConnection):
                device.connection.enable_verbose_logs(self.ssh_debug)
                device.connection.enable_sftp(False)

        self.test_start_time = int(time.time())
        result = self.ctf_api.create_test_run_result(
            name=self.TEST_NAME,
            identifier=str(int(time.time())),
            description=self.DESCRIPTION,
            team_id=self.team_id,
            test_setup=self.test_setup_id,
        )
        logger.debug(f"Got test run result: '{result}'")
        test_exe_details = result.get("data")
        if not test_exe_details:
            logger.error(f"Did not receive test run data: '{test_exe_details}'")
            return 11

        self.test_exe_id = test_exe_details.get("id")
        if not self.test_exe_id:
            logger.error(f"Unable to get test_exe_id: {self.test_exe_id}")
            return 12

        self.post_test_init()

        return 0

    def post_test_init(self) -> None:
        """Function called after init_test_run(), when all test data should be
        initialized.
        """
        self.nodes_data = self._load_nodes_data(self.nodes_data_file)

    def get_test_steps(self) -> List[Dict]:
        """Return a list of test steps to be executed in run_test_steps().

        Each step must be an object with the following structure:
        ```
        {
            "name": "<description of test step>",
            "function": <function to call>,
            "function_args": (<tuple of function arguments to pass>),
            "success_msg": "<message to log upon success>",
            "concurrent": <bool>,
            "delay": <int>,
            "post_delay": <int>,
            "error_handler": [
                {
                    "function": <function to call if step fails>,
                    "function_args": (<tuple of error function arguments to pass>),
                }
            ],
            "continue_on_failure": <bool>,
            "negate_result": <bool, toggles step result>,
            "never_fail": <bool>
        }
        ```
        """
        return []

    def get_meta_data_for_step(self, step: Dict) -> List[Dict]:
        """
        Use this to get ActionTags and logfiles which needs to be recorded with step.
        Returns data in below format which includes
        1. list of error tags (referred as action tags in CTF) which will be hooked to action.
        2. List of log files for each node_id which will be saved under CTF action
        3. Function to call for cleanup of logs after logs are pulled
        4. Args for the above function
        {
            "tags": List[ActionTag],
            "logs": Dict[int, List],
            "logs_cleanup_fn": <function to call>,
            "logs_cleanup_fn_args": (<tuple of function arguments to pass>)
        }
        """
        return []

    def _run_test_step(self, step: Dict, step_idx) -> int:
        """Run one test step and report result to CTF.

        Note: `step_idx` is 1-based
        Returns 0 on success, `step_idx` otherwise
        """

        # We are in a new thread. Publish step_idx in thread local data.
        self.thread_local.init(step_idx)

        step_start = datetime.datetime.now()
        logger.info(f"[Step {step_idx}] {step['name']}")
        step["start_time"] = datetime.datetime.utcnow()

        # Delay
        delay_sec = step.get("delay", 0)
        if delay_sec > 0:
            self.log_to_ctf(
                f"Delaying step {step_idx} {step['name']} for {delay_sec} s"
            )
            time.sleep(delay_sec)

        # Run the test step
        step_outcome: int = 0  # 0=success, otherwise failed step_idx
        try:
            step["function"](*step["function_args"])
            if step["success_msg"]:
                self.log_to_ctf(step["success_msg"], "info")
        except Exception as e:
            step_outcome = step_idx
            err_msg = f"Failed to run step [{step['name']}]: {e} ({type(e)})"
            logger.exception(err_msg)
            self.log_to_ctf(err_msg, "error")

        # Negate step result
        if step.get("negate_result", False):
            if step_outcome == 0:
                step_outcome = step_idx
            else:
                step_outcome = 0
            self.log_to_ctf(
                f"Test step {step_idx} result negated to {step_outcome}", "info"
            )

        # Find the test action outcome code for CTF
        never_fail: bool = step.get("never_fail", False)
        if step_outcome == 0:
            reported_outcome = TestActionStatusEnum.SUCCESS
        elif never_fail:
            reported_outcome = TestActionStatusEnum.WARNING
        else:
            reported_outcome = TestActionStatusEnum.FAILURE

        # Post Delay
        post_delay_sec = step.get("post_delay", 0)
        if post_delay_sec > 0 and (
            step.get("continue_on_failure", False) or never_fail or step_outcome == 0
        ):
            self.log_to_ctf(
                f"Waiting for {post_delay_sec}s after executing step {step_idx} {step['name']}"
            )
            time.sleep(post_delay_sec)

        # Get log files and tags for this step
        step_meta_data = self.get_meta_data_for_step(step=step)

        # Filter tags and log files from the step_meta_data
        error_tags = []
        log_files: Dict[int, List] = {}
        for meta_data in step_meta_data:
            error_tags.extend(meta_data.get("tags", []))
            if "logs" in meta_data:
                self.merge_dict_of_lists(log_files, meta_data["logs"])

        # Get the CTF logs for the current step.
        with self.ctf_log_lock:
            ctf_logs = self.ctf_logs.get(step_idx, [])

        # Save the action result
        # TODO: Return `action_result` to avoid ctf_push_lock
        with self.ctf_push_lock:
            action_result = self.ctf_api.save_test_action_result(
                test_run_id=self.test_exe_id,
                description=step["name"],
                outcome=reported_outcome,
                logs="\n".join(ctf_logs),
                start_time=step_start,
                end_time=datetime.datetime.now(),
                step_idx=step_idx,
                tags=error_tags,
            )
        logger.debug(f"Recorded test action result: {action_result}")

        test_action_result_id = action_result["data"]["test_action_result_id"]

        # Get the CTF json data
        with self.ctf_json_data_lock:
            ctf_json_data = self.ctf_json_data.get(step_idx, {})

        # Save CTF Json Data
        if len(ctf_json_data) > 0:
            with self.ctf_push_lock:
                save_json_data_result = self.ctf_api.save_test_action_result_json_data(
                    test_action_result_id=test_action_result_id,
                    ctf_json_data_all=json.dumps(ctf_json_data),
                )
                logger.debug(f"Recorded CTF JSON data: {save_json_data_result}")

        # Get the Test Action Result with key
        with self.ctf_keyed_json_objects_lock:
            ctf_keyed_json_objects = self.ctf_keyed_json_objects.get(step_idx, {})

        # Save Test Action Result Key Json Objects
        if len(ctf_keyed_json_objects) > 0:
            with self.ctf_push_lock:
                for test_action_result_key in ctf_keyed_json_objects:
                    save_test_action_result_keyed_json = (
                        self.ctf_api.save_test_action_result_keyed_json_object(
                            self.test_exe_id,
                            test_action_result_id,
                            test_action_result_key["key"],
                            test_action_result_key["json_object"],
                            team_id=self.team_id,
                        )
                    )
                    logger.debug(
                        f"Recorded CTF Test Action Result key JSON: {save_test_action_result_keyed_json}"
                    )

        # Pull the log files from node and push to CTF
        self.collect_logfiles_for_action(log_files, test_action_result_id)
        # Use this method to do any post processing
        self.secondary_step_action(test_action_result_id, step)

        # Run the logs_cleanup_fn
        for meta_data in step_meta_data:
            try:
                if "logs_cleanup_fn" in meta_data:
                    meta_data["logs_cleanup_fn"](*meta_data["logs_cleanup_fn_args"])
            except Exception as e:
                err_msg = f"Failed to handle logs_cleanup_fn [{step['name']}]: {e} ({type(e)})"
                logger.exception(err_msg)
                self.log_to_ctf(err_msg, "error")

        ret_val: int = step_outcome
        if never_fail:
            ret_val = 0
        logger.debug(
            f'step:{step["name"]} never_fail:{never_fail} step_outcome:{step_outcome} return:{ret_val}'
        )
        return ret_val

    def secondary_step_action(self, test_action_result_id: int, step: Dict) -> None:
        """Use this method to do any post processing after the step result is saved on CTF"""
        return

    def _get_max_concurrent_steps(self, steps: List[Dict]) -> int:
        """Get the max number of concurrent thread steps"""
        max_concurrent: int = 1
        concurrent: int = 0
        idx: int = 0
        while idx < len(steps):
            if "concurrent" in steps[idx]:
                concurrent = concurrent + 1
            else:
                max_concurrent = max(concurrent, max_concurrent)
                concurrent = 0
            idx = idx + 1
        logger.debug(f"Max number of concurrent test steps = {max_concurrent}")
        return max_concurrent

    def run_test_steps(
        self, steps: List[Dict], post_run_idx: Optional[int] = None
    ) -> int:
        """Run a list of test steps and report each result to CTF.

        See get_test_steps() for the expected data format.

        If any step fails, this will abort and return with the step number
        (1-indexed) that failed. Otherwise, this returns 0 upon success.

        If `post_run_idx` is provided, steps starting at this index (0-based)
        will always be run.
        """

        logger.info(f"**** Starting test: '{self.TEST_NAME} - {self.DESCRIPTION}' ****")

        # Create a thread pool for the concurrent test-steps
        max_step_workers: int = self._get_max_concurrent_steps(steps)
        step_thread_pool = ThreadPoolExecutor(
            thread_name_prefix="TestStepWorkers", max_workers=max_step_workers
        )

        idx: int = 0  # 0-based index into "steps"
        test_outcome: int = 0  # 0=success, otherwise (index of first failed step + 1)
        futures: Dict = {}
        while idx < len(steps):
            # Run the next concurrent test-step group
            futures.clear()
            done: bool = False
            while not done:
                futures[
                    step_thread_pool.submit(
                        self._run_test_step, step=steps[idx], step_idx=idx + 1
                    )
                ] = idx
                if (
                    steps[idx].get("concurrent", False)
                    and (idx + 1) < len(steps)
                    and steps[idx + 1].get("concurrent", False)
                ):
                    idx = idx + 1
                else:
                    done = True

            # Wait for completion of the futures in the test-step group
            first_failed_idx: int = -1
            error_handler_idx: int = -1
            group_continue_on_failure: bool = True

            for future in as_completed(futures.keys()):
                result = future.result()
                completed_idx = futures[future]
                if result != 0:
                    if first_failed_idx == -1:
                        first_failed_idx = completed_idx
                        test_outcome = first_failed_idx + 1
                    step = steps[completed_idx]
                    if (
                        error_handler_idx == -1
                        and "error_handler" in step
                        and len(step["error_handler"]) > 0
                    ):
                        # First failed step in the concurrent group with an error_handler
                        error_handler_idx = completed_idx
                    if not steps[completed_idx].get("continue_on_failure", False):
                        group_continue_on_failure = False

            # Insert an error handler and skip the the rest of the steps when
            #  (1) Any step from the concurrent group has failed --AND--
            #  (2) continue_on_failure is false for *any* failed step in the group --AND--
            #  (3) The concurrent "group" was not the post_run
            # The inserted error handler is the first failed test from the
            # concurrent group that has an error handler.
            if (
                first_failed_idx >= 0
                and not group_continue_on_failure
                and post_run_idx is not None
                and idx < post_run_idx
            ):
                idx = post_run_idx - 1
                if error_handler_idx >= 0:
                    step = steps[error_handler_idx]
                    logger.info(
                        f"**** Inserting error handler for failed step {error_handler_idx+1} ****"
                    )
                    steps.insert(
                        post_run_idx,
                        {
                            "name": "[ Error handler ]",
                            "function": self._run_error_handler,
                            "function_args": (step["error_handler"],),
                            "success_msg": "Error handler finished.",
                        },
                    )

            idx = idx + 1

        self.cleanupThreadPool(step_thread_pool)

        return test_outcome

    def _run_error_handler(self, error_handler: List[Dict]) -> None:
        """Run all functions in the given error handler sequentially."""
        for obj in error_handler:
            obj["function"](*obj["function_args"])

    def get_dashboard_links(self) -> List[Dict]:
        """Return list of dashboard links which will be hooked to test run result
        Dashboard links will be used to show on TestRunResult page.

        CTF accepts dashboard details in below format:
        [{"label":"Grafana" ,"link":"http://grafana/dashboard"}]
        """
        return []

    def finish_test_run(self, test_outcome: int) -> int:
        """Mark the CTF test run as finished."""
        test_status = "Test PASSED"
        # test_outcome is 0 for pass else it is the failed step id
        if test_outcome != 0:
            test_status = f"Test FAILED at step {test_outcome}"
        logger.info(f"*** {test_status} ***")

        dashboard_details = self.get_dashboard_links()
        test_result = self.ctf_api.save_test_run_outcome(
            test_run_id=self.test_exe_id,
            dashboard_details=dashboard_details,
            test_status=test_outcome,
        )
        logger.info(f"**** {test_result['message']}! ****")
        test_url = self.test_url()
        if not self.serverless:
            logger.info(f"Test ID {self.test_exe_id} finished: {test_url}")
        if self.run_sandcastle and not self.serverless:
            pass_fail_symbol = "\u2705" if test_outcome == 0 else "\u274e"
            label = f"CTF {self.test_exe_id} {pass_fail_symbol}"
            logger.info(f"SANDCASTLE|addLink|{label}|{test_url}")

        # Disconnect from all devices
        for device in self.device_info.values():
            device.connection.disconnect()  # TODO Introduce disconnectAllThreads()

        return 0

    def test_url(self) -> str:
        """Return a URL to access test results (after `self.init_test_run()`)."""
        # TODO replace this when added to CTF API
        if self.test_exe_id:
            return f"https://internalfb.com/intern/bunny/?q=ctf+{self.test_exe_id}"
        else:
            return ""

    def _collect_logfiles_wrapper(self) -> None:
        """Call `collect_logfiles()` with `self.logfiles`."""
        # needed to allow subclasses to modify self.logfiles
        self.collect_logfiles(self.logfiles)

    def collect_logfiles(self, logfiles: Dict[str, List[str]]) -> None:
        """Collect any requested log files from the test devices and submit
        them to CTF.
        """
        if not logfiles:
            self.log_to_ctf("No log files to collect.", "info")
            return

        self.log_to_ctf(f"Collecting log files: [{logfiles}]", "info")

        futures: Dict = {}
        for node_id, device in self.device_info.items():
            if device.device_type() in logfiles and logfiles[device.device_type()]:
                futures[
                    self.thread_pool.submit(
                        self._fetch_and_submit_logfiles,
                        node_id,
                        device.connection,
                        logfiles[device.device_type()],
                        self.thread_local.step_idx,
                    )
                ] = node_id

        failed_nodes = []
        for future in as_completed(futures.keys(), timeout=self.log_collect_timeout):
            result = future.result()
            node_id = futures[future]
            if result:
                self.log_to_ctf(
                    f"Node {node_id} finished fetching and pushing log files"
                )
            else:
                failed_nodes.append(node_id)
                self.log_to_ctf(
                    f"Failed to collect log files from node {node_id}", "error"
                )

        if failed_nodes:
            raise DeviceCmdError(
                f"Errors were raised during log collection on {len(failed_nodes)} "
                + f"node(s): {sorted(failed_nodes)}"
            )

    def collect_logfiles_for_action(
        self,
        logfiles: Dict[int, List[str]],
        test_action_result_id: int,
    ) -> None:
        """Collect any requested log files from the test devices and submit
        them to CTF action log.
        """
        if not logfiles:
            self.log_to_ctf(
                f"No log files to collect for action {test_action_result_id}", "info"
            )
            return

        if not test_action_result_id:
            raise TestUsageError("Missing Action result id")

        self.log_to_ctf(
            f"Collecting log files for action {test_action_result_id}: [{logfiles}]",
            "info",
        )

        futures: Dict = {}
        for node_id, device in self.device_info.items():
            if logfiles.get(node_id, None):
                futures[
                    self.thread_pool.submit(
                        self._fetch_and_submit_logfiles,
                        node_id,
                        device.connection,
                        logfiles[node_id],
                        self.thread_local.step_idx,
                        test_action_result_id,
                    )
                ] = node_id

        failed_nodes = []
        for future in as_completed(futures.keys(), timeout=self.log_collect_timeout):
            result = future.result()
            node_id = futures[future]
            if result:
                self.log_to_ctf(
                    f"Node {node_id} finished fetching and pushing log files"
                )
            else:
                failed_nodes.append(node_id)
                self.log_to_ctf(
                    f"Failed to collect log files from node {node_id}", "error"
                )

        if failed_nodes:
            raise DeviceCmdError(
                f"Errors were raised during log collection on {len(failed_nodes)} "
                + f"node(s): {sorted(failed_nodes)}"
            )

    def _fetch_and_submit_logfiles(
        self,
        node_id: int,
        connection: SSHConnection,
        logfiles: Tuple[str, ...],
        step_idx: Optional[int] = None,
        test_action_result_id: Optional[int] = None,
    ) -> bool:
        """Collect the requested log files and submit them to CTF.
        If test_action_result_id is mentioned save logs against given action else
        save logs for test run"""

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        try:
            connection.connect()
        except Exception as e:
            self.log_to_ctf(
                f"Connection failed to {connection.ip_address}: {str(e)}", "error"
            )
            raise

        result: Dict = {}
        success: bool = True
        if self.store_logs_locally:
            local_dir = path.join(
                self.store_logs_locally, str(self.test_exe_id), str(node_id)
            )
            makedirs(local_dir, exist_ok=True)
        else:
            tmp_dir = TemporaryDirectory(prefix="logfiles-")
            local_dir = tmp_dir.name

        for logfile in logfiles:
            # Fetch log file from test device
            self.log_to_ctf(f"Fetching {logfile} to local dir: {local_dir}")
            if not self.fetch_file(connection, local_dir, logfile, recursive=True):
                success = False
                # attempt to reconnect and try to fetch the next file
                try:
                    connection.connect()
                except Exception as e:
                    self.log_to_ctf(
                        f"Connection failed to {connection.ip_address}: {str(e)}",
                        "error",
                    )
                continue

            # Push to CTF
            local_path = Path(f"{local_dir}/{Path(logfile).name}")
            # use step to form log destination path
            step = f"step_{step_idx}_" if step_idx else ""
            if local_path.is_dir():
                dest_path = (
                    f"{node_id}/{step}{test_action_result_id}{logfile}"
                    if test_action_result_id
                    else f"{node_id}{logfile}"
                )
                for f in local_path.glob("*"):
                    if f.is_file():
                        self.log_to_ctf(f"Pushing {f} to CTF path: {dest_path}")
                        if test_action_result_id:
                            result = self.ctf_api.save_action_log_file(
                                source_file_path=f,
                                constructive_path=dest_path,
                                test_exe_id=self.test_exe_id,
                                test_action_result_id=test_action_result_id,
                            )
                        else:
                            result = self.ctf_api.save_log_file(
                                test_exe_id=self.test_exe_id,
                                source_file_path=f,
                                constructive_path=dest_path,
                            )
                        if result["error"]:
                            success = False
                            self.log_to_ctf(result["message"], "error")
                if "error" in result and result["error"]:
                    success = False
            else:
                dest_path = (
                    f"{node_id}/{step}{test_action_result_id}{Path(logfile).parent}"
                    if test_action_result_id
                    else f"{node_id}{Path(logfile).parent}"
                )
                self.log_to_ctf(f"Pushing {local_path} to CTF path: {dest_path}")
                if test_action_result_id:
                    result = self.ctf_api.save_action_log_file(
                        source_file_path=local_path,
                        constructive_path=dest_path,
                        test_exe_id=self.test_exe_id,
                        test_action_result_id=test_action_result_id,
                    )
                else:
                    result = self.ctf_api.save_log_file(
                        test_exe_id=self.test_exe_id,
                        source_file_path=local_path,
                        constructive_path=dest_path,
                    )
                if result["error"]:
                    success = False
                    self.log_to_ctf(result["message"], "error")
            # Break if log push to ctf fails and store_logs_locally is disabled
            if not success and not self.store_logs_locally:
                break
        if not self.store_logs_locally:
            tmp_dir.cleanup()

        return success

    def log_to_ctf(self, msg: str, severity: Optional[str] = "debug") -> None:
        """Record a log message for the current thread.

        This will queue the log for CTF, as well as log it locally at a given
        logging level ("debug", "info", "warning", "error", "critical").

        These logs are not pushed here; they are typically pushed to CTF during
        test steps in run_test_steps().
        """

        if self.thread_local.initialized:
            # Test step execution has started.
            # Note: _run_test_step() initializes self.thread_local.step_idx
            step_idx = self.thread_local.step_idx
        else:
            # Test step execution has not started yet.
            # Tag these logs, and lump them in with logs for test step 1,
            # this ensures that they will get pushed to CTF.
            step_idx = 1
            msg = f"[pre step 1] {msg}"

        timestamped_msg = (
            f"[{datetime.datetime.now().replace(microsecond=0).isoformat()}] {msg}"
        )

        if step_idx < 1:
            raise ValueError(f"Invalid step_idx {step_idx}. See ThreadLocal.")

        with self.ctf_log_lock:
            self.ctf_logs.setdefault(step_idx, []).append(timestamped_msg)

        # Also log to the console
        if severity:
            log_method = getattr(logger, severity, None)
            if callable(log_method):
                log_method(msg)
            else:
                logger.warning(
                    f"log_to_ctf() invoked with unknown severity: {severity}"
                )

    def ping_output_to_ctf_table(
        self, ping_summary: str, ping_stats: str, from_node_id: int, dest_ip: str
    ) -> None:
        packets_transmitted = re.search(r"(\S+) packets transmitted", ping_summary)
        if packets_transmitted:
            packets_transmitted = packets_transmitted.group(1)
        packets_received = re.search(r"(\S+) received", ping_summary)
        if packets_received:
            packets_received = packets_received.group(1)
        packet_loss = re.search(r"(\S+)% packet loss", ping_summary)
        if packet_loss:
            packet_loss = packet_loss.group(1)
        time = re.search(r"time (\S+)ms", ping_summary)
        if time:
            time = time.group(1)

        stats_min = None
        stats_avg = None
        stats_max = None
        stats_mdev = None
        stats_search = re.search(r"= (\S+)/(\S+)/(\S+)/(\S+) ms", ping_stats)
        if stats_search:
            stats_min = stats_search.group(1)
            stats_avg = stats_search.group(2)
            stats_max = stats_search.group(3)
            stats_mdev = stats_search.group(4)

        data_list = [
            {
                "packets transmitted": packets_transmitted,
                "packets received": packets_received,
                "packet loss %": packet_loss,
                "time ms": time,
                "min": stats_min,
                "avg": stats_avg,
                "max": stats_max,
                "mdev": stats_mdev,
            },
        ]
        data_source = f"Node {from_node_id} to {dest_ip}"
        json_data = {
            "data_source": data_source,
            "data_list": data_list,
        }

        json_table_summary = {
            "title": "Ping Summary",
            "columns": "packets transmitted,packets received,packet loss %,time ms",
            "data_source_list": data_source,
        }
        json_table_stats = {
            "title": "Ping Stats",
            "columns": "min,avg,max,mdev",
            "data_source_list": data_source,
        }

        ctf_json_data_all = {
            "ctf_tables": [json_table_summary, json_table_stats],
            "ctf_data": [json_data],
        }
        self.save_ctf_json_data(ctf_json_data_all)

    def save_ctf_json_data(self, json_data: Dict) -> None:
        """Record CTF JSON data for the current test step.

        This JSON data is not pushed here; they are typically pushed to CTF during
        test steps in run_test_steps().
        """

        step_idx = self.thread_local.step_idx
        if step_idx < 1:
            raise ValueError(f"Invalid step_idx {step_idx}. See ThreadLocal.")

        with self.ctf_json_data_lock:
            self.ctf_json_data[step_idx] = json_data

    def save_ctf_test_action_result_with_key(self, key: str, json_object: Dict) -> Dict:
        """Record CTF JSON objects for the current test step.

        This information is useful to retrieve this test action result in future test runs.

        This JSON data is not pushed here; they are typically pushed to CTF during
        test steps in run_test_steps().
        """

        step_idx = self.thread_local.step_idx
        if step_idx < 1:
            raise ValueError(f"Invalid step_idx {step_idx}. See ThreadLocal.")

        with self.ctf_keyed_json_objects_lock:
            self.ctf_keyed_json_objects.setdefault(step_idx, []).append(
                {
                    "key": key,
                    "json_object": json_object,
                }
            )

    def get_ctf_test_action_result_with_key(self, key: str) -> Dict:
        """Retrieve CTF JSON object from previous test runs."""
        test_action_result_keyed_json = (
            self.ctf_api.get_test_action_result_keyed_json_object(key, self.team_id)
        )
        return test_action_result_keyed_json

    def delete_ctf_test_action_result_with_key(self, key: str) -> Dict:
        """Delete CTF JSON object from previous test runs."""
        with self.ctf_keyed_json_objects_lock:
            self.ctf_api.delete_test_action_result_keyed_json_object(key, self.team_id)

    def run_cmd(
        self,
        cmd: str,
        node_ids: Optional[List[int]] = None,
        device_type: str = "generic",
        timeout: Optional[int] = None,
    ) -> Dict[Any, int]:
        """Run a given command on a list of test devices.

        If 'node_ids' is empty, the command will run on all devices of a given
        type.

        Returns a map of Future objects to the associated 'node_id'. Typically,
        wait_for_cmds() is invoked on this return value.
        """
        futures: Dict = {}
        node_set: Set = set(node_ids or [])
        cmd_timeout: int = timeout if timeout else self.timeout

        for node_id, device in self.device_info.items():
            if node_ids:
                if node_id not in node_set:
                    continue
            elif device.device_type() != device_type:
                continue
            futures[
                self.thread_pool.submit(
                    device.action_custom_command, cmd, cmd_timeout - 1
                )
            ] = node_id

        return futures

    def wait_for_cmds(
        self, futures: Dict[Any, int], timeout: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Wait for the given commands to finish, after invoking run_cmd().

        This yields objects with the following format as each command finishes:
        ```
        {
            "success": <boolean>,
            "message": "<command output upon success>",
            "error": "<error string upon failure>",
            "node_id": <int>
        }
        ```

        If a connection error is encountered, raises `DeviceCmdError`.
        """
        cmd_timeout: int = timeout if timeout else self.timeout
        for future in as_completed(futures.keys(), timeout=cmd_timeout):
            result = future.result()
            node_id = futures[future]

            if "connection_error" in result and result["connection_error"]:
                raise DeviceCmdError(
                    f"Node {node_id}: Connection failure: {result['message']}"
                )

            yield {
                "success": result["error"] == 0 and result["returncode"] == 0,
                "message": result["message"],
                "error": result["error"] or result["stderr"] or "",
                "node_id": node_id,
            }

    def _thread_main(self, fn, fn_args: Tuple, step_idx: int) -> Any:
        """Publish step_idx and execute fn"""
        self.thread_local.init(step_idx)
        return fn(*fn_args)

    def try_until_timeout(
        self, fn, fn_args: Tuple, retry_interval: float, timeout: float
    ) -> None:
        """Wrapper for try_until_timeout_noexcept() to generate an exception when it fails.
        Raises: Exception when try_until_timeout_noexcept() returns False.
        """

        success = self.try_until_timeout_noexcept(
            fn=fn, fn_args=fn_args, retry_interval=retry_interval, timeout=timeout
        )
        if not success:
            raise Exception(f"try_until_timeout {fn.__name__} | timed out")

    def try_until_timeout_noexcept(
        self, fn, fn_args: Tuple, retry_interval: float, timeout: float
    ) -> bool:
        """Repeatedly execute `fn` (a function) until it returns a
        truthy value or None, or until the timeout is reached.

        `Exception` raised by `fn` during the retries is ignored.
        The actual max timeout is (timeout + 6 * retry_interval)

        Returns: True if `fn` ran successfully
        Raises : nothing
        """
        time_left = float(timeout)
        start_time = time.monotonic()
        end_time = start_time + time_left
        while True:
            try:
                future = next(
                    as_completed(
                        [
                            self.thread_pool.submit(
                                self._thread_main,
                                fn,
                                fn_args,
                                self.thread_local.step_idx,
                            )
                        ],
                        timeout=time_left,
                    )
                )
                ret = future.result()
                if type(ret) is dict:
                    success = "error" not in ret or str(ret["error"]) == "0"
                else:
                    success = ret is None or bool(ret)
                if success:
                    return True
            except TimeoutError as e:
                self.log_to_ctf(
                    f"try_until_timeout {fn.__name__} | caught {str(e)}", "error"
                )
                return False
            except Exception:
                pass

            now = time.monotonic()
            if now > end_time:
                self.log_to_ctf(f"try_until_timeout {fn.__name__} | timed out", "error")
                return False

            elapsed = now - start_time
            self.log_to_ctf(
                f"try_until_timeout {fn.__name__} | elapsed {elapsed} | retrying in {retry_interval}"
            )
            time_left = max(timeout - elapsed, 5.0 * retry_interval)
            time.sleep(retry_interval)
        return False

    def _test_can_connect(self, connection: SSHConnection) -> bool:
        """Try to connect/disconnect a test device.

        Return: True if connect/disconnect are both successful.

        Note that threads can only disconnect SSHConnection's that
        they established. See ThreadSafeSshConnection in CTF for
        more details.
        """
        result = connection.connect()
        if result["error"] != 0:
            return False
        result = connection.disconnect()
        if "error" in result and result["error"] != 0:
            logger.error(
                f'_test_can_connect | disconnect failed | f{result["message"]}'
            )
            return False
        return True

    def test_can_connect(
        self,
        node_id: int,
        retry_interval: int,
        timeout: int,
        step_idx: Optional[int] = None,
    ) -> bool:
        """Repeatedly attempt connect/disconnect to a test device

        Return: True if connect/disconnect are both successful
        """

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        device = self.device_info[node_id]
        return self.try_until_timeout_noexcept(
            fn=self._test_can_connect,
            fn_args=(device.connection,),
            retry_interval=retry_interval,
            timeout=timeout,
        )

    # TODO This should replace fetch_file, and not reconnect between transfers.
    def fetch_files(
        self,
        node_id: int,
        connection: SSHConnection,
        files: List[str],
        local_tmp_dir: str,
        step_idx: Optional[int] = None,
    ) -> bool:
        """Collect the requested files locally
        This will collect files to local_tmp_dir. The local_tmp_dir will be managed by the caller
        """

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        success: bool = True
        logger.info(
            f"Fetching {files} from node {node_id} to local dir {local_tmp_dir}"
        )

        for file in files:
            # Fetch file from test device
            self.log_to_ctf(f"Fetching {file} to local dir: {local_tmp_dir}")
            if not self.fetch_file(connection, local_tmp_dir, file, recursive=True):
                success = False

        return success

    def fetch_file(
        self,
        connection: SSHConnection,
        local_path: str,
        remote_path: str,
        recursive: bool = True,
    ) -> bool:
        """Fetch a file or directory from a test device, and return True upon
        success.

        The connection object must be initialized before calling this function.
        """
        connection.connect(timeout=self.scp_timeout)
        result: Dict = connection.copy_files_from_remote(
            local_path, remote_path, recursive
        )
        connection.disconnect()
        if result["error"]:
            self.log_to_ctf(
                f"Failed to fetch remote file '{remote_path}' to '{local_path}': "
                + f"{result['message']}",
                "error",
            )
            return False
        return True

    def push_file(
        self,
        connection: SSHConnection,
        local_path: str,
        remote_path: str,
        recursive: bool = True,
        step_idx: Optional[int] = None,
    ) -> bool:
        """Push a file or directory to a test device, and return True upon
        success.

        The connection object must be initialized before calling this function.
        """

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        connection.connect(timeout=self.scp_timeout)
        result: Dict = connection.copy_files_to_remote(
            local_path, remote_path, recursive
        )
        connection.disconnect()

        if result["error"]:
            self.log_to_ctf(
                f"Failed to push local file '{local_path}' to remote path "
                + f"'{remote_path}': {result['message']}",
                "error",
            )
            return False
        return True

    def push_json_file(
        self, connection: SSHConnection, obj: Dict, remote_path: str
    ) -> bool:
        """Push a dictionary as a JSON file to a test device, and return
        True upon success.

        The connection object must be initialized before calling this function.
        """
        with NamedTemporaryFile(mode="w", delete=False) as ntf:
            ntf_path = Path(ntf.name)
            json.dump(obj, ntf, indent=2, sort_keys=True)

        success: bool = False
        try:
            success = self.push_file(
                connection, str(ntf_path), remote_path, recursive=False
            )
        except Exception as e:
            logger.error(f"{type(e).__name__} - SCP failed: {str(e)}")
            raise
        finally:
            ntf_path.unlink()

        return success

    def copy_files_parallel(
        self,
        local_file_path: str,
        remote_file_path: str,
        node_ids: Optional[List[int]] = None,
    ) -> None:
        """Copy files/directories to test nodes."""
        if not (local_file_path and remote_file_path):
            raise TestUsageError("Empty local or remote file paths")

        futures: Dict = {}
        for node_id, device in self.device_info.items():
            if node_ids and node_id not in node_ids:
                continue

            self.log_to_ctf(
                f"Node {node_id}: Copying file from {local_file_path}"
                + f" to node: {remote_file_path}",
                "info",
            )
            futures[
                self.thread_pool.submit(
                    self.push_file,
                    device.connection,
                    local_file_path,
                    remote_file_path,
                    step_idx=self.thread_local.step_idx,
                )
            ] = node_id

        for future in as_completed(futures.keys(), timeout=self.scp_timeout):
            result = future.result()
            node_id = futures[future]
            if result:
                self.log_to_ctf(f"Node {node_id} finished copying files", "info")
            else:
                raise DeviceCmdError(f"Failed to copy files to node {node_id}")

    @classmethod
    def merge_dict(cls, a: Dict, b: Dict) -> None:
        """Recursively merge dictionary 'b' into 'a' in-place."""
        for k in b.keys():
            if k in a and isinstance(a[k], dict) and isinstance(b[k], Mapping):
                cls.merge_dict(a[k], b[k])
            else:
                a[k] = b[k]

    @classmethod
    def merge_dict_of_lists(cls, a: Dict[Any, List], b: Dict[Any, List]) -> None:
        """merge List values of dictionary 'b' into 'a' in-place with unique records"""
        for k, v in b.items():
            if k in a:
                a[k].extend(v)
                a[k] = list(set(a[k]))
            else:
                a[k] = v

    def _load_nodes_data(self, nodes_data_file: str) -> Dict:
        """Load a node data file from disk and merge overrides on top."""
        # Load node data JSON
        nodes_data: Dict = {}
        if nodes_data_file:
            with open(nodes_data_file) as f:
                logger.info(f"Loading node data: {nodes_data_file}")
                nodes_data = json.load(f)
        else:
            self.log_to_ctf("No node data file provided")

        device_count = max(len(nodes_data), len(self.device_info))

        # Convert string node_ids into integers (JSON only allows string keys)
        nodes_data = {int(key): value for key, value in nodes_data.items()}

        # Merge overrides
        self.merge_dict(nodes_data, self.nodes_data_amend(device_count))

        # Merge any config overrides from test_args
        self.nodes_data_amend_test_args(nodes_data, device_count)

        logger.debug(f"Using node data ({device_count} devices): {nodes_data}")
        return nodes_data

    def read_nodes_data(self, path, required: bool = True) -> Any:
        """Read a value from `self.nodes_data` given a key path.

        If a null value is encountered, raises DeviceConfigError if `required`
        is True, otherwise returns None.
        """
        d = self.nodes_data
        for k in path:
            if k not in d:
                if required:
                    path_str = ".".join(str(x) for x in path)
                    raise DeviceConfigError(
                        f"Required fields are missing from node data: '{path_str}'"
                    )
                else:
                    return None
            d = d[k]
        return d

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        """Get test/setup specific amendments to merge into `self.nodes_data`.
        The amendments have identical structure to `self.nodes_data`
        """
        return {}

    def nodes_data_amend_test_args(self, nodes_data: Dict, num_nodes: int) -> Dict:
        """Get amendments to nodes_data from test_args."""
        return nodes_data

    @contextmanager
    def _test_manager(self):
        """
        Function for intiation and cleanup of test-specific resources
        Sets up a file logging handler so that all logger logs can be accessed at the end of the test run.
        Calls the save_total_logs after test execution is complete

        Clears the thread_local vattribute for the next test execution.
        """
        with TemporaryDirectory(prefix="ctf_") as templog_dir:
            self.templog_path = path.join(templog_dir, TOTAL_LOGS_FILE_NAME)
            # Add a file handler to the root logger pointing to the templog_path we just created
            root_logger = logging.getLogger()
            file_handler = self._get_log_file_handler(self.templog_path)
            root_logger.addHandler(file_handler)
            # yield the contextmanager
            yield templog_dir
            # will be called on context manager's __exit__
            self.save_total_logs()
            # remove the handler so the next test run (in the event of a test suite) will only use its new handler
            root_logger.removeHandler(file_handler)
            # NamedTemporaryFile's exit is called now and the log file is deleted

        # All steps (in all threads) are done - set class ThreadLocal variable 'initialized' to False.
        # This is mostly important for TestSuites where the next test iteration will make use
        # of the class variable and will expect it to not be intialized yet
        self.thread_local.clear()

    def save_total_logs(self):
        """Save the logger output from the test's duration"""
        return self.ctf_api.save_total_logs_file(
            source_file_path=self.templog_path,
            constructive_path=TOTAL_LOGS_DIR_NAME,
            test_exe_id=self.test_exe_id,
        )

    def _get_log_file_handler(self, log_file_path):
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)"
            )
        )
        return file_handler


class CtfHelpers:
    """CTF API wrappers."""

    def __init__(self, args: Namespace) -> None:
        # CTF run mode flag. Running in serverless mode or CTF server APIs
        self.serverless = (
            False if not args.serverless else bool(strtobool(args.serverless))
        )
        logger.info(f"Running in serverless mode = {self.serverless}")

        # Run with or without ctf server
        self.ctf_api = get_ctf_api(serverless=self.serverless)

        # Configure serverless variables
        if self.serverless:
            self.ctf_api.set_serverless_config()

    def list_test_setups(self, team_id: int) -> List[Any]:
        return cast(List[Any], self.ctf_api.get_list_of_user_team_test_setups(team_id))

    def force_free_test_setup(self, test_setup_id: int) -> bool:
        if self.ctf_api.check_if_test_setup_is_free(test_setup_id):
            return True
        else:
            return bool(self.ctf_api.set_test_setup_and_devices_free(test_setup_id))


if __name__ == "__main__":
    logger.error("Do not run directly")
