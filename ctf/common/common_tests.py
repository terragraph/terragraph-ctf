# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import unittest

from ctf.common.helper_functions import create_full_path


class CommonTests(unittest.TestCase):
    def test_linux_device_path(self) -> None:
        dir_path = "/tmp/mydir"
        full_path = "/tmp/mysource_dir/file.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file.txt")

    def test_windows_device_path(self) -> None:
        dir_path = "/tmp/mydir"
        full_path = "C:\\Users\\file.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file.txt")

    def test_linux_device_path_glob(self) -> None:
        dir_path = "/tmp/mydir"
        full_path = "/tmp/mysource_dir/file_*.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file_*.txt")

    def test_windows_device_path_glob(self) -> None:
        dir_path = "/tmp/mydir"
        full_path = "C:\\Users\\file_*.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file_*.txt")

    def test_linux_device_path_trail_backslash(self) -> None:
        dir_path = "/tmp/mydir/"
        full_path = "/tmp/mysource_dir/file.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file.txt")

    def test_windows_device_path_trail_backslash(self) -> None:
        dir_path = "/tmp/mydir/"
        full_path = "C:\\Users\\file.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file.txt")

    def test_linux_device_path_glob_trail_backslash(self) -> None:
        dir_path = "/tmp/mydir/"
        full_path = "/tmp/mysource_dir/file_*.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file_*.txt")

    def test_windows_device_path_glob_trail_backslash(self) -> None:
        dir_path = "/tmp/mydir/"
        full_path = "C:\\Users\\file_*.txt"
        created_path = create_full_path(dir_path, full_path)
        self.assertEqual(created_path, "/tmp/mydir/file_*.txt")
