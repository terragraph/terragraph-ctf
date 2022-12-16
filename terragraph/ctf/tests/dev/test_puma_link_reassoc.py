#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from time import sleep
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import (
    DeviceConfigError,
    TestFailed,
    TestUsageError,
)
from terragraph.ctf.puma import PumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgPumaLinkReassoc(PumaTgCtfTest):
    TEST_NAME = "PUMA: Link Re-Assoc"
    DESCRIPTION = "Repeatedly assoc and disassoc Terragraph links."
    LOG_FILES = ["/var/log/vpp/vnet.log", "/var/log/e2e_minion/current"]
    NODES_DATA_FORMAT = "link-up-nodes-data-setup-{SETUP_ID}.json"

    @staticmethod
    def test_params() -> Dict[str, Dict]:
        test_params: Dict[str, Dict] = super(
            TestTgPumaLinkReassoc, TestTgPumaLinkReassoc
        ).test_params()
        test_params["reassoc_iterations"] = {
            "desc": "How many times should we re-assoc each link?",
            "default": 4,
            "convert": int,
        }
        test_params["reassoc_sleep_s"] = {
            "desc": "How many seconds should we wait between dissoc and assoc?",
            "default": 4,
            "convert": int,
        }
        return test_params

    def _verify_link_state(self, initiator_id: int) -> None:
        """Verify that the current link state matches the original state.

        Upon mismatch, raises `TestFailed`. Otherwise, store the new state as
        `self._link_state`.
        """
        link_state = self.minion_get_link_status_dumps([initiator_id])[initiator_id]
        if hasattr(self, "_link_state"):
            # pyre-fixme[16]: `TestTgPumaLinkReassoc` has no attribute `_link_state`.
            prev_link_state = self._link_state
            if link_state != prev_link_state:
                err = (
                    "Current link state differs from original!"
                    + f"\n\nCurrent ({len(link_state)} alive): {link_state}"
                    + f"\n\nOriginal ({len(prev_link_state)} alive): {prev_link_state}"
                )
                raise TestFailed(err)
        self._link_state = link_state

    def get_test_steps(self) -> List[Dict]:
        initiator_id = self.find_initiator_id()
        if initiator_id is None:
            raise DeviceConfigError("Can't find initiator ID")
        assoc_conf = self.read_nodes_data([initiator_id, "assoc"])

        # Start with typical assoc procedure
        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["assoc_terra_links"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
        ]

        # Store current link state
        # At each reassoc step, we ensure that any other links were not affected
        steps.append(
            {
                "name": "Store initial link state",
                "function": self._verify_link_state,
                "function_args": (initiator_id,),
                "success_msg": f"Stored link state from node {initiator_id}",
            },
        )

        # Add re-assoc steps (i.e. loop: dissoc => assoc for each defined link)
        n = self.test_args["reassoc_iterations"]
        if n < 1:
            raise TestUsageError(f"reassoc_iterations must be positive (got {n})")
        reassoc_sleep_s = self.test_args["reassoc_sleep_s"]
        for i in range(n):
            for link_idx, link in enumerate(assoc_conf["links"]):
                initiator_mac = link["initiator_mac"]
                responder_mac = link["responder_mac"]
                link_str = f"link #{link_idx + 1}: {initiator_mac} -> {responder_mac}"
                iteration_str = f"iteration {i + 1} of {n}"

                steps.append(
                    {
                        "name": f"Dissoc {link_str} ({iteration_str})",
                        "function": self.minion_dissoc,
                        "function_args": (
                            initiator_id,
                            initiator_mac,
                            responder_mac,
                        ),
                        "success_msg": "Dissoc succeeded",
                        "error_handler": self.get_common_error_handler(),
                    }
                )
                if reassoc_sleep_s > 0:
                    steps.append(
                        {
                            "name": f"Wait {reassoc_sleep_s} seconds before re-assoc",
                            "function": sleep,
                            "function_args": (reassoc_sleep_s,),
                            "success_msg": "Finished waiting",
                        }
                    )
                steps.extend(
                    [
                        {
                            "name": f"Assoc {link_str} ({iteration_str})",
                            "function": self.minion_assoc,
                            "function_args": (
                                initiator_id,
                                initiator_mac,
                                responder_mac,
                                link.get("respNodeType", None),
                                link.get("polarity", None),
                                link.get("controlSuperframe", None),
                                link.get("txGolayIdx", None),
                                link.get("rxGolayIdx", None),
                            ),
                            "success_msg": "Assoc succeeded",
                            "error_handler": self.get_common_error_handler(),
                        },
                        {
                            "name": "Verify link state",
                            "function": self._verify_link_state,
                            "function_args": (initiator_id,),
                            "success_msg": "Link state is unchanged",
                        },
                    ]
                )

        return steps


class TestTgPumaLinkReassocKernel(TestTgPumaLinkReassoc):
    TEST_NAME = "PUMA: Link Re-Assoc (Kernel)"
    DESCRIPTION = (
        "Repeatedly assoc and disassoc Terragraph links with the kernel driver."
    )

    def nodes_data_amend(self, num_nodes: int) -> Dict:
        nodes_data_amend = super().nodes_data_amend(num_nodes)
        self.merge_dict(
            nodes_data_amend,
            {
                i: {"node_config": {"envParams": {"DPDK_ENABLED": "0"}}}
                for i in range(1, num_nodes + 1)
            },
        )
        return nodes_data_amend


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
