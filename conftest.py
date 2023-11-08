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
"""Pytest fixtures common across multiple test modules."""
from pathlib import Path

import pytest


@pytest.fixture(name="repo_tree")
def fixture_repo_tree(tmp_path: Path) -> Path:
    """Fixture for a repo tree."""
    (tmp_path / ".repo").mkdir()
    (tmp_path / "external/foobar").mkdir(parents=True)
    return tmp_path


@pytest.fixture(name="pore_tree")
def fixture_pore_tree(repo_tree: Path) -> Path:
    """Fixture for a pore tree."""
    (repo_tree / ".pore").mkdir()
    return repo_tree
