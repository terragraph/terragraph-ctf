# E2E Controller Tests

## Basic Tests

### `PUMA_RF_E2E-REG-1` RF Software Upgrade/Downgrade Test
Description: This test is to check that the network successfully does upgrade
and downgrade and comes back online after software upgrade/downgrade.

Test Setup: Fig-of-8

Procedure:
* Upgrade both primary and backup controller to new version
* Downgrade to a previous stable code
* Download code and upgrade whole network to new version
* Measure time taken for prepare and commit phase

Pass/Fail Criteria:
* All nodes should be able to download new code and run upgrade and successful
  come back online within given timeout

### `PUMA_RF_E2E-REG-2` Power Outage network recovery Test
Description: This test checks that after power outage the network ignites by
itself.

Test Setup: Fig-of-8

Procedure:
* Check network is ignited
* Power cycle all nodes by using the PDUs on the poles remotely
* Check network recovery
* Repeat 10 times

Pass/Fail Criteria:
* Validate all links and nodes come back online after power failure within given
  timeout

### `PUMA_RF_E2E-REG-3` POP Fiber cut Test (multi-POP)
Description: This test is to check that if connection to 1 POP node is
terminated then the network will recover and reroute through the other POP
nodes.

Test Setup: Fig-of-8

Procedure:
* Check network is ignited
* Switch off fiber port on ubiquiti switch connecting to one of the POP nodes

Pass/Fail Criteria:
* Network should recover and reroute through other POP node
* All links and nodes should be online in the topology

### `PUMA_RF_E2E-REG-4` POP Fiber cut Test (single-POP)
Description: This test checks network ignition functionality on a standard
figure of 8 topology with single POP. Post network ignition, cutting the fiber
from switch to POP and checking whether the network is down

Test Setup: Fig-of-8

Procedure:
* Ignite the topology (single POP)
* switch off fiber port on ubiquiti switch connecting to POP
* switch on the fiber port on ubiquiti switch connecting to POP

Pass/Fail Criteria:
* Network goes down after the fiber cut to POP happens.
* After switching on the fiber connectivity to POP the network should be up and
  active.

### `PUMA_RF_E2E-1` Network Ignition Tests
Description: This test checks network ignition functionality on a standard
figure of 8 topology. Post network ignition, each node in the topology is pinged
from the controller to validate connectivity.

Test Setup: Fig-of-8

Procedure:
* Bring up the network using x86 controller. To bring up a network,
    * Existing topology file can be copied to the controller and controller can
      be started using systemctl services.
* After ignition of the network, ping from E2E to all nodes.
* Check whether the network is up and active.
* Check the ignition state of the controller using REST API.
  (`/api/getIgnitionState`)

Pass/Fail Criteria:
* All links remain up and reachable from controller to all nodes and ping
  session remains unaffected.
* Ping from E2E to all nodes should succeed.
* Ignition time of the fig-of-8 network must be less than 5 min.

### `PUMA_RF_E2E-2` POP node power cycle test
Description: This test checks network ignition functionality on a standard
figure of 8 topology.  In this test, POP node comes back online after the power
cycle and all links and nodes in the network are expected to recover.

Test Setup: Fig-of-8

Procedure:
* Bring up the network using x86 controller with all the nodes.
* Check whether the network is up and active.
* Power cycle the pop_node in the topology (`/api/rebootNode`)
* While pop_node is down, send traffic through POP node to all other nodes.
* While sending traffic when POP node is down, throughput drops to zero.
* After POP is up, throughput should raise.
* Validate all wireless links are up and routable from the pop_node.

Pass/Fail Criteria:
* Throughput of zero is observed while traffic is pushed from controller when
  POP is down.
* Raising in the throughput value should happen while traffic is pushed from
  controller after POP is up.

### `PUMA_RF_E2E-3` Node failure during network ignition
Description: This test checks network ignition functionality on a standard
figure of 8 topology.  However, during the process of network ignition, some
node are rebooted and check whether E2E is bringing up the network.

Test Setup: Fig-of-8

Procedure:
* Ignite the network using x86 controller.
* During network ignition, randomly pick a DN and reboot it.
* Wait for the last DN to boot up (ping sectors through OOB).
* Check to see all the links in the topology came up successfully.
* Ping each node and see for connectivity.
* Iterate node bootup for 5 times and check for connectivity

Pass/Fail Criteria:
* All the links in the testbed successfully come up.

### `PUMA_RF_E2E-4` Link failure during network ignition
Description: This test checks network ignition functionality on a standard
figure of 8 topology. During the process of network ignition, any of the
previously ignited links goes down.

Test Setup: Fig-of-8

Procedure:
1. Ignite the network using x86 controller.
2. During network ignition, bring down an ignited link (tg link down/attenuator)
   using `/api/setLinkStatus`.
3. Check to see all the links in the topology came up successfully after 60
   sec (re-ignition time?).
4. Ping all nodes and see for connectivity.

Pass/Fail Criteria:
1. All the links in the testbed successfully come up.
2. No wireless link takes more than 5 attempts to come up.

### `PUMA_RF_E2E-5` Repeated link failure(s) post network ignition
Description: This test checks network ignition functionality on a standard
figure of 8 topology. During the process of network ignition, any of the
previously ignited links go down repeatedly.

Test Setup: Fig-of-8

Procedure:
1. Ignite the network and ping across each wireless link to validate
   connectivity.
2. Pick any wireless links at random and take them down (`tg link down`) using
   `/api/setLinkStatus`.
3. Wait (X*60) seconds for E2E controller to re-ignite links.
    * X = { 1, 2, 3, 4 }
4. Ping across each wireless link (can use lo interface) to validate
   connectivity. (`/api/startPing`)
5. Ping to each end of each wireless link to validate they are reachable via E2E
   controller and pop_node.
6. Repeat the above steps 20 times.

Pass/Fail Criteria:
1. Network check to see all the links in the topology came up successfully.
2. E2E controller is able to re-ignite all links taken down within (X*60)
   seconds and they are pingable across local DN sector interfaces and reachable
   via the pop_node.

### `PUMA_RF_E2E-6` Repeated node failure(s) post network ignition
Description: This test checks network ignition functionality on a standard
figure of 8 topology. During the process of network ignition, any of the
previously ignited node go down repeatedly.

Test Setup: Fig-of-8

Procedure:
* Ignite the network topology using x86 controller.
* Ping across each wireless link (using link local addresses) to validate
  connectivity. (`/api/startPing`)
* Pick up to X DN sectors at random and take them down (via reboot).
  (`/api/rebootNode`)
* Wait (X*60) seconds for DNs to boot up within 60 seconds.
    * X = { 1, 2, 3, 4 }
* Wait (X*60) seconds for E2E controller to re-ignite all DN sectors.
    * X = { 1, 2, 3, 4 }
* Ping each sector from pop_node.
* Repeat the above steps 10 times.

Pass/Fail Criteria:
* Check to see all the links in the topology came up successfully.
* E2E controller is able to re-ignite all DN sectors taken down within (X*60)
  seconds of them coming up and they are reachable via the pop_node.

### `PUMA_RF_E2E-7` Network outage to controller
Description: This test checks whether network is unperturbed by temporary loss
of connectivity to E2E in figure of 8 topology.

Test Setup: Fig-of-8

Procedure:
1. Ignite the network using x86 controller.
2. Check network state to verify if all links are enabled and nodes are
   reachable(recheck network state).
3. Take down controller network interface for 300 sec (but do not shut down the
   controller)
     * `ifconfig ens160 down; sleep 300; ifconfig ens160 up`
4. In parallel, Ping between nodes while the controller is not reachable from
   them.
5. Recheck network state again after 300sec while pinging across all the nodes

Pass/Fail Criteria:
1. All paths are up and operational after restoration of connection to E2E
2. Ping between all nodes/Paths should have 0% packet loss.

### `PUMA_RF_E2E-8` Controller crash test
Description: This test checks whether network is unperturbed by killing E2E in
figure of 8 topology.

Test Setup: Fig-of-8

Procedure:
1. Ignite the network using x86 controller.
2. Check network state to verify if all links are enabled and nodes are
   reachable(recheck network state).
3. Start iterate (count: 5)
    1. Start ping from from POP to any node and in parallel, kill E2E controller
       on the controller x86. Ping across each wireless link (using lo address)
       to validate L3 wireless connectivity. (`killall e2e_controller`)
    2. Bring down any link in the network while E2E is down. (`tg link down`)
    3. Re-spawn E2E controller on x86 and wait 60 seconds
4. End iterate

Pass/Fail Criteria:
1. All links remain up and reachable via POP node after re-spawning E2E
   controller.
2. Ping session remains unaffected during the duration of controller
   kill/restart.

### `PUMA_RF_E2E-9` Software Upgrade/Downgrade test using BitTorrent
Description: The purpose of this test is to validate the BitTorrent SW upgrade
process at the network level, for a figure of "8" network topology.

Test Setup: Fig-of-8

Upgrade steps:
* Add the image binary file manually to the `/data/images` directory and restart
  controller.
* The image file name has to be in the format `<NAME>.bin` where NAME is the MD5
  string of the binary image. The MD5 string is part of the binary file header.
* During ignition of controller, global addressable ipv6 interface on the
  controller is set on the flag as `bt_tracker_ipv6_global_addressable_ifname`
  "interfacename".

APIs used:
```
/api/sendUpgradeRequest
/api/getUpgradeState
/api/getUpgradeCommitPlan
/api/addUpgradeImage
/api/delUpgradeImage
/api/listUpgradeImages
/api/abortUpgrade
```

Procedure:
1. Bring up TG network using E2E controller on a X86 machine. Set the flag
   `bt_tracker_ipv6_global_addressable_ifname` "interfacename" during ignition.
2. Start the tracker in the port 6969 by running command:
    * `tg upgrade torrent start_tracker -g ens160 -p 6969`
3. Kill the running e2e_controller and then start again.
4. Run the prepare torrent command"
    * `tg upgrade network prepare_torrent -m 'magnet url' --md5 'md5 of bin'`
    * Magnet url and md5 can be obtained by running command on the controller:
        * `tg upgrade torrent list_images`
5. Run a script (`/data/stop_minion.sh`) on all nodes to emulate random nodes
   down by restarting e2e_minion at random time interval.
6. Delay for 300 seconds
7. Check if all nodes are prepared (excluding the ones which were
   down). Optimization: All nodes should be prepared.
8. Run command to prepare all nodes again.
9. Check if all nodes are prepared (including the ones which were down).
10. Commit upgrade:
    * `tg upgrade network commit`
11. Verify if upgrade is successful.
12. Follow the steps from 2 to 10 for downgrade with new image.
13. Verify if downgrade is successful.

Pass/Fail Criteria:
1. Network comes up with new software for all nodes.
2. Optimization: Nodes are not reflashed a 2nd time with same software version.

### `PUMA_RF_E2E-10` Remove and add nodes and links from topology file
Description: Validate controller addition and deletion of nodes/links to
topology from the TG CLI.

Test Setup: Fig-of-8

Procedure:
1. Bring up network using x86 controller and check if all links are up.
2. Disable auto-ignition.
3. Bring down 1 or 2 links from the topology
4. Remove the links brought down in step 3 using E2E API.
5. Remove nodes forming the links which are down from the topology using E2E
   CLI.
6. check if the E2E state machine is stable and nodes are deleted.
7. Add nodes back to topology using API.
8. Add the deleted links back to topology using API.
9. Make the links alive by using API.
10. Enable auto ignition.
11. Verify the new nodes are now in topology and reporting to controller
12. Run ping to verify connectivity.
```
APIs used:
/api/setLinkStatus
/api/setIgnitionState
/api/addLink
/api/delLink
/api/addNode
/api/delNode
/api/startPing
```

Pass/Fail Criteria:
1. Verify that the E2E state machine is stable and nodes are deleted and added
   back.

### `PUMA_RF_E2E-11` Verify controller side config validation framework
Description: E2E Verify controller config tests to validate E2E will throw error
if incorrect values are pushed for the nodes.

Test Setup: Fig-of-8

Procedure:
1. Ignite network using x86 controller.
2. Set `forceGpsDisable` to "x" for a node using TG CLI on the controller.
3. Set `OOB_INTERFACE` to "nic3" for the network or particular node using TG
   CLI.
4. Set `laMaxMcs` to 50 using TG CLI on controller.
5. Check if all commands fail with error and config is not pushed to network.

APIs used:
```
/api/setNodeOverridesConfig
/api/getNodeOverridesConfig
```

Pass/Fail Criteria:
1. Verify if the config is validated on the controller side and incorrect values
   are not pushed to the network.

### `PUMA_RF_E2E-12.2` Multiple node BGP POP config
Description: To test multiple BGP sessions to two different IP's on switch using
different sites in a network.

Test Setup: Fig-of-8

Procedure:
1. Configure multiple BGP sessions from 2 different switches to both the POP
   sites.
2. Ignite the network and validate both POP are up.
3. Disconnect fiber cable from one POP (manually? / port down?).
4. Run pings from both the POP nodes.
5. While ping is running, cut POP and check for ping latency.

APIs used:
```
/api/getNodeConfig
/api/setNodeOverridesConfig
/api/getNodeOverridesConfig
```

Pass/Fail Criteria:
1. All pings go through and there is no loss of connectivity while failing POP
   or connectivity to router.
2. Ping latency (need to confirm numbers)

### `PUMA_RF_E2E-12.1` Network ignition with 2 POP sites with BGP
Test Setup: Fig-of-8

Procedure:
1. Configure 2 sites on fig-8 as POP nodes with BGP configured to the same peer
2. Ignite the network and validate both POP nodes and whole network is up
3. Validate BGP sessions are established on both POP nodes and default route is
   advertized
4. Ping all nodes from POP sites to validate connectivity

Pass/Fail Criteria:
1. Network Ignites successfully
2. Both POP nodes are online, with BGP established and advertising default
3. All pings go through

### `PUMA_RF_E2E-13.1` High Availability test - network interface Down on primary E2E
Description: This test checks high availability feature of E2E on a standard
figure of 8 topology (with two E2E controllers on a network).

Test Setup: Fig-of-8

Procedure:
1. Ignite the network using primary x86 controller with all the necessary
   controller configs on primary and secondary.
2. Check network state to verify if all links are enabled and nodes are
   reachable (recheck network state).
3. In parallel:
    1. Take down primary controller network interface for 300 sec (but do not
       shut down the controller).
    2. Ping between nodes.
4. Ping all nodes from primary controller.
5. Check state. (`/api/getHighAvailabilityState`)

Pass/Fail Criteria:
1. All paths are up and operational after restoration of connection to E2E and
   ping between all nodes/Paths should have 0% packet loss.
2. when primary controller is down the backup should be in 'active' state and
   network should remain up
3. when primary is restarted, it should go back to 'active' state and backup
   should go back to 'passive' state
4. All links and nodes in network should remain online

### `PUMA_RF_E2E-13.2` High Availability test - reboot primary E2E
Description: This test checks high availability feature of E2E on a standard
figure of 8 topology (with two E2E controllers on a network).

Test Setup: Fig-of-8

Procedure:
1. Ignite the network using primary x86 controller with all the necessary
   controller configs on primary and secondary.
2. Check network state to verify if all links are enabled and nodes are
   reachable (recheck network state).
3. In parallel:
    1. Reboot the primary E2E
    2. Ping between nodes.
4. Ping all nodes from primary controller.
5. Check state. (`/api/getHighAvailabilityState`)

Pass/Fail Criteria:
1. All paths are up and operational after restoration of connection to E2E and
   ping between all nodes/Paths should have 0% packet loss.
2. when primary controller is down the backup should be in 'active' state and
   network should remain up
3. when primary is restarted, it should go back to 'active' state and backup
   should go back to 'passive' state
4. All links and nodes in network should remain online

### `PUMA_RF_E2E-14` Controller switch after topology change, changes reflect in passive controller
Description: This test checks high availability feature of E2E on a standard
figure of 8 topology (with two E2E controllers on a network).

Test Setup: Fig-of-8

Procedure:
1. Ignite the network using primary x86 controller with all the necessary
   controller configs on primary and secondary.
2. Check network state to verify if all links are enabled and nodes are
   reachable (recheck network state).
3. Ping all nodes from primary controller
4. Remove some links and nodes in the topology file.
    1. Backup original topology file to later restore
5. Confirm change propagated back to secondary
6. Give outage to primary for 300s and restore original topology on primary
7. Ping all nodes from secondary controller - during 300s outage - Ensure its
   the same as step 5 missing the changes made
8. After primary comes up ensure another ping check matches step 5

Pass/Fail Criteria:
1. All paths are up and operational after restoration of connection to E2E
2. Ping between all nodes/Paths should have 0% packet loss
3. At the end of step 6, passive controller topology should not include the
   nodes and links removed.
4. At the end of step 8, passive controller topology should show the nodes and
   links added.
5. Ping between all nodes/Paths should have 0% packet loss

### `PUMA_RF_E2E-15` E2E does not report link re-ignitions in IF steady state
Description: To verify there are no link re-ignition attempts when the network
is stable.

Test Setup: Fig-of-8

Procedure:
1. Bring up TG network using E2E controller on x86 machine.
2. Recheck network state.
3. Ping for 3660 seconds on all terra interface for all links.
4. Recheck network state.

Pass/Fail Criteria:
1. All pings should go through with 0% packet loss.
2. LinkupAttempts in the topology should not increment.

### `PUMA_RF_E2E-17` Change channel, MCS, txpower, Disable GPS of entire network
Description: Validate if network remains in a stable state if channel, MCS,
TxPower is changed and all nodes are up. Also, check if network remains in a
stable state if GPS is disabled in-band using config manager.

Test Setup: Fig-of-8(RF)

Procedure:
1. Bring up the F8-CN network using the E2E controller with managed config
   enabled
2. Change channel to 3.
    1. `tg fw network channel_config --channel #` (# = 1, 3, & 4)
    2. `/api/setNodeOverridesConfig`
3. Check if network remains up after config change (expected action is 'set fw
   params when changed' when config is changed so links and node should stay up
   after config change)
4. Check fw params to see if channel is updated
5. Change channel back to 2.
6. Check if network remains up after config change (expected action is 'set fw
   params when changed')
7. Check fw params to see if channel is updated
8. Change MCS to 3/5/7/9/10/12 on all nodes using E2E API
9. Check if network remains up after config change (expected action is 'set fw
   params when changed')
10. Check fw params to see if channel is updated
11. Change MCS back to 12.
12. Check if network remains up after config change (expected action is 'set fw
    params when changed')
13. Check fw params to see if channel is updated
14. Change TxPower to 12/17/21 on different nodes using using E2E API.
15. Check if network remains up after config change (expected action is 'set fw
    params when changed')
16. Check fw params to see if channel is updated
17. Change TxPower back to 21.
18. Check if network remains up after config change (expected action is 'set fw
    params when changed')
19. Check fw params to see if channel is updated
20. Disable GPS for whole network using E2E API (timeout: 300 sec)
21. Check if network remains up after config change (expected action is 'set fw
    params when changed')
22. Check if GPS is disabled in all nodes in firmware
23. Enable GPS back in all nodes.
24. Check if network remains up after config change (expected action is 'set fw
    params when changed')

Pass/Fail Criteria:
* Verify channel is changed for whole network and all nodes/link are online on
  new channel using TG CLI after step 5.
* MCS is changed for whole network and all nodes/link are online. Nodes and
  links should not flap while MCS is changed (after step 9)
* TxPower is changed for whole network and all nodes/link are online (after step
  11). Nodes and links should not flap while Tx power is changed.
* Network remains up with GPS disabled on all nodes.(after step 15)

### `PUMA_RF_E2E-18` E2E controller should ignite the CNs even when some other CNs and/or links are down
Description: To verify that E2E controller is able to ignite the P2MP setup even
when some nodes and links are down.

Test Setup: P2MP

Procedure:
1. Bring up TG network(P2MP setup) using E2E controller on x86 machine.
2. Recheck network state.
3. Stop minion on CN0, CN1, CN2 and CN3.
4. Recheck network state should show the CN0,CN1, CN2 and CN3 nodes as offline
   and links associated with them as false.
5. Give a delay of 60 seconds.
6. Start minion on CN0 and CN1.
7. Recheck network state should show the CN2 and CN3 nodes as offline and links
   associated with them as false while other links(CN0 and CN1) should be
   ignited.
8. Stop minion service on  CN0 and CN1.
9. Start minion on CN2 and CN3.
10. Give a delay of 60 seconds and check network state
11. Recheck network state should show the CN0 and CN1 nodes as offline and links
    associated with them as false. CN2 and CN3 should show as ONLINE and links
    associated with them as true.
12. Start minion on CN0 and CN1.
13. Network should come up with all nodes after a delay of 60 seconds.

Pass/Fail Criteria:
1. Recheck network state after step 13 should have all the nodes as online and
   all links as true.

## Neighbor Discovery Tests

### `PUMA_RF_E2E-19` Topology Scan tests
Description: This test performs a topology scan at a given node, returning
information about nearby nodes in a P2MP setup.

Test Setup: RF P2MP

Procedure:
1. Start the E2E controller service in E2E controller
2. Set the auto ignition to be disabled.
3. Shut down the DN --> CN1 and DN—CN2 links down (`tg link down`)
4. Initiate a Topology Scan (2 times) from DN using API service (`txNode`: DN)
   using `/api/startTopologyScan`.

Pass/Fail Criteria:
* The output of the API call must have the details of all the CN1 and CN2(whose
  links are down) as responders address in the network. It must have 2 outputs
  with all the CN's details.
* Check in the output of API for the CN1 and CN2 MAC address

### `PUMA_RF_E2E-20` Link Discovery scan tests
Description: This test performs a link discovery scan at a given node, returning
information about the best link(s) for a node.

Test Setup: RF P2MP

Procedure:
1. Start the E2E controller service in E2E controller
2. Set the auto ignition to be disabled. (Make sure the DNs and CN0 link is not
   alive with `tg link down`)
3. Initiate a Topology Scan from CN using API service (`targetMac`: CN0) using
   `/api/startLinkDiscoveryScan`.
4. Use API call to get the results of the scan status.
   (`/api/getLinkDiscoveryScanStatus`)

Pass/Fail Criteria:
* At the end of step 3, "Link discovery scans started' message must be received.
* The output of the API call after step 4 must have the MAC address of DN which
  have link in the topology file.

### `PUMA_RF_E2E-21` Redundancy-DN goes down
Description: P2P test between DN-P and CN where DN-P goes down and CN connects
to the backup DN-B

Test Setup: Fig-of-8

Procedure:
* Initialize the topology with the backup link DN-B ↔ CN and add
  is_backup_cn_link = true
* Bring up the link Between DN-P ↔ CN using E2E
* Power down DN-P using PDU (don't bring it up)
* Controller should bring up the link between DN-B ↔ CN (Only if DN-P has been
  down for over 5 mins as `linkup_backup_cn_link_interval` default value is 5
  mins)
    * Run test with different interval values: 30 sec, 1 min, 3 min and default
      value (5 min)

Passing:
* E2E controller will ignite the DN-B ↔ CN link after DN-P goes down

### `PUMA_RF_E2E-22` Redundancy-DN goes down
Description: P2P test between DN-P and CN where DN-P ↔ CN goes down DN-P turns
off and CN connects to the backup DN-B

Test Setup: Fig-of-8

Procedure:
* Initialize the topology with the backup link DN-B ↔ CN and add
  is_backup_cn_link = true
* Bring up the link Between DN-P ↔ CN using E2E
* Bring down the link between DN-P ↔ CN and then power off DN-P using PDU
* Controller should bring up the link between DN-B ↔ CN (Only if DN-P has been
  down for over 5 mins as `linkup_backup_cn_link_interval` default value is 5
  mins)
    * Run test with different interval values: 30 sec, 1 min, 3 min and default
      value (5 min)

Passing:
* E2E controller will ignite the DN-B ↔ CN link after DN-P goes down

### `PUMA_RF_E2E-23` Redundancy-CN goes down
Description: P2P test between DN and CN where CN goes down and comes back up and
it connects back to DN-P

Procedure:
* Initialize the topology with the backup link DN-B ↔ CN and add
  is_backup_cn_link = true
* Bring up the link Between DN-P ↔ CN using E2E
* Reboot CN
* Controller brings up the link between DN-P ↔ CN

Passing:
* E2E controller will ignite the DN-P ↔ CN link after CN reboots

### `PUMA_RF_E2E-24` Redundancy-CN goes down
Description: P2P test between DN and CN where CN goes down for over 5 mins and
comes back up and it connects back to either DN-P or DN-B

Procedure:
* Initialize the topology with the backup link DN-B ↔ CN and add
  is_backup_cn_link = true
* Bring up the link Between DN-P ↔ CN using E2E
* Power down CN for over 5 mins(using PDU) and power it on
* Controller brings up the link between DN-P ↔ CN or DN-B ↔ CN

Passing:
* E2E controller will ignite either DN-P ↔ CN or DN-B ↔ CN after CN powers on.
