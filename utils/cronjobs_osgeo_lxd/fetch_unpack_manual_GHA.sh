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
#
# How this script works:
#
# to be run on grass.osgeo.org, in "neteler" or "grassbot" userspace
# - executes gh_cli_download_artifact.sh
# - unpacks the Documentation artifact both in grass85 and grass-devel dirs on the server
#########

ZIP=/tmp/mkdocs-site.zip

cd "$HOME" || exit 1
# fetch artifact; do not touch the existing manuals if the download failed
# (e.g. "gh: Artifact has expired (HTTP 410)")
if ! bash /home/neteler/cronjobs/gh_cli_download_artifact.sh; then
  echo "ERROR: Artifact download failed, keeping existing manuals."
  exit 1
fi

# verify the ZIP before deleting anything (guards against truncated
# downloads and error bodies saved as file content)
if [ ! -s "$ZIP" ] || ! unzip -tq "$ZIP" > /dev/null; then
  echo "ERROR: <$ZIP> is missing or not a valid ZIP archive, keeping existing manuals."
  exit 1
fi

# unpack into a staging directory first, so the live manuals are only
# replaced once a complete, successful extraction is available
STAGING=$(mktemp -d /tmp/mkdocs-site.XXXXXX)
if ! unzip -q "$ZIP" -d "$STAGING"; then
  echo "ERROR: Failed to unpack <$ZIP>, keeping existing manuals."
  rm -rf "$STAGING"
  exit 1
fi

# update twice: number-version and devel-version
for TARGET in /var/www/code_and_data/grass85/manuals /var/www/code_and_data/grass-devel/manuals; do
  rm -rf "${TARGET:?}"/* && cp -a "$STAGING"/. "$TARGET"/
done
rm -rf "$STAGING"

# if run as "neteler", let the grassbot user also write therein
chmod -R g+rw /var/www/code_and_data/grass85/manuals/* /var/www/code_and_data/grass-devel/manuals/*

# cleanup the artifact file
rm -f "$ZIP"
