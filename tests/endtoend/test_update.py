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

import git_utils
from .treebuilder import TreeBuilder

UNFORMATTED_BP_FILE = """\
cc_library_shared {
    name: "test",
    srcs: [
        "source2.c",
        "source1.c",
    ],
    cflags: ["-Wno-error=ignored-attributes", "-Wall", "-Werror"],
}
"""

FORMATTED_BP_FILE = """\
cc_library_shared {
    name: "test",
    srcs: [
        "source2.c",
        "source1.c",
    ],
    cflags: [
        "-Wno-error=ignored-attributes",
        "-Wall",
        "-Werror",
    ],
}
"""


class TestUpdate:

    def update(
        self,
        updater_cmd: list[str],
        paths: list[Path],
        args: list[str] | None = None,
    ) -> str:
        """Runs `external_updater update` with the given arguments.

        Returns:
        The output of the command.
        """
        return subprocess.run(
            updater_cmd + ["update"] +
            (args if args is not None else []) +
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
        self.update(updater_cmd, [a.local.path], args=['--refresh', '--bug', bug_number])
        latest_sha = a.local.head()
        latest_commit_message = a.local.commit_message_at_revision(latest_sha)
        assert f"Bug: {bug_number}" in latest_commit_message

    def test_custom_update_to_tag_successful(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that upgrade to a specific tag is successful."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        a.upstream.tag("v1.0.0")
        tree.create_manifest_repo()
        a.initial_import(True)
        tree.init_and_sync()
        a.upstream.commit("Second commit.", allow_empty=True)
        a.upstream.tag("v2.0.0")
        a.upstream.commit("Third commit.", allow_empty=True)
        a.upstream.tag("v3.0.0")
        self.update(updater_cmd, [a.local.path], args=['--custom-version', "v2.0.0"])
        latest_sha = a.local.head()
        latest_commit_message = a.local.commit_message_at_revision(latest_sha)
        assert "Upgrade test to v2.0.0" in latest_commit_message

    def test_custom_downgrade_to_tag_unsuccessful(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that downgrade to a specific tag is unsuccessful."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        a.upstream.tag("v1.0.0")
        a.upstream.commit("Second commit.", allow_empty=True)
        a.upstream.tag("v2.0.0")
        tree.create_manifest_repo()
        a.initial_import(True)
        tree.init_and_sync()
        self.update(updater_cmd, [a.local.path], args=['--custom-version', "v1.0.0"])
        latest_sha = a.local.head()
        latest_commit_message = a.local.commit_message_at_revision(latest_sha)
        assert "Add metadata files." in latest_commit_message

    def test_custom_update_to_sha_successful(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that upgrade to a specific sha is successful."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        a.upstream.commit("Second commit.", allow_empty=True)
        custom_sha = a.upstream.head()
        a.upstream.commit("Third commit.", allow_empty=True)
        self.update(updater_cmd, [a.local.path], args=['--custom-version', custom_sha])
        latest_sha = a.local.head()
        latest_commit_message = a.local.commit_message_at_revision(latest_sha)
        assert f"Upgrade test to {custom_sha}" in latest_commit_message

    def test_custom_downgrade_to_sha_unsuccessful(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that downgrade to a specific sha is unsuccessful."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        custom_sha = a.upstream.head()
        a.upstream.commit("Second commit.", allow_empty=True)
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        self.update(updater_cmd, [a.local.path], args=['--custom-version', custom_sha])
        latest_sha = a.local.head()
        latest_commit_message = a.local.commit_message_at_revision(latest_sha)
        assert "Add metadata files." in latest_commit_message

    def test_bpfmt_one_local_bp_file_no_upstream_bp_file(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that bpfmt formats the only local bp file."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        tree.create_manifest_repo()
        a.initial_import()
        a.android_mirror.commit("Add Android.bp file", update_files={"Android.bp": UNFORMATTED_BP_FILE})
        tree.init_and_sync()
        a.upstream.commit("Second commit.", allow_empty=True)
        self.update(updater_cmd, [a.local.path])
        latest_sha = a.local.head()
        bp_content = a.local.file_contents_at_revision(latest_sha, 'Android.bp')
        assert bp_content == FORMATTED_BP_FILE

    def test_bpfmt_one_local_bp_file_one_upstream_bp_file(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests that bpfmt doesn't format the bp file because it's an upstream file."""
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit and adding bp file", update_files={"Android.bp": UNFORMATTED_BP_FILE})
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        a.upstream.commit("Second commit.", allow_empty=True)
        self.update(updater_cmd, [a.local.path])
        latest_sha = a.local.head()
        bp_content = a.local.file_contents_at_revision(latest_sha, 'Android.bp')
        assert bp_content == UNFORMATTED_BP_FILE

    def test_repo_sync(
        self, tree_builder: TreeBuilder, updater_cmd: list[str]
    ) -> None:
        """Tests if updater is fooled by checking out an older commit.

        We want to see if we checkout an older update commit, external_updater
        knows we are up to date and it is not fooled by the fake out of date
        state.
        """
        tree = tree_builder.repo_tree("tree")
        a = tree.project("platform/external/foo", "external/foo")
        a.upstream.commit("Initial commit.", allow_empty=True)
        tree.create_manifest_repo()
        a.initial_import()
        tree.init_and_sync()
        head_after_import = a.android_mirror.head()
        a.upstream.commit("Second commit.", allow_empty=True)
        commit_two = a.upstream.head()
        self.update(updater_cmd, [a.local.path])
        a.android_mirror.checkout(head_after_import)
        output = self.update(updater_cmd, [a.local.path])
        assert output == (
            f"repo sync has finished successfully.\n"
            f"Checking {a.local.path}...\n"
            f"Current version: {commit_two}\n"
            f"Latest version: {commit_two}\n"
            "Up to date.\n"
        )
