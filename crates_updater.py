# Copyright (C) 2020 The Android Open Source Project
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
"""Module to check updates from crates.io."""


import json
import re
import urllib.request

import archive_utils
import fileutils
import metadata_pb2    # pylint: disable=import-error
import updater_utils


CRATES_IO_URL_PATTERN = (r'^https:\/\/crates.io\/crates\/([-\w]+)')

CRATES_IO_URL_RE = re.compile(CRATES_IO_URL_PATTERN)

VERSION_PATTERN = r'([0-9]+)\.([0-9]+)\.([0-9]+)'

VERSION_MATCHER = re.compile(VERSION_PATTERN)


class CratesUpdater():
    """Updater for crates.io packages."""

    def __init__(self, url, proj_path, metadata):
        if url.type != metadata_pb2.URL.HOMEPAGE:
            raise ValueError('Only check HOMEPAGE url.')
        match = CRATES_IO_URL_RE.match(url.value)
        if match is None:
            raise ValueError('HOMEPAGE url must have crates.io.')
        self.proj_path = proj_path
        self.metadata = metadata
        self.package = match.group(1)
        self.upstream_url = url
        self.new_version = None
        self.dl_path = None

    def _get_version_numbers(self, version):
        match = VERSION_MATCHER.match(version)
        if match is not None:
            return tuple(int(match.group(i)) for i in range(1, 4))
        return (0, 0, 0)

    def _is_newer_version(self, prev_version, prev_id, check_version, check_id):
        """Return true if check_version+id is newer than prev_version+id."""
        return ((self._get_version_numbers(check_version), check_id) >
                (self._get_version_numbers(prev_version), prev_id))

    def check(self):
        """Checks crates.io and returns whether a new version is available."""
        url = 'https://crates.io/api/v1/crates/{}/versions'.format(self.package)
        with urllib.request.urlopen(url) as request:
            data = json.loads(request.read().decode())
        last_id = 0
        self.new_version = ''
        for v in data['versions']:
            if not v['yanked'] and self._is_newer_version(
                self.new_version, last_id, v['num'], int(v['id'])):
                last_id = int(v['id'])
                self.new_version = v['num']
                self.dl_path = v['dl_path']
        print('Current version: {}. Latest version: {}'.format(
            self.get_current_version(), self.new_version), end='')

    def get_current_version(self):
        """Returns the latest version name recorded in METADATA."""
        return self.metadata.third_party.version

    def get_latest_version(self):
        """Returns the latest version name in upstream."""
        return self.new_version

    def _write_metadata(self, path):
        updated_metadata = metadata_pb2.MetaData()
        updated_metadata.CopyFrom(self.metadata)
        updated_metadata.third_party.version = self.new_version
        fileutils.write_metadata(path, updated_metadata)

    def update(self):
        """Updates the package.

        Has to call check() before this function.
        """
        try:
            url = 'https://crates.io' + self.dl_path
            temporary_dir = archive_utils.download_and_extract(url)
            package_dir = archive_utils.find_archive_root(temporary_dir)
            self._write_metadata(package_dir)
            updater_utils.replace_package(package_dir, self.proj_path)
        finally:
            urllib.request.urlcleanup()
