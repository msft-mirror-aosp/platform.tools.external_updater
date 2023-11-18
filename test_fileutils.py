#
# Copyright (C) 2023 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Unit tests for fileutils."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import fileutils


class ResolveCommandLinePathsTest(unittest.TestCase):
    """Unit tests for resolve_command_line_paths."""

    def test_empty_paths(self) -> None:
        """Tests that an empty argument returns an empty list."""
        self.assertListEqual([], fileutils.resolve_command_line_paths([]))

    def test_absolute_paths(self) -> None:
        """Tests that absolute paths are resolved correctly."""
        # The current implementation will remove paths which do not exist from the
        # output, so the test inputs need to be paths that exist on the system running
        # the test.
        self.assertListEqual(
            ["/usr/lib", "/bin"],
            fileutils.resolve_command_line_paths(["/usr/lib", "/bin"]),
        )

    def test_external_relative_paths(self) -> None:
        """Tests that paths relative to //external are resolved correctly."""
        with TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            external = temp_dir / "external"
            external.mkdir()
            a = external / "a"
            b = external / "b"
            a.mkdir()
            b.mkdir()
            old_env = dict(os.environ)
            try:
                os.environ["ANDROID_BUILD_TOP"] = str(temp_dir)
                self.assertListEqual(
                    [str(a), str(b)], fileutils.resolve_command_line_paths(["a", "b"])
                )
            finally:
                os.environ = old_env  # type: ignore


if __name__ == "__main__":
    unittest.main(verbosity=2)
