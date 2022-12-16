# Routing Tests

## All Tests

### `PUMA_RF_ROU1` Link Flap Route Convergence
Description: This test is check if Open/R routes converge after random links are
repeatedly flapped in the network.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Bring up IF setup with external E2E controller with BGP
* Run iPerf traffic of 300 Mbps on every link
* Flap a random selection of 30% of links for a duration of 15 mins
* Measure time took for network to converge
* Run  10 iterations depending on time & availability

Pass/Fail Criteria:
* Make sure following validations pass:
    * All nodes and links in network are online and alive
    * `breeze nss validate` passes
    * `breeze fib validate` passes
    * Make sure every node has all routes to every other nodes
    * Make sure every node has all prefixes
    * Make sure `breeze kvstore adj --nodes all` match on all nodes

### `PUMA_RF_ROU2` Open/R Flap Route Convergence
Description: This test is check if Open/R routes converge after repeatedly
flapping `openr` process on random nodes in the network.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Run iPerf traffic of 300 Mbps on every link
* Flap `openr` process on a random selection of 30% of nodes in the network for
  a duration of 15 mins
* Measure time took for network to converge
* Run 10 iterations

Pass/Fail Criteria:
* Make sure following validations pass:
    * All nodes and links in network are online and alive
    * `breeze nss validate` passes
    * `breeze fib validate` passes
    * Make sure every node has all routes to every other nodes
    * Make sure every node has all prefixes
    * Make sure `breeze kvstore adj --nodes all` match on all nodes

### `PUMA_RF_ROU3` Fib Flap Route Convergence (fib_vpp process)
Description: This test is check if fib routes converge after repeatedly flapping
fib process on random nodes in the network.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Run iPerf traffic of 300 Mbps on every link
* Flap fib process on a random selection of 30% of nodes in the network for a
  duration of 15 mins
* Measure time took for network to converge
* Run 10 iterations

Pass/Fail Criteria:
* Make sure following validations pass:
    * All nodes and links in network are online and alive
    * `breeze nss validate` passes
    * `breeze fib validate` passes
    * Make sure every node has all routes to every other nodes
    * Make sure every node has all prefixes
    * Make sure `breeze kvstore adj --nodes all` match on all nodes

### `PUMA_RF_ROU4` Reboot Route Convergence
Description: This test is check if Open/R routes converge after rebooting random
nodes in the network.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Reboot a random selection of 20% of the nodes in the network
* Measure time took for network to converge
* Run 5-10 iterations

Pass/Fail Criteria:
* Make sure following validations pass:
    * All nodes and links in network are online and alive
    * `breeze nss validate` passes
    * `breeze fib validate` passes
    * Make sure every node has all routes to every other nodes
    * Make sure every node has all prefixes
    * Make sure `breeze kvstore adj --nodes all` match on all nodes

### `PUMA_RF_ROU5` Link Down Reroute Convergence Time
Description: The purpose of this test is to ensure that on link down, Open/R
finds a new route within 240 ms.

Test Setup: Any Fig 0 with 4 IF links

Procedure:
* Program all attenuators with 0 dB attenuation.
* Make sure time for attenuator between DN1 → DN2 is correct otherwise test will
  fail
* Bring up the Fig 0 using E2E
* Ping1: Ping all terra links over lo to validate connectivity
* Parallel block
    * Ping3: Ping DN1 → DN2 for 240 sec with a period of 20ms
    * After 120 sec, set attenuation between DN1-DN2 to 60 dB to cause link to
      go down

Pass/Fail Criteria:
* Ping1: Average ping latency for terra links (terra-lo-RTT) < 3.8 ms
* Ping3: Average ping latency < $(98*\text{terra-lo-RTT} + (240-98)*3*\text{terra-lo-RTT})/240*1.1$
    * Ping should go over DN1 → DN2 path for the first ~98 seconds, and the
      longer 3-IF-hop path afterward
    * terra-lo-RTT is the average RTT of pings sent across the terra links on
      the lo interface (approximately 3.3 ms)
    * 98 seconds because TAS spends ~22 seconds doing initializing steps before
      starting the actual ping
    * 1.1 is to allow for 10% room above the expected average ping latency
      because the calculation is approximate
* Ping3: Allowed ping max latency < 240ms
* Ping3: Allowed ping packet loss <= 0.1 % ((Ping packets transmitted - packets
  received)*20ms < 240ms)
* Time difference between attenuation going up and Open/R rerouting finishing <
  240ms for all nodes
    * Use Open/R log "Processing route add/update for x routes" with x > 0
    * Use the first such log within -1s to 5s of attenuation-up-timestamp (-1s
      is to allow for mismatch in attenuator and node timestamps)

### `PUMA_RF_ROU6` MCS-Based Reroute Convergence Time
Description:  The purpose of this test is to ensure that on MCS change across
boundary, Open/R finds a new route within 240 ms.

Test Setup: Any Fig 0 with 4 IF links

Procedure:
* Program all attenuators with 0 dB attenuation.
* Make sure time for attenuator between DN1 → DN2 is correct otherwise test will
  fail
* Bring up the Fig 0 using E2E (MCS based routing works only if minion is
  running on the nodes)
* Set `openrParams.linkMetricConfig.metricMap.MCSX` to 15 for MCS4, MCS5, MCS6,
  MCS7 and MCS8 for all nodes through E2E
* Ping1: Ping all terra links over lo to validate connectivity
* Parallel block
    * Ping3: Ping DN1 → DN2 for 240 sec with a period of 20ms
    * After 120 sec, set attenuation between DN1-DN2 to 30 dB to cause link MCS
      to drop to the range MCS4-MCS8

Pass/Fail Criteria:
* Ping1: Average ping latency for terra links (terra-lo-RTT) < 3.8 ms
* Ping3: Average ping latency < $(98*\text{terra-lo-RTT} +(240-98)*3*\text{terra-lo-RTT})/240*1.1$
    * Ping should go over DN1 → DN2 path for the first ~98 seconds, and the
      longer 3-IF-hop path afterward
    * terra-lo-RTT is the average RTT of pings sent across the terra links on
      the lo interface (approximately 3.3 ms)
    * 98 seconds because TAS spends ~22 seconds doing initializing steps before
      starting the actual ping
    * 1.1 is to allow for 10% room above the expected average ping latency
      because the calculation is approximate
* Ping3: Allowed ping max latency < 240ms
* Ping3: Allowed ping packet loss <= 0.1 % ((Ping packets transmitted - packets
  received)*20ms < 240ms)
* Time difference between attenuation going up and Open/R rerouting finishing <
  240ms for all nodes
    * Use Open/R log "Processing route add/update for x routes" with x > 0
    * Use the first such log within -1s to 5s of attenuation-up-timestamp (-1s
      is to allow for mismatch in attenuator and node timestamps)

### `PUMA_RF_ROU7` Link Flap Backoff
Description: The purpose of this test is to ensure that after the link flaps,
Open/R debouncing keeps the link down for expected time.

Test Setup: Any Fig 0 with 4 IF links

Procedure:
* Program all attenuators with 0 dB attenuation.
* Bring up the Fig 0 (use E2E so links are re-ignited by themselves after
  flapping)
* Set `envParams.OPENR_LINK_FLAP_MAX_BACKOFF_MS` to 60000 for DN1 and/or DN2
  through E2E
* Ping1: Ping all terra links over lo to validate connectivity
* Ping2: Ping all USB links over lo to validate connectivity
* Parallel block
    * On DN1 and/or DN2 (node with high backoff) run command:
        * `for((i=1; i<=120; i++)); do date; breeze lm links | grep terra0; done > out.txt &`
    * Set attenuation between DN1-DN2 to 60 dB to cause link to go down
    * With delay of 15 seconds bring attenuation back to 0
    * With delay of 30 seconds set attenuation to 60 dB
    * With delay of 45 seconds bring attenuation back to 0
    * With delay of 60 seconds set attenuation to 60 dB
    * With delay of 75 seconds bring attenuation back to 0
    * With delay of 90 seconds set attenuation to 60 dB
    * With delay of 105 seconds bring attenuation back to 0
    * With delay of 110 seconds, start ping DN1 → DN2 for 30 sec

Pass/Fail Criteria:
* Ping1: Average ping latency for terra links (terra-lo-RTT) < 3.8 ms
* Ping3: $2*\text{terra-lo-RTT}$ < Average ping latency < $3*\text{terra-lo-RTT}*1.05$
    * 3x because ping should go over the longer 3-terra-link path because the
      direct link is in 60 sec backoff
    * terra-lo-RTT is the average RTT of pings sent across the terra links on
      the lo interface (approximately 3.3 ms)
    * 1.05 is to allow for 5% room above the expected average ping latency
      because 3.3 is approximate
* In out.txt on DN1 and/or DN2 (node with high backoff), maximum 60sec > 'Hold'
  time > 55 sec

### `PUMA_RF_ROU8` MCS-Based Routing
Description: The purpose of this test is to ensure that routing uses MCS based
costs.

Test Setup: Any Fig 0 with 4 IF links

Procedure:
* Program all attenuators with 0 dB attenuation.
* Bring up the Fig 0 using E2E (MCS based routing works only if minion is
  running on the nodes)
* In node config set `openrParams.linkMetricConfig.metricMap.MCSX` to 15 for
  MCS4, MCS5, MCS6, MCS7 and MCS8 for DN1 and DN2
* Ping1: Ping all terra links over lo to validate connectivity
* Set attenuation between DN1-DN2 to 30dB to cause link MCS to drop below MCS8,
  and recored the attenuation-up timestamp
* Add delay of 5 seconds to let the system stabilize
* Ping3: Ping DN1 → DN2 for 240 sec
* Read `/var/log/openr/current` from DN1 and DN2
* Remove `openrParams.linkMetricConfig.metricMap.MCSX` overrides to restore
  defaults on DN1
* Reset attenuation between DN1-DN2 to 0dB

Pass/Fail Criteria:
* Ping1: Average ping latency for terra links < 3.8 ms
* Ping3: $2*\text{terra-lo-RTT}$ < Average ping latency < $3*\text{terra-lo-RTT}*1.05$
    * 3x because ping should go over the longer 3-terra-link path
    * terra-lo-RTT is the average RTT of pings sent across the terra links on
      the lo interface (approximately 3.3 ms)
    * 1.05 is to allow for 5% room above the expected average ping latency
      because 3.3 is approximate
* In Open/R logs, 'Overriding metric for interface terra0 to 15' should exist
* Timestamp for that log should be within 5 seconds of the attenuation-up
  timestamp
