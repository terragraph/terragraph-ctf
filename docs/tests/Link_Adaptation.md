# Link Adaptation Tests

## All Tests

### `PUMA_RF_LA-0.1` UDP Throughput with Fixed MCS VS Link Adaptation
Description: The purpose of this test to ensure that LA's performance is at
least as good as Fixed MCS, given the link SNR yields < 0.1% PER for that MCS.

Test Setup: P2P setup

Procedure:
* Program front/back attenuators with no attenuation.
* Reboot the TGs, the DN and the CN.
* For each MCSx in the set {9, 10, 11, 12}, repeat the following tests:
* On both the DN and CN, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Fix the MCS to MCSx.
    * Disable TPC.
* Associate both DN and CN.
* Program the attenuator to ensure that STF SNR is at least 2dB above the min
  SNR for MCSx (LA-TB-1 only).
* Ping DN → CN and CN → DN to validate connectivity.
* Run iPerf (on the TG) for 10 mins with the following parameters:
    * Push rate TBD
    * Packet size of 1500 bytes.
* Record the throughput on the link in each direction.
* On both the DN and CN, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Enable link adaptation on the link with Max MCS = MCSx picked in the
      earlier step.
    * Disable TPC.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Run iPerf (on the TG) for 10 mins with the following parameters:
    * Push rate TBD
    * Packet size of 1500 bytes
* Record the throughput on the link in each direction.

Pass Criterion:
* The mean UDP throughput with Link Adaptation is within 95% of Fixed MCS
  performance.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.

### `PUMA_RF_LA-0.2` TCP stability with Fixed MCS VS Link Adaptation
Description: The purpose of this test is to ensure that LA maintains good and
stable TCP performance as compared to Fixed MCS.

Test Setup: P2P setup

Procedure:
* Program front/back attenuators with no attenuation.
* Reboot the TGs, the DN and the CN.
* For each MCSx in the set {9, 10, 11, 12}, repeat the following tests:
* On both the DN and CN, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Fix the MCS to MCSx.
    * Disable TPC.
* Associate both DN and CN.
* Program the attenuator to ensure that STF SNR is at least 2dB above the min
  SNR for MCSx (LA-TB-1 only).
* Ping DN → CN and CN → DN to validate connectivity.
* Run iPerf (on the TG) for 10 mins with the following parameters:
    * Push rate TBD
    * Packet size of 1500 bytes
* Record the throughput on the link in each direction.
* On both the DN and CN, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Enable link adaptation on the link with Max MCS = MCSx picked in the
      earlier step.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Run iPerf (on the TG) for 10 mins with the following parameters:
    * Push rate TBD
    * Packet size of 1500 bytes
* Record the throughput on the link in each direction.

Pass/Fail Criterion:
* The mean TCP throughput with Link Adaptation is within 95% of Fixed MCS
  performance.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.

### `PUMA_RF_LA-1.0` Point-to-MultiPoint Link Stability with Link Adaptation
Description: The purpose of this test is to ensure that LA maintains good TCP
performance for both links on a P2MP setup.

Test Setup: P2MP-2 setup

Procedure:
* Program front/back attenuators with no attenuation.
* Reboot the TGs, the DN, CN1 and CN2.
* For each MCSx in the set {9, 10, 12}, repeat the following tests:
* On both the DN, CN1, and CN2, update `/etc/e2e_config/fw_cfg.json` to reflect
  the following:
    * Fix the MCS to MCSx.
    * Disable TPC and set txPowerIndex on both sides to 31 for MCS 9, 27 for MCS
      10 and 25 for MCS12
* Associate both DN and CN1.
* Ping DN → CN1 and CN1 → DN to validate connectivity.
* Associate both DN and CN2.
* Ping DN → CN2 and CN2 → DN to validate connectivity.
* Run iPerf (on the TG) for 10 mins on both links with the following parameters:
    * Push rate limited to 1.25 Gbps (-b 1250m)
    * MTU size of 1500 bytes (since it is TCP iPerf will pick the corresponding
      packet size0
* Record the throughput on the link in each direction.
* On both the DN, CN1, and CN2, Enable link adaptation on the link with Max MCS
  = MCSx picked in the earlier step.
* Re-associate both DN and CN1.
    * Re-associate both DN and CN2.
* Ping DN → CN1 and CN1 → DN to validate connectivity.
* Ping DN → CN2 and CN2 → DN to validate connectivity.
* Run iPerf (on the TG) for 10 mins on both links with the following parameters:
    * Push rate limited to 1.25 Gbps (-b 1250m)
    * MTU size of 1500 bytes (since it is TCP iPerf will pick the corresponding
      packet size0
* Record the throughput on the link in each direction.

Pass/Fail Criteria:
* TCP throughput is stable over both the DN-CN1 and CN-CN2 links, with a
  standard deviation of < 30 Mbps.
* The mean TCP throughput with Link Adaptation is within 95% of Fixed MCS
  performance for both the links.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.

### `PUMA_RF_LA-2.1` Gradually increase/decrease attenuation on a link (ramp test)
Description: The purpose of this test is to insure that LA adaptation picks the
right MCS as the SNR is varied across the link using a programmable attenuator
while running iPerf over the wireless link.

Test Setup: P2P setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN.
* On both the DN and CN1, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Disable TPC.
* Init and Config FW on DN and CN.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Measure STF SNR on the link and compute median link SNR.
* Program attenuation limit for the test (i.e. AttenMax) to ensure STF SNR is
  no less than 5 dB.
* Run iPerf (on the TG) in the background with the following parameters:
    * Push rate TBD
    * Packet size of 1500 bytes
* Every 40 seconds, increase the attenuation by 1dB until you reach AttenMax
* Every 40 seconds, decrease the attenuation by 1dB until attenuation reaches 0.
* Terminate iPerf after going through all attenuations

Pass/Fail Criterion:
* For *MCS_i*, validate that > 90% of the SNR values between [threshold_i,
  threshold_j] have *MCS_i* as the PHY data rate for the link.
* Effective throughput > 90% of expected rate throughout the test.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.

#### Post-Processing Data
* Collect STF SNR values for the CN link.
* Create histogram of SNRs within ranges of *threshold_i*  to *threshold_j*,
  where *threshold_i* is the threshold for *MCS_i* and *threshold_j* is the
  threshold for the next highest *MCS_j*. For example, for MCS 9, *threshold_i*
  = 9 and *threshold_j* = 11.5 (as seen in Table 1 below). The thresholds are
  defined depending on whether the test is undergoing increase or decrease in
  attenuation.

**Table 1:**

| Min Expected SNR (dB) for Ramp Down (Attenuation Increase) | Max Expected SNR (dB) for Ramp up (Attenuation Decrease) | Selected MCS | Effective Data Rate (Mbps) |
| --- | --- | --- | --- |
| 17 | 18 | 12 | 1939 |
| 15 | 16 | 11 | 1616 |
| 13 | 14 | 10 | 1292 |
| 11.5 | 12.5 | 9 | 1050 |
| 9 | 10 | 8 | 969 |
| 7.5 | 8.5 | 7 | 808 |
| 5.5 | 6.5 | 6 | 646 |
| 5 | 6 | 5 | 525 |
| 4.5 | 5.5 | 4 | 485 |
| 3 | 4 | 3 | 404 |
| 2.5 | 3.5 | 2 | 323 |
| 1 | 2 | 1 | 162 |

### `PUMA_RF_LA-2.2` Gradually Increase and Decrease Attenuation on a Point to MultiPoint Setup (Simultaneous Ramp Test)
Description: The purpose of this test is to ensure that Link Adaptation
correctly adapts the MCS on each link for a P2MP setup. Furthermore, LA is able
to ensure that the aggregate throughput on both links is approximately constant.

Test Setup: P2MP-2 setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN.
* On both the DN, CN1, and CN2, update `/etc/e2e_config/fw_cfg.json` to reflect
  the following:
    * Disable TPC.
* Init and Config FW on DN and CN.
* Associate both DN and CN1 and DN and CN2.
* Ping DN → CN1 and CN1 → DN to validate connectivity.
* Ping DN → CN2 and CN2 → DN to validate connectivity.
* Measure STF SNR on the link and compute median link SNR.
* Program attenuation limit for DN-CN1 (i.e. AttenMax) to ensure STF SNR is no
  less than 5 dB.
* Program attenuation for DN-CN2 such that the STF SNR is ~5dB on the link.
* Run iPerf (on the TG) in the background with the following parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 40 seconds, increase the attenuation by 1dB on DN-CN1 and decrease
  attenuation by 1 dB on DN-CN2. Continue until AttenMax is reached on DN-CN1
  and 0 is reached on DN-CN2.
* Every 40 seconds, decrease the attenuation by 1dB on DN-CN1 and increase
  attenuation by 1 dB on DN-CN2. Continue until AttenMax is reached on DN-CN2
  and 0 is reached on DN-CN1.
* Terminate iPerf after going through all attenuations

Pass/Fail Criterion:
* The MCS is correctly chosen, as a function of SNR,  based on the criterion
  discussed in LA-2.0.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.
* The combined throughput from both DN-CN1 and CN-CN2 links is effectively
  constant throughout the run.

### `PUMA_RF_LA-3.1` Point-to-Point Link Survivability with High Attenuation and Traffic
Description: The purpose of this test to ensure that LA quickly adapts the MCS
in response to high attenuation and maintains PER within the acceptable range.
This tests how well outer loop of LA uses PER to quickly adapt the MCS, even if
the true STF SNR on the link hasn't been communicated back to the transmitter
within a BWGD.

Test Setup: P2P setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN.
* On both the DN and CN1, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Disable TPC.
* Init and Config FW on DN and CN.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Run iPerf (on the TG) in the background with the following parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 10 seconds, increase and then immediately decrease attenuation, using
  AttenMax computed in the previous step. Repeat this for 100 iterations.
* Terminate iPerf after going through all iterations

| Test ID  | Min Expected SNR (dB) (greater than) | Expected Final MCS | Max PER due to Attenuation | MAX Time to Reach expected MCS (ms) |
| -------- | --- | - | --------------- | ----- |
| LA-3.1.1 |  10 | 8 | < 1%+Target PER | 102.4 |
| LA-3.1.2 | 6.5 | 6 | < 1%+Target PER | 102.4 |
| LA-3.1.3 | 5.5 | 4 | < 1%+Target PER | 102.4 |

Pass/Fail Criterion:
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.
* LA's convergence time to expected MCS < 4 BWGDs (i.e. 102.4ms).

### `PUMA_RF_LA-3.2` Point-to-Multi-Point Link Survivability with High Attenuation and traffic
Description: The purpose of this test to ensure that LA quickly adapts the MCS
in response to high attenuation and maintains PER within the acceptable range.

Test Setup: P2MP-2 setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CNs.
* On both the DN, CN1 and CN2, update `/etc/e2e_config/fw_cfg.json` to reflect
  the following:
    * Disable TPC.
* Init and Config FW on DN, CN1, and CN2.
* Associate both DN and CN1 and DN and CN2.
* Ping DN → CN1 and CN1 → DN to validate connectivity.
* Ping DN → CN2 and CN2 → DN to validate connectivity.
* Run iPerf (on the TG) between DN → CN2 and DN → CN1 with the following
  parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 10 seconds, increase and then immediately decrease attenuation on
  DN-CN1, similar to how it is done in LA-3.1. Repeat this for 100 iterations.
* Terminate iPerf after going through all iterations.

Pass/Fail Criterion:
* There is no impact to throughput on DN-CN2 due to attenuation on DN-CN1.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.
* LA's convergence time to expected MCS < 4 BWGDs (i.e. 102.4ms).

### `PUMA_RF_LA-3.3` Stability of Link Adaptation to small scale fades
Description: The purpose of this test is to check the hysteresis in Link
Adaptation, by simulating +/- 2 dB fades close to the operational limit of any
given MCS.

Test Setup: P2P setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN.
* For each MCSx in the set {6, 9, 10, 11, 12}, repeat the following tests:
* On both the DN and CN, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Disable TPC.
* Init and Config FW on DN and CN.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Measure STF SNR on the link and compute median link SNR.
* Program the attenuator to ensure that STF SNR is at least 2dB above the min
  SNR for MCSx (see Table 1).
* Run iPerf (on the TG) in the background with the following parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 2 seconds, increase and immediately decrease the attenuation by 1 dB on
  DN-CN and continue this for 100 iterations.
* Terminate iPerf after going through all attenuations

Pass/Fail Criterion:
* LA maintains the MCS and does not oscillate between two MCSes for the +/- 1dB
  attenuations on the DN-CN link.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.

### `PUMA_RF_LA-4.0` Stability of Link Adaptation across the range of SNRs
Description: The purpose of this test is to check whether hysteresis in Link
Adaptation is functioning correctly and prevents oscillations across the entire
operational range of SNR values.

Test Setup: P2P setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN.
* On both the DN and CN1, update `/etc/e2e_config/fw_cfg.json` to reflect the
  following:
    * Disable TPC.
* Init and Config FW on DN and CN1.
* Associate both DN and CN1.
* Ping DN → CN1 and CN1 → DN to validate connectivity.
* Measure STF SNR on the link and compute median link SNR.
* Program attenuation limit for DN-CN1 (i.e. AttenMax) to ensure STF SNR is no
  less than 2 dB.
* Run iPerf (on the TG) in the background with the following parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 60 seconds, increase the attenuation by 0.25 dB on DN-CN1 and continue
  until AttenMax is reached on DN-CN1.
* Every 60 seconds, decrease the attenuation by 0.25 dB on DN-CN1 and continue
  until attenuator value of 0 is reached on the DN-CN1 link.
* Terminate iPerf after going through all attenuations

Pass/Fail Criterion:
* LA does not oscillate between two MCSes for any programmed value for
  attenuation on DN-CN1.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.

### `PUMA_RF_LA-4.1` Point-to-Point Link RAMP TEST for TPC
Description: The purpose of this test to check whether TPC adapts the Tx Power
to maintain the target SNR on the link. Attenuation is adjusted 1 dB / second,
to allow TPC to adapt to the change without causing any PER on the link.

Test Setup: LA-TB-1 setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN1.
* Init and Config FW on DN and CN.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Sample the STF SNR on the link and program attenuator to bring STF SNR to 15
  dB, if it isn't already.
* Sample the Tx Power on the link and record this value (currTxPower).
* Run iPerf (on the TG) in the background with the following parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 30 seconds, increase the attenuation by 0.5 dB and continue to do so for
  2*(MaxPower - currTxPower) steps.
* Terminate iPerf after going through all attenuations

Pass/Fail Criterion:
* TPC maintains the target STF SNR of 15 dB throughout the test.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.
* LA is able to maintain MCS 9 the test.

### `PUMA_RF_LA-4.2` Point-to-Point Link high attenuation TEST for TPC
Description: This test is intended to assess TPC's ability to handle foliage
related impairments on the link and adjusting Transmit Power to account for deep
fades introduced on the link.

Test Setup: P2P setup

Procedure:
* Program attenuator with 0 dB attenuation.
* Reboot both TGs, the DN and the CN.
* Init and Config FW on DN and CN.
* Associate both DN and CN.
* Ping DN → CN and CN → DN to validate connectivity.
* Sample the Tx Power on the link and record this value (currTxPower).
* Run iPerf (on the TG) in the background with the following parameters:
    * 2 Gbps of UDP traffic (bi-directional)
    * Packet size of 1500 bytes
* Every 60 seconds, increase and then immediately decrease attenuation for a
  total of 3-10 iterations (picked uniformly at random), using the attenuation
  values in the range [0, MaxPower - currTxPower]. Repeat this for 30
  iterations.
* Terminate iPerf after going through all iterations

Pass/Fail Criterion:
* TPC adapts to using high TX Power in response to first attenuation sequence
  and maintains that for the rest of the test run.
* Long term PER < Target PER throughout the run.
* Short term PER < 1%+Target PER throughout the run.
