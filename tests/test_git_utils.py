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
"""Tests for git_utils."""
import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import git_utils

from .gitrepo import GitRepo


class GitRepoTestCase(unittest.TestCase):
    """Common base for tests that operate on a git repo."""

    def setUp(self) -> None:
        # Local test runs will probably pass without this since the caller
        # almost certainly has git configured, but the bots that run the tests
        # may not. **Do not** use `git config --global` for this, since that
        # will modify the caller's config during local testing.
        self._original_env = os.environ.copy()
        os.environ["GIT_AUTHOR_NAME"] = "Testy McTestFace"
        os.environ["GIT_AUTHOR_EMAIL"] = "test@example.com"
        os.environ["GIT_COMMITTER_NAME"] = os.environ["GIT_AUTHOR_NAME"]
        os.environ["GIT_COMMITTER_EMAIL"] = os.environ["GIT_AUTHOR_EMAIL"]

        with ExitStack() as stack:
            temp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
            stack.enter_context(temp_dir)
            self.addCleanup(stack.pop_all().close)
            self.repo = GitRepo(Path(temp_dir.name) / "repo")

    def tearDown(self) -> None:
        # This isn't trivially `os.environ = self._original_env` because
        # os.environ isn't actually a dict, it's an os._Environ, and there isn't
        # a good way to construct a new one of those.
        os.environ.clear()
        os.environ.update(self._original_env)


class IsAncestorTest(GitRepoTestCase):
    """Tests for git_utils.is_ancestor."""

    def test_if_commit_is_its_own_ancestor(self) -> None:
        """Tests that False is returned when both commits are the same."""
        self.repo.init()
        self.repo.commit("Initial commit.", allow_empty=True)
        initial_commit = self.repo.head()
        assert not git_utils.is_ancestor(self.repo.path, initial_commit, initial_commit)

    def test_is_ancestor(self) -> None:
        """Tests that True is returned when the ref is an ancestor."""
        self.repo.init()
        self.repo.commit("Initial commit.", allow_empty=True)
        initial_commit = self.repo.head()
        self.repo.commit("Second commit.", allow_empty=True)
        second_commit = self.repo.head()
        git_utils.is_ancestor(self.repo.path, initial_commit, second_commit)

    def test_is_not_ancestor(self) -> None:
        """Tests that False is returned when the ref is not an ancestor."""
        self.repo.init()
        self.repo.commit("Initial commit.", allow_empty=True)
        initial_commit = self.repo.head()
        self.repo.commit("Second commit.", allow_empty=True)
        second_commit = self.repo.head()
        assert not git_utils.is_ancestor(self.repo.path, second_commit, initial_commit)

    def test_error(self) -> None:
        """Tests that an error is raised when git encounters an error."""
        self.repo.init()
        with self.assertRaises(CalledProcessError):
            git_utils.is_ancestor(self.repo.path, "not-a-ref", "not-a-ref")


class GetMostRecentTagTest(GitRepoTestCase):
    """Tests for git_utils.get_most_recent_tag."""

    def test_find_tag_on_correct_branch(self) -> None:
        """Tests that only tags on the given branch are found."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        self.repo.tag("v1.0.0")
        self.repo.switch_to_new_branch("release-2.0")
        self.repo.commit("Second commit.", allow_empty=True)
        self.repo.tag("v2.0.0")
        self.assertEqual(
            git_utils.get_most_recent_tag(self.repo.path, "main"), "v1.0.0"
        )

    def test_no_tags(self) -> None:
        """Tests that None is returned when the repo has no tags."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        self.assertIsNone(git_utils.get_most_recent_tag(self.repo.path, "main"))

    def test_no_describing_tags(self) -> None:
        """Tests that None is returned when no tags describe the ref."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        self.repo.switch_to_new_branch("release-2.0")
        self.repo.commit("Second commit.", allow_empty=True)
        self.repo.tag("v2.0.0")
        self.assertIsNone(git_utils.get_most_recent_tag(self.repo.path, "main"))


class DiffTest(GitRepoTestCase):
    def test_diff_stat_A_filter(self) -> None:
        """Tests for git_utils.diff_stat."""
        self.repo.init("main")
        self.repo.commit(
            "Add README.md", update_files={"README.md": "Hello, world!"}
        )
        first_commit = self.repo.head()
        self.repo.commit(
            "Add OWNERS and METADATA",
            update_files={"OWNERS": "nobody"}
        )
        diff = git_utils.diff_stat(self.repo.path, 'A', first_commit)
        assert 'OWNERS | 1 +' in diff

    def test_diff_name_only_A_filter(self) -> None:
        """Tests for git_utils.diff_name_only."""
        self.repo.init("main")
        self.repo.commit(
            "Add README.md", update_files={"README.md": "Hello, world!"}
        )
        first_commit = self.repo.head()
        self.repo.commit(
            "Add OWNERS and METADATA",
            update_files={"OWNERS": "nobody", "METADATA": "name: 'foo'"}
        )
        diff = git_utils.diff_name_only(self.repo.path, 'A', first_commit)
        assert diff == 'METADATA\nOWNERS\n'


class GetShaForRevisionTest(GitRepoTestCase):
    """Tests for git_utils.get_sha_for_revision."""

    def test_get_sha_for_existing_tag(self) -> None:
        """Tests if it can find the SHA of an existing tag"""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        first_commit = self.repo.head()
        self.repo.tag("tag1")
        out = git_utils.get_sha_for_revision(self.repo.path, "tag1")
        assert first_commit == out

    def test_get_sha_for_existing_sha(self) -> None:
        """Tests if the same SHA is returned."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        first_commit = self.repo.head()
        out = git_utils.get_sha_for_revision(self.repo.path, first_commit)
        assert first_commit == out

    def test_get_sha_for_non_existent_tag(self) -> None:
        """Tests if it prints error message if the tag doesn't exist."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        out = git_utils.get_sha_for_revision(self.repo.path, "tag1")
        assert "fatal: ambiguous argument" in out


class GetTagForRevisionTest(GitRepoTestCase):
    """Tests for git_utils.get_tag_for_revision."""

    def test_describe_a_tagged_sha(self) -> None:
        """Tests if it finds the tag of a SHA."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        self.repo.tag("tag1")
        first_commit = self.repo.head()
        out = git_utils.get_tag_for_revision(self.repo.path, first_commit)
        assert out == "tag1"

    def test_describe_a_non_tagged_sha(self) -> None:
        """Tests if None is returned if no tag is associated with a SHA."""
        self.repo.init("main")
        self.repo.commit("Initial commit.", allow_empty=True)
        first_commit = self.repo.head()
        out = git_utils.get_tag_for_revision(self.repo.path, first_commit)
        assert out is None


class MergeBaseTest(GitRepoTestCase):
    """Tests for git_utils.merge_base."""

    def test_merge_base_with_common_ancestor(self) -> None:
        """Tests if it finds the common ancestor of two branches."""
        self.repo.init("main")
        self.repo.commit("Initial commit on main branch.", allow_empty=True)
        first_commit = self.repo.head()
        self.repo.switch_to_new_branch("dev")
        self.repo.commit("Second commit on dev", allow_empty=True)
        out = git_utils.merge_base(self.repo.path, "main", "dev")
        assert first_commit == out


class FindNonDefaultBranchTest(unittest.TestCase):
    """Tests for git_utils.find_non_default_branch"""
    def test_branch_in_github_url(self) -> None:
        """Tests if the branch attached to the url is found."""
        url = 'https://github.com/robolectric/robolectric/tree/google'
        non_default_branch = git_utils.find_non_default_branch(url)
        self.assertEqual(non_default_branch, "google")

    def test_no_branch_in_url(self) -> None:
        """Tests if None is returned when the url doesn't have a branch."""
        url = 'https://github.com/GNOME/libxml2/'
        non_default_branch = git_utils.find_non_default_branch(url)
        self.assertIsNone(non_default_branch)

    def test_branch_in_gitlab_url(self) -> None:
        """Tests if None is returned when the url is non-GitHub git."""
        url = 'https://gitlab.xiph.org/xiph/opus/-/tree/whitespace'
        non_default_branch = git_utils.find_non_default_branch(url)
        self.assertIsNone(non_default_branch)


if __name__ == "__main__":
    unittest.main(verbosity=2)
