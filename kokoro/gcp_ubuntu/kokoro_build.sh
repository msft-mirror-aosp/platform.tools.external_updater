#!/bin/bash
set -e

TOP=$(cd $(dirname $0)/../../../.. && pwd)
EXTERNAL_UPDATER=$TOP/tools/external_updater

cd $TOP
echo Current directory: $PWD
echo "Initializing Android tree and syncing"
repo init -u https://android.googlesource.com/platform/manifest -b main --depth=1 < /dev/null
repo sync -c

source build/envsetup.sh
lunch aosp_cf_x86_64_phone-trunk_staging-eng

cd $EXTERNAL_UPDATER
echo Current directory: $PWD

echo "Building external_updater"
mm -j

echo "Checking compatible projects"

compatible_repositories=("libxml2")

for project in "${compatible_repositories[@]}"; do
  PROJ_PATH=$TOP/external/$project
  echo "Trying to upgrade $PROJ_PATH"
  $TOP/out/host/linux-x86/bin/external_updater update --no-build --skip-post-update $PROJ_PATH
done

trap 'rm -rf $TOP' EXIT
