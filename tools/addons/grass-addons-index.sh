#!/bin/sh

# PURPOSE: Generates index.html of GRASS GIS Addons
#          https://grass.osgeo.org/grass7/manuals/addons/
#
# Markus Neteler 9/2002
# updated for GRASS GIS Addons by Markus Neteler and Martin Landa, 2013
# updated for new CMS path MN 8/2015
# display module prefix by ML 8/2015

# Important: keep log links in sync at https://grass.osgeo.org/download/addons/

##################
# generated Addon HTML manual pages are expected to be in the directory
# /var/www/grass/grass-cms/grass${major}${minor}/manuals/addons

module_prefix () {
    case "$1" in
	"db")
	    label="Database"
	    anchor="db"
	    ;;
	"d")
	    label="Display"
            anchor="d"
	    ;;
	"g")
	    label="General"
            anchor="g"
	    ;;
	"i")
	    label="Imagery"
            anchor="i"
	    ;;
	"m")
	    label="Miscellaneous"
            anchor="m"
	    ;;
	"r")
	    label="Raster"
            anchor="r"
	    ;;
	"r3")
	    label="3D raster"
            anchor="r3"
	    ;;
	"v")
	    label="Vector"
            anchor="v"
	    ;;
	"t")
	    label="Temporal"
            anchor="t"
	    ;;
	"ps")
	    label="Postscript"
            anchor="ps"
	    ;;
	*)
	    label="unknown"
	    ;;
    esac
    echo "<a name=\"$anchor\"></a>"
    echo "<h3>$label</h3>"
}

generate () {
    # 6 4 | 7 0
    major=$1
    minor=$2

    # DEBUG
    # mkdir -p /tmp/grass${major}${minor}/manuals/addons ; cd /tmp/grass${major}${minor}/manuals/addons
    # grass.osgeo.org SERVER
    cd /var/www/grass/grass-cms/grass${major}${minor}/manuals/addons
    SRC=${HOME}/src/

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

<!-- Generated from: /home/martinl/src/grass_addons/tools/addons/ -->
<!--       See also: https://github.com/OSGeo/grass-addons/blob/master/tools/addons/README.md -->

<table><tr><td>
<script type=\"text/javascript\" src=\"https://www.openhub.net/p/grass_gis_addons/widgets/project_factoids_stats?format=js\"></script>
</td><td>
<a href=\"https://grass.osgeo.org\">GRASS GIS</a> is free software,
anyone may develop his/her own extensions.  The <a
href=\"https://grasswiki.osgeo.org/wiki/AddOns/GRASS_${major}\">GRASS GIS
Add-ons Wiki page</a> contains a growing list of links to GRASS GIS
extensions, which are currently not part of the standard
distribution.<br>
They can be easily <b>installed</b> in the local installation
through the graphical user interface (<i>Menu - Settings - Addons
Extension - Install</i>) or via the <a
href=\"../g.extension.html\">g.extension</a> command.  <p> <i>These
manual pages are updated daily.</i>
<p> How to contribute?
<p> You may upload your add-on to the <strong>GRASS Add-ons repository</strong>.
Further details about gaining write access to our Git repository can be found in
<a href=\"https://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASSaddonsrepository\">this document</a>.
Please also read <a href=\"https://trac.osgeo.org/grass/wiki/Submitting\">GRASS GIS programming best practice</a>.
<p> How to get the source code:
<p> <tt>git clone https://github.com/OSGeo/grass-addons.git</tt>
<p>
See also log files of compilation:
<a href=\"https://grass.osgeo.org/addons/grass${major}/logs\">Linux log files</a> |
<a href=\"https://wingrass.fsv.cvut.cz/grass78/x86_64/addons/latest/logs/\">Windows log files</a>

</tr></table>
<hr>
<div class=\"toc\">
<h4 class=\"toc\">Table of contents</h4>
<ul class=\"toc\">
<li class=\"toc\"><a class=\"toc\" href=\"#d\">Display commands (d.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#db\">Database commands (db.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#g\">General commands (g.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#i\">Imagery commands (i.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#m\">Miscellaneous commands (m.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#ps\">PostScript commands (ps.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#r\">Raster commands (r.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#r3\">3D raster commands (r3.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#t\">Temporal commands (t.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#v\">Vector commands (v.*)</a></li>
</ul>
</div>" > index.html

    prefix_last=""
    for currfile in `ls -1 *.html | grep -v index.html` ; do
	# module prefix
	prefix=`echo $currfile | cut -d'.' -f1`
	if [ -z $prefix_last ] || [ $prefix != $prefix_last ] ; then
	    if [ "$prefix_last" != "" ]; then
		echo "</ul>" >> index.html
	    fi
	    module_prefix $prefix >> index.html
	    echo "<ul>" >> index.html
	    prefix_last=$prefix
	fi

	module=`echo $currfile | sed 's+\.html$++g'`
	echo "<li style=\"margin-left: 20px\"><a href=\"$currfile\">$module</a>: " >> index.html
        ${SRC}/grass-addons/tools/addons/get_page_description.py $currfile >> index.html
    done

    year=`date +%Y`
    echo "</ul><hr>
&copy; 2013-${year} <a href=\"https://grass.osgeo.org\">GRASS Development Team</a>, GRASS GIS ${major} Addons Reference Manual<br>" >> index.html
    echo "<i><small>`date -u`</small></i>" >> index.html
    echo "</body></html>" >> index.html
}

generate 7 8
generate 6 4

exit 0

