/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 *
 * @format
 */
/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: 'doc',
      id: 'README',
    },
    {
      type: 'category',
      label: 'Tests',
      items: [
        'tests/IBF',
        'tests/Association',
        'tests/Throughput',
        'tests/Link_Adaptation',
        'tests/Interference',
        'tests/802.1X',
        'tests/WSEC',
        'tests/LLS',
        'tests/Scans',
        'tests/SW_Hybrid',
        'tests/Y_Street',
        'tests/Z_Street',
        'tests/Coordinated_Scheduling',
        'tests/E2E_Controller',
        'tests/Stability',
        'tests/RFC_2544',
        'tests/Routing',
        'tests/Prefix_Allocation',
        'tests/QoS',
        'tests/Link_Overloading',
      ],
    },
  ]
};

module.exports = sidebars;
