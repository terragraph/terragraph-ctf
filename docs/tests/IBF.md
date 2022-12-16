# IBF Tests
All IBF tests should be run with the E2E controller.

## P2P
Note: Auto PBF after IBF available in M37+. Heat map data is based on IBF.

### `PUMA_RF_IBF-P2P-1` DN-DN Assocication
Description: P2P heat map test (DN to DN) on long link.

Procedure:
1. Enable BF stats using `r2d2` command on both nodes.
2. Associate DN-I ↔ DN-R.
3. Record the phyPeriodic.txBeam used each time.
4. Delay of 30 seconds and send 50 (TBR) pings once a second (TBR).
5. Disassociate DN-I ↔ DN-R link.
6. Repeat 50 times.
7. Measure phystatus.srssi and LQM in each iteration.

Passing:
1. No failed assocs, pings, disassocs.
2. Figure out the max and verify that beam indices pick the max LQM.
3. Note: 5-6 sec difference is acceptable verifying the beam indices and the max
   LQM.

### `PUMA_RF_IBF-P2P-2` DN-DN Assocication
Description: P2P heat map test (DN to DN) on short link.

Procedure:
1. Enable BF stats using `r2d2` command on both nodes.
2. Associate DN-I ↔ DN-R.
3. Record the phyPeriodic.txBeam used each time.
4. Delay of 30 seconds and send 50 (TBR) pings once a second (TBR)
5. Disassociate DN-I ↔ DN-R link.

Passing:
1. No failed assocs, pings, disassocs.
2. Same beams must be selected every time.

### `PUMA_RF_IBF-P2P-3` Bring up link E2E with different attenuation levels
Description: Ignite P2P link in coffin setup multiple times and verify link
comes up with same beams.

Procedure:
1. Enable BF stats on both nodes.
2. Set xdB attenuation on the link (where x is enough to not bring the link up).
3. Ignite P2P link in coffin.
4. Reset attenuation back to 0dB.
5. Delay of 30 seconds and send 50 (TBR) pings once a second (TBR).
6. Repeat 10 times.
7. Plot the phystatus.srssi in each iteration.
8. Measure LQM in each iteration.

Passing:
1. Verify that the E2E controller attempts to ignite the P2P link when
   attenuation is high till the command times out.
2. Verify LQM diff is no more than +/-1 between each iteration.

### `PUMA_RF_IBF-P2P-4` Bring up link using E2E with high attenuation
Description: Ignite P2P link in coffin setup with high attenuation and verify
ignition succeeds with 0dB attenuation.

Procedure:
1. Enable BF stats on both nodes.
2. Set xdB attenuation on the link (where x is enough to not bring the link up).
3. Ignite P2P link in coffin.
4. Reset attenuation back to 0dB.
5. Delay of 30 seconds and send 50 (TBR) pings once a second (TBR).
6. Repeat 5 times.
7. Plot the phystatus.srssi in each iteration.
8. Measure LQM in each iteration.

Passing:
1. Verify that the E2E controller attempts to ignite the P2P link when
   attenuation is high till the command times out.
2. Verify LQM diff is no more than +/-1 between each iteration.

### `PUMA_RF_IBF-P2P-5` Bring up link using E2E with low attenuation
Description: Ignite P2P link in coffin setup with 0dB attenuation and verify
ignition fails with high attenuation.

Procedure:
1. Enable BF stats on both nodes.
2. Set 0dB attenuation on the link.
3. Ignite P2P link in coffin.
4. Delay of 30 seconds and send 50 (TBR) pings once a second (TBR).
5. Set attenuation to high value.
6. Repeat 5 times.
7. Plot the phystatus.srssi in each iteration.
8. Measure LQM in each iteration.

Passing:
1. Verify that the E2E controller attempts to ignite the P2P link when
   attenuation is high till the command times out.
2. Verify LQM diff is no more than +/-1 between each iteration.

### `PUMA_RF_IBF-P2P-6` Off-boresight beam selection
Description: Ignite a P2P link that is off-boresight and check beam.

Procedure:
1. Enable BF stats on both nodes.
2. Associate the P2P link.
3. Delay of 30 seconds and send 50 (TBR) pings once a second (TBR).
4. Repeat 5 times.
5. Plot the phystatus.srssi in each iteration.
6. Measure LQM in each iteration.

Passing:
1. Verify that the beam idx picked each time correlates with the actual angle
   between the nodes.
2. Verify LQM diff is no more than +/-1 between each iteration.
