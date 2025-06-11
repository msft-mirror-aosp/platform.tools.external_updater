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
"""Module to check updates from Git upstream."""

from pathlib import Path
from string import Template

import metadata_pb2  # type: ignore

import base_updater
import fileutils
import git_utils
import updater_utils
# pylint: disable=import-error
from color import Color, color_string
from manifest import Manifest

BUGANIZER_LINK = "go/android-external-updater-bug"
ARCHIVE_WARNING = f"This is most likely an Archive, not Git. Please consider " \
                  f"editing the METADATA file or filing a bug {BUGANIZER_LINK}."

ACCURATE_VERSION_IN_METADATA = "The version in METADATA file is accurate."

INACCURATE_VERSION_IN_METADATA = f"The version in the METADATA file is not " \
                                 f"correct. We suspect that it should be " \
                                 f"$real_version. Please consider editing the" \
                                 f" METADATA file or filing a bug" \
                                 f"{BUGANIZER_LINK}."


class GitUpdater(base_updater.Updater):
    """Updater for Git upstream."""
    UPSTREAM_REMOTE_NAME: str = "update_origin"

    def __init__(self, proj_path: Path, old_identifier: metadata_pb2.Identifier,
        old_ver: str) -> None:
        super().__init__(proj_path, old_identifier, old_ver)
        non_default_branch = git_utils.find_non_default_branch(old_identifier.value)
        if non_default_branch is not None:
            self.upstream_branch = non_default_branch
            self._identifier_with_branch = old_identifier.value
            old_identifier.value = old_identifier.value.strip(f'tree/{self.upstream_branch}')
        else:
            self.upstream_branch = git_utils.detect_default_branch(proj_path, self.UPSTREAM_REMOTE_NAME)

    def is_supported_url(self) -> bool:
        return git_utils.is_valid_url(self._proj_path, self._old_identifier.value)

    def setup_remote(self) -> None:
        remotes = git_utils.list_remotes(self._proj_path)
        current_remote_url = None
        for name, url in remotes.items():
            if name == self.UPSTREAM_REMOTE_NAME:
                current_remote_url = url

        if current_remote_url is not None and current_remote_url != self._old_identifier.value:
            git_utils.remove_remote(self._proj_path, self.UPSTREAM_REMOTE_NAME)
            current_remote_url = None

        if current_remote_url is None:
            git_utils.add_remote(self._proj_path, self.UPSTREAM_REMOTE_NAME,
                                 self._old_identifier.value)

        git_utils.fetch(self._proj_path, self.UPSTREAM_REMOTE_NAME)

    def set_custom_version(self, custom_version: str) -> None:
        super().set_custom_version(custom_version)
        if not git_utils.list_branches_with_commit(self._proj_path, custom_version, self.UPSTREAM_REMOTE_NAME):
            raise RuntimeError(
                f"Can not upgrade to {custom_version}. This version does not belong to any branches.")

    def set_new_versions_for_commit(self, latest_sha: str, latest_tag: str | None = None) -> None:
        self._new_identifier.version = latest_sha
        if latest_tag is not None and git_utils.is_ancestor(
            self._proj_path, self._old_identifier.version, latest_tag):
            self._alternative_new_ver = latest_tag

    def set_new_versions_for_tag(self, latest_sha: str, latest_tag: str | None = None) -> None:
        if latest_tag is None:
            project = fileutils.canonicalize_project_path(self.project_path)
            print(color_string(
                f"{project} is currently tracking upstream tags but either no "
                "tags were found in the upstream repository or the tag does not "
                "belong to any branch. No latest tag available", Color.STALE
            ))
            self._new_identifier.ClearField("version")
            self._alternative_new_ver = latest_sha
            return
        self._new_identifier.version = latest_tag
        if git_utils.is_ancestor(
            self._proj_path, self._old_identifier.version, latest_sha):
            self._alternative_new_ver = latest_sha

    def check(self) -> None:
        """Checks upstream and returns whether a new version is available."""
        self.setup_remote()

        latest_sha = git_utils.get_sha_for_revision(
            self._proj_path, self.UPSTREAM_REMOTE_NAME + '/' + self.upstream_branch)
        latest_tag = self.latest_tag_of_upstream()

        if git_utils.is_commit(self._old_identifier.version):
            self.set_new_versions_for_commit(latest_sha, latest_tag)
        else:
            self.set_new_versions_for_tag(latest_sha, latest_tag)

    def latest_tag_of_upstream(self) -> str | None:
        tags = git_utils.list_remote_tags(self._proj_path, self.UPSTREAM_REMOTE_NAME)
        if not tags:
            return None

        parsed_tags = [updater_utils.parse_remote_tag(tag) for tag in tags]
        tag = updater_utils.get_latest_stable_release_tag(self._old_identifier.version, parsed_tags)
        if not git_utils.list_branches_with_commit(self._proj_path, tag, self.UPSTREAM_REMOTE_NAME):
            return None

        return tag

    def current_head_of_upstream_default_branch(self) -> str:
        branch = git_utils.detect_default_branch(self._proj_path,
                                                 self.UPSTREAM_REMOTE_NAME)
        return git_utils.get_sha_for_revision(
            self._proj_path, self.UPSTREAM_REMOTE_NAME + '/' + branch)

    def update(self) -> None:
        """Updates the package.
        Has to call check() before this function.
        """
        print(f"Running 'git merge {self._new_identifier.version}'...")
        git_utils.merge(self._proj_path, self._new_identifier.version)

    def is_metadata_accurate(self, common_ancestor: str) -> bool:
        sha_of_claimed_version = git_utils.get_sha_for_revision(self._proj_path, self._old_identifier.version)
        if sha_of_claimed_version == common_ancestor:
            return True
        return False

    def find_real_version(self, common_ancestor: str) -> str:
        read_version = f"SHA {common_ancestor}"
        tag = git_utils.get_tag_for_revision(self._proj_path, common_ancestor)
        if tag is not None:
            read_version = f"tag {tag} or SHA {common_ancestor}"
        return read_version

    def find_common_ancestor(self) -> str | None:
        """Finds the most recent common ancestor of Android's main branch and upstream's default branch."""
        upstream_default_branch = git_utils.detect_default_branch(self._proj_path, self.UPSTREAM_REMOTE_NAME)
        local_remote_name = git_utils.determine_remote_name(self._proj_path)
        local_default_branch = git_utils.detect_default_branch(self._proj_path, local_remote_name)
        android_default_branch = local_remote_name + "/" + local_default_branch
        upstream_default_branch = self.UPSTREAM_REMOTE_NAME + "/" + upstream_default_branch
        common_ancestor = git_utils.merge_base(self._proj_path, android_default_branch, upstream_default_branch)
        return common_ancestor

    def validate(self) -> None:
        """Checks whether Android version is what it claims to be."""
        super().validate()

        common_ancestor = self.find_common_ancestor()

        if common_ancestor is None:
            print(ARCHIVE_WARNING)
            return

        is_metadata_accurate = self.is_metadata_accurate(common_ancestor)
        if is_metadata_accurate:
            print(color_string(ACCURATE_VERSION_IN_METADATA, Color.FRESH))
            return
        real_version = self.find_real_version(common_ancestor)
        template = Template(INACCURATE_VERSION_IN_METADATA)
        print(template.substitute(real_version=real_version))
        return

    def _determine_android_fetch_ref(self) -> str:
        """Returns the ref that should be fetched from the android remote."""
        # It isn't particularly efficient to reparse the tree for every
        # project, but we don't guarantee that all paths passed to updater.sh
        # are actually in the same tree so it wouldn't necessarily be correct
        # to do this once at the top level. This isn't the slow part anyway,
        # so it can be dealt with if that ever changes.
        root = fileutils.find_tree_containing(self._proj_path)
        manifest = Manifest.for_tree(root)
        manifest_path = str(self._proj_path.relative_to(root))
        try:
            project = manifest.project_with_path(manifest_path)
        except KeyError as ex:
            raise RuntimeError(
                f"Did not find {manifest_path} in {manifest.path} (tree root is {root})"
            ) from ex
        return project.revision
