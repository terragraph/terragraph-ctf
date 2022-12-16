#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import json
import logging
import time
from argparse import Namespace
from collections import defaultdict
from concurrent.futures import as_completed, ThreadPoolExecutor, TimeoutError
from os import makedirs, path
from pathlib import Path
from string import Template
from tempfile import TemporaryDirectory
from threading import Event
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed, TestUsageError
from ctf.ctf_client.runner.lib import (
    create_ssh_connection,
    get_ssh_connection_class,
    TagLevel,
)
from requests.exceptions import RequestException
from terragraph.ctf.consts import TgCtfConsts
from terragraph.ctf.puma import PumaTgCtfTest

LOG = logging.getLogger(__name__)

TgCtfSITConsts: Dict = {
    # ElasticSearch IndexPattern
    "ELASTICSEARCH_INDEX_PATTERN_CHECK_ASSERTS": "fluentd-log-node-vpp_vnet*",
    # Text to search for in the ES logs
    "ELASTICSEARCH_ASSERT_PATTERN": "assert codes FW",
    # elastic query dsl
    "ELASTICSEARCH_QUERY_CHECK_ASSERT": '{"version":true,"size":50,"query":{"bool":{"filter":[{"match_phrase":{"log":"$assert_pattern"}},{"bool":{"should":$source_field_query_dsl,"minimum_should_match":1}},{"range":{"ingest_time":{"format":"strict_date_optional_time","gte":"$start_time","lte":"$end_time"}}}]}}}',
    # List of grafana dashboards names with format [{"dashboard_uid": "<grafana dashboard uid>", "dashboard_name": "<name to display on result page>"}]
    "GRAFANA_DASHBOARDS": [
        {"dashboard_uid": "link_prom", "dashboard_name": "Link Metrics"}
    ],
    # List of kibana dashboards names with format [{"dashboard_uid": "<kibana dashboard uid>", "dashboard_name": "<name to display on result page>"}]
    "KIBANA_DASHBOARDS": [
        {"dashboard_uid": "puma_logs", "dashboard_name": "Puma Logs"}
    ],
    # metrics to be pulled on assert
    "ELASTICSEARCH_ASSERT_METRICS": [
        "fluentd-log-node-vpp_vnet*",
        "fluentd-log-node-fw_trace*",
    ],
    # NOTE: Change the test ID to CTF UI test which will run TgCollectLogs test for Elasticsearch and Prometheus logs collection
    # TODO: Fetch this test id with new CTF api
    "TG_COLLECT_LOGS_UI_TEST_ID": 68354,
}
# Setup meta information will be maintained under nodes_data/setup.json with key "0"
SETUP_INFO_ID = 0
MAX_LOG_COLLECTION_DURATION = 900
LOG_COLLECTION_BUFFER_DURATION = 600


class ProxyDevice(object):
    """ProxyDevice is introduced to bypass the port 80 restriction from Tupperware(TW) instance.
    The TW instance will use port 22 to access ProxyDevice and run the command on host.
    ProxyDevice is added specifically to reach the NMS instance in the lab network
    """

    def __init__(self, connection: Dict) -> None:
        connection_obj = get_ssh_connection_class(connection)
        _, self.connection = create_ssh_connection(connection_obj)

    def action_custom_command(self, cmd, timeout=60) -> Dict:
        """Run the command on proxy server
        return: result dictionary with the following format
        {
            "error": <0 = success, 1 = failure>,
            "message": "<stdout>",
            "stderr": "<stderr>",
            "returncode": <int>,
            "connection_error": <bool>
        }
        Raises exception on connection failure
        """
        result = self.connection.send_command(cmd=cmd, timeout=timeout)
        if result.get("connection_error", None):
            raise DeviceCmdError(
                f"NMS proxy server connection failure: {result['message']}"
            )
        return result


# Elasticsearch has a maximum number of results it will return from a single query.
# This constant is used several places in this file.
MAX_ES_QUERY_RESPONSES = 10_000

# Number of worker threads to allow for stat and log collection.
# TODO (T109859801): The number of worker threads might be better based on the number of nodes used in a test.
# TODO (T111307427): Another idea is to query the NMS proxy server for CPU count.
MAX_QUERY_AND_SAVE_LOGS_WORKER_THREADS = 4


class SitPumaTgCtfTest(PumaTgCtfTest):
    """CTF Terragraph test base class extended with Puma System Integration testing (SIT) specific
    functionality.
    """

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_data = {}
        if self.test_args["test_data"]:
            self.test_data = json.load(open(self.test_args["test_data"]))
        self.test_meta_info = self.test_data.get("test_meta_info", {})
        self.nodes_data_amend_config = self.test_data.get("nodes_data_amend", {})
        self.nodes_data_amend_all_config = self.test_data.get(
            "nodes_data_amend_all", {}
        )
        self.TEST_NAME = f"{self.TEST_NAME}: {self.test_meta_info.get('test_code', '')}"
        self.DESCRIPTION = f"{self.DESCRIPTION}: {self.test_meta_info.get('test_code_description', '')}"
        self.nms_proxy = None
        self.query_and_save_pool = ThreadPoolExecutor(
            thread_name_prefix="_query_and_save",
            max_workers=self.test_args["collection_threadpool_size"],
        )
        # Start time of the test (monotonic to track elapsed time regardless of system time changes)
        self.test_start_time_monotonic = int(time.monotonic())
        # Provide a thread "exit now" event for looping threads to query for early exiting when resource_cleanup is called.
        self.thread_exit_event = Event()

    def __del__(self) -> None:
        self.cleanupThreadPool(self.query_and_save_pool)
        super().__del__()

    def resource_cleanup(self) -> None:
        super().resource_cleanup()
        # Tell running collection threads a chance to stop.
        self.thread_exit_event.set()
        # Give threads extra time time to react to exit_event.
        LOG.info("Give threads time to react to exit_event.")
        time.sleep(60)
        self.finish_test_run(False)

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            SitPumaTgCtfTest, SitPumaTgCtfTest
        ).test_params()
        test_params["save_sysdump"]["default"] = True
        test_params["enable_fw_logs"]["default"] = True
        test_params["fw_log_level_fb"]["default"] = "debug"
        test_params["test_data"] = {
            "desc": (
                "path to json file defining test meta data, test specific node config, "
                + "traffic profiles and other test specific configurations"
            ),
            "required": True,
        }
        test_params["elasticsearch_endpoint"] = {
            "desc": "elastisearch endpoint to query for logs",
            "default": TgCtfConsts.get("DEFAULT_ELASTICSEARCH_ENDPOINT", None),
        }
        test_params["grafana_endpoint"] = {
            "desc": "Grafana server end point url for visualization",
            "default": TgCtfConsts.get("DEFAULT_GRAFANA_ENDPOINT", ""),
        }
        test_params["kibana_endpoint"] = {
            "desc": "Kibana server end point url for visualization",
            "default": TgCtfConsts.get("DEFAULT_KIBANA_ENDPOINT", ""),
        }
        test_params["prometheus_endpoint"] = {
            "desc": "prometheus endpoint to query for stats",
            "default": TgCtfConsts.get("DEFAULT_PROMETHEUS_ENDPOINT", None),
        }
        test_params["collect_stats"] = {
            "desc": "write SIT stats as CVS files to CTF",
            "default": True,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["use_nms_proxy"] = {
            "desc": "Use proxy server to reach NMS server",
            "default": True,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["managed_config"] = {
            "desc": "Enable managed config on the E2E controller",
            "default": True,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["set_system_time"] = {
            "desc": "Force system time update via NTP",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        test_params["collection_threadpool_size"] = {
            "desc": "maximum number of threads to use for collection",
            "default": MAX_QUERY_AND_SAVE_LOGS_WORKER_THREADS,
            "convert": int,
        }
        test_params["skip_nms_log_collection_for_cores"] = {
            "desc": "skip the [nms] elasticsearch and prometheus logs collection for step even if cores were observed",
            "default": False,
            "convert": lambda k: k.lower() == "true",
        }
        return test_params

    def _set_system_time(self, node_ids: Optional[List[int]] = None) -> None:
        """Force system time update via NTP."""

        if not self.test_args["set_system_time"]:
            LOG.info("_set_system_time | skipping update")
            return

        update_time_cmd = "ip netns exec oob /usr/sbin/time_set >/dev/null 2>/dev/null"
        futures: Dict = self.run_cmd(update_time_cmd, node_ids)
        for result in self.wait_for_cmds(futures):
            if result["error"]:
                raise DeviceCmdError(
                    f"_set_system_time | failed on node_id {result['node_id']} | error {result['error']}"
                )
            else:
                LOG.info(f"_set_system_time | ok on node_id {result['node_id']}")

    def pre_run(self) -> None:
        super().pre_run()
        self._set_system_time()  # NOTE May need to be done earlier and also after every reboot.

    def log_test_info(self) -> None:
        super().log_test_info()
        if self.test_args["test_data"]:
            self.log_to_ctf(f"Test config: \n {self.test_data}")

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        merged_nodes_data = super().nodes_data_amend(num_nodes)
        if self.nodes_data_amend_config:
            self.merge_dict(
                merged_nodes_data,
                {
                    int(node_id): config
                    for node_id, config in self.nodes_data_amend_config.items()
                },
            )
        if self.nodes_data_amend_all_config:
            self.merge_dict(
                merged_nodes_data,
                {
                    node_id: self.nodes_data_amend_all_config
                    for node_id in range(1, num_nodes + 1)
                },
            )
        return merged_nodes_data

    def nodes_data_amend_test_args(self, nodes_data: Dict, num_nodes: int):
        merged_nodes_data = super().nodes_data_amend_test_args(nodes_data, num_nodes)

        self.merge_dict(
            merged_nodes_data,
            {
                i: {
                    "node_config": {
                        "radioParamsBase": {"fwParams": {"channel": 2}},
                        "sysParams": {
                            "managedConfig": self.test_args["managed_config"]
                        },
                    }
                }
                for i in range(1, num_nodes + 1)
            },
        )

        return merged_nodes_data

    def post_test_init(self) -> None:
        super().post_test_init()
        if self.test_args["use_nms_proxy"]:
            # Use nms proxy server details specifed in nodes_data (setup.json)
            nms_proxy_connection = self.read_nodes_data(
                [SETUP_INFO_ID, "nms_proxy_server"], False
            )
            if not nms_proxy_connection:
                # Use nms proxy server details from TgCtfConsts if not provided with setup.json
                nms_proxy_connection = TgCtfConsts.get("NMS_PROXY_SERVER", None)
            self.nms_proxy = ProxyDevice(nms_proxy_connection)
            self.log_to_ctf("Using nms proxy server", "info")

    def reset_config_and_reboot(self):
        """
        reset node_config.json to default and reboot all nodes to apply default config
        """

        cmd = "rm -f /data/cfg/node_config.json; sleep 5; diff_node_config | grep -q -m 1 'No differences found'"

        futures: Dict = self.run_cmd(cmd)
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = f"{cmd} failed on node {result['node_id']} | message {result['message']} | stderr {result['stderr']}"
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\t{output}")

        self.reboot_and_wait(self.device_info)

    def _collect_logfiles_wrapper(self) -> None:
        """Call `collect_logfiles()` with `self.logfiles`."""
        # needed to allow subclasses to modify self.logfiles
        super()._collect_logfiles_wrapper()

        # TODO: Move to tear down step after log collection
        self.reset_config_and_reboot()

    def secondary_step_action(self, test_action_result_id: int, step: Dict) -> None:
        super().secondary_step_action(test_action_result_id, step)
        if step.get("found_error_tags", None):
            if self.test_args["skip_nms_log_collection_for_cores"]:
                self.log_to_ctf("NMS log collection is disabled for cores", "info")
                return
            node_macs = self.get_all_node_mac()
            network = self.read_nodes_data([SETUP_INFO_ID, "setup", "name"], False)
            self.query_and_save_logs_to_ctf(
                step["start_time"],
                step["end_time"],
                TgCtfSITConsts.get("ELASTICSEARCH_ASSERT_METRICS", None),
                node_macs,
                network,
                test_action_result_id,
            )

    def interface_info(self, clear: bool = False) -> None:
        """Clears vppctl interface info if clear is true else will dump
        vppctl intreface info
        """

        if clear:
            cmd = (
                "echo '# vppctl clear interface'; vppctl clear interface;"
                "echo '# vppctl clear error'; vppctl clear error;"
                "echo '# vppctl clear hardware'; vppctl clear hardware;"
                "echo '# vppctl clear run'; vppctl clear run;"
            )
        else:
            cmd = (
                "echo '# vppctl show interface'; vppctl show interface;"
                "echo '# vppctl show error'; vppctl show error;"
                "echo '# vppctl show hardware'; vppctl show hardware;"
                "echo '# vppctl show run'; vppctl show run;"
            )

        futures: Dict = self.run_cmd(cmd)
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to run cmd: "
                    + f"{cmd}\n{output}\n{result['error']}"
                )
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{output}")

    def steps_ping_nodes_from_src(
        self,
        src_node_id,
        dest_node_ids: List[int],
        interface: str = "lo",
    ):
        steps = []
        for node_id in dest_node_ids:
            steps.append(
                {
                    "name": f"Run ping from {src_node_id} to {node_id}",
                    "function": self.ping_nodes,
                    "function_args": (src_node_id, node_id, interface),
                    "success_msg": "ping ran successfully",
                },
            )
        return steps

    def switch_gpsd(self, node_id: int, enable: bool):
        """
        Start or stop gpsd for the specified `node_id`
        `enable`: True (start), False (stop)
        """

        if enable:
            cmd = "sv start gpsd"
        else:
            cmd = "if ! sv force-stop gpsd; then sleep 1; sv status gpsd; fi"

        self.log_to_ctf(cmd)

        futures: Dict = self.run_cmd(cmd, node_ids=[node_id])
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to run cmd: "
                    + f"{cmd}\n{output}\n{result['error']}"
                )
                raise DeviceCmdError(error_msg)

            self.log_to_ctf(f"Node {result['node_id']}: {cmd}\n{output}")

    def steps_ping_lo_all_tg_nodes_from_src(
        self,
        src_node_id: int,
        skip_node_ids: Optional[List[int]] = None,
        is_cont_on_fail: Optional[bool] = False,
        is_concurrent: Optional[bool] = False,
        start_delay: Optional[int] = 0,
        count: Optional[int] = 25,
        wait_time: Optional[int] = 1,
        interval: Optional[float] = 1,
    ) -> List[Dict]:
        # start with empty list
        ping_all_steps = []
        for node_id in self.get_tg_devices():
            if node_id == src_node_id:
                continue
            if skip_node_ids and (node_id in skip_node_ids):
                continue
            ping_all_steps.append(
                {
                    "name": f"Ping Over lo link from src node id:{src_node_id} to dst node id:{node_id}",
                    "function": self.ping_nodes,
                    "function_args": (
                        src_node_id,
                        node_id,
                        "lo",
                        "global",
                        count,
                        wait_time,
                        interval,
                    ),
                    "success_msg": f"Ping Over lo link from src node id:{src_node_id} to dst node id:{node_id} succeeded",
                    "error_handler": self.get_common_error_handler(),
                    "continue_on_failure": is_cont_on_fail,
                    "concurrent": is_concurrent,
                    "delay": start_delay,
                }
            )
        return ping_all_steps

    def set_attenuation_x_db(self, attenuator_id: int, attenuation_level: int):
        self.log_to_ctf(f"attenuator_id: {attenuator_id}")
        self.log_to_ctf(f"attenuation_level: {attenuation_level}")
        attenuator_ids: Optional[List[int]] = [attenuator_id]
        self.set_front_back_attenuation_x_db(attenuator_ids, attenuation_level, "front")
        self.set_front_back_attenuation_x_db(attenuator_ids, attenuation_level, "back")
        self.log_to_ctf(f"Attenuation set to {attenuation_level} dB")

    def set_front_back_attenuation_x_db(
        self,
        attenuator_id: Optional[List[int]],
        attenutation_level: int,
        attenuator_side: str,
    ):
        cmd = f"python /home/odroid/coffin/set_coffin_atten.py -i {attenuator_side} --attendB {attenutation_level}"
        self.log_to_ctf(cmd)
        futures: Dict = self.run_cmd(cmd, attenuator_id)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Attenuator {result['node_id']}: {cmd} failed: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(f"RESULT_MESSAGE: {result['message']}")

    def get_meta_data_for_step(self, step) -> List[Dict]:
        step_meta_data = super().get_meta_data_for_step(step)
        cores_data = self._query_cores_for_logs_and_tag(step)
        if cores_data:
            step_meta_data.append(cores_data)
        asserts_data = self._query_es_for_asserts_logs_and_tags(step)
        if asserts_data:
            step_meta_data.append(asserts_data)
        return step_meta_data

    def delete_files_on_node(self, node_files: Dict[int, List], step_name: str) -> None:
        try:

            futures: Dict = {}
            for node_id, files in node_files.items():
                if len(files) > 0:
                    cmd = f"rm -v {' '.join(files)}"
                    futures.update(self.run_cmd(cmd, node_ids=[node_id]))

            for result in self.wait_for_cmds(futures, timeout=self.timeout):
                if not result["success"]:
                    self.log_to_ctf(
                        f"Node {result['node_id']} failed to remove files",
                        "warning",
                    )
                else:
                    self.log_to_ctf(f"Deleted files from {result['node_id']}", "info")
        except Exception as e:
            error_msg = (
                f"Exception while deleting files for step {step_name} {e} ({type(e)}) "
            )
            LOG.warning(error_msg)
            self.log_to_ctf(error_msg, "warning")

    def _query_cores_for_logs_and_tag(self, step: Dict) -> Optional[Dict]:
        """Get cores files and tags if exist from all TG nodes"""
        cores_thread_pool = None
        try:
            self.log_to_ctf("Checking for cores", "info")
            futures: Dict = {}
            cores_path = "/var/volatile/cores/"
            cores_timeout = 300  # wait for 300s for cores compression
            tg_devices = self.get_tg_devices()
            cores_thread_pool = ThreadPoolExecutor(
                thread_name_prefix="Cores", max_workers=len(tg_devices)
            )
            for node_id in tg_devices:
                futures[
                    cores_thread_pool.submit(
                        self._get_valid_core_files_from_node,
                        node_id,
                        cores_path,
                        self.thread_local.step_idx,
                    )
                ] = node_id

            cores_files: Dict[int, List] = {}
            tags = defaultdict(int)

            for future in as_completed(futures.keys(), timeout=cores_timeout):
                logs = future.result()
                if logs:
                    node_id = futures[future]
                    # Use process name as tag
                    for log in logs:
                        # Skip the stacktrace in the tags
                        if "stack" in log:
                            continue
                        process_name = log.split(cores_path)[1].split("/")[0]
                        # limit tag name to 15 char for better readability and UI crunch
                        tags[process_name[:15]] += 1
                    cores_files[node_id] = logs
                    LOG.debug(f"Fetched cores logs {logs} from node {node_id}")

            # Create Action Tags
            cores_tags = []
            # max char limit for "description" is 50
            for core_name, count in tags.items():
                cores_tags.append(
                    {
                        "description": f"[{count}] {core_name}",
                        "level": TagLevel.HIGH,
                    }
                )

            if cores_files:
                # Add vnet logs path
                log_files: Dict[int, List] = {}
                vnet_logs = ["/var/log/vpp/vnet.log"]
                for node_id, files in cores_files.items():
                    # cleanup only cores_files. Hence store files with new object
                    log_files[node_id] = files + vnet_logs
                return {
                    "tags": cores_tags,
                    "logs": log_files,
                    "logs_cleanup_fn": self.delete_files_on_node,
                    "logs_cleanup_fn_args": (
                        cores_files,  # cleanup only cores_files
                        step["name"],
                    ),
                }
        except Exception as e:
            err_msg = f"Failed to check for cores in [{step['name']}]: {e} ({type(e)})"
            self.log_to_ctf(err_msg, "warning")
        finally:
            if cores_thread_pool:
                self.cleanupThreadPool(cores_thread_pool)

        return None

    def _get_valid_core_files_from_node(
        self, node_id: int, path: str, step_idx: Optional[int] = None
    ) -> List:
        """Returns all valid core files which were generated before this function call except
        in progress gzip files which didn't complete even after waiting"""

        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        # get all cores files which were generated before this function call
        cores_files = self.find_files_under_path(
            file_pattern="*", path=path, node_id=node_id
        )

        # get inprogress gzip
        in_progress_gzip_files = self.get_in_progress_gzip(
            gzip_path=path, node_id=node_id
        )

        # get only valid files and skip all in progress gzip files
        files = [file for file in cores_files if file not in in_progress_gzip_files]

        self.log_to_ctf(
            f"Node {node_id} found {len(cores_files)} {cores_files} core files and {len(in_progress_gzip_files)} {in_progress_gzip_files} in progress gzip files",
            "info",
        )
        return files

    def find_files_under_path(self, file_pattern: str, path: str, node_id: int) -> List:
        cmd = f"find {path} -type f -name '{file_pattern}'"
        futures: Dict = self.run_cmd(cmd, node_ids=[node_id])
        for result in self.wait_for_cmds(futures, timeout=self.timeout):
            if result["success"]:
                files = [
                    line for line in result["message"].split("\n") if line.strip() != ""
                ]
                return files
        return []

    def get_in_progress_gzip(self, gzip_path: str, node_id: int) -> List:
        """Returns in progress gzip files"""
        # Find gzip files
        gzip_node_files: list = self.find_files_under_path(
            file_pattern="*.gz", path=gzip_path, node_id=node_id
        )

        in_progress_files = []
        if len(gzip_node_files) > 0:
            # Some process takes long to compress the file/s, wait until compression is done or timeout occurs
            in_progress_files = self._wait_for_gzip_to_compress(
                gzip_files=gzip_node_files, node_id=node_id
            )

        return in_progress_files

    def _wait_for_gzip_to_compress(
        self,
        gzip_files: List[str],
        node_id: int,
        max_attempt: int = 6,
        sleep_time: int = 5,
    ) -> List:
        """Wait until gzip compression is done or timeout"""
        self.log_to_ctf("Check if gzip is in progress", "info")

        attempt = 1
        gzip_in_progress_reason = "unexpected end of file"
        gzip_in_progress = True
        while attempt < max_attempt and gzip_in_progress:
            files = " ".join(gzip_files)
            gzip_test_cmd = f"gzip -vt {files}"
            futures: Dict = self.run_cmd(gzip_test_cmd, node_ids=[node_id])
            for result in self.wait_for_cmds(futures, timeout=self.timeout):
                LOG.debug(f"gzip result {result}")
                if gzip_in_progress_reason in result["error"]:
                    time.sleep(sleep_time)
                else:
                    gzip_in_progress = False

            attempt += 1

        # Filter in progreess gzip files, for this will have to go through all files 1 at a time
        if gzip_in_progress:
            futures = {}
            for file in gzip_files:
                gzip_test_cmd = f"ls {file}; gzip -t {file}"
                future = self.run_cmd(gzip_test_cmd, node_ids=[node_id])
                futures.update(future)

            in_progress_files = []
            for result in self.wait_for_cmds(futures, timeout=self.timeout):
                if gzip_in_progress_reason in result["error"]:
                    in_progress_files.append(result["message"].split("\n")[0])

            LOG.debug(f"files in gzip process {in_progress_files}")
            return in_progress_files

        return []

    # TODO: Return vpp logs for given time window
    def _query_es_for_asserts_logs_and_tags(self, step: Dict) -> Optional[Dict]:
        """Find asserts in logs using elasticsearch query
        This function will return action tags and logs which will include assert codes
        """
        try:
            es_endpoint = self.test_args["elasticsearch_endpoint"]
            index_pattern = TgCtfSITConsts.get(
                "ELASTICSEARCH_INDEX_PATTERN_CHECK_ASSERTS", None
            )
            es_query = TgCtfSITConsts.get("ELASTICSEARCH_QUERY_CHECK_ASERRT", None)
            if es_endpoint and index_pattern and es_query:
                es_api = f"{es_endpoint}{index_pattern}/_search"
                assert_pattern = TgCtfSITConsts.get(
                    "ELASTICSEARCH_ASSERT_PATTERN", "ASSERT"
                )

                # create filter to fetch logs based on the mac address of all the nodes
                """
                [
                    {
                        "match_phrase": {
                            "mac_addr": "34:ef:b6:8a:15:fa"
                        }
                    }
                ]
                """
                mac_addrs = self.get_all_node_mac()
                source_field_query = []
                for node_id in self.get_tg_devices():
                    source_field = {}
                    source_field["match_phrase"] = {"mac_addr": mac_addrs.get(node_id)}
                    source_field_query.append(source_field)

                start_time = datetime.datetime.utcfromtimestamp(
                    step["start_time"]
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
                es_query_vars = {
                    "assert_pattern": assert_pattern,
                    "source_field_query_dsl": json.dumps(source_field_query),
                    "start_time": start_time,
                    "end_time": datetime.datetime.utcnow().isoformat(),
                }
                es_query = Template(es_query).substitute(**es_query_vars)
                LOG.info(f"ES API {es_api}")
                LOG.info(f"ES Body {es_query}")
                self.log_to_ctf(f"ES Body {es_query_vars}", "info")
                if self.test_args["use_nms_proxy"]:
                    curl_cmd = f"curl -X POST -H 'Content-Type: application/json' -d '{es_query}' {es_api}"
                    result = self.nms_proxy.action_custom_command(curl_cmd, timeout=10)
                    self.log_to_ctf("nms proxy command result")
                    self.log_to_ctf(result)
                    if result["error"] != 0 or result["returncode"] != 0:
                        error = f'error: {result["error"]} | stderr: {result["stderr"]} | message: {result["message"]}'
                        raise DeviceCmdError(
                            f"ES query failed on proxy server: {error}"
                        )
                    es_response = json.loads(result["message"])
                    if not es_response.get("hits", None):
                        self.log_to_ctf(
                            f"ES failed to return defined result | {result}",
                            "warning",
                        )
                        return None
                else:
                    response = requests.post(
                        es_api,
                        json=json.loads(es_query),
                        timeout=10,
                    )
                    response.raise_for_status()
                    es_response = response.json()

                """
                ES response structre (response is trimmed to show essential ones only)
                {
                    "hits": {
                        "total": {
                            "value": 1,
                            "relation": "eq"
                        },
                        "hits": [
                            {
                                "_source": {
                                    "log": "I0915 17:33:06.632311 15185 IgnitionApp.cpp:796] <04:ce:14:fe:b3:47> Status of link to 04:ce:14:fe:b3:4e on interface terra0 is: LINK_UP",
                                    "mac_addr": "34:ef:b6:8a:15:fa",
                                    "node_name": "Fig0-TIP-DUT3",
                                    "log_file": "e2e_minion"
                                }
                            }
                        ]
                    }
                }
                """
                if es_response["hits"]["total"]["value"] <= 0:
                    return None  # No asserts were found

                assert_info = defaultdict(int)
                # parse response to log the assert if any
                for hit in es_response["hits"]["hits"]:
                    _source = hit["_source"]
                    log = _source["log"]
                    log_file = _source["log_file"]
                    node_name = _source.get(
                        "node_name", "NotFound"
                    )  # node_name and mac_addr are conditional
                    mac_addrs = _source.get("mac_addr", "NotFound")
                    msg = f"Assert found node:{node_name} | {log} | {log_file} | mac:{mac_addrs}"
                    self.log_to_ctf(msg, "error")
                    assert_code = log
                    # Get the assert code
                    # log : "Firmware error detected, assert codes FW 0x0000409e, UCODE 0x00000000"
                    assert_code = log.split(assert_pattern)[1].split(",")[0].strip()
                    # Maintain number of times same assert was found
                    assert_info[assert_code] += 1

                assert_tags = []
                # Create Action Tags
                # limiting assert tags to 5
                for assert_code, count in list(assert_info.items())[:5]:
                    # max char limit for "description" is 50
                    tag = f"[{count}] {assert_code}"
                    assert_tags.append(
                        {
                            "description": tag[:50],
                            "level": TagLevel.CRITICAL,
                        }
                    )
                return {"tags": assert_tags}
        except (RequestException, DeviceCmdError, json.JSONDecodeError) as e:
            err_msg = f"Failed to check for asserts | step [{step['name']}] | {type(e)} | {str(e)}"
            self.log_to_ctf(err_msg, "warning")
        return None

    def get_dashboard_links(self) -> List[Dict]:
        """Return list of dashboard links which will be hooked to test run result
        Dashboard links will be used to show on TestRunResult page.

        CTF accepts dashboard details in below format:
        [{"label":"Grafana" ,"link":"http://grafana/dashboard"}]
        """
        dashboard_links = super().get_dashboard_links()
        dashboard_links.extend(self._get_grafana_dashboard_links())
        dashboard_links.extend(self._get_kibana_dashboard_links())
        dashboard_links.extend(self._get_explorer_links())
        return dashboard_links

    def _get_grafana_dashboard_links(self) -> List[Dict]:
        """This method will return list of grafana dashbaord links in below format
        [{"label":"Grafana" ,"link":"http://grafana/dashboard"}]
        """
        network_name = self.read_nodes_data([SETUP_INFO_ID, "setup", "name"], False)
        if not network_name:
            # grafana API accepts empty network name
            network_name = ""

        grafana_api = self.test_args["grafana_endpoint"]
        if grafana_api:
            dashboards = TgCtfSITConsts.get("GRAFANA_DASHBOARDS", [])
            dashboard_links = []
            for dashboard in dashboards:
                dashboard_name = dashboard["dashboard_name"]
                dashboard_uid = dashboard["dashboard_uid"]
                link = f"{grafana_api}d/{dashboard_uid}?var-network={network_name}&from={int(self.test_start_time)*1000}&to={int(time.time()*1000)}"
                dashboard_links.append({"label": dashboard_name, "link": link})

            LOG.info(f"GF dashboard links {dashboard_links}")

            return dashboard_links

        return []

    def _get_kibana_dashboard_links(self) -> List[Dict]:
        """This method will return list of kibana dashboard links in below format
        [{"label":"Kibana" ,"link":"http://kibana/dashboard"}]
        """
        kibana_api = self.test_args["kibana_endpoint"]
        if not kibana_api:
            return []

        # Kibana likes dates in 2021-09-01T00:00:00Z format, so format epoch time that way
        start_time = datetime.datetime.utcfromtimestamp(self.test_start_time).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        end_time = datetime.datetime.utcfromtimestamp(int(time.time())).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        dashboards = TgCtfSITConsts.get("KIBANA_DASHBOARDS", [])
        dashboard_links = []
        for dashboard in dashboards:
            dashboard_name = dashboard["dashboard_name"]
            link = f"{kibana_api}discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{start_time}',to:'{end_time}'))&_a=(columns:!(_source),interval:auto,query:(language:kuery,query:''),sort:!(!('ingest_time',desc)))"
            dashboard_links.append({"label": dashboard_name, "link": link})

        LOG.info(f"KB dashboard links {dashboard_links}")

        return dashboard_links

    def _get_explorer_links(self) -> List[Dict]:
        """This method will return list of grafana explorer links similar to
        _get_kibana_dashboard_links and _get_grafana_dashboard_links
        """
        explorer_links = []
        grafana_api = self.test_args["grafana_endpoint"]
        if grafana_api:
            explorer_links.append(
                {
                    "label": "Grafana explorer",
                    "link": f"{grafana_api}explore?orgId=1&left=%5B%22{int(self.test_start_time)*1000}%22,%22{int(int(time.time()*1000))}%22,%22Prometheus%22,%7B%7D%5D",
                }
            )
        return explorer_links

    def _fix_csv_field(self, field: str) -> str:
        # Fix three things:
        # 1. remove carridge returns and line feeds
        # 2. if field contains comma, wrap with double-quotes
        # 3. if field with commas contains double-quotes, change them to two double-quotes

        # since numbers might get passed in, simplify this logic by forcing to string type
        field = str(field)
        field = field.replace("\r", "")
        field = field.replace("\n", "")
        if "," in field:
            if '"' in field:
                field = field.replace('"', '""')
            field = f'"{field}"'
        return field

    def _prometheus_stats_query(self, url):
        try:
            self.log_to_ctf(f"PT Query for stats | {url}", "info")
            if self.test_args["use_nms_proxy"]:
                curl_cmd = f"curl -k '{url}'"
                result = self.nms_proxy.action_custom_command(curl_cmd, timeout=10)
                self.log_to_ctf("nms proxy command result")
                self.log_to_ctf(result)
                if result["error"] != 0 or result["returncode"] != 0:
                    error = f'error: {result["error"]} | stderr: {result["stderr"]} | message: {result["message"]}'
                    raise DeviceCmdError(f"PT query failed on proxy server: {error}")
                es_response = json.loads(result["message"])
                if not es_response.get("data", None):
                    self.log_to_ctf(
                        f"PT failed to return defined result | {result}",
                        "error",
                    )
                    return None
            else:
                response = requests.get(url, verify=False, timeout=10)
                response.raise_for_status()
                es_response = response.json()
            return es_response

        except (RequestException, DeviceCmdError) as e:
            self.log_to_ctf(
                f"Failed to fetch stats from Prometheus | {type(e)} | {str(e)}",
                "error",
            )

        return {}

    def _get_node_macs(self):
        mac_addrs = self.get_all_node_mac()
        node_macs = []
        for node_id in self.get_tg_devices():
            node_macs.append(mac_addrs.get(node_id))
        return node_macs

    def _collect_and_submit_prometheus_stats(
        self,
        start_time: int,
        end_time: int,
        node_macs: Dict,
        network: str,
        test_action_result_id: Optional[int] = None,
    ) -> None:
        """Collect Link Dashboard Prometheus metrics to CSV files.
        Parameters:

        Returns:
        None
        """
        endpoint = self.test_args["prometheus_endpoint"]
        # require an endpoint and network
        self.log_to_ctf(f"_collect_prometheus_stats with {endpoint} and {network}")
        if not endpoint:
            self.log_to_ctf("No prometheus endpoint is available", "info")
            return
        if not network:
            self.log_to_ctf("No prometheus query network is available", "info")
            return

        files = []
        for node_id, node_mac in node_macs.items():
            if self.store_logs_locally:
                local_dir = path.join(
                    self.store_logs_locally,
                    str(self.test_exe_id),
                    str(node_id),
                    "pt_logs",
                )
                makedirs(local_dir, exist_ok=True)
            else:
                tmp_dir = TemporaryDirectory(prefix="logfiles-")
                local_dir = tmp_dir.name

            query = f'{{__name__=~"tgf_.*",network="{network}",nodeMac="{node_mac}"}}'
            url = f"{endpoint}api/v1/query_range?query={quote(query)}&start={start_time}&end={end_time}&step=15"
            body = self._prometheus_stats_query(url)
            file_path = f"{local_dir}/log-stats-prometheus-{node_mac}-{start_time}-{end_time}.csv"
            files.append(file_path)
            with open(f"{file_path}", "wt") as stats_file:
                """
                Prometheus returns a dict like:
                {
                    "status": "success",
                    "data": {
                        "resultType": "matrix",
                        "result": [
                            {
                                "metric": {
                                    "__name__": "tgf_04:ce:14:fc:b8:03_phystatus_ssnrest",
                                    "instance": "prometheus_cache:9091",
                                    "intervalSec": "1",
                                    "job": "node_stats_kafka",
                                    "linkDirection": "Z",
                                    "linkName": "link-14-Main-17-Roof-North",
                                    "network": "puma_e2e_dryrun",
                                    "nodeMac": "34:ef:b6:ed:0e:d2",
                                    "nodeName": "17-Roof-North",
                                    "pop": "true",
                                    "radioMac": "04:ce:14:fc:b9:64",
                                    "siteName": "17-Roof-North"
                                },
                                "values": [
                                    [
                                        1634175257, # timestamp
                                        "14"        # value
                                    ]
                                ]
                            },
                        ...
                        ]
                    }
                }
                """

                data = body.get("data", {"result": []})
                results = data.get("result", [])

                if len(results) > 0:
                    header = [
                        "Time",
                        "metric_name",
                        "value",
                        "linkName",
                    ]

                    # print CSV header row
                    print(",".join(header), file=stats_file)

                for result in results:
                    metrics = result.get("metric", {})
                    metric_name = metrics.get("__name__", None)
                    if metric_name:
                        link_name = metrics.get("linkName", "")
                        values = result.get("values", [])
                        # print CSV data rows
                        for pair in values:
                            if len(pair) == 2:
                                timestamp = pair[0]
                                value = pair[1]
                                record = [
                                    self._fix_csv_field(timestamp),
                                    self._fix_csv_field(metric_name),
                                    self._fix_csv_field(value),
                                    self._fix_csv_field(link_name),
                                ]
                                print(",".join(record), file=stats_file)

        if not self.store_logs_locally:
            tmp_dir.cleanup()

        fs_wait = []
        for file_path in files:
            self.log_to_ctf(f"COLLECT STATS SEND {file_path}", severity="info")

            if test_action_result_id:
                fs_wait.append(
                    self.query_and_save_pool.submit(
                        self.ctf_api.save_action_log_file,
                        file_path,
                        Path(file_path).name,
                        self.test_exe_id,
                        test_action_result_id,
                    )
                )
            else:
                fs_wait.append(
                    self.query_and_save_pool.submit(
                        self.ctf_api.save_log_file,
                        file_path,
                        Path(file_path).name,
                        self.test_exe_id,
                    )
                )

        for results in as_completed(fs_wait):
            result = results.result()
            self.log_to_ctf(f"save_log_file result: {result}", "info")

    def _elasticsearch_stats_query_inner(
        self, url, mac_addr, query_start_time, query_end_time
    ):
        try:
            query = {
                "version": True,
                "size": MAX_ES_QUERY_RESPONSES,
                "sort": [{"ingest_time": "asc"}],
                "query": {
                    "bool": {
                        "must": [],
                        "filter": [
                            {"match_phrase": {"mac_addr": mac_addr}},
                            {
                                "range": {
                                    "ingest_time": {
                                        "format": "strict_date_optional_time",
                                        "gt": query_start_time,
                                        "lte": query_end_time,
                                    }
                                }
                            },
                        ],
                        "should": [],
                        "must_not": [],
                    }
                },
            }

            self.log_to_ctf(f"ES API {url}", "info")
            self.log_to_ctf(f"ES Query {query}", "info")
            if self.test_args["use_nms_proxy"]:
                curl_cmd = f"curl -X POST -H 'Content-Type: application/json' -d '{json.dumps(query)}' {url}"
                result = self.nms_proxy.action_custom_command(curl_cmd, timeout=60)
                self.log_to_ctf("nms proxy command result")
                self.log_to_ctf(result)
                if result["error"] != 0 or result["returncode"] != 0:
                    error = f'error: {result["error"]} | stderr: {result["stderr"]} | message: {result["message"]}'
                    raise DeviceCmdError(f"ES query failed on proxy server: {error}")
                es_response = json.loads(result["message"])
                if not es_response.get("hits", None):
                    self.log_to_ctf(
                        f"ES failed to return defined result | {result}", "error"
                    )
                    return None
            else:
                response = requests.post(
                    url,
                    json=query,
                    verify=False,
                    timeout=60,
                )
                response.raise_for_status()
                es_response = response.json()
            return es_response

        except DeviceCmdError as de:
            self.log_to_ctf(
                f"DeviceCmdError: failed to fetch logs from ES | {type(de)} | {str(de)}",
                "error",
            )
        except requests.exceptions.Timeout as te:
            self.log_to_ctf(
                f"Timeout: failed to fetch logs from ES | {type(te)} | {str(te)}",
                "error",
            )
        except requests.exceptions.HTTPError as he:
            self.log_to_ctf(
                f"Invalid response: failed to fetch logs from ES | {type(he)} | {str(he)}",
                "error",
            )
        except Exception as e:
            self.log_to_ctf(
                f"Failed to fetch logs from ES | {type(e)} | {str(e)}", "error"
            )
        return None

    def _collect_elasticsearch_stats_outer(
        self,
        endpoint: str,
        node_id: str,
        mac_addr: str,
        metrics: List,
        start_time: int,
        end_time: int,
        step_idx=None,
        test_action_result_id: Optional[int] = None,
    ):
        if step_idx:
            # We are in a new thread. Publish step_idx in thread local data.
            # See also: ThreadLocal
            self.thread_local.init(step_idx)

        for metric in metrics:
            self._save_es_logs_locally(
                endpoint,
                node_id,
                mac_addr,
                metric,
                start_time,
                end_time,
                test_action_result_id,
            )

    def _push_to_ctf(self, fp, remote_file, test_action_result_id=None):
        fp.flush()
        if test_action_result_id:
            result = self.ctf_api.save_action_log_file(
                fp.name,
                remote_file,
                self.test_exe_id,
                test_action_result_id,
            )
        else:
            result = self.ctf_api.save_log_file(
                fp.name,
                remote_file,
                self.test_exe_id,
            )
        self.log_to_ctf(
            f"_push_to_ctf fp.name={fp.name} remote_file={remote_file} result={result}",
            "debug",
        )

    def _save_es_logs_locally(
        self,
        endpoint,
        node_id,
        mac_addr,
        metric,
        start_time,
        end_time,
        test_action_result_id,
    ):
        total_records = 0
        file_split = 0

        url = f"{endpoint}{metric}/_search"

        self.log_to_ctf(
            f"METRIC {metric} MAC {mac_addr} {start_time} {end_time}",
            "info",
        )

        # query range start time
        query_start_time = datetime.datetime.utcfromtimestamp(start_time).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # query range end time
        query_end_time = datetime.datetime.utcfromtimestamp(end_time).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # Logs collection from Elasticsearch takes approximately same amount of the test run duration
        collection_deadline = (
            time.monotonic() + (end_time - start_time) + LOG_COLLECTION_BUFFER_DURATION
        )

        if self.store_logs_locally:
            local_dir = path.join(
                self.store_logs_locally, str(self.test_exe_id), str(node_id), "es_logs"
            )
            makedirs(local_dir, exist_ok=True)
        else:
            tmp_dir = TemporaryDirectory(prefix="logfiles-")
            local_dir = tmp_dir.name

        while True:
            self.log_to_ctf(
                f"metric={metric} mac_addr={mac_addr} query_start_time={query_start_time} query_end_time={query_end_time} file_split={file_split}",
                "debug",
            )
            if query_start_time == "":
                self.log_to_ctf(
                    f"Completed query ({metric}/{mac_addr}/{file_split})", "info"
                )
                break

            if self.thread_exit_event.is_set():
                self.log_to_ctf(
                    f"Early exit of loop because of thread_exit_event ({metric}/{mac_addr}/{file_split})",
                    "warning",
                )
                break

            if time.monotonic() > collection_deadline:
                self.log_to_ctf(
                    f"Early exit of loop because collection_deadline arrived ({metric}/{mac_addr}/{file_split})",
                    "warning",
                )
                break

            prefix = f"log-elasticsearch-{metric}-{mac_addr}-{start_time}-{end_time}-{file_split:04d}-"
            suffix = ".csv"
            filename = f"{prefix}{suffix}"
            try:
                with open(f"{local_dir}/{filename}", "wt") as fp:
                    body = self._elasticsearch_stats_query_inner(
                        url, mac_addr, query_start_time, query_end_time
                    )

                    if body is None:
                        self.log_to_ctf(
                            f"Search from {query_start_time} to {query_end_time} ({metric}/{mac_addr}/{file_split}) returned no results",
                            "warning",
                        )
                        break

                    """
                    elasticsearch should return a dict with an array of dict(s) like:
                    {"hits": {
                        {"hits": [
                                {
                                    "_source": {
                                        "fieldname": "valuename",
                                    }
                                }
                            ],
                        }
                    }
                    ...where "fieldname" and "valuename" are the real items from the elasticsearch query
                    """

                    top_level_hits = body.get("hits", {"hits": []})
                    hits = top_level_hits.get("hits", [])

                    if len(hits) == 0:
                        self.log_to_ctf(
                            f"Search from {query_start_time} to {query_end_time} ({metric}/{mac_addr}/{file_split}) returned results but 0 hits",
                            "info",
                        )
                        break

                    columns = list(hits[0].get("_source", {}).keys())
                    for i in range(len(columns)):
                        columns[i] = self._fix_csv_field(columns[i])

                    # print CSV header row
                    print(",".join(columns), file=fp)

                    # print CSV data rows
                    for hit in range(len(hits)):
                        source = hits[hit].get("_source", {})
                        record = []
                        for field in columns:
                            this = source.get(field, "")
                            record.append(self._fix_csv_field(this))
                        print(",".join(record), file=fp)

                    total_records += len(hits)

                    self._push_to_ctf(fp, filename, test_action_result_id)

                if len(hits) < MAX_ES_QUERY_RESPONSES:
                    # this means we've gotten everything from this time range
                    self.log_to_ctf(
                        f"Received all logs from elastic search during {metric}/{mac_addr}/{file_split} (hits={len(hits)}).",
                        "debug",
                    )
                    break

                # Get the start time of the next split
                source = hits[-1].get("_source", {})
                query_start_time = source.get("ingest_time", "")

                file_split += 1
            except FileNotFoundError:
                self.log_to_ctf(
                    f"Failed to open temporary file for {metric}/{mac_addr}/{file_split}.",
                    "error",
                )
                break
            except Exception as e:
                self.log_to_ctf(
                    f"Error in _save_es_logs_locally {type(e)} {str(e)}", "error"
                )
                break

        if not self.store_logs_locally:
            tmp_dir.cleanup()
        self.log_to_ctf(
            f"METRIC {metric} MAC {mac_addr} {start_time} {end_time} file_split={file_split} total_records={total_records}",
            "info",
        )

    def _collect_and_submit_elasticsearch_stats(
        self,
        start_time: int,
        end_time: int,
        metrics: List,
        node_macs: Dict,
        test_action_result_id: Optional[int] = None,
    ) -> None:
        """Collect Elasticsearch Prometheus logs to CSV files.
        Parameters:

        Returns:
        None
        """

        endpoint = self.test_args["elasticsearch_endpoint"]
        self.log_to_ctf(f"_collect_and_submit_elasticsearch_stats with {endpoint}")
        if not endpoint or not metrics:
            self.log_to_ctf("No Elasticsearch endpoint or metric list is available")
            return

        self.log_to_ctf("Threading _collect_elasticsearch_stats_outer...", "info")
        # Run Elasticsearch queries and log pushes to CTF in parallel
        tasks = {}
        for node_id, node_mac in node_macs.items():
            # Since long running tests can generate large log files, threading strictly
            # on nodes doesn't reduce the time to retrieve data in a reasonable
            # time. To mitigate this, we break the provided time range into smaller time ranges
            # and query each of those in parallel.
            # By empirical evidence, collection by 10 minute chunks appears to reduce the
            # collection time by between 1/2 and 1/3.
            split_start_time = start_time
            split_end_time = end_time
            split_duration_length = 10 * 60  # this is specificed in seconds
            split_by_duration = True
            while split_by_duration:
                split_end_time = split_start_time + split_duration_length
                if split_end_time > end_time:
                    split_end_time = end_time
                    split_by_duration = False
                key = self.query_and_save_pool.submit(
                    self._collect_elasticsearch_stats_outer,
                    endpoint,
                    node_id,
                    node_mac,
                    metrics,
                    split_start_time,
                    split_end_time,
                    self.thread_local.step_idx,
                    test_action_result_id,
                )
                tasks[
                    key
                ] = f"_collect_elasticsearch_stats_outer node_mac={node_mac} ({split_start_time}/{split_end_time})"
                split_start_time = split_end_time

        # Logs collection from Elasticsearch takes approximately same amount of the test run duration
        wait_timeout = (end_time - start_time) + LOG_COLLECTION_BUFFER_DURATION
        self.log_to_ctf(
            f"Waiting on collect threads (timeout={wait_timeout})...",
            "info",
        )

        for task in as_completed(tasks, timeout=wait_timeout):
            result = task.result()
            info = tasks[task]

            result = task.result()
            self.log_to_ctf(
                f"Received {result} files from {info}",
                "debug",
            )

        # Cancel and show info for threads that did not complete.
        for task in tasks.keys():
            if not task.done():
                self.log_to_ctf(f"Cancel running task {tasks[task]}", "debug")
                task.cancel()

    def query_and_save_logs_to_ctf(
        self,
        start_time: int,
        end_time: int,
        metrics: List,
        node_macs: Dict,
        network: str,
        test_action_result_id: Optional[int] = None,
    ) -> None:
        self._collect_and_submit_elasticsearch_stats(
            start_time,
            end_time,
            metrics,
            node_macs,
            test_action_result_id,
        )
        self._collect_and_submit_prometheus_stats(
            start_time, end_time, node_macs, network, test_action_result_id
        )

    def schedule_tg_collect_logs_test(
        self,
        tg_collect_logs_test_id: int,
        log_collection_request: Dict,
        start_time: int,
        end_time: int,
    ) -> None:
        """Schedules the TgCollectLogs CTF UI test.
        tg_collect_logs_test_id: the CTF UI test id
        log_collection_request: this TgCollectLogs CTF UI test arg
        start_time: start time of the log collection
        end_time: end time of the log collection
        """
        test_terminal_env = {}
        log_collection_request["start_time"] = start_time
        log_collection_request["end_time"] = end_time
        test_terminal_env["log_collection_request"] = log_collection_request

        # Using store_logs_locally to skip automated [NMS] ES and PT log collection
        if self.store_logs_locally:
            self.log_to_ctf(
                "Manually run below commands to collect logs locally", "info"
            )
            cmd = f"./buck-out/gen/terragraph/ctf/tg_ctf_runner.par run TgCollectLogs --test-setup-id 166 --test-args log_collection_request='{json.dumps(log_collection_request)}' --store-logs-locally --skip pre_run post_run"
            self.log_to_ctf(cmd, "info")
        else:
            self.log_to_ctf(
                f"Schedule TgCollectLogs UI test {tg_collect_logs_test_id} with args {test_terminal_env}",
                "info",
            )
            self.ctf_api.run_test(tg_collect_logs_test_id, test_terminal_env)

    def collect_logfiles(self, logfiles: Dict[str, List[str]]) -> None:

        if self.test_args["collect_stats"]:
            self.log_to_ctf(
                f"COLLECT STATS with threadpool size {self.test_args['collection_threadpool_size']}",
                severity="info",
            )
            try:
                # Schedule a separate CTF TgCollectLogs test to collect the elastic search and prometheus logs
                # Motivation: don't un-necessarily block the test setup for a long time.
                tg_collect_logs_test_id = TgCtfSITConsts.get(
                    "TG_COLLECT_LOGS_UI_TEST_ID", None
                )
                if tg_collect_logs_test_id is None:
                    self.log_to_ctf(
                        "Failed to schedule elastic search and prometheus log collection. UI test id not found",
                        "error",
                    )
                    return

                network = self.read_nodes_data([SETUP_INFO_ID, "setup", "name"], False)
                log_collection_request = {}
                log_collection_request["target_test_exe_id"] = self.test_exe_id
                log_collection_request["start_time"] = self.test_start_time
                log_collection_request["end_time"] = int(time.time())
                log_collection_request["node_macs"] = self.get_all_node_mac()
                log_collection_request["network_name"] = network
                log_collection_request["target_test_name"] = self.TEST_NAME

                test_terminal_env = {}
                test_terminal_env["log_collection_request"] = log_collection_request

                # Split the log collection to MAX_LOG_COLLECTION_DURATION duration each, for the test run which executes beyond MAX_LOG_COLLECTION_DURATION
                start_time = self.test_start_time
                end_time = int(time.time())
                while end_time > start_time:
                    self.schedule_tg_collect_logs_test(
                        tg_collect_logs_test_id,
                        log_collection_request,
                        start_time,
                        min(end_time, start_time + MAX_LOG_COLLECTION_DURATION),
                    )
                    start_time = start_time + MAX_LOG_COLLECTION_DURATION

            except TimeoutError:
                self.log_to_ctf("Timeout during collect_logfiles.", "warning")
            except Exception as e:
                self.log_to_ctf(f"Error during collect_logfiles {e}", "error")
        super().collect_logfiles(logfiles)

    def get_fw_params_link(self, node_id: int, responder_mac: str) -> Dict:
        """Get link based fw params for given responder mac"""
        cmd = f"tg2 minion fw_get_params -t link -r {responder_mac}"
        self.log_to_ctf(cmd)
        futures: Dict = self.run_cmd(cmd, node_ids=[node_id])
        if not futures:
            raise TestUsageError(f"Node id {node_id} not found")
        result = next(self.wait_for_cmds(futures))
        output = result["message"]
        if not result["success"]:
            error_msg = (
                f"Node {result['node_id']}: failed to run cmd: "
                + f"{cmd}\n{output}\n{result['error']}"
            )
            raise DeviceCmdError(error_msg)
        self.log_to_ctf(f"Node {result['node_id']} | cmd {cmd} | output {output}")
        return result

    def verify_golay(self, node_id: int, responder_mac: str, golay: Dict) -> None:
        """Verify rx and tx golay for a specific link"""
        result = self.get_fw_params_link(node_id, responder_mac)
        run_time_fw_params = json.loads(result["message"])
        rxGolay = run_time_fw_params["optParams"].get("rxGolayIdx", -1)
        txGolay = run_time_fw_params["optParams"].get("txGolayIdx", -1)
        if rxGolay != golay["rxGolayIdx"] and txGolay != golay["txGolayIdx"]:
            raise TestFailed(
                f"Run time golay state in fw rx:{rxGolay}-tx:{txGolay} didn't match with expected golay {golay}"
            )
        self.log_to_ctf(
            f"Run time golay state in fw matched with expected golay {golay}"
        )

    def log_node_config_diff(self, node_ids: Optional[List[int]] = None) -> None:
        """Log the diff between the node config and the base config"""
        cmd = "diff_node_config"
        self.log_to_ctf(cmd)
        futures: Dict = self.run_cmd(cmd, node_ids=node_ids)
        for result in self.wait_for_cmds(futures):
            output = result["message"]
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: failed to run cmd: "
                    + f"{cmd}\n{output}\n{result['error']}"
                )
                raise DeviceCmdError(error_msg)
            self.log_to_ctf(f"Node {result['node_id']}| cmd {cmd} | output {output}")
