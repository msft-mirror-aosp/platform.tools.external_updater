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

from git_utils import find_tree_root_for_project
from conftest import make_repo_tree
import pytest


def test_find_tree_root_for_project_cwd_is_in_tree(repo_tree: Path) -> None:
    """Tests that the root is found when the CWD is in the same tree."""
    (repo_tree / "external/a").mkdir(parents=True)
    (repo_tree / "external/b").mkdir(parents=True)

    with contextlib.chdir(repo_tree / "external/a"):
        assert find_tree_root_for_project(repo_tree / "external/b") == repo_tree


def test_find_tree_root_for_project_cwd_is_in_other_tree(
    tmp_path: Path
) -> None:
    """Tests that the root is found when the CWD is in another tree."""
    tree_a = make_repo_tree(tmp_path / "a")
    tree_b = make_repo_tree(tmp_path / "b")
    (tree_a / "external/a").mkdir(parents=True)
    (tree_b / "external/b").mkdir(parents=True)

    with contextlib.chdir(tree_a / "external/a"):
        assert find_tree_root_for_project(tree_b / "external/b") == tree_b


def test_find_tree_root_for_project_no_root(tmp_path: Path) -> None:
    """Tests that an error is raised when no tree is found."""
    with pytest.raises(FileNotFoundError):
        find_tree_root_for_project(tmp_path)
