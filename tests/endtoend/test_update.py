#
# Copyright (C) 2024 The Android Open Source Project
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
"""End-to-end tests for external_updater."""
import subprocess
from pathlib import Path

from .treebuilder import TreeBuilder


class TestUpdate:

    def update(self, updater_cmd: list[str], paths: list[Path], args: list[str] | None = None, bug_number: str | None = None) -> str:
        """Runs `external_updater update` with the given arguments.

        Returns:
        The output of the command.
        """
        return subprocess.run(
            updater_cmd + ["update"] +
            (args if args is not None else []) +
            (["--bug", bug_number] if bug_number is not None else []) +
            [str(p) for p in paths],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def test_bug_number(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that bug number is added to the commit message."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        bug_number = "12345"
        self.update(updater_cmd, [a.local.path], args=['--refresh'], bug_number=bug_number)
        latest_sha = a.local.head()
        latest_commit_message = a.local.commit_message_at_revision(latest_sha)
        assert f"Bug: {bug_number}" in latest_commit_message
