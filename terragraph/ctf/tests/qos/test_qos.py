#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import re
from typing import Any, Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.sit import SitPumaTgCtfTest
from terragraph.ctf.x86_traffic_gen import x86TrafficGenCtfTest

LOG = logging.getLogger(__name__)


class TestTgQos(SitPumaTgCtfTest, x86TrafficGenCtfTest):
    def packet_capture(
        self, node_ids: List[int], interface: str, testname: str
    ) -> None:
        cmd: str = f"ip netns exec {interface} nohup tcpdump -i {interface} > {interface}_{testname}x86.pcap 2>&1 &"
        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {cmd} failed: " + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"Packet capture cmd {cmd} applied successfully on node {result['node_id']} : {result['message']}"
            )

    def print_policerinfo(self, node_ids: List[int]) -> None:
        cmd: str = "vppctl show policer"
        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {cmd} failed: " + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(
                f"node {result['node_id']}'s policer info is {result['message']}"
            )

    def cpe_ping_result_check(
        self,
        from_device_id: int,
        to_device_id: int,
        from_netns: str,
        to_netns: str,
        ping_options: Dict,
    ) -> None:

        """To validate the ping results"""
        ping_count = ping_options["duration"] / ping_options["periodicity"]
        ping_options["allow_pkt_loss_percnt"] = ping_options.get(
            "allow_pkt_loss_percnt", 0
        )
        ping_options["allow_min_latency"] = ping_options.get("allow_min_latency", -1)
        ping_options["allow_avg_latency"] = ping_options.get("allow_avg_latency", -1)
        ping_options["allow_max_latency"] = ping_options.get("allow_max_latency", -1)

        ping_result = self.cpe_ping(
            from_device_id,
            to_device_id,
            from_netns,
            to_netns,
            count=ping_count,
            interval=ping_options["periodicity"],
            tos=ping_options["tos"],
            pkt_sz=ping_options["pkt_sz"],
        )

        if (
            ping_options["allow_pkt_loss_percnt"] != 0
            or ping_options["allow_min_latency"] != -1
            or ping_options["allow_avg_latency"] != -1
            or ping_options["allow_max_latency"] != -1
        ):
            if ping_result:
                sumry_packet_loss = re.search(
                    r"(\S+)% packet loss", ping_result["ping_summary"]
                )
                sumry_loss_per = -1
                if sumry_packet_loss:
                    sumry_loss_per = sumry_packet_loss.group(1)

                stats_search = re.search(
                    r"= (\S+)/(\S+)/(\S+)/(\S+) ms", ping_result["ping_stats"]
                )
                stat_rtt_min = -1
                stat_rtt_avg = -1
                stat_rtt_max = -1
                if stats_search:
                    stat_rtt_min = stats_search.group(1)
                    stat_rtt_avg = stats_search.group(2)
                    stat_rtt_max = stats_search.group(3)

                self.log_to_ctf(
                    f"in cpe ping evaluate: ping stats:{ping_result['ping_stats']} min:{stat_rtt_min} avg:{stat_rtt_avg} max:{stat_rtt_max}",
                    "info",
                )
                self.log_to_ctf(
                    f"in cpe ping evaluate: ping_summary:{ping_result['ping_summary']} loss per:{sumry_loss_per}",
                    "info",
                )

                if (
                    ping_options["allow_pkt_loss_percnt"] != -1
                    and float(sumry_loss_per) > ping_options["allow_pkt_loss_percnt"]
                ):
                    error_msg = f"Cpe ping failed to meet packet loss criteria of {ping_options['allow_pkt_loss_percnt']} "
                    raise TestFailed(error_msg)

                if (
                    ping_options["allow_min_latency"] != -1
                    and float(stat_rtt_min) > ping_options["allow_min_latency"]
                ):
                    error_msg = f"Cpe ping failed to meet minimum latency criteria of {ping_options['allow_min_latency']} "
                    raise TestFailed(error_msg)

                if (
                    ping_options["allow_avg_latency"] != -1
                    and float(stat_rtt_avg) > ping_options["allow_avg_latency"]
                ):
                    error_msg = f"Cpe ping failed to meet average latency criteria of {ping_options['allow_avg_latency']} "
                    raise TestFailed(error_msg)

                if (
                    ping_options["allow_max_latency"] != -1
                    and float(stat_rtt_max) > ping_options["allow_max_latency"]
                ):
                    error_msg = f"Cpe ping failed to meet maximum latency criteria of {ping_options['allow_max_latency']} "
                    raise TestFailed(error_msg)

    def iterate_iperf(
        self, iterations: int, traffic_profile: List[Dict[str, Any]]
    ) -> None:
        for i in range(0, iterations):
            self.log_to_ctf(
                f"this is the {i} number of iteration for {traffic_profile}"
            )
            self.run_traffic(traffic_profile)
            port_num = traffic_profile[len(traffic_profile) - 1]["port"] + 1
            for stream in range(len(traffic_profile)):
                traffic_profile[stream]["port"] = port_num + stream

    def cpe_parallel_ping(
        self,
        ping_profile: List[Dict],
    ) -> List[Dict]:
        ping_all_steps = []
        for stream in ping_profile:
            ping_all_steps.append(
                {
                    "name": "parallel ping started",
                    "function": self.cpe_ping_result_check,
                    "function_args": (
                        stream["from_device_id"],
                        stream["to_device_id"],
                        stream["from_netns"],
                        stream["to_netns"],
                        stream["ping_options"],
                    ),
                    "success_msg": "parallel ping done successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                }
            )
        return ping_all_steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
