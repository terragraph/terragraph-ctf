# WSEC (WPA-PSK) Tests
The WSEC tests validate Over-The-Air Security with WPA-PSK.

## Base Feature Validation
It's important to run through some negative tests, to ensure that the state
machine for the security feature is properly exercised and works as expected in
all such conditions. We've determined the following negative tests for feature
validation:
* Pass-phrase mismatch on opposite ends of the link
* Termination of `hostapd`/`wpa_supplicant`

### `WSEC-0-1` Pass-phrase mismatch
Description: For the aforementioned negative tests, we plan to use two P2P
scenarios (DN-CN and DN-DN). The test details for each of the above negative
tests are listed below.

Procedure and validation: For each P2P scenario (DN-DN and DN-CN), do the
following:
1. On the initiator DN, edit wpa_passphrase field in
   `/etc/hostapd/hostapd_terra0.conf` from "psk_test" to "psk2_test".
2. Follow the steps in WSEC-1 and validate that link-up fails.
3. Revert step 1, i.e. restore wpa_passphrase field to "psk_test".
4. Validate that the link-up succeeds.
5. Reboot all the nodes.
6. On the responder DN/CN, edit psk field in
   `/etc/wpa_supplicant/wpa_supplicant_terra0.conf` from "psk_test" to
   "psk2_test".
7. Follow the steps in WSEC-1 and validate that link-up fails.
8. Revert step 6, i.e. restore psk field to "psk_test".
9. Validate that the link-up succeeds.

## Ignition Test Cases

### `WSEC-1` 1DN+7CN Association (SAME Passphrase on all links)
Procedure:
* Ignite the network for this topology, using the appropriate topology file.
* Ping each link using link local and verify it has come up.
* Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces
  from traffic generators.
* Execute the following E2E commands:
    1. `tg config modify network -i "radioParamsBase.fwParams.wsecEnable" 1`
    2. Output of the security application is redirected. Please check files like
       `/tmp/hostapd_terra0` and `/tmp/wpa_supplicant_terra0`.
* Ping each link using link local and verify it has come up.
* Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces
  from traffic generators.

Validation:
* All Associations succeed.
* Ping success
* No packet loss.
* In all case, iPerf throughput of 100Mbps is achieved on each link

### `WSEC-2` 1DN+6CN+1DN Association
Procedure:
* Same as `WSEC-1`, but assign DN role in topology file to one of the 7 peers.

### `WSEC-3` 1DN+5CN+2DN Association
Procedure:
* Same as `WSEC-1`, but assign DN role in topology file to two of the 7 peers.

### `WSEC-4` 1DN+5CN+2DN Association (Reverse Polarity, Reverse disassoc)
Procedure:
* Same as `WSEC-3`, but use flip the polarity on each sector.

### `WSEC-5` Reassoc Stress Test
Procedure:
* Randomly select a peer
* Toggle linkup state between initiator and peer, using attenuator cabled to the
  link.
* After linkup, ping the peer.
* Repeat these steps 50 times.

Validation:
* No crashes.
* All pings succeed.

### `WSEC-6` Bring-up RF Butterfly
Test Setup: Butterfly test setup

Procedure:
* Ignite the network for this topology, using the appropriate topology file.
* Ping each link using link local and verify it has come up.
* Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces
  from traffic generators.
* Execute the following E2E commands:
    1. `tg config modify network -i "radioParamsBase.fwParams.wsecEnable" 1`
    2. Output of the security application is redirected. Please check files like
       `/tmp/hostapd_terra0` and `/tmp/wpa_supplicant_terra0`.
* Ping each link using link local and verify it has come up.
* Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces
  from traffic generators.

Validation:
* All Associations succeed.
* Ping success
* No packet loss.
* iPerf throughput of 100Mbps is achieved on each link.
* Disassociation success.

## Throughput Test Cases
Description: These test cases are purposed to evaluate the performance impact of
enabling OTA security in topological scenarios.

| Test ID | Topology  | Packet Size (bytes) | UDP Push Rate (Mbps) - laMaxMcs = 9 | UDP Expected Throughput (Mbps) | UDP Push Rate (Mbps) - laMaxMcs = 12 | UDP Expected Throughput (Mbps) |
| --- | --- | --- | --- | --- | --- | --- |
| WSEC-12 | Butterfly (2DNs, 2 CNs per DN) | 5602(MCS9)/ 5469(MCS12) | 900(serial)/ 320(parallel) | 891.90(serial)/ 302.59(parallel) | 900(serial)/ 320(parallel) | 891.90(serial)/ 302.59(parallel) |
| WSEC-13 | Y-street (3 DNs only) | 5602(MCS9)/ 5469(MCS12) | 900(serial)/ 450(parallel) | 891.90(serial)/ 441(parallel) | 1420(serial)/ 770(parallel) | 1405.84(serial)/ 765.16(parallel) |
| WSEC-14 | Figure of U | 5602(MCS9)/ 5469(MCS12) | 1050 | 1000 | 1650 | 1610 |

**Note:** Due to setup limitations/availability, throughput numbers might have
to be adjusted.

Procedure:
* Ignite topology for the test ID shown in the table above.
* Ping each link using link local.
* Send iPerf UDP traffic serially on each link from traffic generators, using
  the push rate provided in the table above.
* Send iPerf UDP traffic simultaneously on all links from traffic generators (if
  applicable), using the push rate provided in the table above.

Validation:
* All Associations succeed for the ignited topology.
* Ping success on all links.
* iPerf throughput is within 95% expected throughput, as shown in the table
  above.
