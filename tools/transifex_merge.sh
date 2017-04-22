#!/bin/bash

# Luca Delucchi 2017

# this script has to be launched in `locale` directory.
# the `locale` directory should contain a folder called `transifex`
# inside the `transifex` folder you need to run the instruction documentated here
# https://grasswiki.osgeo.org/wiki/GRASS_messages_translation#Get_the_translated_po_files 

MSGMERGE="msgmerge -N --no-wrap"

# download the translation from transifex

cd transifex

if [ $? -ne 0 ]; then
  echo "ECHO: transifex folder not found, you should run this command in locale folder"
  exit 1;
fi

tx pull -a

cd ..

cd po
NEWPODIR="../transifex/.tx/"
NEWLIBPODIR="${NEWPODIR}grass72.grasslibspot/"

for fil in `ls $NEWLIBPODIR`;
do
  MYLANG=`echo $fil | rev | cut -c 13- | rev`
  sed "s+charset=CHARSET+charset=UTF-8+g" ${NEWLIBPODIR}${MYLANG}_translation > ${NEWLIBPODIR}${MYLANG}_translation_new
  sed "s+charset=CHARSET+charset=UTF-8+g" ${NEWPODIR}grass72.grassmodspot/${MYLANG}_translation > ${NEWPODIR}grass72.grassmodspot/${MYLANG}_translation_new
  sed "s+charset=CHARSET+charset=UTF-8+g" ${NEWPODIR}grass72.grasswxpypot/${MYLANG}_translation > ${NEWPODIR}grass72.grasswxpypot/${MYLANG}_translation_new
  if [ -f grasslibs_${MYLANG}.po ]; then
    $MSGMERGE ${NEWLIBPODIR}${MYLANG}_translation_new grasslibs_${MYLANG}.po -o grasslibs_${MYLANG}.po2 &&  mv grasslibs_${MYLANG}.po2 grasslibs_${MYLANG}.po
  else
    cp ${NEWLIBPODIR}${MYLANG}_translation_new grasslibs_${MYLANG}.po
  fi
  if [ -f grassmods_${MYLANG}.po ]; then
    $MSGMERGE ${NEWPODIR}grass72.grassmodspot/${MYLANG}_translation_new grassmods_${MYLANG}.po -o grassmods_${MYLANG}.po2 &&  mv grassmods_${MYLANG}.po2 grassmods_${MYLANG}.po
  else
    cp ${NEWPODIR}grass72.grassmodspot/${MYLANG}_translation_new grassmods_${MYLANG}.po
  fi
  if [ -f grasswxpy_${MYLANG}.po ]; then
    $MSGMERGE ${NEWPODIR}grass72.grasswxpypot/${MYLANG}_translation_new grasswxpy_${MYLANG}.po -o grasswxpy_${MYLANG}.po2 &&  mv grasswxpy_${MYLANG}.po2 grasswxpy_${MYLANG}.po
  else
    cp ${NEWPODIR}grass72.grasswxpypot/${MYLANG}_translation_new grasswxpy_${MYLANG}.po
  fi
done
rm -rf ${NEWLIBPODIR} ${NEWPODIR}grass72.grassmodspot/ ${NEWPODIR}grass72.grasswxpypot/
