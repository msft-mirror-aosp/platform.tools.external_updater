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

# Project specific reviewers.
PROJ_REVIEWER = {
    'rust/crates/aho-corasick': 'chh@google.com',
    'rust/crates/anyhow': 'mmaurer@google.com',
    'rust/crates/async-trait': 'qwandor@google.com',
    # more could be added later
}

# Reviewers for external/rust/crates projects not found in PROJ_REVIEWER.
RUST_REVIEWERS = [
    'chh@google.com',
    'ivanlozano@google.com',
    'jeffv@google.com',
    'jgalenson@google.com',
    'mmaurer@google.com',
    'srhines@google.com',
]


def find_reviewer(proj_path: str) -> str:
    """Returns an empty string or a reviewer parameter for git push."""
    index = proj_path.find('/external/')
    if index >= 0:  # full path
        proj_path = proj_path[(index + len('/external/')):]
    elif proj_path.startswith('external/'):  # relative path
        proj_path = proj_path[len('external/'):]
    if proj_path in PROJ_REVIEWER:
        return PROJ_REVIEWER[proj_path]
    if proj_path.startswith('rust/crates/'):
        return random.choice(RUST_REVIEWERS)
    return ''
