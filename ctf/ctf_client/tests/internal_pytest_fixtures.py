# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os

import pytest
from ctf.common import constants as common_constants


# TODO: These are temporary pytest fixtures for internal.
# Using TEST env VARS until internal test infra is developed.
@pytest.fixture(scope="session")
def apiserver_url():
    return os.environ.get(common_constants.CTF_TEST_API_SERVER_URL)


@pytest.fixture(scope="session")
def fileserver_url():
    return os.environ.get(common_constants.CTF_TEST_FILE_SERVER_URL)
