#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from argparse import Namespace


FAKE_ARGS = Namespace(
    max_workers=2,
    debug=True,
    run_sandcastle=False,
    team_id=69,
    test_setup_id=69,
    nodes_data=None,
    nodes_data_dir=None,
    timeout=1,
    log_collect_timeout=300,
    no_ssh_debug=False,
    scp_timeout=1,
    testname="unittest",
    serverless=False,
    json_args="{}",
    store_logs_locally="/tmp/ctf_logs",
)

NODE_CURRENT_CONFIG = {
    "bgpParams": {"neighbors": {"0": {"asn": 65069}}},
    "envParams": {"CPE_INTERFACE": ""},
}

NODE_TEST_CONFIG = {
    "bgpParams": {"neighbors": {"0": {"ipv6": "69::1"}}},
    "envParams": {"CPE_INTERFACE": "OneHundredGigabitEthernet69"},
    "syslogParams": {"enabled": True},
}

EXPECTED_MERGED_CONFIG = {
    "bgpParams": {"neighbors": {"0": {"asn": 65069, "ipv6": "69::1"}}},
    "envParams": {"CPE_INTERFACE": "OneHundredGigabitEthernet69"},
    "syslogParams": {"enabled": True},
}
