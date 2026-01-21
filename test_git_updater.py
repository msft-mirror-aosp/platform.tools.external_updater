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
"""Unit tests for git_updater."""

import unittest
from pathlib import Path
from unittest import mock

# pylint: disable=import-error
import metadata_pb2  # type: ignore

import git_updater

# pylint: enable=import-error


class GitUpdaterTest(unittest.TestCase):

    @mock.patch("git_utils.get_sha_for_revision")
    def test_update_metadata_records_sha_for_tag(
            self, mock_get_sha_for_revision
    ) -> None:
        expected_version = "2.0.0"
        expected_sha = "expected-sha"
        mock_get_sha_for_revision.return_value = expected_sha

        old_identifier = metadata_pb2.Identifier(
            type="Git", value="repo-name", version="1.0.0"
        )

        updater = git_updater.GitUpdater(
            Path("/"),
            old_identifier,
            "1.0.0",
        )
        updater.set_new_version(expected_version)

        metadata = metadata_pb2.MetaData(
            third_party=metadata_pb2.ThirdPartyMetaData(identifier=[old_identifier])
        )
        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(
            updated_metadata.third_party.identifier[0].version, expected_sha
        )
        self.assertEqual(
            updated_metadata.third_party.identifier[0].closest_version,
            expected_version,
        )

    @mock.patch("git_utils.get_sha_for_revision")
    def test_update_metadata_handles_sha_version(
            self, mock_get_sha_for_revision
    ) -> None:
        expected_version = "e5fa44f2b31c1fb553b6021e7360d07d5d91ff5e"
        mock_get_sha_for_revision.return_value = "unexpected-sha"

        old_identifier = metadata_pb2.Identifier(
            type="Git", value="repo-name", version="1.0.0"
        )

        updater = git_updater.GitUpdater(
            Path("/"),
            old_identifier,
            "1.0.0",
        )
        updater.set_new_version(expected_version)

        metadata = metadata_pb2.MetaData(
            third_party=metadata_pb2.ThirdPartyMetaData(identifier=[old_identifier])
        )
        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(
            updated_metadata.third_party.identifier[0].version, expected_version
        )
        self.assertFalse(
            updated_metadata.third_party.identifier[0].HasField("closest_version")
        )
        mock_get_sha_for_revision.assert_not_called()

    @mock.patch("git_utils.get_sha_for_revision")
    def test_update_metadata_non_git_identifier(
            self, mock_get_sha_for_revision
    ) -> None:
        expected_version = "2.0.0"
        mock_get_sha_for_revision.return_value = "unexpected_sha"

        old_identifier = metadata_pb2.Identifier(
            type="Archive", value="repo-name", version="1.0.0"
        )
        updater = git_updater.GitUpdater(
            Path("/"),
            old_identifier,
            "1.0.0",
        )
        updater.set_new_version(expected_version)

        metadata = metadata_pb2.MetaData(
            third_party=metadata_pb2.ThirdPartyMetaData(identifier=[old_identifier])
        )
        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(
            updated_metadata.third_party.identifier[0].version, expected_version
        )
        self.assertFalse(
            updated_metadata.third_party.identifier[0].HasField("closest_version")
        )
        mock_get_sha_for_revision.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
