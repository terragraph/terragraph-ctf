# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging

import docker
import requests
from ctf.common.enums import DeviceTypeEnum
from ctf.ctf_client.tests import testing_fixtures

HTTP_RESPONSE_STATUS_OK = 200
APISERVER_URL_DOCKER = "http://apiserver.ctf:8000"
FILESERVER_URL_DOCKER = "http://fileserver.ctf:8001"
UI_URL_DOCKER = "http://ui.ctf:4200"
FILESERVER_PREF_S3 = "Third Party"
FILESERVER_PREF_DISK = "File Disk"
DEVICE_USERNAME = "root"
DEVICE_PASSWORD = "root"
DEVICE_SSH_PORT = 22
DEVICE_CONNECTION_TYPE = 100
CTF_TEAM = "CTF_TEST"

API_DATA = "data"
API_ERROR = "error"
API_MESSAGE = "message"
API_TEAM_DATA = "team_data"
API_ID = "id"
API_USER_ID = "user_id"
API_DEVICE_ID = "device_id"
API_DEVICE_DATA = "device_data"
API_TEST_SETUP_DEVICE_MAPPING = "test_setup_device_mapping"


logger = logging.getLogger(__name__)


class ApiUtilsException(Exception):
    # exception class for errors
    pass


class ApiUtils:
    def __init__(self, apiserver, fileserver):
        self.apiserver = apiserver
        self.fileserver = fileserver
        self.apiserver_url = apiserver + "web_server_api/"
        self.fileserver_url = fileserver + "file_server_api/"
        self.admin_user = testing_fixtures.TEST_PARAMS["CTF_BUCK_USER"]
        self.admin_password = testing_fixtures.TEST_PARAMS["CTF_BUCK_PASSWORD"]
        self.admin_token = None
        self.admin_user_id = None
        self.admin_user_name = "Admin ctf"
        self.setup_mircoservice_urls()
        self.docker_client = docker.from_env()

    def _login_admin(self):
        self.admin_token, self.admin_user_id = self.login(
            self.admin_user, self.admin_password
        )

    def _logout_admin(self):
        self.logout(self.admin_token)
        self.admin_token = None
        self.admin_user_id = None

    def _set_authorization_header(self):
        if self.admin_token is None or self.admin_user_id is None:
            self._login_admin()

        return self.set_authorization_header(self.admin_token)

    def _validate_response(self, response):
        if response.status_code == HTTP_RESPONSE_STATUS_OK:
            response_data = response.json()
            error_message = ""

            if API_ERROR in response_data and response_data[API_ERROR] != 0:
                if API_MESSAGE in response_data:
                    error_message = response_data[API_MESSAGE]
                raise ApiUtilsException(
                    str(response_data[API_ERROR]) + ": " + error_message
                )
        else:
            raise ApiUtilsException(
                "Invalid response code: "
                + str(response.status_code)
                + ", "
                + response.text
            )

    def set_authorization_header(self, token):
        header = {
            "Authorization": "Token " + token,
            "Content-Type": "application/json",
        }
        return header

    def setup_mircoservice_urls(self):
        sys_pref_url = self.apiserver_url + "system_pref/update/"

        data_apiserver = {
            "key": "api_server_host_url",
            "value": APISERVER_URL_DOCKER,
            "old_key": "api_server_host_url",
        }

        data_fileserver = {
            "key": "file_server_host_url",
            "value": FILESERVER_URL_DOCKER,
            "old_key": "file_server_host_url",
        }

        data_ui = {
            "key": "web_server_host_url",
            "value": UI_URL_DOCKER,
            "old_key": "web_server_host_url",
        }

        try:
            response_api = requests.post(
                url=sys_pref_url,
                data=json.dumps(data_apiserver),
                headers=self._set_authorization_header(),
            )
            response_file = requests.post(
                url=sys_pref_url,
                data=json.dumps(data_fileserver),
                headers=self._set_authorization_header(),
            )
            response_ui = requests.post(
                url=sys_pref_url,
                data=json.dumps(data_ui),
                headers=self._set_authorization_header(),
            )

            self._validate_response(response_api)
            self._validate_response(response_file)
            self._validate_response(response_ui)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)

    def setup_fileserver_pref(self, pref=FILESERVER_PREF_S3):
        sys_pref_url = self.fileserver_url + "file_server_pref/create/"
        pref_data = {
            "key": "file_saving_mode",
            "value": {
                "saving_mode": [FILESERVER_PREF_DISK, FILESERVER_PREF_S3],
                "current_mode": pref,
            },
        }
        try:
            response = requests.post(
                url=sys_pref_url,
                data=json.dumps(pref_data),
                headers={"Content-Type": "application/json"},
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)

    def __check_if_team_present(self):
        team_list_url = self.apiserver_url + "team/list/"

        try:
            response = requests.get(
                team_list_url, headers=self._set_authorization_header()
            )
            self._validate_response(response)
            response_data = response.json()
            if (
                (API_DATA in response_data)
                and (API_TEAM_DATA in response_data[API_DATA])
                and len(response_data[API_DATA][API_TEAM_DATA]) > 0
            ):
                # return team ID of the first team
                return response_data[API_DATA][API_TEAM_DATA][0][API_ID]
            return 0
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
        return 0

    def create_team(self, name, description="", private="true", team_admin=None):
        team_url = self.apiserver_url + "team/create/"
        headers = self._set_authorization_header()

        if team_admin is None:
            team_admin = [
                {
                    API_USER_ID: self.admin_user_id,
                    "user_name": self.admin_user_name,
                }
            ]
        team_data = {
            API_ID: "null",
            "name": name,
            "avatar": None,
            "description": description,
            "is_private": private,
            "admin": json.dumps(team_admin),
        }
        try:
            response = requests.post(
                url=team_url,
                data=json.dumps(team_data),
                headers=headers,
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)

    def login(self, user, password):
        login_url = self.apiserver_url + "user/login/"
        data = {"username": user, "password": password}
        token = None
        user_id = None

        try:
            response = requests.post(url=login_url, data=data)
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
        else:
            token = response.json()[API_DATA]["token"]
            user_id = response.json()[API_DATA][API_USER_ID]

        return token, user_id

    def logout(self, token):
        logout_url = self.apiserver_url + "user/logout/"

        try:
            response = requests.get(
                url=logout_url, headers=self.set_authorization_header(token)
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)

    def create_device(
        self,
        team_id,
        name,
        fw_verison="",
        description="",
        latitude="0",
        longitude="0",
        altitude="0",
        private=True,
        timeout=60,
        prompt="",
    ):
        device_url = self.apiserver_url + "device/add_private/"
        container = None
        try:
            container = self.docker_client.containers.run(
                "gotechnies/alpine-ssh:alpine3.10",
                detach=True,
                remove=True,
                name=name,
                network="ctf_dev_ctf",
            )
            device_connections = [
                {
                    API_ID: None,
                    "username": DEVICE_USERNAME,
                    "password": DEVICE_PASSWORD,
                    "ip_address": name,
                    "port": DEVICE_SSH_PORT,
                    "timeout": timeout,
                    "prompt": prompt,
                    "connection_type": DEVICE_CONNECTION_TYPE,
                    "jump_host": None,
                },
            ]
            device_type_data = {API_DATA: None}
            device_data = {
                API_ID: None,
                "name": name,
                "firmware_version": fw_verison,
                "serial_number": container.id,
                "description": description,
                "latitude": latitude,
                "longitude": longitude,
                "height": altitude,
                "device_type": DeviceTypeEnum.GENERIC,
                "is_private": private,
                "connections": device_connections,
                "device_slots": [],
                "team_id": team_id,
                "device_type_data": device_type_data,
            }
            response = requests.post(
                url=device_url,
                data=json.dumps(device_data),
                headers=self._set_authorization_header(),
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
            self.remove_device(container, None)
            container = None

        device_id = self.get_device_id(container, team_id)
        return container, device_id

    def get_device_id(self, container, team_id):
        device_id = None
        if container:
            device_list_url = (
                self.apiserver_url
                + "device_team/team_device_list/"
                + str(team_id)
                + "/"
            )
            query_type = [
                {
                    "type": "serial_number",
                    "search": container.id,
                }
            ]

            params = {"q": json.dumps(query_type)}

            try:
                response = requests.get(
                    url=device_list_url,
                    params=params,
                    headers=self._set_authorization_header(),
                )
                self._validate_response(response)
            except (ApiUtilsException, Exception) as e:
                logger.exception(e)
            else:
                response_data = response.json()
                if (
                    API_DATA in response_data
                    and API_DEVICE_DATA in response_data[API_DATA]
                    and len(response.json()[API_DATA][API_DEVICE_DATA]) == 1
                    and API_DEVICE_ID in response_data[API_DATA][API_DEVICE_DATA][0]
                ):
                    device_id = response_data[API_DATA][API_DEVICE_DATA][0][
                        API_DEVICE_ID
                    ]
            return device_id

    # this is hacky, this function uses the existing team, if there is one
    # to run tests. If there is no team it creates one. When we have an API to delete
    # teams we will not have to do this
    def get_team_id(self):
        existing_team_id = self.__check_if_team_present()
        if existing_team_id == 0:
            self.create_team(CTF_TEAM)
            return 1
        return existing_team_id

    def remove_device(self, container, device_id):
        if container:
            try:
                container.stop()
            except docker.errors.NotFound:
                pass

        if device_id:
            delete_device_url = (
                self.apiserver_url + "device/delete/" + str(device_id) + "/"
            )
            try:
                response = requests.post(
                    url=delete_device_url,
                    headers=self._set_authorization_header(),
                )
                self._validate_response(response)
            except (ApiUtilsException, Exception) as e:
                logger.exception(e)

    def _create_testbed(self, name, team_id, description, metadata):
        create_testbed_url = self.apiserver_url + "test_setup/create/"
        testbed_id = None
        testbed_data = {
            API_ID: None,
            "name": name,
            "description": description,
            "metadata": metadata,
            "team_id": team_id,
        }

        try:
            response = requests.post(
                url=create_testbed_url,
                data=json.dumps(testbed_data),
                headers=self._set_authorization_header(),
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
        else:
            response_data = response.json()
            if API_DATA in response_data and API_ID in response_data[API_DATA]:
                testbed_id = response.json()[API_DATA][API_ID]
        return testbed_id

    def _add_device_types_to_testbed(self, team_id, testbed_id, device_count):
        add_dev_types_url = self.apiserver_url + "test_setup/add_device_types_in_setup/"

        dev_type_list = [
            {
                API_ID: DeviceTypeEnum.GENERIC,
                "count": device_count,
            }
        ]
        dev_type_data = {
            "test_setup_id": testbed_id,
            "team_id": team_id,
            "device_type_list": dev_type_list,
        }

        try:
            response = requests.post(
                url=add_dev_types_url,
                data=json.dumps(dev_type_data),
                headers=self._set_authorization_header(),
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)

    def _get_testbed_detail(self, testbed_id):
        dev_mapping_id = None
        testbed_detail_url = (
            self.apiserver_url + "test_setup/detail/" + str(testbed_id) + "/"
        )
        try:
            response = requests.get(
                url=testbed_detail_url,
                headers=self._set_authorization_header(),
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
        else:
            response_data = response.json()
            if (
                API_DATA in response_data
                and API_TEST_SETUP_DEVICE_MAPPING in response_data[API_DATA]
                and "99" in response_data[API_DATA][API_TEST_SETUP_DEVICE_MAPPING]
                and len(response_data[API_DATA][API_TEST_SETUP_DEVICE_MAPPING]["99"])
                > 0
                and API_ID
                in response_data[API_DATA][API_TEST_SETUP_DEVICE_MAPPING]["99"][0]
            ):
                dev_mapping_id = response_data[API_DATA][API_TEST_SETUP_DEVICE_MAPPING][
                    "99"
                ][0][API_ID]
        return dev_mapping_id

    def _add_devices_to_testbed(self, team_id, device_ids, mapping_id):
        add_dev_url = self.apiserver_url + "test_setup/add_device_in_test_setup/"

        for device_id in device_ids:
            device_data = {
                "test_setup_mapping_id": mapping_id,
                API_DEVICE_ID: device_id,
                "team_id": team_id,
            }
            try:
                response = requests.post(
                    url=add_dev_url,
                    data=json.dumps(device_data),
                    headers=self._set_authorization_header(),
                )
                self._validate_response(response)
            except (ApiUtilsException, Exception) as e:
                logger.exception(e)
                return False
            mapping_id = mapping_id + 1
        return True

    def create_testbed(self, name, team_id, device_ids, description="", metadata=""):
        testbed_id = self._create_testbed(name, team_id, description, metadata)
        if testbed_id is not None:
            self._add_device_types_to_testbed(team_id, testbed_id, len(device_ids))
            mapping_id = self._get_testbed_detail(testbed_id)
            if mapping_id is None or not self._add_devices_to_testbed(
                team_id, device_ids, mapping_id
            ):
                self.remove_testbed(team_id, testbed_id)
                testbed_id = None
        return testbed_id

    def remove_testbed(self, team_id, testbed_id):
        if testbed_id is not None:
            remove_testbed_url = (
                self.apiserver_url + "test_setup/delete/" + str(testbed_id) + "/"
            )
            testbed_data = {
                "team_id": team_id,
            }
            try:
                response = requests.post(
                    url=remove_testbed_url,
                    data=json.dumps(testbed_data),
                    headers=self._set_authorization_header(),
                )
                self._validate_response(response)
            except (ApiUtilsException, Exception) as e:
                logger.exception(e)

    def create_test(self, team_id, testbed_id, test_data_json_file):
        create_test_url = self.apiserver_url + "test/create/"
        test_id = None
        with open(test_data_json_file) as f:
            data = json.load(f)

        test_actions = []
        for action in data["actions"]:
            test_action = {
                "code": action["code"],
                API_DATA: action[API_DATA],
                "sequence_number": action["sequence_number"],
                "skip": action["skip"],
                "treat_failure_as_success": action["treat_failure_as_success"],
                "is_determine_test_result": action["is_determine_test_result"],
                "parent_action": 0,
                "tag": None,
                "uuid": None,
            }
            test_actions.append(test_action)

        test_data = {
            "title": data["title"],
            "repeat": data["repeat"],
            "pass_count": data["pass_count"],
            "test_id": 0,
            "description": data["description"],
            "test_setup": testbed_id,
            "insta_stop": data["insta_stop"],
            "actions": test_actions,
            "team_id": team_id,
            "meta_data": {"used_device_type": []},
        }
        logger.info(f"test_data: {test_data}")
        try:
            response = requests.post(
                url=create_test_url,
                data=json.dumps(test_data),
                headers=self._set_authorization_header(),
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
        else:
            response_data = response.json()
            if API_DATA in response_data and API_ID in response_data[API_DATA]:
                test_id = response_data[API_DATA][API_ID]
        return test_id

    def remove_test(self, team_id, test_id):
        delete_test_url = self.apiserver_url + "test/delete/" + str(test_id) + "/"
        delete_test_data = {"team_id": team_id}
        try:
            response = requests.post(
                url=delete_test_url,
                data=json.dumps(delete_test_data),
                headers=self._set_authorization_header(),
            )
            self._validate_response(response)
        except (ApiUtilsException, Exception) as e:
            logger.exception(e)
