#!/bin/bash
set -e

TOP=$(cd $(dirname $0)/../../.. && pwd)
EXTERNAL_UPDATER=$(pwd)

cd $TOP

repo init -u sso://android/platform/manifest -b main --depth=1 < /dev/null
repo sync -c

source build/envsetup.sh
lunch aosp_cf_x86_64_phone-trunk_staging-eng
mm -j tools/external_updater

cd $EXTERNAL_UPDATER

input="compatible_repositories.txt"

while IFS= read -r line; do
    PROJ_PATH=$TOP/external/$line
    $TOP/out/host/linux-x86/bin/external_updater check $PROJ_PATH
done < "$input"

trap 'rm -rf $TOP' EXIT
