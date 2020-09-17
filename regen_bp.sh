#!/bin/bash
#
# Copyright (C) 2020 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script is used by external_updater to replace a package. Don't
# invoke directly.

set -e

# Call this in two ways:
# (1) in a .../external/* rust directory with .bp and Cargo.toml,
#     development/scripts/cargo2android.py must be in PATH
# (2) in a tmp new directory with .bp and Cargo.toml,
#     and $1 equals to the rust Android source tree root,
#     and $2 equals to the rust sub-directory path name under external.
if [ "$1" == "" ]; then
  external_dir=`pwd`
  C2A=`which cargo2android.py`
  if [ "$C2A" == "" ]; then
    echo "ERROR: cannot find cargo2android.py in PATH"
    exit 1
  fi
else
  external_dir="$2"  # e.g. rust/crates/bytes
  C2A="$1/development/scripts/cargo2android.py"
  if [ ! -f $C2A ]; then
    echo "ERROR: cannot find $C2A"
    exit 1
  fi
fi

# Save Cargo.lock if it existed before this update.
if [ -f Cargo.lock ]; then
  mv Cargo.lock Cargo.lock.saved
fi

LINE1=`head -1 Android.bp`
FLAGS=`echo $LINE1 | sed -e 's:^.*cargo2android.py ::;s:\.$::'`
CMD="$C2A $FLAGS"
echo "Updating Android.bp: $CMD"
$CMD
rm -rf target.tmp cargo.out Cargo.lock

# Restore Cargo.lock if it existed before this update.
if [ -f Cargo.lock.saved ]; then
  mv Cargo.lock.saved Cargo.lock
fi

# Some .bp files have manual changes.
# Add a note to force a manual edit.
case $external_dir in
  */libloading|*/libsqlite3-sys|*/serde|*/unicode-xid)
    echo "FIXME: Copy manual changes from old version!" >> Android.bp
esac

exit 0
