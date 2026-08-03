#!/bin/bash

# Purpose: Script to download GRASS 8.5+ "Documentation" artifact from GitHub (produced by GitHub action workflow) and unpack
#
# (c) 2025, GPL 2+ Markus Neteler <neteler@osgeo.org>
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
# requires: jq, gh cli and login via gh auth login
#
###################################################################
# How this script works:
#
# to be run on grass.osgeo.org, in "neteler" or "grassbot" userspace
# - executes gh_cli_download_artifact.sh
# - unpacks the Documentation artifact both in grass85 and grass-devel dirs on the server
#
# NOTE: one-time server-side setup (cannot be done from this job): the target
# manuals directories themselves must be writable by every user running this
# job, e.g. shared group ownership with g+ws on the directories
#
#########

GRASSSTABLE=85
GRASSSDEVEL=86

# per-user directory for artifact ZIPs and staging: the job runs as different
# users (neteler, grassbot, ...) and a shared /tmp path lets one user's
# leftover file block another user's run (sticky /tmp forbids replacing it);
# gh_cli_download_artifact.sh honors this variable for its output path
OUTPUT_DIR="${OUTPUT_DIR:-${TMPDIR:-/tmp}/grass_manuals_${USER}}"
export OUTPUT_DIR
mkdir -p "$OUTPUT_DIR" || exit 1

cd "$HOME" || exit 1

# fetch the manual ZIP for one branch and unpack it into the given target
# dirs; the existing manuals are only replaced once a complete, successful
# extraction is available
fetch_and_unpack () {
  BRANCH=$1
  shift
  ZIP="$OUTPUT_DIR/${BRANCH}.zip"

  # fetch artifact; do not touch the existing manuals if the download failed
  # (e.g. "gh: Artifact has expired (HTTP 410)")
  if ! bash /home/neteler/cronjobs/gh_cli_download_artifact.sh "$BRANCH"; then
    echo "ERROR: Artifact download for <$BRANCH> failed, keeping existing manuals."
    return 1
  fi

  # verify the ZIP before deleting anything (guards against truncated
  # downloads and error bodies saved as file content)
  if [ ! -s "$ZIP" ] || ! unzip -tq "$ZIP" > /dev/null; then
    echo "ERROR: <$ZIP> is missing or not a valid ZIP archive, keeping existing manuals."
    return 1
  fi

  # unpack into a staging directory first
  STAGING=$(mktemp -d "$OUTPUT_DIR/${BRANCH}.XXXXXX")
  if ! unzip -q "$ZIP" -d "$STAGING"; then
    echo "ERROR: Failed to unpack <$ZIP>, keeping existing manuals."
    rm -rf "$STAGING"
    return 1
  fi

  # GitHub artifact ZIPs carry no unix permissions, so unzip creates files
  # per the cron user's umask; make everything world-readable so the web
  # server can serve it (a restrictive umask otherwise leads to 403 errors)
  chmod -R u+rwX,g+rwX,o+rX "$STAGING"

  for TARGET in "$@"; do
    rm -rf "${TARGET:?}"/* && cp -a "$STAGING"/. "$TARGET"/
    # keep the tree group-writable so the other job users (e.g. "grassbot"
    # when run as "neteler") can replace it on the next run
    chmod -R a+rX,g+w "$TARGET"
  done

  # cleanup staging directory and artifact file
  rm -rf "$STAGING"
  rm -f "$ZIP"
  return 0
}

STATUS=0

# fetch artifact stable
echo "## Processing grass${GRASSSTABLE} / grass-stable manual pages..."
# unpack stable-version: due to the needed SEO meta canonical injection we keep it "duplicated"
fetch_and_unpack releasebranch_8_5 \
  /var/www/code_and_data/grass${GRASSSTABLE}/manuals \
  /var/www/code_and_data/grass-stable/manuals || STATUS=1

####

# fetch artifact devel
echo "## Processing grass${GRASSSDEVEL} / grass-devel manual pages..."
# unpack devel-version: due to the needed SEO meta canonical injection we keep it "duplicated"
fetch_and_unpack main \
  /var/www/code_and_data/grass${GRASSSDEVEL}/manuals \
  /var/www/code_and_data/grass-devel/manuals || STATUS=1

####

exit $STATUS
