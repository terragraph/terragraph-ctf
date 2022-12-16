#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
List of all Terragraph CTF tests and test suites.
"""

from terragraph.ctf.tests.dev.test_puma_chrony import TestTgPumaChrony
from terragraph.ctf.tests.dev.test_puma_ctf_connectivity import TestTgCtfTest
from terragraph.ctf.tests.dev.test_puma_distributed_ignition import (
    TestTgDistributedIgnition,
)
from terragraph.ctf.tests.dev.test_puma_e2e_network_up import (
    TestTgE2ENetworkUpExternal,
    TestTgE2ENetworkUpInternal,
)
from terragraph.ctf.tests.dev.test_puma_image_upgrade import TestTgPumaImageUpgrade
from terragraph.ctf.tests.dev.test_puma_iperf_vpp import TestTgPumaIperfVpp
from terragraph.ctf.tests.dev.test_puma_ipv6_bgp import (
    TestTgPumaIpv6BGP,
    TestTgPumaIpv6BGPKernel,
)
from terragraph.ctf.tests.dev.test_puma_ipv6_frr_bgp import TestTgPumaIpv6FrrBgp
from terragraph.ctf.tests.dev.test_puma_ipv6_up import (
    TestTgPumaIpv6Up,
    TestTgPumaIpv6UpKernel,
)
from terragraph.ctf.tests.dev.test_puma_link_reassoc import (
    TestTgPumaLinkReassoc,
    TestTgPumaLinkReassocKernel,
)
from terragraph.ctf.tests.dev.test_puma_link_up import (
    TestTgPumaLinkUp,
    TestTgPumaLinkUpKernel,
)
from terragraph.ctf.tests.dev.test_puma_microcode_log import TestTgMicrocodeLog
from terragraph.ctf.tests.dev.test_puma_p2p_traffic import (
    TestP2PTraffic,
    TestP2PTrafficJumboFrame,
)
from terragraph.ctf.tests.dev.test_puma_srv6_l2 import TestTgPumaSrv6L2
from terragraph.ctf.tests.dev.test_puma_topo_scan import TestTgPumaTopoScan
from terragraph.ctf.tests.dev.test_puma_vxlan_l2 import TestTgPumaVxlanL2
from terragraph.ctf.tests.dev.test_x86_tg_setup import TestTgX86Setup
from terragraph.ctf.tests.link_level_scheduler_tests.test_lls import TestTgLLS
from terragraph.ctf.tests.link_overloading_tests.test_LOT import TestTgLOT
from terragraph.ctf.tests.link_overloading_tests.test_LOT3 import TestTgLOT3
from terragraph.ctf.tests.pbf.test_puma_pbf import TestPBF
from terragraph.ctf.tests.qos.qos_nw import Qos_Nw
from terragraph.ctf.tests.qos.qos_p2p import Qos_P2p
from terragraph.ctf.tests.qos.qos_p2p_2 import Qos_P2p_2
from terragraph.ctf.tests.qos.qos_p2p_3 import Qos_P2p_3
from terragraph.ctf.tests.qos.qos_p2p_5 import Qos_P2p_5
from terragraph.ctf.tests.qos.qos_ptmp import Qos_Ptmp
from terragraph.ctf.tests.qos.test_qos import TestTgQos
from terragraph.ctf.tests.routing.test_rou_link_down import TestTgRouteLinkDown
from terragraph.ctf.tests.routing.test_rou_link_flap import TestTgRouteLinkFlap
from terragraph.ctf.tests.routing.test_rou_mcs_change import TestTgRouteMCSChange
from terragraph.ctf.tests.stress.super_assoc import TestTgSuperAssoc
from terragraph.ctf.tests.test_association.test_AT import TestTgAT
from terragraph.ctf.tests.test_e2e.test_e2e_ignition import TestX86TGIgn
from terragraph.ctf.tests.test_e2e.test_e2e_ignition_multi_pop import (
    TestX86TGIgnMultiPOP,
)
from terragraph.ctf.tests.test_e2e.test_e2e_ignition_traffic import TestX86TGIgnTraffic
from terragraph.ctf.tests.test_e2e.test_e2e_ignition_traffic_serial import (
    TestX86TGIgnTrafficSerial,
)
from terragraph.ctf.tests.test_e2e.test_ignition_inval_ovrds import (
    TestX86TGIgnInvalOvrds,
)
from terragraph.ctf.tests.test_e2e_reg.test_e2e_reg import (
    TestTgE2EReg2,
    TestTgE2EReg3,
    TestTgE2EReg4,
)
from terragraph.ctf.tests.test_e2e_reignition.test_re_ign_cntr_if import (
    TestX86TGReIgnCntrIf,
)
from terragraph.ctf.tests.test_e2e_reignition.test_re_ign_cntr_svc import (
    TestX86TGReIgnCntrSvc,
)
from terragraph.ctf.tests.test_e2e_reignition.test_re_ign_link import TestX86TGReIgnLink
from terragraph.ctf.tests.test_e2e_reignition.test_re_ign_node_re_add import (
    TestX86TGReIgnNodeReAdd,
)
from terragraph.ctf.tests.test_e2e_reignition.test_re_ign_reboot import (
    TestX86TGReIgnReboot,
)
from terragraph.ctf.tests.test_e2e_reignition.test_recheck_minion_stop_start import (
    TestX86TGIgnMinionStop,
)
from terragraph.ctf.tests.test_e2e_reignition.test_recheck_modify_config import (
    TestX86TGIgnModifyConfig,
)
from terragraph.ctf.tests.test_e2e_reignition.test_reignition_with_minion_restart import (
    TestTgMinionRestart,
)
from terragraph.ctf.tests.test_ens.test_tg_vxlan_traffic import TestTgVxlanTraffic
from terragraph.ctf.tests.test_golay.test_e2e_basic_golay import TestPumaE2EGolay
from terragraph.ctf.tests.test_golay.test_e2e_diff_resp_golay import (
    TestPumaE2EGolayDiffResp,
)
from terragraph.ctf.tests.test_golay.test_e2e_diff_rx_golay import (
    TestPumaE2EGolayDiffRx,
)
from terragraph.ctf.tests.test_golay.test_p2p_golay import TestTgPumaP2PGolay
from terragraph.ctf.tests.test_gps.test_gps import (
    TestTgGps,
    TestTgGps_6_1,
    TestTgGps_6_4,
    TestTgGpsStr1,
    TestTgGpsStr2,
)
from terragraph.ctf.tests.test_ibf.test_ibf import (
    TestTgIbf_AttenuationEffect,
    TestTgIbf_Minion,
)
from terragraph.ctf.tests.test_iot.test_network_ignition import (
    TestNetworkIotNIT1NIT2,
    TestNetworkIotNIT3,
    TestNetworkIotNIT4,
    TestNetworkIotNIT5,
)
from terragraph.ctf.tests.test_iot.test_network_software_upgrade import (
    TestNetworkIotNSU2,
    TestNetworkIotNSU3,
)
from terragraph.ctf.tests.test_iot.test_node_iot import TestNodeIotNLT1
from terragraph.ctf.tests.test_iot.test_node_routing import TestNodeIotRouting
from terragraph.ctf.tests.test_iot.test_node_software_upgrade import (
    TestIotNSU1,
    TestNodeIotNSU2,
)
from terragraph.ctf.tests.test_iot.test_node_throughput import TestIotNodeThroughput
from terragraph.ctf.tests.test_iot.test_node_time_sync import (
    TestNodeIotNOTS1,
    TestNodeIotNOTS2,
    TestNodeIotNOTS3,
)
from terragraph.ctf.tests.test_iot.test_node_wireless_security import TestNodeIotNWS1
from terragraph.ctf.tests.test_la.test_la import TestTgLa1
from terragraph.ctf.tests.test_la.test_la1 import TestTgLa
from terragraph.ctf.tests.test_la.test_la2 import TestTgLa2
from terragraph.ctf.tests.test_multihop_latency.test_mh_latency import TestTgMHLatency
from terragraph.ctf.tests.test_multihop_throughput.test_puma_3sector_9 import (
    TestTg3Sector,
)
from terragraph.ctf.tests.test_multihop_throughput.test_puma_tp_mh_xhop_9 import (
    TestTgTPMHXHop9,
)
from terragraph.ctf.tests.test_puma_e2e_network_up_x86 import (
    TestTgE2ENetworkUpExternalX86,
)
from terragraph.ctf.tests.test_sta.test_stability import TestStability
from terragraph.ctf.tests.test_sta.test_stability_burst import TestStabilityBurst
from terragraph.ctf.tests.test_tg_image_upgrade import TestTgImageUpgrade
from terragraph.ctf.tests.test_x86_e2e_upgrade import TestTgX86E2EUpgrade
from terragraph.ctf.tests.tests_8021x.test_8021x import (
    TestTg8021xIgniteAndTraffic,
    TestTg8021xIgnition,
    TestTg8021xIgnition16,
    TestTg8021xInvalidCredentials,
    TestTg8021xMissingCredentials,
)
from terragraph.ctf.tests.tg_collect_logs import TgCollectLogs
from terragraph.ctf.tests.xena.test_xena import TestTgXenaLinkUp

# All available tests
TG_CTF_TESTS = {
    TestTgCtfTest.__name__: TestTgCtfTest,
    TestTgPumaChrony.__name__: TestTgPumaChrony,
    TestTgPumaLinkUp.__name__: TestTgPumaLinkUp,
    TestTgPumaLinkUpKernel.__name__: TestTgPumaLinkUpKernel,
    TestTgPumaIpv6Up.__name__: TestTgPumaIpv6Up,
    TestTgPumaIpv6UpKernel.__name__: TestTgPumaIpv6UpKernel,
    TestTgMicrocodeLog.__name__: TestTgMicrocodeLog,
    TestP2PTraffic.__name__: TestP2PTraffic,
    TestP2PTrafficJumboFrame.__name__: TestP2PTrafficJumboFrame,
    TestTgPumaIpv6BGP.__name__: TestTgPumaIpv6BGP,
    TestTgPumaIpv6BGPKernel.__name__: TestTgPumaIpv6BGPKernel,
    TestTgPumaIpv6FrrBgp.__name__: TestTgPumaIpv6FrrBgp,
    TestTgDistributedIgnition.__name__: TestTgDistributedIgnition,
    TestTgPumaImageUpgrade.__name__: TestTgPumaImageUpgrade,
    TestTgE2ENetworkUpExternal.__name__: TestTgE2ENetworkUpExternal,
    TestTgE2ENetworkUpExternalX86.__name__: TestTgE2ENetworkUpExternalX86,
    TestTgE2ENetworkUpInternal.__name__: TestTgE2ENetworkUpInternal,
    TestTgPumaTopoScan.__name__: TestTgPumaTopoScan,
    TestTgX86Setup.__name__: TestTgX86Setup,
    TestTgPumaLinkReassoc.__name__: TestTgPumaLinkReassoc,
    TestTgPumaLinkReassocKernel.__name__: TestTgPumaLinkReassocKernel,
    TestTgX86E2EUpgrade.__name__: TestTgX86E2EUpgrade,
    TestTgPumaIperfVpp.__name__: TestTgPumaIperfVpp,
    TestTgLLS.__name__: TestTgLLS,
    TestTgTPMHXHop9.__name__: TestTgTPMHXHop9,
    TestTg8021xIgnition.__name__: TestTg8021xIgnition,
    TestTg8021xIgniteAndTraffic.__name__: TestTg8021xIgniteAndTraffic,
    TestTg8021xIgnition16.__name__: TestTg8021xIgnition16,
    TestTg8021xInvalidCredentials.__name__: TestTg8021xInvalidCredentials,
    TestTg8021xMissingCredentials.__name__: TestTg8021xMissingCredentials,
    TestX86TGIgn.__name__: TestX86TGIgn,
    TestTgMinionRestart.__name__: TestTgMinionRestart,
    TestX86TGIgnTraffic.__name__: TestX86TGIgnTraffic,
    TestTgVxlanTraffic.__name__: TestTgVxlanTraffic,
    TestTgSuperAssoc.__name__: TestTgSuperAssoc,
    TestNodeIotNLT1.__name__: TestNodeIotNLT1,
    TestNodeIotNWS1.__name__: TestNodeIotNWS1,
    TestTgE2EReg2.__name__: TestTgE2EReg2,
    TestTgE2EReg3.__name__: TestTgE2EReg3,
    TestTgE2EReg4.__name__: TestTgE2EReg4,
    TestTg3Sector.__name__: TestTg3Sector,
    TestNodeIotNOTS1.__name__: TestNodeIotNOTS1,
    TestNodeIotNOTS2.__name__: TestNodeIotNOTS2,
    TestNodeIotNOTS3.__name__: TestNodeIotNOTS3,
    TestNodeIotRouting.__name__: TestNodeIotRouting,
    TestIotNSU1.__name__: TestIotNSU1,
    TestNodeIotNSU2.__name__: TestNodeIotNSU2,
    TestIotNodeThroughput.__name__: TestIotNodeThroughput,
    TestTgPumaSrv6L2.__name__: TestTgPumaSrv6L2,
    TestTgPumaVxlanL2.__name__: TestTgPumaVxlanL2,
    TestX86TGReIgnCntrIf.__name__: TestX86TGReIgnCntrIf,
    TestX86TGReIgnCntrSvc.__name__: TestX86TGReIgnCntrSvc,
    TestX86TGIgnInvalOvrds.__name__: TestX86TGIgnInvalOvrds,
    TestX86TGReIgnLink.__name__: TestX86TGReIgnLink,
    TestX86TGReIgnNodeReAdd.__name__: TestX86TGReIgnNodeReAdd,
    TestX86TGReIgnReboot.__name__: TestX86TGReIgnReboot,
    TestX86TGIgnModifyConfig.__name__: TestX86TGIgnModifyConfig,
    TestX86TGIgnMinionStop.__name__: TestX86TGIgnMinionStop,
    TestTgMHLatency.__name__: TestTgMHLatency,
    TestX86TGIgnTrafficSerial.__name__: TestX86TGIgnTrafficSerial,
    TestNetworkIotNIT1NIT2.__name__: TestNetworkIotNIT1NIT2,
    TestNetworkIotNIT3.__name__: TestNetworkIotNIT3,
    TestNetworkIotNIT4.__name__: TestNetworkIotNIT4,
    TestNetworkIotNIT5.__name__: TestNetworkIotNIT5,
    TestTgGps.__name__: TestTgGps,
    TestTgGps_6_1.__name__: TestTgGps_6_1,
    TestTgGps_6_4.__name__: TestTgGps_6_4,
    TestTgGpsStr1.__name__: TestTgGpsStr1,
    TestTgGpsStr2.__name__: TestTgGpsStr2,
    TestTgLOT.__name__: TestTgLOT,
    TestNetworkIotNSU2.__name__: TestNetworkIotNSU2,
    TestNetworkIotNSU3.__name__: TestNetworkIotNSU3,
    TestTgIbf_Minion.__name__: TestTgIbf_Minion,
    TestTgIbf_AttenuationEffect.__name__: TestTgIbf_AttenuationEffect,
    TestTgRouteLinkFlap.__name__: TestTgRouteLinkFlap,
    TestTgRouteMCSChange.__name__: TestTgRouteMCSChange,
    TestTgRouteLinkDown.__name__: TestTgRouteLinkDown,
    TestPBF.__name__: TestPBF,
    TestTgXenaLinkUp.__name__: TestTgXenaLinkUp,
    Qos_P2p.__name__: Qos_P2p,
    Qos_P2p_2.__name__: Qos_P2p_2,
    Qos_P2p_3.__name__: Qos_P2p_3,
    Qos_P2p_5.__name__: Qos_P2p_5,
    Qos_Ptmp.__name__: Qos_Ptmp,
    Qos_Nw.__name__: Qos_Nw,
    TestTgQos.__name__: TestTgQos,
    TestTgPumaP2PGolay.__name__: TestTgPumaP2PGolay,
    TestTgAT.__name__: TestTgAT,
    TestPumaE2EGolay.__name__: TestPumaE2EGolay,
    TestTgLa.__name__: TestTgLa,
    TestTgLa1.__name__: TestTgLa1,
    TestTgLa2.__name__: TestTgLa2,
    TgCollectLogs.__name__: TgCollectLogs,
    TestTgLOT3.__name__: TestTgLOT3,
    TestX86TGIgnMultiPOP.__name__: TestX86TGIgnMultiPOP,
    TestStability.__name__: TestStability,
    TestStabilityBurst.__name__: TestStabilityBurst,
    TestPumaE2EGolayDiffResp.__name__: TestPumaE2EGolayDiffResp,
    TestPumaE2EGolayDiffRx.__name__: TestPumaE2EGolayDiffRx,
    TestTgImageUpgrade.__name__: TestTgImageUpgrade,
}

# All available test suites
TG_CTF_TEST_SUITES = {
    "TestTgPumaNightlySanity": [
        TestTgPumaIpv6Up,
        TestTgPumaIpv6BGP,
        TestTgPumaIpv6UpKernel,
        TestTgE2ENetworkUpInternal,
        TestTgPumaIperfVpp,
    ]
}
