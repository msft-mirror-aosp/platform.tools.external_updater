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
import git_utils
# pylint: disable=import-error
import metadata_pb2  # type: ignore
import updater_utils


class GitUpdater(base_updater.Updater):
    """Updater for Git upstream."""
    UPSTREAM_REMOTE_NAME: str = "update_origin"

    def is_supported_url(self) -> bool:
        return git_utils.is_valid_url(self._proj_path, self._old_url.value)

    def _setup_remote(self) -> None:
        remotes = git_utils.list_remotes(self._proj_path)
        current_remote_url = None
        android_remote_name: str | None = None
        for name, url in remotes.items():
            if name == self.UPSTREAM_REMOTE_NAME:
                current_remote_url = url

            if '/platform/external/' in url:
                android_remote_name = name

        if android_remote_name is None:
            remotes_formatted = "\n".join(f"{k} {v}" for k, v in remotes.items())
            raise RuntimeError(
                f"Could not determine android remote for {self._proj_path}. Tried:\n"
                f"{remotes_formatted}")

        if current_remote_url is not None and current_remote_url != self._old_url.value:
            git_utils.remove_remote(self._proj_path, self.UPSTREAM_REMOTE_NAME)
            current_remote_url = None

        if current_remote_url is None:
            git_utils.add_remote(self._proj_path, self.UPSTREAM_REMOTE_NAME,
                                 self._old_url.value)

        git_utils.fetch(self._proj_path,
                        [self.UPSTREAM_REMOTE_NAME, android_remote_name])

    def check(self) -> None:
        """Checks upstream and returns whether a new version is available."""
        self._setup_remote()
        if git_utils.is_commit(self._old_ver):
            # Update to remote head.
            self._check_head()
        else:
            # Update to latest version tag.
            self._check_tag()

    def _check_tag(self) -> None:
        tags = git_utils.list_remote_tags(self._proj_path,
                                          self.UPSTREAM_REMOTE_NAME)
        self._new_ver = updater_utils.get_latest_version(self._old_ver, tags)

    def _check_head(self) -> None:
        branch = git_utils.detect_default_branch(self._proj_path,
                                                 self.UPSTREAM_REMOTE_NAME)
        self._new_ver = git_utils.get_sha_for_branch(
            self._proj_path, self.UPSTREAM_REMOTE_NAME + '/' + branch)

    def update(self, skip_post_update: bool) -> None:
        """Updates the package.
        Has to call check() before this function.
        """
        print(f"Running `git merge {self._new_ver}`...")
        git_utils.merge(self._proj_path, self._new_ver)
        if not skip_post_update:
            updater_utils.run_post_update(self._proj_path, self._proj_path)