#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import random
from argparse import Namespace
from time import sleep
from typing import Dict, List

from ctf.ctf_client.runner.exceptions import TestUsageError
from terragraph.ctf.sit import SitPumaTgCtfTest


LOG = logging.getLogger(__name__)


class TestTgSuperAssoc(SitPumaTgCtfTest):
    TEST_NAME = "Super Assoc"
    DESCRIPTION = (
        "Performs assoc, ping and disassoc on randomly chosen link and "
        + "repeats this for specified number of iterations"
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.test_options = self.test_data["test_options"]
        self.selected_links = self.test_data["selected_links"]

    def _ping_over_terra(
        self, initiator_id: int, initiator_mac: str, responder_mac: str
    ) -> None:
        # Verify link is up and get ifname
        ifname: str = self.minion_get_link_interface(
            initiator_id, initiator_mac, responder_mac
        )
        self.verify_ll_ping(initiator_id, ifname, 25)

    def _ping_test_steps(
        self,
        initiator_id: int,
        initiator_mac: str,
        responder_id: int,
        responder_mac: str,
        iteration_str: str,
        interface: str,
    ) -> List[Dict]:
        # start with empty list
        ping_steps = []

        terra_ping_step = {
            "name": f"Ping Over terra link ({iteration_str})",
            "function": self._ping_over_terra,
            "function_args": (
                initiator_id,
                initiator_mac,
                responder_mac,
            ),
            "success_msg": "Ping Over terra link succeeded",
            "continue_on_failure": True,
            "error_handler": self.get_common_error_handler(),
        }

        lo_ping_step = {
            "name": f"Ping Over lo link ({iteration_str})",
            "function": self.ping_nodes,
            "function_args": (
                initiator_id,
                responder_id,
                "lo",
                "global",
                25,
            ),
            "success_msg": "Ping Over lo link succeeded",
            "continue_on_failure": True,
            "error_handler": self.get_common_error_handler(),
        }

        if "terra" == interface:
            ping_steps.append(terra_ping_step)
        elif "lo" == interface:
            ping_steps.append(lo_ping_step)
        else:
            ping_steps.extend(
                [
                    terra_ping_step,
                    lo_ping_step,
                ]
            )
        return ping_steps

    def _get_dissoc_step(
        self,
        initiator_id: int,
        initiator_mac: str,
        responder_mac: str,
        link_str: str,
        iteration_str: str,
    ) -> Dict:

        dict_for_dissoc = {
            "name": f"Dissoc {link_str} ({iteration_str})",
            "function": self.minion_dissoc,
            "function_args": (
                initiator_id,
                initiator_mac,
                responder_mac,
            ),
            "success_msg": "Dissoc succeeded",
            "continue_on_failure": True,
            "error_handler": self.get_common_error_handler(),
        }
        return dict_for_dissoc

    def _super_assoc_test_steps(
        self, sel_links: List[Dict], test_options: Dict
    ) -> List[Dict]:
        if sel_links is None:
            err = "input selected links is missing in test data"
            self.log_to_ctf(err, "error")
            raise TestUsageError(err)

        if test_options is None:
            err = "input set params is missing in test data"
            self.log_to_ctf(err, "error")
            raise TestUsageError(err)

        LOG.debug(f"sel_links:\n{sel_links}")
        LOG.debug(f"test_options:\n{test_options}")

        n = test_options["num_iterations"]
        if n < 1:
            raise TestUsageError(f"num_iterations must be positive (got {n})")
        delay_before_reassoc = test_options["delay_before_reassoc"]
        reassoc_delay_step = {
            "name": f"Wait {delay_before_reassoc} seconds before an assoc",
            "function": sleep,
            "function_args": (delay_before_reassoc,),
            "success_msg": "Finished waiting",
        }
        is_random_disassoc_enabled = test_options["enable_random_disassoc"]
        # start with empty list
        super_assoc_steps = []
        for i in range(n):
            random_order_list = (
                random.sample(sel_links, len(sel_links))
                if len(sel_links) > 1
                else sel_links
            )
            for link_idx, link in enumerate(random_order_list):
                initiator_id = link["initiator_id"]
                initiator_mac = link["initiator_mac"]
                responder_id = link["responder_id"]
                responder_mac = link["responder_mac"]
                link_str = f"link #{link_idx + 1}: {initiator_mac} -> {responder_mac}"
                iteration_str = f"iteration {i + 1} of {n}"
                super_assoc_steps.append(
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
                        "continue_on_failure": True,
                        "error_handler": self.get_common_error_handler(),
                    }
                )
                resp_ping_steps = self._ping_test_steps(
                    initiator_id,
                    initiator_mac,
                    responder_id,
                    responder_mac,
                    iteration_str,
                    self.test_options["ping_interface"],
                )
                super_assoc_steps.extend(resp_ping_steps)

                if not is_random_disassoc_enabled:
                    dissoc_step = self._get_dissoc_step(
                        initiator_id,
                        initiator_mac,
                        responder_mac,
                        link_str,
                        iteration_str,
                    )
                    super_assoc_steps.append(dissoc_step)
                    if delay_before_reassoc > 0:
                        super_assoc_steps.append(reassoc_delay_step)

            if is_random_disassoc_enabled:
                random_order_list_disassoc = (
                    random.sample(sel_links, len(sel_links))
                    if len(sel_links) > 1
                    else sel_links
                )
                for link_idx, link in enumerate(random_order_list_disassoc):
                    initiator_id = link["initiator_id"]
                    initiator_mac = link["initiator_mac"]
                    responder_mac = link["responder_mac"]
                    link_str = (
                        f"link #{link_idx + 1}: {initiator_mac} -> {responder_mac}"
                    )
                    iteration_str = f"iteration {i + 1} of {n}"
                    dissoc_step = self._get_dissoc_step(
                        initiator_id,
                        initiator_mac,
                        responder_mac,
                        link_str,
                        iteration_str,
                    )
                    super_assoc_steps.append(dissoc_step)
                # Add only one step of delay before next cycle of reassoc
                if delay_before_reassoc > 0:
                    super_assoc_steps.append(reassoc_delay_step)
        return super_assoc_steps

    def get_test_steps(self) -> List[Dict]:
        steps = [
            self.COMMON_TEST_STEPS["check_software_versions"],
            self.COMMON_TEST_STEPS["init_nodes"],
            self.COMMON_TEST_STEPS["check_timing_sync"],
        ]
        resp_super_assoc_steps = self._super_assoc_test_steps(
            self.selected_links, self.test_options
        )
        steps.extend(resp_super_assoc_steps)

        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
