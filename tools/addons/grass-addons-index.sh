#!/bin/sh

# PURPOSE: Generates index.html of GRASS GIS Addons
#          http://grass.osgeo.org/grass70/manuals/addons/
#
# Markus Neteler 9/2002
# updated for GRASS GIS Addons by Markus Neteler and Martin Landa, 2013


##################
# generated Addon HTML manual pages are expected to be in the directory
# /osgeo/grass/grass-cms/grass${major}${minor}/manuals/addons

generate () {
    # 6 4 | 7 0
    major=$1
    minor=$2

    # DEBUG
    # mkdir -p /tmp/grass${major}${minor}/manuals/addons ; cd /tmp/grass${major}${minor}/manuals/addons
    # grass.osgeo.org SERVER
    cd /osgeo/grass/grass-cms/grass${major}${minor}/manuals/addons

    if test -f index.html ; then
	mv index.html index.html.bak
    fi

    TMP=$$

    echo "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">
<html>
<head>
 <title>GRASS GIS ${major} Addons Manual pages</title>
 <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">
 <meta name=\"Author\" content=\"GRASS Development Team\">
 <link rel=\"stylesheet\" href=\"../grassdocs.css\" type=\"text/css\">
</head>
<body bgcolor=\"#FFFFFF\">
<h2>GRASS GIS ${major} Addons Manual pages</h2>

<!-- Generated from: /home/martinl/src/grass-addons/tools/addons/ -->

<a href=\"http://grass.osgeo.org\">GRASS GIS</a> is free software,
anyone may develop his/her own extensions.  The <a
href=\"http://grasswiki.osgeo.org/wiki/AddOns/GRASS_${major}\">GRASS GIS
Add-ons Wiki page</a> contains a growing list of links to GRASS GIS
extensions, which are currently not part of the standard
distribution. They can be easily added to the local installation
through the graphical user interface (<i>Menu - Settings - Addons
Extension - Install</i>) or via the <a
href=\"../g.extension.html\">g.extension</a> command.  <p> <i>These
manual pages are updated daily.</i>
<p> How to contribute?
<p> You may upload your add-on to the <strong>GRASS Add-ons repository</strong>.
Further details about gaining write access to our SVN repository can be found in
<a href=\"http://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASS-Addons-SVNrepository\">this document</a>.
Please also read <a href=\"https://trac.osgeo.org/grass/wiki/Submitting\">GRASS GIS programming best practice</a>.
<p>
See also: <a href=\"http://grass.osgeo.org/addons/grass${major}/logs/summary.html\">log files</a> of compilation.
<p>
<script type=\"text/javascript\" src=\"https://www.openhub.net/p/grass_gis_addons/widgets/project_factoids_stats?format=js\"></script>
<p>
<hr> <ul>" > index.html

    ls -1 *.html | grep -v index.html | sed 's+^+<li style="margin-left: 20px"><a href=+g' | sed 's+$+>+g' > /tmp/a.$TMP

    ls -1 *.html | grep -v index.html | sed 's+\.html$+</a>: +g' > /tmp/b.$TMP

# size
# ls -sh *.html | sed 's/^\ //g' | grep -v total | cut -d' ' -f1 | sed 's/$/\<br\>/g'> /tmp/c.$TMP
# paste -d' ' /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP >> index.html
    
    # fetch one-line descriptions into a separate file:
    # let's try to be more robust against missing keywords in a few HTML pages
    for currfile in `ls -1 *.html | grep -v index.html` ; do
        grep 'KEYWORDS' $currfile 2> /dev/null > /dev/null
        if [ $? -eq 0 ] ; then
           # keywords found, so go ahead with extraction of one-line description
           cat $currfile | awk '/NAME/,/KEYWORDS/' | grep ' - ' | cut -d'-' -f2- | cut -d'<' -f1 | sed 's+>$+></li>+g'  > /tmp/d.$TMP
           # argh, fake keyword line found (broken manual page or missing g.parser usage)
	   if [ ! -s /tmp/d.$TMP ] ; then
	      echo "(incomplete manual page, please fix)" > /tmp/d.$TMP
           fi
	   cat /tmp/d.$TMP >> /tmp/c.$TMP
	   rm -f /tmp/d.$TMP
        else
           # argh, no keywords found (broken manual page or missing g.parser usage)
           echo "(incomplete manual page, please fix)" >> /tmp/c.$TMP
        fi
    done

    # merge it all
    paste -d' ' /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP >> index.html

    echo "</ul>" >> index.html
    echo "<hr>
&copy; 2013-2015 <a href=\"http://grass.osgeo.org\">GRASS Development Team</a>, GRASS GIS ${major} Addons Reference Manual<br>" >> index.html
    echo "<i><small>`date -u`</small></i>" >> index.html
    echo "</body></html>" >> index.html
    rm -f /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP
}

generate 7 0
generate 6 4

exit 0

