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
    upstream_remote_name: str
    android_remote_name: str

    def is_supported_url(self) -> bool:
        return self._old_url.type == metadata_pb2.URL.GIT

    def _setup_remote(self) -> None:
        remotes = git_utils.list_remotes(self._proj_path)
        upstream_remote_name = None
        for name, url in remotes.items():
            if url == self._old_url.value:
                upstream_remote_name = name

            # Guess android remote name.
            if '/platform/external/' in url:
                self.android_remote_name = name

        if upstream_remote_name is None:
            upstream_remote_name = "update_origin"
            git_utils.add_remote(self._proj_path, upstream_remote_name,
                                 self._old_url.value)
        self.upstream_remote_name = upstream_remote_name

        git_utils.fetch(self._proj_path,
                        [self.upstream_remote_name, self.android_remote_name])

    def check(self) -> None:
        """Checks upstream and returns whether a new version is available."""
        self._setup_remote()
        if git_utils.is_commit(self._old_ver):
            # Update to remote head.
            self._check_head()
        else:
            # Update to latest version tag.
            self._check_tag()

    def _check_tag(self):
        tags = git_utils.list_remote_tags(self._proj_path,
                                          self.upstream_remote_name)
        self._new_ver = updater_utils.get_latest_version(self._old_ver, tags)

    def _check_head(self):
        self._new_ver = git_utils.get_sha_for_branch(
            self._proj_path, self.upstream_remote_name + '/master')

    def update(self) -> None:
        """Updates the package.

        Has to call check() before this function.
        """
        print(f"Running `git merge {self._new_ver}`...")
        git_utils.merge(self._proj_path, self._new_ver)
