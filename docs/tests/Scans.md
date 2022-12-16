# Scan Tests

## PBF/IM

### `PUMA_PBF.RF.T08` DN0 to DN1:: UDP traffic:: Measurement :: Apply
Procedure:
1. DN0 is the initiator and DN1 is the responder
2. Verify that ignition met the pass criteria if not we need to debug the link
3. Start the bidirectional UDP traffic on the link
4. Verify that link with traffic met the pass criteria if not we need to debug
   the link
5. Issue the PBF command from DN0 to DN1 → What is the "Issue PBF Command?"
    * tg minion fine relative ??
    * manual and automated schedule from E2E?
6. Apply PBF recommendation for new Tx and Rx beam selection
7. Capture PBF results and produce the heat-map for packet index {0} and {1}
   based on SNR and RSSI
8. Capture link quality metrics before and after applying PBF recommendations
9. Repeat steps 5 to 8 in reverse direction from DN1 to DN0
10. Evaluate the data against pass criteria
11. Repeat the test 5 times to ensure repeatability

Pass/Fail Criteria:
* Heat-map with the main cluster around the center and proper sinc pattern
* Highly correlated results for packet index {0} and packet index {1}
    * ~identical heat-maps
    * ~identical number of received measurement packets
* No impact on link quality metrics (PER, SNR, ...) except 60% throughput loss
  during PBF procedure.
* Better or equal link quality metrics after applying the new beams.

### `PUMA_PBF.RF.T11` DN0 to DN1:: UDP traffic:: Measurement :: Apply:: Hybrid
Procedure:
* Same instructions as `PBF.RF.T08` on SW HYBRID link

### `PUMA_PBF.RF.T13` DN0 to DN1:: +30-degree azimuth rotation
Procedure:
* Start with broadside link
* Modify the setup by physically rotating one of the sectors in azimuth plane
  (+30 degree)
* Verify that physical rotation has been correctly captured by repeating
  `PUMA_PBF.RF.T08` test

### `PUMA_PBF.RF.T14` DN0 to DN1:: -30-degree azimuth rotation
Procedure:
* Start with broadside link
* Modify the setup by physically rotating one of the sectors in azimuth plane
  (-30 degree)
* Verify that physical rotation has been correctly captured by repeating
  `PUMA_PBF.RF.T08` test

### `PUMA_PBF.RF.T15` DN0 to CN0:: All
Procedure:
* Repeat all `PBF.RF` tests by configuring one side of the link as a CN sector.

### `PUMA_PBF.RF.T16` P2MP topology
Procedure:
* Borrow P2MP setup from LLS test plan (`LLS-1.1`)
* Identify the broadside link or modify the setup to create one broadside link
* Ignite the topology (Please refer to LLS test plan section `LLS-1.1`)
* Repeat `RF.T08`, `RF.T09` tests on broadside link
    * PUMA_Follow the suggested traffic profile in each test for the entire
      topology
    * Follow the topology spec to identify each sector as DN or CN and ignore
      the test specification
* Link quality metrics of the entire topology should remain intact after
  executing each test
    * Zero link down due to executing the test
    * No impact on critical link metrics like SNR, PER, Throughput, etc.

### `PUMA_PBF.RF.T17` Butterfly topology
Procedure:
* Borrow butterfly setup from LLS test plan (`LLS-3.1`)
* Identify the broadside link or modify the setup to create one broadside link
* Ignite the topology (Please refer to LLS test plan section `LLS-3.1`)
* Repeat `RF.T01`, `RF.T02`, `RF.T03`, `RF.T07`, `RF.T08`, `RF.T09` tests on
  broadside link
    * Follow the suggested traffic profile in each test for the entire topology
    * Follow the topology spec to identify each sector as DN or CN and ignore
      the test specification
* Link quality metrics of the entire topology should remain intact after
  executing each test
    * Zero link down due to executing the test
    * No impact on critical link metrics like SNR, PER, Throughput, etc.

### `PUMA_PBF.RF.T18` Y-street topology
Procedure:
* Borrow Y-street setup from Y-street test plan.
* Identify the broadside link or modify the setup to create one broadside link
* Ignite the topology (Please refer to Y-street test plan section `Y.C.D.D-1.x`)
* Repeat `RF.T01`, `RF.T02`, `RF.T03`, `RF.T07`, `RF.T08`, `RF.T09` tests on
  broadside link
    * Follow the suggested traffic profile in each test for the entire topology
    * Follow the topology spec to identify each sector as DN or CN and ignore
      the test specification
* Link quality metrics of the entire topology should remain intact after
  executing each test
    * Zero link down due to executing the test
    * No impact on critical link metrics like SNR, PER, Throughput, etc.

### `PUMA_IM.RF.Txx` All:: PBF:: Broadcast MAC address
Procedure:
* Repeat all tests in IM mode with broadcast MAC address but limit to test case
  `PBF.RF.T01` through `PBF.RF.T06` as we are not applying the results in IM
  mode and it is measurement only. Tests `PBF.RFT16-18` should also be run in
  the context of IM, since they excite P2MP topologies for this feature.

## RTCAL

### `PUMA_RF_RTCAL.RF.T08` DN0 to DN1:: UDP traffic:: Measurement ::Apply:: Top Panel
Procedure:
1. DN0 is the initiator and DN1 is the responder
2. Verify that ignition met the pass criteria if not we need to debug the link
3. Start the bidirectional UDP traffic on the link
4. Verify that link with traffic met the pass criteria if not we need to debug
   the link
5. Issue the RTCAL command from DN0 (CAL Tx) to DN1
6. Capture RTCAL results for packet index {0} and {1}
7. Repeat steps 5 & 6 in reverse direction from DN1 to DN0
8. Issue the RTCAL command from DN0 to DN1(CAL RX)
9. Capture RTCAL results for packet index {0} and {1}
10. Repeat steps 8 & 9 in reverse direction from DN1 to DN0
11. Apply newly calibrated arrays
12. Capture link quality metrics before and after applying RTCAL updates
13. Evaluate the data against pass criteria
14. Repeat the test 5 times to ensure repeatability

Pass/Fail Criteria:
* Negligible packet loss for packet index {0}
* Negligible packet loss for packet index {1}
* Uniform SNR and RSSI distribution with +/- 5db of the nominal link SNR and
  RSSI
* Verify correct indices on each side of the link based on the RTCAL
  specification
* No impact on link quality metrics (PER, SNR, ...) except 60% throughput loss
  during RTCAL procedure.
* Better or equal link quality metrics after calibrating the beams

### `PUMA_RF_RTCAL.RF.T11` DN0 to DN1:: UDP traffic:: Measurement ::Apply:: Hybrid:: Top Panel
Procedure:
* Same instructions as `RTCAL.RF.T08` on SW HYBRID link

### `PUMA_RF_RTCAL.RF.T17` P2MP Topology
Procedure:
* Borrow P2MP setup from LLS test plan (`LLS-1.1`)
* Identify the broadside link or modify the setup to create one broadside link
* Ignite the topology (Please refer to LLS test plan section `LLS-1.1`)
* Repeat `RF.T01`, `RF.T02`, `RF.T03`, `RF.T07`, `RF.T08`, `RF.T09` tests on
  broadside link
    * Follow the suggested traffic profile in each test for the entire topology
    * Follow the topology spec to identify each sector as DN or CN and ignore
      the test specification
* Link quality metrics of the entire topology should remain intact after
  executing each test
    * Zero link down due to executing the test
    * No impact on critical link metrics like SNR, PER, Throughput, etc.

## Interference Nulling (CBF)

### `CBF-1.4` Max Distance Link
Procedure:
* RX CBF with 300 m victim link and 30 m aggressor link (functional test for
  victim TX delay)
    * Verify VRX packet 0 SINR (with interference) <= VRX packet 1 SINR (no
      interference) for all beams (if victim packets arrive first SINR may be
      higher for packets with interference than those without interference)

### `CBF-1.6` Stats
Procedure:
* Verify scan stats can be enabled/disabled from controller
* Verify when scan stats enabled scan counters updated correctly (`numOfScan`,
  `numOfImScan`, etc.)
    * Currently no stats for RTCAL and CBF beam in use

### `CBF-2.2` Y-street
Procedure:
* RX CBF and TX CBF with Y-street links

### `CBF-3.2` Force link down during scan procedure
Procedure:
* Verify link up still functional
* After link up completes, verify scan procedures (system still in good state)

### `CBF-3.4` With continuous pings throughout scan verify no timeouts before, during, and after scan
Details TBD

### `CBF-4.1` Performance validation
Procedure:
* Execute RX CBF and TX CBF for nominal V topology with main lobes close to
  boresight and interference <20 degrees
    * Verify >5 dB suppression achieved for direct sidelobe interference

### `CBF-4.2` Small-scale performance quantification
Procedure:
* Quantify RX CBF and TX CBF interference suppression across interference angle
  (main lobe close to boresight)
* Quantify RX CBF and TX CBF interference suppression across main lobe angle
  (fixed interference angle relative main lobe)
* Quantify RX CBF performance with 2 or more aggressor links
* Quantify TX CBF performance with 2 or more victim link
