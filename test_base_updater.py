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
"""Unit tests for base_updater."""

import unittest
from pathlib import Path

import base_updater
# pylint: disable=import-error
import metadata_pb2  # type: ignore
# pylint: enable=import-error


class UpdaterTest(unittest.TestCase):
    """Unit tests for Updater."""

    def test_current_version(self) -> None:
        """Tests that Updater.current_version returns the appropriate value."""
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            metadata_pb2.Identifier(),
            "old version",
        )
        self.assertEqual(updater.current_version, "old version")

        identifier = metadata_pb2.Identifier()
        identifier.version = "old version"
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            identifier,
            "",
        )
        self.assertEqual(updater.current_version, "old version")

    def test_update_metadata_with_cpe_tag(self) -> None:
        """Tests that Updater.update_metadata returns the updated metadata with updated version in CPE tags."""
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            metadata_pb2.Identifier(),
            "1.0.0",
        )
        metadata = metadata_pb2.MetaData()
        third_party = metadata_pb2.ThirdPartyMetaData()
        security = metadata_pb2.Security()
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:1.0.0:*:*:*:*:*:*:*"
        )
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product"
        )
        third_party.security.CopyFrom(security)
        metadata.third_party.CopyFrom(third_party)
        updater.set_new_version("v2.0.1")

        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(updater.latest_version, "v2.0.1")
        self.assertEqual(
            updated_metadata.third_party.security.tag[0],
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:2.0.1:*:*:*:*:*:*:*",
        )
        self.assertEqual(
            updated_metadata.third_party.security.tag[1],
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product:2.0.1",
        )

    def test_update_metadata_with_cpe_tags_and_version_with_non_numeric_prefix(self) -> None:
        """Tests that Updater.update_metadata returns the updated metadata with updated sanitized version in CPE tags."""
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            metadata_pb2.Identifier(),
            "1.0.0",
        )
        metadata = metadata_pb2.MetaData()
        third_party = metadata_pb2.ThirdPartyMetaData()
        security = metadata_pb2.Security()
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:1.0.0:*:*:*:*:*:*:*"
        )
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product"
        )
        third_party.security.CopyFrom(security)
        metadata.third_party.CopyFrom(third_party)
        updater.set_new_version("test-2.0.1")

        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(updater.latest_version, "test-2.0.1")
        self.assertEqual(
            updated_metadata.third_party.security.tag[0],
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:2.0.1:*:*:*:*:*:*:*",
        )
        self.assertEqual(
            updated_metadata.third_party.security.tag[1],
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product:2.0.1",
        )

    def test_update_metadata_with_cpe_tags_and_sha_version(self) -> None:
        """Tests that Updater.update_metadata returns the updated metadata and does not update CPE tags with SHA version."""
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            metadata_pb2.Identifier(),
            "1.0.0",
        )
        metadata = metadata_pb2.MetaData()
        third_party = metadata_pb2.ThirdPartyMetaData()
        security = metadata_pb2.Security()
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:1.0.0:*:*:*:*:*:*:*"
        )
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product"
        )
        third_party.security.CopyFrom(security)
        metadata.third_party.CopyFrom(third_party)
        updater.set_new_version("e5fa44f2b31c1fb553b6021e7360d07d5d91ff5e")

        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(updater.latest_version, "e5fa44f2b31c1fb553b6021e7360d07d5d91ff5e")
        self.assertEqual(
            updated_metadata.third_party.security.tag[0],
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:1.0.0:*:*:*:*:*:*:*",
        )
        self.assertEqual(
            updated_metadata.third_party.security.tag[1],
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product",
        )

    def test_update_metadata_with_cpe_tags_and_version_with_underscores(self) -> None:
        """Tests that Updater.update_metadata returns the updated metadata with updated sanitized version in CPE tags."""
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            metadata_pb2.Identifier(),
            "1.0.0",
        )
        metadata = metadata_pb2.MetaData()
        third_party = metadata_pb2.ThirdPartyMetaData()
        security = metadata_pb2.Security()
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:1.0.0:*:*:*:*:*:*:*"
        )
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product"
        )
        third_party.security.CopyFrom(security)
        metadata.third_party.CopyFrom(third_party)
        updater.set_new_version("test-2_0_1")

        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(updater.latest_version, "test-2_0_1")
        self.assertEqual(
            updated_metadata.third_party.security.tag[0],
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:2.0.1:*:*:*:*:*:*:*",
        )
        self.assertEqual(
            updated_metadata.third_party.security.tag[1],
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product:2.0.1",
        )

    def test_update_metadata_with_cpe_tags_and_version_with_dashes(self) -> None:
        """Tests that Updater.update_metadata returns the updated metadata with updated sanitized version in CPE tags."""
        updater = base_updater.Updater(
            # This is absolute so we get the fast path out of the path canonicalization
            # that would otherwise require us to define ANDROID_BUILD_TOP or run from a
            # temp repo tree.
            Path("/"),
            metadata_pb2.Identifier(),
            "1.0.0",
        )
        metadata = metadata_pb2.MetaData()
        third_party = metadata_pb2.ThirdPartyMetaData()
        security = metadata_pb2.Security()
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:1.0.0:*:*:*:*:*:*:*"
        )
        security.tag.append(
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product"
        )
        third_party.security.CopyFrom(security)
        metadata.third_party.CopyFrom(third_party)
        updater.set_new_version("test-2-0-1")

        updated_metadata = updater.update_metadata(metadata)

        self.assertEqual(updater.latest_version, "test-2-0-1")
        self.assertEqual(
            updated_metadata.third_party.security.tag[0],
            "NVD-CPE2.3:cpe:/a:test1_vendor:test1_product:2.0.1:*:*:*:*:*:*:*",
        )
        self.assertEqual(
            updated_metadata.third_party.security.tag[1],
            "NVD-CPE2.3:cpe:/a:test2_vendor:test2_product:2.0.1",
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
