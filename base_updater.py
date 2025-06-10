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
"""Base class for all updaters."""

import re
from pathlib import Path

# pylint: disable=import-error
import metadata_pb2  # type: ignore

import fileutils
import git_utils
from color import Color, color_string

VERSION_MATCH_PATTERN = r"^[^\d]*([\d].*)$"
VERSION_WITH_UNDERSCORES_PATTERN = r"^[^\d]*([\d+_]+[\d])$"
VERSION_WITH_DASHES_PATTERN = r"^[^\d]*([\d+-]+[\d])$"


def _sanitize_version_for_cpe(version: str) -> str:
    """Sanitizes a version in SemVer format by removing the prefix before the first digit.

    This is necessary to match the CPE (go/metadata-cpe) version attribute
    against the one in the National Vulnerability Database (NVD)."""
    version_match = re.match(VERSION_MATCH_PATTERN, version)
    version_with_underscore_match = re.match(VERSION_WITH_UNDERSCORES_PATTERN, version)
    version_with_dashes_match = re.match(VERSION_WITH_DASHES_PATTERN, version)
    if version_with_underscore_match is not None:
        return version_with_underscore_match.group(1).replace("_", ".")
    if version_with_dashes_match is not None:
        return version_with_dashes_match.group(1).replace("-", ".")
    if version_match is not None:
        return version_match.group(1)
    return version


class Updater:
    """Base Updater that defines methods common for all updaters."""
    def __init__(self, proj_path: Path, old_identifier: metadata_pb2.Identifier,
                 old_ver: str) -> None:
        self._proj_path = fileutils.get_absolute_project_path(proj_path)
        self._old_identifier = old_identifier
        self._old_identifier.version = old_identifier.version if old_identifier.version else old_ver

        self._new_identifier = metadata_pb2.Identifier()
        self._new_identifier.CopyFrom(old_identifier)

        self._alternative_new_ver: str | None = None
        self._identifier_with_branch: str | None = None
        self._has_errors = False

    def is_supported_url(self) -> bool:
        """Returns whether the url is supported."""
        raise NotImplementedError()

    def setup_remote(self) -> None:
        raise NotImplementedError()

    def validate(self) -> None:
        """Checks whether Android version is what it claims to be."""
        self.setup_remote()
        diff = git_utils.diff_stat(self._proj_path, 'a', self._old_identifier.version)
        print("No diff" if len(diff) == 0 else color_string(diff, Color.STALE))

    def check(self) -> None:
        """Checks whether a new version is available."""
        raise NotImplementedError()

    def update(self) -> Path | None:
        """Updates the package.

        Has to call check() before this function. Returns either the temporary
        dir it stored the old version in after upgrading or None.
        """
        raise NotImplementedError()

    def rollback(self) -> bool:
        """Rolls the current update back.

        This is an optional operation.  Returns whether the rollback succeeded.
        """
        return False

    def update_metadata(self, metadata: metadata_pb2.MetaData) -> metadata_pb2:
        """Rewrites the metadata file."""
        updated_metadata = metadata_pb2.MetaData()
        updated_metadata.CopyFrom(metadata)
        updated_metadata.third_party.ClearField("version")
        for identifier in updated_metadata.third_party.identifier:
            if identifier == self.current_identifier:
                identifier.CopyFrom(self.latest_identifier)
                # Reset identifier.value to one that contains the branch name
                if self.identifier_with_branch is not None:
                    identifier.value = self.identifier_with_branch
        version_is_sha= git_utils.is_commit(self.latest_version)
        # TODO: b/412615684 - Implement a way to track the closest version
        # associated with a package that uses a commit hash as the version. For
        # example, in a "Git" Identifier that tracks the version as a git
        # commit, the closest version would be the git tag. This would allow CPE
        # tags to be updated with the closest version if the version is a commit
        # hash.

        # Update CPE tags with the latest version (go/metadata-cpe).
        if updated_metadata.third_party.HasField("security") and not version_is_sha:
            copy_of_security = metadata_pb2.Security()
            copy_of_security.CopyFrom(updated_metadata.third_party.security)
            for tag in copy_of_security.tag:
                old_tag = tag
                updated_version = _sanitize_version_for_cpe(self.latest_version)
                if tag.startswith("NVD-CPE2.3"):
                    cpe_parts = tag.split(":")
                    if len(cpe_parts) > 5:
                        new_tag = cpe_parts[:5] + [updated_version] + cpe_parts[6:]
                    elif len(cpe_parts) == 5:
                        new_tag = cpe_parts + [updated_version]
                    else:
                        continue
                    new_tag = ":".join(new_tag)
                    updated_metadata.third_party.security.tag.remove(old_tag)
                    updated_metadata.third_party.security.tag.append(new_tag)
        return updated_metadata

    @property
    def project_path(self) -> Path:
        """Gets absolute path to the project."""
        return self._proj_path

    @property
    def current_version(self) -> str:
        """Gets the current version."""
        return self._old_identifier.version

    @property
    def current_identifier(self) -> metadata_pb2.Identifier:
        """Gets the current identifier."""
        return self._old_identifier

    @property
    def latest_version(self) -> str:
        """Gets latest version."""
        return self._new_identifier.version

    @property
    def latest_identifier(self) -> metadata_pb2.Identifier:
        """Gets identifier for latest version."""
        return self._new_identifier

    @property
    def has_errors(self) -> bool:
        """Gets whether this update had an error."""
        return self._has_errors

    @property
    def alternative_latest_version(self) -> str | None:
        """Gets alternative latest version."""
        return self._alternative_new_ver

    @property
    def identifier_with_branch(self) -> str | None:
        """Gets the identifier with branch name attached to it."""
        return self._identifier_with_branch

    def refresh_without_upgrading(self) -> None:
        """Uses current version and url as the latest to refresh project."""
        self._new_identifier.version = self._old_identifier.version
        self._new_identifier.value = self._old_identifier.value

    def set_new_version(self, version: str) -> None:
        """Uses the passed version as the latest to upgrade project."""
        self._new_identifier.version = version

    def set_custom_version(self, custom_version: str) -> None:
        """Uses the passed version as the latest to upgrade project if the
        passed version is not older than the current version."""
        if git_utils.is_ancestor(self._proj_path, self._old_identifier.version, custom_version):
            self._new_identifier.version = custom_version
        else:
            raise RuntimeError(
                f"Cannot upgrade to {custom_version}. "
                f"Either the current version is newer than {custom_version} "
                f"or the current version in the METADATA file is not correct.")
