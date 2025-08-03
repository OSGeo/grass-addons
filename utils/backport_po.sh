#!/bin/sh

# GRASS GIS po files backport script: merges msg from the main branch
# Huidae Cho 2022, based on transifex_merge.sh
# Luca Delucchi 2017, based on gettext message merge procedure by Markus Neteler
# Markus Neteler 2006, original gettext message merge procedure

# see also: https://grasswiki.osgeo.org/wiki/GRASS_messages_translation#Get_the_translated_po_files

# Usage:
# this script has to be launched in the `locale/` directory in a release branch.

MSGMERGE="msgmerge -N --no-wrap"

if [ "`basename $PWD`" != "locale" ]; then
  echo "ERROR: Run `basename $0` command in locale/ folder of GRASS GIS source code"
  exit 1
fi

RELEASEBRANCH=`git branch --show-current`
if [ "$RELEASEBRANCH" = "main" ]; then
  echo "ERROR: Run `basename $0` command in a release branch"
  exit 1
fi

cd po

# copy the po files from the main branch
git checkout main
if [ "`git branch --show-current`" != "main" ]; then
  echo "ERROR: Failed to checkout main"
  exit 1
fi

test -d tmp && rm -rf tmp
mkdir tmp
cp *.po tmp

git checkout $RELEASEBRANCH
if [ "`git branch --show-current`" != "$RELEASEBRANCH" ]; then
  echo "ERROR: Failed to checkout $RELEASEBRANCH"
  exit 1
fi

# merge updated files into existing ones
for POFILE in `ls tmp | grep '\.po$'`; do
  # https://www.gnu.org/software/gettext/manual/html_node/msgmerge-Invocation.html#msgmerge-Invocation
  # if po file locally present, update it, otherwise copy over new file from the main branch
  if [ -f $POFILE ]; then
    $MSGMERGE tmp/$POFILE $POFILE -o $POFILE.2 && mv $POFILE.2 $POFILE
  else
    cp tmp/$POFILE $POFILE
  fi
done

# cleanup the po files fetched from the main branch
rm -rf tmp
