#!/bin/sh

migrate() {
    DIR=$1
    rm -rf $DIR
    cp -r ${DIR}-fetch $DIR
    cd $DIR

    # Remove remote branches
    for i in `git branch -r`; do
        git branch -dr $i
    done
    cd ..
}

migrate "grass-addons"
migrate "grass-promo"
