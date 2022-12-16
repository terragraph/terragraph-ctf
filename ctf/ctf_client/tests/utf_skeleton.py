# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import atexit
import datetime
import json
import logging
import os
import unittest
import uuid

from crypto.keychain_service.keychain import ttypes as keychain
from ctf.ctf_client.lib.helper_functions import (
    check_if_test_setup_is_free,
    create_test_run_result,
    get_test_setup_devices_and_connections,
    save_log_file,
    save_test_action_result,
    save_test_action_result_json_data,
    save_test_run_outcome,
    set_test_setup_and_devices_busy,
    set_test_setup_and_devices_free,
)
from libfb.py.thrift_clients.keychain_thrift_client import KeychainClient


test_setup_id = 23
team_id = 7

logger = logging.getLogger(__name__)


@unittest.skip("Disabling tests as they currently hit Production.")
class UTFTestCases(unittest.TestCase):
    def getSecret(self, secret):
        req = keychain.GetSecretRequest(name=secret, author=keychain.RequestAuthor())
        try:
            secret = KeychainClient().getSecret(req)
            secret_str = str(secret.secret)
            return secret_str
        except (
            keychain.KeychainServiceException,
            keychain.KeychainClientException,
        ) as e:
            logger.exception(str(e))
            return None

    def setUp(self):
        user = self.getSecret("CTF_BUCK_USER")
        password = self.getSecret("CTF_BUCK_PASSWORD")
        api_server_url = self.getSecret("CTF_API_SERVER_URL")
        file_server_url = self.getSecret("CTF_FILE_SERVER_URL")
        if user and password and api_server_url and file_server_url:
            os.environ["CTF_USER"] = user
            os.environ["CTF_PASSWORD"] = password
            os.environ["CTF_API_SERVER_URL"] = api_server_url
            os.environ["CTF_FILE_SERVER_URL"] = file_server_url

    def free_test_setup_clean_up(self) -> None:
        logger.info("\n------------free_test_setup_clean_up-------------")
        set_test_setup_and_devices_free(test_setup_id)
        os.system("if [ -f /tmp/dummy.log ]; then rm /tmp/dummy.log; fi")

    def test_utf_basic(self) -> None:
        logger.info("\n------------test_utf_basic-------------")
        # Check if configuration is free
        ok_to_proceed = check_if_test_setup_is_free(test_setup_id)
        if ok_to_proceed:
            # Use the configuration, mark it busy, so other will get its status as
            # busy
            ok_to_proceed = set_test_setup_and_devices_busy(test_setup_id)

        if ok_to_proceed:
            # Get the configuration
            atexit.register(self.free_test_setup_clean_up)
            device_info = get_test_setup_devices_and_connections(test_setup_id)

            if device_info:

                result = create_test_run_result(
                    name="Skeleton UTF Test",
                    identifier=str(uuid.uuid4),
                    description="Check to make sure all basic APIs are working",
                    team_id=team_id,
                    test_setup=test_setup_id,
                )

                if result["data"]:
                    test_exe_details = result["data"]
                    test_exe_id = test_exe_details["id"]

                    device_1 = device_info[1]

                    date_result_start = datetime.datetime.now()
                    date_result = device_1.action_custom_command("date", 120)
                    logger.debug(date_result)

                    action_result = save_test_action_result(
                        test_run_id=test_exe_id,
                        description="Date Custom Command",
                        outcome=date_result["error"],
                        logs=date_result["message"],
                        start_time=date_result_start,
                        end_time=datetime.datetime.now(),
                    )

                    data_list1 = [
                        {
                            "Interval": 0,
                            "Transfer Mbytes": 121,
                            "Bandwidth Mbits/sec": 1014,
                            "Jitter ms": 0.059,
                        },
                        {
                            "Interval": 1,
                            "Transfer Mbytes": 121,
                            "Bandwidth Mbits/sec": 1013,
                            "Jitter ms": 0.058,
                        },
                        {
                            "Interval": 2,
                            "Transfer Mbytes": 121,
                            "Bandwidth Mbits/sec": 1010,
                            "Jitter ms": 0.058,
                        },
                    ]
                    data_source1_name = "iperf data 1"

                    data_list2 = [
                        {
                            "Interval": 0,
                            "Transfer Mbytes": 108,
                            "Bandwidth Mbits/sec": 909,
                            "Jitter ms": 0.061,
                        },
                        {
                            "Interval": 1,
                            "Transfer Mbytes": 103,
                            "Bandwidth Mbits/sec": 861,
                            "Jitter ms": 0.070,
                        },
                        {
                            "Interval": 2,
                            "Transfer Mbytes": 121,
                            "Bandwidth Mbits/sec": 950,
                            "Jitter ms": 0.058,
                        },
                    ]
                    data_source2_name = "iperf data 2"

                    json_data1 = {
                        "data_source": data_source1_name,
                        "data_list": data_list1,
                    }
                    json_data2 = {
                        "data_source": data_source2_name,
                        "data_list": data_list2,
                    }

                    table_data_source_list = ",".join(
                        [data_source1_name, data_source2_name]
                    )
                    json_table1 = {
                        "title": "Demo Iperf Table Small",
                        "table_type": "static",
                        "columns": "Interval, Bandwidth Mbits/sec",
                        "data_source_list": table_data_source_list,
                    }

                    json_table2 = {
                        "title": "Demo Iperf Table Full",
                        "data_source_list": data_source1_name
                        + ", "
                        + data_source2_name,
                    }

                    x_axis1 = {
                        "key": "Interval",
                        "options": {
                            "label": "Interval ms",
                            "position": "top",
                        },
                    }
                    x_axis1_fewer_opts = {
                        "key": "Interval",
                        "options": {
                            "label": "Interval ms",
                        },
                    }
                    y_axis1 = {
                        "series_list": [
                            {
                                "data_source": data_source1_name,
                                "key": "Bandwidth Mbits/sec",
                                "label": "TestData_iperflink1",
                            },
                            {
                                "data_source": data_source2_name,
                                "key": "Bandwidth Mbits/sec",
                                "label": "TestData_iperflink2",
                                "fill": True,
                            },
                        ],
                        "options": {"label": "Bandwidth Mbits/sec"},
                    }
                    y_axis1_notfill = {
                        "series_list": [
                            {
                                "data_source": data_source1_name,
                                "key": "Bandwidth Mbits/sec",
                                "label": "TestData_iperflink1",
                            },
                            {
                                "data_source": data_source2_name,
                                "key": "Bandwidth Mbits/sec",
                                "label": "TestData_iperflink2",
                            },
                        ],
                        "options": {"label": "Bandwidth Mbits/sec"},
                    }
                    chart_options = {
                        "display_type": "line",
                        "tension": False,
                        "summary_table": True,
                    }
                    json_chart = {
                        "title": "Iperf Chart",
                        "axes": {
                            "x_axis1": x_axis1,
                            "y_axis1": y_axis1,
                        },
                        "chart_type": "static",
                        "options": chart_options,
                    }

                    json_chart_noopts = {
                        "title": "Iperf Chart",
                        "axes": {
                            "x_axis1": x_axis1_fewer_opts,
                            "y_axis1": y_axis1_notfill,
                        },
                    }

                    ctf_json_data_all = {
                        "ctf_data": [json_data1, json_data2],
                        "ctf_tables": [json_table1, json_table2],
                        "ctf_charts": [json_chart_noopts, json_chart],
                    }

                    save_json_data_result = save_test_action_result_json_data(
                        test_action_result_id=action_result["data"][
                            "test_action_result_id"
                        ],
                        ctf_json_data_all=json.dumps(ctf_json_data_all),
                    )
                    os.system("date > /tmp/dummy.log")
                    os.system("tar -zcvf /tmp/dummy.tar.gz /tmp/dummy.log")

                    save_log_file(
                        source_file_path="/tmp/dummy.log",
                        constructive_path="dummy_logs",
                        test_exe_id=test_exe_id,
                    )

                    save_log_file(
                        source_file_path="/tmp/dummy.tar.gz",
                        constructive_path="dummy_logs",
                        test_exe_id=test_exe_id,
                    )

                    os.system("rm /tmp/dummy.log")
                    os.system("rm /tmp/dummy.tar.gz")

                    saving_status = save_test_run_outcome(test_exe_id)

                    self.assertEqual(date_result["error"], 0)
                    self.assertEqual(save_json_data_result["error"], 0)
                    self.assertEqual(saving_status["error"], 0)

            else:
                self.fail("Failed to reach the device")

        # Free the configuration
        set_test_setup_and_devices_free(test_setup_id)
