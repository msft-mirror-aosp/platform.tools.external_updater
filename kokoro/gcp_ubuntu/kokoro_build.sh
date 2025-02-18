#!/bin/bash
set -e

TOP=$(cd $(dirname $0)/../../../.. && pwd)
EXTERNAL_UPDATER=$(pwd)/../..

cd $TOP
echo "Initializing Android tree and syncing"
repo init -u https://android.googlesource.com/platform/manifest -b main --depth=1 < /dev/null
repo sync -c

source build/envsetup.sh
lunch aosp_cf_x86_64_phone-trunk_staging-eng

cd $EXTERNAL_UPDATER
echo "Building external_updater"
mm -j

echo "Checking compatible projects"
input=$EXTERNAL_UPDATER/kokoro/gcp_ubuntu/"compatible_repositories.txt"

while IFS= read -r line; do
    PROJ_PATH=$TOP/external/$line
    echo "$PROJ_PATH"
    $TOP/out/host/linux-x86/bin/external_updater check $PROJ_PATH
done < "$input"

trap 'rm -rf $TOP' EXIT
