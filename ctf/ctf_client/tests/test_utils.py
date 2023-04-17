# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import os

from ctf.ctf_client.tests import testing_fixtures

logger = logging.getLogger(__name__)
CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

if CTF_INTERNAL:
    from crypto.keychain_service.keychain import ttypes as keychain
    from libfb.py.thrift_clients.keychain_thrift_client import KeychainClient


class TestUtils:
    def __init__(self, apiserver_url, fileserver_url):
        self.apiserver_url = apiserver_url
        self.fileserver_url = fileserver_url

    def remove_envar_params(self):
        if (
            os.environ.get("CTF_USER")
            and os.environ.get("CTF_PASSWORD")
            and os.environ.get("CTF_API_SERVER_URL")
            and os.environ.get("CTF_FILE_SERVER_URL")
        ):
            del os.environ["CTF_USER"]
            del os.environ["CTF_PASSWORD"]
            del os.environ["CTF_API_SERVER_URL"]
            del os.environ["CTF_FILE_SERVER_URL"]

    def get_secret(self, secret):
        req = keychain.GetSecretRequestV2(name=secret)
        try:
            secret_resp = KeychainClient().getSecretV2(req)
            secret_str = str(secret_resp.secret.value, "utf-8")
            return secret_str
        except (
            keychain.KeychainServiceException,
            keychain.KeychainClientException,
        ) as e:
            logger.exception(str(e))
            return None

    def get_param(self, param):
        if CTF_INTERNAL:
            return self.get_secret(param)
        else:
            if param == "CTF_API_SERVER_URL":
                return self.apiserver_url
            elif param == "CTF_FILE_SERVER_URL":
                return self.fileserver_url
            else:
                return testing_fixtures.TEST_PARAMS[param]

    def get_test_param(self, param):
        return testing_fixtures.TEST_PARAMS[param]

    def load_secrets(self):
        os.environ["CTF_USER"] = self.get_param("CTF_BUCK_USER")
        os.environ["CTF_PASSWORD"] = self.get_param("CTF_BUCK_PASSWORD")
        os.environ["CTF_API_SERVER_URL"] = self.get_param("CTF_API_SERVER_URL")
        os.environ["CTF_FILE_SERVER_URL"] = self.get_param("CTF_FILE_SERVER_URL")

    def before_test_run(self):
        self.remove_envar_params()
        self.load_secrets()
        os.system(
            "if [ -f ~/.ctf_config ]; then mv ~/.ctf_config ~/.ctf_config.bak; fi"
        )

    def after_test_run(self):
        os.system(
            "if [ -f ~/.ctf_config.bak ]; then mv ~/.ctf_config.bak ~/.ctf_config; fi"
        )
        os.system(
            "if [ -f /tmp/dummy.log.bak ]; then mv /tmp/dummy.log /tmp/dummy.log; fi"
        )
        os.system("if [ -f /tmp/dummy.log ]; then rm /tmp/dummy.log; fi")
        self.remove_envar_params()
