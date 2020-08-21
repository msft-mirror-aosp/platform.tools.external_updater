# Copyright (C) 2020 The Android Open Source Project
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
"""Find main reviewers for git push command."""

import random
from typing import List, Mapping, Set, Union

# Note that for randomly-pick-one reviewers, we put them in a List[str]
# to work with random.choice efficiently.
# For pick-all reviewers, use a Set[str] to distinguish with List[str].

# A ProjMapping maps a project path string to
# (1) a single reviewer email address as a string
# (2) multiple reviewer email addresses in a List; one to be randomly picked
# (3) multiple reviewer email addresses in a Set; all to be picked
ProjMapping = Mapping[str, Union[str, List[str], Set[str]]]

# Project specific reviewers.
PROJ_REVIEWERS: ProjMapping = {
    'rust/crates/aho-corasick': 'chh@google.com',
    'rust/crates/anyhow': 'mmaurer@google.com',
    # more could be added later
}

# Reviewers for external/rust/crates projects not found in PROJ_REVIEWER.
RUST_REVIEWERS: List[str] = [
    'chh@google.com',
    'ivanlozano@google.com',
    'jeffv@google.com',
    'jgalenson@google.com',
    'mmaurer@google.com',
    'srhines@google.com',
]


def find_reviewers(proj_path: str) -> str:
    """Returns an empty string or a reviewer parameter(s) for git push."""
    index = proj_path.find('/external/')
    if index >= 0:  # full path
        proj_path = proj_path[(index + len('/external/')):]
    elif proj_path.startswith('external/'):  # relative path
        proj_path = proj_path[len('external/'):]
    if proj_path in PROJ_REVIEWERS:
        reviewers = PROJ_REVIEWERS[proj_path]
        if isinstance(reviewers, List):  # pick any one reviewer
            return 'r=' + random.choice(reviewers)
        if isinstance(reviewers, Set):  # add all reviewers
            return ','.join(map(lambda x: 'r=' + x, reviewers))
        # reviewers must be a string
        return 'r=' + reviewers
    if proj_path.startswith('rust/crates/'):
        return 'r=' + random.choice(RUST_REVIEWERS)
    return ''
