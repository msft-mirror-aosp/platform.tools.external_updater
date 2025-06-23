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
from string import Template

from .treebuilder import TreeBuilder

WRONG_METADATA_FILE = """\
name: "test"
description: "It's a test."
third_party {
  license_type: UNENCUMBERED
  last_upgrade_date {
    year: 2023
    month: 12
    day: 1
  }
  identifier {
    type: "Git"
    value: "$upstream_uri"
    version: "$upstream_version"
  }
}
"""


class TestValidate:
    def validate(
        self,
        updater_cmd: list[str],
        paths: list[Path],
        args: list[str] | None = None,
        input: str | None = None,
    ) -> str:
        """Runs `external_updater validate` with the given arguments.

        Returns:
        The output of the command.
        """
        return subprocess.run(
            updater_cmd + ["validate"] +
            (args if args is not None else []) +
            [str(p) for p in paths],
            check=True,
            capture_output=True,
            text=True,
            input=input
        ).stdout

    def test_metadata_version_accurate(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that bug number is added to the commit message."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        output = self.validate(updater_cmd, [a.local.path])
        assert "No diff" in output

    def test_metadata_version_not_accurate(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that bug number is added to the commit message."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        commit_one = a.upstream.head()
        a.upstream.commit("Second commit.", allow_empty=True)
        commit_two = a.upstream.head()
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        upstream_url = a.upstream.path.as_uri()
        template = Template(WRONG_METADATA_FILE)
        new_metadata = template.substitute(upstream_uri=upstream_url, upstream_version=commit_one)
        a.android_mirror.commit("Changing METADATA version to commit_one",
                       update_files={"METADATA": new_metadata})
        output = self.validate(updater_cmd, [a.local.path])
        expected_output = f"We suspect that it should be SHA {commit_two}"
        assert expected_output in output
