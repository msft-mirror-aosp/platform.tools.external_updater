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
