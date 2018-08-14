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
"""Module to update packages from GitHub archive."""


import json
import re
import urllib.request

import archive_utils
import fileutils
import metadata_pb2    # pylint: disable=import-error
import updater_utils

GITHUB_URL_PATTERN = (r'^https:\/\/github.com\/([-\w]+)\/([-\w]+)\/' +
                      r'(releases\/download\/|archive\/)')
GITHUB_URL_RE = re.compile(GITHUB_URL_PATTERN)


def _edit_distance(str1, str2):
    prev = list(range(0, len(str2) + 1))
    for i, chr1 in enumerate(str1):
        cur = [i + 1]
        for j, chr2 in enumerate(str2):
            if chr1 == chr2:
                cur.append(prev[j])
            else:
                cur.append(min(prev[j + 1], prev[j], cur[j]) + 1)
        prev = cur
    return prev[len(str2)]


def choose_best_url(urls, previous_url):
    """Returns the best url to download from a list of candidate urls.

    This function calculates similarity between previous url and each of new
    urls. And returns the one best matches previous url.

    Similarity is measured by editing distance.

    Args:
        urls: Array of candidate urls.
        previous_url: String of the url used previously.

    Returns:
        One url from `urls`.
    """
    return min(urls, default=None,
               key=lambda url: _edit_distance(
                   url, previous_url))


class GithubArchiveUpdater():
    """Updater for archives from GitHub.

    This updater supports release archives in GitHub. Version is determined by
    release name in GitHub.
    """

    VERSION_FIELD = 'tag_name'

    def __init__(self, url, proj_path, metadata):
        self.proj_path = proj_path
        self.metadata = metadata
        self.old_url = url
        self.owner = None
        self.repo = None
        self.data = None
        self._parse_url(url)

    def _parse_url(self, url):
        if url.type != metadata_pb2.URL.ARCHIVE:
            raise ValueError('Only archive url from Github is supported.')
        match = GITHUB_URL_RE.match(url.value)
        if match is None:
            raise ValueError('Url format is not supported.')
        try:
            self.owner, self.repo = match.group(1, 2)
        except IndexError:
            raise ValueError('Url format is not supported.')

    def _get_latest_version(self):
        """Checks upstream and returns the latest version name we found."""

        url = 'https://api.github.com/repos/{}/{}/releases/latest'.format(
            self.owner, self.repo)
        with urllib.request.urlopen(url) as request:
            self.data = json.loads(request.read().decode())
        return self.data[self.VERSION_FIELD]

    def _get_current_version(self):
        """Returns the latest version name recorded in METADATA."""
        return self.metadata.third_party.version

    def _write_metadata(self, url, path):
        updated_metadata = metadata_pb2.MetaData()
        updated_metadata.CopyFrom(self.metadata)
        updated_metadata.third_party.version = self.data[self.VERSION_FIELD]
        for metadata_url in updated_metadata.third_party.url:
            if metadata_url == self.old_url:
                metadata_url.value = url
        fileutils.write_metadata(path, updated_metadata)

    def check(self):
        """Checks update for package.

        Returns True if a new version is available.
        """
        latest = self._get_latest_version()
        current = self._get_current_version()
        print('Current version: {}. Latest version: {}'.format(
            current, latest), end='')
        return current != latest

    def update(self):
        """Updates the package.

        Has to call check() before this function.
        """

        supported_assets = [
            a['browser_download_url'] for a in self.data['assets']
            if archive_utils.is_supported_archive(a['browser_download_url'])]

        # Adds source code urls.
        supported_assets.append(
            'https://github.com/{}/{}/archive/{}.tar.gz'.format(
                self.owner, self.repo, self.data.get('tag_name')))
        supported_assets.append(
            'https://github.com/{}/{}/archive/{}.zip'.format(
                self.owner, self.repo, self.data.get('tag_name')))

        latest_url = choose_best_url(supported_assets, self.old_url.value)

        temporary_dir = None
        try:
            temporary_dir = archive_utils.download_and_extract(latest_url)
            package_dir = archive_utils.find_archive_root(temporary_dir)
            self._write_metadata(latest_url, package_dir)
            updater_utils.replace_package(package_dir, self.proj_path)
        finally:
            # Don't remove the temporary directory, or it'll be impossible
            # to debug the failure...
            # shutil.rmtree(temporary_dir, ignore_errors=True)
            urllib.request.urlcleanup()
