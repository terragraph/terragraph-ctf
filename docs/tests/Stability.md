# Stability Tests

## P2P

### `PUMA_RF_STA1` Low Load Availability - P2P
Description: This test checks network availability on a P2P setup with a load of
50Mbps.

Test Setup: P2P

Procedure:
1. On the P2P setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between two nodes with the following characteristics:
    1. 50Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Link must be available for all 8 hours

### `PUMA_RF_STA2` Medium Load Availability - P2P
Description: This test checks network availability on a P2P setup with a load of
950 Mbps.

Test Setup: P2P

Procedure:
1. On the P2P setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between DN to CN with the following characteristics:
    1. 950 Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA3` High Load Availability - P2P
Description: This test checks network availability on a P2P setup with a load of
1.2Gbps.

Test Setup: P2P

Procedure:
1. On the P2P setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between DN to CN with the following characteristics:
    1. 1.2 Gbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA3.1` High Load Availability - P2P
Description: This test checks network availability on a P2P setup with a load of
2Gbps.

Test Setup: P2P

Procedure:
1. On the P2P setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between DN to CN with the following characteristics:
    1. 2 Gbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA4` Burst Mode Availability - P2P
Description: This test checks network availability on a P2P setup with a burst
load of 1.5 Gbps.

Test Setup: P2P

Procedure:
1. On the P2P setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between DN to CN with the following characteristics:
    1. 1000 Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum
    4. In parallel, after every 1 hour, send iPerf of 3Gbps UDP, bidirectional
       for 15 minutes.

Pass/Fail Criteria:
1. Availability should be 99.9%
2. Every link must get 1000Mbps all the time

## P2MP

### `PUMA_RF_STA5` Low Load Availability - P2MP
Description: This test checks network availability on a P2MP setup with a load
of 50Mbps.

Test Setup: P2MP

Procedure:
1. On the P2MP setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between initiator to 7 responder nodes with the following
   characteristics:
    1. 50Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA6` Medium Load Availability - P2MP
Description: This test checks network availability on a P2MP setup with a load
of 950 Mbps.

Test Setup: P2MP

Procedure:
1. On the P2MP setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between initiator to 7 responder nodes with the following
   characteristics:
    1. 950 Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA7` High Load Availability - P2MP
Description: This test checks network availability on a P2MP setup with a load
of 1.2Gbps.

Test Setup: P2MP

Procedure:
1. On the P2MP setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between initiator to 7 responder nodes with the following
   characteristics:
    1. 1.2 Gbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA8` Burst Mode Availability - P2MP
Description: This test checks network availability on a P2MP setup with a burst
load of 1 Gbps.

Test Setup: P2MP

Procedure:
1. On the P2MP setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between initiator to 7 responder nodes with the following
   characteristics:
    1. 1000 Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum
    4. In parallel, after every 1 hour, send iPerf of 3Gbps UDP, bidirectional
       for 15 minutes.

Pass/Fail Criteria:
1. Availability should be 99.9%
2. DN link must get 1000Mbps all the time

### `PUMA_RF_STA16` High Load Availability - P2MP
Description: This test checks network availability on a P2MP setup with a load
of 1.2Gbps.

Test Setup: P2MP

Procedure:
1. On the P2MP setup, ignite the network using E2E.
2. Ping over the terra interface to make sure the link is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 10%
3. Ping over the CPE interface to make sure the end-to-end connection is up
    1. Duration : 2 mins
    2. Interval : 0.2 s
    3. Allowed packet loss : 40%
4. Run iPerf between initiator to 8 responder nodes with the following
   characteristics:
    1. 1.2 Gbps
    2. UDP/Bidirectional
    3. Duration of 8 hours minimum

Pass/Fail Criteria:
1. Availability should be 99.9%

## Multi-Hop Setup

### `PUMA_RF_STA9` Low Load Availability - Fig-of-8 (Multi-Hop)
Description: This test checks network availability on a fig-of-8 setup with a
load of 50Mbps.

Test Setup: fig-of-8

Procedure:
1. Bring up the fig-of-8 network using E2E controller.
2. Run iPerf between POP nodes to all nodes with the following characteristics:
    1. 50Mbps (Note: POP links might be hitting capacity)
    2. UDP/Bidirectional
    3. Duration of 24 hours and for 3 days.

Pass/Fail Criteria:
1. Availability should be 99.9%

Note: Need to add tests on measuring availability metrics.

### `PUMA_RF_STA10` Medium Load Availability - Fig-of-8 (Multi-Hop)
Description: This test checks network availability on a fig-of-8 setup with a
load of 100 Mbps.

Test Setup: fig-of-8

Procedure:
1. Bring up the fig-of-8 network using E2E controller.
2. Run iPerf between POP nodes to all nodes with the following characteristics:
    1. 100Mbps (Note: POP links might be hitting capacity)
    2. UDP/Bidirectional
    3. Duration of 24 hours and for 4 days.

Pass/Fail Criteria:
1. Availability should be 99.9%

Note: Need to add tests on measuring availability metrics.

### `PUMA_RF_STA11` Low Load Availability of a LSN network (Fig-of-8 or larger)
Description: This test checks network availability on a RF fig-of-8 (or larger)
setup with a load of 50Mbps.

Test Setup: RF fig-of-8 (preferably larger)

Procedure:
1. Bring up the network using E2E controller.
2. Run iPerf between POP nodes to all nodes with the following characteristics:
    1. 50Mbps (Note: POP links might be hitting capacity)
    2. UDP/Bidirectional
    3. Duration of 24 hours and for 3 days.

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA12` Medium Load Availability of a LSN network (Fig-of-8 or larger)
Description: This test checks network availability on a RF fig-of-8 (or larger)
setup with a load of 50Mbps.

Test Setup: RF fig-of-8 (preferably larger)

Procedure:
1. Bring up the network using E2E controller.
2. Run iPerf between  POP nodes to all nodes with the following characteristics:
    1. 100Mbps (Note: POP links might be hitting capacity)
    2. UDP/Bidirectional
    3. Duration of 24 hours and for 4 days.

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA13` Low Load Availability of a LSN network with scans enabled (Fig-of-8 or larger)
Test Setup: Figure-8 (RF) (preferably with P2MP)

Procedure:
* Bring up network and run 50Mbps traffic from POP node to every node in the
  network
* Enable periodic scans (PBF & IM) through E2E scan APIs
* Run scans for 24 hours
* **Note:** should be run after basic network stability test (`PUMA_RF_STA11`)

Pass/Fail Criteria:
* Confirm periodic scans are running from scan schedule
* Network availability should be greater than 99.9%

### `PUMA_RF_STA14` High Load Availability - Fig-of-8 (Multi-Hop)
Description: This test checks network availability on a fig-of-8 setup with a
load of 1000Mbps.

Test Setup: fig-of-8

Procedure:
1. Bring up the fig-of-8 network.
2. Run iPerf from POP node to another node (5Hop) with the following
   characteristics:
    1. 1000Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours

Pass/Fail Criteria:
1. Availability should be 99.9%

### `PUMA_RF_STA15` Low Load Availability - Fremont Puma Multi-Hop
Description: This test checks network availability on a Fremont Puma Multi-Hop
setup with a load of 50Mbps.

Test Setup: Fremont Puma Multi-Hop

Procedure:
1. Bring up the network.
2. Run iPerf between POP nodes to all nodes with the following characteristics:
    1. 50Mbps
    2. UDP/Bidirectional
    3. Duration of 8 hours

Pass/Fail Criteria:
1. Availability should be 99.9%
