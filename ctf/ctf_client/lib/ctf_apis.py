# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ctf.common.constants import ActionTag
from ctf.common.enums import TagLevel


class ActionTagsList:
    def __init__(self):
        self._list = []

    # appends a tag to the list of tags
    def append(self, description: str, level: TagLevel):
        self._list.append(self.__get_tag(description, level))

    # removes a tag from the list if the description is matched.
    # will remove all instances of the tag.
    def remove(self, description: str):
        self._list = [tag for tag in self._list if tag["description"] != description]

    # removes and returns the last object from the list
    def pop(self):
        return self._list.pop()

    def get_list(self):
        return self._list

    def __get_tag(self, description: str, level: TagLevel):
        return {"description": description, "level": level}


class CtfApis(ABC):
    """
    CTF API abstract base class
    """

    @abstractmethod
    def check_if_test_setup_is_free(self, test_setup_id: int, team_id: int = None):
        """
        Checks test setup status
        """
        pass

    @abstractmethod
    def set_test_setup_and_devices_busy(self, test_setup_id: int, team_id: int = None):
        """
        Set the test setup as busy
        """
        pass

    @abstractmethod
    def set_test_setup_and_devices_free(self, test_setup_id: int, team_id: int = None):
        """
        Set the test setup as free
        """
        pass

    @abstractmethod
    def get_test_setup_devices_and_connections(
        self, test_setup_id: int, team_id: int = None
    ):
        """
        Returns list of all the devices used in the given test setup and their connections objects
        """
        pass

    @abstractmethod
    def create_test_run_result(
        self,
        name: str,
        identifier: str,
        description: str,
        team_id: int = None,
        test_setup: int = None,
    ):
        """
        Create a test run result
        """
        pass

    @abstractmethod
    def save_test_action_result(
        self,
        test_run_id: int,
        description: str,
        outcome: int,
        logs: str,
        start_time: datetime.datetime.now(),
        end_time: datetime.datetime.now(),
        step_idx: int,
        tags: Union[ActionTagsList, List[ActionTag], List[str], None] = None,
    ):
        """
        Save Test action result against the given test_run_id and return the test action result details
        """
        pass

    @abstractmethod
    def save_test_action_result_json_data(
        self,
        test_action_result_id: int,
        ctf_json_data_all: str,
    ):
        """
        Save json data against the given test_action_result_id
        """
        pass

    @abstractmethod
    def save_action_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        test_action_result_id,
        data_processing_config_key: str = None,
    ):
        """
        Saves the action log against the given test_action_result_id
        """
        pass

    @abstractmethod
    def save_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        log_type: int = None,
        data_processing_config_key: str = None,
    ):
        """
        Saves the log file against the given test_exe_id
        """
        pass

    @abstractmethod
    def save_total_logs_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        data_processing_config_key: str = None,
    ):
        """
        Saves the total log file against the given test_exe_id
        """
        pass

    @abstractmethod
    def save_test_run_outcome(
        self,
        test_run_id: int,
        dashboard_details: List[Dict] = None,
        test_result_summary: List[Dict] = None,
    ):
        """
        Saves the final test status and add the test result summary to test_run_id
        """
        pass

    @abstractmethod
    def get_list_of_user_team_test_setups(self, team_id: int):
        """
        Fetch the list of test setups for given team_id
        """
        pass

    @abstractmethod
    def save_test_action_result_keyed_json_object(
        self,
        test_exec_id: Union[str, int],
        test_action_result_id: Union[str, int],
        key: str,
        json_object: Dict[str, Optional[Any]],
        *args,
        **kwargs,
    ):
        pass

    @abstractmethod
    def get_test_action_result_keyed_json_object(self, key: str, team_id: int):
        pass

    @abstractmethod
    def delete_test_action_result_keyed_json_object(self, key: str, team_id: int):
        pass

    @abstractmethod
    def save_heatmap_files(
        self,
        test_exe_id,
        test_action_result_id,
        initiator_file_path,
        responder_file_path,
        description="Heatmap",
    ):
        pass
