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
"""Tests for gitrepo."""
import subprocess
from pathlib import Path

import pytest

from .gitrepo import GitRepo


class TestGitRepo:
    """Tests for gitrepo.GitRepo."""

    def test_commit_adds_files(self, tmp_path: Path) -> None:
        """Tests that new files in commit are added to the repo."""
        repo = GitRepo(tmp_path / "repo")
        repo.init()
        repo.commit("Add README.md.", update_files={"README.md": "Hello, world!"})
        assert repo.commit_message_at_revision("HEAD") == "Add README.md.\n"
        assert repo.file_contents_at_revision("HEAD", "README.md") == "Hello, world!"

    def test_commit_updates_files(self, tmp_path: Path) -> None:
        """Tests that updated files in commit are modified."""
        repo = GitRepo(tmp_path / "repo")
        repo.init()
        repo.commit("Add README.md.", update_files={"README.md": "Hello, world!"})
        repo.commit("Update README.md.", update_files={"README.md": "Goodbye, world!"})
        assert repo.commit_message_at_revision("HEAD^") == "Add README.md.\n"
        assert repo.file_contents_at_revision("HEAD^", "README.md") == "Hello, world!"
        assert repo.commit_message_at_revision("HEAD") == "Update README.md.\n"
        assert repo.file_contents_at_revision("HEAD", "README.md") == "Goodbye, world!"

    def test_commit_deletes_files(self, tmp_path: Path) -> None:
        """Tests that files deleted by commit are removed from the repo."""
        repo = GitRepo(tmp_path / "repo")
        repo.init()
        repo.commit("Add README.md.", update_files={"README.md": "Hello, world!"})
        repo.commit("Remove README.md.", delete_files={"README.md"})
        assert repo.commit_message_at_revision("HEAD^") == "Add README.md.\n"
        assert repo.file_contents_at_revision("HEAD^", "README.md") == "Hello, world!"
        assert repo.commit_message_at_revision("HEAD") == "Remove README.md.\n"
        assert (
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo.path),
                    "ls-files",
                    "--error-unmatch",
                    "README.md",
                ],
                check=False,
            ).returncode
            != 0
        )

    def test_current_branch(self, tmp_path: Path) -> None:
        """Tests that current branch returns the current branch name."""
        repo = GitRepo(tmp_path / "repo")
        repo.init("main")
        assert repo.current_branch() == "main"

    def test_current_branch_fails_if_not_init(self, tmp_path: Path) -> None:
        """Tests that current branch fails when there is no git repo."""
        with pytest.raises(subprocess.CalledProcessError):
            GitRepo(tmp_path / "repo").current_branch()

    def test_switch_to_new_branch(self, tmp_path: Path) -> None:
        """Tests that switch_to_new_branch creates a new branch and switches to it."""
        repo = GitRepo(tmp_path / "repo")
        repo.init("main")
        repo.switch_to_new_branch("feature")
        assert repo.current_branch() == "feature"

    def test_switch_to_new_branch_does_not_clobber_existing_branches(
        self, tmp_path: Path
    ) -> None:
        """Tests that switch_to_new_branch raises an error for extant branches."""
        repo = GitRepo(tmp_path / "repo")
        repo.init("main")
        repo.commit("Initial commit.", allow_empty=True)
        with pytest.raises(subprocess.CalledProcessError):
            repo.switch_to_new_branch("main")

    def test_switch_to_new_branch_with_start_point(self, tmp_path: Path) -> None:
        """Tests that switch_to_new_branch uses the provided start point."""
        repo = GitRepo(tmp_path / "repo")
        repo.init("main")
        repo.commit("Initial commit.", allow_empty=True)
        initial_commit = repo.head()
        repo.commit("Second commit.", allow_empty=True)
        repo.switch_to_new_branch("feature", start_point=initial_commit)
        assert repo.current_branch() == "feature"
        assert repo.head() == initial_commit
