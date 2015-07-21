#!/bin/bash
# Sync GRASS source code for CI.

# REQUIREMENTS
# ------------
# * git-svn
# * authors-prog.sh
# * grass-ci-ssh-key
# * grass-ci-ssh-key.pub
# * ssh.sh

# REPOSITORY INITIALIZATION (DO IT ONLY ONCE)
# -------------------------------------------
# $ mkdir grass-ci
# $ cd grass-ci
# $ wget https://trac.osgeo.org/grass/export/HEAD/grass/trunk/contributors.csv
# $ awk -F "," '{gsub(" ", "@", $3); print $5 " = " $2 " " $3}' ./contributors.csv | grep -v "^osgeo_id" | grep -v "^-"  > grass-authors.txt
# $ git svn clone -s -r 65500:HEAD https://svn.osgeo.org/grass/grass/ --authors-file=grass-authors.txt --authors-prog=authors-prog.sh --prefix=svn/
# $ cd grass
# $ git remote add origin git@github.com:GRASS-GIS/grass-ci.git
# $ cd .. && grass-ci.sh

# SOURCE CODE SYNC (RUN EVERY FIVE MINUTES)
# ----------------------------------------
# Create cron job file '/etc/cron.d/grass-ci' with following content:
# */5 * * * *  username  /path/to/grass-ci/grass-ci.sh

# URLs
# ----
# * GitHub page    - https://github.com/GRASS-GIS/grass-ci
# * Travis CI page - https://travis-ci.org/GRASS-GIS/grass-ci

# Author: Ivan Mincik, ivan.mincik@gmail.com

set -e

GRASS_CI_DIR=$(dirname "$(readlink -f "$0")")
export GRASS_CI_DIR

# configure SSH key
export GIT_SSH=$GRASS_CI_DIR/ssh.sh

# update src
cd $GRASS_CI_DIR/grass
REBASE_LOG=$(git svn rebase --authors-file=../grass-authors.txt --authors-prog=../authors-prog.sh)
git push -u origin master > /dev/null

# write log
echo -e "\n$(date -R)" >> $GRASS_CI_DIR/grass-ci.log
echo "$REBASE_LOG" >> $GRASS_CI_DIR/grass-ci.log

# vim: set ts=4 sts=4 sw=4 noet:
