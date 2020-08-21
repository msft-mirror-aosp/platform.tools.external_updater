# Copyright (C) 2018 The Android Open Source Project
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
"""Unit tests for external updater."""

from typing import List, Mapping, Set
import unittest

import github_archive_updater
import reviewers


class ExternalUpdaterTest(unittest.TestCase):
    """Unit tests for external updater."""

    def test_url_selection(self):
        """Tests that GithubArchiveUpdater can choose the right url."""
        prefix = "https://github.com/author/project/"
        urls = [
            prefix + "releases/download/ver-1.0/ver-1.0-binary.zip",
            prefix + "releases/download/ver-1.0/ver-1.0-binary.tar.gz",
            prefix + "releases/download/ver-1.0/ver-1.0-src.zip",
            prefix + "releases/download/ver-1.0/ver-1.0-src.tar.gz",
            prefix + "archive/ver-1.0.zip",
            prefix + "archive/ver-1.0.tar.gz",
        ]

        previous_url = prefix + "releases/download/ver-0.9/ver-0.9-src.tar.gz"
        url = github_archive_updater.choose_best_url(urls, previous_url)
        expected_url = prefix + "releases/download/ver-1.0/ver-1.0-src.tar.gz"
        self.assertEqual(url, expected_url)

        previous_url = prefix + "archive/ver-0.9.zip"
        url = github_archive_updater.choose_best_url(urls, previous_url)
        expected_url = prefix + "archive/ver-1.0.zip"
        self.assertEqual(url, expected_url)

    def collect_reviewers(self, num_runs, proj_path):
        counters = {}
        for _ in range(num_runs):
            name = reviewers.find_reviewers(proj_path)
            if name in counters:
                counters[name] += 1
            else:
                counters[name] = 1
        return counters

    def test_reviewers(self):
        # There should be enough people in the reviewers pool.
        self.assertGreaterEqual(len(reviewers.RUST_REVIEWERS), 3)
        # Check element types of the reviewers list and map.
        self.assertIsInstance(reviewers.RUST_REVIEWERS, List)
        for x in reviewers.RUST_REVIEWERS:
            self.assertIsInstance(x, str)
        self.assertIsInstance(reviewers.PROJ_REVIEWERS, Mapping)
        for key, value in reviewers.PROJ_REVIEWERS.items():
            self.assertIsInstance(key, str)
            if isinstance(value, Set) or isinstance(value, List):
                for x in value:
                    self.assertIsInstance(x, str)
            else:
                self.assertIsInstance(value, str)
        # Check random selection of reviewers.
        # This might fail when the random.choice function is extremely unfair.
        # With N * 20 tries, each reviewer should be picked at least twice.
        counters = self.collect_reviewers(len(reviewers.RUST_REVIEWERS) * 20,
                                          "rust/crates/no_such_project")
        self.assertEqual(len(counters), len(reviewers.RUST_REVIEWERS))
        for key, value in counters.items():
            self.assertGreaterEqual(value, 2)
        # For specific projects, select only the specified reviewers.
        saved_reviewers = reviewers.PROJ_REVIEWERS
        reviewers.PROJ_REVIEWERS = {
            "rust/crates/p1": "x@g.com",
            "rust/crates/p_any": ["x@g.com", "y@g.com"],
            "rust/crates/p_all": {"x@g.com", "y@g.com"},
        }
        counters = self.collect_reviewers(20, "external/rust/crates/p1")
        self.assertEqual(len(counters), 1)
        self.assertTrue(counters["r=x@g.com"], 20)
        counters = self.collect_reviewers(20, "external/rust/crates/p_any")
        self.assertEqual(len(counters), 2)
        self.assertGreater(counters["r=x@g.com"], 2)
        self.assertGreater(counters["r=y@g.com"], 2)
        self.assertTrue(counters["r=x@g.com"] + counters["r=y@g.com"], 20)
        counters = self.collect_reviewers(20, "external/rust/crates/p_all")
        counted = 0
        if "r=x@g.com,r=y@g.com" in counters:
            counted += counters["r=x@g.com,r=y@g.com"]
        if "r=y@g.com,r=x@g.com" in counters:
            counted += counters["r=y@g.com,r=x@g.com"]
        self.assertEqual(counted, 20)
        reviewers.PROJ_REVIEWERS = saved_reviewers


if __name__ == "__main__":
    unittest.main()
