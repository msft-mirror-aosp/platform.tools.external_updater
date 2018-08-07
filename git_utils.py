# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Helper functions to communicate with Git.'''

import datetime
import subprocess


def _run(cmd, cwd):
    """Runs a command with stdout and stderr redirected."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True, cwd=cwd)


def fetch(proj_path, remote_names):
    """Runs git fetch.

    Args:
        proj_path: Path to Git repository.
        remote_names: Array of string to specify remote names.
    """
    _run(['git', 'fetch', '--multiple'] + remote_names, cwd=proj_path)


def add_remote(proj_path, name, url):
    """Adds a git remote.

    Args:
        proj_path: Path to Git repository.
        name: Name of the new remote.
        url: Url of the new remote.
    """
    _run(['git', 'remote', 'add', name, url], cwd=proj_path)


def list_remotes(proj_path):
    """Lists all Git remotes.

    Args:
        proj_path: Path to Git repository.

    Returns:
        A dict from remote name to remote url.
    """
    out = _run(['git', 'remote', '-v'], proj_path)
    lines = out.stdout.decode('utf-8').splitlines()
    return dict([line.split()[0:2] for line in lines])


def get_commits_ahead(proj_path, branch, base_branch):
    """Lists commits in `branch` but not `base_branch`."""
    out = _run(['git', 'rev-list', '--left-only',
                '{}...{}'.format(branch, base_branch)],
               proj_path)
    return out.stdout.decode('utf-8').splitlines()


def get_commit_time(proj_path, commit):
    """Gets commit time of one commit."""
    out = _run(['git', 'show', '-s', '--format=%ct', commit], cwd=proj_path)
    return datetime.datetime.fromtimestamp(int(out.stdout))


def list_remote_branches(proj_path, remote_name):
    """Lists all branches for a remote."""
    out = _run(['git', 'branch', '-r'], cwd=proj_path)
    lines = out.stdout.decode('utf-8').splitlines()
    stripped = [line.strip() for line in lines]
    remote_path = remote_name + '/'
    remote_path_len = len(remote_path)
    return [line[remote_path_len:] for line in stripped
            if line.startswith(remote_path)]
