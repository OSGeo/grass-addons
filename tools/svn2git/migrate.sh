#!/bin/sh

# Initialize git repo (preferably use AUTHORS.txt from SVN)

mkdir grass-gis-git ; cd grass-gis-git
git svn init --stdlayout --no-metadata https://svn.osgeo.org/grass/grass
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
    j=`echo $i | sed 's#origin/tags/release_[0-9]\+_##g'`
    git branch $b $i
    git tag -a $j -m "Tagging release $j"
done
git checkout master
for i in `git branch | grep tags`; do
    git branch -D $i
done

# Remove remote branches
for i in `git branch -r | grep origin`; do git branch -dr $i; done

# Fix commit messages (#x -> https://trac.osgeo.org/...)
git reset --hard HEAD && git checkout master
git filter-branch --msg-filter 'python  ../rewrite.py' -- --all
# check out /tmp/log.txt for changes overview ...
