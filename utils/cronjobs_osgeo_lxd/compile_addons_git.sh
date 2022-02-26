#!/bin/sh

# Martin Landa, 2013
# updated for GRASS GIS 7 (only) Addons by Markus Neteler, 2020
# fixes for addon creation by Tomas Zigo, 2020
# changes to variables by Markus Neteler, 2021

# This script compiles GRASS Addons, it's called by cron_grass${GMAJOR}_main_build_binaries.sh | cron_grass${GMAJOR}_main_src_snapshot.sh

#################

if [ -z "$1" ]; then
    echo "ERROR: Set GRASS GIS major version"
    exit 1
fi

if [ -z "$2" ]; then
    echo "ERROR: Set GRASS GIS minor version"
    exit 1
fi

GMAJOR="$1"
GMINOR="$2"

if [ `uname -m` = "x86_64" ] ; then
    PLATFORM=x86_64
else
    PLATFORM=x86
fi

if [ -z "$3" ]; then
    echo "Usage: $0 grass_major_version grass_minor_version git_path \
topdir addons_path grass_startup_program [separate]"
    echo "eg. $0 8 0 ~/src/grass_addons/grass${GMAJOR}/ \
~/src/releasebranch_${GMAJOR}_${GMINOR}/dist.${PLATFORM}-pc-linux-gnu \
~/.grass${GMAJOR}/addons \
~/src/releasebranch_${GMAJOR}_${GMINOR}/bin.${PLATFORM}-pc-linux-gnu/grass${GMAJOR}"
    exit 1
fi

GIT_PATH="$3"
TOPDIR="$4"
ADDON_PATH="$5"
GRASS_STARTUP_PROGRAM="$6"
INDEX_FILE="index"
INDEX_MANUAL_PAGES_FILE="index_manual_pages"
ADDONS_PATHS_JSON_FILE="addons_paths.json"

if [ ! -d "$5" ] ; then
    mkdir -p "$5"
fi

if [ -z "$6" ] ; then
    echo "ERROR: Set GRASS GIS startup program with full path (e.g., ~/src/releasebranch_${GMAJOR}_${GMINOR}/bin.${PLATFORM}-pc-linux-gnu/grass${GMAJOR})"
    exit 1
fi

if [ -n "$7" ] ; then
    SEP=1 # useful for collecting files (see build-xml.py)
else
    SEP=0
fi

rm -rf "$ADDON_PATH"
mkdir  "$ADDON_PATH"

cd "$GIT_PATH"

date=`date -R`
uname=`uname`
mkdir "$ADDON_PATH/logs"
touch "$ADDON_PATH/logs/${INDEX_FILE}.log"

html_template="<!--<?xml-stylesheet href=\"style.css\" type=\"text/css\"?>-->
<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\"
      \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">

<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\" >

<head>
<meta http-equiv=\"Content-Type\" content=\"application/xhtml+xml; charset=utf-8\" />
<title>GRASS $ADDON_PATH AddOns Logs ($PLATFORM)</title>
<style type=\"text/css\">
h1 { font-size: 125%; font-weight: bold; }
table
{
border-collapse:collapse;
}
table,th, td
{
border: 1px solid black;
}
</style>
</head>
<body>
<h1>GRASS $GMAJOR Addons ($PLATFORM) / $uname (logs generated $date)</h1>
<hr />
<table cellpadding=\"5\">
<tr><th style=\"background-color: grey\">AddOns</th>
<th style=\"background-color: grey\">Status</th>"

# initiate the index file
echo "$html_template" > "$ADDON_PATH/logs/${INDEX_FILE}.html"
echo "<th style=\"background-color: grey\">Log file</th></tr>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"

echo "$html_template" > "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.html"

echo "-----------------------------------------------------"
echo "Addons '$ADDON_PATH'..."
echo "-----------------------------------------------------"

pwd=`pwd`
# .. "hadoop"
# from ../../grass${GMAJOR}/
for c in "db" "display" "general" "gui/wxpython" "imagery" "misc" "raster" "raster3d" "temporal" "vector" ; do
    if [ ! -d $c ]; then
        continue
    fi
    cd $c
    for m in `ls -d */Makefile 2>/dev/null` ; do
    m="${m%%/Makefile}"
    echo -n "Compiling $m..."
    cd "$m"
    if [ $SEP -eq 1 ] ; then
        path="$ADDON_PATH/$m"
    else
        path="$ADDON_PATH"
    fi

    export GRASS_ADDON_BASE=$path
    if [ ! -f $GRASS_ADDON_BASE ]; then
        # Create addon dir first for download addons_paths.json file if
        # addon has own dir e.g. ~/.grass8/addons/db.join/ with bin/ docs/
        # etc/ scripts/ subdir (check condition $SEP -eq 1)
        mkdir $GRASS_ADDON_BASE
    fi
    # Try download Add-Ons json file paths
    if [ ! -f "$GRASS_ADDON_BASE/$ADDONS_PATHS_JSON_FILE" ] && [ ! -f "$(dirname $GRASS_ADDON_BASE)/$ADDONS_PATHS_JSON_FILE" ]; then
        $GRASS_STARTUP_PROGRAM --tmp-location EPSG:4326 --exec g.extension -j
        # Prevent download addons_paths.json file for every addon compilation if
        # addon has own dir e.g. ~/.grass8/addons/db.join/ with bin/ docs/
        # etc/ scripts/ subdir (check condition $SEP -eq 1)
        if [ ! -f "$(dirname $GRASS_ADDON_BASE)/$ADDONS_PATHS_JSON_FILE" ]; then
            mv "$GRASS_ADDON_BASE/$ADDONS_PATHS_JSON_FILE" "$(dirname $GRASS_ADDON_BASE)/$ADDONS_PATHS_JSON_FILE"
        fi
    fi
    echo "<tr><td><tt>$c/$m</tt></td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
    make MODULE_TOPDIR="$TOPDIR" clean > /dev/null 2>&1
    make MODULE_TOPDIR="$TOPDIR" \
        BIN="$path/bin" \
        HTMLDIR="$path/docs/html" \
        MANBASEDIR="$path/docs/man" \
        SCRIPTDIR="$path/scripts" \
        ETC="$path/etc" \
            SOURCE_URL="https://github.com/OSGeo/grass-addons/tree/grass${GMAJOR}/src/" > \
            "$ADDON_PATH/logs/$m.log" 2>&1 \
        HTML_PAGE_FOOTER_PAGES_PATH="../"
    if [ `echo $?` -eq 0 ] ; then
        printf "%-30s%s\n" "$c/$m" "SUCCESS" >> "$ADDON_PATH/logs/${INDEX_FILE}.log"
        echo " SUCCESS"
        echo "<td style=\"background-color: green\">SUCCESS</td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
    else
        printf "%-30s%s\n" "$c/$m" "FAILED" >> "$ADDON_PATH/logs/${INDEX_FILE}.log"
        echo " FAILED"
        echo "<td style=\"background-color: red\">FAILED</td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
    fi
    echo "<td><a href=\"$m.log\">log</a></td></tr>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
    cd ..
    done
    cd $pwd
    unset GRASS_ADDON_BASE
done

echo "</table><hr />
<div style=\"text-align: right\">Valid: <a href=\"http://validator.w3.org/check/referer\">XHTML</a></div>
</body></html>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"

echo ""
bash ~/cronjobs/check_addons_urls.sh "$ADDON_PATH" \
   "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.log" \
   "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.html"
echo ""

echo "</table><hr />
<div style=\"text-align: right\">Valid: <a href=\"http://validator.w3.org/check/referer\">XHTML</a></div>
</body></html>" >> "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.html"

echo "Log file written to <$ADDON_PATH/logs/>"
exit 0
