#!/bin/bash

# Reconstruction of GRASS GIS historic versions as grass-legacy repo (V 3.2 - 4.3)
# 2019, by Markus Neteler and Antonio Galea

##############################
# we start with an empty repo,
# in this script files are copied in the correct time order and the git repo is built
#
# Requirement: tarballs of GRASS GIS Versions with intact file timestamps (partially originating from cpio files).

## prep one time only
mkdir grass-legacy
cd grass-legacy/
git init .

GITAUTHOR="bot <grass-svn2git@osgeo.org>"

# have a first file
cp -p ../old_grass_versions/releasebranch_3_2/fhgis83rep.pdf .
git add fhgis83rep.pdf 

git commit -m 'Fort Hood GIS software (FHGIS) design document' --author "CERL <nobody@usace.army.mil>" --date 'May  1  1983' fhgis83rep.pdf 

## we are in master
# adding first chunk of code = 3.2
cp -rp ../old_grass_versions/releasebranch_3_2/* .

### loop
# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v 'fhgis83rep.pdf\|/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
cat /tmp/list_of_files.csv | while IFS="|" read MYDATE NAME ; do
    git add "$NAME"
    git diff --cached --quiet --exit-code || \
      git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "added"
done
git branch releasebranch_3_2
git status
git branch -a


#### next one: 4.0
# this still keeps .git/
rm -rf /home/mneteler/software/grass-legacy/*
cp -rp ../old_grass_versions/releasebranch_4_0/* .

# if still there, delete files with ugly  name (incl. *, ^, ...) to not trigger shell expansion later on:
find . -type f | grep -E '\s|\*|\?|\$|\%|\^'  | xargs rm -f

# initial cleanup with respect to previous version: deleted files (may have be moved elsewhere in the tree)
git status --porcelain | egrep "^ D " | cut -b4- | xargs git add

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
MYDATE=$(head -n 1 /tmp/list_of_files.csv | cut -d'|' -f1)
git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "deleted or moved"

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
cat /tmp/list_of_files.csv | while IFS="|" read MYDATE NAME ; do
    git add "$NAME"
    git diff --cached --quiet --exit-code || \
      git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "added"
done
git branch releasebranch_4_0
git status
git branch -a


#### next one: 4.1
# this still keeps .git/
rm -rf /home/mneteler/software/grass-legacy/*
cp -rp ../old_grass_versions/releasebranch_4_1/* .

# if still there, delete files with ugly  name (incl. *, ^, ...) to not trigger shell expansion later on:
find . -type f | grep -E '\s|\*|\?|\$|\%|\^'  | xargs rm -f

# initial cleanup with respect to previous version: deleted files (may have be moved elsewhere in the tree)
git status --porcelain | egrep "^ D " | cut -b4- | xargs git add

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
MYDATE=$(head -n 1 /tmp/list_of_files.csv | cut -d'|' -f1)
git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "deleted or moved"

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
cat /tmp/list_of_files.csv | while IFS="|" read MYDATE NAME ; do
    git add "$NAME"
    git diff --cached --quiet --exit-code || \
      git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "added"
done
git branch releasebranch_4_1
git status
git branch -a


#### next one: 4.2
# this still keeps .git/
rm -rf /home/mneteler/software/grass-legacy/*
cp -rp ../old_grass_versions/releasebranch_4_2/* .

# if still there, delete files with ugly  name (incl. *, ^, ...) to not trigger shell expansion later on:
find . -type f | grep -E '\s|\*|\?|\$|\%|\^'  | xargs rm -f

# initial cleanup with respect to previous version: deleted files (may have be moved elsewhere in the tree)
git status --porcelain | egrep "^ D " | cut -b4- | xargs git add

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
MYDATE=$(head -n 1 /tmp/list_of_files.csv | cut -d'|' -f1)
git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "deleted or moved"

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
cat /tmp/list_of_files.csv | while IFS="|" read MYDATE NAME ; do
    git add "$NAME"
    git diff --cached --quiet --exit-code || \
      git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "added"
done
git branch releasebranch_4_2
git status
git branch -a



#### next one: 4.3
# this still keeps .git/
rm -rf /home/mneteler/software/grass-legacy/*
cp -rp ../old_grass_versions/releasebranch_4_3/* .

# if still there, delete files with ugly  name (incl. *, ^, ...) to not trigger shell expansion later on:
find . -type f | grep -E '\s|\*|\?|\$|\%|\^'  | xargs rm -f

# delete 0 byte size files
find . -size 0 -exec rm {} \+

# initial cleanup with respect to previous version: deleted files (may have be moved elsewhere in the tree)
git status --porcelain | egrep "^ D " | cut -b4- | xargs git add

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
MYDATE=$(head -n 1 /tmp/list_of_files.csv | cut -d'|' -f1)
git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "deleted or moved"

# create list for timestamps
find . -type f -printf "%T@|%Tc|%p\n" | grep -v '/.git/' | sort -n | cut -f2- -d'|' > /tmp/list_of_files.csv
cat /tmp/list_of_files.csv | while IFS="|" read MYDATE NAME ; do
    git add "$NAME"
    git diff --cached --quiet --exit-code || \
      git commit --author "${GITAUTHOR}" --date "${MYDATE}" -m "added"
done
git branch releasebranch_4_3
git status
git branch -a



## at the very end: push it to github
git remote add origin git@github.com:grass-svn2git/grass-legacy.git

# create new ssh key for upload to grass-svn2git (here it is called "id_rsa_grass-svn2git[.pub]":
ssh-keygen

# multi ssh key trick: see https://superuser.com/a/912281/71963
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_rsa_grass-svn2git" git push -u origin master
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_rsa_grass-svn2git" git push --all

