# Prefix Allocation (CPA/DPA) Tests

## All Tests

### `PUMA_IF_CPA1` Enable Centralized Prefix Allocation
Description: This test is check if a network comes up with enabling centralized
prefix allocation.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Set the controller config `enable_centralized_prefix` as true, and
  `prefixAllocParam` using API service
* Restart the `e2e_controller.service`
* Recheck network state

Pass/Fail Criteria:
* Network should come up with CPA enabled and the nodes in the network must have
  the prefixes provided by the controller.
* Check the prefixes in the topology file on E2E to make sure, each node in the
  network has the prefix allocated by the controller.

### `PUMA_IF_CPA2` Disable Centralized Prefix Allocation and Re-Enable
Description: This test is check if a network comes up with enabling centralized
prefix allocation.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
1. Bring up the network as specified in test CPA1.
2. Recheck network state.
3. Set the controller config `enable_centralized_prefix` as false using API
   service
4. Give a delay of around 5 minutes
5. Restart the `e2e_controller.service`
6. Recheck network state
7. Set the controller config `enable_centralized_prefix` as true using API
   service
8. Give a delay of around 5 minutes
9. Restart the `e2e_controller.service`
10. Recheck network state

Pass/Fail Criteria:
* Network should come up with CPA disabled after step 6.
* Network should come up with CPA enabled after step 10 and the nodes in the
  network must have the prefixes provided by the controller.

### `PUMA_IF_DPA1` Enable Deterministic Prefix Allocation
Description: This test is check if a network comes up with enabling
deterministic prefix allocation.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Set the controller config enable_deterministic_prefix as true
* Restart the `e2e_controller.service`
* Recheck network state

Pass/Fail Criteria:
* Network should come up with DPA enabled

### `PUMA_IF_DPA2` Disable Deterministic Prefix Allocation
Description: This test is check if a network stays up after disabling
deterministic prefix allocation.

Test Setup: IF Fig-of-8 or largest IF setup available

Procedure:
* Ignite the network with DPA enabled (`enable_deterministic_prefix` as true)
* Set the controller config `enable_deterministic_prefix` as false
* Restart the `e2e_controller.service`
* Recheck network state

Pass/Fail Criteria:
* Network should come up with DPA disabled
