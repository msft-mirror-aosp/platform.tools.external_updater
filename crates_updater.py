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
from base_updater import Updater
import metadata_pb2  # type: ignore
import updater_utils

CRATES_IO_URL_PATTERN: str = (r'^https:\/\/crates.io\/crates\/([-\w]+)')

CRATES_IO_URL_RE: re.Pattern = re.compile(CRATES_IO_URL_PATTERN)


class CratesUpdater(Updater):
    """Updater for crates.io packages."""

    dl_path: str
    package: str

    def is_supported_url(self) -> bool:
        if self._old_url.type != metadata_pb2.URL.HOMEPAGE:
            return False
        match = CRATES_IO_URL_RE.match(self._old_url.value)
        if match is None:
            return False
        self.package = match.group(1)
        return True

    def check(self) -> None:
        """Checks crates.io and returns whether a new version is available."""
        url = "https://crates.io/api/v1/crates/" + self.package
        with urllib.request.urlopen(url) as request:
            data = json.loads(request.read().decode())
            self._new_ver = data["crate"]["max_version"]
        url = url + "/" + self._new_ver
        with urllib.request.urlopen(url) as request:
            data = json.loads(request.read().decode())
            self.dl_path = data["version"]["dl_path"]

    def update(self) -> None:
        """Updates the package.

        Has to call check() before this function.
        """
        try:
            url = 'https://crates.io' + self.dl_path
            temporary_dir = archive_utils.download_and_extract(url)
            package_dir = archive_utils.find_archive_root(temporary_dir)
            updater_utils.replace_package(package_dir, self._proj_path)
        finally:
            urllib.request.urlcleanup()
