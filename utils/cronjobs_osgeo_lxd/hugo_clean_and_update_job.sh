#!/bin/sh

############################################################################
#
# TOOL:         hugo_clean_and_update_job.sh
# AUTHOR(s):    Markus Neteler, Corey T. White
# PURPOSE:      Deploy updated web site from the CI-built release artifact
# COPYRIGHT:    (c) 2020-2026 Markus Neteler and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
#############################################################################

# The website is no longer built on this server. GitHub Actions
# (grass-website: .github/workflows/build-production-site.yml) builds the
# site with the pinned Hugo Extended + Dart Sass + Node toolchain on every
# push to master and publishes it as a checksummed tarball on a per-deploy
# GitHub release, marking the newest one "latest":
#   https://github.com/OSGeo/grass-website/releases/latest
#
# This job downloads that tarball from the "latest" release, verifies its
# SHA256 checksum, and rsyncs it into the web root. It requires only curl,
# tar, sha256sum, and rsync. No GitHub token is needed (public release URL
# over HTTPS). To roll back a bad build, mark an older release as latest
# (gh release edit <tag> --latest) and this job deploys it on the next run.
####
# Procedure:
#  1. fetch the published checksum; exit early if it matches the deployed one
#  2. download the tarball and verify the checksum (abort on mismatch)
#  3. unpack into a clean staging directory
#  4. rsync over updated pages to target web directory, deleting leftover files
#  5. generate links from src code directory content into web directory
#  6. restore timestamps of links from their original time stamps in src directory
####

# Overridable for testing (e.g. RELEASE_URL="file:///tmp/fake" TARGET=/tmp/www ...)
RELEASE_URL="${RELEASE_URL:-https://github.com/OSGeo/grass-website/releases/latest/download}"
WORK="${WORK:-${HOME}/grass-website-deploy}"
TARGET="${TARGET:-/var/www/html}"
CODE_AND_DATA="${CODE_AND_DATA:-/var/www/code_and_data}"

TARBALL="grass-website.tar.gz"
CHECKSUM="${TARBALL}.sha256"

# function to update timestamp of link to the source timestamp
fix_link_timestamp()
{
 if [ -z "$1" ] ; then
   echo 'ERROR: Parameter missing. Specify the folder (. for current)!'
   exit
 fi

 for mylink in $(find . -type l) ; do
  LINK="$(namei ${mylink} | grep '^ l ' | tr -s ' ' ' ' | cut -d' ' -f3)"
  ORIG="$(namei ${mylink} | grep '^ l ' | tr -s ' ' ' ' | cut -d' ' -f5-)"

  echo "Updating timestamp of link <$ORIG> ---> <$LINK> timestamp"

  # transfer timestamp
  touch -h -m -r "$ORIG" "$LINK"
 done
}

mkdir -p "$WORK" && cd "$WORK" || exit 1

# fetch the published checksum first
curl -fsSL -o "$CHECKSUM" "$RELEASE_URL/$CHECKSUM" || exit 1

# nothing to do if the published build is already deployed
if [ -f deployed.sha256 ] && cmp -s "$CHECKSUM" deployed.sha256 ; then
   echo "Published build already deployed, nothing to do."
   exit 0
fi

curl -fsSL -o "$TARBALL" "$RELEASE_URL/$TARBALL" && \
   sha256sum -c "$CHECKSUM" && \
   rm -rf public && mkdir public && \
   tar -xzf "$TARBALL" -C public && \
   rsync -a --delete "$WORK/public/" "$TARGET/" && \
   ln -s "$CODE_AND_DATA"/* "$TARGET/" && \
   (cd "$TARGET/" && fix_link_timestamp .) && \
   cp "$CHECKSUM" deployed.sha256
