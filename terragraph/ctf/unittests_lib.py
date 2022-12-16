#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import time
from concurrent.futures import as_completed, ThreadPoolExecutor
from copy import deepcopy
from typing import Any

from later.unittest import TestCase
from terragraph.ctf import unittests_fixtures
from terragraph.ctf.tg import BaseTgCtfTest


class TgCtfLibTests(TestCase):
    retry: int = 0  # current retry used in test_try_until_timeout

    def setUp(self) -> None:
        self.bt = BaseTgCtfTest(unittests_fixtures.FAKE_ARGS)

    def test_modify_node_config(self) -> None:
        config = deepcopy(unittests_fixtures.NODE_CURRENT_CONFIG)
        self.bt.merge_dict(config, unittests_fixtures.NODE_TEST_CONFIG)
        self.assertEqual(unittests_fixtures.EXPECTED_MERGED_CONFIG, config)

    def _expect_thread_local(self, step_idx) -> None:
        self.assertEqual(step_idx, self.bt.thread_local.step_idx)

    def _step_thread_main(self, step_idx: int, subthread: bool) -> None:
        """Test threadlocal in this thread and one sub-threaded if requested"""

        # Test ThreadLocal default initialization
        #
        # Note: This only succeeds once per new thread. Will fail on pooled
        # threads in which thread local has been initialized (when they are
        # re-used by ThreadPoolExecutor).
        self._expect_thread_local(self.bt.thread_local.DEFAULT_INVALID_STEP_IDX)

        # ThreadLocal was initialized at least once before (in test_thread_local)
        self.assertTrue(self.bt.thread_local.initialized)

        # Test ThreadLocal initialization
        self.bt.thread_local.init(step_idx)
        self._expect_thread_local(step_idx)

        # ThreadLocal in sub-thread
        if subthread:
            thread_pool = ThreadPoolExecutor(thread_name_prefix="Step", max_workers=1)
            futures = {}
            futures[
                thread_pool.submit(self._step_thread_main, step_idx, subthread=False)
            ] = 1

            for _future in as_completed(futures.keys(), timeout=5):
                pass

            self.bt.cleanupThreadPool(thread_pool)

    def test_thread_local(self) -> None:
        """Test ThreadLocal initialization in threads and subthreads"""

        # Test threadLocal default initialization
        self._expect_thread_local(self.bt.thread_local.DEFAULT_INVALID_STEP_IDX)
        self.assertFalse(self.bt.thread_local.initialized)

        # Test ThreadLocal initialization
        step_idx: int = 17  # Valid step_idx > 0
        self.bt.thread_local.init(step_idx)
        self._expect_thread_local(step_idx)
        self.assertTrue(self.bt.thread_local.initialized)

        # Test ThreadLocal in threads and sub-threads
        thread_pool = ThreadPoolExecutor(thread_name_prefix="Step", max_workers=1)
        futures = {}
        futures[
            thread_pool.submit(self._step_thread_main, step_idx, subthread=True)
        ] = 1

        for _future in as_completed(futures.keys(), timeout=5):
            pass

        self.bt.cleanupThreadPool(thread_pool)

    def _timeout_fn(
        self, sleep_sec: float, raise_until_retry: int, return_val: Any
    ) -> Any:
        """Helper for testing try_until_timeout()"""
        self.retry = self.retry + 1
        time.sleep(sleep_sec)
        if raise_until_retry > 0 and self.retry <= raise_until_retry:
            raise Exception("timeout_fn failed")
        return return_val

    def _get_deadline(self, timeout: float, retry_interval: float) -> float:
        """Get conservative wallclock deadline for try_until_timeout()"""
        return time.monotonic() + timeout + 6.0 * retry_interval + 0.1

    def test_try_until_timeout(self) -> None:
        """Test try_until_timeout"""

        T: float = 0.25  # unit of time (in seconds)
        deadline: float = 0.0

        # Pretend this is test step 1 to unblock log_to_ctf()
        self.bt.thread_local.init(1)

        # Succeed: succeed on the first try by returning None
        self.retry = 0
        deadline = self._get_deadline(timeout=3 * T, retry_interval=T)
        self.assertTrue(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(T, 0, None),
                retry_interval=T,
                timeout=3 * T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)

        # Succeed: succeed on the first try by returning dict
        self.retry = 0
        deadline = self._get_deadline(timeout=3 * T, retry_interval=T)
        self.assertTrue(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(T, 0, {"error": 0}),
                retry_interval=T,
                timeout=3 * T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)

        # Fail: time out on the first try
        self.retry = 0
        deadline = self._get_deadline(timeout=T, retry_interval=T)
        self.assertFalse(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(2 * T, 0, None),
                retry_interval=T,
                timeout=T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)

        # Succeed: raise exceptions for 3 retries, then succeed by returning True
        self.retry = 0
        deadline = self._get_deadline(timeout=6 * T, retry_interval=T)
        self.assertTrue(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(T, 3, True),
                retry_interval=T,
                timeout=6 * T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)

        # Fail: raise exceptions for 3 retries, then fail by returning dict
        self.retry = 0
        deadline = self._get_deadline(timeout=6 * T, retry_interval=T)
        self.assertFalse(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(T, 3, {"error": "oops"}),
                retry_interval=T,
                timeout=6 * T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)

        # Fail: raise exceptions on every retry
        self.retry = 0
        deadline = self._get_deadline(timeout=4 * T, retry_interval=T)
        self.assertFalse(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(T, 10, True),
                retry_interval=T,
                timeout=4 * T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)

        # Fail: raise exception once, and then return False on every retry
        self.retry = 0
        deadline = self._get_deadline(timeout=4 * T, retry_interval=T)
        self.assertFalse(
            self.bt.try_until_timeout_noexcept(
                fn=self._timeout_fn,
                fn_args=(T, 1, False),
                retry_interval=T,
                timeout=4 * T,
            )
        )
        self.assertTrue(time.monotonic() <= deadline)
