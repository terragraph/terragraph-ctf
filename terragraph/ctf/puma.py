#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Library containing Puma-specific Terragraph test utilities.
"""

import functools
import ipaddress
import json
import logging
import operator
import subprocess
from argparse import Namespace
from concurrent.futures import as_completed
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep, time
from typing import Callable, cast, Dict, List, Optional, Set, Tuple

from ctf.ctf_client.runner.exceptions import (
    DeviceCmdError,
    DeviceConfigError,
    DeviceError,
    TestFailed,
    TestUsageError,
)
from terragraph.ctf.tg import BaseTgCtfTest, NODE_CONFIG_FILE

LOG = logging.getLogger(__name__)

FW_STATS = "fw_stats_ctf"
FW_STATS_DIR = "fw_stats_dir"
FW_STATS_PATH = f"/tmp/{FW_STATS_DIR}"
FW_STATS_OUTPUT_FILE = f"/tmp/{FW_STATS}"
FW_STATS_OUTPUT_FILE_COMPRESSED = f"{FW_STATS_OUTPUT_FILE}.gz"


class PumaDpMode(Enum):
    VPP = 1
    LINUX = 2


class PumaTgCtfTest(BaseTgCtfTest):
    """CTF Terragraph test base class extended with Puma-specific
    functionality.
    """

    # Container for KPIs per node_id
    # {node_id: {key:value, key:value, ...}, ...}
    kpi_container: Dict[int, Dict[str, int]]

    # Map of TG device node mac addresses to CTF node id's in the current setup
    # Enables the easy lookup of responder id's for running commands
    mac_to_node_id_map: Dict[str, int]

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.kpi_container = {}
        self.mac_to_node_id_map = {}

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        # NOTE: Python allows calling super() in static methods, but mypy has a
        # bug that throws an error here (which we suppress):
        #   super() requires one or more positional arguments in enclosing function
        test_params: Dict[str, Dict] = super(PumaTgCtfTest, PumaTgCtfTest).test_params()
        test_params["image_path"] = {
            "desc": (
                "If specified, upgrade nodes to the given software image "
                + "during the pre_run step"
            )
        }
        test_params["save_sysdump"] = {
            "desc": "When collecting logs, also save the sysdump from each node",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["disable_gps"] = {
            "desc": "If specified, disable GPS on the nodes",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["enable_fw_logs"] = {
            "desc": "If specified, enable firmware log collection",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        # NOTE: This is only set during the "init_nodes" (tg_init_nodes) step!
        # If this is supported in node config in the future, set it there...
        test_params["fw_log_level_fb"] = {
            "desc": (
                "Set the Facebook firmware logging level [debug, info, error, fatal] "
                + "(used when 'enable_fw_logs' is set)"
            ),
            "default": None,
        }
        test_params["fw_log_level_qti"] = {
            "desc": (
                "Set the QTI firmware logging level "
                + "[0:default of ERROR+WARN+INFO, 1:ERROR, 2:+WARN, 3:+INFO, 4:+VERBOSE] "
                + "(used when 'enable_fw_logs' is set)"
            ),
            "default": None,
            "convert": int,
        }
        test_params["enable_fw_stats"] = {
            "desc": "If specified, enable firmware stats collection",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["compress_fw_stats"] = {
            "desc": "Compress collected firmware stats with gzip",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["skip_reboot"] = {
            "desc": "Should we skip rebooting nodes during the pre-run step?",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["remove_python"] = {
            "desc": "Should we remove Python while running this test?",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["use_sw_htsf_sync"] = {
            "desc": (
                "If specified, set PPS timestamp source to SW-HTSF on all "
                + "nodes except 'htsf_sync_device_id'"
            ),
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["htsf_sync_device_id"] = {
            "desc": (
                "Use this Terragraph device ID as the time originator when "
                + "SW-HTSF sync is enabled ('use_sw_htsf_sync')"
            ),
            "default": 1,
            "convert": int,
        }
        test_params["htsf_sync_source"] = {
            "desc": (
                "Set the time source on 'htsf_sync_device_id' ('gps' or 'ptp') "
                + "when SW-HTSF sync is enabled ('use_sw_htsf_sync')"
            ),
            "default": "gps",
        }
        test_params["scribe_category_kpi_upload"] = {
            "desc": "If specified, upload KPIs to the provided Scribe category",
            "default": "",
        }
        test_params["upload_kpi_after_test"] = {
            "desc": (
                "If specified, upload KPIs only after the provided test class name. "
                + "scribe_category_kpi_upload must be specified to upload KPIs."
            ),
            "default": "",
        }
        test_params["bf_stats"] = {
            "desc": "If specified, enable beamforming stats collection during association",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        return test_params

    def get_common_test_steps(self) -> Dict:
        steps = super().get_common_test_steps()
        steps.update(
            {
                "add_loopback_ipv6_addr": {
                    "name": "Add IPv6 address to 'lo' interface",
                    "function": self.add_interface_addr,
                    "function_args": ("lo",),
                    "success_msg": "All nodes have been allocated static prefixes",
                },
                "init_nodes": {
                    "name": "Initialize node(s)",
                    "function": self.tg_init_nodes,
                    "function_args": (),
                    "success_msg": "All nodes are initialized",
                    "error_handler": self.get_common_error_handler(),
                },
                "assoc_terra_links": {
                    "name": "Bring up terra link(s)",
                    "function": self.tg_assoc_links,
                    "function_args": (),
                    "success_msg": "Successfully associated terra link(s)",
                    "error_handler": self.get_common_error_handler(),
                },
                "setup_l2_tunnels": {
                    "name": "Setup L2 tunnels",
                    "function": self.setup_l2_tunnel_config,
                    "function_args": (),
                    "success_msg": "L2 tunnels have been setup and configured.",
                },
                "disable_l2_tunnels": {
                    "name": "Disable L2 tunnels",
                    "function": self.disable_l2_tunnel_config,
                    "function_args": (),
                    "success_msg": "L2 tunnels have been disabled.",
                },
                "check_openr_adjacencies": {
                    "name": "Check for Open/R adjacencies",
                    "function": self.openr_adjacency_check,
                    "function_args": (),
                    "success_msg": "All nodes have an Open/R adjacency",
                },
                "check_timing_sync": {
                    "name": "Check timing synchronization mode",
                    "function": self.tg_check_sync,
                    "function_args": (),
                    "success_msg": "Synchronization mode matches configuration",
                },
            }
        )
        return steps

    # TODO: move this somewhere better
    def get_common_error_handler(self) -> List[Dict]:
        """Returns the common error handler steps."""
        return [
            {"function": self.inspect_vpp_vnet_logs, "function_args": ()},
            {"function": self.inspect_gps_stats, "function_args": ()},
            {"function": self.inspect_core_dumps, "function_args": ()},
            {"function": self.inspect_crash_logs, "function_args": ()},
        ]

    def collect_logfiles(self, logfiles: Dict[str, List[str]]) -> None:
        try:
            if self.test_args["enable_fw_logs"]:
                logfiles["terragraph"].append("/var/log/wil6210/")

            if self.test_args["enable_fw_stats"]:
                if self.test_args["compress_fw_stats"]:
                    logfiles["terragraph"].append(FW_STATS_OUTPUT_FILE_COMPRESSED)
                else:
                    logfiles["terragraph"].append(FW_STATS_OUTPUT_FILE)

            # if needed, run the sysdump script and collect the resulting archive
            if self.test_args["save_sysdump"]:
                sysdump_filename = f"/tmp/sysdump-ctf-{self.test_exe_id}.tgz"
                self.run_sysdump(sysdump_filename)
                logfiles["terragraph"].append(sysdump_filename)
        except Exception as e:
            self.log_to_ctf(f"Error preparing logfiles: {str(e)}", "error")

        super().collect_logfiles(logfiles)

    def pre_run(self) -> None:
        super().pre_run()

        # send and log all node configs
        TMP_CONFIG_PATH = "/tmp/ctf_base_config.json"
        self.generate_base_node_config(TMP_CONFIG_PATH)
        self.get_current_node_config(TMP_CONFIG_PATH)
        self.set_node_config(self.nodes_data)
        self.log_to_ctf(
            f"Full node configs:\n{json.dumps(self.node_configs, indent=2)}"
        )

        # if image path is found, and image is different than running versions,
        # upgrade image and verify, else reboot
        if self.test_args["image_path"] and self.check_image_upgrade_required(
            self.test_args["image_path"]
        ):
            self.run_image_upgrade_sequence(self.test_args["image_path"])
        else:
            if self.test_args["skip_reboot"]:
                self.log_to_ctf("Skipping reboot", "info")
            else:
                self.reboot_and_wait(self.device_info)

        if self.test_args["remove_python"]:
            self.set_python_usable(False)

        if self.test_args["enable_fw_stats"]:
            self.collect_fw_stats(
                start=True, compress=self.test_args["compress_fw_stats"]
            )

    def post_run(self) -> None:
        super().post_run()

        if self.test_args["enable_fw_stats"]:
            self.collect_fw_stats(start=False)

        if self.test_args["remove_python"]:
            self.set_python_usable(True)

        if self.test_args["scribe_category_kpi_upload"] != "":
            if (
                self.test_args["upload_kpi_after_test"] == self.__class__.__name__
                or self.test_args["upload_kpi_after_test"] == ""
            ):
                self.upload_node_kpis(self.test_args["scribe_category_kpi_upload"])
            else:
                self.log_to_ctf("Skipping KPI upload", "info")

    def nodes_data_amend_test_args(self, nodes_data: Dict, num_nodes: int) -> Dict:
        """Merge config overrides provided through test args."""
        merged_nodes_data = super().nodes_data_amend_test_args(nodes_data, num_nodes)

        if self.test_args["disable_gps"]:
            LOG.info("GPS is disabled on all nodes for this test")
            self.merge_dict(
                merged_nodes_data,
                {
                    i: {
                        "node_config": {
                            "radioParamsBase": {"fwParams": {"forceGpsDisable": 1}}
                        }
                    }
                    for i in range(1, num_nodes + 1)
                },
            )

        if self.test_args["enable_fw_logs"]:
            LOG.info("Enabling firmware logs on all nodes for this test")
            log_config = {"node_config": {"envParams": {"FW_LOGGING_ENABLED": "1"}}}
            if self.test_args["fw_log_level_qti"] is not None:
                qti_level = self.test_args["fw_log_level_qti"]
                if qti_level < 0 or qti_level > 4:
                    raise TestUsageError(
                        f"Invalid test argument 'fw_log_level_qti={qti_level}' (expecting 0-4)"
                    )
                self.merge_dict(
                    log_config,
                    {"node_config": {"envParams": {"FW_LOG_VERBOSE": str(qti_level)}}},
                )
            self.merge_dict(
                merged_nodes_data,
                {i: log_config for i in range(1, num_nodes + 1)},
            )

        # Configure OTA sync to use:
        # - GPS on first node
        # - SW-HTSF on all other nodes
        if self.test_args["use_sw_htsf_sync"]:
            d: Dict = {
                i: {
                    "node_config": {
                        "envParams": {"GPSD_ENABLED": "0"},
                        "timingParams": {"PPS_TIMESTAMP_SOURCE": "SW_HTSF"},
                    }
                }
                for i in range(1, num_nodes + 1)
            }
            ts_device_id: int = self.test_args["htsf_sync_device_id"]
            ts_source: str = self.test_args["htsf_sync_source"]
            if ts_source == "ptp":
                d[ts_device_id]["node_config"] = {
                    "envParams": {"GPSD_ENABLED": "0"},
                    "timingParams": {"PPS_TIMESTAMP_SOURCE": "PTP"},
                }
            elif ts_source == "gps":
                d[ts_device_id]["node_config"] = {
                    "envParams": {"GPSD_ENABLED": "1"},
                    "timingParams": {"PPS_TIMESTAMP_SOURCE": "GPS"},
                }
            else:
                raise TestUsageError(f"Invalid test-arg: htsf_sync_source={ts_source}")
            self.merge_dict(merged_nodes_data, d)

        return merged_nodes_data

    def secondary_step_action(self, test_action_result_id: int, step: Dict) -> None:
        super().secondary_step_action(test_action_result_id, step)
        # Allow test to continue even if stats collection fails
        try:
            self.get_heatmap_stats_for_assoc_step(test_action_result_id, step)
        # FIXME: Handle specific exceptions
        except Exception as e:
            error_msg = (
                f"secondary_step_action | caught {str(e)} in step {step['name']}"
            )
            self.log_to_ctf(error_msg, "warning")
        return

    def get_heatmap_stats_for_assoc_step(
        self, test_action_result_id: int, step: Dict
    ) -> None:
        """Get heatmap stats for all the links in given association step"""

        # Step can perform multiple association using tg_assoc_links or single association using minion_assoc
        # The initiator, responder and link information is derived from the function_args of respective functions.
        # Hence order of args is important.

        if (
            self.test_args["bf_stats"]
            and step["function"] == self.tg_assoc_links
            or step["function"] == self.minion_assoc
        ):
            self.log_to_ctf(
                f"Collecting heatmap stats for action {step['name']}: {test_action_result_id}",
                "info",
            )
            # node_ids will hold all nodes from which we need to collect stats
            node_ids: Set = set()
            # links will hold link information which will be used with tg_add_test_action_heatmap()
            links: List = []
            initiator_id = None
            # FIXME: Use a more robust way to find the initiator_id and the responder_id
            if step["function"] == self.minion_assoc:
                args = step["function_args"]
                initiator_id = args[0]
                responder_mac = args[2]
                responder_id = self._get_node_id(responder_mac)
                node_ids.update([initiator_id, responder_id])
                links.append(
                    {"initiator_id": initiator_id, "responder_id": responder_id}
                )
            else:
                args = step["function_args"]
                if args:
                    # FIXME: Find better way to fetch initiator_id and responder_id
                    initiator_id = args[0]
                node_ids, links = self._get_nodes_and_links_from_assoc_config(
                    initiator_id
                )

            link_info: Dict = {}
            link_info["node_ids"] = node_ids
            link_info["links"] = links
            self._fetch_heatmap_stats(test_action_result_id, step, link_info)

    def _get_nodes_and_links_from_assoc_config(
        self, initiator_id: Optional[int] = None
    ) -> Tuple[Set[int], List[Dict[str, int]]]:
        """Gets the unique initiator and responder node_ids from assoc config and
        link information which will hold initiator and responder id pairs.
        Returns
        {
            "node_ids": <unique list of node_ids>,
            "links": [{"initiator_id": <initiator_id>, "responder_id": <responder_id>}]
        }
        """
        nodes_data = self.nodes_data.items()
        # Get details associated with initiator_id only
        if initiator_id:
            nodes_data = {}
            nodes_data[initiator_id] = self.nodes_data[initiator_id]

        node_ids = set()
        links: List = []
        for node_id, v in nodes_data:
            if "assoc" not in v:
                continue
            node_ids.add(node_id)
            assoc = self.read_nodes_data([int(node_id), "assoc"])
            if "links" not in assoc:
                continue  # TODO Can this happen?
            for link in assoc["links"]:
                responder_id = self._get_node_id(link["responder_mac"])
                node_ids.add(responder_id)
                links.append({"initiator_id": node_id, "responder_id": responder_id})

        return (node_ids, links)

    def _fetch_heatmap_stats(
        self, test_action_result_id: int, step: Dict, link_info: Dict
    ) -> None:
        """Fetch heatmap stats to a local temp directory and push to CTF"""

        with TemporaryDirectory(prefix="heatmap_stats-") as tmp_dir:
            futures: Dict = {}
            for node_id in link_info["node_ids"]:
                device = self.device_info.get(node_id, None)
                if device is None:
                    raise TestUsageError(
                        f"_fetch_heatmap_stats | can't find CTF device info for node_id {node_id}"
                    )
                if device.device_type() != "terragraph":
                    LOG.info(
                        f"_fetch_heatmap_stats | skipping node {node_id} type {device.device_type()}"
                    )
                    continue
                futures[
                    self.thread_pool.submit(
                        self.fetch_files,
                        node_id,
                        device.connection,
                        [FW_STATS_PATH],
                        tmp_dir,
                        self.thread_local.step_idx,
                    )
                ] = node_id

            for future in as_completed(
                futures.keys(), timeout=self.log_collect_timeout
            ):
                result = future.result()
                node_id = futures[future]
                if result:
                    self.log_to_ctf(f"_fetch_heatmap_stats | node_id {node_id} ok")
                else:
                    # TODO Return a warning test step outcome instead of failing the entire test
                    raise DeviceCmdError(
                        f"_fetch_heatmap_stats | failed for node_id {node_id}"
                    )

            # Push heatmap (beamforming) stats to CTF
            futures.clear()
            links = link_info["links"]
            for link in links:
                link_name = f"{link['initiator_id']}_{link['responder_id']}"
                futures[
                    self.thread_pool.submit(
                        self._push_heatmap_stats_to_ctf,
                        tmp_dir,
                        test_action_result_id,
                        link,
                        self.thread_local.step_idx,
                    )
                ] = link_name

            for future in as_completed(
                futures.keys(), timeout=self.log_collect_timeout
            ):
                result = future.result()
                link_name = futures[future]
                if not result:
                    self.log_to_ctf(
                        f"Failed to push heatmap stats for link {link_name}",
                        "error",
                    )

    def _push_heatmap_stats_to_ctf(
        self,
        local_tmp_dir: str,
        test_action_result_id: int,
        link: Dict,
        step_idx: Optional[int] = None,
    ) -> bool:
        """Push heatmap stats from local temp dir to CTF"""

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        description = f"Link-{link['initiator_id']}-{link['responder_id']}"
        initiator_stats = f"{FW_STATS}_{link['initiator_id']}_link_{link['initiator_id']}_{link['responder_id']}"
        responder_stats = f"{FW_STATS}_{link['responder_id']}_link_{link['initiator_id']}_{link['responder_id']}"

        initiator_stats_path = Path(
            f"{local_tmp_dir}/{FW_STATS_DIR}/{Path(initiator_stats).name}"
        )
        responder_stats_path = Path(
            f"{local_tmp_dir}/{FW_STATS_DIR}/{Path(responder_stats).name}"
        )
        self.log_to_ctf(
            f"Pushing initiator {initiator_stats_path} and responder {responder_stats} to CTF for heatmaps"
        )

        result = self.ctf_api.save_heatmap_files(
            test_exe_id=self.test_exe_id,
            test_action_result_id=test_action_result_id,
            initiator_file_path=str(initiator_stats_path),
            responder_file_path=str(responder_stats_path),
            description=description,
        )

        if result["error"]:
            self.log_to_ctf(result["message"], "error")
            return False

        # TODO: Remove once heatmap logs can be pulled via "Download Action logs"
        self.ctf_api.save_action_log_file(
            source_file_path=str(initiator_stats_path),
            constructive_path=str(initiator_stats_path),
            test_exe_id=self.test_exe_id,
            test_action_result_id=test_action_result_id,
        )
        self.ctf_api.save_action_log_file(
            source_file_path=str(responder_stats_path),
            constructive_path=str(responder_stats_path),
            test_exe_id=self.test_exe_id,
            test_action_result_id=test_action_result_id,
        )

        return True

    def add_interface_addr(
        self, interface: str = "lo", node_ids: Optional[List[int]] = None
    ) -> None:
        """Add an IP address on the given interface for each node.

        Expects the following node data:
        ```
        {"<interface>": {"ip": "<ip>"}}
        ```
        """
        futures: Dict = {}
        for node_id in self.get_tg_devices():
            if node_ids and node_id not in node_ids:
                continue

            ip = self.read_nodes_data([node_id, interface, "ip"], False)
            if ip is None:
                continue

            self.log_to_ctf(f"Node {node_id}: adding {ip} on interface '{interface}'")

            cmd: str = f"/sbin/ip addr add {ip} dev {interface}"
            futures.update(self.run_cmd(cmd, [node_id]))

        for result in self.wait_for_cmds(futures):
            # Dont fail if the same IP already exists on the interface
            if not result["success"] and "File exists" not in result["error"]:
                raise DeviceCmdError(
                    f"Node {result['node_id']} failed to assign an IP prefix "
                    + f"to {interface}"
                )

    def add_vpp_interface_addr(self, prefix: Dict[int, str]) -> None:
        """Add an IP address on the given VPP interface for each node.

        Expects maps of interfaces and IPv6 prefixes indexed by node_id
        """
        futures: Dict = {}
        links = self.minion_get_link_status_dumps(self.get_tg_devices())
        for node_id in self.get_tg_devices():
            if node_id not in prefix:
                continue

            if len(links[node_id]) == 0:
                raise TestFailed(f"Node {node_id}: Could not find a link")
            if len(links[node_id]) > 1:
                raise TestFailed(f"Node {node_id}: Too many links for this test")

            link = next(iter(links[node_id].values()))
            ifname = link["ifname"]
            vpp_ifname = f"vpp-{ifname}"
            cmd: str = f"/usr/bin/vppctl set int ip addr {vpp_ifname} {prefix[node_id]}"
            self.log_to_ctf(
                f"Node {node_id}: Adding {prefix[node_id]} on VPP interface '{vpp_ifname}:'\n{cmd}"
            )

            futures.update(self.run_cmd(cmd, [node_id]))

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise DeviceCmdError(
                    f"Node {result['node_id']} failed to assign an IP prefix "
                    # pyre-fixme[61]: `vpp_ifname` may not be initialized here.
                    + f"to VPP interface {vpp_ifname}"
                )

    def vpp_ping(self, prefix: Dict[int, str]) -> None:
        """Ping over vpp

        Every given node will ping every address except itself.

        Expects maps of IPv6 prefixes indexed by node_id
        """
        # strip length portion of prefix if it exists
        address = {i: prefix[i].split("/")[0] for i in prefix}
        futures: Dict = {}
        for from_node in self.get_tg_devices():
            if from_node not in prefix:
                continue

            for to_node in self.get_tg_devices():

                if to_node not in prefix or from_node == to_node:
                    continue

                cmd: str = f"/usr/bin/vppctl ping {address[to_node]}"
                self.log_to_ctf(
                    f"Node {from_node}: Pinging node {address[to_node]}:\n{cmd}"
                )
                futures.update(self.run_cmd(cmd, [from_node]))

        for result in self.wait_for_cmds(futures):
            if not result["success"] or " 0 received" in result["message"]:
                raise DeviceCmdError(f"Node {result['node_id']} failed to ping")

    def run_iperf_vpp_to_vpp(
        self, prefix: Dict[int, str], min_tput_bps: float, time: int = 10
    ) -> None:
        """Run iperf from one Puma node to another and expect to meet the given
        throughput

        Expects maps of IPv6 prefixes indexed by node_id

        iperf is run between first and last nodes from the given dictionary of
        prefixes, sorted by node_id
        """

        server_id = min(self.get_tg_devices())
        client_id = max(self.get_tg_devices())

        server_ip = prefix[server_id].split("/")[0]

        cmd_timeout = max(self.timeout, time) + 10  # add buffer time

        server_cmd = "nohup /usr/bin/iperf_wrapper.sh -s --daemon --one-off"
        server_future = self.run_cmd(server_cmd, [server_id], timeout=cmd_timeout)
        result = next(self.wait_for_cmds(server_future, cmd_timeout))
        if result["error"]:
            raise DeviceCmdError(f"Running '{server_cmd}' failed: {result['error']}")

        client_cmd = f"/usr/bin/iperf_wrapper.sh -c {server_ip} -i 0 -t {time} --json"
        client_future = self.run_cmd(client_cmd, [client_id], timeout=cmd_timeout)
        result = next(self.wait_for_cmds(client_future, cmd_timeout))

        self.log_to_ctf(f"{client_cmd}\n{result['message']}")

        if result["error"]:
            # iperf will print the following warning to stderr, but that is not a reason to fail
            # warning: Ignoring nonsense TCP MSS 0
            self.log_to_ctf(f"{client_cmd}\n{result['error']}")

        log = json.loads(result["message"])
        if (
            "end" not in log
            or "sum_received" not in log["end"]
            or "bits_per_second" not in log["end"]["sum_received"]
        ):
            raise TestFailed("Failed to obtain throughput results")

        tput = log["end"]["sum_received"]["bits_per_second"]
        self.kpi_container.setdefault(server_id, {})["throughput_bps"] = tput
        if tput < min_tput_bps:
            raise TestFailed(f"iperf throughput too low: {tput} < {min_tput_bps}")

    def get_all_node_mac(self, node_ids: Optional[List[int]] = None) -> Dict[int, str]:
        """Get the MAC address of TG nodes.
        Returns a mapping between node ID and MAC address.
        """
        node_info_cmd = "get_hw_info NODE_ID"
        futures: Dict = self.run_cmd(node_info_cmd, node_ids)
        mac_addrs: Dict[int, str] = {}
        for result in self.wait_for_cmds(futures):
            if result["error"]:
                self.log_to_ctf(f"{node_info_cmd}\n{result['error']}")
                continue
            mac_addrs[result["node_id"]] = result["message"].strip()
        return mac_addrs

    def _get_mac_to_node_id_map(self) -> Dict[str, int]:
        """Get TG radio mac address to node-id map"""

        status_cmd = "tg2 minion status --json"
        futures: Dict = self.run_cmd(status_cmd)
        mac_map: Dict[str, int] = {}
        for result in self.wait_for_cmds(futures):
            node_id = result["node_id"]
            if result["error"]:
                raise DeviceCmdError(
                    f"{status_cmd} failed on node-id {node_id} error {result['error']}"
                )
                continue
            radios = self._parse_tg2_json(result["message"])["radioStatus"]
            for r in radios:
                if r in mac_map.keys():
                    raise DeviceCmdError(
                        f"Radio mac address {r} is duplicated in node {node_id} and node {mac_map[r]}"
                    )
                else:
                    mac_map[r] = node_id
        self.log_to_ctf(f"radio mac to node-id map {mac_map}", "info")
        return mac_map

    def _get_node_id(self, mac_addr: str) -> int:
        """Get node id for a given mac address."""
        node_id = self.mac_to_node_id_map.get(mac_addr, None)
        if not node_id:
            raise DeviceError(f"Unknown sector mac address {mac_addr}")
        return node_id

    def get_all_system_stats(
        self,
        stats_to_display_name: Dict[str, str],
        node_ids: Optional[List[int]] = None,
    ) -> Dict[int, Dict[str, float]]:
        """Get system stats from nodes.
        Returns a map of node ID to collected stats.
        """
        dump_stats_cmd = "tg2 stats --dump system"
        futures: Dict = self.run_cmd(dump_stats_cmd, node_ids)
        all_stats: Dict[int, Dict[str, float]] = {}
        for result in self.wait_for_cmds(futures):
            if result["error"]:
                self.log_to_ctf(f"{dump_stats_cmd}\n{result['error']}")
                continue
            stats = {}
            lines = result["message"].splitlines()
            for line in lines:
                tokens = line.split(",")
                key = tokens[1].strip()
                if key in stats_to_display_name:
                    value = float(tokens[2].strip())
                    stats[stats_to_display_name[key]] = value
            all_stats[result["node_id"]] = stats

        return all_stats

    def upload_node_kpis(self, scribe_category: str) -> None:
        """Get and upload the node KPIs to Scuba."""
        stats_to_display_name = {
            # memory utilization %
            "mem.util": "mem_util",
            # 1-min CPU load average
            "load-1": "cpu_load",
            # per-core CPU utilization %
            "core_0.cpu.util": "cpu_util_core_0",
            "core_1.cpu.util": "cpu_util_core_1",
            "core_2.cpu.util": "cpu_util_core_2",
            "core_3.cpu.util": "cpu_util_core_3",
            # process-specific memory/CPU utilization %
            "e2e_minion.cpu.util": "e2e_minion-cpu_util",
            "e2e_minion.mem.util": "e2e_minion-mem_util",
            "openr.cpu.util": "openr-cpu_util",
            "openr.mem.util": "openr-mem_util",
            "stats_agent.cpu.util": "stats_agent-cpu_util",
            "stats_agent.mem.util": "stats_agent-mem_util",
        }
        all_node_mac = self.get_all_node_mac()
        all_sys_stats = self.get_all_system_stats(stats_to_display_name)

        ts = int(time())
        for node_id in self.get_tg_devices():
            # construct scribe command
            # - "int": integer numbers (MUST include "time")
            # - "double": floating-point numbers
            # - "normal": strings
            msg = {}
            msg["normal"] = {"Node MAC": all_node_mac.get(node_id)}
            msg["int"] = {"time": ts}
            msg["double"] = {}
            msg["double"].update(all_sys_stats.get(node_id, {}))
            msg["double"].update(self.kpi_container.get(node_id, {}))
            scribe_cmd = "scribe_cat {} {}".format(
                scribe_category, json.dumps(json.dumps(msg))
            )

            # log stats to CTF
            self.log_to_ctf(f"Uploading KPIs to {scribe_category}: {msg}")
            # issue scribe command
            cmd_output = subprocess.getoutput(scribe_cmd)
            # log command and result to CTF
            self.log_to_ctf(f"{scribe_cmd}\n{cmd_output}")

    def openr_adjacency_check(self) -> None:
        """Verify that Open/R adjacencies have formed on all test devices."""
        futures: Dict = self.run_cmd("/usr/sbin/puff decision adj | grep terra")
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise TestFailed(
                    f"Node {result['node_id']} does not have an Open/R adjacency"
                )

            self.log_to_ctf(
                f"Node {result['node_id']} finished checking Open/R adjacency:\n"
                + f"{result['message'].strip()}"
            )

    def get_datapath_mode(self, node_id: int) -> PumaDpMode:
        """Get DP mode - VPP or Linux Kernel."""
        # Since this config is default, directly access the keys
        dpdk_enabled = self.node_configs[node_id]["envParams"]["DPDK_ENABLED"]
        return PumaDpMode.VPP if dpdk_enabled == "1" else PumaDpMode.LINUX

    @functools.lru_cache(maxsize=64, typed=True)
    def is_node_pop(self, node_id: int = 1) -> bool:
        """Use valid PopAddr and tap1 interface prefix as
        the check for POP.
        """

        # Check if popAddr from config matches tap1 interface
        popAddr = self.read_nodes_data(
            [node_id, "node_config", "popParams", "POP_ADDR"], required=False
        )

        if popAddr:
            # Wait for VPP-tap or linux interface bridged to 10G
            # to come up. Futures will timeout/fail in 60 seconds.
            # vpp mode - tap1 interface
            # linux kernel mode - nic1 interface.
            pop_intf = (
                "tap1" if self.get_datapath_mode(node_id) == PumaDpMode.VPP else "nic1"
            )
            wait_pop_intf = (
                f"while ! ip addr show | grep {pop_intf}; do sleep 1;"
                + "echo waiting for pop intf...; done"
            )
            futures = self.run_cmd(wait_pop_intf, [node_id])
            for result in self.wait_for_cmds(futures):
                if not (pop_intf or "UP") in result["message"]:
                    return False

            # Verified tap1 is up, check prefix
            ip_addr_map = self.get_ip([node_id], pop_intf)
            pop_ipv6 = ip_addr_map[node_id]
            if pop_ipv6 == popAddr:
                return True

        return False

    # TODO - Get GW IP from appropriate POP for the particular DN/CN
    def get_gw_ip(self) -> str:
        """Get GW IP address from the first POP."""

        # Find the first POP and return GW address
        for node_id in self.get_tg_devices():
            if self.is_node_pop(node_id):
                gw_addr = self.read_nodes_data(
                    [node_id, "node_config", "popParams", "GW_ADDR"]
                )
                if not gw_addr:
                    raise TestFailed("GW IP is empty!")
                return str(gw_addr)

        raise TestFailed("No POPs, no GW")

    def verify_pop_bgp_config(self) -> None:
        """Verify there is at least one POP with a BGP config."""

        for node_id in self.get_tg_devices():
            if self.is_node_pop(node_id):
                if self.read_nodes_data(
                    [node_id, "node_config", "bgpParams"], required=False
                ):
                    # Found a valid POP with BGP config, bail
                    return

        # No Valid POPs found
        raise TestFailed("No POPs found - Check POP and BGP config")

    def bgp_exabgp_default_route_check(self, retry: int = 5) -> None:
        """Verify on POP ExaBGP's RIB has a learned default
        route to upstream router.
        """
        while retry > 0:
            cmd = "/usr/bin/exabgpcli show adj-rib in | grep 'ipv6 unicast ::/0'"
            futures: Dict = self.run_cmd(
                cmd, [id for id in self.get_tg_devices() if self.is_node_pop(id)]
            )

            for result in self.wait_for_cmds(futures):
                no_default = False
                if not result["success"]:
                    LOG.debug(
                        f"Node {result['node_id']} ExaBGP does not have a"
                        + "BGP default routes, retrying ..."
                    )
                    no_default = True

            retry -= 1
            # pyre-fixme[61]: `no_default` may not be initialized here.
            if not no_default:
                LOG.debug(
                    f"Node {result['node_id']} finished checking ExaBGP"
                    + " default routes"
                )
                self.log_to_ctf(result["message"])
                break
            elif retry > 0:
                continue
            else:
                raise TestFailed(
                    f"Node {result['node_id']} ExaBGP does not have a BGP default route"
                )

    def bgp_frr_bgpd_default_route_check(self) -> None:
        """Verify on POP FRR bgpd's RIB has a learned default
        route to upstream router.
        """
        cmd = "/usr/bin/vtysh -c 'show bgp' | grep '*> ::/0'"
        futures: Dict = self.run_cmd(
            cmd, [id for id in self.get_tg_devices() if self.is_node_pop(id)]
        )
        failed_nodes = []
        for result in self.wait_for_cmds(futures):
            if result["success"]:
                self.log_to_ctf(result["message"])
                self.log_to_ctf(
                    f"Node {result['node_id']}: Found BGP default route and next hop via FRR bgpd"
                )
            else:
                failed_nodes.append(result["node_id"])
        if failed_nodes:
            raise TestFailed(
                f"FRR bgpd missing BGP default route on the following nodes: {failed_nodes}"
            )

    def bgp_openr_default_route_check(self) -> None:
        """Verify on DN/CN that Open/R RIB has a learned default
        route to upstream router.
        """

        # If DN or CN, look for BGP default route in Open/R
        cmd = "/usr/sbin/puff decision routes | grep '::/0'"
        futures: Dict = self.run_cmd(
            cmd, [id for id in self.get_tg_devices() if not self.is_node_pop(id)]
        )

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise TestFailed(
                    f"Node {result['node_id']}: Open/R does not have a BGP default route"
                )

            LOG.debug(
                f"Node {result['node_id']}: finished checking Open/R default routes"
            )
            self.log_to_ctf(result["message"])

    def bgp_default_route_check(self) -> None:
        """Check default route for valid next hop in
        both VPP and Linux FIBs based on node config.
        """

        dp_mode_nodes: Dict[PumaDpMode, List[int]] = {
            PumaDpMode.VPP: [],
            PumaDpMode.LINUX: [],
        }
        for id in self.get_tg_devices():
            dp_mode_nodes[self.get_datapath_mode(id)].append(id)

        if dp_mode_nodes[PumaDpMode.VPP]:
            self.bgp_vpp_default_route_check(dp_mode_nodes[PumaDpMode.VPP])

        if dp_mode_nodes[PumaDpMode.LINUX]:
            self.bgp_linux_kernel_default_route_check(dp_mode_nodes[PumaDpMode.LINUX])

    def bgp_linux_kernel_default_route_check(self, node_ids: List[int]) -> None:
        """Check Linux FIB default route for valid next hop."""

        # All nodes should have a valid next hop in Linux FIB/
        # route table but only check POP's next hop for validity
        # as it's easy to cross check with GW address config

        fib_linux_cmd = "ip route show table all | grep default"
        futures: Dict = self.run_cmd(
            fib_linux_cmd, [id for id in node_ids if self.is_node_pop(id)]
        )

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise TestFailed(
                    f"Node {result['node_id']} Linux FIB does not have"
                    + " a BGP default route"
                )
            next_hop = result["message"].split("via ")[1].split()[0]

            gw_addr = self.read_nodes_data(
                [result["node_id"], "node_config", "popParams", "GW_ADDR"]
            )
            # Match the next_hop with configured GW_ADDR
            if gw_addr != next_hop:
                raise TestFailed(
                    f"Node {result['node_id']} Linux FIB default route"
                    + " next-hop is invalid!"
                )

            LOG.debug(
                f"Node {result['node_id']} finished checking Linux FIB"
                + " default routes and next hops"
            )
            self.log_to_ctf(
                f"Node {result['node_id']} Linux FIB\n" + f"{result['message']}", "info"
            )

    def bgp_vpp_default_route_check(self, node_ids: List[int]) -> None:
        """Check VIP FIB default route for valid next hop."""

        # All nodes should have a valid next hop in VPP FIB
        # but only check POP's next hop for validity for now
        # as it's easy to cross check with GW address config
        fib_vpp_cmd = "vppctl show ip6 fib | grep -A4 '::/0'"
        futures: Dict = self.run_cmd(
            fib_vpp_cmd, [id for id in node_ids if self.is_node_pop(id)]
        )

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise TestFailed(
                    f"Node {result['node_id']} VPP FIB does not have"
                    + " a BGP default route"
                )
            next_hop = result["message"].split("via ")[1].split()[0]

            gw_addr = self.read_nodes_data(
                [result["node_id"], "node_config", "popParams", "GW_ADDR"]
            )
            # Match the next_hop with configured GW_ADDR
            if gw_addr != next_hop:
                raise TestFailed(
                    f"Node {result['node_id']} VPP FIB default route"
                    + " next-hop is invalid!"
                )

            LOG.debug(
                f"Node {result['node_id']} finished checking VPP FIB"
                + " default routes and next hops"
            )
            self.log_to_ctf(
                f"Node {result['node_id']} VPP FIB\n" + f"{result['message']}", "info"
            )

    def vxlan_vpp_check(
        self,
        node_ids: Optional[List[int]] = None,
    ) -> None:
        """Check VxLAN L2 tunnels are properly configured on source and
        destination nodes. Expects `tunnel_destinations` in node data and
        `tunnelParams.vlanId` under `tunnelConfig` in the node configuration."""

        ip_addr_map = self.get_ip(interface="lo", ip_type="global")

        for src_node_id in self.get_tg_devices():
            dst_nodes = self.read_nodes_data([src_node_id, "tunnel_destinations"])
            if not dst_nodes:
                continue
            vpp_vxlan_endpoints = self.get_vpp_vxlan_endpoints(src_node_id)

            for dst_id in dst_nodes:
                # In VPP/vpp_chaperone, the VxLAN tunnel endpoints are formed
                # between the VPP loopback IPs.
                ipaddr = ipaddress.ip_address(ip_addr_map[src_node_id]).exploded
                config_src_endpoint = str(ipaddress.ip_address(ipaddr[:-4] + "0002"))
                ipaddr = ipaddress.ip_address(ip_addr_map[dst_id]).exploded
                config_dst_endpoint = str(ipaddress.ip_address(ipaddr[:-4] + "0002"))

                # Validate config and VPP VxLAN IPs match for each tunnel.
                # Check 1 - Config destination endpoint is configured in VPP
                if config_dst_endpoint not in vpp_vxlan_endpoints:
                    raise TestFailed(
                        f"Node {src_node_id} tunnel destination endpoint "
                        + f"{config_dst_endpoint} is not configured in VPP {vpp_vxlan_endpoints}"
                    )

                # Check 2 - source endpoints match
                if vpp_vxlan_endpoints[config_dst_endpoint] != config_src_endpoint:
                    raise TestFailed(
                        f"Node {src_node_id} tunnel source endpoint "
                        + f"{vpp_vxlan_endpoints[config_dst_endpoint]} "
                        + f"does not match node config {config_src_endpoint}"
                    )

                self.log_to_ctf(
                    f"VxLAN tunnels and config match {vpp_vxlan_endpoints[config_dst_endpoint]}: "
                    + f"{config_dst_endpoint}"
                )

    def srv6_vpp_check(
        self,
        node_ids: Optional[List[int]] = None,
        source_encap_base: int = 1001,
        dest_decap_base: int = 2001,
    ) -> None:
        """Check SRv6 L2 encap and decap policies are properly
        configured on source and destination nodes. Expects `tunnel_destinations`
        in node data and `tunnelParams.vlanId` under `tunnelConfig` in the
        node configuration."""

        ip_addr_map = self.get_ip(interface="lo", ip_type="global")

        for src_node_id in self.get_tg_devices():
            dst_nodes = self.read_nodes_data([src_node_id, "tunnel_destinations"])
            if not dst_nodes:
                continue
            vpp_srv6_sids = self.get_vpp_srv6_sids(src_node_id)

            for dst_id in dst_nodes:
                tunnel_config = self.read_nodes_data(
                    [src_node_id, "node_config", "tunnelConfig", str(dst_id)]
                )
                # In VPP/vpp_chaperone, the unique source/destination tunnel IPs
                # are derived by adding the VLAN ID to source/destination base
                # hextexts and joining with the node's /64 prefix.

                ipaddr = ipaddress.ip_address(ip_addr_map[src_node_id]).exploded
                config_src_sid = str(
                    ipaddress.ip_address(
                        ipaddr[:-4]
                        + str(
                            source_encap_base
                            + int(tunnel_config["tunnelParams"]["vlanId"])
                        )
                    )
                )

                ipaddr = ipaddress.ip_address(ip_addr_map[dst_id]).exploded
                config_dst_sid = str(
                    ipaddress.ip_address(
                        ipaddr[:-4]
                        + str(
                            dest_decap_base
                            + int(tunnel_config["tunnelParams"]["vlanId"])
                        )
                    )
                )
                # Validate config and VPP Segment IDs match for each tunnel.
                # Check 1 - Config destination SID is actually configured in VPP
                if config_dst_sid not in vpp_srv6_sids:
                    raise TestFailed(
                        f"Node {src_node_id} tunnel destination SID {config_dst_sid} "
                        + "is not configured in VPP"
                    )

                # Check 2 - source SID match
                if vpp_srv6_sids[config_dst_sid] != config_src_sid:
                    raise TestFailed(
                        f"Node {src_node_id} tunnel source SID {vpp_srv6_sids[config_dst_sid]} "
                        + f"does not match node config {config_src_sid}"
                    )

                self.log_to_ctf(
                    f"SRv6 tunnel policies and config match {vpp_srv6_sids[config_dst_sid]}: {config_dst_sid}"
                )

    def get_vpp_srv6_sids(self, node_id: int) -> Dict[str, str]:
        """Queries VPP for SRv6 policies of a given node. Returns a map of
        destination (decap) SID to source (encap) SID for each tunnel."""

        cmd: str = '/usr/bin/vppctl show sr policies | grep "].-"'
        tunnel_sids: Dict[str, str] = {}
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to get SRv6 policies: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            output = result["message"].splitlines()
            # The VPP command output contains source and destination SIDs
            # for each tunnel every 2 lines. Output is something like below.
            # [0].-   BSID: 2620:10d:c089:3388::1101
            #        [0].- < 2620:10d:c089:3389::2101 > weight: 1

            for idx in range(0, len(output), 2):
                try:
                    src_sid = output[idx].strip().split("BSID: ")[1]
                    dst_sid = (
                        output[idx + 1]
                        .strip()
                        .split("< ")[1]
                        .split(" >")[0]
                        .split(",")[0]
                    )
                    tunnel_sids[dst_sid] = src_sid
                except Exception:
                    raise DeviceCmdError(f"Failed to parse VPP SRv6 output: {output}")

        return tunnel_sids

    def get_vpp_vxlan_endpoints(self, node_id: int) -> Dict[str, str]:
        """Queries VPP for VxLAN tunnels in a given node. Returns a map of
        destination (decap) endpoints to source (encap) endpoints for each tunnel."""

        cmd: str = '/usr/bin/vppctl show vxlan tunnel | grep "instance"'
        tunnel_endpoints: Dict[str, str] = {}
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to get VxLAN policies: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            output = result["message"].splitlines()
            # The VPP command output is something like below.
            # vppctl show vxlan tunnel
            # instance 0 src 2620:10d:c089:3388::2 dst 2620:10d:c089:3389::2 ...

            for line in output:
                try:
                    src_endpoint = line.split()[4]
                    dst_endpoint = line.split()[6]
                    tunnel_endpoints[dst_endpoint] = src_endpoint
                except Exception:
                    raise DeviceCmdError(f"Failed to parse VPP VxLAN output: {output}")

        return tunnel_endpoints

    def verify_ping_upstream(self, node_ids: Optional[List[int]] = None) -> None:
        """Verify that each node can ping upstream to a GW."""
        gw_addr = self.get_gw_ip()
        for node_id in self.get_tg_devices():
            if node_ids and node_id not in node_ids:
                continue

            # Ping GW first
            self.ping_ip(node_id, gw_addr)

            # Ping the upstream router IP from config
            router_addr = self.read_nodes_data([node_id, "router_ip"])
            self.ping_ip(node_id, router_addr)
            # If pings fail, base ping APIs will raise exception

    def gps_enable_if_needed(self, node_id: int):
        """Enable GPS on a given node if `forceGpsDisable` is not set."""
        fw_params = self.read_nodes_data(
            [node_id, "node_config", "radioParamsBase", "fwParams"], required=False
        )
        if fw_params and fw_params.get("forceGpsDisable", None) == 1:
            self.log_to_ctf("GPS is disabled")
        else:
            self.minion_gps_enable([node_id])

    def minion_gps_enable(self, node_ids: Optional[List[int]] = None) -> None:
        """Issue a GPS enable command to the given node(s), or all nodes if
        omitted.
        """
        futures: Dict = self.run_cmd("/usr/sbin/tg2 minion gps_enable", node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to enable GPS: {result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"GPS enable command sent to node {result['node_id']}")

    def send_node_params(
        self,
        node_id: int,
        mac_addr: Optional[str] = None,
        channel: Optional[int] = None,
        polarity: Optional[int] = None,
    ) -> None:
        """Send node parameters to the given node."""
        opts = []
        if mac_addr is not None:
            opts.append(f"-m {mac_addr}")
        if channel is not None:
            opts.append(f"-c {channel}")
        if polarity is not None:
            opts.append(f"-p {polarity}")
        cmd: str = f"/usr/sbin/tg2 minion set_params {' '.join(opts)}"

        self.log_to_ctf(f"Sending node params to node {node_id}: {cmd}")
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to set node params: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"Node params sent to node {result['node_id']}")

    def minion_set_fb_fw_log_config(self, node_ids: List[int], level: str) -> None:
        """Set the Facebook firmware log level.

        Supported levels: `debug`, `info`, `error`, `fatal`
        """
        cmd: str = f"/usr/sbin/tg2 minion fw_set_log_config -l {level}"

        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to set FB firmware log level: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")

            self.log_to_ctf(
                f"Set FB firmware log level on node {result['node_id']} to '{level}'"
            )

    def setup_l2_tunnel_config(self) -> None:
        """Fill in missing tunnel config and setup L2 tunnels between nodes. Expects
        `tunnel_destinations` field in node data per node."""

        config_pending_nodes: List[int] = []
        ip_addr_map = self.get_ip(interface="lo", ip_type="global")

        for src_node_id in self.get_tg_devices():
            dst_nodes = self.read_nodes_data([src_node_id, "tunnel_destinations"])
            if not dst_nodes:
                continue

            config_pending_nodes.append(src_node_id)
            self.log_to_ctf(
                f"Node {src_node_id}: tunnel destination nodes '{dst_nodes}'"
            )
            # Query tunnel destination IP and update the tunnel config runtime.
            for dst_id in dst_nodes:
                dst_ip = ip_addr_map[dst_id]
                config_sub_cmd: str = f" -s tunnelConfig.{dst_id}.dstIp {dst_ip}"
                self.modify_node_config_runtime(config_sub_cmd, [src_node_id])
                self.log_to_ctf(f"Tunnel config sent to node {src_node_id}")

                config_sub_cmd: str = f" -b tunnelConfig.{dst_id}.enabled true"
                self.modify_node_config_runtime(config_sub_cmd, [src_node_id])
                self.log_to_ctf(f"Sent tunnel disable config to node {src_node_id}")

        self.sync_node_config_runtime(config_pending_nodes)

    def disable_l2_tunnel_config(self) -> None:
        """Overwrite 'enabled' field in 'tunnelConfig' to be false, and disable tunnels."""

        config_pending_nodes: List[int] = []

        for src_node_id in self.get_tg_devices():
            dst_nodes = self.read_nodes_data([src_node_id, "tunnel_destinations"])
            if not dst_nodes:
                continue

            config_pending_nodes.append(src_node_id)

            for dst_id in dst_nodes:
                config_sub_cmd: str = f" -b tunnelConfig.{dst_id}.enabled false"
                self.modify_node_config_runtime(config_sub_cmd, [src_node_id])
                self.log_to_ctf(f"Sent tunnel disable config to node {src_node_id}")

        self.sync_node_config_runtime(config_pending_nodes)

    def modify_node_config_runtime(
        self,
        config_sub_cmd: str,
        node_ids: Optional[List[int]] = None,
    ) -> None:
        """Modify node config at runtime using `config_set` utility.
        Accepts the configuration subcommand like "-i envParams.DPDK_ENABLED 0"."""

        base_cmd: str = f"/usr/sbin/config_set -n {NODE_CONFIG_FILE} "

        futures: Dict = self.run_cmd(base_cmd + config_sub_cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to set node config: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"Runtime config sent to node {result['node_id']}")

    def sync_node_config_runtime(self, node_ids: Optional[List[int]] = None) -> None:
        """Sync node config by sending a command to trigger config actions"""

        cmd: str = "/usr/sbin/tg2 minion set_node_config"
        self.log_to_ctf(f"Syncing node config {node_ids}: {cmd}")
        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to sync node config: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

    def _parse_tg2_json(self, s: str) -> Dict:
        """Parse `tg2` CLI JSON output."""
        try:
            return cast(Dict, json.loads(s))
        except Exception:
            raise DeviceCmdError(f"Failed to parse tg2 JSON output: {s}")

    def minion_get_link_status_dumps(self, node_ids: List[int]) -> Dict[int, Dict]:
        """Retrieve the link status dump from e2e_minion on the given nodes.

        This returns a map from node IDs to thrift::LinkStatusDump.
        """
        cmd = "/usr/sbin/tg2 minion links --json"
        futures = self.run_cmd(cmd, node_ids)
        ret: Dict[int, Dict] = {}
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: '{cmd}' failed: {result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            output = result["message"]
            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{output}")
            ret[result["node_id"]] = self._parse_tg2_json(output)["linkStatusDump"]

        return ret

    def minion_get_link_interface(
        self, node_id: int, initiator_mac: str, responder_mac: str
    ) -> str:
        """Verify that a given link is up according to e2e_minion, and return
        the (terra) network interface name.
        """
        dump = self.minion_get_link_status_dumps([node_id])[node_id]
        if (
            responder_mac not in dump
            or dump[responder_mac]["radioMac"] != initiator_mac
        ):
            error_msg = (
                "Link up check failed (link not found: "
                + f"'{initiator_mac}' -> '{responder_mac}')"
            )
            self.log_to_ctf(error_msg, "error")
            raise TestFailed(error_msg)

        return str(dump[responder_mac]["ifname"])

    def minion_get_status(self, node_ids: Optional[List[int]] = None) -> Dict:
        """Retrieve the status report from e2e_minion on the given nodes.

        This returns a map from node IDs to thrift::StatusReport.
        """
        cmd: str = "/usr/sbin/tg2 minion status --json"
        futures = self.run_cmd(cmd, node_ids)
        statuses: Dict[int, Dict] = {}
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                # let caller handle errors (might want to retry later)
                self.log_to_ctf(f"{cmd}\n{result['error']}", "error")
                continue

            self.log_to_ctf(f"{cmd}\n{result['message']}")
            statuses[result["node_id"]] = self._parse_tg2_json(result["message"])

        return statuses

    def verify_nodes_ready(self, node_ids: List[int], init_retries: int = 10) -> None:
        """Verify that the given nodes are initialized and radios
        are configured, with multiple retries. If at least one
        of the nodes' radios are not configured, we will timeout
        after init_retries attempts.
        """
        node_check_list = node_ids
        retries = init_retries
        while retries > 0:
            self.log_to_ctf(
                f"Check if nodes {node_check_list} are ready"
                + f" (remaining retries: {retries})",
                "info",
            )
            statuses = self.minion_get_status(node_check_list)
            for node_id, status in statuses.items():
                if "radioStatus" not in status or not status["radioStatus"]:
                    continue

                radio_status = status["radioStatus"]
                ready = True
                for mac in radio_status.keys():
                    # If a radio is not ready, skip this node
                    if not radio_status[mac]["initialized"]:
                        ready = False
                        break
                if ready:
                    # all radios are configured, no need to check this node again
                    node_check_list.remove(node_id)
                    continue

            # One or more nodes are still not ready, check again
            if node_check_list:
                # We probably still want to sleep for a second even though
                # the futures + result processing does shave off few seconds
                sleep(1)
                retries -= 1
            else:
                break

        # Timed out with at least one node not ready
        if node_check_list and not retries:
            raise DeviceCmdError(
                f"Nodes {node_check_list} failed to init minion/radios"
                + f" after {init_retries} attempts"
            )

        self.log_to_ctf("All nodes are configured and ready", "info")

    def tg_init_nodes(self) -> None:
        """Initialize all Terragraph devices and wait until they are ready.

        Specifically:
        1. Wait for e2e_minion to report that radios are initialized on all
           Terragraph devices.
        2. If the `fw_log_level_fb` test arg is set, configure it on all
           Terragraph devices.
        3. Configure the wireless channel and enable GPS (if needed) for
           every initiator.
        """
        node_ids: List[int] = self.get_tg_devices()

        # Wait for minion to initialize on all nodes
        self.verify_nodes_ready(node_ids)

        # Set FB firmware log level if needed
        if self.test_args["enable_fw_logs"] and self.test_args["fw_log_level_fb"]:
            self.minion_set_fb_fw_log_config(
                node_ids, self.test_args["fw_log_level_fb"]
            )

        # Set the channel and enable GPS on all initiator nodes
        initiator_id = None
        for node_id, v in self.nodes_data.items():
            if "assoc" not in v:
                continue

            # Validate the initiator_id
            initiator_id = int(node_id)
            if initiator_id not in self.device_info:
                err = f"Unable to find initiator node ID {initiator_id}"
                self.log_to_ctf(err, "error")
                raise TestUsageError(err)

            # Read data from "assoc" config
            assoc_conf = self.read_nodes_data([initiator_id, "assoc"])
            initiator_mac = assoc_conf.get("initiator_mac", None)
            channel = assoc_conf.get("channel", 2)

            # Set channel
            self.send_node_params(initiator_id, mac_addr=initiator_mac, channel=channel)

            # Enable GPS
            self.gps_enable_if_needed(initiator_id)

        # Wait for params to take effect (e.g. before trying assoc)
        if initiator_id is not None:
            sleep(1)

        # If necessary, initialize the mac address to node-id map.
        if self.test_args["bf_stats"]:
            self.mac_to_node_id_map = self._get_mac_to_node_id_map()

    def find_initiator_id(self) -> Optional[int]:
        """Find the id of the initiator node. Raise an exception if
        there are multiple initiators in self.nodes_data.
        """
        id = None
        for node_id, v in self.nodes_data.items():
            if "assoc" in v:
                if id is None:
                    id = int(node_id)
                else:
                    err = "Multiple initiator IDs found"
                    LOG.debug(err)
                    raise DeviceConfigError(err)
        return id

    def __get_initiator_node_order(self) -> List[Tuple[int, int]]:
        """Get the initiator node order.

        Raises DeviceConfigError when there are no initiators.

        Returns a sorted list of {assoc_sequence, node_id} tuples.
        Note that the `assoc_sequence` field is not required to be
        present in `nodes_data` for single-initiator setups.
        """

        default_seq: int = -1
        seq: Dict[int, int] = {}  # seq number -> node_id
        for node_id, v in self.nodes_data.items():
            if "assoc" not in v:
                continue
            assoc = self.read_nodes_data([int(node_id), "assoc"])
            s = assoc.get("assoc_sequence")
            if s is None:
                s = default_seq
            elif (type(s) is not int) or s < 0:
                raise DeviceConfigError(f"Invalid assoc_sequence, node {node_id}")
            if s in seq:
                raise DeviceConfigError(
                    f"Duplicate/missing assoc_sequence, node {node_id}"
                )
            seq[s] = node_id

        if len(seq) == 0:
            raise DeviceConfigError("Could not find any initiators")

        if default_seq in seq and len(seq) > 1:
            raise DeviceConfigError(f"Missing assoc_sequence, node {seq[default_seq]}")

        return sorted(seq.items(), key=operator.itemgetter(0))

    def tg_assoc_links(self, initiator_id: Optional[int] = None) -> None:
        """Associate links via e2e_minion and verify that they are up
        for every initiator or for `initiator_id`.

        Expects the following node data:
        ```
        {
            "assoc": {
                "channel": <1-4>,

                [Required when there are multiple initiators]
                "assoc_sequence": <non-negative int>,

                "links": [
                    {
                        "initiator_mac": "<mac>",
                        "responder_mac": "<mac>",

                        [Optional Fields]
                        "respNodeType": "<CN|DN>",
                        "polarity": "<ODD|EVEN|HYBRID_ODD|HYBRID_EVEN>",
                        "controlSuperframe": <int>,
                        "txGolayIdx": <int>,
                        "rxGolayIdx": <int>
                    },
                    <... more links>
                ]
            }
        }
        ```
        """

        if initiator_id is not None:
            self.__assoc_links(initiator_id)
        else:
            for initiator in self.__get_initiator_node_order():
                self.__assoc_links(initiator[1])

    def __assoc_links(self, initiator_id: int) -> None:
        """Associate links via e2e_minion and verify that they are up
        in the specified `initiator_id`.
        """

        # Validate the initiator_id
        if initiator_id not in self.device_info:
            err = f"Unable to find initiator node ID {initiator_id}"
            self.log_to_ctf(err, "error")
            raise TestUsageError(err)

        # Look up the required node data
        assoc_conf = self.read_nodes_data([initiator_id, "assoc"])
        self.log_to_ctf(f"assoc config:\n{assoc_conf}")
        self.log_to_ctf(
            f"Bringing up {len(assoc_conf['links'])} link(s) from node {initiator_id}",
            "info",
        )

        # Assoc each link in order
        for link in assoc_conf["links"]:
            self.minion_assoc(
                initiator_id,
                # read required/optional fields from assoc config
                link["initiator_mac"],
                link["responder_mac"],
                respNodeType=link.get("respNodeType", None),
                polarity=link.get("polarity", None),
                controlSuperframe=link.get("controlSuperframe", None),
                txGolayIdx=link.get("txGolayIdx", None),
                rxGolayIdx=link.get("rxGolayIdx", None),
                verify_link=True,
            )

    def minion_assoc(
        self,
        initiator_id: int,  # TODO Remove and look up with _get_node_id(initiator_mac)
        initiator_mac: str,
        responder_mac: str,
        respNodeType: Optional[str] = None,
        polarity: Optional[str] = None,
        controlSuperframe: Optional[int] = None,
        txGolayIdx: Optional[int] = None,
        rxGolayIdx: Optional[int] = None,
        verify_link: Optional[bool] = False,
    ) -> None:
        """Issue an assoc command to the given initiator node and verify that
        the link is up.
        """
        # from Topology.thrift
        NodeType = {"CN": 1, "DN": 2}
        PolarityType = {"ODD": 1, "EVEN": 2, "HYBRID_ODD": 3, "HYBRID_EVEN": 4}

        # build CLI options
        assoc_opts = [f"-i '{initiator_mac}'", f"-m '{responder_mac}'"]
        if respNodeType is not None:
            if respNodeType not in NodeType:
                raise TestUsageError(f"Invalid 'respNodeType': {respNodeType}")
            assoc_opts.append(f"-n {respNodeType.lower()}")
        if polarity is not None:
            if polarity not in PolarityType:
                raise TestUsageError(f"Invalid 'polarity': {polarity}")
            assoc_opts.append(f"-p {polarity.lower()}")
        if controlSuperframe is not None:
            assoc_opts.append(f"-s {controlSuperframe}")
        if txGolayIdx is not None:
            assoc_opts.append(f"--tx_golay {txGolayIdx}")
        if rxGolayIdx is not None:
            assoc_opts.append(f"--rx_golay {rxGolayIdx}")

        fw_stats_count: Dict = {}
        if self.test_args["bf_stats"]:
            fw_stats_count = self._start_bf_stats(initiator_mac, responder_mac)

        assoc_cmd: str = f"/usr/sbin/tg2 minion assoc {' '.join(assoc_opts)}"
        futures: Dict = self.run_cmd(assoc_cmd, [initiator_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: '{assoc_cmd}' failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"{assoc_cmd}\n{result['message']}")
        if self.test_args["bf_stats"]:
            self._stop_bf_stats(initiator_mac, responder_mac, fw_stats_count)

        if verify_link:
            # Verify link is up and get ifname
            ifname: str = self.minion_get_link_interface(
                initiator_id, initiator_mac, responder_mac
            )

            # Ping across the link
            sleep(1)  # Ensure that the link is ready
            self.verify_ll_ping(initiator_id, ifname, count=5)

    def _set_fw_stats_config(
        self, enable: bool, config_name: str, node_ids: Optional[List[int]] = None
    ) -> None:
        cmd = "tg2 minion fw_stats_config"
        cmd = f"{cmd} -y {config_name}" if enable else f"{cmd} -n {config_name}"
        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: '{cmd}' failed: " + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"{cmd}\n{result['message']}")
            LOG.info(f"{cmd}\n{result['message']}")

    def _start_bf_stats(self, initiator_mac: str, responder_mac: str) -> Dict:
        """Enable beamforming stats.
        Return: fw stats line count before beamforming is enabled.
        The line count enables finding the relevant part of the fw stats
        file after assoc.
        """

        if not self.test_args["bf_stats"]:
            raise TestUsageError("bf_stats test arg is False")

        initiator_id: int = self._get_node_id(initiator_mac)
        responder_id: int = self._get_node_id(responder_mac)

        fw_stats_count: Dict = {
            initiator_id: 1,
            responder_id: 1,
        }  # Assume that a new fw stats file will be created

        fw_stats_file = (
            FW_STATS_OUTPUT_FILE_COMPRESSED
            if self.test_args["compress_fw_stats"]
            else FW_STATS_OUTPUT_FILE
        )

        if self.test_args["enable_fw_stats"]:
            # Find the fw stats file line counts
            cmd = f"wc -l {fw_stats_file}"
            futures: Dict = self.run_cmd(cmd, [initiator_id, responder_id])
            for result in self.wait_for_cmds(futures):
                if not result["success"]:
                    error_msg = (
                        f"Node {result['node_id']}: '{cmd}' failed: "
                        + f"{result['error']}"
                    )
                    self.log_to_ctf(error_msg, "error")
                    raise DeviceCmdError(error_msg)

                line_count = result["message"].split()[0]
                if result["node_id"] == initiator_id:
                    fw_stats_count[initiator_id] = line_count
                else:
                    fw_stats_count[responder_id] = line_count
                self.log_to_ctf(
                    f"_start_bf_stats | cmd {cmd} | result {result['message']}", "info"
                )

        # Enable the beamforming stats and restart fw stats to put it into effect
        self._set_fw_stats_config(True, "TGF_STATS_BF", [initiator_id, responder_id])
        self.restart_fw_stats(
            append_stats=self.test_args["enable_fw_stats"],
            node_ids=[initiator_id, responder_id],
        )

        return fw_stats_count

    def _stop_bf_stats(
        self, initiator_mac: str, responder_mac: str, fw_stats_count: Dict
    ) -> None:
        """Stop beamforming stats, and save/copy the part of the fw stats
        file relevant to the last beamforming event - for further processing.
        """

        if not self.test_args["bf_stats"]:
            raise TestUsageError("bf_stats test arg is False")

        initiator_id: int = self._get_node_id(initiator_mac)
        responder_id: int = self._get_node_id(responder_mac)

        fw_stats_file = (
            FW_STATS_OUTPUT_FILE_COMPRESSED
            if self.test_args["compress_fw_stats"]
            else FW_STATS_OUTPUT_FILE
        )

        initiator_stats = f"{FW_STATS_PATH}/{FW_STATS}_{initiator_id}_link_{initiator_id}_{responder_id}"
        cmd = f"mkdir -p {FW_STATS_PATH}; sed -n '{fw_stats_count[initiator_id]},\\$p'  {fw_stats_file} > {initiator_stats}"
        futures: Dict = self.run_cmd(cmd, [initiator_id])

        responder_stats = f"{FW_STATS_PATH}/{FW_STATS}_{responder_id}_link_{initiator_id}_{responder_id}"
        cmd = f"mkdir -p {FW_STATS_PATH}; sed -n '{fw_stats_count[responder_id]},\\$p'  {fw_stats_file} > {responder_stats}"
        futures.update(self.run_cmd(cmd, [responder_id]))

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: '{cmd}' failed: " + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(
                f"_stop_bf_stats | cmd {cmd} | result {result['message']}", "info"
            )

        # Disable beamforming stats
        self._set_fw_stats_config(False, "TGF_STATS_BF", [initiator_id, responder_id])
        if self.test_args["enable_fw_stats"]:
            # Resume fw stats collection without beamforming stats
            self.restart_fw_stats(
                append_stats=True, node_ids=[initiator_id, responder_id]
            )
        else:
            # Stop fw stats collection - which was only enabled for beamforming
            self.collect_fw_stats(start=False, node_ids=[initiator_id, responder_id])

    def minion_dissoc(
        self, initiator_id: int, initiator_mac: str, responder_mac: str
    ) -> None:
        """Issue a dissoc command to the given initiator node and verify that
        the link is down.
        """
        dissoc_cmd: str = (
            f"/usr/sbin/tg2 minion dissoc -i '{initiator_mac}' -m '{responder_mac}'"
        )
        futures: Dict = self.run_cmd(dissoc_cmd, [initiator_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: '{dissoc_cmd}' failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"{dissoc_cmd}\n{result['message']}")

    def tg_check_sync(self, node_id: Optional[int] = None) -> None:
        """Check that the timing synchronization mode matches expectations
        for all initiators or for `node_id`.
        """

        if node_id is not None:
            self.__check_sync(node_id)
        else:
            # No need to check initiators in assoc order, but
            # __get_initiator_node_order() raises convenient exceptions
            for initiator in self.__get_initiator_node_order():
                self.__check_sync(initiator[1])

    def __check_sync(self, node_id: int) -> None:
        """Check that the timing synchronization mode matches expectations
        in `node_id`.
        """

        # validate node_id argument
        if node_id not in self.device_info:
            err = f"Unable to find node ID {node_id}"
            self.log_to_ctf(err, "error")
            raise TestUsageError(err)

        # look up node data
        fw_params = self.read_nodes_data(
            [node_id, "node_config", "radioParamsBase", "fwParams"], required=False
        )
        expected_mode_rf = fw_params and fw_params.get("forceGpsDisable", None) == 1

        # fetch stats
        stats_cmd = "tg2 stats driver-if | sed -e '/syncModeGps/q' | tail -1"
        futures: Dict = self.run_cmd(stats_cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"Node {result['node_id']}: '{stats_cmd}' failed"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            output = result["message"].strip()
            self.log_to_ctf(f"Node {result['node_id']}: {output}")

            if (expected_mode_rf and "syncModeGps, 1" in output) or (
                (not expected_mode_rf) and "syncModeGps, 0" in output
            ):
                raise DeviceError(f"Unexpected synchronization mode: {output}")

    def inspect_gps_stats(self, node_ids: Optional[List[int]] = None) -> None:
        """Inspect GPS-related stats for errors and log them to CTF."""
        if not node_ids:
            node_ids = self.get_tg_devices()

        # List of tuples:
        #   ("<stat name>", <min acceptable value>, <max acceptable value>)
        stat_checks = [
            ("tgd.gpsStat.fixType", 3, None),
            ("tgd.gpsStat.fixNumSat", 5, None),
            ("tgd.gpsStat.numGoodSnr", 1, None),
            ("tgf.00:00:00:00:00:00.gps.maxDriverDelay", None, 950000),
            ("tgf.00:00:00:00:00:00.gps.numMissedSec", None, 1),
            ("tgf.00:00:00:00:00:00.gps.maxPpsJitter", None, 19),
        ]

        # Skip any nodes with GPS disabled
        gps_enabled_node_ids = [
            node_id
            for node_id in node_ids
            if "node_config" not in self.nodes_data[node_id]
            or not (
                self.nodes_data[node_id]["node_config"]
                .get("radioParamsBase", {})
                .get("fwParams", {})
                .get("forceGpsDisable", 0)
            )
        ]
        futures = self.run_cmd(
            "tg2 stats driver-if -t 2 | grep -e 'gpsStat.[^0-9]' -e '.gps.'",
            gps_enabled_node_ids,
        )

        logs_per_node = {}
        for result in self.wait_for_cmds(futures):
            if result["success"]:
                # Parse stat lines
                stats: Dict[str, int] = {}
                for line in result["message"].splitlines():
                    tokens = [s.strip() for s in line.split(",")]
                    if len(tokens) < 3:
                        LOG.warn(f"Failed to parse stat: {line}")
                        continue
                    key: str = tokens[1]
                    value: int = int(tokens[2])
                    # Take max value if we saw the same key before
                    if key in stats and stats[key] >= value:
                        continue
                    stats[key] = value

                # Perform all checks
                failing_checks: List = []
                for key, min_value, max_value in stat_checks:
                    if key in stats:
                        if (min_value is not None and stats[key] < min_value) or (
                            max_value is not None and stats[key] > max_value
                        ):
                            failing_checks.append(f"{key} = {stats[key]}")
                if len(failing_checks) > 0:
                    logs_per_node[result["node_id"]] = "\n".join(failing_checks)

        if len(logs_per_node):
            msg_lines = [f"Found {len(logs_per_node)} node(s) with GPS issues:"]
            for k, v in logs_per_node.items():
                msg_lines.append(f"** Node {k} **\n{v}")
            self.log_to_ctf("\n".join(msg_lines), "info")
        else:
            self.log_to_ctf("No GPS issues found.", "info")

    def tg_get_mcs(
        self, node_to_resp_macs: Dict[int, List[str]]
    ) -> Dict[int, Dict[str, int]]:
        """Return the MCS on links to given responder MAC addresses.

        `node_to_resp_macs` should be a map from node_id to a list of all
        responder MACs for which to fetch MCS levels.

        This will return a map from node_id to another map from responder MAC to
        MCS level.
        """
        # We can run commands in parallel for each node
        cmd_batches: List = []
        for node_id, resp_macs in node_to_resp_macs.items():
            for i, resp_mac in enumerate(resp_macs):
                stats_cmd = f"tg2 stats driver-if | sed -e '/tgf.{resp_mac}.staPkt.mcs/q' | tail -1"
                if len(cmd_batches) <= i:
                    cmd_batches.append([])
                cmd_batches[i].append((node_id, stats_cmd))

        # Process all batches
        node_to_mcs: Dict[int, Dict[str, int]] = {}
        for batch in cmd_batches:
            futures: Dict = {}
            for node_id, cmd in batch:
                futures.update(self.run_cmd(cmd, [node_id]))
            for result in self.wait_for_cmds(futures):
                if not result["success"]:
                    # pyre-fixme[61]: `stats_cmd` may not be initialized here.
                    error_msg = f"Node {result['node_id']}: '{stats_cmd}' failed"
                    self.log_to_ctf(error_msg, "error")
                    raise DeviceCmdError(error_msg)

                # Parse output stat line
                tokens = result["message"].split(",")
                responder_mac = tokens[1].strip().split(".")[1]
                mcs = int(tokens[2].strip())
                self.log_to_ctf(
                    f"Node {result['node_id']}: MCS on link to {responder_mac} = {mcs}"
                )
                node_to_mcs.setdefault(result["node_id"], {})[responder_mac] = mcs

        return node_to_mcs

    def tg_restart_minion(
        self,
        node_ids: Optional[List[int]] = None,
        action: Optional[str] = "force-restart",
    ) -> None:
        """Restart e2e_minion on all test devices.
        action param can overwrite this function to start or stop the e2e_minion in node(s)
        This will return immediately. The caller is expected to wait for
        initialization by calling `tg_init_nodes()` or `verify_nodes_ready()`.
        """
        # force-restart/force-stop/start e2e_minion SV service
        minion_sv_cmd: str = f"/usr/bin/sv {action} e2e_minion"
        futures: Dict = self.run_cmd(minion_sv_cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                warning_msg = f"Node {result['node_id']}: received {result['message']} to {action} e2e_minion"
                self.log_to_ctf(warning_msg, "warning")
            else:
                self.log_to_ctf(f"Node {result['node_id']}: Issued e2e_minion {action}")

    def inspect_vpp_vnet_logs(self, node_ids: Optional[List[int]] = None) -> None:
        """Inspect VPP's "current" and "vnet.log" files for errors and log them
        to CTF.
        """
        VPP_LOGS = ["/var/log/vpp/current", "/var/log/vpp/vnet.log"]
        error_msgs = [
            # ---- from "current" ----
            "deadlock",
            # ---- from "vnet.log" ----
            "Firmware error detected, assert codes",
            "Firmware not ready",
        ]
        error_msgs = [f"-e '{msg}'" for msg in error_msgs]
        futures = self.run_cmd(
            f"grep -a {' '.join(error_msgs)} {' '.join(VPP_LOGS)}", node_ids
        )

        logs_per_node = {}
        for result in self.wait_for_cmds(futures):
            if result["success"]:
                logs_per_node[result["node_id"]] = result["message"].strip()

        if len(logs_per_node):
            msg_lines = [f"Found {len(logs_per_node)} node(s) with issues in VPP logs:"]
            for k, v in logs_per_node.items():
                msg_lines.append(f"** Node {k} **\n{v}")
            self.log_to_ctf("\n".join(msg_lines), "info")
        else:
            self.log_to_ctf("No issues found in VPP logs.", "info")

    def tg_run_topo_scan(
        self, initiator_id: Optional[int] = None, initiator_mac: Optional[str] = None
    ) -> None:
        """Associate links via e2e_minion and verify that they are up."""
        if initiator_id is None:
            initiator_id = self.find_initiator_id()
            if initiator_id is None:
                raise DeviceConfigError("Can't find initiator ID")

        # Validate initiator_id
        if initiator_id not in self.device_info:
            err = f"Unable to find initiator node ID {initiator_id}"
            self.log_to_ctf(err, "error")
            raise TestUsageError(err)

        # look up optional node data
        responder_macs = None
        channel = 2
        if not initiator_mac:
            assoc_conf = self.nodes_data.get(initiator_id, {}).get("assoc", None)
            if assoc_conf:
                initiator_mac = assoc_conf["initiator_mac"]
                if type(assoc_conf["responder_mac"]) is list:
                    responder_macs = assoc_conf["responder_mac"]
                else:
                    responder_macs = [assoc_conf["responder_mac"]]
                if "channel" in assoc_conf:
                    channel = assoc_conf["channel"]

        self.verify_nodes_ready([initiator_id])
        self.send_node_params(initiator_id, mac_addr=initiator_mac, channel=channel)
        self.gps_enable_if_needed(initiator_id)

        self.minion_topo_scan(initiator_id, initiator_mac, responder_macs)

    def minion_topo_scan(
        self,
        initiator_id: int,
        initiator_mac: Optional[str] = None,
        responder_macs: Optional[List[str]] = None,
    ) -> None:
        """Issue a topology scan command to the given initiator node and verify
        that expected responses are received.
        """
        cmd: str = "/usr/sbin/tg2 minion topo_scan --json"
        if initiator_mac:
            cmd = f"{cmd} -m '{initiator_mac}'"

        self.log_to_ctf(f"Starting topo scan on node {initiator_id}: {cmd}")

        futures: Dict = self.run_cmd(cmd, [initiator_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: '{cmd}' failed: {result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"{cmd}\n{result['message']}")
            result = self._parse_tg2_json(result["message"])

            # check response
            if result["status"] != 0:  # ScanFwStatus.COMPLETE
                error_msg = f"Topology scan returned error status {result['status']}"
                self.log_to_ctf(error_msg, "error")
                raise TestFailed(error_msg)
            if responder_macs:
                responder_macs_left = set(responder_macs)
                for resp in result.get("topoResps", {}).values():
                    if resp["addr"] in responder_macs_left:
                        self.log_to_ctf(f"Got response from {resp['addr']}")
                        responder_macs_left.remove(resp["addr"])
                if responder_macs_left:
                    error_msg = (
                        f"Topology scan missing responses from {len(responder_macs_left)} "
                        + f"node(s): {str(responder_macs_left)}"
                    )
                    self.log_to_ctf(error_msg, "error")
                    raise TestFailed(error_msg)

    def get_radio_pci_ids(self, node_id: int) -> List[str]:
        """Retrieve the PCI IDs of all Qualcomm radios on a given node."""
        futures: Dict = self.run_cmd("lspci -d 17cb:1201", [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"Node {result['node_id']}: failed to retrieve PCI IDs"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            pci_ids = result["message"]
            self.log_to_ctf(
                f"Node {result['node_id']} radio PCI IDs:\n{pci_ids}", "info"
            )

            # pyre-fixme[7]: Expected `List[str]` but got implicit return value of
            #  `None`.
            return [line.split()[0] for line in pci_ids.splitlines()]

    def run_wil_fw_trace(self, node_id: int, pci_id: str, get_ucode_logs: bool = False):
        """Run wil_fw_trace for a given PCI ID to retrieve either the firmware
        logs (default) or microcode logs (when `get_ucode_logs` is set).
        """
        bad_log_strs = ["Usage: wil_fw_trace", "Params underflow"]
        if get_ucode_logs:
            cmd_args = "-u -s /data/firmware/wil6210/ucode_image_trace_string_load.bin"
        else:
            cmd_args = "-s /data/firmware/wil6210/fw_image_trace_string_load.bin"
        cmd = f"/usr/bin/wil_fw_trace -1 -d {pci_id} {cmd_args}"
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"Node {result['node_id']}: failed to run wil_fw_trace"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            logs = result["message"]
            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{logs}")
            if not logs or any(s in logs for s in bad_log_strs):
                error_msg = "Error reading wil_fw_trace logs"
                self.log_to_ctf(error_msg, "error")
                raise TestFailed(error_msg)

    def start_e2e_controller(self, node_id: int) -> None:
        """Start the E2E controller on a given node."""
        futures: Dict = self.run_cmd("sv restart e2e_controller", [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"Node {result['node_id']}: failed to start e2e_controller"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

    def get_controller_topology(self, node_id: Optional[int] = None) -> Dict:
        """Fetch the network topology from the E2E controller by invoking a
        CLI command from a node.

        Expects the following node data on one node:
        ```
        {
            "e2e_controller": {
                "host": "<host_or_ip>",
                "port": <port>
            }
        }
        ```
        """
        if node_id is None:
            node_id = next(
                (k for k, v in self.nodes_data.items() if "e2e_controller" in v), None
            )
            if node_id is None:
                raise DeviceConfigError("Missing 'e2e_controller' field in node data")

        # validate node_id argument
        if node_id not in self.device_info or node_id not in self.nodes_data:
            err = f"Unable to find node ID {node_id}"
            self.log_to_ctf(err, "error")
            raise TestUsageError(err)
        if "e2e_controller" not in self.nodes_data[node_id]:
            raise DeviceConfigError(
                f"Missing 'e2e_controller' field in node data for node {node_id}"
            )

        controller_opts = self.nodes_data[node_id]["e2e_controller"]
        controller_flags: List[str] = []
        if "host" in controller_opts:
            controller_flags.append(f"--controller_host {controller_opts['host']}")
        if "port" in controller_opts:
            controller_flags.append(f"--controller_port {controller_opts['port']}")

        cmd: str = f"tg2 {' '.join(controller_flags)} topology ls --json"
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to fetch topology from "
                    + f"e2e_controller: {result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            # pyre-fixme[7]: Expected `Dict[typing.Any, typing.Any]` but got
            #  implicit return value of `None`.
            return self._parse_tg2_json(result["message"])

    def controller_verify_topology_up(
        self,
        get_topology_fn: Callable,
        get_topology_fn_args: Optional[List] = None,
        skip_nodes: Optional[Set] = None,
        skip_links: Optional[Set] = None,
    ) -> None:
        """
        Verify that all nodes and links in the network are up while skipping the validation
        for nodes and links listed in `skip_links` and `skip_nodes`
        """
        if not skip_nodes:
            skip_nodes = set()
        if not skip_links:
            skip_links = set()
        topology: Dict = (
            get_topology_fn(*get_topology_fn_args)
            if get_topology_fn_args
            else get_topology_fn()
        )
        NodeStatusType_OFFLINE: int = 1  # Thrift enum
        nodes_down = [
            node["name"]
            for node in topology["nodes"]
            if (
                (node["status"] == NodeStatusType_OFFLINE)
                and (node["name"] not in skip_nodes)
            )
        ]
        links_down = [
            link["name"]
            for link in topology["links"]
            if (not link["is_alive"] and link["name"] not in skip_links)
        ]
        if nodes_down or links_down:
            if nodes_down:
                self.log_to_ctf(
                    f"{len(nodes_down)} node(s) are down: {', '.join(nodes_down)}",
                    "error",
                )
            if links_down:
                self.log_to_ctf(
                    f"{len(links_down)} link(s) are down: {', '.join(links_down)}",
                    "error",
                )
            raise TestFailed(
                f"{len(nodes_down)} node(s) and {len(links_down)} link(s) are down"
            )

        self.log_to_ctf(
            f"{len(topology['nodes']) - len(skip_nodes)} node(s) and "
            + f"{len(topology['links']) - len(skip_links)} link(s) are up",
            "info",
        )

    def verify_chrony_sync(self, node_id: int, max_time_offset: float = 0.5) -> None:
        """Check that chrony has synced time successfully by invoking chronyc"""
        gpsd_enabled = (
            self.node_configs.get(node_id, {})
            .get("envParams", {})
            .get("GPSD_ENABLED", "1")
        )
        num_timeservers = len(
            self.node_configs.get(node_id, {})
            .get("sysParams", {})
            .get("ntpServers", {})
        )
        futures = self.run_cmd("chronyc -c sources")
        for result in self.wait_for_cmds(futures):
            self.log_to_ctf(f"Checking chrony output in node: {result['node_id']}")
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']} failed to run chronyc: {result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            else:
                errors: List = []
                # 'chronyc -c sources' produces output in the following format:
                # Source mode,Source state,Name/IP address,Stratum,Poll,Reach,LastRx,Last sample
                # Source state can be one of the following:
                # '*' = current synced, '+' = combined , '-' = not combined,
                # '?' = unreachable, 'x' = time may be in error, '~' = time too variable.
                failed_sync: List = []
                large_offset: List = []
                timeservers_found: int = 0
                nmea_found: int = 0
                pps_found: int = 0
                chrony_synced: bool = False
                for line in result["message"].split():
                    source_state = line.split(",")[1]
                    name = line.split(",")[2]
                    offset = float(line.split(",")[7])
                    if abs(offset) > max_time_offset:
                        large_offset.append(line)
                    if (
                        source_state == "?"
                        or source_state == "x"
                        or source_state == "~"
                    ):
                        failed_sync.append(line)
                    else:
                        if source_state == "*":
                            chrony_synced = True
                        if gpsd_enabled == "1":
                            if name == "NMEA":
                                nmea_found += 1
                                continue
                            if name == "PPS":
                                pps_found += 1
                                continue
                        try:
                            ipaddress.ip_address(name)
                            timeservers_found += 1
                        except ipaddress.AddressValueError:
                            errors.append(f"{name} is not a valid IPv6 address")

                if not chrony_synced:
                    errors.append("Chrony is not currently synced to a time source")
                if timeservers_found < num_timeservers:
                    errors.append(
                        f"{num_timeservers - timeservers_found} time server(s) not recognized by chrony"
                    )
                if not nmea_found:
                    errors.append("NMEA is not recognized by chrony")
                if not pps_found:
                    errors.append("PPS is not recognized by chrony")
                newline = "\n"
                if failed_sync:
                    errors.append(
                        f"The following time sources failed to sync:\n{newline.join(failed_sync)}"
                    )
                if large_offset:
                    errors.append(
                        f"The following time sources had unreasonably large offsets:\n{newline.join(large_offset)}"
                    )
                if errors:
                    errorMsg = f"Found the following time errors on node: {result['node_id']}:\n{newline.join(errors)}"
                    self.log_to_ctf(errorMsg, "error")
                    raise TestFailed(errorMsg)

    def set_python_usable(self, flag: bool) -> None:
        """Enable or disable the Python executable on all nodes.

        This will move all files `/usr/bin/python*` to/from a temporary
        directory.
        """
        TMPDIR = "/usr/bin/.ctf_tmp"
        if flag:
            self.log_to_ctf("Re-enabling Python on all nodes", "info")
            cmd = f"mv -v {TMPDIR}/* /usr/bin/ ; rmdir {TMPDIR}"
        else:
            self.log_to_ctf("Disabling Python on all nodes", "info")
            cmd = f"mkdir {TMPDIR} && mv -v /usr/bin/python* {TMPDIR}/"
        cmd = self.remount_cmd(cmd)
        futures: Dict = self.run_cmd(cmd)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise DeviceCmdError(f"Node {result['node_id']}:\n{result['error']}")
            if result["message"]:
                self.log_to_ctf(f"Node {result['node_id']}:\n{result['message']}")

    def remount_cmd(self, cmd: str) -> str:
        """Wrap a given command such that it is executed with the root
        filesystem remounted as read-write (if not already mounted as such).
        """
        TMP_MARKER_FILE = "/tmp/.ctf-remount-marker"
        return (
            f"rm -vf {TMP_MARKER_FILE}; "
            + 'if grep -q "[[:space:]]ro[[:space:],]" /proc/mounts; then '
            + "  mount -o rw,remount /; "
            + f"  touch {TMP_MARKER_FILE}; "
            + "fi; "
            + f"({cmd}); "
            + f'if [ -f "{TMP_MARKER_FILE}" ]; then '
            + "  mount -o ro,remount /; "
            + f"  rm -vf {TMP_MARKER_FILE}; "
            + "fi"
        )

    def collect_fw_stats(
        self,
        start: bool,
        compress: bool = False,
        mac_addr: str = "",
        append_stats: bool = False,
        node_ids: Optional[List[int]] = None,
    ) -> None:
        """Start or stop firmware stats collection"""
        cmd: str = ""
        stats_cmd: str = "tg2 stats driver-if"
        if start:
            outfile: str = (
                FW_STATS_OUTPUT_FILE_COMPRESSED if compress else FW_STATS_OUTPUT_FILE
            )
            cmd_parts = [stats_cmd]
            if mac_addr:
                cmd_parts.append(f"-m {mac_addr}")
            if compress:
                cmd_parts.append("| gzip")
            cmd = " ".join(cmd_parts)
            redirect_out = ">"
            if append_stats:
                redirect_out = ">>"
            cmd = f"({cmd}) {redirect_out} {outfile} < /dev/null 2>&1 &"
            self.log_to_ctf(f"Starting firmware stats collection on all nodes: {cmd}")
        else:
            cmd = f"pkill -f '{stats_cmd}'"
            self.log_to_ctf("Stopping firmware stats collection on all nodes")

        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                self.log_to_ctf(f"Node {result['node_id']}: {cmd} failed", "error")

    def restart_fw_stats(
        self, append_stats: bool = True, node_ids: Optional[List[int]] = None
    ):
        """Restart starts fw_stats collection and by default will append to outfile"""
        # Stop fw stats collection
        self.collect_fw_stats(start=False, node_ids=node_ids)
        # Start fw stats collection
        self.collect_fw_stats(
            start=True,
            compress=self.test_args["compress_fw_stats"],
            append_stats=append_stats,
            node_ids=node_ids,
        )

    def inspect_core_dumps(self, node_ids: Optional[List[int]] = None) -> None:
        """Log any core dump information to CTF."""
        # Count the number of core dumps for each process
        cmd: str = "find /var/volatile/cores/ -type f | cut -d/ -f5 | sort | uniq -c"
        futures = self.run_cmd(cmd, node_ids)
        core_dumps_per_node = {}
        for result in self.wait_for_cmds(futures):
            if result["success"] and result["message"].strip():
                core_dumps_per_node[result["node_id"]] = result["message"]

        if len(core_dumps_per_node):
            msg_lines = [f"Found {len(core_dumps_per_node)} node(s) with core dumps:"]
            for k, v in core_dumps_per_node.items():
                msg_lines.append(f"** Node {k} **\n{v}")
            self.log_to_ctf("\n".join(msg_lines), "info")
        else:
            self.log_to_ctf("No core dumps found.", "info")

    def inspect_crash_logs(self, node_ids: Optional[List[int]] = None) -> None:
        """Try to locate any application crash logs and log them to CTF."""
        # List of application logs that we care about here
        APP_LOGS = ["/var/log/e2e_minion/current", "/var/log/openr/current"]

        # Scan application logs and output crash lines with surrounding context.
        #
        # 'grep' flags:
        # -a   Process a binary file as if it were text
        # -A3  Print NUM=3 lines of trailing context after matching lines
        # -E   Extended regular expression
        # -e   Used to specify multiple patterns
        #
        # Patterns:
        # > C++ abort text
        #   *** Aborted at 1602198897 (unix time) try "date -d @1602198897" if you are using GNU date ***
        # > glog (Google logging) abort text
        #   *** Check failure stack trace: ***
        # > Terragraph ExceptionHandler abort text
        #   *** Terminated due to exception: ***
        cmd: str = (
            "grep -a -A3 -E "
            + "-e '^*** Aborted at' "
            + "-e '^*** Check failure stack trace' "
            + "-e '*** Terminated due to exception' "
            + " ".join(APP_LOGS)
        )
        futures = self.run_cmd(cmd, node_ids)
        logs_per_node = {}
        for result in self.wait_for_cmds(futures):
            if result["success"]:
                logs_per_node[result["node_id"]] = result["message"]

        if len(logs_per_node):
            msg_lines = [f"Found {len(logs_per_node)} node(s) with crash logs:"]
            for k, v in logs_per_node.items():
                msg_lines.append(f"** Node {k} **\n{v}")
            self.log_to_ctf("\n".join(msg_lines), "info")
        else:
            self.log_to_ctf("No crash logs found.", "info")
