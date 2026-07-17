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
#########

GRASSSTABLE=85
GRASSSDEVEL=86

cd $HOME
# fetch artifact stable
echo "## Processing grass${GRASSSTABLE} / grass-stable manual pages..."
bash /home/neteler/cronjobs/gh_cli_download_artifact.sh releasebranch_8_5
# unpack stable-version: due to the needed SEO meta canonical injection we keep it "duplicated"
cd /var/www/code_and_data/grass${GRASSSTABLE}/manuals/ && rm -rf * && unzip -q /tmp/releasebranch_8_5.zip
cd /var/www/code_and_data/grass-stable/manuals/ && rm -rf * && unzip -q /tmp/releasebranch_8_5.zip

####

# fetch artifact devel
echo "## Processing grass${GRASSSDEVEL} / grass-devel manual pages..."
bash /home/neteler/cronjobs/gh_cli_download_artifact.sh main
# unpack devel-version: due to the needed SEO meta canonical injection we keep it "duplicated"
cd /var/www/code_and_data/grass${GRASSSDEVEL}/manuals/ && rm -rf * && unzip -q /tmp/main.zip
cd /var/www/code_and_data/grass-devel/manuals/ && rm -rf * && unzip -q /tmp/main.zip

####

# if run as "neteler", grant write access also to "grassbot" user
chmod -R g+rw /var/www/code_and_data/grass${GRASSSTABLE}/manuals/* \
              /var/www/code_and_data/grass-stable/manuals/* \
              /var/www/code_and_data/grass${GRASSSDEVEL}/manuals/* \
              /var/www/code_and_data/grass-devel/manuals/*

# cleanup the artifact file
rm -f /tmp/releasebranch_8_5.zip /tmp/main.zip
