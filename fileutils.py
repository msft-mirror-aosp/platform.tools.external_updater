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
"""Tool functions to deal with files."""

import datetime
import os
from pathlib import Path
import textwrap

# pylint: disable=import-error
from google.protobuf import text_format  # type: ignore

# pylint: disable=import-error
import metadata_pb2  # type: ignore

ANDROID_TOP = Path(os.environ.get('ANDROID_BUILD_TOP', os.getcwd()))
EXTERNAL_PATH = ANDROID_TOP / 'external'

METADATA_FILENAME = 'METADATA'


def get_absolute_project_path(proj_path: Path) -> Path:
    """Gets absolute path of a project.

    Path resolution starts from external/.
    """
    return EXTERNAL_PATH / proj_path


def get_metadata_path(proj_path: Path) -> Path:
    """Gets the absolute path of METADATA for a project."""
    return get_absolute_project_path(proj_path) / METADATA_FILENAME


def get_relative_project_path(proj_path: Path) -> Path:
    """Gets the relative path of a project starting from external/."""
    return get_absolute_project_path(proj_path).relative_to(EXTERNAL_PATH)


def canonicalize_project_path(proj_path: Path) -> Path:
  """Returns the canonical representation of the project path.

  For paths that are in the same tree as external_updater (the common case), the
  canonical path is the path of the project relative to //external.

  For paths that are in a different tree (an uncommon case used for updating projects
  in other builds such as the NDK), the canonical path is the absolute path.
  """
  try:
      return get_relative_project_path(proj_path)
  except ValueError:
      # A less common use case, but the path might be to a non-local tree, in which case
      # the path will not be relative to our tree. This happens when using
      # external_updater in another project like the NDK or rr.
      if proj_path.is_absolute():
        return proj_path

      # Not relative to //external, and not an absolute path. This case hasn't existed
      # before, so it has no canonical form.
      raise ValueError(
        f"{proj_path} must be either an absolute path or relative to {EXTERNAL_PATH}"
      )


def read_metadata(proj_path: Path) -> metadata_pb2.MetaData:
    """Reads and parses METADATA file for a project.

    Args:
      proj_path: Path to the project.

    Returns:
      Parsed MetaData proto.

    Raises:
      text_format.ParseError: Occurred when the METADATA file is invalid.
      FileNotFoundError: Occurred when METADATA file is not found.
    """

    with get_metadata_path(proj_path).open('r') as metadata_file:
        metadata = metadata_file.read()
        return text_format.Parse(metadata, metadata_pb2.MetaData())


def write_metadata(proj_path: Path, metadata: metadata_pb2.MetaData, keep_date: bool) -> None:
    """Writes updated METADATA file for a project.

    This function updates last_upgrade_date in metadata and write to the project
    directory.

    Args:
      proj_path: Path to the project.
      metadata: The MetaData proto to write.
      keep_date: Do not change date.
    """

    if not keep_date:
        date = metadata.third_party.last_upgrade_date
        now = datetime.datetime.now()
        date.year = now.year
        date.month = now.month
        date.day = now.day
    rel_proj_path = get_relative_project_path(proj_path)
    usage_hint = textwrap.dedent(f"""\
    # This project was upgraded with external_updater.
    # Usage: tools/external_updater/updater.sh update {rel_proj_path}
    # For more info, check https://cs.android.com/android/platform/superproject/+/master:tools/external_updater/README.md

    """)
    text_metadata = usage_hint + text_format.MessageToString(metadata)
    with get_metadata_path(proj_path).open('w') as metadata_file:
        if metadata.third_party.license_type == metadata_pb2.LicenseType.BY_EXCEPTION_ONLY:
           metadata_file.write(textwrap.dedent("""\
            # THIS PACKAGE HAS SPECIAL LICENSING CONDITIONS. PLEASE
            # CONSULT THE OWNERS AND opensource-licensing@google.com BEFORE
            # DEPENDING ON IT IN YOUR PROJECT.

            """))
        metadata_file.write(text_metadata)
