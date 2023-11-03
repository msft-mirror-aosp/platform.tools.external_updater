#
# Copyright (C) 2023 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests for the git_utils module."""
import contextlib
from pathlib import Path

from pytest_mock import MockerFixture

from git_utils import find_tree_root_for_project, tree_uses_pore


def test_tree_uses_pore_fast_path(tmp_path: Path, mocker: MockerFixture) -> None:
    """Tests that the fast-path does not recurse."""
    which_mock = mocker.patch("shutil.which")
    which_mock.return_value = None
    path_parent_mock = mocker.patch("pathlib.Path.parent")
    assert not tree_uses_pore(tmp_path)
    path_parent_mock.assert_not_called()


def test_tree_uses_pore_identifies_pore_trees(pore_tree: Path, mocker: MockerFixture) -> None:
    """Tests that a pore tree is correctly identified."""
    which_mock = mocker.patch("shutil.which")
    which_mock.return_value = Path("pore")
    assert tree_uses_pore(pore_tree)


def test_tree_uses_pore_identifies_repo_trees(repo_tree: Path, mocker: MockerFixture) -> None:
    """Tests that a repo tree is correctly identified."""
    which_mock = mocker.patch("shutil.which")
    which_mock.return_value = Path("pore")
    assert not tree_uses_pore(repo_tree)


def test_find_tree_root_for_project_cwd_is_in_tree(repo_tree: Path) -> None:
    """Tests that the root is found when the CWD is in the same tree."""
    (repo_tree / "external/a").mkdir(parents=True)
    (repo_tree / "external/b").mkdir(parents=True)

    with contextlib.chdir(repo_tree / "external/a"):
        assert find_tree_root_for_project(repo_tree / "external/b") == repo_tree


# Using both a pore tree and repo tree here isn't important, it's just annoying to use
# the same fixture twice, so it's easier to use both fixtures.
def test_find_tree_root_for_project_cwd_is_in_other_tree(
    repo_tree: Path, pore_tree: Path
) -> None:
    """Tests that the root is found when the CWD is in another tree."""
    (repo_tree / "external/a").mkdir(parents=True)
    (pore_tree / "external/b").mkdir(parents=True)

    with contextlib.chdir(repo_tree / "external/a"):
        assert find_tree_root_for_project(repo_tree / "external/b") == pore_tree


def test_finds_pore_trees(pore_tree: Path) -> None:
    """Tests that pore trees are found."""
    (pore_tree / "external/a").mkdir(parents=True)
    assert find_tree_root_for_project(pore_tree / "external/b") == pore_tree
