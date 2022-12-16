#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from argparse import Namespace
from shutil import make_archive, rmtree
from typing import Dict, List

from terragraph.ctf.consts import TgCtfConsts
from terragraph.ctf.sit import ProxyDevice, SitPumaTgCtfTest

TgCtfNmsConsts: Dict = {
    # List of elasticsearch queries
    "ELASTICSEARCH_METRICS": [
        "fluentd-log-node-e2e_minion-*",
        "fluentd-log-node-fib_vpp-*",
        "fluentd-log-node-kern-*",
        "fluentd-log-node-openr*",
        "fluentd-log-node-vpp-*",
        "fluentd-log-node-vpp_vnet*",
        "fluentd-log-node-fw_trace*",
    ]
}
CTF_URL = "https://internalfb.com/intern/bunny/?q=ctf"
LOG = logging.getLogger(__name__)


class TgCollectLogs(SitPumaTgCtfTest):
    """
    TgCollectLogs is created speicifically to pull large amount of logs from Elasticsearch and Prometheus store and upload to CTF.
    The intention is to avoid this time consuming process while running the actual test and release the setup for other tests.
    This test is scheduled on CTF at the end of each sit.py test (during collect_logfiles step).
    There are two components for the TgCollectLogs to work automatically:
    1. We need to have a CTF UI test with below command in "CTF Client Action"
    tg_ctf_runner.par run TgCollectLogs --test-setup-id <setup_id> --test-args log_collection_request='{{log_collection_request}}'
    2. The sit tests have to pass the required log_collection_request args in below format
    {
        'log_collection_request':
            {
                'target_test_exe_id': '<original target_test_exe_id>',
                'network_name': '<network_name>',
                'node_macs': {'<node_id>':'<mac_address>'},
                'start_time': '<start_time>',
                'end_time': '<end_time>'
            }
    }
    """

    TEST_NAME = "TgCollectLogs"
    DESCRIPTION = (
        "Collect [NMS] Elasticsearch and Prometheus logs for a completed test."
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.target_test_exe_id = None
        log_collection_request = json.loads(self.test_args["log_collection_request"])
        self.TEST_NAME = f'TgCollectLogs_{log_collection_request["target_test_exe_id"]}_{log_collection_request["target_test_name"]}'

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(TgCollectLogs, TgCollectLogs).test_params()
        test_params["test_data"]["required"] = False
        test_params["log_collection_request"] = {
            "desc": (
                """ Request json to collect Elasticsearch and Prometheus logs
                {'target_test_exe_id': '<original target_test_exe_id>',
                'network_name': '<network_name>',
                'node_macs': {'<node_id>':'<mac_address>'},
                'start_time': '<start_time>',
                'end_time': '<end_time>',
                'target_test_name': '<original target_test_name>'
                }"""
            ),
            "required": True,
        }
        return test_params

    def post_test_init(self) -> None:
        # NOTE: Override post_test_init() to avoid any test or setup related changes by super
        if self.test_args["use_nms_proxy"]:
            # Use nms proxy server details from TgCtfConsts
            nms_proxy_connection = TgCtfConsts.get("NMS_PROXY_SERVER", None)
            self.nms_proxy = ProxyDevice(nms_proxy_connection)
            self.log_to_ctf("Using nms proxy server", "info")

        log_collection_request = json.loads(self.test_args["log_collection_request"])
        self.target_test_exe_id = log_collection_request["target_test_exe_id"]

        # Link self to the original test
        self.log_to_ctf(
            f"Link self to the original test {self.target_test_exe_id}", "info"
        )
        dashboard_link = [
            {
                "label": "TgCollectLogs Result Link",
                "link": f"{CTF_URL}+{self.test_exe_id}",
            }
        ]
        self.ctf_api.save_test_run_outcome(self.target_test_exe_id, dashboard_link)

    def finish_test_run(self, test_passed):
        super().finish_test_run(test_passed)

        # Update dashboard links after the TgCollectLogs result is saved
        # Link the original test to self
        LOG.info(f"Link the original test {self.target_test_exe_id} to self")
        dashboard_link = [
            {
                "label": "Test Run Result Link",
                "link": f"{CTF_URL}+{self.target_test_exe_id}",
            }
        ]
        self.ctf_api.save_test_run_outcome(self.test_exe_id, dashboard_link)

    def collect_logfiles(self, logfiles: Dict[str, List[str]]) -> None:
        # NOTE: Overriding collect_logfiles(), which is called from base as the last step in the test
        try:
            self.log_to_ctf("Collect [NMS] Elasticsearch and Promethues logs", "info")
            """
            {
            "log_collection_request":
                {
                "target_test_exe_id": "<original target_test_exe_id>",
                "network_name": "<network_name>",
                "node_macs": {'<node_id>':'<mac_address>'},
                "start_time": "<start_time>",
                "end_time": "<end_time>",
                'target_test_name': '<original target_test_name>'
                }
            }
            """
            log_collection_request = json.loads(
                self.test_args["log_collection_request"]
            )
            start_time = log_collection_request["start_time"]
            end_time = log_collection_request["end_time"]
            network_name = log_collection_request["network_name"]
            node_macs = log_collection_request["node_macs"]
            metrics = TgCtfNmsConsts.get("ELASTICSEARCH_METRICS", None)

            self.query_and_save_logs_to_ctf(
                start_time, end_time, metrics, node_macs, network_name
            )
        except TimeoutError:
            self.log_to_ctf("Timeout during collect_logfiles.", "warning")
        except Exception as e:
            self.log_to_ctf(f"Error during collect_logfiles {e}", "error")

        # Compress and then remove the locally collected log files
        if self.store_logs_locally:
            logs_path = f"{self.store_logs_locally}{self.test_exe_id}"
            LOG.info(f"Compressing local logs directory {logs_path}")
            make_archive(logs_path, "zip", logs_path)
            LOG.info(f"Removing local logs directory {logs_path}")
            rmtree(logs_path)
