#!/bin/sh

# Indent source code according to modified GRASS GIS submitting rules

# difference to GRASS
# -ut -> --no-tabs

# TODO: replace short options by long ones to improve readability
# TODO: check C++ behavior if we stick to C++

if [ $# -lt 1 ] ; then
 echo "No files specified (give file name(s) as parameter)"
 exit 1
else
 indent -npro -bad -bap -bbb -br -bli0 -bls -cli0 -ncs -fc1 -hnl -i4 \
      -nbbo -nbc -nbfda -nbfde -ncdb -ncdw -nce -nfca -npcs -nprs \
      -npsl -nsc -nsob -saf -sai -saw -sbi0 -ss -ts8 --no-tabs "$@"

 # fix broken gettext macros:
 grep -l '\<_$' "$@" | \
     while read file ; do sed -i -e '/[( \t]_$/{;N;s/\n[ \t]*//;}' $file ; done

 # restore original file with timestamp if indent did not change anything
 cmp "$@"~ "$@" > /dev/null && mv -f "$@"~ "$@"
fi
