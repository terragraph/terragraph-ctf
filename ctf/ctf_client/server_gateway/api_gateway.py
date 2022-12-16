# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging

logger = logging.getLogger(__name__)

# TODO: Check if we can create a shipit rule to export a new api_gateway which will only use serverless_api
def get_ctf_api(serverless=False):
    """
    Returns CtfApi instance based on serverless param.
    """
    if serverless:
        from ctf.ctf_client.serverless_lib.serverless_api import ServerlessApi

        logger.info("Serverless api")
        return ServerlessApi()
    else:
        from ctf.ctf_client.server_lib.server_api import ServerApi

        logger.info("Server api")
        return ServerApi()
