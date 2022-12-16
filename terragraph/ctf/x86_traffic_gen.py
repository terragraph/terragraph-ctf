#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Library for x86 traffic generator specific actions for Terragraph
"""

import datetime
import ipaddress
import logging
import re
import threading
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from ctf.ctf_client.runner.exceptions import (
    DeviceCmdError,
    DeviceConfigError,
    TestFailed,
    TestUsageError,
)
from ctf.ctf_client.runner.lib import BaseCtfTest


LOG = logging.getLogger(__name__)


class x86TrafficGenCtfTest(BaseCtfTest):
    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            x86TrafficGenCtfTest, x86TrafficGenCtfTest
        ).test_params()
        test_params["continue_run_traffic"] = {
            "desc": "Continue on run_traffic failures",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        return test_params

    # TODO - identify traffic gen devices better?
    # TODO - differentiate traffic gen and x86 TG VM
    def get_traffic_gen_devices(self) -> List[int]:
        """Return all test devices with type 'generic'."""
        return [
            node_id
            for node_id, device in self.device_info.items()
            if device.device_type() == "generic"
        ]

    def read_traffic_gen_info(self) -> None:
        """Get and save traffic gen info from nodes_data, to be used for the
        cpe_ping and iperf functions. Raise an exception if there are
        multiple traffic gen confs in self.nodes_data.

        Expects the following node data:
        ```
        "<server_node_id>": {
            "traffic_gen": {
                "server_id": <server_node_id>,
                "client_id": <client_node_id>
            },
            "port_name": "<server_port_name>"
        },
        "<client_node_id>": {
            "port_name": "<client_port_name>"
        }
        ```
        """
        id = None
        err = "Can't find traffic gen conf"
        for node in self.nodes_data:
            if "traffic_gen" in self.nodes_data[node]:
                if id is None:
                    id = int(node)
                else:
                    err = "Multiple traffic gen confs found"
                    id = None
                    break
        if id is None:
            LOG.debug(err)
            raise DeviceConfigError(err)

        traffic_gen_conf = self.read_nodes_data([id, "traffic_gen"])
        self.log_to_ctf(f"traffic gen config:\n{traffic_gen_conf}")

        # pyre-fixme[16]: `x86TrafficGenCtfTest` has no attribute `server_id`.
        self.server_id = traffic_gen_conf["server_id"]
        # pyre-fixme[16]: `x86TrafficGenCtfTest` has no attribute `client_id`.
        self.client_id = traffic_gen_conf["client_id"]
        # pyre-fixme[16]: `x86TrafficGenCtfTest` has no attribute `server_port_name`.
        self.server_port_name = self.read_nodes_data([self.server_id, "port_name"])
        # pyre-fixme[16]: `x86TrafficGenCtfTest` has no attribute `client_port_name`.
        self.client_port_name = self.read_nodes_data([self.client_id, "port_name"])

    def get_x86_traffic_gen_ip(
        self, traffic_gen_id: int, netns: str, intf: str, ipv6: bool = True
    ) -> str:
        """Retrieve CPE ip on the ethernet port the node
        is connected to the x86 traffic_gen on"""
        if traffic_gen_id not in self.device_info:
            raise TestUsageError(
                f"traffic generator device {traffic_gen_id} not found in device_info"
            )
        if ipv6:
            grep_str = "global"
        else:
            grep_str = "inet "

        cmd = f"ip netns exec {netns} ifconfig {intf} | grep -i {grep_str}"
        cmd_success = self.device_info[traffic_gen_id].action_custom_command(
            cmd, self.timeout - 1
        )
        if cmd_success["error"]:
            error_msg = f"Check '{cmd}' failed: {cmd_success['message'].strip()}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

        if not cmd_success["message"]:
            error_msg = f"traffic gen {traffic_gen_id} did not get a global IP from CPE prefix: {cmd_success}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

        # parse and return CPE ip
        tokens = cmd_success["message"].split()

        if ipv6:
            raw_addr = str(tokens[2] if tokens[1].startswith("addr") else tokens[1])
            ip_addr = raw_addr.split("/")[0]
        else:
            ipv4_token = tokens[1].split(":")
            ip_addr = tokens[1] if len(ipv4_token) == 1 else ipv4_token[1]
        ipaddress.ip_address(ip_addr)
        return ip_addr

    # TODO - cleanup this API to use ping_ip

    def cpe_ping(
        self,
        from_device_id: int,
        to_device_id: int,
        from_netns: str,
        to_netns: str,
        from_intf: str = "",
        to_intf: str = "",
        ipv6: bool = True,
        count: int = 5,
        wait_time: float = 0.5,
        interval: float = 1,
        pkt_sz: int = 64,
        tos: str = "",
    ) -> Dict[str, Any]:

        """ping from traffic gen client node to traffic gen server node
        input arguments:
          from_device_id: source node id
          to_device_id  : destination node id
          from_netns    : source network namepace
          to_netns      : destination network namespace
          from_intf     : source interface name
          to_intf       : destination interface name
          count         : stop ping after sending count echo request packets.
          wait_time     : time to wait for response in seconds.
          interval      : wait interval seconds between sending each packet.
                          default is 1 second and there are cases of using 0.2 seconds.
          pkt_sz        : to send bytes other than default 64 bytes
          tos           : quality of service related bits
        """
        # if tos value provided, create a tos param with -Q option
        # or else ignore it by giving empty space in the ping command

        if tos:
            tos_param = f"-Q {tos}"
        else:
            tos_param = ""

        # If source and network interfaces are not specified, use
        # corresponding network namespaces.
        if not from_intf:
            from_intf = from_netns
        if not to_intf:
            to_intf = to_netns
        ret_ping_result = {}
        dest_ip = self.get_x86_traffic_gen_ip(
            to_device_id, to_netns, to_intf, ipv6=ipv6
        )
        if from_device_id not in self.device_info:
            raise TestUsageError(
                f"traffic generator device {from_device_id} not found in device_info"
            )
        ping = "ping6" if ipv6 else "ping"
        cmd = (
            f"ip netns exec {from_netns} /bin/{ping} -c {count} "
            f"-w {wait_time} -i {interval} -s {pkt_sz} {dest_ip} {tos_param}"
        )
        cmd_success = self.device_info[from_device_id].action_custom_command(
            cmd, self.timeout - 1
        )
        self.log_to_ctf(cmd)
        self.log_to_ctf(f"message:{cmd_success}")

        if cmd_success["error"]:
            error_msg = f"Running '{cmd}' failed: {cmd_success['message'].strip()}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

        output = cmd_success["message"]
        self.log_to_ctf(f"{cmd}\n{output}")
        ping_summary = ""
        ping_stats = ""
        for output_line in output.split("\n"):
            if "packets transmitted" in output_line:
                ping_summary = output_line
            if "min/avg/max/mdev" in output_line:
                ping_stats = output_line

        self.log_to_ctf(f"ping_summary: {ping_summary}")
        self.log_to_ctf(f"ping_stats: {ping_stats}")
        self.ping_output_to_ctf_table(ping_summary, ping_stats, from_device_id, dest_ip)

        if int(ping_summary.split()[3]) == 0:
            error_msg = f"{cmd} from x86 traffic generator {from_device_id} failed: {ping_summary}"
            self.log_to_ctf(error_msg, "error")
            raise TestFailed(error_msg)

        self.log_to_ctf(
            f"ping from {from_intf} on device {from_device_id} to {to_intf} on "
            + f"device {to_device_id} summary: {ping_summary}",
            "info",
        )

        ret_ping_result = {"ping_summary": ping_summary, "ping_stats": ping_stats}

        return ret_ping_result

    def cpe_ping_and_verification(
        self,
        from_device_id: int,
        to_device_id: int,
        from_netns: str,
        to_netns: str,
        from_interface: str,
        to_interface: str,
        ipv6: bool,
        ping_options: Dict,
    ) -> None:

        """ping check and verification from traffic gen client node to traffic gen server node
        input arguments:
          from_device_id: source node id
          to_device_id  : destination node id
          from_netns    : source network namepace
          to_netns      : destination network namespace
          from_interface: source interface name
          to_interface  : destination interface name
          ipv6          : do IPv4 or Ipv6 ping
          ping_options  : Dict to pass ping specific parameters
                          e.g - ping_packets (default 100),
                                ping_duration (default 100 seconds)
        """

        ping_pkts = ping_options.get("ping_packets", 100)
        ping_duration = ping_options.get("ping_duration", 100)
        ping_interval = ping_duration / ping_pkts

        ping_result = self.cpe_ping(
            from_device_id,
            to_device_id,
            from_netns,
            to_netns,
            from_interface,
            to_interface,
            ipv6=ipv6,
            count=ping_pkts,
            interval=ping_interval,
        )

        if ping_result:
            sumry_loss_per = 100.0
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
            else:
                error_msg = (
                    f"no results available in cpe ping result {str(ping_result)}"
                )
                raise TestFailed(error_msg)

    def cpe_set_mtu(
        self,
        device_id: int,
        interface: str,
        mtu: int,
        # pyre-fixme[9]: netns has type `str`; used as `None`.
        netns: str = None,
    ) -> None:
        """Default config for traffic generators is each nic in its own namespace"""
        if netns is None:
            netns = interface

        cmd = f"ip netns exec {netns} ip link set dev {interface} mtu {mtu}"
        cmd_success = self.device_info[device_id].action_custom_command(
            cmd, self.timeout - 1
        )
        self.log_to_ctf(cmd)
        if cmd_success["error"]:
            error_msg = f"Running '{cmd}' failed: {cmd_success['message'].strip()}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

        self.log_to_ctf(
            f"Set MTU of interface {interface} in netns {netns} to {mtu}", "info"
        )

    def cpe_set_all_interfaces_mtu(self, mtu: int) -> None:
        for node_id in self.get_traffic_gen_devices():
            self.cpe_set_mtu(node_id, self.read_nodes_data([node_id, "port_name"]), mtu)

    def configure_iperf_stream(
        self,
        traffic_profile: Dict[str, Any],
        reverse: bool = False,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        from traffic_profile configure iperf client and server and return tuple of iperf server and client info
        of format
        ```
            (
                {
                    "cmd": <iperf server command string>
                    "device_id": <device to run iperf server>
                    "netns": <namespace on device to run iperf server>
                },
                {
                    "cmd": <iperf client command string>
                    "device_id": <device to run iperf client>
                    "netns": <namespace on device to run iperf client>
                    "threshold": <map of threshold values to compare iperf result with>
                }
            )
        ```
        """
        server_cmd = {}
        client_cmd = {}
        threshold = {
            "throughput": (
                traffic_profile["threshold"]["throughput"]
                * traffic_profile["bandwidth"]
            ),
            "lost datagrams": traffic_profile["threshold"]["lost datagrams"],
        }
        timeout = traffic_profile["time"]
        port = traffic_profile["port"]
        window_size = traffic_profile.get("window_size", 4)
        tos = traffic_profile.get("tos", "")
        if tos != "":
            tos = f"-S {tos}"
        if reverse:
            server_netns = traffic_profile["from_netns"]
            server_device_id = traffic_profile["from_device_id"]
            server_ip = traffic_profile["from_ip"]

            client_netns = traffic_profile["to_netns"]
            client_device_id = traffic_profile["to_device_id"]
            port = port + 1
        else:
            server_netns = traffic_profile["to_netns"]
            server_device_id = traffic_profile["to_device_id"]
            server_ip = traffic_profile["to_ip"]

            client_netns = traffic_profile["from_netns"]
            client_device_id = traffic_profile["from_device_id"]

        iperf_server_cmd = (
            f"date; ip netns exec {server_netns} nohup timeout {timeout + 10} "
            + f"iperf3 -s -B {server_ip}  -p {port} -i 1  -fm > "
            + f"/tmp/{client_device_id}-{client_netns}--{server_device_id}-{server_netns}-{port}_server.txt &"
        )
        iperf_client_cmd = (
            f"date; ip netns exec {client_netns} iperf3 -c {server_ip} -t {timeout}"
            + f" -p {port} -w {window_size}M -b {traffic_profile['bandwidth']}M "
            + f"-l {traffic_profile['packet_size']} {tos} -i 1 -fm --connect-timeout 5000"
        )
        if traffic_profile["traffic_type"] == "UDP":
            iperf_client_cmd = f"{iperf_client_cmd} -u"

        server_cmd = {
            "cmd": iperf_server_cmd,
            "device_id": server_device_id,
            "netns": server_netns,
            "port": port,
        }
        client_cmd = {
            "cmd": iperf_client_cmd,
            "device_id": client_device_id,
            "netns": client_netns,
            "threshold": threshold,
        }

        return server_cmd, client_cmd

    def process_iperf_result(
        self, result: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        parse iperf result data and return iperf_data_summary and iperf_data_list dictionaries
        to be used to visualize iperf results.
        """
        iperf_data_list = []
        iperf_data_summary = {}
        interval = 0
        for line in result.split("\n")[6:]:
            if (
                (line == "")
                or ("sender" in line)
                or ("connected" in line)
                or ("5]" not in line)
            ):
                continue
            elif "receiver" in line:
                try:
                    iperf_data_summary = {"Bandwidth Mbits/sec": float(line.split()[6])}
                    if "%" in line:
                        iperf_data_summary.update(
                            {
                                "Jitter ms": float(line.split()[8]),
                                "lost_datagrams": int(line.split()[10].split("/")[0]),
                                "total_datagrams": int(line.split()[10].split("/")[1]),
                                "lost_datagram_percentage": float(
                                    line.split()[11].strip("(%)")
                                ),
                            }
                        )
                except IndexError:
                    self.log_to_ctf(f"Index error caught in this entry of iperf {line}")
                    pass
                except ValueError:
                    self.log_to_ctf(f"Value error caught in this entry of iperf {line}")
                    pass
            else:
                try:
                    iperf_entry = {"Bandwidth Mbits/sec": float(line.split()[6])}
                    if "%" in line:
                        iperf_entry.update(
                            {
                                "Jitter ms": float(line.split()[8]),
                                "lost_datagrams": int(line.split()[10].split("/")[0]),
                                "total_datagrams": int(line.split()[10].split("/")[1]),
                                "lost_datagram_percentage": float(
                                    line.split()[11].strip("(%)")
                                ),
                            }
                        )
                    if "receiver" in line:
                        iperf_data_summary = iperf_entry
                    else:
                        iperf_entry["time interval"] = interval
                        iperf_data_list.append(iperf_entry)
                except IndexError:
                    self.log_to_ctf(f"Index error caught in this entry of iperf {line}")
                    pass
                except ValueError:
                    self.log_to_ctf(f"Value error caught in this entry of iperf {line}")
                    pass
            interval += 1
        return iperf_data_list, iperf_data_summary

    def thread_log(self, log: str = " ") -> str:
        return f"[thread:{threading.get_native_id()}] [{datetime.datetime.now()}] {log}"

    def run_iperf_stream(
        self,
        server_cmd: Dict[str, Any],
        client_cmd: Dict[str, Any],
        run_time: int = 300,
        step_idx: Optional[int] = None,
    ) -> Dict[Any, int]:
        """
        starts a single iperf server and client on respective traffic generator devices from
        their respective network namespaces (defined in dict server_cmd, client_cmd for the iperf stream).
        Returns an object with the following format once iperf stream finishes running
        ```
            {
                "success": <boolean>,
                "message": {
                    "msg": <iperf output on success>
                    "stream_name": <iperf stream name string>
                    "server_device_id": <device id where iperf server ran>
                    "threshold": <map of threshold values>
                },
                "error": "<error string upon iperf failure>",
                "node_id": <int>
            }
        ```
        """

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            self.thread_local.init(step_idx)
        self.log_to_ctf(self.thread_log("iperf thread start time"))
        # Start iperf server
        server_cmd_success = self.device_info[
            server_cmd["device_id"]
        ].action_custom_command(server_cmd["cmd"], run_time)
        self.log_to_ctf(self.thread_log(f"server_cmd: {server_cmd['cmd']}"))
        if server_cmd_success["error"]:
            server_cmd_success["message"] = {
                "msg": server_cmd_success["message"],
                "stream_name": f"{client_cmd['device_id']}-{client_cmd['netns']}--{server_cmd['device_id']}-{server_cmd['netns']}-{server_cmd['port']}",
                "server_device_id": server_cmd["device_id"],
            }
            return server_cmd_success
        self.log_to_ctf(server_cmd_success["message"])

        # Start iperf client
        client_cmd_success = self.device_info[
            client_cmd["device_id"]
        ].action_custom_command(client_cmd["cmd"], run_time)
        self.log_to_ctf(self.thread_log(f"client_cmd: {client_cmd['cmd']}"))
        self.log_to_ctf(client_cmd_success["message"])
        client_cmd_success["message"] = {
            "msg": client_cmd_success["message"],
            "stream_name": f"{client_cmd['device_id']}-{client_cmd['netns']}--{server_cmd['device_id']}-{server_cmd['netns']}-{server_cmd['port']}",
            "threshold": client_cmd["threshold"],
            "server_device_id": server_cmd["device_id"],
        }
        return client_cmd_success

    def configure_traffic_profile(
        self, traffic_profile: List[Dict[str, Any]]
    ) -> Dict[int, List[Any]]:
        """
        From traffic_profile configure and return a map of steam_no to traffic_stream.
        Where traffic_stream format is:
        ```
            [
                self.run_iperf_stream <function to run iperf stream>,
                server_cmd <dict defining iperf server>,
                client_cmd <dict defining iperf client>,
                time <time in seconds for which iperf is run>,
            ]
        ```
        """
        traffic_streams = {}
        stream_idx = 0
        for traffic_stream in traffic_profile:
            from_interface = traffic_stream.get(
                "from_interface", traffic_stream.get("from_netns", None)
            )
            to_interface = traffic_stream.get(
                "to_interface", traffic_stream.get("to_netns", None)
            )
            ipv6 = traffic_stream.get("ipv6", True)
            traffic_stream["from_ip"] = self.get_x86_traffic_gen_ip(
                traffic_stream["from_device_id"],
                traffic_stream["from_netns"],
                from_interface,
                ipv6=ipv6,
            )
            traffic_stream["to_ip"] = self.get_x86_traffic_gen_ip(
                traffic_stream["to_device_id"],
                traffic_stream["to_netns"],
                to_interface,
                ipv6=ipv6,
            )
            server_cmd, client_cmd = self.configure_iperf_stream(traffic_stream)
            traffic_streams[stream_idx] = [
                self.run_iperf_stream,
                server_cmd,
                client_cmd,
                traffic_stream["time"] + 10,
            ]
            if traffic_stream["direction"] == "bi":
                server_cmd, client_cmd = self.configure_iperf_stream(
                    traffic_stream, True
                )
                traffic_streams[stream_idx + 1] = [
                    self.run_iperf_stream,
                    server_cmd,
                    client_cmd,
                    traffic_stream["time"] + 10,
                ]
                stream_idx += 2
            stream_idx += 1
        return traffic_streams

    def visualize_iperf_results(
        self,
        ctf_results_data_sources: List[str],
        ctf_results_data: List[Dict[str, Any]],
        ctf_summary_data: List[Dict[str, Any]],
        ctf_summary_data_sources: List[str],
    ) -> None:
        """
        visualize iperf stream summary data as a table.
        visualize iperf stream results as a time series graph
        """
        series_list = []
        ctf_summary_table = {
            "title": "Iperf Summary Table",
            "data_source_list": ",".join(ctf_summary_data_sources),
        }
        for result_data_source in ctf_results_data_sources:
            series_info = {}
            series_info["data_source"] = result_data_source
            series_info["key"] = "Bandwidth Mbits/sec"
            # the results was appended to uniquify the results vs summary
            # the summary table uses the data source name directly and not
            # want to have 'summary' in the table
            series_info["label"] = result_data_source.split()[0]
            series_list.append(series_info)

        x_axis1 = {
            "key": "time interval",
            "options": {
                "label": "Interval ms",
                "type": "linear",
                "position": "bottom",
            },
        }
        y_axis1 = {
            "series_list": series_list,
            "options": {"label": "Bandwidth Mbits/sec", "fill": "false"},
        }
        chart_options = {"display_type": "line", "tension": "true"}
        ctf_results_chart = {
            "title": "Iperf Chart",
            "axes": {
                "x_axis1": x_axis1,
                "y_axis1": y_axis1,
            },
            "chart_type": "static",
            "options": chart_options,
        }

        ctf_json_data_all = {
            "ctf_tables": [ctf_summary_table],
            "ctf_charts": [ctf_results_chart],
            "ctf_data": ctf_summary_data + ctf_results_data,
        }
        self.save_ctf_json_data(ctf_json_data_all)

    def run_traffic(self, traffic_profile: List[Dict[str, Any]]) -> None:
        """Configure and run iperf streams on traffic generators according to
        the traffic_profile and visualize results. The traffic profile defines iperf input and threshold parameters.
        """
        futures: Dict = {}
        ctf_summary_data = []
        ctf_summary_data_sources = []
        ctf_results_data = []
        ctf_results_data_sources = []
        traffic_streams = self.configure_traffic_profile(traffic_profile)
        wait_time = 0

        # Launching parallel iperf streams
        for stream in traffic_profile:
            if wait_time < stream["time"]:
                wait_time = stream["time"] + 60

        traffic_thread_pool = ThreadPoolExecutor(
            thread_name_prefix="RunTrafficWorker",
            max_workers=2 * (len(traffic_streams.items())) + 1,
        )
        self.log_to_ctf(
            self.thread_log(
                f"Number of threads in thread pool {len(traffic_streams.items()) + 1}"
            )
        )

        success = 1

        for id, traffic_stream in traffic_streams.items():
            futures[
                traffic_thread_pool.submit(
                    self.run_iperf_stream,
                    server_cmd=traffic_stream[1],
                    client_cmd=traffic_stream[2],
                    run_time=traffic_stream[3],
                    step_idx=self.thread_local.step_idx,
                )
            ] = id

        # Waiting from iperf stream to run, collecting and processing results
        self.log_to_ctf(self.thread_log("traffic stream threads launched"))

        self.log_to_ctf(f"futures wait time is {wait_time}")
        for result in self.wait_for_cmds(futures, wait_time):
            if not result["success"]:
                err = self.thread_log(
                    f"iperf stream {result['message']['stream_name']} Failed to run, error: {result}"
                )
                if self.test_args["continue_run_traffic"]:
                    self.log_to_ctf(err, "error")
                    continue
                else:
                    raise DeviceCmdError(err)
                self.log_to_ctf(
                    self.thread_log(
                        f"iperf stream {result['message']['stream_name']} completed successfully"
                    )
                )
            # get iperf server logs
            cmd = f"cat /tmp/{result['message']['stream_name']}_server.txt"
            iperf_server_result = self.device_info[
                result["message"]["server_device_id"]
            ].action_custom_command(cmd, self.timeout)
            if iperf_server_result["error"]:
                err = f"iperf stream {result['message']['stream_name']}: Failed to collect iperf results"
                if self.test_args["continue_run_traffic"]:
                    self.log_to_ctf(err, "error")
                    continue
                else:
                    raise DeviceCmdError(err)

            self.log_to_ctf(f'{cmd}\n{iperf_server_result["message"]}')

            # parse iperf results
            iperf_results, iperf_summary = self.process_iperf_result(
                iperf_server_result["message"]
            )

            thresholds = result["message"]["threshold"]
            iperf_stream = result["message"]["stream_name"]
            expected_throughput = result["message"]["threshold"]["throughput"]
            throughput = iperf_summary["Bandwidth Mbits/sec"]
            self.log_to_ctf(
                f"iperf stream {iperf_stream} result summary: throughput {throughput} Mbps"
            )
            # validate threshold is met for expected throughput
            if throughput < expected_throughput:
                success = 0
                self.log_to_ctf(
                    f"iperf stream {iperf_stream} failed to meet threshold for throughput {expected_throughput}Mbps",
                    "error",
                )

            # validate threshold is met for expected lost datagrams
            if "lost_datagram_percentage" in iperf_summary.keys():
                expected_lost_datagrams = thresholds["lost datagrams"]
                lost_datagram_percentage = iperf_summary["lost_datagram_percentage"]
                self.log_to_ctf(
                    f"iperf stream {iperf_stream} result summary: lost packet percentage {lost_datagram_percentage}%"
                )
                if lost_datagram_percentage > expected_lost_datagrams:
                    success = 0
                    self.log_to_ctf(
                        f"iperf stream {iperf_stream} failed to meet threshold for expected lost datagrams {expected_lost_datagrams}%",
                        "error",
                    )

            data_source_name = result["message"]["stream_name"]
            summary_data = {
                "data_source": data_source_name,
                "data_list": [iperf_summary],
            }
            ctf_summary_data.append(summary_data)
            ctf_summary_data_sources.append(data_source_name)

            results_data_source_name = f"{data_source_name} results"
            results_data = {
                "data_source": results_data_source_name,
                "data_list": iperf_results,
            }
            ctf_results_data.append(results_data)
            ctf_results_data_sources.append(results_data_source_name)

            LOG.debug(
                f"iperf stream {result['message']['stream_name']}: finished iperf run"
            )
            self.log_to_ctf(f"{iperf_stream} completed running traffic")

        self.cleanupThreadPool(traffic_thread_pool)

        self.log_to_ctf(f"Iperf result summary: {ctf_summary_data}")
        self.visualize_iperf_results(
            ctf_results_data_sources,
            ctf_results_data,
            ctf_summary_data,
            ctf_summary_data_sources,
        )
        if not success:
            raise TestFailed(
                "Traffic run failed to meet required threshold values in one or more iperf streams"
            )
