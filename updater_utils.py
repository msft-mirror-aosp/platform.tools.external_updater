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
"""Helper functions for updaters."""

import os
import subprocess
import sys


def create_updater(metadata, proj_path, updaters):
    """Creates corresponding updater object for a project.

    Args:
      metadata: Parsed proto for METADATA file.
      proj_path: Absolute path for the project.

    Returns:
      An updater object.

    Raises:
      ValueError: Occurred when there's no updater for all urls.
    """
    for url in metadata.third_party.url:
        for updater in updaters:
            try:
                return updater(url, proj_path, metadata)
            except ValueError:
                pass

    raise ValueError('No supported URL.')


def replace_package(source_dir, target_dir):
    """Invokes a shell script to prepare and update a project.

    Args:
      source_dir: Path to the new downloaded and extracted package.
      target_dir: The path to the project in Android source tree.
    """

    print('Updating {} using {}.'.format(target_dir, source_dir))
    script_path = os.path.join(
        os.path.dirname(
            sys.argv[0]),
        'update_package.sh')
    subprocess.check_call(['bash', script_path, source_dir, target_dir])
