#!/bin/sh

# Initialize git repo (preferably use AUTHORS.txt from SVN)

mkdir grass-gis-git
cd grass-gis-git
git svn init --stdlayout https://svn.osgeo.org/grass/grass # --no-metadata 
git svn --authors-file=../AUTHORS.txt fetch

# Create local branches
git branch develbranch_6 origin/develbranch_6
for branch in `git branch -r | grep releasebranch | sed 's#  origin/##g'`; do
    git branch $branch origin/$branch
done
git checkout develbranch_6
git branch -D master
git branch master origin/trunk
git checkout master

# Rename tags
for i in `git branch -r | grep tags`; do
    b=`echo $i | sed 's#origin/##'`
    if [ `echo $i | grep -c release` -gt 0 ] ; then
        j=`echo $i | sed 's#origin/tags/release_[0-9]\+_##g'`
    else
        j=`echo $i | sed 's#origin/tags/##g'`
    fi
    git branch $b $i
    d=`git log -1 --format=%cd --date=iso $b`
    h=`git log -1 --format=%h --date=iso $b`
    GIT_COMMITTER_DATE="$d" git tag -a $j -m "Tagging release $j" $h
done
git checkout master
for i in `git branch | grep tags`; do
    git branch -D $i
done

# Remove remote branches
for i in `git branch -r | grep origin`; do git branch -dr $i; done

# Fix commit messages (#x -> https://trac.osgeo.org/...)
### git reset --hard HEAD && git checkout master
### SCRIPT=`realpath $0` # realpath is a separate package and doesn't need to be installed
### SCRIPTPATH=`dirname $SCRIPT`
### git filter-branch --msg-filter "python  $SCRIPTPATH/rewrite.py" -- --all
# check out /tmp/log.txt for changes overview ...
