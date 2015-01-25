#!/bin/sh

# Markus Neteler 9/2002
# updated for GRASS GIS Addons by Markus Neteler and Martin Landa, 2013

# Generates index.html for existing directory

generate () {
    major=$1
    minor=$2

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

<!-- Generated from: /home/martinl/cronjobs/make_grass7_addons_index.sh -->

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
<p> Please upload your add-ons to <strong>GRASS Add-ons
repository</strong>.  Further details about gaining access to our SVN
repository can be found in <a
href=\"http://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASS-Addons-SVNrepository\">this
document</a>.
<p>
See also: <a href=\"http://wingrass.fsv.cvut.cz/grass70/addons/grass-7.0.0svn/logs/\">log files</a> of compilation.
<p>
<hr> <ul>" > index.html

    ls -1 *.html | grep -v index.html | sed 's+^+<li style="margin-left: 20px"><a href=+g' | sed 's+$+>+g' > /tmp/a.$TMP

    ls -1 *.html | grep -v index.html | sed 's+\.html$+</a>: +g' > /tmp/b.$TMP

# size
# ls -sh *.html | sed 's/^\ //g' | grep -v total | cut -d' ' -f1 | sed 's/$/\<br\>/g'> /tmp/c.$TMP
# paste -d' ' /tmp/a.$TMP /tmp/b.$TMP /tmp/c.$TMP >> index.html
    
    # get one-line description:
    awk '/NAME/,/KEYWORDS/'  *.html | grep ' - ' | cut -d'-' -f2- | cut -d'.' -f1 | cut -d'<' -f1 | sed 's+>$+></li>+g'  > /tmp/c.$TMP

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
