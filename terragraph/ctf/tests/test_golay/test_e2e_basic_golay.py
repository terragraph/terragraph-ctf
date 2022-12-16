#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from argparse import Namespace
from typing import Dict, List

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestPumaE2EGolay(TestX86TGIgn):
    TEST_NAME = "Puma RF golay"
    DESCRIPTION = (
        "Update link golay using apis after link is ignited by e2e controller."
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        ignition_timeout_s = self.test_args["ignition_timeout_s"]
        steps.extend(
            self.steps_ping_lo_all_tg_nodes_from_src(
                src_node_id=self.test_options["ping_all_src_node_id"],
                skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                is_cont_on_fail=True,
                is_concurrent=True,
            )
        )
        steps.extend(
            [
                {
                    "name": "Get node config of initiator node",
                    "function": self.api_service_request,
                    "function_args": (
                        "getNodeConfig",
                        {"node": self.test_options["initiator_node_name"]},
                    ),
                    "success_msg": "Got node config of initiator node",
                },
                {
                    "name": "Get node config of responder node",
                    "function": self.api_service_request,
                    "function_args": (
                        "getNodeConfig",
                        {"node": self.test_options["responder_node_name"]},
                    ),
                    "success_msg": "Got node config of responder node",
                },
                {
                    "name": "Dump FW params on initiator",
                    "function": self.get_fw_params_link,
                    "function_args": (
                        self.test_options["initiator_node_id"],
                        self.test_options["responder_mac"],
                    ),
                    "success_msg": "Dumped FW params on initiator",
                    "continue_on_failure": True,
                },
                {
                    "name": "Dump FW params on responder",
                    "function": self.get_fw_params_link,
                    "function_args": (
                        self.test_options["responder_node_id"],
                        self.test_options["initiator_mac"],
                    ),
                    "success_msg": "Dumped FW params on responder",
                    "continue_on_failure": True,
                },
            ]
        )
        golay_test_idxs = self.test_options["golay_test_idxs"]
        for golay_idx in golay_test_idxs:
            config_dict: Dict = {}
            config_dict["key"] = self.test_options["override_key_tx"]
            config_dict["value"] = golay_idx
            test_overrides = self.create_node_overrides(
                config_dict,
                node_names=[self.test_options["initiator_node_name"]],
            )
            steps.append(
                {
                    "name": f"e2e rest API to Modify Node Overrides on initiator with txGolayIdx#{golay_idx}",
                    "function": self.api_service_request,
                    "function_args": (
                        "modifyNodeOverridesConfig",
                        test_overrides,
                    ),
                    "success_msg": "Called e2e rest API to Modify Node Overrides",
                    "continue_on_failure": True,
                }
            )
            config_dict: Dict = {}
            config_dict["key"] = self.test_options["override_key_rx"]
            config_dict["value"] = golay_idx
            test_overrides = self.create_node_overrides(
                config_dict,
                node_names=[self.test_options["initiator_node_name"]],
            )
            steps.append(
                {
                    "name": f"e2e rest API to Modify Node Overrides on initiator with rxGolayIdx#{golay_idx}",
                    "function": self.api_service_request,
                    "function_args": (
                        "modifyNodeOverridesConfig",
                        test_overrides,
                    ),
                    "success_msg": "Called e2e rest API to Modify Node Overrides",
                    "continue_on_failure": True,
                }
            )
            steps.extend(
                [
                    {
                        "name": "Check that the network is entirely up",
                        "function": self.try_until_timeout,
                        "function_args": (
                            self.controller_verify_topology_up,
                            (self.api_service_request, ["getTopology"]),
                            5,
                            ignition_timeout_s,
                        ),
                        "delay": 60,
                        "success_msg": "Network is up",
                        "error_handler": self.get_common_error_handler(),
                        "continue_on_failure": True,
                    },
                ]
            )
            steps.extend(
                self.steps_ping_lo_all_tg_nodes_from_src(
                    src_node_id=self.test_options["ping_all_src_node_id"],
                    skip_node_ids=self.test_options["ping_all_skip_node_ids"],
                    is_cont_on_fail=True,
                    is_concurrent=True,
                )
            )
            steps.extend(
                [
                    {
                        "name": "Get node config of initiator node",
                        "function": self.api_service_request,
                        "function_args": (
                            "getNodeConfig",
                            {"node": self.test_options["initiator_node_name"]},
                        ),
                        "success_msg": "Got node config of initiator node",
                    },
                    {
                        "name": "Get node config of responder node",
                        "function": self.api_service_request,
                        "function_args": (
                            "getNodeConfig",
                            {"node": self.test_options["responder_node_name"]},
                        ),
                        "success_msg": "Got node config of responder node",
                    },
                    {
                        "name": "Dump FW params on initiator",
                        "function": self.get_fw_params_link,
                        "function_args": (
                            self.test_options["initiator_node_id"],
                            self.test_options["responder_mac"],
                        ),
                        "success_msg": "Dumped FW params on initiator",
                        "continue_on_failure": True,
                    },
                    {
                        "name": "Dump FW params on responder",
                        "function": self.get_fw_params_link,
                        "function_args": (
                            self.test_options["responder_node_id"],
                            self.test_options["initiator_mac"],
                        ),
                        "success_msg": "Dumped FW params on responder",
                        "continue_on_failure": True,
                    },
                ]
            )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
