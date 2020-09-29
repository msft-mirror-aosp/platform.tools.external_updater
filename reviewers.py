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
"""Find main reviewers for git push commands."""

import math
import random
from typing import List, Mapping, Set, Union

# To randomly pick one of multiple reviewers, we put them in a List[str]
# to work with random.choice efficiently.
# To pick all of multiple reviewers, we use a Set[str].

# A ProjMapping maps a project path string to
# (1) a single reviewer email address as a string, or
# (2) a List of multiple reviewers to be randomly picked, or
# (3) a Set of multiple reviewers to be all added.
ProjMapping = Mapping[str, Union[str, List[str], Set[str]]]

# Upgrades of Rust futures-* crates should be reviewed/tested together,
# not split to radomly different people. In additional to one rust-dev
# reviewer, we need one crosvm-dev reviewer to check the impact to crosvm.
RUST_FUTURES_REVIEWERS: Set[str] = {'chh@google.com', 'natsu@google.com'}

# Rust crate owners (reviewers).
RUST_CRATE_OWNERS: ProjMapping = {
    'rust/crates/aho-corasick': 'chh@google.com',
    'rust/crates/anyhow': 'mmaurer@google.com',
    'rust/crates/bindgen': 'chh@google.com',
    'rust/crates/bytes': 'chh@google.com',
    'rust/crates/cexpr': 'chh@google.com',
    'rust/crates/cfg-if': 'chh@google.com',
    'rust/crates/clang-sys': 'chh@google.com',
    'rust/crates/futures': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-channel': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-core': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-executor': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-io': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-macro': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-sink': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-task': RUST_FUTURES_REVIEWERS,
    'rust/crates/futures-util': RUST_FUTURES_REVIEWERS,
    'rust/crates/glob': 'chh@google.com',
    'rust/crates/lazycell': 'chh@google.com',
    'rust/crates/lazy_static': 'chh@google.com',
    'rust/crates/libloading': 'chh@google.com',
    'rust/crates/log': 'chh@google.com',
    'rust/crates/nom': 'chh@google.com',
    'rust/crates/once_cell': 'chh@google.com',
    'rust/crates/peeking_take_while': 'chh@google.com',
    'rust/crates/pin-project': 'chh@google.com',
    'rust/crates/pin-project-internal': 'chh@google.com',
    'rust/crates/protobuf': 'chh@google.com',
    'rust/crates/protobuf-codegen': 'chh@google.com',
    'rust/crates/regex': 'chh@google.com',
    'rust/crates/regex-syntax': 'chh@google.com',
    'rust/crates/rustc-hash': 'chh@google.com',
    'rust/crates/shlex': 'chh@google.com',
    'rust/crates/thread_local': 'chh@google.com',
    'rust/crates/which': 'chh@google.com',
    # more rust crate owners could be added later
}

PROJ_REVIEWERS: ProjMapping = {
    # define non-rust project reviewers here
}

# Combine all roject reviewers.
PROJ_REVIEWERS.update(RUST_CRATE_OWNERS)

# Estimated number of rust projects, not the actual number.
# It is only used to make random distribution "fair" among RUST_REVIEWERS.
# It should not be too small, to spread nicely to multiple reviewers.
# It should be larger or equal to len(RUST_CRATES_OWNERS).
NUM_RUST_PROJECTS = 90

# Reviewers for external/rust/crates projects not found in PROJ_REVIEWER.
# Each person has a quota, the number of projects to review.
# Sum of these numbers should be greater or equal to NUM_RUST_PROJECTS
# to avoid error cases in the creation of RUST_REVIEWER_LIST.
RUST_REVIEWERS: Mapping[str, int] = {
    'chh@google.com': 15,
    'ivanlozano@google.com': 15,
    'jeffv@google.com': 15,
    'jgalenson@google.com': 15,
    'mmaurer@google.com': 15,
    'srhines@google.com': 15,
    'tweek@google.com': 15,
    # If a Rust reviewer needs to take a vacation, comment out the line,
    # and distribute the quota to other reviewers.
}


def add_proj_count(projects: Mapping[str, float], reviewer: str, n: float):
    """Add n to the number of projects owned by the reviewer."""
    if reviewer in projects:
        projects[reviewer] += n
    else:
        projects[reviewer] = n


# Random Rust reviewers are selected from RUST_REVIEWER_LIST,
# which is created from RUST_REVIEWERS and PROJ_REVIEWERS.
# A person P in RUST_REVIEWERS will occur in the RUST_REVIEWER_LIST N times,
# if N = RUST_REVIEWERS[P] - (number of projects owned by P in PROJ_REVIEWERS)
# is greater than 0. N is rounded up by math.ceil.
def create_rust_reviewer_list() -> List[str]:
    """Create a list of duplicated reviewers for weighted random selection."""
    # Count number of projects owned by each reviewer.
    rust_reviewers = set(RUST_REVIEWERS.keys())
    projects = {}  # map from owner to number of owned projects
    for value in PROJ_REVIEWERS.values():
        if isinstance(value, str):  # single reviewer for a project
            add_proj_count(projects, value, 1)
            continue
        # multiple reviewers share one project, count only rust_reviewers
        reviewers = set(filter(lambda x: x in rust_reviewers, value))
        if reviewers:
            count = 1.0 / len(reviewers)  # shared among all reviewers
            for name in reviewers:
                add_proj_count(projects, name, count)
    result = []
    for (x, n) in RUST_REVIEWERS.items():
        if x in projects:  # reduce x's quota by the number of assigned ones
            n = n - projects[x]
        if n > 0:
            result.extend([x] * math.ceil(n))
    if result:
        return result
    # Something was wrong or quotas were too small so that nobody
    # was selected from the RUST_REVIEWERS. Select everyone!!
    return list(RUST_REVIEWERS.keys())


RUST_REVIEWER_LIST: List[str] = create_rust_reviewer_list()


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
        if isinstance(reviewers, Set):  # add all reviewers in sorted order
            return ','.join(map(lambda x: 'r=' + x, sorted(reviewers)))
        # reviewers must be a string
        return 'r=' + reviewers
    if proj_path.startswith('rust/crates/'):
        return 'r=' + random.choice(RUST_REVIEWER_LIST)
    return ''
