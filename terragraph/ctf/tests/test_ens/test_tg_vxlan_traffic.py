#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import copy
import json
import logging
from argparse import Namespace
from typing import Dict, List, Optional

from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn

LOG = logging.getLogger(__name__)


class TestTgVxlanTraffic(TestX86TGIgn):
    TEST_NAME = "ENS: TG node upgrade, vxlan tunnel and test traffic"
    DESCRIPTION = (
        "Bring up TG node with new image setup Vxlan tunnel "
        + " running traffic over establish link"
    )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.ping_options = self.test_data["ping_options"]
        self.test_options = self.test_data["test_options"]
        self.action_data = self.test_options["action_data"]

    def node_config_tunnel_removed(
        self, node_names: Optional[List[str]] = None
    ) -> Dict:
        node_overrides: Dict[str, Dict] = {}
        overrides: Dict[str, str] = {}
        local_nodes_data = copy.deepcopy(self.nodes_data)
        if not node_names:
            e2e_ctrl_node_id = self.find_x86_tg_host_id()
            e2e_topology = local_nodes_data[e2e_ctrl_node_id]["e2e_controller"][
                "topology"
            ]
            node_names = [node["name"] for node in e2e_topology["nodes"]]

        node_overrides = local_nodes_data[e2e_ctrl_node_id]["e2e_controller"][
            "configs"
        ]["node_config_overrides"]
        for node_name in node_names:
            node_overrides[node_name]["tunnelConfig"] = {}

        overrides["overrides"] = json.dumps(node_overrides)
        return overrides

    def get_test_steps(self) -> List[Dict]:
        steps = super().get_test_steps()
        steps.extend(
            [
                self.COMMON_TEST_STEPS["check_openr_adjacencies"],
                {
                    "name": "Check VxLAN L2 tunnels in VPP",
                    "function": self.vxlan_vpp_check,
                    "function_args": (),
                    "success_msg": "VxLAN L2 tunnels are enabled in VPP",
                },
            ]
        )
        traffic_profile = self.test_data["traffic_profile"]
        for stream in traffic_profile:
            steps.extend(
                [
                    {
                        "name": "IPv4 Verification for ping check result",
                        "function": self.cpe_ping_and_verification,
                        "function_args": (
                            stream["from_device_id"],
                            stream["to_device_id"],
                            stream["from_netns"],
                            stream["to_netns"],
                            stream["from_interface"],
                            stream["to_interface"],
                            stream["ipv6"],
                            self.ping_options,
                        ),
                        "success_msg": "IPv4 ping check over VXLAN is successful",
                    },
                    {
                        "name": "IPv6 Verification for ping check result",
                        "function": self.cpe_ping_and_verification,
                        "function_args": (
                            stream["from_device_id"],
                            stream["to_device_id"],
                            stream["from_netns"],
                            stream["to_netns"],
                            stream["from_interface"],
                            stream["to_interface"],
                            True,
                            self.ping_options,
                        ),
                        "success_msg": "IPv6 ping check over VXLAN tunnel is successful",
                    },
                ]
            )
        steps.extend(
            [
                {
                    "name": "Clear vpp interface",
                    "function": self.interface_info,
                    "function_args": (True,),
                    "success_msg": "Cleared vpp interface",
                    "continue_on_failure": True,
                },
                {
                    "name": "Run Traffic",
                    "function": self.run_traffic,
                    "function_args": (traffic_profile,),
                    "success_msg": "iperf ran successfully",
                    "continue_on_failure": True,
                },
                {
                    "name": "vpp interface info",
                    "function": self.interface_info,
                    "function_args": (),
                    "success_msg": "Dumped vpp interface info",
                    "continue_on_failure": True,
                },
            ]
        )
        steps.extend(
            [
                {
                    "name": "Check VxLAN L2 tunnels in VPP",
                    "function": self.vxlan_vpp_check,
                    "function_args": (),
                    "success_msg": "VxLAN L2 tunnels are enabled in VPP",
                },
                {
                    "name": "override L2 Tunnel config from controller node config",
                    "function": self.api_service_request,
                    "function_args": (
                        "setNodeOverridesConfig",
                        self.node_config_tunnel_removed(),
                    ),
                    "success_msg": "L2 tunnel config are removed from controller node config",
                },
                {
                    "name": "Check for VxLAN L2 tunnels are cleared in VPP",
                    "function": self.vxlan_vpp_check,
                    "function_args": (),
                    "success_msg": "VxLAN L2 tunnels are cleared in VPP",
                    "negate_result": True,
                    "continue_on_failure": True,
                    "delay": 30,
                },
            ]
        )
        return steps


if __name__ == "__main__":
    LOG.error("Not designed to run directly")
