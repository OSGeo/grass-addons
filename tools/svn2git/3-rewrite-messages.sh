#!/bin/sh

SCRIPT=`realpath $0` # realpath is a separate package and doesn't need to be installed
SCRIPTPATH=`dirname $SCRIPT`

# Note: range can be applied by
# ... -- 244063d26e4d541039e4af7ab7191801591ebce8..HEAD

rewrite_msg() {
    repo=$1

    cd $repo
    
    # Fix commit messages (#x -> https://trac.osgeo.org/...)
    git reset --hard HEAD
    git filter-branch --msg-filter "python  $SCRIPTPATH/rewrite.py" -- --all
    mv /tmp/log_touched.txt ../log_${repo}__touched.txt
    mv /tmp/log_untouched.txt ../log_${repo}_untouched.txt

    cd ..
}

rewrite_msg "grass"
rewrite_msg "grass-legacy"
rewrite_msg "grass-addons"
rewrite_msg "grass-promo"
