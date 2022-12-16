#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Library containing actions for x86 Terragraph services (ex. e2e_controller,
api_service).
"""

import json
import logging
from argparse import Namespace
from typing import Any, cast, Dict, List, Optional, Set

from ctf.ctf_client.runner.exceptions import (
    DeviceCmdError,
    DeviceConfigError,
    TestFailed,
)
from terragraph.ctf.tg import BaseTgCtfTest


LOG = logging.getLogger(__name__)

# X86 image file path
TG_LOCAL_IMAGE_BIN_FILE = "/tmp/terragraph-image-x86-tgx86.tar.gz"
# X86 remote rootfs dir
TG_REMOTE_ROOTFS_DIR = "/tmp/terragraph-rootfs-ctf"
# X86 remote /data dir (inside TG_REMOTE_ROOTFS_DIR)
TG_REMOTE_ROOTFS_DATA_DIR = "/data"
# X86 remote log dir (inside TG_REMOTE_ROOTFS_DIR)
TG_REMOTE_LOG_DIR = f"{TG_REMOTE_ROOTFS_DATA_DIR}/ctf-logs"
# X86 remote topology file path (inside TG_REMOTE_ROOTFS_DIR)
TG_REMOTE_TOPOLOGY_FILE = f"{TG_REMOTE_ROOTFS_DATA_DIR}/e2e_topology.conf"
# X86 remote node images dir (inside TG_REMOTE_ROOTFS_DIR)
TG_REMOTE_IMAGE_DIR = f"{TG_REMOTE_ROOTFS_DATA_DIR}/images"
# Default api_service HTTP port
API_SERVICE_HTTP_PORT = 8080


class x86TgCtfTest(BaseTgCtfTest):
    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(x86TgCtfTest, x86TgCtfTest).test_params()
        test_params["x86_image_path"] = {
            "desc": "If specified, copy and install the given x86 software image"
        }
        test_params["managed_config"] = {
            "desc": "Enable managed config on the E2E controller",
            "default": True,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["keep_ctrl_alive"] = {
            "desc": "Keep E2E controller services alive after end of the test",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }

        return test_params

    def get_common_x86_test_steps(self) -> Dict:
        return {
            "setup_x86_services": {
                "name": "Set up x86 Terragraph services",
                "function": self.setup_x86_tg_services,
                "function_args": (),
                "success_msg": "Finished setting up x86 Terragraph services.",
            },
            "start_x86_services": {
                "name": "Start x86 Terragraph services",
                "function": self.start_x86_tg_services,
                "function_args": (),
                "success_msg": "All x86 Terragraph services were started.",
            },
            "start_x86_bt_tracker": {
                "name": "Start x86 BitTorrent tracker",
                "function": self.start_x86_opentracker,
                "function_args": (),
                "success_msg": "opentracker was started.",
            },
        }

    def find_x86_tg_host_id(self, nodes_data: Optional[Dict] = None) -> int:
        """Find the id of the x86 Terragraph host. Raise an exception if
        there are multiple or none defined in self.nodes_data.
        """
        if nodes_data is None:
            nodes_data = self.nodes_data

        id = None
        for node_id, v in nodes_data.items():
            if "e2e_controller" in v:
                if id is None:
                    id = int(node_id)
                else:
                    err = "Multiple x86 Terragraph host IDs found"
                    LOG.debug(err)
                    raise DeviceConfigError(err)
        if id is None:
            raise DeviceConfigError("Missing 'e2e_controller' field in node data")
        return id

    def nodes_data_amend_test_args(self, nodes_data: Dict, num_nodes: int) -> Dict:
        merged_nodes_data = super().nodes_data_amend_test_args(nodes_data, num_nodes)

        # Fetch controller id which can be used with test steps
        e2e_ctrl_id = self.find_x86_tg_host_id(merged_nodes_data)
        # Set network override for sysParams.managedConfig
        self.merge_dict(
            merged_nodes_data,
            {
                e2e_ctrl_id: {
                    "e2e_controller": {
                        "configs": {
                            "network_config_overrides": {
                                "sysParams": {
                                    "managedConfig": self.test_args["managed_config"]
                                },
                                "statsAgentParams": {
                                    "endpointParams": {
                                        "kafkaParams": {
                                            "config": {
                                                "brokerEndpointList": self.test_args.get(
                                                    "kafka_endpoint", ""
                                                )
                                            }
                                        }
                                    }
                                },
                                "fluentdParams": {
                                    "endpoints": {
                                        "CTF": {
                                            "host": self.test_args.get(
                                                "fluentd_host", ""
                                            ),
                                            "port": self.test_args.get(
                                                "fluentd_port", 24224
                                            ),
                                        }
                                    },
                                },
                            }
                        }
                    }
                }
            },
        )

        if self.test_args.get("enable_fw_logs", None):
            self.merge_dict(
                merged_nodes_data,
                {
                    e2e_ctrl_id: {
                        "e2e_controller": {
                            "configs": {
                                "network_config_overrides": {
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
                                        },
                                    },
                                }
                            }
                        }
                    }
                },
            )

        return merged_nodes_data

    def stop_ctrl_services(self) -> None:
        """Stop E2E controller and API service."""
        node_id = self.find_x86_tg_host_id()
        self._stop_x86_tg_service(node_id, "e2e_controller")
        self._stop_x86_tg_service(node_id, "api_service")

    def pre_run(self) -> None:
        """
        stop and kill e2e controller service before regular pre-run functions because
        an active e2e controller service overwrites the node config changes and unexpectedly reboots the nodes.
        """
        self.stop_ctrl_services()
        super().pre_run()

    def post_run(self) -> None:
        super().post_run()
        if not self.test_args["keep_ctrl_alive"]:
            self.stop_ctrl_services()

    def _chroot_cmd(self, cmd: str) -> str:
        """Wrap the given command in 'chroot'."""
        return f"sudo chroot {TG_REMOTE_ROOTFS_DIR} {cmd}"

    def _start_x86_tg_service(
        self, node_id: int, service: str, args: Optional[List[str]] = None
    ) -> None:
        """Start an x86 Terragraph service in the background."""
        service_cmd: str = self._chroot_cmd(
            f"{service} {' '.join(args if args else [])}"
        )
        log_path: str = f"{TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_LOG_DIR}/{service}.log"
        cmd: str = f"{service_cmd} > {log_path} 2>&1 &"
        self.log_to_ctf(f"Starting {service}: {cmd}")
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: Failed to start {service}: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

    def _stop_x86_tg_service(self, node_id: int, service: str) -> None:
        """Stop an x86 Terragraph service."""
        cmd: str = f"systemctl stop {service}; pkill -9 {service}"
        self.log_to_ctf(f"Stopping {service}: {cmd}")
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])

    def setup_x86_tg_services(
        self,
        node_id: Optional[int] = None,
        e2e_topology: Optional[Dict] = None,
        e2e_configs: Optional[Dict] = None,
    ) -> None:
        """Set up the environment for running x86 Terragraph services."""
        if node_id is None:
            node_id = self.find_x86_tg_host_id()
        if e2e_topology is None:
            e2e_topology = self.read_nodes_data([node_id, "e2e_controller", "topology"])
        if e2e_configs is None:
            e2e_configs = (
                self.read_nodes_data(
                    [node_id, "e2e_controller", "configs"], required=False
                )
                or {}
            )

        # Kill any running services
        self._stop_x86_tg_service(node_id, "e2e_controller")
        self._stop_x86_tg_service(node_id, "api_service")

        # Clean up old data dir (config/log files, etc.)
        cmd: str = f"rm -rfv {TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_ROOTFS_DATA_DIR}/*"
        self.log_to_ctf(f"Wiping old data directory: {cmd}")
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])

        # Create log dir
        log_dir: str = f"{TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_LOG_DIR}"
        cmd = f"mkdir -p {log_dir}"
        self.log_to_ctf(f"Creating log directory: {cmd}")
        futures = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])

        # Add log dir to CTF results
        self.logfiles.setdefault("terragraph_controller", []).append(log_dir)

        # Push E2E config files
        self.set_e2e_config_files(node_id, e2e_configs, TG_REMOTE_ROOTFS_DIR)

        # Push E2E topology file
        self.set_topology_file(
            node_id, e2e_topology, f"{TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_TOPOLOGY_FILE}"
        )

    def start_x86_tg_services(
        self,
        node_id: Optional[int] = None,
        global_iface: Optional[str] = None,
        service_names: Optional[Set[str]] = None,
    ) -> None:
        """Start all Terragraph services."""
        if node_id is None:
            node_id = self.find_x86_tg_host_id()
        if global_iface is None:
            global_iface = (
                self.read_nodes_data(
                    [node_id, "e2e_controller", "global_iface"], required=False
                )
                or "ens160"
            )

        # list of pairs with service name and its args
        service_name_args = [
            (
                "e2e_controller",
                [
                    "--v=3",
                    f"--topology_file={TG_REMOTE_TOPOLOGY_FILE}",
                    f"--bt_tracker_ipv6_global_addressable_ifname={global_iface}",
                ],
            ),
            (
                "api_service",
                [
                    f"--http_port={API_SERVICE_HTTP_PORT}",
                    f"--ipv6_global_addressable_ifname={global_iface}",
                ],
            ),
        ]
        for service_name, args in service_name_args:
            if not service_names or service_name in service_names:
                self._start_x86_tg_service(
                    node_id,
                    service=service_name,
                    args=args,
                )

    def start_x86_opentracker(self, node_id: Optional[int] = None) -> None:
        """Start the 'opentracker' service (BitTorrent tracker)."""
        if node_id is None:
            node_id = self.find_x86_tg_host_id()

        self._stop_x86_tg_service(node_id, "opentracker")
        self._start_x86_tg_service(node_id, "opentracker", ["-p 6969"])

    def push_x86_image(
        self, image_file_path: str, node_id: Optional[int] = None
    ) -> None:
        """Push the x86 image to the given device and extract it."""
        if node_id is None:
            node_id = self.find_x86_tg_host_id()

        # SCP image
        device = self.device_info[node_id]
        if not self.push_file(
            device.connection, image_file_path, TG_LOCAL_IMAGE_BIN_FILE, recursive=False
        ):
            error_msg = f"Failed to push x86 image to node {node_id}: {image_file_path}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)

        # Extract image
        cmd: str = (
            f"rm -rf {TG_REMOTE_ROOTFS_DIR}; "
            + f"mkdir -p {TG_REMOTE_ROOTFS_DIR}; "
            + f"tar -xf {TG_LOCAL_IMAGE_BIN_FILE} -C {TG_REMOTE_ROOTFS_DIR}"
        )
        self.log_to_ctf(f"Extracting x86 image: {cmd}")
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: Failed to extract x86 image: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

        # Delete archive
        cmd = f"rm -f {TG_LOCAL_IMAGE_BIN_FILE}"
        self.log_to_ctf(f"Deleting x86 archive: {cmd}")
        futures = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])
            if not result["success"]:
                self.log_to_ctf(
                    f"Node {result['node_id']}: Failed to delete x86 archive", "warning"
                )

        # Post-setup
        cmd = self._chroot_cmd("mknod /dev/urandom c 1 9 2>/dev/null")
        self.log_to_ctf(f"Setting up /dev/urandom: {cmd}")
        futures = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: Failed to create /dev/urandom: "
                    + result["error"]
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

    def push_tg_image_to_x86(
        self,
        image_file_path: str,
        tg_remote_image_file: str = "tg-image.bin",
        node_id: Optional[int] = None,
    ):
        """Push the Terragraph image to the given device's node image directory."""
        if node_id is None:
            node_id = self.find_x86_tg_host_id()

        # Create image dir
        remote_image_dir = f"{TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_IMAGE_DIR}"
        cmd: str = f"mkdir -p {remote_image_dir}"
        self.log_to_ctf(f"Creating node image directory: {cmd}")
        futures = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])

        # SCP image
        remote_image_file = (
            f"{TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_IMAGE_DIR}/{tg_remote_image_file}"
        )
        device = self.device_info[node_id]
        if not self.push_file(
            device.connection, image_file_path, remote_image_file, recursive=False
        ):
            error_msg = f"Failed to push TG image to node {node_id}: {image_file_path}"
            self.log_to_ctf(error_msg, "error")
            raise DeviceCmdError(error_msg)
        self.log_to_ctf(f"Pushed TG image to {remote_image_file}")

        # make image an executable
        cmd = f"chmod a+x {remote_image_file}"
        self.log_to_ctf(f"Running: {cmd}")
        futures = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            if result["message"].strip():
                self.log_to_ctf(result["message"])

    def api_service_request(
        self,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        node_id: Optional[int] = None,
    ) -> Dict:
        """Send an api_service request and return the parsed result."""
        if node_id is None:
            node_id = self.find_x86_tg_host_id()

        url: str = f"http://localhost:{API_SERVICE_HTTP_PORT}/api/{method}"
        cmd: str = f"curl -d '{json.dumps(data if data else {})}' {url}"
        futures: Dict = self.run_cmd(cmd, [node_id])
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: api_service request failed: "
                    + f"{cmd}\n{output}\n{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            # Expect JSON output
            try:
                d = json.loads(output)
            except ValueError:
                error_msg = (
                    f"Node {result['node_id']}: api_service request returned "
                    + f"invalid JSON: {cmd}\n{output}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"{cmd}\n{json.dumps(d, indent=2, sort_keys=True)}")
            # pyre-fixme[7]: Expected `Dict[typing.Any, typing.Any]` but got
            #  implicit return value of `None`.
            return cast(Dict, d)

    def show_topology_and_verify(
        self,
        filter: Optional[str] = "",
        expected_num_nodes: Optional[int] = 0,
        expected_num_links: Optional[int] = 0,
    ) -> None:
        # look up tables for easy interpretation of topology table
        link_type = {1: "WIRELESS", 2: "ETHERNET"}
        node_type = {1: "CN", 2: "DN"}
        node_status = {1: "OFFLINE", 2: "ONLINE", 3: "ONLINE_INITIATOR"}

        rtrn_topology: Dict = self.api_service_request("getTopology")
        nodes = rtrn_topology["nodes"]
        links = rtrn_topology["links"]
        sites = rtrn_topology["sites"]
        if filter == "nodes_offline_links_down":
            nodes = [node for node in nodes if node_status[node["status"]] == "OFFLINE"]
            links = [link for link in links if not bool(link["is_alive"])]

        title_string_nodes: str = (
            "\nNodeName\tMacAddr\t\t\tPopNode\tNodeType\tStatus\t\t\tSiteName\n"
        )
        title_string_links: str = "\nLinkName\t\t\t\tANodeName\tZNodeName\tAlive\tLinkType\t\tLinkupAttempts\n"
        title_string_sites: str = (
            "\nSiteName\tLatitude\tLongitude\tAltitude\tAccuracy\n"
        )

        print_nodes: str = title_string_nodes
        for node in nodes:
            print_nodes += (
                f"{node['name']}\t{node['mac_addr']}\t{str(node['pop_node']):5}"
                + f"\t{node_type[node['node_type']]}\t\t\t{node_status[node['status']]:>16}"
                + f"\t{node['site_name']}\n"
            )
        print_links: str = title_string_links
        for link in links:
            print_links += (
                f"{link['name']}\t{link['a_node_name']}\t{link['z_node_name']}"
                + f"\t{str(link['is_alive']):5}\t{link_type[link['link_type']]}\t{link['linkup_attempts']}\n"
            )
        print_sites: str = title_string_sites
        for site in sites:
            print_sites += (
                f"{site['name']}\t\t{site['location']['latitude']}\t{site['location']['longitude']}"
                + f"\t\t{site['location']['altitude']}\t\t{site['location']['accuracy']}\n"
            )

        if filter == "nodes":
            print_select = print_nodes
        elif filter == "links":
            print_select = print_links
        elif filter == "sites":
            print_select = print_sites
        elif filter == "nodes_offline_links_down":
            print_select = print_nodes + print_links
        else:
            print_select = print_nodes + print_links + print_sites

        self.log_to_ctf(print_select, "info")

        if expected_num_nodes != 0 and len(nodes) != expected_num_nodes:
            raise TestFailed(
                "Nodes in topology with filter {filter} did not match with expected nodes"
            )

        if expected_num_links != 0 and len(links) != expected_num_links:
            raise TestFailed(
                "Links in topology with filter {filter} did not match with expected links"
            )

        return

    def api_check_link_state(
        self, link_name: str, expected_is_alive: Optional[bool] = True
    ) -> None:

        method: str = "getLink"
        data: Optional[Dict[str, Any]] = {
            "name": link_name,
        }

        api_result = self.api_service_request(method=method, data=data)
        self.log_to_ctf("api_result:\n" + str(api_result))

        is_alive = api_result.get("is_alive")
        link_state = "Up" if is_alive else "Down"

        self.log_to_ctf(f"link: {link_name} is {link_state}.")

        expected_link_state = "Up" if expected_is_alive else "Down"

        if is_alive != expected_is_alive:
            raise TestFailed(
                f"link: {link_name} state is {link_state}, expected value was {expected_link_state}."
            )

    def create_node_overrides(
        self, config: Dict, node_names: Optional[List[str]] = None
    ) -> Dict:
        """
        creates node overrides for input config in the format radioParamsBase.fwParams.forceGpsDisable
        and node ids.
        for example: consider input config of radioParamsBase.fwParams.forceGpsDisable
                     and node_id=1 in setup 92
        this method generated output in the format of
        {'overrides': '{"IF-404-8A": {"radioParamsBase": {"fwParams": {"forceGpsDisable": 1}}}}')

        """
        node_overrides: Dict[str, Dict] = {}
        overrides: Dict[str, str] = {}

        if not node_names:
            e2e_ctrl_node_id = self.find_x86_tg_host_id()
            e2e_topology = self.nodes_data[e2e_ctrl_node_id]["e2e_controller"][
                "topology"
            ]
            node_names = [node["name"] for node in e2e_topology["nodes"]]

        path = config["key"].split(".")
        result = {}
        obj = result
        for k in path[:-1]:
            obj = obj.setdefault(k, {})
        obj[path[-1]] = config["value"]

        for node_name in node_names:
            node_overrides[node_name] = result
        node_overrides_json_encoded = json.dumps(node_overrides)
        overrides["overrides"] = node_overrides_json_encoded
        return overrides

    def get_service_logs(self, service: str) -> None:
        """Dump the logs for the given service."""
        e2e_ctrl_node_id = self.find_x86_tg_host_id()
        log_path: str = f"{TG_REMOTE_ROOTFS_DIR}{TG_REMOTE_LOG_DIR}/{service}.log"
        futures: Dict = self.run_cmd(f"cat {log_path}", [e2e_ctrl_node_id])

        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise DeviceCmdError(
                    f"Failed to read X86 {service} log from device {result['node_id']}"
                )
            self.log_to_ctf(f"X86 {service} log: \n{result['message']}")

    def get_e2e_cntrl_version(self) -> Set[str]:
        """Retrieve the e2e controller version string."""
        e2e_ctrl_node_id = self.find_x86_tg_host_id()
        version_path: str = f"{TG_REMOTE_ROOTFS_DIR}/etc/tgversion"
        futures: Dict = self.run_cmd(f"cat {version_path}", [e2e_ctrl_node_id])
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
