#!/bin/sh

SCRIPT=`realpath $0` # realpath is a separate package and doesn't need to be installed
SCRIPTPATH=`dirname $SCRIPT`

rewrite_msg() {
    repo=$1

    cd $repo
    
    # Fix commit messages (#x -> https://trac.osgeo.org/...)
    git reset --hard HEAD
    for b in `git branch | cut -c 3-`; do
        echo $b
        git checkout $b
        git filter-branch --msg-filter "python  $SCRIPTPATH/rewrite.py" -- --all
        mv /tmp/log_touched.txt ../log_${repo}_${b}_touched.txt
        mv /tmp/log_untouched.txt ../log_${repo}_${b}_untouched.txt
    done

    cd ..
}

rewrite_msg "grass"
rewrite_msg "grass-legacy"
rewrite_msg "grass-addons"
rewrite_msg "grass-promo"
