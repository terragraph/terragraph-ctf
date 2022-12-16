# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import sys

import pytest


sys.path.append("../../../")

from ctf.ctf_client.lib.api_helper import (
    UTFApis,
)  # TODO: Change UTFApis to CTF_Client etc
from ctf.ctf_client.tests.dev_fixtures import dev_apiserver_url, dev_fileserver_url

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"

if not CTF_INTERNAL:
    from ctf.ctf_client.tests.api_utils import ApiUtils as TestApiUtils


@pytest.fixture(scope="session")
def client_api(dev_apiserver_url, dev_fileserver_url):
    return UTFApis(api_server_url=dev_apiserver_url, file_server_url=dev_fileserver_url)


@pytest.fixture(scope="session")
def test_api_utils(dev_apiserver_url, dev_fileserver_url):
    if not CTF_INTERNAL:
        return TestApiUtils(dev_apiserver_url, dev_fileserver_url)
    return None
