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
"""A commandline tool to check and update packages in external/

Example usage:
updater.sh checkall
updater.sh update kotlinc
"""

import argparse
import os
import subprocess

from google.protobuf import text_format    # pylint: disable=import-error

import fileutils
from git_updater import GitUpdater
from github_archive_updater import GithubArchiveUpdater
import updater_utils


UPDATERS = [GithubArchiveUpdater, GitUpdater]


def color_string(string, color):
    """Changes the color of a string when print to terminal."""
    colors = {
        'FRESH': '\x1b[32m',
        'STALE': '\x1b[31;1m',
        'ERROR': '\x1b[31m',
    }
    end_color = '\033[0m'
    return colors[color] + string + end_color


def build_updater(proj_path):
    """Build updater for a project specified by proj_path.

    Reads and parses METADATA file. And builds updater based on the information.

    Args:
      proj_path: Absolute or relative path to the project.

    Returns:
      The updater object built. None if there's any error.
    """

    proj_path = fileutils.get_absolute_project_path(proj_path)
    try:
        metadata = fileutils.read_metadata(proj_path)
    except text_format.ParseError as err:
        print('{} {}.'.format(color_string('Invalid metadata file:', 'ERROR'),
                              err))
        return None

    try:
        updater = updater_utils.create_updater(metadata, proj_path, UPDATERS)
    except ValueError:
        print(color_string('No supported URL.', 'ERROR'))
        return None
    return updater


def check_update(proj_path):
    """Checks updates for a project. Prints result on console.

    Args:
      proj_path: Absolute or relative path to the project.
    """

    print(
        'Checking {}. '.format(fileutils.get_relative_project_path(proj_path)),
        end='')
    updater = build_updater(proj_path)
    if updater is None:
        return (None, None)
    try:
        new_version = updater.check()
        if new_version:
            print(color_string(' Out of date!', 'STALE'))
        else:
            print(color_string(' Up to date.', 'FRESH'))
        return (updater, new_version)
    except IOError as err:
        print('{} {}.'.format(color_string('Failed.', 'ERROR'),
                              err))
        return (None, None)
    except subprocess.CalledProcessError as err:
        print(
            '{} {}\nstdout: {}\nstderr: {}.'.format(
                color_string(
                    'Failed.',
                    'ERROR'),
                err,
                err.stdout,
                err.stderr))
        return (None, None)


def check(args):
    """Handler for check command."""

    check_update(args.path)


def update(args):
    """Handler for update command."""

    updater, new_version = check_update(args.path)
    if updater is None:
        return
    if not new_version and not args.force:
        return

    updater.update()


def checkall(args):
    """Handler for checkall command."""
    for root, _dirs, files in sorted(os.walk(args.path)):
        if fileutils.METADATA_FILENAME in files:
            check_update(root)


def parse_args():
    """Parses commandline arguments."""

    parser = argparse.ArgumentParser(
        description='Check updates for third party projects in external/.')
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    # Creates parser for check command.
    check_parser = subparsers.add_parser(
        'check', help='Check update for one project.')
    check_parser.add_argument(
        'path',
        help='Path of the project. '
        'Relative paths will be resolved from external/.')
    check_parser.set_defaults(func=check)

    # Creates parser for checkall command.
    checkall_parser = subparsers.add_parser(
        'checkall', help='Check update for all projects.')
    checkall_parser.add_argument(
        '--path',
        default=fileutils.EXTERNAL_PATH,
        help='Starting path for all projects. Default to external/.')
    checkall_parser.set_defaults(func=checkall)

    # Creates parser for update command.
    update_parser = subparsers.add_parser('update', help='Update one project.')
    update_parser.add_argument(
        'path',
        help='Path of the project. '
        'Relative paths will be resolved from external/.')
    update_parser.add_argument(
        '--force',
        help='Run update even if there\'s no new version.',
        action='store_true')
    update_parser.set_defaults(func=update)

    return parser.parse_args()


def main():
    """The main entry."""

    args = parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
