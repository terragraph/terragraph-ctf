#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import re
from argparse import Namespace
from typing import Dict, List, Optional

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgMHLatency(TestX86TGIgn):
    TEST_NAME = "Multi-hop latency"
    DESCRIPTION = "latency test with multiple hops like 5,4,3 and 2 hops"

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.cpe_ping_options = self.test_data["cpe_ping_options"]

    def send_ifconfig_command(
        self,
        node_ids: List[int],
        net_name_space: Optional[str] = "",
        is_controller_node: Optional[bool] = False,
        interface: Optional[str] = "",
        action: Optional[str] = "",
    ) -> None:

        command_ifconfig: str = f"ifconfig {interface} {action}"
        if net_name_space != "":
            nm_spc: str = f"ip netns exec {net_name_space}"
            command_ifconfig = f"{nm_spc} {command_ifconfig}"
        if is_controller_node:
            command_ifconfig = self._chroot_cmd(command_ifconfig)

        futures: Dict = self.run_cmd(command_ifconfig, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_ifconfig} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"command_ifconfig in Node {result['node_id']}:\n{result['message']}"
            )

    def cpe_ping_and_check_result(
        self,
        from_device_id: int,
        to_device_id: int,
        from_netns: str,
        to_netns: str,
        cpe_ping_options: Dict,
    ) -> None:

        ping_count = cpe_ping_options["duration"] / cpe_ping_options["periodicity"]

        ping_result = self.cpe_ping(
            from_device_id,
            to_device_id,
            from_netns,
            to_netns,
            count=ping_count,
            interval=cpe_ping_options["periodicity"],
        )

        if (
            cpe_ping_options["allow_pkt_loss_percnt"] != 0
            or cpe_ping_options["allow_min_latency"] != -1
            or cpe_ping_options["allow_avg_latency"] != -1
            or cpe_ping_options["allow_max_latency"] != -1
        ):

            if ping_result:
                sumry_packet_loss = re.search(
                    r"(\S+)% packet loss", ping_result["ping_summary"]
                )
                if sumry_packet_loss:
                    sumry_loss_per = sumry_packet_loss.group(1)

                stats_search = re.search(
                    r"= (\S+)/(\S+)/(\S+)/(\S+) ms", ping_result["ping_stats"]
                )
                if stats_search:
                    stat_rtt_min = stats_search.group(1)
                    stat_rtt_avg = stats_search.group(2)
                    stat_rtt_max = stats_search.group(3)

                self.log_to_ctf(
                    # pyre-fixme[61]: `stat_rtt_min` may not be initialized here.
                    # pyre-fixme[61]: `stat_rtt_avg` may not be initialized here.
                    # pyre-fixme[61]: `stat_rtt_max` may not be initialized here.
                    f"in cpe ping evaluate: ping stats:{ping_result['ping_stats']} min:{stat_rtt_min} avg:{stat_rtt_avg} max:{stat_rtt_max}",
                    "info",
                )
                self.log_to_ctf(
                    # pyre-fixme[61]: `sumry_loss_per` may not be initialized here.
                    f"in cpe ping evaluate: ping_summary:{ping_result['ping_summary']} loss per:{sumry_loss_per}",
                    "info",
                )

                if (
                    cpe_ping_options["allow_pkt_loss_percnt"] != -1
                    # pyre-fixme[61]: `sumry_loss_per` may not be initialized here.
                    and float(sumry_loss_per)
                    > cpe_ping_options["allow_pkt_loss_percnt"]
                ):
                    error_msg = f"Cpe ping failed to meet packet loss criteria of {cpe_ping_options['allow_pkt_loss_percnt']} "
                    raise TestFailed(error_msg)

                if (
                    cpe_ping_options["allow_min_latency"] != -1
                    # pyre-fixme[61]: `stat_rtt_min` may not be initialized here.
                    and float(stat_rtt_min) > cpe_ping_options["allow_min_latency"]
                ):
                    error_msg = f"Cpe ping failed to meet minimum latency criteria of {cpe_ping_options['allow_min_latency']} "
                    raise TestFailed(error_msg)

                if (
                    cpe_ping_options["allow_avg_latency"] != -1
                    # pyre-fixme[61]: `stat_rtt_avg` may not be initialized here.
                    and float(stat_rtt_avg) > cpe_ping_options["allow_avg_latency"]
                ):
                    error_msg = f"Cpe ping failed to meet average latency criteria of {cpe_ping_options['allow_avg_latency']} "
                    raise TestFailed(error_msg)

                if (
                    cpe_ping_options["allow_max_latency"] != -1
                    # pyre-fixme[61]: `stat_rtt_max` may not be initialized here.
                    and float(stat_rtt_max) > cpe_ping_options["allow_max_latency"]
                ):
                    error_msg = f"Cpe ping failed to meet maximum latency criteria of {cpe_ping_options['allow_max_latency']} "
                    raise TestFailed(error_msg)

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()

        traffic_profile = self.test_data["traffic_profile"]
        udp_trfc_prfl = traffic_profile["udp"]
        tcp_trfc_prfl = traffic_profile["tcp"]
        from_device_id = udp_trfc_prfl[0]["from_device_id"]
        to_device_id = udp_trfc_prfl[0]["to_device_id"]
        from_netns = udp_trfc_prfl[0]["from_netns"]
        to_netns = udp_trfc_prfl[0]["to_netns"]
        ping_from_to: str = (
            f"Ping from CPE device {from_device_id} port {from_netns }"
            f" to CPE device {to_device_id} port {to_netns}"
        )
        steps.append(
            {
                "name": "Clear vpp interface",
                "function": self.interface_info,
                "function_args": (True,),
                "success_msg": "Cleared vpp interface",
                "continue_on_failure": True,
            }
        )
        for trfc_type in ["udp", "tcp"]:
            steps.extend(
                [
                    {
                        "name": "Show vpp interface info",
                        "function": self.interface_info,
                        "function_args": (),
                        "success_msg": "Showed vpp interface info",
                        "continue_on_failure": True,
                    },
                    {
                        "name": f"Check ifconfig in {from_device_id}",
                        "function": self.send_ifconfig_command,
                        "function_args": (
                            [from_device_id],
                            from_netns,
                        ),
                        "success_msg": f"Checked ifconfig in node {from_device_id}",
                    },
                    {
                        "name": f"Check ifconfig in {to_device_id}",
                        "function": self.send_ifconfig_command,
                        "function_args": (
                            [to_device_id],
                            to_netns,
                        ),
                        "success_msg": f"Checked ifconfig in {to_device_id}",
                    },
                    {
                        "name": f"Iperf with {trfc_type}  traffic",
                        "function": self.run_traffic,
                        "function_args": (
                            (udp_trfc_prfl if trfc_type == "udp" else tcp_trfc_prfl),
                        ),
                        "success_msg": f"Successfully ran iperf {trfc_type} traffic",
                        "continue_on_failure": True,
                        "concurrent": True,
                    },
                    {
                        "name": f"Call evaluate {ping_from_to}",
                        "function": self.cpe_ping_and_check_result,
                        "function_args": (
                            from_device_id,
                            to_device_id,
                            from_netns,
                            to_netns,
                            self.cpe_ping_options,
                        ),
                        "success_msg": f"{ping_from_to} is successful",
                        "continue_on_failure": True,
                        "concurrent": True,
                    },
                ]
            )
        steps.extend(
            [
                {
                    "name": "Show vpp interface info",
                    "function": self.interface_info,
                    "function_args": (),
                    "success_msg": "Showed vpp interface info",
                    "continue_on_failure": True,
                },
                {
                    "name": f"Check ifconfig in {from_device_id}",
                    "function": self.send_ifconfig_command,
                    "function_args": (
                        [from_device_id],
                        from_netns,
                    ),
                    "success_msg": f"Checked ifconfig in {from_device_id}",
                },
                {
                    "name": f"Check ifconfig in {to_device_id}",
                    "function": self.send_ifconfig_command,
                    "function_args": (
                        [to_device_id],
                        to_netns,
                    ),
                    "success_msg": f"Checked ifconfig in {to_device_id}",
                },
            ]
        )

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
