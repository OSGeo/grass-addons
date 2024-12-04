#!/bin/sh
# Compile GRASS GIS Addons
set -e

test -d "$1" && cd "$1"

export PATH=/c/msys64/usr/bin:${PATH}
# export PYTHONPATH=
export LANGUAGE=C
export OSGEO4W_ROOT_MSYS="/c/OSGeo4W"

SRC_PATH=$(pwd)/src
# GISBASE_PATH=/c/msys64/usr/src
TARGET_PATH=$(pwd)/build
GRASS_PATH=$OSGEO4W_ROOT_MSYS/apps/grass8

fetchenv() {
    local IFS
    IFS=
    batch=$1
    shift
    srcenv=$(mktemp /tmp/srcenv.XXXXXXXXXX)
    dstenv=$(mktemp /tmp/dstenv.XXXXXXXXXX)
    diffenv=$(mktemp /tmp/diffenv.XXXXXXXXXX)
    args="$@"
    cmd.exe //c set >$srcenv
    cmd.exe //c "call `cygpath -w $batch` $args \>nul 2\>nul \& set" >$dstenv
    diff -u $srcenv $dstenv | sed -f ${SRC_GRASS}/mswindows/osgeo4w/envdiff.sed >$diffenv
    . $diffenv
    PATH=$PATH:/usr/bin:/mingw64/bin/:$PWD/mswindows/osgeo4w/lib:$PWD/mswindows/osgeo4w:/c/windows32/system32:/c/windows:/c/windows32/system32:/c/windows
    rm -f $srcenv $dstenv $diffenv
}

function compile {
    SRC_PATH="$1"
    GRASS_PATH="$2"
    TARGET_PATH="$3"
    GRASS_VERSION=`echo -n ${SRC_PATH} | tail -c 1`
    INDEX_FILE="index"

    if [ ! -d "$3" ] ; then
        mkdir -p "$3"
    fi

    if [ -n "$4" ] ; then
        SEP=1 # useful for collecting files (see build-xml.py)
    else
        SEP=0
    fi

    PLATFORM=x86_64

    rm -rf "$TARGET_PATH"
    mkdir  "$TARGET_PATH"

    cd "$SRC_PATH"

    date=`date -R`
    uname=`uname`
    mkdir "$TARGET_PATH/logs"
    touch "$TARGET_PATH/logs/${INDEX_FILE}.log"
    echo "<!--<?xml-stylesheet href=\"style.css\" type=\"text/css\"?>-->
    <!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\"
              \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">

    <html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\" >

    <head>
    <meta http-equiv=\"Content-Type\" content=\"application/xhtml+xml; charset=utf-8\" />
    <title>GRASS $TARGET_PATH AddOns Logs ($PLATFORM)</title>
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
    <h1>GRASS $GRASS_VERSION AddOns ($PLATFORM) / $uname (logs generated $date)</h1>
    <hr /> 
    <table cellpadding=\"5\">
    <tr><th style=\"background-color: grey\">AddOns</th>
    <th style=\"background-color: grey\">Status</th>
    <th style=\"background-color: grey\">Log file</th></tr>" > "$TARGET_PATH/logs/${INDEX_FILE}.html"

    echo "-----------------------------------------------------"
    echo "AddOns '$TARGET_PATH'..."
    echo "-----------------------------------------------------"

    pwd=`pwd`
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
                path="$TARGET_PATH/$m"
            else
                path="$TARGET_PATH"
            fi

            export GRASS_ADDON_BASE=$path
            echo "<tr><td><tt>$c/$m</tt></td>" >> "$TARGET_PATH/logs/${INDEX_FILE}.html"
            make MODULE_TOPDIR="$GRASS_PATH" clean > /dev/null 2>&1
            make MODULE_TOPDIR="$GRASS_PATH" \
                BIN="$path/bin" \
                HTMLDIR="$path/docs/html" \
                MANBASEDIR="$path/docs/man" \
                SCRIPTDIR="$path/scripts" \
                ETC="$path/etc" \
                SOURCE_URL="https://github.com/OSGeo/grass-addons/tree/master/grass${GRASS_VERSION}/" > \
                "$TARGET_PATH/logs/$m.log" 2>&1
            if [ `echo $?` -eq 0 ] ; then
                printf "%-30s%s\n" "$c/$m" "SUCCESS" >> "$TARGET_PATH/logs/${INDEX_FILE}.log"
                echo " SUCCESS"
                echo "<td style=\"background-color: green\">SUCCESS</td>" >> "$TARGET_PATH/logs/${INDEX_FILE}.html"
            else
                printf "%-30s%s\n" "$c/$m" "FAILED" >> "$TARGET_PATH/logs/${INDEX_FILE}.log"
                echo " FAILED"
                echo "<td style=\"background-color: red\">FAILED</td>" >> "$TARGET_PATH/logs/${INDEX_FILE}.html"
            fi
            echo "<td><a href=\"$m.log\">log</a></td></tr>" >> "$TARGET_PATH/logs/${INDEX_FILE}.html"
            cd ..
        done
        cd $pwd
        unset GRASS_ADDON_BASE
    done

    echo "</table><hr />
    <div style=\"text-align: right\">Valid: <a href=\"http://validator.w3.org/check/referer\">XHTML</a></div>
    </body></html>" >> "$TARGET_PATH/logs/${INDEX_FILE}.html"
}

function build_addons {
    SRC_GRASS=${GISBASE_PATH}/grass$1
    fetchenv $OSGEO4W_ROOT_MSYS/bin/o4w_env.bat
    export PATH=${PATH}:/c/msys64/usr/bin:/c/msys64/mingw64/bin

    rm -rf $TARGET_PATH
    compile $SRC_PATH $GRASS_PATH $TARGET_PATH 1
    cd $TARGET_PATH
    for d in `ls -d */`; do
	mod=${d%%/}
	if [ $mod == "logs" ] ; then
	    continue
	fi
	cd $mod
	echo $mod
	for f in `ls bin/*.bat 2> /dev/null` ; do
	    echo $f
	    if [ `echo $1 | sed -e 's/\(^.*\)\(.$\)/\2/'` = "6" ] ; then
		replace_gisbase="GRASS_TARGET_PATH"
	    else
		replace_gisbase="GRASS_ADDON_BASE"
	    fi
	    sed "s/GISBASE/$replace_gisbase/" $f > tmp
	    mv tmp $f
	done
	zip -r $mod.zip *
	mv $mod.zip ..
	cd ..
	md5sum $mod.zip > ${mod}.md5sum
    done
}

while read release; do
    build_addons $release
done < $(pwd)/.github/workflows/grass_versions.csv

exit 0
