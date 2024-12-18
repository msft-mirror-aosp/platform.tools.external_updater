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

import base_updater
import fileutils
import git_utils
import updater_utils
# pylint: disable=import-error
from color import Color, color_string
from manifest import Manifest
import metadata_pb2  # type: ignore


class GitUpdater(base_updater.Updater):
    """Updater for Git upstream."""
    UPSTREAM_REMOTE_NAME: str = "update_origin"

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

        latest_sha = self.current_head_of_upstream_default_branch()
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
        return git_utils.get_sha_for_branch(
            self._proj_path, self.UPSTREAM_REMOTE_NAME + '/' + branch)

    def update(self) -> None:
        """Updates the package.
        Has to call check() before this function.
        """
        print(f"Running `git merge {self._new_identifier.version}`...")
        git_utils.merge(self._proj_path, self._new_identifier.version)

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
