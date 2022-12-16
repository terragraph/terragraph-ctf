#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from time import sleep
from typing import Dict, List

from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIot

LOG = logging.getLogger(__name__)


class TestNodeIotNOTSBase(TestNodeIot):
    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestNodeIotNOTSBase, TestNodeIotNOTSBase
        ).test_params()
        test_params["disable_gps_node_id"] = {
            "desc": "Node ID of the Node where GPS will be disabled!",
            "required": True,
            "convert": int,
        }
        test_params["traffic_streams"] = {
            "desc": (
                "path to json file defining device id and ports of traffic generators "
                + "to run traffic"
            ),
            "required": True,
        }
        return test_params


class TestNodeIotNOTS1(TestNodeIotNOTSBase):
    TEST_NAME = "NodeIOTv2-NOTS-1 (Node Time Sync)"
    DESCRIPTION = "The purpose of this test is to ensure links on the  OEM-DN-DUT come up when GPS is not available on reference puma DN node. "

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        steps = super().get_test_steps()

        ignition_timeout_s = self.test_args["ignition_timeout_s"]

        disable_gps_node_id = self.test_args["disable_gps_node_id"]
        traffic_streams = json.load(open(self.test_args.get("traffic_streams", [])))
        ping_streams = traffic_streams.get("ping_streams", [])
        traffic_streams = traffic_streams.get("traffic_streams", [])

        steps.extend(
            [
                {
                    "name": f"Disable GPS on reference node {disable_gps_node_id}",
                    "function": self.switch_gpsd,
                    "function_args": (
                        disable_gps_node_id,
                        False,
                    ),
                    "success_msg": "gpsd service stopped",
                },
                {
                    "name": "Wait 35 seconds",
                    "function": sleep,
                    "function_args": (35,),
                    "success_msg": "Finished waiting",
                },
                {
                    "name": "Check that the network is entirely up",
                    "function": self.try_until_timeout,
                    "function_args": (
                        self.controller_verify_topology_up,
                        (self.api_service_request, ["getTopology"]),
                        5,
                        ignition_timeout_s,
                    ),
                    "success_msg": "Network is up",
                    "error_handler": self.get_common_error_handler(),
                },
            ]
        )

        for stream in ping_streams:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                }
            )

        for i, stream in enumerate(traffic_streams):
            stream.update(
                {
                    "bandwidth": 500,
                    "threshold": {"throughput": 0.99, "lost datagrams": 0.015},
                    "port": 5002 + i,
                    "traffic_type": "UDP",
                    "direction": "bi",
                    "packet_size": "1452",
                    "time": 120,
                }
            )
            steps.extend(
                [
                    {
                        "name": "Run Traffic",
                        "function": self.run_traffic,
                        "function_args": ([stream],),
                        "success_msg": "iperf ran successfully",
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Re-Enable GPS on reference node {disable_gps_node_id}",
                        "function": self.switch_gpsd,
                        "function_args": (
                            disable_gps_node_id,
                            True,
                        ),
                        "success_msg": "GPSD Started",
                    },
                ]
            )

        return steps


class TestNodeIotNOTS2(TestNodeIotNOTSBase):
    TEST_NAME = "NodeIOTv2-NOTS-2 (Node Time Sync)"
    DESCRIPTION = "The purpose of this test to ensure links on OEM-DN-DUT are taken down when GPS is not available on OEM-DN-DUT sectors when only CNs are associated with OEM-DN-DUT."

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        steps = super().get_test_steps()

        disable_gps_node_id = self.test_args["disable_gps_node_id"]
        traffic_streams = json.load(open(self.test_args.get("traffic_streams", [])))
        ping_streams = traffic_streams.get("ping_streams", [])

        # Ping from POP-Traffic-Generator to CN-Traffic-Generator and verify link up.
        for stream in ping_streams:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                }
            )

        # Shutdown GPS on DN in the middle. Verify link down event.
        steps.extend(
            [
                {
                    "name": "Disable GPS on reference node {disable_gps_node_id}",
                    "function": self.switch_gpsd,
                    "function_args": (
                        disable_gps_node_id,
                        False,
                    ),
                    "success_msg": "GPSD Stopped",
                },
                {
                    "name": "Wait 35 seconds for controller to decide if the link died after disabling GPS",
                    "function": sleep,
                    "function_args": (35,),
                    "success_msg": "Finished waiting",
                },
            ]
        )

        # Try pinging from POP-Traffic-Generator to CN-Traffic-Generator and vice versa, and ping should fail.
        for stream in ping_streams:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is FAILED"
                    ),
                    "continue_on_failure": True,
                    "negate_result": True,
                }
            )

        # Restore GPS on DN in the middle.
        steps.extend(
            [
                {
                    "name": "Re-Enable GPS on reference node {disable_gps_node_id}",
                    "function": self.switch_gpsd,
                    "function_args": (
                        disable_gps_node_id,
                        True,
                    ),
                    "success_msg": "GPSD started",
                },
                {
                    "name": "Wait 35 seconds",
                    "function": sleep,
                    "function_args": (35,),
                    "success_msg": "Finished waiting",
                },
            ]
        )

        # Ping from POP-Traffic-Generator to CN-Traffic-Generator and vice versa. Ping should Pass.
        for stream in ping_streams:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                }
            )

        return steps


class TestNodeIotNOTS3(TestNodeIotNOTSBase):
    TEST_NAME = "NodeIOTv2-NOTS-3 (Node Time Sync)"
    DESCRIPTION = "No link between middle-DN and CN. The purpose of this test is to ensure links on the OEM-DN-DUT remain up even when GPS is taken down on all the DUT sectors and time is sourced from peer DN sectors."

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        steps = super().get_test_steps()

        disable_gps_node_id = self.test_args["disable_gps_node_id"]
        traffic_streams = json.load(open(self.test_args.get("traffic_streams", [])))
        ping_streams = traffic_streams.get("ping_streams", [])

        # Ping between nodes and verify link up.
        for stream in ping_streams:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                }
            )

        # Shutdown GPS on given node. Link should stay up.
        steps.extend(
            [
                {
                    "name": "Disable GPS on reference node {disable_gps_node_id}.",
                    "function": self.switch_gpsd,
                    "function_args": (
                        disable_gps_node_id,
                        False,
                    ),
                    "success_msg": "GPSD Stopped",
                },
                {
                    "name": "Wait 35 seconds",
                    "function": sleep,
                    "function_args": (35,),
                    "success_msg": "Finished waiting",
                },
            ]
        )

        # Ping between nodes and verify link stays up.
        for stream in ping_streams:
            steps.append(
                {
                    "name": (
                        f"ping from CPE device {stream['from_device_id']} port {stream['from_netns']}"
                        f" to CPE device {stream['to_device_id']} port {stream['to_netns']}"
                    ),
                    "function": self.cpe_ping,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                    ),
                    "success_msg": (
                        f"ping from device {stream['from_device_id']} port {stream['from_netns']}"
                        f"to device {stream['to_device_id']} port {stream['to_netns']} is successful"
                    ),
                    "continue_on_failure": True,
                }
            )

        # Restart GPS.
        steps.append(
            {
                "name": "Re-Enable GPS on reference node {disable_gps_node_id}.",
                "function": self.switch_gpsd,
                "function_args": (
                    disable_gps_node_id,
                    False,
                ),
                "success_msg": "GPSD Started",
            }
        )

        return steps
