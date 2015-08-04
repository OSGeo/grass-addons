#!/bin/sh

# Markus Neteler 9/2002
# updated for GRASS GIS Addons, 2013

# Generates index.html for existing directory

if test -z "$1" ; then
    echo "Missing DEST"
    exit 1
fi

DEST="$1"
MAJOR="$2"
MINOR="$3"

cd $DEST/grass${MAJOR}${MINOR}/manuals/addons

if test -f index.html ; then
   mv index.html index.html.bak
fi

TMP=$$

echo "<html>
<head>
 <title>GRASS GIS ${MAJOR} Addons Manual pages</title>
 <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">
 <meta name=\"Author\" content=\"GRASS Development Team\">
 <link rel=\"stylesheet\" href=\"grassdocs.css\" type=\"text/css\">
</head>
<body width=\"100%\">
<h1>GRASS GIS ${MAJOR} Addons Manual pages</h1>

<a href=\"http://grass.osgeo.org\">GRASS GIS</a> is free software, anyone may develop his/her own extensions.
The <a href=\"http://grasswiki.osgeo.org/wiki/AddOns/GRASS_${MAJOR}\">GRASS GIS Add-ons Wiki page</a>
contains a growing list of links to GRASS GIS extensions,
which are currently not part of the standard distribution. They can be easily
added to the local installation through the graphical user interface
(Menu - Settings - Addons Extension - Install) or via the <a href=\"http://grass.osgeo.org/grass${MAJOR}${MINOR}/manuals/g.extension.html\">g.extension</a> command.
<p>
<i>These manual pages are updated regularly.</i>
<p>
How to contribute?
<p>
Please upload your add-ons to <strong>GRASS Add-ons repository</strong>.
Further details about gaining access to our SVN repository can be found in
<a href=\"http://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASS-Addons-SVNrepository\">this document</a>.
<p>
<hr>
<ul>
" > index.html
ls -1 *.html  | sed 's/^/\<li style=\"padding: 5px\"\>\<a href=/g' | sed 's/$/\>/g' > /tmp/a.$TMP
ls -1 *.html  | sed 's/$/\<\/a\>\<\/li\>/g' | sed 's/.html//g' > /tmp/b.$TMP

# get one-line perhaps like this:
## awk '/NAME/,/KEYWORDS/' | grep ' - ' *.html

# size
# ls -sh *.html | sed 's/^\ //g' | grep -v total | cut -d' ' -f1 | sed 's/$/\<br\>/g'> /tmp/c.$TMP
# paste -d' ' /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP >> index.html

paste -d' ' /tmp/a.$TMP /tmp/b.$TMP >> index.html

year=`date +%Y`
echo "</ul><hr>
&copy; 2013-${year} <a href="http://grass.osgeo.org">GRASS Development Team</a>, GRASS GIS 7 Addons Reference Manual<br>" >> index.html
echo "<i>`date -u`</i>" >> index.html
echo "</body></html>" >> index.html
rm -f /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP

chgrp -R grass $DEST/grass${MAJOR}${MINOR}/manuals/addons
chmod -R g+w $DEST/grass${MAJOR}${MINOR}/manuals/addons

exit 0
