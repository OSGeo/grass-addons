#!/bin/sh

# Markus Neteler 9/2002
# updated for GRASS GIS Addons, 2013

# Generates index.html for existing directory

cd /osgeo/grass/grass-cms/grass70/manuals/addons

if test -f index.html ; then
   mv index.html index.html.bak
   echo "index.html saved to index.html.bak"
fi

TMP=$$

echo "<html>
<head>
 <title>GRASS GIS 7 Addons Manual pages</title>
 <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">
 <meta name=\"Author\" content=\"GRASS Development Team\">
 <link rel=\"stylesheet\" href=\"../grassdocs.css\" type=\"text/css\">
</head>
<body bgcolor=\"#FFFFFF\">
<h2>GRASS GIS 7 Addons Manual pages</h2>

GRASS GIS is free software, anyone may develop his/her own extensions.
The <a href=\"http://grasswiki.osgeo.org/wiki/AddOns/GRASS_7\">GRASS GIS Add-ons Wiki page</a>
contains a growing list of links to GRASS GIS extensions,
which are currently not part of the standard distribution. They can be easily
added to the local installation through the graphical user interface
(Menu - Settings - Addons Extension - Install) or via the "g.extension" command.
<p>
<i>These manual pages are updated weekly.</i>
<p>
How to contribute?
<p>
Please upload your add-ons to <strong>GRASS Add-ons repository</strong>.
Further details about gaining access to our SVN repository can be found in
<a href=\"http://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASS-Addons-SVNrepository\">this document</a>.
<p>
<hr>
" > index.html
ls -1 *.html  | sed 's/^/\<a href=/g' | sed 's/$/\>/g' > /tmp/a.$TMP
ls -1 *.html  | sed 's/$/\<\/a\>\<br\>/g' > /tmp/b.$TMP

# get one-line perhaps like this:
## awk '/NAME/,/KEYWORDS/' | grep ' - ' *.html

# size
# ls -sh *.html | sed 's/^\ //g' | grep -v total | cut -d' ' -f1 | sed 's/$/\<br\>/g'> /tmp/c.$TMP
# paste -d' ' /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP >> index.html

paste -d' ' /tmp/a.$TMP /tmp/b.$TMP >> index.html

echo "<hr>
&copy; 2013-2014 <a href="http://grass.osgeo.org">GRASS Development Team</a>, GRASS GIS 7 Addons Reference Manual<br>" >> index.html
echo "<i><small>`date -u`</small></i>" >> index.html
echo "</body></html>" >> index.html
rm -f /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP
echo "written index.html"

exit 0
