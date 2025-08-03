#!/bin/bash

# Purpose: Script to download GRASS "Documentation" artifact from GitHub (produced by GitHub action workflow) and unpack
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
# GRASS 8.5 `main` mkdocs documentation update
#
# to be run on grass.osgeo.org, in "neteler" or "grassbot" userspace
# - executes gh_cli_download_artifact.sh
# - unpacks the Documentation artifact both in grass85 and grass-devel dirs on the server

cd $HOME

# fetch artifact
bash /home/neteler/cronjobs/gh_cli_download_artifact.sh

# update twice: version and devel
cd /var/www/code_and_data/grass85/manuals/ && rm -rf * && unzip -q /tmp/mkdocs-site.zip
cd /var/www/code_and_data/grass-devel/manuals/ && rm -rf * && unzip -q /tmp/mkdocs-site.zip

# if run as "neteler", let the grassbot user also write therein
chmod -R g+rw /var/www/code_and_data/grass85/manuals/* /var/www/code_and_data/grass-devel/manuals/*

# cleanup the artifact file
rm -f /tmp/mkdocs-site.zip
