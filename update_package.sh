#!/bin/bash
#
# Copyright (C) 2007 The Android Open Source Project
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
# invoke directly

cd $1

# Copies all files we want to reserve.
cp -a -n $2/Android.bp       $1/  2> /dev/null
cp -a -n $2/Android.mk       $1/  2> /dev/null
cp -a -n $2/LICENSE          $1/  2> /dev/null
cp -a -n $2/NOTICE           $1/  2> /dev/null
cp -a -n $2/MODULE_LICENSE_* $1/  2> /dev/null
cp -a -n $2/METADATA         $1/  2> /dev/null
cp -a -n $2/.git             $1/  2> /dev/null
cp -a -n $2/.gitignore       $1/  2> /dev/null
cp -a -n $2/patches          $1/  2> /dev/null
cp -a -n $2/post_update.sh   $1/  2> /dev/null

# Applies all patches
for p in $1/patches/*.diff
do
  [ -e "$p" ] || continue
  echo Applying $p
  patch -p1 -d $1 < $p;
done

if [ -f $1/post_update.sh ]
then
  echo Running post update script
  $1/post_update.sh $1 $2
fi

# Swap old and new.
rm -rf $2
mv $1 $2
