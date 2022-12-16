# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os

import pytest

CTF_INTERNAL = os.environ.get("CTF_INTERNAL", "False") == "True"


@pytest.fixture(scope="session")
def dev_apiserver_url():
    if CTF_INTERNAL:
        # TODO: Update this once we have internal dev env setup
        return ""
    else:
        return "http://localhost:4230/"


@pytest.fixture(scope="session")
def dev_fileserver_url():
    if CTF_INTERNAL:
        # TODO: Update this once we have internal dev env setup
        return ""
    else:
        return "http://localhost:4230/"
