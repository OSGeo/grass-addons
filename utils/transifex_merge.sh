#!/bin/bash

# GRASS GIS transifex support script: fetches msg from transifex
# Luca Delucchi 2017, based on gettext message merge procedure by Markus Neteler
# - keep headers added by Markus
# 2018, grass72 -> grass7

# Required installation:
#  sudo pip3 install transifex-client
# see also: https://grasswiki.osgeo.org/wiki/GRASS_messages_translation#Get_the_translated_po_files

# Usage:
# this script has to be launched in the `locale/` directory.
# upon proper installation, the `locale/` directory contains a folder called `transifex`

MSGMERGE="msgmerge -N --no-wrap"

if [ "`basename $PWD`" != "locale" ]; then
  echo "ERROR: run $0 command in locale/ folder of GRASS GIS source code"
  exit 1;
fi

# download the translation from transifex
cd transifex

if [ $? -ne 0 ]; then
  echo "ERROR: transifex folder not found, for requirements see https://grasswiki.osgeo.org/wiki/GRASS_messages_translation#Get_the_translated_po_files"
  exit 1;
fi

# fetch updated po from transifex server into local directory under transifex/.tx/
tx pull -a

cd ..

# merge updated files into existing ones
cd po
NEWPODIR="../transifex/.tx/"
NEWLIBPODIR="${NEWPODIR}grass7.grasslibspot/"

for fil in `ls $NEWLIBPODIR`;
do
  # TODO: keep uppercase for pt_BR etc - rename in SVN as needed
  MYLANG=`echo $fil | sed 's+_translation++g'`

  # LV is not translated in Tx thus skip it
  if [[ ${MYLANG} == "lv" ]]; then
    continue
  fi

  # fix undefined CHARSET in files pulled from transifex (grrr...)
  sed "s+charset=CHARSET+charset=UTF-8+g" ${NEWLIBPODIR}${MYLANG}_translation > ${NEWLIBPODIR}${MYLANG}_translation_new
  sed "s+charset=CHARSET+charset=UTF-8+g" ${NEWPODIR}grass7.grassmodspot/${MYLANG}_translation > ${NEWPODIR}grass7.grassmodspot/${MYLANG}_translation_new
  sed "s+charset=CHARSET+charset=UTF-8+g" ${NEWPODIR}grass7.grasswxpypot/${MYLANG}_translation > ${NEWPODIR}grass7.grasswxpypot/${MYLANG}_translation_new

  # https://www.gnu.org/software/gettext/manual/html_node/msgmerge-Invocation.html#msgmerge-Invocation
  # if po file locally present, update it, otherwise copy over new file from transifex
  if [ -f grasslibs_${MYLANG}.po ]; then
    POFILE=grasslibs_${MYLANG}.po
    grep -m1 -B555 '^$' $POFILE > grasslibs_${MYLANG}.header
    msgcat --use-first --no-wrap grasslibs_${MYLANG}.header ${NEWLIBPODIR}${MYLANG}_translation_new > ${NEWLIBPODIR}${MYLANG}_translation_new.2
    $MSGMERGE ${NEWLIBPODIR}${MYLANG}_translation_new.2 $POFILE -o $POFILE.2 &&  mv $POFILE.2 $POFILE && rm -f grasslibs_${MYLANG}.header
  else
    # update header for newly created files
    # TODO: missing Last-Translator
    POFILE=${NEWLIBPODIR}${MYLANG}_translation_new
    sed -i "s+# SOME DESCRIPTIVE TITLE.+# Translation of grasslibs_${MYLANG}.po+g" $POFILE
    sed -i "s+as the PACKAGE package+as the GRASS GIS package+g" $POFILE
    sed -i "s+# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER+# Copyright (C) 2017 GRASS Development Team+g" $POFILE
    sed -i "s+# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.+# transifex generated, 2017+g" $POFILE
    cp $POFILE grasslibs_${MYLANG}.po
    # fix some header entries in newly created files
    sed -i "s+PACKAGE VERSION+grasslibs_${MYLANG}+g" grasslibs_${MYLANG}.po
    TIMESTAMP=`date +"%Y-%m-%d %H:%M%z"`
    sed -i "s/YEAR-MO-DA HO:MI+ZONE/$TIMESTAMP/g" grasslibs_${MYLANG}.po
  fi

  if [ -f grassmods_${MYLANG}.po ]; then
    POFILE=grassmods_${MYLANG}.po
    grep -m1 -B555 '^$' $POFILE > grassmods_${MYLANG}.header
    msgcat --use-first --no-wrap grassmods_${MYLANG}.header ${NEWPODIR}grass7.grassmodspot/${MYLANG}_translation_new > ${NEWPODIR}grass7.grassmodspot/${MYLANG}_translation_new.2
    $MSGMERGE ${NEWPODIR}grass7.grassmodspot/${MYLANG}_translation_new.2 grassmods_${MYLANG}.po -o grassmods_${MYLANG}.po2 &&  mv grassmods_${MYLANG}.po2 grassmods_${MYLANG}.po && rm -f grassmods_${MYLANG}.header
  else
    # update header for newly created files
    # TODO: missing Project-Id-Version, PO-Revision-Date, Last-Translator
    POFILE=${NEWPODIR}grass7.grassmodspot/${MYLANG}_translation_new
    sed -i "s+# SOME DESCRIPTIVE TITLE.+# Translation of grassmods_${MYLANG}.po+g" $POFILE
    sed -i "s+as the PACKAGE package+as the GRASS GIS package+g" $POFILE
    sed -i "s+# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER+# Copyright (C) 2017 GRASS Development Team+g" $POFILE
    sed -i "s+# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.+# transifex generated, 2017+g" $POFILE
    cp $POFILE grassmods_${MYLANG}.po
    # fix some header entries in newly created files
    sed -i "s+PACKAGE VERSION+grasslibs_${MYLANG}+g" grassmods_${MYLANG}.po
    TIMESTAMP=`date +"%Y-%m-%d %H:%M%z"`
    sed -i "s/YEAR-MO-DA HO:MI+ZONE/$TIMESTAMP/g" grassmods_${MYLANG}.po
  fi

  if [ -f grasswxpy_${MYLANG}.po ]; then
    POFILE=grasswxpy_${MYLANG}.po
    grep -m1 -B555 '^$' $POFILE > grasswxpy_${MYLANG}.header
    msgcat --use-first --no-wrap grasswxpy_${MYLANG}.header ${NEWPODIR}grass7.grasswxpypot/${MYLANG}_translation_new > ${NEWPODIR}grass7.grasswxpypot/${MYLANG}_translation_new.2
    $MSGMERGE ${NEWPODIR}grass7.grasswxpypot/${MYLANG}_translation_new.2 grasswxpy_${MYLANG}.po -o grasswxpy_${MYLANG}.po2 &&  mv grasswxpy_${MYLANG}.po2 grasswxpy_${MYLANG}.po && rm -f grasswxpy_${MYLANG}.header
  else
    # update header for newly created files
    # TODO: missing Project-Id-Version, PO-Revision-Date, Last-Translator
    POFILE=${NEWPODIR}grass7.grasswxpypot/${MYLANG}_translation_new
    sed -i "s+# SOME DESCRIPTIVE TITLE.+# Translation of grasswxpy_${MYLANG}.po+g" $POFILE
    sed -i "s+as the PACKAGE package+as the GRASS GIS package+g" $POFILE
    sed -i "s+# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER+# Copyright (C) 2017 GRASS Development Team+g" $POFILE
    sed -i "s+# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.+# transifex generated, 2017+g" $POFILE
    cp $POFILE grasswxpy_${MYLANG}.po
    # fix some header entries in newly created files
    sed -i "s+PACKAGE VERSION+grasslibs_${MYLANG}+g" grasswxpy_${MYLANG}.po
    TIMESTAMP=`date +"%Y-%m-%d %H:%M%z"`
    sed -i "s/YEAR-MO-DA HO:MI+ZONE/$TIMESTAMP/g" grasswxpy_${MYLANG}.po
  fi
done

# cleanup the po files fetched from transifex
rm -rf ${NEWLIBPODIR} ${NEWPODIR}grass7.grassmodspot/ ${NEWPODIR}grass7.grasswxpypot/
