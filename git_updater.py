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
        self.latest_commit = None

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
        commits = git_utils.get_commits_ahead(
            self.proj_path, self.upstream_remote_name + '/master',
            self.android_remote_name + '/master')

        if not commits:
            return False

        self.latest_commit = commits[0]
        commit_time = git_utils.get_commit_time(self.proj_path, commits[-1])
        time_behind = datetime.datetime.now() - commit_time
        print('{} commits ({} days) behind.'.format(
            len(commits), time_behind.days), end='')
        return True

    def _write_metadata(self, path):
        updated_metadata = metadata_pb2.MetaData()
        updated_metadata.CopyFrom(self.metadata)
        updated_metadata.third_party.version = self.latest_commit
        fileutils.write_metadata(path, updated_metadata)

    def update(self):
        """Updates the package.

        Has to call check() before this function.
        """
        # See whether we have a local upstream.
        branches = git_utils.list_remote_branches(
            self.proj_path, self.android_remote_name)
        upstreams = [
            branch for branch in branches if branch.startswith('upstream-')]
        if len(upstreams) == 1:
            merge_branch = '{}/{}'.format(
                self.android_remote_name, upstreams[0])
        elif not upstreams:
            merge_branch = 'update_origin/master'
        else:
            raise ValueError('Ambiguous upstream branch. ' + upstreams)

        upstream_branch = self.upstream_remote_name + '/master'

        commits = git_utils.get_commits_ahead(
            self.proj_path, merge_branch, upstream_branch)
        if commits:
            print('Warning! {} is {} commits ahead of {}. {}'.format(
                merge_branch, len(commits), upstream_branch, commits))

        commits = git_utils.get_commits_ahead(
            self.proj_path, upstream_branch, merge_branch)
        if commits:
            print('Warning! {} is {} commits behind of {}.'.format(
                merge_branch, len(commits), upstream_branch))

        self._write_metadata(self.proj_path)
        print("""
This tool only updates METADATA. Run the following command to update:
    git merge {merge_branch}

To check all local changes:
    git diff {merge_branch} HEAD
""".format(merge_branch=merge_branch))
