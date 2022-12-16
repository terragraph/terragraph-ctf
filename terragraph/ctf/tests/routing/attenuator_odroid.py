#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from argparse import Namespace
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed

from ctf.ctf_client.runner.lib import BaseCtfTest


class AttenuatorOdroid(BaseCtfTest):
    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.atten_up_time_ms: int = 0

    def attenuator_odroid_service(
        self,
        node_ids: List[int],
        action: Optional[str] = "stop",
    ) -> None:
        """
        This methods stops or starts attenuation daemon service in attenuator devices.
        """

        command_service: str = f"systemctl {action} attenuator_daemon"
        futures: Dict = self.run_cmd(command_service, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_service} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_service} in Node {result['node_id']}:\n{result['message']}"
            )
        return

    def attenuator_odroid_set_value(
        self,
        node_ids: List[int],
        value: int,
    ) -> None:
        """
        This method sets attenuation value from 0 to 60 in attenuator devices.
        0 value means no attenuation and value 60 means at maximum attenuation.
        """

        command_set = f"python3 /usr/bin/attenuator_daemon.py --attenuation {value}"
        futures: Dict = self.run_cmd(command_set, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_set} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"{command_set} in Node {result['node_id']}:\n{result['message']}"
            )
            # result message in format of "1621374211059 , 60.0 \nDone\n"
            atten_set_resp = result["message"].strip(" ").split(",")
            atten_set_val = atten_set_resp[1].split("\n")
            if float(atten_set_val[0]) > 0.0:
                self.atten_up_time_ms = int(atten_set_resp[0])
        return

    def verify_date_time_in_attenuator_odroid(
        self,
        node_ids: List[int],
    ) -> None:
        """
        This method checks for matching date and time in attenuator device with the host
        machine's date & time. To make sure that date and time are properly set in attenuator device.
        """

        command_date: str = "date -u +%s%3N"
        futures: Dict = self.run_cmd(command_date, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_date} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            host_date_timestamp = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
            time_diff_ms = host_date_timestamp - int(result["message"])
            self.log_to_ctf(
                f"{command_date} in Node {result['node_id']}:\n{result['message']}"
            )
            self.log_to_ctf(
                f"host date timestamp in msecs:{host_date_timestamp}, timestamp difference:{time_diff_ms}"
            )
            if time_diff_ms > 15000:
                raise TestFailed(
                    "Date and time in odriod device is more than 15 secs apart from host time. please reset the time in odroid device"
                )
        return
