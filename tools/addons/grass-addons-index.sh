#!/bin/sh

# PURPOSE: Generates index.html of GRASS GIS Addons
#          http://grass.osgeo.org/grass70/manuals/addons/
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
	    ;;
	"d")
	    label="Display"
	    ;;
	"g")
	    label="General"
	    ;;
	"i")
	    label="Imagery"
	    ;;
	"m")
	    label="Miscellaneous"
	    ;;

	"r")
	    label="Raster"
	    ;;
	"r3")
	    label="3D raster"
	    ;;
	"v")
	    label="Vector"
	    ;;
	"t")
	    label="Temporal"
	    ;;
	"ps")
	    label="Postscript"
	    ;;
	*)
	    label="unknown"
	    ;;
    esac
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

<!-- Generated from: /home/martinl/src/grass-addons/tools/addons/ -->
<!--       See also: https://svn.osgeo.org/grass/grass-addons/tools/addons/README.txt -->

<table><tr><td>
<script type=\"text/javascript\" src=\"https://www.openhub.net/p/grass_gis_addons/widgets/project_factoids_stats?format=js\"></script>
</td><td>
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
See also log files of compilation:
<a href=\"http://grass.osgeo.org/addons/grass${major}/logs\">Linux log files</a> |
<a href=\"http://wingrass.fsv.cvut.cz/x86/grass70/addons/latest/logs/\">Windows log files</a>

</tr></table>
<hr>" > index.html

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
        ${SRC}grass-addons/tools/addons/get_page_description.py $currfile >> index.html
    done

    year=`date +%Y`
    echo "</ul><hr>
&copy; 2013-${year} <a href=\"http://grass.osgeo.org\">GRASS Development Team</a>, GRASS GIS ${major} Addons Reference Manual<br>" >> index.html
    echo "<i><small>`date -u`</small></i>" >> index.html
    echo "</body></html>" >> index.html
}

generate 7 0
generate 6 4

exit 0

