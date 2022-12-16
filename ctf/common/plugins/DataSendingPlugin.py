# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging


"""
This function get a data out of system, user can add a functionality
to send/parse/analyze this payload as per the requirement
It is intended that user will write his own implementation of data sending
to scuba, pelican or any other third party tool
"""

logger = logging.getLogger(__name__)


class DataSendingPlugin:
    def __init__(self):
        pass

    def send_logs_to_any_platform(self, payload):
        if self:
            logger.info(json.dumps(payload))
