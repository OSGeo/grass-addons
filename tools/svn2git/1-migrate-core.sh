#!/bin/sh

migrate_git() {
    DIR=$1
    
    rm -rf $DIR
    cp -ra ${DIR}-fetch $DIR
    cd $DIR

    # Create local branches
    if [ $DIR = "grass" ] ; then
        branch_filter="releasebranch_7"
    else
        branch_filter="releasebranch_[0-6]"
    fi
    for branch in `git branch -r | grep $branch_filter | sed 's#  origin/##g'`; do
        git branch $branch origin/$branch
        git checkout $branch
    done
    git branch -D master
    if [ $DIR = "grass" ] ; then
        git branch master origin/trunk
        git checkout master
    fi

    # Rename tags
    if [ $DIR = "grass" ] ; then
        tag_filter="grass_7"
    else
        tag_filter="grass_[0-6]"
    fi
    for i in `git branch -r | grep tags | grep $tag_filter`; do
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

    if [ $DIR = "grass" ] ; then
        git checkout master
    fi
    for i in `git branch | grep tags`; do
        git branch -D $i
    done

    # Remove remote branches
    for i in `git branch -r | grep origin`; do
        git branch -dr $i
    done

    cd ..
}

migrate_git "grass"
migrate_git "grass-legacy"
