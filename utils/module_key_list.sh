#!/bin/sh

############################################################################
#
# MODULE:       module_key_list.sh
# AUTHOR(S):    Hamish Bowman, Dunedin, New Zealand
# PURPOSE:      make a list of all the module options for later comparison
# COPYRIGHT:    (C) 2012 GRASS Development Team/hb
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %Module
# %  description: Generates a list of all modules' option and flag names.
# %  keywords: infrastructure
# %End


if [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program." 1>&2
    exit 1
fi

if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi


TEMPFILE="`g.tempfile pid=$$`"
if [ $? -ne 0 ] || [ -z "$TEMPFILE" ] ; then
    g.message -e "Unable to create temporary files"
    exit 1
fi

#### check if we have awk
if [ ! -x "`which xml2`" ] ; then
    g.message -e "xml2 is required, please install it first"
    exit 1
fi

OUTFILE="module_key_list_$GRASS_VERSION.txt"

# check if we will overwrite data
if [ -e "$OUTFILE" ] ; then
   if [ -z "$GRASS_OVERWRITE" ] || [ "$GRASS_OVERWRITE" -ne 1 ] ; then
      g.message -e "Output file <$OUTFILE> already exists."
      exit 1
   fi
fi

BASE_DIR="`pwd`"

cd "$GISBASE"

for MOD in bin/* scripts/* ; do
    MODULE=`basename "$MOD"`
    if [ "$MODULE" = "g.parser" ] || \
       [ "$MODULE" = "r.mapcalc" ] || \
       [ "$MODULE" = "r3.mapcalc" ] ; then
	continue
    fi

    g.message -v "[$MODULE]"
    "$MODULE"  --interface-description >> "$TEMPFILE"
done


# -i is a GNU extension, won't work on a Mac?
sed -i -e 's/^<?xml .*//' -e 's/^<!DOCTYPE .*//' "$TEMPFILE"

cat << EOF > "$TEMPFILE.header"
<?xml version="1.0" encoding="ANSI_X3.4-1968"?>
<!DOCTYPE task SYSTEM "grass-interface.dtd">
<modules>
EOF

cat << EOF > "$TEMPFILE.footer"
</modules>
EOF

cat "$TEMPFILE.header" "$TEMPFILE" "$TEMPFILE.footer" > "$TEMPFILE.xml"



cd "$BASE_DIR"

echo "# `g.version`module key list -- `date`" > "$OUTFILE"

xml2 < "$TEMPFILE.xml" | grep '/@name=' | \
   sed -e 's+^/modules/task/++' -e 's+@name=+name=+' \
       -e 's+^\(name=\)+\n\1+' -e 's/name=//'| \
   grep -v '^flag/verbose$\|^flag/quiet$' \
 >> "$OUTFILE"


g.message "List written to <$OUTFILE>."
g.message " Next run: diff -U 7 module_key_list_\$OLD.txt module_key_list_\$NEW.txt"

## todo: how to sort per-module params and flags so a re-arrangement of
##       order doesn't indicate an interface change?


#cleanup
rm -f "$TEMPFILE" "$TEMPFILE.xml" "$TEMPFILE.header" "$TEMPFILE.footer"

exit 0


#########################################################################
### howto get this to work ????
# see http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=506788

BASE="modules/task"
FIELDS="
@name
parameter/@name
flag/@name
"

xml2 < "$TEMPFILE.xml" | grep '/@name=' |
   grep -v '/flag/@name=verbose$\|/flag/@name=quiet' | \
   2csv -d'|' $BASE $FIELDS | less
