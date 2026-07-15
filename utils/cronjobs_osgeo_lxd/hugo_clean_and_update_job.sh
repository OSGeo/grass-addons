#!/bin/sh

############################################################################
#
# TOOL:         hugo_clean_and_update_job.sh
# AUTHOR(s):    Markus Neteler
# PURPOSE:      Deploy updated web site from github repo
# COPYRIGHT:    (c) 2020-2025  Markus Netelerand the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
#############################################################################

# Preparations:
#  sudo chown -R neteler.users /var/www
# get grass-website repo
#  cd ~/
#  git clone https://github.com/OSGeo/grass-website.git
####
# Procedure:
#  1. change into local git repo copy
#  2. update local repo from github
#  3. build updated pages with hugo into clean directory
#  4. rsync over updated pages to target web directory, deleting leftover files
#  5. generate links from src code directory content into web directory
#  6. restore timestamps of links from their original time stamps in src directory
####

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

cd /home/neteler/grass-website/ && \
   git pull origin master && \
   rm -rf /home/neteler/grass-website/public/* && \
   nice /home/neteler/go/bin/hugo && \
   rsync -a --delete /home/neteler/grass-website/public/ /var/www/html/ && \
   ln -s /var/www/code_and_data/* /var/www/html/ && \
   (cd /var/www/html/ && fix_link_timestamp .)
