# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging


logger = logging.getLogger(__name__)


class BaseInterfaceClass:
    def __init__(self):
        self.connection = None
        self.driver = None
        self.metadata = {}

    def action_custom_command(
        self,
        cmd,
        timeout=50,
        on_process_start=None,
        on_process_stop=None,
        on_stdin_send=None,
        on_stdout_recv=None,
        on_stderr_recv=None,
        check_cancel=None,
        check_cancel_complete=None,
        can_split_cmd=False,
    ):
        return self.connection.send_command(
            cmd=cmd,
            timeout=timeout,
            on_process_start=on_process_start,
            on_process_stop=on_process_stop,
            on_stdin_send=on_stdin_send,
            on_stdout_recv=on_stdout_recv,
            on_stderr_recv=on_stderr_recv,
            check_cancel=check_cancel,
            check_cancel_complete=check_cancel_complete,
            # custom_channel_processing must be enabled in Connection class for split_cmd_on_semicolon to then be enabled
            split_cmd=can_split_cmd and self.connection.custom_channel_processing,
        )

    def run_driver_action(self, action_name, input_var=None):
        action = getattr(self.driver, action_name)
        result = action(input_var) if input_var else action()
        return result

    def set_driver(self, driver):
        self.driver = driver

    def set_metadata(self, metadata):
        self.metadata = metadata

    @classmethod
    def custom_fun(cls):
        logger.debug(f"hello from {cls.__name__}")
