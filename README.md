# external_updater

external updater is a tool to automatically update libraries in external/.

The documentation on this page is for users of `external_updater`. If you're
looking for developer docs, see [docs/dev.md](docs/dev.md).

## Usage

In each of the examples below, `$PROJECT_PATH` is the path to the project to
operate on. If more than one path is given, external_updater will operate on
each in turn.

Make sure you have initialized AOSP main source code. The default remote for
external updater is AOSP.

If you are trying to upgrade a project in other remotes, you can pass
`--remote-name $REMOTE` to the `update` parser. We strongly recommend updating
projects in AOSP and allowing automerger to merge the upgrade CL with other
branches.

To use this tool, a METADATA file must present at the root of the
repository. The full definition can be found in
[metadata.proto](https://android.googlesource.com/platform/tools/external_updater/+/refs/heads/main/metadata.proto).
Or
[external/toybox/METADATA](https://android.googlesource.com/platform/external/toybox/+/refs/heads/main/METADATA)
is a concrete example.

From within your working directory, source the `envsetup.sh` script to set up
your build environment and pick a target to build with the `lunch` command. You
can pass any target that you want. After upgrading a project, external_updater
starts building for the selected lunch target:

```shell
source build/envsetup.sh
lunch aosp_cf_x86_64_phone-trunk_staging-eng
```

Check updates for a library or verify METADATA is valid:

```shell
tools/external_updater/updater.sh check PROJECT_PATH
```

Update a library, commit, and upload the change to Gerrit:

```shell
tools/external_updater/updater.sh update PROJECT_PATH
```

PROJECT_PATH can be the path to a library under external/, e.g.
external/kotlinc, or external/python/cpython3. You can press Tab to complete the
path.

The following options can be passed to `update` parser:
```shell
--no-build                        Skip building
--no-upload                       Does not upload to Gerrit after upgrade
--bug BUG                        Bug number for this update
--custom-version CUSTOM_VERSION  Custom version we want to upgrade to.
--skip-post-update                Skip post_update script if post_update script exists
--keep-local-changes              Updates the current branch instead of creating a new branch
--no-verify                       Pass --no-verify to git commit
--remote-name REMOTE_NAME        Remote repository name, the default is set to aosp
--exclude$EXCLUDE                Names of projects to exclude. These are just the final part of the path with no directories.
--refresh                         Run update and refresh to the current version.
--keep-date                       Run update and do not change date in METADATA.
--json-output JSON_OUTPUT        Path of a json file to write result to.
```

For example:

```shell
tools/external_updater/updater.sh update --custom-version $VERSION $PROJECT_PATH
```

## Configure

The most important part in the file is a list of urls.
`external_updater` will go through all urls and uses the first
supported url.

### Git upstream

If the url type is `Git`, the URL must be a git upstream
(the one you can use with `git clone`). And the version field must
be either a version tag, or SHA. The tool will find the latest
version tag or sha based on it.

When upgrade, the tool will simply run `git merge tag/sha`.

IMPORTANT: It is suggested to set up a `upstream-main` branch to
replicate upstream. Because most users don't have the privilege to
upload changes not authored by themselves. This can be done by
filing a bug to componentid:99104.

#### SHA

If the version is a SHA, the tool will always try to upgrade to the
top of upstream. As long as there is any new change upstream, local
library will be treated as stale.

#### Version tag

If the version is not a SHA, the tool will try to parse the version
to get a numbered version. Currently the supported version format is:

```markdown
<prefix><version_number><suffix>
```

version_number part can be numbers separated by `.` or `-` or `_`.

If you have project where this isn't working, file a bug so we can take a look.

#### Local changes

It is suggested to verify all local changes when upgrading. This can
be done easily in Gerrit, by comparing parent2 and the patchset.


### GitHub archive

If the url type is `Archive`, and the url is from GitHub, `external_updater`
will upgrade a library based on GitHub tags/releases.

If you have the choice between archives and git tags, choose tags.
Because that makes it easier to manage local changes.

The tool will query GitHub to get the latest release from:

```url
https://github.com/user/proj/releases/latest
```

If the tag of latest release is not equal to version in METADATA file, a
new version is found. The tool will download the tarball and overwrite the
library with it.

If there are multiple archives in one GitHub release, the one most
[similar](https://en.wikipedia.org/wiki/Edit_distance) to previous
(from METADATA) will be used.

After upgrade, files not present in the new tarball will be removed. But we
explicitly keep files famous in Android tree.
See [update_package.sh](https://android.googlesource.com/platform/tools/external_updater/+/refs/heads/main/update_package.sh).

If more files need to be reserved, a post_update.sh can be created to copy
these files over.
See [example](https://android.googlesource.com/platform/external/kotlinc/+/refs/heads/main/post_update.sh).

#### Local patches

Local patches can be kept as patches/*.diff. They will be applied after
upgrade. [example](https://cs.android.com/android/platform/superproject/main/+/main:external/jsmn/patches/header.diff)

## Email notification

There is some support to automatically check updates for all external
libraries every hour, send email and change. Currently this is done by
running the following script on a desktop machine.

```shell
#!/bin/bash

cd /src/aosp
while true
do
        repo abandon tmp_auto_upgrade
        repo forall -c git checkout .
        repo forall -c git clean -xdf
        repo sync -c
        source build/envsetup.sh
        lunch aosp_arm-eng
        mmma tools/external_updater

        out/soong/host/linux-x86/bin/external_updater_notifier \
                --history ~/updater/history \
                --recipients=android_external_lib_updates@google.com \
                --generate_change \
                --all
        date
        echo "Sleeping..."
        sleep 3600
done
```
