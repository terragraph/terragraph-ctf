# SW Hybrid Tests

## DN-Only Tests
These tests are performed using E2E controller (ARM or x86 depending on
availability).

### `PUMA_RF_SHT-1.0` Single DN-to-DN link
Description: P2P association according to polarities shown in the table below:

| Test ID  | DN1 Polarity | DN2 Polarity | laMaxMcs |
|----------|--------------|--------------|----------|
| SHT-1.1  | ODD          | HYBRID_EVEN  | 12       |
| SHT-1.2  | EVEN         | HYBRID_ODD   | 12       |
| SHT-1.5  | HYBRID_EVEN  | ODD          | 12       |
| SHT-1.6  | HYBRID_ODD   | EVEN         | 12       |
| SHT-1.11 | ODD          | HYBRID_EVEN  | 9        |
| SHT-1.12 | EVEN         | HYBRID_ODD   | 9        |
| SHT-1.15 | HYBRID_EVEN  | ODD          | 9        |
| SHT-1.16 | HYBRID_ODD   | EVEN         | 9        |

Test Setup: P2P setup

Procedure:
* Associate DN1 and DN2, with DN1 as the initiator.
* Ping on link using link local from DN1 → DN2, and vice versa.
* Send bidirectional iPerf traffic using traffic generators.
* Dissociate from DN1.

Passing:
* All Associations succeed within 2 attempts.
* Performance is as expected, as shown in the table above.
* The slot map is 50:50 on the Hybrid DN sector.
* Ping success.
* Disassociation success.

## DN-CN Tests
These tests are done using E2E controller (ARM or x86 depending on
availability).

### `PUMA_RF_SHT-2.0` DN-to-CN (P2MP)
Description: For these tests all three CNs are associated but traffic is only
transmitted to the number of CNs givin in the "Number of CNs" column. For the
case of traffic being transmitted to multiple CNs each CN is given equal
bandwidth as shown in table below:

| Test ID | DN Polarity | Number of CNs |
|---------|-------------|---------------|
| SHT-2.1 | HYBRID_EVEN | 1             |
| SHT-2.2 | HYBRID_EVEN | 2             |
| SHT-2.3 | HYBRID_EVEN | 3             |
| SHT-2.4 | HYBRID_EVEN | 1             |
| SHT-2.5 | HYBRID_EVEN | 2             |
| SHT-2.6 | HYBRID_EVEN | 3             |

Test Setup: P2MP setup

Procedure:
* Associate all CNs to the DN, based on the test ID in the table above.
* Ping on link using link local in both directions serially to each CN.
* Send bidirectional iPerf traffic to all CNs from traffic generators.
* Dissociate each CN one-by-one.

Passing:
* All assocs should succeed within 2 attempts
* Performance is as expected, as shown in the Table above
* The slot map is 50:50 on the Hybrid DN sector
* All pings should pass
* All disassocs should succeed

### `PUMA_RF_SHT-3.0` DN-to-DN+CNs
Description: For this test no matter how many CNs receive/transmitt traffic all
are associated. In this case the DN to DN link has laMaxMcs set to 12 while the
DN to CN links has laMaxMcs set to 9. We consider two different cases: in the
first the DN ↔ DN link is given 75% of the slots and the DN ↔ CNs link share
20%. In the second case the DN ↔ DN link is given 20% of the slots and the DN ↔
CNs link share 75%. In these tests all CNs split the available BW equally as
shown in table below:

| Test ID  | DN1 Polarity | DN2 Polarity | Number of Transmitting CNs on DN1 | DN/CN bandwidth allocation                               |
|----------|--------------|--------------|-----------------------------------|----------------------------------------------------------|
| SHT-3.1  | EVEN         | HYBRID_ODD   | 1                                 | 75/20                                                    |
| SHT-3.2  | EVEN         | HYBRID_ODD   | 2                                 | 75/20                                                    |
| SHT-3.3  | EVEN         | HYBRID_ODD   | 3                                 | 75/20                                                    |
| SHT-3.4  | ODD          | HYBRID_EVEN  | 1                                 | 75/20                                                    |
| SHT-3.5  | ODD          | HYBRID_EVEN  | 2                                 | 75/20                                                    |
| SHT-3.6  | ODD          | HYBRID_EVEN  | 3                                 | 75/20                                                    |
| SHT-3.7  | HYBRID_ODD   | EVEN         | 1                                 | 75/20                                                    |
| SHT-3.8  | HYBRID_ODD   | EVEN         | 2                                 | 75/20                                                    |
| SHT-3.9  | HYBRID_ODD   | EVEN         | 3                                 | 75/20                                                    |
| SHT-3.10 | HYBRID_EVEN  | ODD          | 1                                 | 75/20                                                    |
| SHT-3.11 | HYBRID_EVEN  | ODD          | 2                                 | 75/20                                                    |
| SHT-3.12 | HYBRID_EVEN  | ODD          | 3                                 | 75/20                                                    |
| SHT-3.21 | EVEN         | HYBRID_ODD   | 1                                 | 20/75                                                    |
| SHT-3.22 | EVEN         | HYBRID_ODD   | 2                                 | 20/75                                                    |
| SHT-3.23 | EVEN         | HYBRID_ODD   | 3 (DUT5, DUT4, & DUT7)            | 20/75                                                    |
| SHT-3.24 | ODD          | HYBRID_EVEN  | 1 (DUT4)                          | 20/75                                                    |
| SHT-3.25 | ODD          | HYBRID_EVEN  | 2 (DUT5 & DUT4)                   | 20/75                                                    |
| SHT-3.26 | ODD          | HYBRID_EVEN  | 3 (DUT5, DUT4, & DUT7)            | 20/75                                                    |
| SHT-3.27 | HYBRID_ODD   | EVEN         | 1 (DUT4)                          | 20/75                                                    |
| SHT-3.28 | HYBRID_ODD   | EVEN         | 2 (DUT5 & DUT4)                   | 20/75                                                    |
| SHT-3.29 | HYBRID_ODD   | EVEN         | 3 (DUT5, DUT6, & DUT7)            | 20/75                                                    |
| SHT-3.30 | HYBRID_EVEN  | ODD          | 1 (DUT4)                          | The same as SHT-3.27 to SHT-3.29 with Tx and Rx reversed |
| SHT-3.31 | HYBRID_EVEN  | ODD          | 2 (DUT5 & DUT4)                   | The same as SHT-3.27 to SHT-3.29 with Tx and Rx reversed |
| SHT-3.32 | HYBRID_EVEN  | ODD          | 3 (DUT5, DUT4, & DUT7)            | The same as SHT-3.27 to SHT-3.29 with Tx and Rx reversed |

Test Setup: P2MP setup

Procedure:
* Associate network using E2E topology file with the (DN1) acting as the PoP
  node.
* Verify network connectivity with pings.
* Bring the DN1 ↔ DN2 up at laMaxMcs=12 and all the DN1 ↔ CN links up at
  laMaxMcs=9. For airtime allocation on DN1 set 77% of airtime for the DN ↔ DN
  link and 18% for the DN ↔ CN links (the CNs share airtime allocation equally).
* Send bidirectional iPerf traffic between DN1 and DN2 from traffic generators
  only and verify that we achieve 95% of expected.
* Send bidirectional iPerf traffic from DN1 to all CNs from traffic generators.
  Traffic is distributed evenly between all attached CNs. Verify that we achieve
  a minimum of 95% of the maximum throughput on each link.
* Send bidirectional iPerf traffic from DN1 to all links from traffic generator
  to traffic generators. Verify that each link achieves a minimum of 95% of the
  maximum throughput on each link.
* Dissociate each CN one-by-one.
* Dissociate DN1 from DN2.

Passing:
* All assocs should succeed within 2 attempts
* iPerf performance for TCP is 95% and for UDP is 97% of expected for each test
  ID, as shown in table above.
* The slot map is 50:50 on the Hybrid DN sector
* All pings should pass
* All disassocs should pass
