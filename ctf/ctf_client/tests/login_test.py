# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
    isort:skip_file
"""
import json
import logging
import os
import socket
import sys

import pytest

sys.path.append("../../../")

from ctf.ctf_client.lib.api_helper import LoginException
from ctf.ctf_client.tests.test_utils import TestUtils as Utils
from requests.exceptions import MissingSchema

logger = logging.getLogger(__name__)

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

pytestmark = pytest.mark.skipif(
    CTF_INTERNAL is True, reason="Disabling tests as they currently hit Production."
)


@pytest.mark.usefixtures("client_api", "test_api_utils")
class TestCTFClientApiLogin:
    @pytest.fixture(autouse=True)
    def test_fixture(self, client_api, test_api_utils):
        self.api = client_api
        self.test_api_utils = test_api_utils
        self.utils = Utils(test_api_utils.apiserver, test_api_utils.fileserver)
        self.utils.remove_envar_params()
        self.__load_valid_credentials()
        os.system(
            "if [ -f ~/.ctf_config ]; then mv ~/.ctf_config ~/.ctf_config.bak; fi"
        )

        yield
        self.utils.after_test_run()

    def __load_valid_credentials(self):
        self.user = self.utils.get_param("CTF_BUCK_USER")
        self.password = self.utils.get_param("CTF_BUCK_PASSWORD")
        self.api_server_url = self.utils.get_param("CTF_API_SERVER_URL")
        self.file_server_url = self.utils.get_param("CTF_FILE_SERVER_URL")

    def __load_valid_envar_params(self):
        os.environ["CTF_USER"] = self.user
        os.environ["CTF_PASSWORD"] = self.password
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url
        os.environ["CTF_FILE_SERVER_URL"] = self.file_server_url

    def __load_system_config(self, json_format):
        json_str = "'" + str(json_format) + "'"
        os.system("echo %s > ~/.ctf_config" % json_str)

    def __load_config_without_file_server_url(self):
        json_format = json.dumps(
            {
                "user": self.user,
                "pwd": self.password,
                "api_server_url": self.api_server_url,
            }
        )
        self.__load_system_config(json_format)

    def __load_config_invalid_api_server_url_param(self):
        json_format = json.dumps(
            {
                "user": self.user,
                "pwd": self.password,
                "WRONG_SERVER_URL_PARAM": self.api_server_url,
                "file_server_url": self.file_server_url,
            }
        )
        self.__load_system_config(json_format)

    def __load_config_invalid_user_value(self):
        json_format = json.dumps(
            {
                "user": "WRONG_USER",
                "pwd": self.password,
                "api_server_url": self.api_server_url,
                "file_server_url": self.file_server_url,
            }
        )
        self.__load_system_config(json_format)

    def __load_config_invalid_api_server_url_value(self):
        json_format = json.dumps(
            {
                "user": self.user,
                "pwd": self.password,
                "api_server_url": "http://WRONG_API_SERVER_URL/",
                "file_server_url": self.file_server_url,
            }
        )
        self.__load_system_config(json_format)

    def __load_config_invalid_api_server_url_schema(self):
        json_format = json.dumps(
            {
                "user": self.user,
                "pwd": self.password,
                "api_server_url": "WRONG_API_SERVER_URL_SCHEMA",
                "file_server_url": self.file_server_url,
            }
        )
        self.__load_system_config(json_format)

    def test_good_config_noenvar_login(self) -> None:
        logger.info("\n------------test_good_config_noenvar_login-------------")
        logger.info(
            f"user: {self.user}, pwd: {self.password}, api_server_url: {self.api_server_url}, file_server_url: {self.file_server_url}"
        )
        json_format = json.dumps(
            {
                "user": self.user,
                "pwd": self.password,
                "api_server_url": self.api_server_url,
                "file_server_url": self.file_server_url,
            }
        )
        self.__load_system_config(json_format)
        assert self.api.read_credentials_and_login() is True

    def test_no_fileserver_config_noenvar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_noenvar_login-------------"
        )
        self.__load_config_without_file_server_url()
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_no_fileserver_config_good_envar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_good_envar_login-------------"
        )
        self.__load_config_without_file_server_url()
        self.__load_valid_envar_params()
        assert self.api.read_credentials_and_login() is True

    def test_no_fileserver_config_bad_url_schema_envar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_bad_url_schema_envar_login-------------"
        )
        self.__load_config_without_file_server_url()
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = "WRONG_API_SERVER_URL_SCHEMA"
        with pytest.raises(MissingSchema):
            self.api.read_credentials_and_login()

    def test_no_fileserver_config_bad_url_envar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_bad_url_envar_login-------------"
        )
        self.__load_config_without_file_server_url()
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url + "WRONG_API_SERVER_URL"
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_no_fileserver_config_invalid_url_envar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_invalid_url_envar_login-------------"
        )
        self.__load_config_without_file_server_url()
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = "http://WRONG_API_SERVER_URL/"
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_no_fileserver_config_bad_creds_envar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_bad_creds_envar_login-------------"
        )
        self.__load_config_without_file_server_url()
        self.__load_valid_envar_params()
        os.environ["CTF_USER"] = "WRONG_USER"
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_no_fileserver_config_no_fileserver_envar_login(self) -> None:
        logger.info(
            "\n------------test_no_fileserver_config_no_fileserver_envar_login-------------"
        )
        self.__load_config_without_file_server_url()
        os.environ["CTF_USER"] = self.user
        os.environ["CTF_PASSWORD"] = self.password
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_format_config_noenvar_login(self) -> None:
        logger.info("\n------------test_bad_format_config_noenvar_login-------------")
        self.__load_config_invalid_api_server_url_param()
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_format_config_good_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_format_config_good_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_param()
        self.__load_valid_envar_params()
        assert self.api.read_credentials_and_login() is True

    def test_bad_format_config_bad_url_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_format_config_bad_url_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_param()
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = (
            self.api_server_url + "intentionally_incorrect_url_for_unit_test"
        )
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_format_config_bad_creds_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_format_config_bad_creds_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_param()
        self.__load_valid_envar_params()
        os.environ["CTF_USER"] = "WRONG_USER"
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_format_config_no_fileserver_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_format_config_no_fileserver_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_param()
        os.environ["CTF_USER"] = self.user
        os.environ["CTF_PASSWORD"] = self.password
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    # This test must eventually change in order to expect a LoginExcetion
    # instead a Socket.error.
    # We must file an implementation change in order to reflict the
    # LoginExcetion scenario.
    def test_bad_url_config_value_noenvar_login(self) -> None:
        logger.info(
            "\n------------test_bad_url_config_value_noenvar_login-------------"
        )
        self.__load_config_invalid_api_server_url_value()
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_url_config_value_with_invalid_url_schema(self) -> None:
        logger.info(
            "\n------------test_url_config_value_with_invalid_url_schema-------------"
        )
        self.__load_config_invalid_api_server_url_schema()
        with pytest.raises(MissingSchema):
            self.api.read_credentials_and_login()

    def test_bad_url_param_noenvar_login(self) -> None:
        logger.info("\n------------test_bad_url_param_noenvar_login-------------")
        self.__load_config_invalid_api_server_url_param()
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_url_config_good_envar_login(self) -> None:
        logger.info("\n------------test_bad_url_config_good_envar_login-------------")
        self.__load_config_invalid_api_server_url_param()
        self.__load_valid_envar_params()
        assert self.api.read_credentials_and_login() is True

    def test_bad_url_config_bad_url_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_url_config_bad_url_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_value()
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = "http://WRONG_API_SERVER_URL/"
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_bad_url_config_bad_creds_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_url_config_bad_creds_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_value()
        self.__load_valid_envar_params()
        os.environ["CTF_USER"] = "WRONG_USER"
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_bad_url_config_no_fileserver_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_url_config_no_fileserver_envar_login-------------"
        )
        self.__load_config_invalid_api_server_url_value()
        os.environ["CTF_USER"] = self.user
        os.environ["CTF_PASSWORD"] = self.password
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_bad_creds_config_noenvar_login(self) -> None:
        logger.info("\n------------test_bad_creds_config_noenvar_login-------------")
        self.__load_config_invalid_user_value()
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_creds_config_good_envar_login(self) -> None:
        logger.info("\n------------test_bad_creds_config_good_envar_login-------------")
        self.__load_config_invalid_user_value()
        self.__load_valid_envar_params()
        assert self.api.read_credentials_and_login() is True

    def test_bad_creds_config_bad_url_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_creds_config_bad_url_envar_login-------------"
        )
        self.__load_config_invalid_user_value()
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = "http://WRONG_API_SERVER_URL/"
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_bad_creds_config_bad_creds_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_creds_config_bad_creds_envar_login-------------"
        )
        self.__load_config_invalid_user_value()
        self.__load_valid_envar_params()
        os.environ["CTF_USER"] = "WRONG_USER"
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_bad_creds_config_no_fileserver_envar_login(self) -> None:
        logger.info(
            "\n------------test_bad_creds_config_no_fileserver_envar_login-------------"
        )
        self.__load_config_invalid_user_value()
        os.environ["CTF_USER"] = self.user
        os.environ["CTF_PASSWORD"] = self.password
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_noconfig_noenvar_login(self) -> None:
        logger.info("\n------------test_noconfig_noenvar_login-------------")
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_noconfig_good_envar_login(self) -> None:
        logger.info("\n------------test_noconfig_good_envar_login-------------")
        self.__load_valid_envar_params()
        assert self.api.read_credentials_and_login() is True

    def test_noconfig_bad_url_envar_login(self) -> None:
        logger.info("\n------------test_noconfig_bad_url_envar_login-------------")
        self.__load_valid_envar_params()
        os.environ["CTF_API_SERVER_URL"] = "http://WRONG_API_SERVER_URL/"
        with pytest.raises(socket.error):
            self.api.read_credentials_and_login()

    def test_noconfig_bad_creds_envar_login(self) -> None:
        logger.info("\n------------test_noconfig_bad_creds_envar_login-------------")
        self.__load_valid_envar_params()
        os.environ["CTF_USER"] = "WRONG_USER"
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()

    def test_noconfig_no_fileserver_envar_login(self) -> None:
        logger.info(
            "\n------------test_noconfig_no_fileserver_envar_login-------------"
        )
        os.environ["CTF_USER"] = self.user
        os.environ["CTF_PASSWORD"] = self.password
        os.environ["CTF_API_SERVER_URL"] = self.api_server_url
        with pytest.raises(LoginException):
            self.api.read_credentials_and_login()
