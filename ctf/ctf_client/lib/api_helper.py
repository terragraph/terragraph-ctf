# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import requests
from ctf.common import constants as common_constants
from ctf.common.enums import ResponseCode, TestSetupStatusEnum

# NOTE: Terragraph is importing get_ssh_connection_class and create_ssh_connection from api_helper.py hence maintaining it here
from ctf.ctf_client.lib.connections_helper import (  # noqa
    create_ssh_connection,
    get_devices_and_connections,
    get_ssh_connection_class,
)
from ctf.ctf_client.lib.exceptions import LoginException, SaveLogException
from docstring_parser import parse
from prettytable import PrettyTable


class UTFApis(object):
    def __init__(self, api_server_url=None, file_server_url=None):
        super().__init__()
        self.user_details = None
        self.token = os.environ.get(common_constants.CTF_WORKER_AUTH_TOKEN)
        self.api_server_url = (
            api_server_url
            if api_server_url
            else os.environ.get(common_constants.CTF_API_SERVER_URL)
        )
        self.file_server_url = (
            file_server_url
            if file_server_url
            else os.environ.get(common_constants.CTF_FILE_SERVER_URL)
        )

    # Create request header with authorization token
    def set_authorization_header(self):
        """
        Function called to set the authorization header(s) when calling a api.
        :return: returns the authorization header.
        """
        header = None
        if self.token:
            header = {
                "Authorization": "Token " + self.token,
                "Content-Type": "application/json",
            }
        return header

    def attempt_login(self, user, password):
        login_url = self.api_server_url + "web_server_api/user/login/"
        # Build request data
        data = {"username": user, "password": password}
        response = requests.post(login_url, data=data)
        if response.status_code == 200:
            response_data = response.json()
            if (
                "error" in response_data
                and response_data["error"] == 0
                and "data" in response_data
                and "token" in response_data["data"]
            ):
                # Get data and get the token
                self.user_details = response_data["data"]
                self.token = response_data["data"]["token"]
                return True
            else:
                if "message" in response_data["message"]:
                    raise LoginException(response_data["message"])
                else:
                    raise LoginException()
        else:
            raise LoginException(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

    def sso_login(self, user, password):
        ctf_client_id = os.environ.get("OIDC_RP_CLIENT_ID", None)
        ctf_client_secret = os.environ.get("OIDC_RP_CLIENT_SECRET", None)

        if ctf_client_id and ctf_client_secret:
            url = self.api_server_url + "web_server_api/user/client_ssologin/"

            data = {
                "username": user,
                "password": password,
                "ctf_client_id": ctf_client_id,
                "ctf_client_secret": ctf_client_secret,
            }

            response = requests.post(url=url, json=data)

            if response.status_code == 200:
                response_data = response.json()
                self.user_details = response_data["data"]
                self.token = response_data["data"]["token"]
                return True

        return False

    def read_credentials_and_login(self):
        """
        Function called to read credentials of user from a locally stored
        file and login a user.
        :return: None.
        """
        json_format = json.dumps(
            {
                "user": "your_ctf_username",
                "pwd": "your ctf password",
                "api_server_url": "CTF api server URL",
                "file_server_url": "CTF api server URL",
            }
        )

        error_msg = (
            "Credentials are none, please make sure you have "
            + "~/.ctf_config file in for your user. It has your user "
            + "credentials in json format like "
            + json_format
            + " or you have set the following environment variables: "
            + "CTF_USER, CTF_PASSWORD, CTF_API_SERVER_URL, CTF_FILE_SERVER_URL"
        )

        # File path
        file_path = os.path.join(os.path.expanduser("~"), ".ctf_config")
        user = None
        password = None

        # Open the file and read the json
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
                credentials = json.loads(content)
                if (
                    credentials.get("api_server_url")
                    and credentials.get("file_server_url")
                    and credentials.get("user")
                    and credentials.get("pwd")
                ):
                    self.api_server_url = credentials["api_server_url"]
                    self.file_server_url = credentials["file_server_url"]
                    user = credentials["user"]
                    password = credentials["pwd"]
                    try:
                        if self.sso_login(user, password) or self.attempt_login(
                            user, password
                        ):
                            return True
                    except LoginException:
                        pass

        if (
            os.environ.get("CTF_USER")
            and os.environ.get("CTF_PASSWORD")
            and os.environ.get("CTF_API_SERVER_URL")
            and os.environ.get("CTF_FILE_SERVER_URL")
        ):
            self.api_server_url = os.environ.get("CTF_API_SERVER_URL")
            self.file_server_url = os.environ.get("CTF_FILE_SERVER_URL")
            user = os.environ.get("CTF_USER")
            password = os.environ.get("CTF_PASSWORD")
            try:
                if self.sso_login(user, password) or self.attempt_login(user, password):
                    return True
            except LoginException as e:
                raise LoginException(e)
        else:
            raise LoginException(error_msg)

    def run_test(self, test_id, env) -> {}:
        """
        Function called to run a test from terminal.
        :param test_id: contains test id which is to be run.
        :param env: contains arguments required by the test.
        :return: returns the error or success message received by api to run
        a test from terminal.
        """
        return_dict = {}

        if not self.token:
            # Login
            self.read_credentials_and_login()

        # Create url
        test_url = self.api_server_url + "web_server_api/test/run_from_terminal/"
        # Create Data
        data = {"test_id": test_id, "terminal_env": env}
        response = requests.post(
            test_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def get_test_setup_devices_and_connections(self, team_id, test_setup_id) -> {}:
        """
        Function called to get the test setup device
        details and its connections.
        :param test_setup_id: contains test setup id of which the device
        details and connection needs to get.
        :return: returns the list of devices added into the given test setup
        along with their connections.
        """
        return_dict = None
        if not self.token:
            self.read_credentials_and_login()

        # Create url
        url = "web_server_api/test_setup/get_device_connection_details/"
        test_url = self.api_server_url + url
        # Create Data
        data = json.dumps({"test_setup_id": test_setup_id, "team_id": team_id})
        response = requests.post(
            test_url, data=data, headers=self.set_authorization_header()
        )

        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        result_dict = return_dict["data"]

        return get_devices_and_connections(result_dict)

    def schedule_test(self, test_id, execution_date, repeat_interval) -> {}:
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
        return_dict = {}

        if not self.token:
            # Login
            self.read_credentials_and_login()

        # Create url
        api_url = "web_server_api/scheduled/schedule_test_from_terminal/"
        test_url = self.api_server_url + api_url

        # Create Data
        data = {
            "test_id": test_id,
            "execution_date": str(execution_date),
            "repeat_interval": repeat_interval,
        }

        response = requests.post(
            test_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def schedule_test_suite(self, test_suite_id, execution_date, repeat_interval) -> {}:
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
        return_dict = {}

        if not self.token:
            # Login
            self.read_credentials_and_login()

        # Create url
        api_url = "web_server_api/scheduled/schedule_test_suite_from_terminal/"
        test_url = self.api_server_url + api_url
        # Create Data
        data = {
            "test_suite_id": test_suite_id,
            "execution_date": str(execution_date),
            "repeat_interval": repeat_interval,
        }
        response = requests.post(
            test_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    # check is busy/free, set busy, set free
    def check_if_test_setup_is_free(self, team_id, test_setup_id) -> bool:
        """
        Function called from terminal to check if a given test setup id free or
        busy.
        :param test_setup_id: contains test setup id which is to be checked
        as free or busy.
        :return: returns a boolean response as True if given test setup is
        free else return False.
        """
        is_free = False

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        api_url = "web_server_api/test_setup/check_if_test_setup_is_free_from_terminal/"
        test_url = self.api_server_url + api_url
        # Create Data
        data = {"test_setup_id": test_setup_id, "team_id": team_id}
        response = requests.post(
            test_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
            if return_dict["data"]:
                test_setup_data = return_dict["data"]
                if test_setup_data["status"] == 0:
                    is_free = True
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return is_free

    def set_test_setup_and_devices_busy(self, team_id, test_setup_id) -> bool:
        """
        Function called to set test setup and the devices included into it as
        busy.
        :param test_setup_id: contains test setup id which needs to be set to
        busy along with the devices included into the same test setup id.
        :return: returns response in boolean as True if the given test setup
        is set as busy else returns False.
        """
        is_busy = False

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        api_url = "web_server_api/test_setup/set_test_setup_busy_from_terminal/"
        test_url = self.api_server_url + api_url + str(test_setup_id) + "/"
        # Create Data
        data = json.dumps({"team_id": team_id})
        response = requests.post(
            test_url, data=data, headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
            if "error" in return_dict and return_dict["error"] != ResponseCode.SUCCESS:
                msg = return_dict["message"] if "message" in return_dict else ""
                raise Exception(msg)
            else:
                if "data" in return_dict:
                    test_setup_data = return_dict["data"]
                    if (
                        "status" in test_setup_data
                        and test_setup_data["status"] != TestSetupStatusEnum.IDLE
                    ):
                        is_busy = True

        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return is_busy

    def set_test_setup_and_devices_free(self, team_id, test_setup_id) -> bool:
        """
        Function called to set test setup and its devices as free.
        :param test_setup_id: contains test setup id which needs to be set as
        free along with the devices included into the same test setup.
        :return: returns the response in boolean as True if test setup and
        it's devices are set as free else returns False.
        """
        is_free = True

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        api_url = "web_server_api/test_setup/set_test_setup_free_from_terminal/"
        test_url = self.api_server_url + api_url + str(test_setup_id) + "/"
        # Create Data
        data = json.dumps({"team_id": team_id})
        response = requests.post(
            test_url, data=data, headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
            if return_dict["data"]:
                test_setup_data = return_dict["data"]
                if test_setup_data["is_free"] is False:
                    is_free = False
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return is_free

    def create_test_result(
        self, name, identifier, team_id, description="", test_setup=None
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
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        test_run_result_url = (
            "web_server_api/test_run_result" "/create_test_run_result_from_terminal/"
        )
        api_url = self.api_server_url + test_run_result_url
        data = {
            "name": name,
            "identifier": identifier,
            "description": description,
            "team_id": team_id,
            "test_setup": test_setup,
        }

        response = requests.post(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def save_action_result(
        self,
        test_run_id,
        description,
        outcome,
        logs,
        start_time,
        end_time,
        parent_action_id,
        tags,
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
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        run_idx = os.environ.get("RUN_INDEX", 0)

        # Create url
        test_run_result_url = (
            "web_server_api/test_run_result" "/save_test_action_result_from_terminal/"
        )
        api_url = self.api_server_url + test_run_result_url
        data = {
            "run_execution": test_run_id,
            "description": description,
            "outcome": outcome,
            "logs": logs,
            "start_time": str(start_time),
            "end_time": str(end_time),
            "parent_action": parent_action_id,
            "tags": tags,
            "run_index": run_idx,
        }

        response = requests.post(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def save_action_result_json_data(self, test_action_result_id, ctf_json_data_all):
        """
        Function called to save action result data for test run from terminal.
        :param test_action_result_id: test action result id for which the data comes from.
        :param data_source: contains the title of the data source that the data is associated with.
        :param data_list: contains the json list of key value pairs.
        :return: returns response with error or success message that whether
        the action results are successfully saved or not.
        """
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        ctf_json_data = json.loads(ctf_json_data_all)
        if "ctf_data" in ctf_json_data.keys():
            # Create url
            result_text_data_url = (
                "web_server_api/test_run_result" "/save_test_action_result_json_data/"
            )
            api_url = self.api_server_url + result_text_data_url
            data = {
                "test_action_result": test_action_result_id,
                "ctf_json_data_all": ctf_json_data_all,
            }
            response = requests.post(
                api_url, data=json.dumps(data), headers=self.set_authorization_header()
            )
            if response.status_code == 200:
                return_dict = response.json()
            else:
                raise Exception(
                    f"Invalid response: {response.text} status: {response.status_code}"
                )
        else:
            raise Exception(
                "ERROR: ctf_data needs to be specified in a ctf_json_data request"
            )

        return return_dict

    def save_test_action_result_keyed_json_object(
        self,
        test_exec_id: int,
        test_action_result_id: int,
        key: str,
        json_object: Dict[str, Any],
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

        if not self.token:
            self.read_credentials_and_login()

        api_url = f"{self.api_server_url}web_server_api/test_action_result_keyed_json_objects/"

        data = {
            "test_run_execution_id": test_exec_id,
            "test_action_result_id": test_action_result_id,
            "key": key,
            "json_object": json.dumps(json_object),
        }

        response = requests.post(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )

        if response.status_code == 200:
            response = response.json()["data"]
            response["json_object"] = json.loads(response["json_object"])
            return response
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

    def get_test_action_result_keyed_json_object(self, key: str, team_id: int):
        """
        Function called to Get action result keyed object.
        :param key: The unique identifier for this json object.
        :return: returns response with error or TestActionResultKeyedJsonObject.
        """

        if not self.token:
            self.read_credentials_and_login()

        api_url = f"{self.api_server_url}web_server_api/test_action_result_keyed_json_objects/{key}/teams/{team_id}"
        response = requests.get(
            api_url,
            headers=self.set_authorization_header(),
        )

        if response.status_code == 200:
            response = response.json()["data"]
            response["json_object"] = json.loads(response["json_object"])
            return response
        else:
            # TODO: T131449112 We could throw specific custom exceptions, such as ResourceNotFoundException when code is 404
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

    def list_keyed_json_object_for_test_action_result(
        self,
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

        if not self.token:
            self.read_credentials_and_login()

        query_parameters = {"page": page, "offset": offset}
        api_url = f"{self.api_server_url}web_server_api/test_run_result/{test_exec_id}/test_action_results/{test_action_result_id}/test_action_result_keyed_json_objects"

        response = requests.get(
            api_url, headers=self.set_authorization_header(), params=query_parameters
        )

        if response.status_code == 200:
            json_objects = []
            response_data = response.json()["data"]
            for keyed_json_object in response.json()["data"]["json_objects"]:
                keyed_json_object["json_object"] = json.loads(
                    keyed_json_object["json_object"]
                )
                json_objects.append(keyed_json_object)
            response_data["json_objects"] = json_objects
            return response_data
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

    def list_keyed_json_object_for_test_run_execution(
        self,
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

        if not self.token:
            self.read_credentials_and_login()

        query_parameters = {"page": page, "offset": offset}
        api_url = f"{self.api_server_url}web_server_api/test_run_result/{test_exec_id}/test_action_result_keyed_json_objects"

        response = requests.get(
            api_url, headers=self.set_authorization_header(), params=query_parameters
        )

        if response.status_code == 200:
            json_objects = []
            response_data = response.json()["data"]
            for keyed_json_object in response.json()["data"]["json_objects"]:
                keyed_json_object["json_object"] = json.loads(
                    keyed_json_object["json_object"]
                )
                json_objects.append(keyed_json_object)
            response_data["json_objects"] = json_objects
            return response_data
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

    def delete_test_action_result_keyed_json_object(self, key: str, team_id: int):
        """
        Function called to DELETE action result keyed object.
        :param test_action_result_id: test action result id for which the js object comes from.
        :param key: The unique identifier for this json object.
        :return: returns response with error or success message that whether
        the action json object is successfully deleted or not.
        """

        if not self.token:
            self.read_credentials_and_login()

        api_url = f"{self.api_server_url}web_server_api/test_action_result_keyed_json_objects/{key}/teams/{team_id}"

        response = requests.delete(api_url, headers=self.set_authorization_header())

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

    def save_heatmap_files(
        self,
        test_exe_id,
        test_action_result_id,
        initiator_file_path,
        responder_file_path,
        description="Heatmap",
    ):
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        with open(initiator_file_path, "rb") as initiator_file, open(
            responder_file_path, "rb"
        ) as responder_file:
            write_heatmap_url = "file_server_api/heatmap/write_heatmap_files/"
            api_url = self.file_server_url + write_heatmap_url
            data = {
                "description": description,
                "test_action_result_id": test_action_result_id,
                "test_execution_id": test_exe_id,
            }

            log_file_dict = {
                "initiator_file": initiator_file,
                "responder_file": responder_file,
            }
            response = requests.post(
                api_url, data=data, files=log_file_dict, verify=False
            )
            if response.status_code == 200:
                return_dict = response.json()
            else:
                raise SaveLogException(
                    f"Invalid response: {response.text} status: {response.status_code}"
                )

        return return_dict

    def save_action_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        test_action_result_id,
        data_processing_config_key: str = None,
    ):
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        with open(source_file_path, "rb") as source:
            write_log_url = "file_server_api/logs/write_log_file/"
            api_url = self.file_server_url + write_log_url
            data = {
                "test_execution_id": test_exe_id,
                "test_action_result_id": test_action_result_id,
                "constructive_path": constructive_path,
                "data_processing_config_key": data_processing_config_key,
            }

            log_file_dict = {"log_file": source}
            response = requests.post(
                api_url, data=data, files=log_file_dict, verify=False
            )
            if response.status_code == 200:
                return_dict = response.json()
            else:
                raise SaveLogException(
                    f"Invalid response: {response.text} status: {response.status_code}"
                )

        return return_dict

    def save_log_file(
        self,
        source_file_path,
        constructive_path,
        test_exe_id,
        log_type: int = None,
        data_processing_config_key: str = None,
    ):
        # using ctf/api_server/core/file_server/api_manager.py as an example
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()
        try:
            with open(source_file_path, "rb") as source:
                write_log_url = "file_server_api/logs/write_log_file/"
                api_url = self.file_server_url + write_log_url
                data = {
                    "test_execution_id": test_exe_id,
                    "constructive_path": constructive_path,
                    "log_type": log_type,
                    "data_processing_config_key": data_processing_config_key,
                }

                log_file_dict = {"log_file": source}
                response = requests.post(
                    api_url, data=data, files=log_file_dict, verify=False
                )
                if response.status_code == 200:
                    return_dict = response.json()
                else:
                    raise SaveLogException(
                        f"Invalid response: {response.text} status: {response.status_code}"
                    )
        except SaveLogException as e:
            raise SaveLogException(str(e))

        return return_dict

    def save_test_result_outcome(
        self,
        test_run_id: int,
        dashboard_details: List[Dict] = None,
        test_result_summary: List[Dict] = None,
    ) -> Dict:
        """
        Function called to save outcome of a test result from terminal.
        :param test_run_id: test run id for which the outcome needs to be saved.
        :return: returns the response with error or success message that
        whether the test result outcome is successfully saved or not.
        """
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        test_run_result_url = (
            "web_server_api/test_run_result" "/save_test_run_outcome_from_terminal/"
        )
        api_url = self.api_server_url + test_run_result_url
        data = {
            "test_run_id": test_run_id,
            "dashboard_details": json.dumps(dashboard_details),
            "test_result_summary": json.dumps(test_result_summary),
        }
        response = requests.post(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def get_list_of_user_teams(self):
        """
        Function called to get the list of logged in user.
        :return: returns the list of teams with their name, id and
        description of logged in user.
        """
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        test_run_result_url = "web_server_api/team" "/user_team_list/"
        api_url = self.api_server_url + test_run_result_url
        data = {}

        response = requests.get(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
            team_list_table = PrettyTable(["Team ID", "Name", "Description"])
            for team in return_dict["data"]:
                team_list_table.add_row(
                    [str(team["team_id"]), team["name"], team["description"]]
                )
            print(team_list_table)
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def get_list_of_user_team_test_setups(self, team_id):
        """
        Function called to get the list of test setup(s) within the given
        team id from terminal.
        :param team_id: contains team id of which the list of test setup(s)
        needs to get.
        :return: returns response with the list of test setup(s) available
        within given team id with their details such as test setup id, name,
        description and status.
        """
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        test_run_result_url = "web_server_api/test_setup/all/" + str(team_id)
        api_url = self.api_server_url + test_run_result_url
        data = {}

        response = requests.get(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def get_list_of_user_team_tests(self, team_id):
        """
        Function called to get the list of tests within given team.
        :param team_id: team id under which all the test(s) list needs to
        be fetched.
        :return: returns the list of all the test(s) associated with the
        given team id.
        """
        return_dict = {}

        if not self.token:
            self.read_credentials_and_login()

        # Create url
        test_run_result_url = "web_server_api/test/all/" + str(team_id)
        api_url = self.api_server_url + test_run_result_url
        data = {}

        response = requests.get(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
            print("Here is the list of tests " "within your selected team: ")
            tests_list_table = PrettyTable(
                ["ID", "Title", "Test Setup", "Run", "Owner", "Updated at"]
            )
            for tests in return_dict["data"]["test_data"]:
                dt_str_from_db = tests["updated_at"]
                just_date = datetime.strptime(
                    dt_str_from_db, "%Y-%m-%dT%H:%M:%S.%fZ"
                ).date()
                display_date = just_date.strftime("%b %d, %Y")
                tests_list_table.add_row(
                    [
                        str(tests["id"]),
                        tests["title"],
                        tests["test_setup_name"],
                        tests["repeat"],
                        tests["owner_name"],
                        display_date,
                    ]
                )
            print(tests_list_table)
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def get_list_of_user_team_test_suites(self, team_id):
        """
        Function called to get the list of test suites within given team.
        :param team_id: team id under which all the test suite(s) list needs to
        be fetched.
        :return: returns the list of all the test suite(s) associated with the
        given team id.
        """
        return_dict = {}
        if not self.token:
            self.read_credentials_and_login()

        # Create url
        test_run_result_url = "web_server_api/test_suite/list/" + str(team_id)
        api_url = self.api_server_url + test_run_result_url
        data = {}

        response = requests.get(
            api_url, data=json.dumps(data), headers=self.set_authorization_header()
        )

        if response.status_code == 200:
            return_dict = response.json()
            print("Here is the list of test suites " + "within your selected team: ")
            test_suite_list_table = PrettyTable(["Test Suite#", "Test Suite Name"])

            for suite in return_dict["data"]["test_suite_data"]:
                test_suite_list_table.add_row([str(suite["id"]), suite["title"]])

            print(test_suite_list_table)
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict

    def get_help_for_all_function(self, functions_dict):
        """
        Function called from terminal to get the manual/help page of all the
        function added in helper function.
        :param functions_dict: contains the doc strings and name of the
        functions from helper functions.
        :return: returns the manual/documentation for all the functions added
        in helper function class.
        """
        PURPLE = "\033[95m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        BOLD = "\033[1m"
        END = "\033[0m"
        EOL = "\n"
        # DARKCYAN = '\033[36m'
        # BLUE = '\033[94m'
        # UNDERLINE = '\033[4m'
        # YELLOW = '\033[93m'
        # RED = '\033[91m'

        if not self.token:
            self.read_credentials_and_login()

        if functions_dict:
            print(BOLD + PURPLE + "Helper Function API doc" + END + EOL)
            for data in functions_dict:
                doc_value = parse(data.__doc__)
                function_desc = doc_value.short_description + (
                    " " + doc_value.long_description
                    if doc_value.long_description
                    else ""
                )
                print(BOLD + GREEN + "FUNCTION NAME" + END)
                print(
                    "\t"
                    + BOLD
                    + CYAN
                    + data.__name__
                    + END
                    + " - "
                    + function_desc
                    + EOL
                )
                print(BOLD + GREEN + "PARAMETERS" + END)
                for param in doc_value.params:
                    print(
                        "\t"
                        + BOLD
                        + CYAN
                        + "("
                        + param.type_name
                        + ")"
                        + param.arg_name
                        + END
                        + " - "
                        + param.description.replace("\n", " ")
                    )
                print(EOL + BOLD + GREEN + "FUNCTION RESPONSE" + END)
                print("\t" + doc_value.returns.description.replace("\n", " ") + EOL)
                print(
                    "------------------------------------------------"
                    "++++++++++"
                    + "------------------------------------------------"
                    + EOL
                )

    def run_test_suite(self, test_suite_id):
        """
        Function called to run a test suite from terminal.
        :param test_suite_id: contains test suite id which needs to be run.
        :return: returns response with error or success message that whether
        test suite is successfully run from terminal or not.
        """
        return_dict = {}

        if not self.token:
            # Login
            self.read_credentials_and_login()

        # Create url
        test_url = (
            self.api_server_url
            + "web_server_api/test_suite/run_test_suite_from_terminal/"
        )
        # Create Data
        data = {"test_suite_id": test_suite_id}
        response = requests.post(
            test_url, data=json.dumps(data), headers=self.set_authorization_header()
        )
        if response.status_code == 200:
            return_dict = response.json()
        else:
            raise Exception(
                f"Invalid response: {response.text} status: {response.status_code}"
            )

        return return_dict
