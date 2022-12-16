# Y-Street Tests

## Basic Tests

### `PUMA_RF_Y.D.D.1.0` Ignition Test
Description: Test Y-street ignition in different scenarios as mentioned below.

Test Setup: P2MP setup

Procedure:
1. Ignite the links in the following order:
    1. DN1 is the initiator and DN2 is the responder.
    2. DN1 is the initiator and DN3 is the responder.
    3. Ping over the loopback interface (lo) to verify links DN1-DN2 & DN1-DN3
       are up.
2. Ignite the links in the following order:
    1. DN2 is the initiator and DN1 is the responder.
    2. DN1 is the initiator and DN3 is the responder.
    3. Ping over the loopback interface (lo) to verify links DN1-DN2 & DN1-DN3
       are up.
3. Ignite the links in the following order:
    1. DN2 is the initiator and DN1 is the responder.
    2. DN3 is the initiator and DN1 is the responder.
    3. Ping over the loopback interface (lo) to verify links DN1-DN2 & DN1-DN3
       are up.

Repeat the above test steps with traffic running on the already ignited link.
Specifically, when a link is ignited, run UDP iPerf traffic at 1Gbps between
traffic generators (DN0, DN4, and/or DN5), before igniting the next link in the
sequence for a test. Verify that at least 900 Mbps is sustained before and after
the second link ignition. Allow for a short drop in throughput during the second
ignition.

Passing:
1. No failed assocs
2. No failed pings
3. No failed disassocs

### `PUMA_RF_Y.D.D.2.0` Single Link Test
Description: Y-street ignition with traffic on only one link

Test Setup: P2MP setup

Procedure:
1. Ignite the links in the following order: DN1-DN2, DN1-DN3.
2. Run traffic between DN0 and DN4, UDP and TCP, unidirectional in each
   direction and bidirectional (6 subtests total):
    1. Unidirectional:
        1. UDP: Offer 892 Mbps, pass with 95% of offered
        2. TCP: Rate-limit to 1000 Mbps, pass with 830 Mbps
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: (same as unidirectional)
        2. TCP: (same as unidirectional)
        3. Conditional pass = 90% of these thresholds.
3. Repeat for link DN0→DN5 (another 6 subtests).

Passing:
1. No failed assocs
2. No failed pings
3. No failed disassocs
4. iPerf throughput pass criteria as mentioned above

### `PUMA_RF_Y.D.D.3.0` Dual Link Test
Description: Y-street ignition with traffic on both links

Test Setup: P2MP setup

Procedure:
1. Ignite the links in the following order: DN1-DN2, DN1-DN3.
2. Send traffic simultaneously between DN0 and DN5 and between DN0 and DN4, UDP
   and TCP, unidirectional in each direction and bidirectional (6 subtests
   total):
    1. Unidirectional:
        1. UDP: Offer 461 Mbps, pass with 95% of offered (each)
        2. TCP: Rate-limit to 500 Mbps, pass with 430 Mbps (each)
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: (same as unidirectional)
        2. TCP: (same as unidirectional)
        3. Conditional pass = 90% of these thresholds.

Passing:
1. No failed assocs
2. No failed pings
3. No failed disassocs
4. iPerf throughput pass criteria as mentioned above

### `PUMA_RF_Y.D.D.4.0` Child DN to child DN Test
Description: Y-street ignition with traffic between child DNs

Test Setup: P2MP setup

Procedure:
1. Ignite the links in the following order: DN1-DN2, DN1-DN3.
2. Send traffic between DN4 and DN5, UDP and TCP, unidirectional in each
   direction and bidirectional (6 subtests total):
    1. Unidirectional:
        1. UDP: Offer 892 Mbps, pass with 95% of offered
        2. TCP: Rate-limit to 1000 Mbps, pass with 830 Mbps
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: Offer 461 Mbps, pass with 95% of offered
        2. TCP: Rate-limit to 500 Mbps, pass with 430 Mbps
        3. Conditional pass = 90% of these thresholds.

Passing:
1. No failed assocs
2. No failed pings
3. No failed disassocs
4. iPerf throughput pass criteria as mentioned above

### `PUMA_RF_Y.D.D.4.1` Child DN to child DN Test using parallel TCP STreams
Description: Y-street ignition with traffic between child DNs

Test Setup: P2MP setup

Procedure:
* Same traffic profile and same pass thresholds as `Y.D.D.4.0`, but for TCP
  traffic use 3 parallel TCP streams instead of 1. Each configured TCP stream
  shall have 1/3 the offered traffic, and the pass threshold shall apply to the
  aggregate (i.e. sum) of the flows in each direction.

Notes:
1. Fairness (i.e. approximately equal throughput) between the parallel TCP flows
   is not required to pass this test.
2. The pass criteria here cannot be easily automated with our existing test
   infrastructure (specifically, we cannot currently apply an aggregate
   throughput pass criteria).

Passing:
1. No failed assocs
2. No failed pings
3. No failed disassocs
4. iPerf throughput pass criteria as mentioned above

## DN to CN tests
For these tests, ignite the following links in order: DN1-DN2, DN1-DN3, DN1-CN3,
DN2-CN1, DN3-CN2.

### I. DN0 as root sector (i.e. closest to PoP)
1. `PUMA_RF_Y.C.D.C-1.0`: Traffic between DN0 and either CN1 or CN2 (not in
   parallel), UDP and TCP, unidirectional in each direction and bidirectional
   (12 subtests total):
    1. Unidirectional:
        1. UDP: Offer 862 Mbps, pass with 95% of offered
        2. TCP: Rate-limit to 1000 Mbps, pass with 802.5 Mbps
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: Offer 431 Mbps, pass with 95% of offered
        2. TCP: Rate-limit to 500 Mbps, pass with 401 Mbps
        3. Conditional pass = 90% of these thresholds.
2. `PUMA_RF_Y.C.D.C-1.2`: Traffic from DN0 to CN1 and CN2:
    1. Unidirectional:
        1. UDP: Offer 461 Mbps, pass with 95% of offered (each)
        2. TCP: Rate-limit to 500 Mbps, pass with 429 Mbps (each)
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: (same as unidirectional)
        2. TCP: (same as unidirectional)
        3. Conditional pass = 90% of these thresholds.
3. `PUMA_RF_Y.C.D.C-1.5`: Traffic between DN0 and CN1, CN2, and CN3:
    1. Send 300 Mbps uni-directional UDP traffic from DN0 to CN1 & DN0 to CN2 &
       DN0 to CN3 (each — 3 parallel flows) and validate you get at least 95% of
       offered traffic (each).
    2. Same as above except with traffic run in the reverse direction.
    3. Same as above except with bi-directional traffic on all links (total of 6
       parallel flows, 3 in each direction).
    4. Repeat all 3 above steps with TCP traffic, rate-limited to 325 Mbps and
       passing with 279 Mbps (each).

### II. DN4 as root sector (i.e. closest to PoP)
1. `PUMA_RF_Y.C.D.C-2.3`: Traffic between DN4 and CN1 and CN2 (2 paths with
   traffic flowing simultaneously), UDP and TCP, unidirectional in both
   directions and bidirectional (6 subtests total):
    1. Unidirectional in parallel:
        1. UDP: Offer 431 Mbps, pass with 95% of offered (each)
        2. TCP: Rate-limit to 500 Mbps, pass with 401 Mbps (each)
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: (same as unidirectional)
        2. TCP: (same as unidirectional)
        3. Conditional pass = 90% of these thresholds.
2. `PUMA_RF_Y.C.D.C-2.4`: Traffic between DN4 and CN2 and CN3 (2 paths with
   traffic flowing simultaneously), UDP and TCP, unidirectional in both
   directions and bidirectional (6 subtests total):
    1. Unidirectional in parallel:
        1. UDP: Offer 446 Mbps, pass with 95% of offered (each)
        2. TCP: Rate-limit to 500 Mbps, pass with 415 Mbps (each)
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional:
        1. UDP: Offer 223 Mbps, pass with 95% of offered (each)
        2. TCP: Rate-limit to 250 Mbps, pass with 208 Mbps (each)
        3. Conditional pass = 90% of these thresholds.
3. `PUMA_RF_Y.C.D.C-2.6`: Traffic in parallel between DN4 and CN1, CN2, and CN3
   (3 paths with traffic flowing simultaneously), UDP and TCP, unidirectional in
   both directions and bidirectional (6 subtests total):
    1. Unidirectional in parallel:
        1. UDP:
            1. Offer 446 Mbps, pass with 95% of offered for DN4 → CN1
            2. Offer 223 Mbps, pass with 95% of offered for DN4 → CN2 and
               DN4 → CN3 (each)
        2. TCP:
            1. Rate-limit to 500 Mbps, pass with 415 Mbps for DN4 → CN1
            2. Rate-limit to 250 Mbps, pass with 208 Mbps for DN4 → CN2 and
               DN4 → CN3 (each)
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional in parallel:
        1. UDP and TCP (same as unidirectional):
        2. Conditional pass = 90% of these thresholds.

### III. DN4 and DN5 both as root sectors (Multi-Homing)
1. `PUMA_RF_Y.C.D.C-3.1`: Simultaneous traffic between DN4 and CN1 & CN3, AND
   traffic between DN5 and CN2 & CN3 (4 paths with traffic flowing
   simultaneously), UDP and TCP, unidirectional in both directions and
   bidirectional (6 subtests total):
    1. Unidirectional in parallel:
        1. UDP:
            1. Offer 416 Mbps, pass with 95% of offered for DN4 → CN3 and DN5 →
               CN3 (each)
            2. Offer 485 Mbps, pass with 95% of offered for DN4 → CN1 and DN5 →
               CN2 (each)
        2. TCP:
            1. Rate-limit to 500 Mbps, pass with 388 Mbps for DN4 → CN3 and
               DN5 → CN3 (each)
            2. Rate-limit to 500 Mbps, pass with 451 Mbps for DN4 → CN1 and
               DN5 → CN2 (each)
        3. Conditional pass = 90% of these thresholds.
    2. Bidirectional in parallel:
        1. UDP:
            1. Offer 208 Mbps, pass with 95% of offered for DN4 ↔ CN3 and DN5 ↔
               CN3 (each, in both directions)
            2. Offer 243 Mbps, pass with 95% of offered for DN4 ↔ CN1 and DN5 ↔
               CN2 (each, in both directions)
        2. TCP:
            1. Rate-limit to 300 Mbps, pass with 193 Mbps for DN4 → CN3 and
               DN5 → CN3 (each)
            2. Rate-limit to 300 Mbps, pass with 226 Mbps for DN4 → CN1 and
               DN5 → CN2 (each)
        3. Conditional pass = 90% of these thresholds.

### IV. Independent DN sectors (canonical case)
1. `PUMA_RF_Y.C.D.C-4.0`:
    1. In parallel (i.e. simultaneously), send unidirectional UDP traffic:
        1. From DN0 to CN3: Offer 832 Mbps, pass with 95% of offered.
        2. From DN4 to CN1: Offer 892 Mbps, pass with 95% of offered.
        3. From DN5 to CN2: Offer 892 Mbps, pass with 95% of offered.
    2. Conditional pass = 90% of these thresholds.
