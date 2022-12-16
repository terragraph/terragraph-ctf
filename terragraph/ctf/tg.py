#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Library containing Terragraph test utilities.
"""
import datetime
import ipaddress
import json
import logging
import os
import subprocess
import time
from argparse import Namespace
from concurrent.futures import as_completed
from typing import cast, Dict, List, Optional, Set

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed, TestUsageError

from ctf.ctf_client.runner.lib import BaseCtfTest

from .consts import TgCtfConsts


try:
    # py3.8
    from asyncio import TimeoutError
except ImportError:
    # py3.7
    from concurrent.futures import TimeoutError

LOG = logging.getLogger(__name__)

# Default node config file path
NODE_CONFIG_FILE = "/data/cfg/node_config.json"
# Default topology file path
E2E_TOPOLOGY_FILE = "/data/e2e_topology.conf"
# TG Node Image file path
TG_IMAGE_BIN_FILE = "/tmp/tg-update-qoriq.bin"


class BaseTgCtfTest(BaseCtfTest):
    """CTF test base class extended with Terragraph-specific functionality."""

    # Log files to collect from Terragraph devices
    LOG_FILES: List[str] = []

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

        # Map from node IDs (matching `self.device_info` from the CTF database)
        # to node config objects, populated from any of these calls:
        # - `set_node_config()`
        # - `get_current_node_config()`
        self.node_configs: Dict[int, Dict] = {}

        # Set Terragraph device log files
        self.logfiles["terragraph"] = self.LOG_FILES

        # Common test step entries used in get_test_steps()
        self.COMMON_TEST_STEPS: Dict = self.get_common_test_steps()

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        # NOTE: Python allows calling super() in static methods, but mypy has a
        # bug that throws an error here (which we suppress):
        #   super() requires one or more positional arguments in enclosing function
        test_params: Dict[str, Dict] = super(BaseTgCtfTest, BaseTgCtfTest).test_params()
        test_params["allow_mixed_versions"] = {
            "desc": "Should we allow mixed software versions for this test?",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["kafka_endpoint"] = {
            "desc": "Kafka server end point url for stats collection",
            "default": TgCtfConsts.get("DEFAULT_KAFKA_ENDPOINT", ""),
        }
        test_params["fluentd_host"] = {
            "desc": "fluentd server host",
            "default": TgCtfConsts.get("DEFAULT_FLUENTD_HOST", ""),
        }
        test_params["fluentd_port"] = {
            "desc": "fluentd server port",
            "default": TgCtfConsts.get("DEFAULT_FLUENTD_PORT", 24224),
            "convert": int,
        }
        return test_params

    def nodes_data_amend_test_args(self, nodes_data: Dict, num_nodes: int):
        merged_nodes_data = super().nodes_data_amend_test_args(nodes_data, num_nodes)

        if self.test_args["kafka_endpoint"]:
            self.merge_dict(
                merged_nodes_data,
                {
                    i: {
                        "node_config": {
                            "statsAgentParams": {
                                "endpointParams": {
                                    "kafkaParams": {
                                        "config": {
                                            "brokerEndpointList": self.test_args[
                                                "kafka_endpoint"
                                            ],
                                        }
                                    }
                                }
                            },
                        }
                    }
                    for i in range(1, num_nodes + 1)
                },
            )
        if self.test_args["fluentd_host"]:
            self.merge_dict(
                merged_nodes_data,
                {
                    i: {
                        "node_config": {
                            "fluentdParams": {
                                "endpoints": {
                                    "CTF": {
                                        "host": self.test_args["fluentd_host"],
                                        "port": self.test_args["fluentd_port"],
                                    }
                                }
                            },
                        }
                    }
                    for i in range(1, num_nodes + 1)
                },
            )
        if self.test_args.get("enable_fw_logs", None):
            self.merge_dict(
                merged_nodes_data,
                {
                    i: {
                        "node_config": {
                            "envParams": {
                                "FW_LOGGING_ENABLED": "1",
                                "FW_LOG_VERBOSE": "4",
                                "HMAC_VERBOSE": "2",
                            },
                            "fluentdParams": {
                                "sources": {
                                    "fw_trace": {
                                        "enabled": True,
                                        "filename": "/var/log/wil6210/*fw*.txt",
                                    },
                                }
                            },
                        }
                    }
                    for i in range(1, num_nodes + 1)
                },
            )
        return merged_nodes_data

    def get_common_test_steps(self) -> Dict:
        """Return common test step entries used in get_test_steps()."""
        return {
            "check_software_versions": {
                "name": "Check for matching Terragraph software versions",
                "function": self.tg_verify_versions,
                "function_args": (),
                "success_msg": "Successfully checked Terragraph software versions",
            },
            "ping_all_nodes_link_local": {
                "name": "Run link-local ping between all nodes",
                "function": self.ping_all_nodes,
                "function_args": (),
                "success_msg": "All nodes can ping each other",
            },
            "wait_for_loopback_ipv6_addr": {
                "name": "Wait for IPv6 global address on 'lo' interface",
                "function": self.wait_for_nodes_global_prefix,
                "function_args": (),
                "success_msg": "All nodes have global prefixes",
            },
        }

    def get_tg_devices(self) -> List[int]:
        """Return all test devices with type 'terragraph'."""
        return [
            node_id
            for node_id, device in self.device_info.items()
            if device.device_type() == "terragraph"
        ]

    def get_current_node_config(self, path: str = NODE_CONFIG_FILE) -> None:
        """Retrieve the current node configuration from the test devices.

        This will update 'self.node_configs' in order with 'self.device_info'.
        """
        self.log_to_ctf(f"Fetching current node configs from: {path}", "info")
        futures: Dict = self.run_cmd(f"cat {path}")

        for result in self.wait_for_cmds(futures):
            self.log_to_ctf(f"Received node config from node {result['node_id']}")
            if not result["success"]:
                raise DeviceCmdError(
                    f"Failed to obtain node config from node {result['node_id']}"
                )
            self.node_configs[result["node_id"]] = json.loads(result["message"].strip())

    def show_current_node_config(
        self,
        node_ids: List[int],
        path: str = NODE_CONFIG_FILE,
    ) -> None:
        """Show the current node configuration from the test devices."""
        self.log_to_ctf(f"Fetching current node configs from: {path}", "info")
        futures: Dict = self.run_cmd(f"cat {path}", node_ids)

        for result in self.wait_for_cmds(futures):
            self.log_to_ctf(f"Received node config from node {result['node_id']}")
            if not result["success"]:
                raise DeviceCmdError(
                    f"Failed to obtain node config from node {result['node_id']}"
                )
            self.log_to_ctf(
                f"node config in Node {result['node_id']}:\n{result['message']}"
            )

    def generate_base_node_config(self, path: str = NODE_CONFIG_FILE) -> None:
        """Write the (layered) base configuration to a given path.

        By default, this will reset all test devices to the default node
        configuration."""
        self.log_to_ctf(f"Writing base node configs to: {path}", "info")
        futures: Dict = self.run_cmd(f"/usr/sbin/config_get_base {path}")

        for result in self.wait_for_cmds(futures):
            if result["success"]:
                LOG.debug(f"Node {result['node_id']} base node config was generated")
            else:
                raise DeviceCmdError(
                    f"Node {result['node_id']} failed to generate base node config"
                )

    def _gen_and_copy_new_config(
        self, node_id: int, node_config_overrides: Dict, step_idx: Optional[int] = None
    ) -> None:
        """Generate a merged node configuration file and push it to a given
        test device.

        This will update 'self.node_configs'.
        """

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        if node_id not in self.device_info:
            raise TestUsageError(f"Node {node_id} not found in device_info")
        device = self.device_info[node_id]

        # Merge JSON config
        self.merge_dict(self.node_configs[node_id], node_config_overrides)

        # Push file
        if not self.push_json_file(
            device.connection, self.node_configs[node_id], NODE_CONFIG_FILE
        ):
            raise DeviceCmdError(f"Failed to copy config to node {node_id}")

    def set_node_config(self, nodes_data: Dict) -> None:
        """Override the node configuration on all test devices with the given
        object.
        """
        self.log_to_ctf("Setting custom node configs...", "info")
        futures: Dict = {}

        for node_id in self.get_tg_devices():
            if node_id not in nodes_data or "node_config" not in nodes_data[node_id]:
                self.log_to_ctf(f"Node {node_id} has no custom config to apply")
                continue

            futures[
                self.thread_pool.submit(
                    self._gen_and_copy_new_config,
                    node_id,
                    nodes_data[node_id]["node_config"],
                    self.thread_local.step_idx,
                )
            ] = node_id

        for future in as_completed(futures.keys(), timeout=self.timeout):
            self.log_to_ctf(
                f"Finished pushing custom config to node {futures[future]}:\n"
                + f"{json.dumps(nodes_data[futures[future]]['node_config'], indent=2)}"
            )

    def wipe_controller_config_files(self, node_id: int) -> None:
        """Delete all E2E controller config files on a given node."""
        files = [
            "/data/cfg/controller_config.json",
            "/data/cfg/node_config_overrides.json",
            "/data/cfg/network_config_overrides.json",
            "/data/cfg/auto_node_config_overrides.json",
        ]
        cmd: str = f"rm -vf {' '.join(files)}"
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            self.log_to_ctf(f"{cmd}\n{output}")

            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']} failed to wipe controller config files"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

    def set_e2e_config_files(
        self, node_id: int, e2e_configs: Dict, dst_path_prefix: str = ""
    ) -> None:
        """Push E2E config files to a test device."""
        if node_id not in self.device_info:
            raise DeviceCmdError(f"Node {node_id} not found in device_info")
        device = self.device_info[node_id]

        # Create directory
        config_dir: str = f"{dst_path_prefix}/data/cfg"
        mkdir_cmd: str = f"mkdir -p {config_dir}"
        self.log_to_ctf(f"Creating config directory: {mkdir_cmd}")
        futures = self.run_cmd(mkdir_cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])

        # Push each config
        for name, config in e2e_configs.items():
            remote_path = f"{config_dir}/{name}.json"
            self.log_to_ctf(
                f"Pushing E2E config file: {remote_path}\n"
                + f"{json.dumps(config, indent=2)}",
                "info",
            )
            if not self.push_json_file(device.connection, config, remote_path):
                raise DeviceCmdError(
                    f"Failed to copy E2E config file '{name}' to node {node_id}"
                )

    def set_topology_file(
        self, node_id: int, topology: Dict, dst_path: str = E2E_TOPOLOGY_FILE
    ) -> None:
        """Push a given topology structure to a test device."""
        if node_id not in self.device_info:
            raise DeviceCmdError(f"Node {node_id} not found in device_info")
        device = self.device_info[node_id]

        self.log_to_ctf(
            f"Pushing topology file: {dst_path}\n"
            + f"{json.dumps(topology, indent=2)}",
            "info",
        )
        if not self.push_json_file(device.connection, topology, dst_path):
            raise DeviceCmdError(f"Failed to copy topology to node {node_id}")

    # TODO - cleanup this API to use ping_ip
    def verify_ll_ping(
        self, node_id: int, ifname: str, count: int = 3, wait_time: int = 1, timeout=60
    ) -> None:
        """Run a link-local ping on a given node and network interface, and
        verify that a remote response is received.
        """
        self.log_to_ctf(f"Verify lo ping. TIMEOUT {timeout}")

        ping_cmd = f"/bin/ping6 -c {count} -W {wait_time} ff02::1%{ifname}"
        futures = self.run_cmd(ping_cmd, [node_id])

        for result in self.wait_for_cmds(futures, timeout=timeout):
            if not result["success"]:
                error_msg = f"'{ping_cmd}' failed"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            ping_output = result["message"]
            self.log_to_ctf(f"{ping_cmd}\n{ping_output}")
            if "DUP" not in ping_output:
                error_msg = f"'{ping_cmd}' failed: {ping_output.strip()}"
                self.log_to_ctf(error_msg, "error")
                raise TestFailed(error_msg)

    def get_ip(
        self,
        node_ids: Optional[List[int]] = None,
        interface: str = "lo",
        ip_type: str = "global",
    ) -> Dict[int, str]:
        """Retrieve the IP address on a given network interface. Returns a map of
        node IDs to IP addresses."""

        cmd = f"ip addr show {interface} scope {ip_type} | grep {ip_type} | grep -v deprecated"
        futures: Dict = self.run_cmd(cmd, node_ids)
        ip_addr_map: Dict[int, str] = {}

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                warning_msg = f"'{cmd}' failed"
                self.log_to_ctf(warning_msg, "warning")

            output = result["message"]
            if output:
                # parse ip from output
                ip_addr = (output.split()[1]).split("/")[0]
                ipaddress.ip_address(ip_addr)
                ip_addr_map[result["node_id"]] = str(ip_addr)
                self.log_to_ctf(
                    f"Node {result['node_id']} has {ip_type} IP {ip_addr} on interface '{interface}'"
                )
            else:
                error_msg = (
                    f"Node {result['node_id']} does not have {ip_type} IP "
                    + f"assigned on {interface}"
                )
                self.log_to_ctf(error_msg, "error")
                ip_addr_map[result["node_id"]] = ""

        return ip_addr_map

    def wait_for_nodes_global_prefix(
        self, timeout: int = 60, retry_interval: int = 5
    ) -> None:
        """Wait until all the nodes get assigned global IPv6 prefixes
        by the configured prefix allocation scheme.
        """
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=timeout)

        # Since nodes can lose prefixes suddenly, wait until all the
        # nodes consistently report prefixes.
        while True:
            ip_addr_map = self.get_ip(interface="lo", ip_type="global")
            now = datetime.datetime.now()
            pending_node_ids: List[int] = []
            for node_id, prefix in ip_addr_map.items():
                if not prefix:
                    pending_node_ids.append(node_id)

            if not pending_node_ids:
                return

            if now > end_time:
                raise DeviceCmdError(
                    f"Nodes {pending_node_ids} failed to get global IPv6 prefixes"
                    + f" within {timeout} seconds"
                )
            time.sleep(retry_interval)

    def ping_ip(
        self,
        from_node_id: int,
        dest_ip: str,
        count: int = 5,
        wait_time: int = 1,
        interval: float = 1,
    ) -> None:
        """Ping from a node to a destination IP."""
        cmd = f"/bin/ping6 -c {count} -W {wait_time} -i {interval} {dest_ip}"
        futures: Dict = self.run_cmd(cmd, [from_node_id])
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"'{cmd}' failed"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            output = result["message"]
            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{output}")
            ping_summary = ""
            ping_stats = ""
            for output_line in output.split("\n"):
                if "packets transmitted" in output_line:
                    ping_summary = output_line
                if "min/avg/max/mdev" in output_line:
                    ping_stats = output_line

            self.log_to_ctf(f"ping_summary: {ping_summary}")
            self.log_to_ctf(f"ping_stats: {ping_stats}")
            self.ping_output_to_ctf_table(
                ping_summary, ping_stats, from_node_id, dest_ip
            )

            if int(ping_summary.split()[3]) == 0:
                error_msg = (
                    f"{cmd} from node {from_node_id} to "
                    + f"{dest_ip} failed: [{ping_summary}]"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(
                f"Ping from node {from_node_id} to {dest_ip} summary: "
                + f"[{ping_summary}]",
                "info",
            )

    def ping_nodes(
        self,
        from_node_id: int,
        to_node_id: int,
        interface: str = "lo",
        ip_type: str = "global",
        count: int = 5,
        wait_time: int = 1,
        interval: float = 1,
    ) -> None:
        """Ping from one node to another on a specific interface."""
        ip_addr_map = self.get_ip([to_node_id], interface, ip_type)
        to_node_ip = ip_addr_map[to_node_id]
        self.log_to_ctf(f"Ping from node {from_node_id} to node {to_node_id}", "info")

        self.ping_ip(from_node_id, to_node_ip, count, wait_time, interval)

    def ping_all_nodes(self, count: int = 4, wait_time: int = 1) -> None:
        """Run a ping between all test devices, using link-local IPs."""
        for node_id in self.get_tg_devices():
            # Only node 1 pings node 2, everything else pings node 1
            ping_node_id = 2 if node_id == 1 else 1
            self.ping_nodes(node_id, ping_node_id, interface="lo")

    def reboot_and_wait(
        self,
        device_info: Dict,
        timeout: float = 600.0,
        device_type: str = "terragraph",
        node_ids: Optional[List[int]] = None,
    ) -> None:
        """Reboot all test devices and wait until they are reachable."""
        # issue reboot command
        reboot_msg_cmd: str = (
            f"wall -n '==== Rebooting for CTF test {self.test_exe_id} ===='"
        )
        futures: Dict = self.run_cmd(
            f"{reboot_msg_cmd}; reboot", node_ids=node_ids, device_type=device_type
        )
        for result in self.wait_for_cmds(futures):
            self.log_to_ctf(f"Rebooting node {result['node_id']}", "info")
            if not result["success"]:
                raise DeviceCmdError(f"Node {result['node_id']} failed to be reboot")

        # Dont wait for reconnection when timeout=0 and return early
        if timeout == 0:
            return

        # wait for nodes to initiate reboot before re-attempting connection
        time.sleep(5)

        # attempt to reconnect
        self.log_to_ctf(f"Trying to reconnect to all nodes for up to {timeout}s...")
        futures = {}
        for node_id, device in device_info.items():
            if device.device_type() == device_type:
                futures[
                    self.thread_pool.submit(
                        self.test_can_connect,
                        node_id,
                        retry_interval=5,
                        # pyre-fixme[6]: For 4th param expected `int` but got `float`.
                        timeout=timeout - 1,
                        step_idx=self.thread_local.step_idx,
                    )
                ] = node_id
            for future in as_completed(futures.keys(), timeout=timeout):
                if future.result():
                    self.log_to_ctf(f"Can connect to node {futures[future]}")
                else:
                    raise DeviceCmdError(
                        f"Failed to connect to node {futures[future]} after reboot"
                    )

    def tg_verify_versions(self) -> None:
        """Verify that the Terragraph version strings on all test devices
        match.

        Raises TestFailed if any version strings differ or none were found.
        """
        versions = self.get_tg_version()
        fw_versions = self.get_fw_version()
        if len(versions) > 1 or len(fw_versions) > 1:
            error_msg: str = "Mixed versions detected in test setup"
            if self.test_args["allow_mixed_versions"]:
                self.log_to_ctf(error_msg, "error")
            else:
                raise TestFailed(error_msg)
        elif len(versions) < 1 or versions.pop() == "":
            raise TestFailed("No Terragraph versions found")

    def get_tg_version(self, node_ids: Optional[List[int]] = None) -> Set[str]:
        """Retrieve the Terragraph version strings from test devices.

        This checks `/etc/tgversion` first, then falls back to `/etc/version`.
        """
        futures: Dict = self.run_cmd(
            "cat /etc/tgversion 2>/dev/null || cat /etc/version", node_ids
        )
        versions: Set[str] = set()

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise DeviceCmdError(
                    f"Failed to read version from node {result['node_id']}"
                )

            ver = result["message"]
            versions.add(ver)
            self.log_to_ctf(f"Node {result['node_id']} version: {ver.strip()}")

        return versions

    def get_fw_version(self, node_ids: Optional[List[int]] = None) -> Set[str]:
        """Retrieve the wigig firmware version strings from test devices."""
        futures: Dict = self.run_cmd("get_fw_version", node_ids)
        versions: Set[str] = set()

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise DeviceCmdError(
                    f"Failed to read firmware version from node {result['node_id']}"
                )

            ver = result["message"]
            versions.add(ver)
            self.log_to_ctf(f"Node {result['node_id']} firmware version: {ver.strip()}")

        return versions

    def upgrade_and_reboot_tg_images(
        self,
        image_file_path: str,
        node_ids: Optional[List[int]] = None,
        max_upgrade_timeout: int = 600,
        connection_timeout: int = 180,
    ) -> None:
        """Flash/upgrade a TG image on selected nodes and wait
        for reboot.
        """
        self.log_to_ctf("Flashing images on nodes", "info")
        upgrade_msg_cmd: str = (
            f"wall -n '==== Flashing image for CTF test {self.test_exe_id} ===='"
        )
        futures: Dict = self.run_cmd(
            f"{upgrade_msg_cmd}; {image_file_path} -ur", node_ids
        )
        try:
            for result in self.wait_for_cmds(futures, timeout=max_upgrade_timeout):
                self.log_to_ctf(f"Upgrading node {result['node_id']}")
                if not result["success"]:
                    raise DeviceCmdError(f"Node {result['node_id']} failed upgrade")
        except TimeoutError:
            raise DeviceCmdError("Image upgrade took too long")

        self.log_to_ctf("Images are flashed - Reconnecting to nodes", "info")
        # attempt to reconnect to nodes after upgrade
        futures = {}
        node_list = node_ids if node_ids else self.get_tg_devices()
        for node_id in node_list:
            futures[
                self.thread_pool.submit(
                    self.test_can_connect,
                    node_id,
                    retry_interval=5,
                    timeout=connection_timeout - 1,
                    step_idx=self.thread_local.step_idx,
                )
            ] = node_id

        for future in as_completed(futures.keys(), timeout=connection_timeout):
            if future.result():
                self.log_to_ctf(
                    f"Upgrade success: Can connect to node {futures[future]}", "info"
                )
            else:
                raise DeviceCmdError(
                    f"Post upgrade connection failure on {futures[future]}"
                )

    def upgrade_and_verify_tg_images(
        self,
        image_file_path: str,
        node_ids: Optional[List[int]] = None,
        timeout: int = 600,
    ) -> None:
        """Flash/upgrade a TG image on selected nodes. This performs the
        following steps in sequence:

        1) Assuming the image is already downloaded in the given path, verify
           the checksum and store version metadata.

        2) Flash/upgrade the image and wait for reboot.

        3) Post-reboot, match the running image version with the
           downloaded image version from step 1 (pre-upgrade).
        """

        # Ensure exec permission, and verify the checksum of the
        # downloaded image
        futures: Dict = self.run_cmd(
            f"chmod a+x {image_file_path};{image_file_path} -cm", node_ids
        )

        image_versions: Set[str] = set()
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = f"Node {result['node_id']} read metadata failure"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            if "Checksum ok" not in result["message"]:
                error_msg = f"Node {result['node_id']} checksum failed"
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(f"Node {result['node_id']} checksum OK", "info")

            # Remove the checksum etc from the end and parse only metadata as json
            status = cast(Dict, json.loads(result["message"].rsplit("\n", 3)[0]))

            # Store the image versions in a set for matching post-reboot
            image_versions.add(status["version"] + "\n")

        # Upgrade images and wait for reboot
        self.upgrade_and_reboot_tg_images(
            image_file_path, node_ids=node_ids, max_upgrade_timeout=timeout
        )

        running_versions = self.get_tg_version(node_ids)
        # Post-reboot, match the versions of downloaded image with running image
        if running_versions != image_versions:
            self.log_to_ctf(
                f"Version mismatch: running_versions = {running_versions}, "
                + f"image_versions = {image_versions}",
                "error",
            )
            raise DeviceCmdError("Version mismatch detected on TG nodes")

    def get_image_version_from_build(self, local_image_path: str) -> str:
        """Get image version from image built in server."""

        img_cmd = (
            f"chmod a+x {local_image_path}; {os.path.abspath(local_image_path)} -m"
        )

        output, error = subprocess.Popen(
            img_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True,
        ).communicate()

        if error:
            raise DeviceCmdError(
                f"Error: {error} : Could not read built image version."
            )
        self.log_to_ctf(f"Image version: {output }")

        # Parse metadata as json
        status = cast(Dict, json.loads(output))
        return str(status["version"] + "\n")

    def check_image_upgrade_required(self, local_image_path: str) -> bool:
        """Check if a image upgrade is required by comparing
        build version with image version running on the nodes.
        """
        local_image_version = self.get_image_version_from_build(local_image_path)
        # TODO (ipurush) - Get a map of versions to nodes and upgrade nodes which
        # need an image upgrade
        running_versions = self.get_tg_version()
        if len(running_versions) > 1 or local_image_version not in running_versions:
            # At least one node needs an image upgrade
            return True

        # Skip if built image version is same as the images running on the nodes
        self.log_to_ctf(
            "Skipping image upgrade - all nodes are already running the target "
            + f"version: {local_image_version}",
            "info",
        )
        return False

    def run_image_upgrade_sequence(self, local_image_path: str) -> int:
        node_ids: List[int] = self.get_tg_devices()
        self.log_to_ctf("Upgrading images on all nodes", "info")

        # Download images on all nodes
        self.copy_files_parallel(local_image_path, TG_IMAGE_BIN_FILE, node_ids)
        # Upgrade and verify
        # pyre-fixme[7]: Expected `int` but got implicit return value of `None`.
        self.upgrade_and_verify_tg_images(TG_IMAGE_BIN_FILE, node_ids)

    def delete_upgrade_state_cache(self, node_ids: Optional[List[int]] = None) -> None:
        """Delete the upgrade state cache on the given nodes."""
        self.log_to_ctf("Deleting upgrade state cache on nodes")
        futures: Dict = self.run_cmd("rm -fv /data/upgradeCache.json", node_ids)
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(f"Node {result['node_id']}: {result['message']}")

    def run_sysdump(
        self, output_path: str, node_ids: Optional[List[int]] = None
    ) -> None:
        """Run the sysdump generation script on all given nodes."""
        self.log_to_ctf("Generating sysdump archives", "info")
        cmd: str = f"/usr/sbin/sys_dump -o {output_path}"
        futures: Dict = self.run_cmd(cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                self.log_to_ctf(
                    f"Node {result['node_id']}: sysdump failed!\n{result['error']}",
                    "error",
                )
            else:
                self.log_to_ctf(f"Node {result['node_id']}: sysdump complete.")


if __name__ == "__main__":
    LOG.error("Do not run directly")
