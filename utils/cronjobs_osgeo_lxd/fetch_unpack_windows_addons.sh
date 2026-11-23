#!/bin/bash

############################################################################
#
# TOOL:         fetch_unpack_windows_addons.sh
# AUTHOR(s):    Anna Petrasova
# PURPOSE:      Deploy the addons compiled for Windows by the CI
# COPYRIGHT:    (c) 2026 Anna Petrasova and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
#############################################################################

# The addons are compiled for Windows by GitHub Actions (grass-addons:
# .github/workflows/ci-windows.yml) for each supported GRASS version and
# published every night as one ZIP file per GRASS version on a pre-release:
#   https://github.com/OSGeo/grass-addons/releases
# The name of a ZIP file ends with the platform the addons are compiled for,
# which is the distribution and the CPU architecture, e.g. osgeo4w-x86_64.
#
# This job takes the newest ZIP file for each platform and GRASS version and
# unpacks it into the directory g.extension on Windows downloads the addons
# from (GRASS 8.5.1 and newer), e.g. for GRASS 8.5.0 from OSGeo4W:
#   $TARGET_ROOT/addons/grass8/binaries/osgeo4w-x86_64/8.5.0/
# The platforms and GRASS versions are taken from the names of the published
# files, so this job needs no change when the CI starts to build for a new
# version or platform.
#
# It requires python3, curl, sha256sum, unzip, rsync and flock. No GitHub
# token is needed (public API and release URLs over HTTPS).
####
# Procedure, for each platform and GRASS version:
#  1. fetch the published checksum; skip if it matches the deployed one
#  2. download the ZIP file and verify the checksum
#  3. unpack into a clean staging directory, including the build logs
#  4. rsync to the target directory, deleting addons which are no longer built
#  5. store the checksum next to the addons
# The deployed addons are not touched when any of the steps 1-3 fails. When
# step 4 fails, the next run repeats the deployment.
####

# Overridable for testing (e.g. TARGET_ROOT=/tmp/www LOOKUP_ARGS="--api-url ...")
LOOKUP="${LOOKUP:-$(dirname "$(readlink -f "$0")")/windows_addons_latest.py}"
LOOKUP_ARGS="${LOOKUP_ARGS:-}"
WORK="${WORK:-${HOME}/grass-windows-addons-deploy}"
TARGET_ROOT="${TARGET_ROOT:-/var/www/code_and_data}"

# The checksum of the deployed bundle is kept next to the addons.
DEPLOYED="bundle.sha256"

# download a file, giving up on a stalled connection so that runs do not pile up
download () {
  curl -fsSL --connect-timeout 30 --max-time 900 -o "$1" "$2"
}

deploy () {
  platform=$1
  version=$2
  zip_url=$3
  checksum_url=$4

  # osgeo4w-x86_64, 8.5.0 -> addons/grass8/binaries/osgeo4w-x86_64/8.5.0
  major=${version%%.*}
  target="$TARGET_ROOT/addons/grass${major}/binaries/${platform}/${version}"
  zip="${zip_url##*/}"
  checksum="${checksum_url##*/}"
  staging="staging-${platform}-${version}"

  download "$checksum" "$checksum_url" || return 1

  if cmp -s "$checksum" "$target/$DEPLOYED" ; then
    echo "Addons for GRASS $version ($platform) are up to date."
    return 0
  fi

  echo "Deploying addons for GRASS $version ($platform) to <$target>..."
  rm -rf "$staging"
  download "$zip" "$zip_url" || return 1
  # check the downloaded file whatever file name the checksum file has in it
  echo "$(cut -d ' ' -f 1 "$checksum")  $zip" | sha256sum -c - || return 1
  mkdir "$staging" || return 1
  unzip -q -o "$zip" -d "$staging" || return 1

  # The build logs are served from the logs subdirectory.
  if [ -f "$staging/logs.zip" ] ; then
    unzip -q -o "$staging/logs.zip" -d "$staging" || return 1
    rm "$staging/logs.zip"
  fi

  # ZIP files carry no unix permissions; make everything readable for the web
  # server and writable for the group, so that other users can run this job.
  chmod -R u+rwX,g+rwX,o+rX "$staging"

  mkdir -p "$target" || return 1
  # The checksum is stored only after everything is in place, so that an
  # interrupted deployment is repeated. Owner, group, permissions and times
  # of existing directories are left alone, because only the owner of
  # a directory can set them.
  rsync -rlt --omit-dir-times --delete --exclude "/$DEPLOYED" \
    "$staging/" "$target/" || return 1
  cp "$checksum" "$target/$DEPLOYED" || return 1

  rm -rf "$staging" "$zip"
  return 0
}

# New files and directories are writable for the group and readable for all.
umask 002

mkdir -p "$WORK" || exit 1
cd "$WORK" || exit 1

# Two runs at the same time would use the same staging directory.
exec 9> lock
if ! flock -n 9 ; then
  echo "Another run is in progress."
  exit 0
fi

# shellcheck disable=SC2086 # the arguments are split on purpose
bundles=$(python3 "$LOOKUP" $LOOKUP_ARGS) || exit 1

STATUS=0
while IFS=$'\t' read -r platform version zip_url checksum_url ; do
  if ! deploy "$platform" "$version" "$zip_url" "$checksum_url" ; then
    echo "ERROR: Deployment of addons for GRASS $version ($platform) failed."
    STATUS=1
  fi
done <<< "$bundles"

exit $STATUS
