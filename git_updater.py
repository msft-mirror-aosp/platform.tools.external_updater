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


import datetime

import fileutils
import git_utils
import metadata_pb2    # pylint: disable=import-error
import updater_utils


class GitUpdater():
    """Updater for Git upstream."""

    def __init__(self, url, proj_path, metadata):
        if url.type != metadata_pb2.URL.GIT:
            raise ValueError('Only support GIT upstream.')
        self.proj_path = proj_path
        self.metadata = metadata
        self.upstream_url = url
        self.upstream_remote_name = None
        self.android_remote_name = None
        self.new_version = None
        self.merge_from = None

    def _setup_remote(self):
        remotes = git_utils.list_remotes(self.proj_path)
        for name, url in remotes.items():
            if url == self.upstream_url.value:
                self.upstream_remote_name = name

            # Guess android remote name.
            if '/platform/external/' in url:
                self.android_remote_name = name

        if self.upstream_remote_name is None:
            self.upstream_remote_name = "update_origin"
            git_utils.add_remote(self.proj_path, self.upstream_remote_name,
                                 self.upstream_url.value)

        git_utils.fetch(self.proj_path,
                        [self.upstream_remote_name, self.android_remote_name])

    def check(self):
        """Checks upstream and returns whether a new version is available."""

        self._setup_remote()
        if git_utils.is_commit(self.metadata.third_party.version):
            # Update to remote head.
            return self._check_head()

        # Update to latest version tag.
        return self._check_tag()

    def _check_tag(self):
        tags = git_utils.list_remote_tags(self.proj_path,
                                          self.upstream_remote_name)
        current_ver = self.metadata.third_party.version
        self.new_version = updater_utils.get_latest_version(
            current_ver, tags)
        self.merge_from = self.new_version
        print('Current version: {}. Latest version: {}'.format(
            current_ver, self.new_version), end='')
        return self.new_version != current_ver

    def _check_head(self):
        commits = git_utils.get_commits_ahead(
            self.proj_path, self.upstream_remote_name + '/master',
            self.android_remote_name + '/master')

        if not commits:
            return False

        self.new_version = commits[0]

        # See whether we have a local upstream.
        branches = git_utils.list_remote_branches(
            self.proj_path, self.android_remote_name)
        upstreams = [
            branch for branch in branches if branch.startswith('upstream-')]
        if upstreams:
            self.merge_from = '{}/{}'.format(
                self.android_remote_name, upstreams[0])
        else:
            self.merge_from = 'update_origin/master'

        commit_time = git_utils.get_commit_time(self.proj_path, commits[-1])
        time_behind = datetime.datetime.now() - commit_time
        print('{} commits ({} days) behind.'.format(
            len(commits), time_behind.days), end='')
        return True

    def _write_metadata(self, path):
        updated_metadata = metadata_pb2.MetaData()
        updated_metadata.CopyFrom(self.metadata)
        updated_metadata.third_party.version = self.new_version
        fileutils.write_metadata(path, updated_metadata)

    def update(self):
        """Updates the package.

        Has to call check() before this function.
        """
        upstream_branch = self.upstream_remote_name + '/master'

        commits = git_utils.get_commits_ahead(
            self.proj_path, self.merge_from, upstream_branch)
        if commits:
            print('{} is {} commits ahead of {}. {}'.format(
                self.merge_from, len(commits), upstream_branch, commits))

        commits = git_utils.get_commits_ahead(
            self.proj_path, upstream_branch, self.merge_from)
        if commits:
            print('{} is {} commits behind of {}.'.format(
                self.merge_from, len(commits), upstream_branch))

        self._write_metadata(self.proj_path)
        git_utils.merge(self.proj_path, self.merge_from)
