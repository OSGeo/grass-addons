#!/bin/sh

# PURPOSE: Extracts page one line descriptions for index.html of GRASS GIS Addons

# AUTHORS: Martin Landa

if [ $# -ne 1 ]; then
    echo "$(basename $0) takes exactly one argument (HTML manual page name)"
    exit 1
fi

TMP=$$

currfile=$1

grep 'KEYWORDS' $currfile 2> /dev/null > /dev/null
if [ $? -eq 0 ] ; then
    # keywords found, so go ahead with extraction of one-line description
    cat $currfile | awk '/NAME/,/KEYWORDS/' | grep ' - ' | cut -d'-' -f2- | cut -d'<' -f1 | sed 's+>$+></li>+g'  >> /tmp/d.$TMP
    # argh, fake keyword line found (broken manual page or missing g.parser usage)
    if [ ! -s /tmp/d.$TMP ] ; then
        echo "(incomplete manual page, please fix; name part not found)" > /tmp/d.$TMP
    fi
    cat /tmp/d.$TMP
    rm -f /tmp/d.$TMP
else
    # let's try to be more robust against missing keywords in a few HTML pages
    # argh, no keywords found (broken manual page or missing g.parser usage)
    echo "(incomplete manual page, please fix; keyword part not found)"
fi
