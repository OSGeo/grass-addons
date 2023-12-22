#!/bin/sh

# PURPOSE: Generates index.html of GRASS GIS Addons
#          https://grass.osgeo.org/grass7/manuals/addons/
#          https://grass.osgeo.org/grass8/manuals/addons/
#
# Markus Neteler 9/2002
# updated for GRASS GIS Addons by Markus Neteler and Martin Landa, 2013
# updated for new CMS path MN 8/2015
# display module prefix by ML 8/2015
# updated for GRASS GIS 7 only Addons compilation on grasslxd server by Markus Neteler, 6/2020
# updated for GRASS GIS 7 + 8 Addons compilation on grasslxd server by Markus Neteler, 12/2021

# Important: keep log links in sync at https://grass.osgeo.org/download/addons/

####
# Requirements: ./get_page_description.py

CRONJOBDIR=~/cronjobs/
MAJOR=$1
MINOR=$2
PATCH=$3

##################
# generated Addon HTML manual pages are expected to be in the directory
# /var/www/code_and_data/grass${major}${minor}/manuals/addons/

if [ $# -ne 4 ] ; then
  echo "ERROR: addon manpath required.

Usage:

$0 GMAJOR GMINOR GPATCH manpath"
  exit 1
fi


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
    # 7 8 manpath | 8 0 manpath
    major=$1
    minor=$2
    patch=$3
    manpath=$4

    if [ "$major" -eq 7 ]; then
        win_log_url="https://wingrass.fsv.cvut.cz/grass${major}${minor}/x86_64/addons/grass-${major}.${minor}.${patch}/logs/"
    else
        win_log_url="https://wingrass.fsv.cvut.cz/grass${major}${minor}/addons/grass-${major}.${minor}.${patch}/logs/"
    fi

    # DEBUG
    # mkdir -p /tmp/grass${major}${minor}/manuals/addons ; cd /tmp/grass${major}${minor}/manuals/addons
    cd $manpath

    if test -f index.html ; then
	mv index.html index.html.bak
    fi

    TMP=$$
    LASTDATE=`date +"%d %b %Y"`

    echo "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">
<html>
<head>
 <title>GRASS GIS ${major}.${minor} Addons Manual pages</title>
 <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">
 <meta name=\"Author\" content=\"GRASS Development Team\">
 <link rel=\"stylesheet\" href=\"../grassdocs.css\" type=\"text/css\">
</head>
<body bgcolor=\"#FFFFFF\">
<h2>GRASS GIS ${major}.${minor} Addons Manual pages</h2>

<!-- Generated from: grasslxd (on osgeo7): ~/cronjobs/grass-addons-index.sh -->
<!--       See also: https://github.com/OSGeo/grass-addons/tree/grass8/utils/cronjobs_osgeo_lxd/README.md -->

<table><tr><td>
<script type=\"text/javascript\" src=\"https://www.openhub.net/p/grass_gis_addons/widgets/project_factoids_stats?format=js\"></script>
</td><td>
<a href=\"https://grass.osgeo.org\">GRASS GIS</a> is free software,
anyone may develop his/her own extensions (addons).  The <a
href=\"https://github.com/OSGeo/grass-addons\">GRASS GIS
Addons repository</a> on GitHub contains a growing list of links to GRASS GIS
extensions, which are currently not part of the core software package.<br>
Addons can easily be <b>installed</b> in your local GRASS GIS installation
through the graphical user interface (<i>Menu - Settings - Addons
Extension - Install</i>) or via the <a
href=\"../g.extension.html\">g.extension</a> command.  <p> <i>These
manual pages are updated daily. Last run: $LASTDATE</i>
<p> How to contribute?
<p> You may propose your Addon to the <a href=\"https://github.com/OSGeo/grass-addons\">GRASS GIS
Addons repository</a>. Please read the <a href=\"https://github.com/OSGeo/grass-addons/blob/grass8/CONTRIBUTING.md\">Contributing</a>
document as well as the <a href=\"https://trac.osgeo.org/grass/wiki/Submitting\">GRASS GIS programming best practice</a>.
<p> How to get the addons source code:
<p> <tt>git clone https://github.com/OSGeo/grass-addons.git</tt>
<p>
See also log files of compilation:
<a href=\"https://grass.osgeo.org/addons/grass${major}/logs\">Linux log files</a> |
<a href=\"${win_log_url}\">Windows log files</a>

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
        python3 $CRONJOBDIR/get_page_description.py $currfile >> index.html
    done

    year=`date +%Y`
    echo "</ul><hr>
&copy; 2013-${year} <a href=\"https://grass.osgeo.org\">GRASS Development Team</a>, GRASS GIS ${major} Addons Reference Manual<br>" >> index.html
    echo "<i><small>`date -u`</small></i>" >> index.html
    echo "</body></html>" >> index.html
    rm -f index.html.bak
}

## main
# $4 is path to addons manual directory:
generate $MAJOR $MINOR $PATCH $4

exit 0
