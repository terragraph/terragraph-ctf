#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import json
import logging
from time import sleep
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIot

LOG = logging.getLogger(__name__)


class TestNodeIotRouting(TestNodeIot):
    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestNodeIotRouting, TestNodeIotRouting
        ).test_params()
        test_params["test_data"]["required"] = True

        return test_params

    def iterative_link_flapping(
        self, disable_links: Dict, continue_on_failure: bool = True
    ) -> None:
        disabling_order = disable_links["disabling_order"]
        for i, disable_link in enumerate(disabling_order):
            link_name = disable_links[disable_link][
                "link_name"
            ]  # Must match topology file
            initiator_mac = disable_links[disable_link]["initiator_mac"]
            responder_mac = disable_links[disable_link]["responder_mac"]

            self.log_to_ctf(f"ITERATION: {i} - linkname: {link_name}")

            self.log_to_ctf("Disabling auto ignition on controller")
            self.api_set_igntion_state(False)

            sleep(2)

            self.log_to_ctf(
                f"Disabling Link {link_name}: initiator_mac: {initiator_mac} - responder_mac: {responder_mac}"
            )
            self.api_force_dissoc(initiator_mac, responder_mac)

            sleep(2)

            self.log_to_ctf(
                "Checking Topology to ensure that the link actually went down."
            )
            try:
                self.api_check_link_state(link_name, False)
            except TestFailed:
                if continue_on_failure:
                    pass
                else:
                    raise DeviceCmdError("Failed to verify Link State.")

            self.log_to_ctf("Waiting for 240seconds with link down!")
            sleep(240)

            self.log_to_ctf("Re-Enabling Auto Ignition")
            self.api_set_igntion_state(True)

            self.log_to_ctf("Waiting 10 seconds for changes to take place")
            sleep(10)

            self.log_to_ctf(
                "ReChecking network after auto ignition. Down link should come up. It should pass."
            )
            self.try_until_timeout(
                self.controller_verify_topology_up,
                (self.api_service_request, ["getTopology"]),
                5,
                100,
            )

            self.log_to_ctf("Waiting 60 seconds before next iteration starts!")
            sleep(60)

    def get_test_steps(self) -> List[Dict]:
        # ignite network using e2e controller
        # Configure & ignite the topology as described in the topology except no terragraph link to CN.
        test_data = json.load(open(self.test_args["test_data"]))
        stream = test_data["traffic_stream"]

        disable_links = test_data["disable_links"]

        steps = super().get_test_steps()

        steps.extend(
            [
                {
                    "name": f"{datetime.datetime.now()}: Run Traffic",
                    "function": self.run_traffic,
                    "function_args": ([stream],),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                    "concurrent": True,
                },
                {
                    "name": f"{datetime.datetime.now()}: Flapping the provided links in test-data-json while iperf is running in parallel",
                    "function": self.iterative_link_flapping,
                    "function_args": (disable_links,),
                    "success_msg": "Finished flapping the links.",
                    "continue_on_failure": True,
                    "concurrent": True,
                    "delay": 15,
                },
            ]
        )

        return steps
