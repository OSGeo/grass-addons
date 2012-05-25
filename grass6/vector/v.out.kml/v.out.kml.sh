#!/bin/sh

############################################################################
#
# MODULE:       v.out.kml
# AUTHOR(S):    Peter Loewe <peter.loewe AT grass-verein.de>
# PURPOSE:      Export GRASS point/line/area-vectors into a KML file in 
#               geographic coordinates (lat lon).
# COPYRIGHT:    (c) 2007 Peter Loewe and the GRASS DEVELOPMENT TEAM
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# updates:
#
# 7 July 2007  (PL): added support for database-columns
#10 July 2007  (PL): typos fixed
#28 July 2007  (PL): improvement of cleanup operations: Thanks to Jean-Noel Candau
#############################################################################

#%Module
#%  description: Creates a KML-file from GRASS point/line/polygon vectors   
#%End
#%flag
#%  key: l
#%  description: Force line-vector export: Areas are exported as lines/polylines (default).
#%end
#%flag
#%  key: y
#%  description: Force polygon export: Areas are exported as polygons with a fillcolor and fill-transparency.
#%end
#%flag
#%  key: p
#%  description: Point-vector (sites) export: Point data are exported.
#%end
#%flag
#%  key: r
#%  description: Random colors: All line and area colors (if needed) are set to random values.
#%end
#%option
#% key: map
#% type: string
#% gisprompt: old,vector,vector
#% description: vector input map
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new_file,file,file
#% description: name/path of kml output
#% required : no
#%end
#%option
#% key: ogrpath
#% type: string
#% gisprompt: old_file,file,file
#% description: optional path to ogr2ogr
#% required : no
#%end
#%option
#% key: color
#% type: string
#% gisprompt: color,grass,color
#% description: hexcode triplet for line color (blue:green:red 00:00:00-255:255:255) 
#% answer : 00:200:00
#% required : no
#%end
#%option
#% key: transparency
#% type: string
#% description: integer for vector line transparency (0=invisible 255=opaque)
#% answer : 255
#% required : no
#%end
#%option
#% key: fcolor
#% type: string
#% gisprompt: color,grass,color
#% description: hexcode triplet for polygon fill color (blue:green:red 00:00:00-255:255:255)
#% answer : 00:100:00
#% required : no
#%end
#%option
#% key: ftransparency
#% type: string
#% description: integer for polygon transparency (00=invisible 255=opaque)
#% answer : 255
#% required : no
#%end
#%option
#% key: size
#% type: string
#% description: width of the vector lines (default is 1)
#% options: 0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10
#% answer : 1
#% required : no
#%end
#%option
#% key: iconcode
#% type: string
#% description: Select an icons number within its palette for point-vectors 
#% options: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45
#% answer : 1
#% required : no
#%end
#%option
#% key: iconpalette
#% type: string
#% description: Select a KML palette of icons for point-vectors 
#% options: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
#% answer : 1
#% required :no
#%end
#%option
#% key: iconcolor
#% type: string
#% gisprompt: color,grass,color
#% description: hexcode color triplet for point-vectors (blue:green:red 00:00:00-255:255:255) 
#% answer : 00:200:00
#% required : no
#%end
#%option
#% key: icontransparency
#% type: string
#% description: integer for point-vector transparency (0=invisible 255=opaque 0-255)
#% answer : 255
#% required : no
#%end
#%option
#% key: iconurl
#% type: string
#% description: Provide a URL pointing to a symbol for point-vectors 
#% required : no
#%end
#%option
#% key: linecolumn
#% type: string
#% description: column name string for line color ([xxx]:xxx:xxx:xxx). Transparency should be provided as first value, unless 3-Flag is set.
#% required : no
#%end
#%option
#% key: fillcolumn
#% type: string
#% description: column name string for area fill color ([xxx]:xxx:xxx:xxx). Transparency should be provided as first value, unless 3-Flag is set.
#% required : no
#%end

#%option
#% key: linetranscolumn
#% type: string
#% description: column name string for line transparency (xxx). This option is overridden by the 'transparency'-option.
#% required : no
#%end
#%option
#% key: filltranscolumn
#% type: string
#% description: column name string for fill transparency (xxx). This option is overridden by the 'transparency'-option.
#% required : no
#%end

#
### Let's seperate the Flag and Option-Names from the variables used in the script.
### This is good practice if we have to change terms in the GUI/frontend.
#

FLAG_FORCE_LINE_EXPORT=${GIS_FLAG_L}
FLAG_FORCE_POLYGON_EXPORT=${GIS_FLAG_Y}
FLAG_POINT_EXPORT=${GIS_FLAG_P}
FLAG_RANDOM_COLORS=${GIS_FLAG_R}


OPT_MAP=${GIS_OPT_MAP}
OPT_OUTPUT=${GIS_OPT_OUTPUT}
OPT_OGRPATH=${GIS_OPT_OGRPATH}
OPT_LINE_COLOR=${GIS_OPT_COLOR}
OPT_LINE_TRANS=${GIS_OPT_TRANSPARENCY}
OPT_FILL_COLOR=${GIS_OPT_FCOLOR}
OPT_FILL_TRANS=${GIS_OPT_FTRANSPARENCY}
OPT_LINE_SIZE=${GIS_OPT_SIZE}
OPT_ICON_CODE=${GIS_OPT_ICONCODE}
OPT_ICON_PALETTE=${GIS_OPT_ICONPALETTE}
OPT_ICON_COLOR=${GIS_OPT_ICONCOLOR}
OPT_ICON_TRANS=${GIS_OPT_ICONTRANSPARENCY}
OPT_ICON_URL=${GIS_OPT_ICONURL}
OPT_COLUMN_LINE_COLOR=${GIS_OPT_LINECOLUMN}
OPT_COLUMN_LINE_TRANS=${GIS_OPT_LINETRANSCOLUMN}
OPT_COLUMN_FILL_COLOR=${GIS_OPT_FILLCOLUMN}
OPT_COLUMN_FILL_TRANS=${GIS_OPT_FILLTRANSCOLUMN}

##############################################################
TMPDIR=`g.gisenv get="GISDBASE"`
#TMPDIR is used to create the inner temporary latlon location

#################################################################################
# name:     CLEANUP_TEMPFILES
# purpose:  Removes all temporary files which might have been created.
# usage: CLEANUP_TEMPFILES

function CLEANUP_TEMPFILES () 
{
 rm $TMPDIR/.grassrc6_$TEMP_LOCATION
 rm $THE_VECTOR.shp
 rm  $THE_VECTOR.shx
 rm  $THE_VECTOR.prj
 rm  $THE_VECTOR.dbf
 rm  $VECTOR_KML.raw
 rm  $VECTOR_KML.cat_poly
 rm  $VECTOR_KML.cat_point
 rm  $VECTOR_KML.prepoint
 rm -rf $GISDBASE/$TEMP_LOCATION/PERMANENT
 rmdir $GISDBASE/$TEMP_LOCATION
 rm -rf $VECTOR_KML.raw2
}


#######################################################################
# name:     exitprocedure
# purpose:  removes all temporary files
#
exitprocedure ()
{
        message 0 "User break!"
        #rm -f ${TMP}*
        #rm $TMPDIR/.grassrc6_$TEMP_LOCATION
        #rm -rf $GISDBASE/$TEMP_LOCATION
        CLEANUP_TEMPFILES
        exit 1
}
trap "exitprocedure" 2 3 15

BC="bc"
BCARGS="-l"

#----------------------------------------------------------------
export GIS_LOCK=$$
#----------------------------------------------------------------
########################################################################
# name: error_routine
# purpose: If an error occurs, exit gracefully.
#
error_routine () {
echo "ERROR: $1"
exit 1
}
#################################
# is GRASS running ? if not: abort
#################################
if [ -z "$GISBASE" ] ; then
  error_routine "You must be in GRASS to run this program."
fi

#################################
# if no paramters are provided by the user fire up the gui
if [ "$1" != "@ARGS_PARSED@" ] ; then
  exec $GISBASE/bin/g.parser "$0" "$@"
fi

################################################################################
# Database


 # We need a string of all the column names in the layers database

 DB_RESULT=`v.db.connect -c map=$OPT_MAP`
 DB_COLUMN_NAMES=`echo $DB_RESULT |sed 's/^[A-Z]*|//g' | sed 's/[A-Z]*|/ /g'`

#################################################################################
# name: OGR_PATH_USER_OVERRIDE
# purpose: if the user provides a path to a specific version of OGR it will be used. 
# usage: OGR_PATH_USER_OVERRIDE

function OGR_PATH_USER_OVERRIDE ()
{

 if [ "${OPT_OGRPATH}" != "" ] ; then
   #ensure that the path-string properly ends with the file name
   OGR_ENDING=`echo ${OPT_OGRPATH} | grep "/ogr2ogr$" ` 

   if [ "$OGR_ENDING" == "" ] ; then
      OPT_OGRPATH="${OPT_OGRPATH}/ogr2ogr"
   fi

   if [ -f ${OPT_OGRPATH} ]; then
    #store this path as a GRASS variable for further use
    THE_OGR_PATH=$OPT_OGRPATH
    `g.gisenv set="GML_OGR_PATH"=${OPT_OGRPATH}`    
    else
     error_routine "Invalid path to OGR: ${THE_OGR_PATH}" 
   fi 
 fi
} 


#################################################################################
# name:     ENSURE_COLUMN
# purpose:  Verify that string $1 equals the name of column of the maps database.
# usage: ENSURE_COLUMN string-for-column-name

function ENSURE_COLUMN () {
#1: $COLUMN NAME to be verified

   echo $DB_COLUMN_NAMES |grep -q "$1"
  
   if [ $? != 0 ] ; then
     error_routine "$1 is not a database column."
   fi
}

#################################################################################
# name:     SET__HEX_COLORS
# purpose:  create new string variables for R,G,B as 2byte hex numbers from a R:G:B string (can be hex, decimal or other). 
# usage: SET_HEX_COLORS value-string-variable R-variable-name G-variable-name B-variable-name R-hex-default G-hex-default B-hex-default

function SET_HEX_COLORS
{
if [ "$1" != "(null)" ] ; then
  RED_D=`echo ${1} | cut -d: -f 1 `
  eval "$2"=`printf "%02x" $RED_D`  

  GREEN_D=`echo ${1} | cut -d: -f 2 `
  eval "$3"=`printf "%02x" $GREEN_D`

  BLUE_D=`echo ${1} | cut -d: -f 3 `
  eval "$4"=`printf "%02x" $BLUE_D`
else
  eval "$3=$5"
  eval "$3=$6"
  eval "$4=$7"
fi 
if [ "${GIS_FLAG_r}" = 1 ] ; then
     # the flag for random colors is set
     
     RCOLOR=`expr ${RANDOM} % 255`
     eval "$2"=`printf "%02x" $RCOLOR`
     RCOLOR=`expr ${RANDOM} % 255`
     eval "$4"=`printf "%02x" $RCOLOR`
     RCOLOR=`expr ${RANDOM} % 255`   
     eval "$3"=`printf "%02x" $RCOLOR`
fi
}

#################################################################################
# name:     SET_HEX_VALUE
# purpose:  create a new string variable with the value $2 as a 2byte hex number, or a default value $3.
# usage: SET_HEX_VALUE grass_parameter-variable new-variable-name default-value


function SET_HEX_VALUE () {
#1: $OPT_LINE_SIZE 2:GMLSIZE 3:1

if [ "$1" != "(null)" ] ; then
   eval "$2"=`printf "%02x" $1`
 else
   eval "$2"="$3"
fi
}
#
################################################################################


###
### Verify correct column names
### if they are provided, they are needed further below

 if [ "${OPT_COLUMN_LINE_TRANS}" != "" ] ; then
      ENSURE_COLUMN "${OPT_COLUMN_LINE_TRANS}" 
 fi
 if [ "${OPT_COLUMN_FILL_TRANS}" != "" ] ; then
      ENSURE_COLUMN "${OPT_COLUMN_FILL_TRANS}" 
 fi
 if [ "${OPT_COLUMN_LINE_TRANS}" != "" ] ; then
       ENSURE_COLUMN "${OPT_COLUMN_LINE_TRANS}" 
 fi
 if [ "${OPT_COLUMN_FILL_TRANS}" != "" ] ; then
       ENSURE_COLUMN "${OPT_COLUMN_FILL_TRANS}" 
 fi



################################################################################
# Has a value for line color been provided by the user ? 
# Otherwise use grass-green as the default.

SET_HEX_COLORS ${OPT_LINE_COLOR} "GMLRED" "GMLGREEN" "GMLBLUE" "0" "ff" "0" 


#
### Has a value for a polygon fill color been provided by the user ?
#
SET_HEX_COLORS "${OPT_FILL_COLOR}" "GMLFILLRED" "GMLFILLGREEN" "GMLFILLBLUE" "0" "ff" "0"

#
### Has a value for a icon color been provided by the user ?
#
SET_HEX_COLORS "${OPT_ICON_COLOR}" "GMLICONRED" "GMLICONGREEN" "GMLICONBLUE" "0" "ff" "0"

#
### Has a transparency value  been provided by the user ?
# Otherwise use full opacity as the default.

SET_HEX_VALUE "${OPT_LINE_TRANS}" "GMLTRANSPARENCY"  "ff"


#
### Has a fill-transparency value  been provided by the user ?
### Otherwise use full opacity as the default.
#

SET_HEX_VALUE "${OPT_FILL_TRANS}" "GMLFILLTRANSPARENCY"  "ff"

#
## Has a icon-transparency value  been provided by the user ?
## Otherwise use full opacity as the default.
#
SET_HEX_VALUE "${OPT_ICON_TRANS}" "GMLICONTRANSPARENCY"  "ff"

#
## Has a line-size value  been provided by the user ?
## Otherwise use 1 as the default.
#
SET_HEX_VALUE "$OPT_LINE_SIZE" "GMLSIZE"  "1"

############################################################################
# Ensure that the output file has the proper .kml-extension
# if no output file has been named, fall back to the name of the map.
if [ -z "${OPT_OUTPUT}" ] ; then
  VECTOR_KML=${OPT_MAP}.kml
 else
  VECTOR_KML=${OPT_OUTPUT}
fi

KML_ENDING=`echo $VECTOR_KML | grep ".kml$" ` 

if [ -z "$KML_ENDING" ] ; then
 VECTOR_KML=$VECTOR_KML.kml
fi


############################################################################
# Is ogr2ogr installed and available ?
# Search for ogr2ogr command in user's path

for i in `echo $PATH | sed 's/^:/.:/
     s/::/:.:/g
     s/:$/:./
     s/:/ /g'`
     do
            if [ -f $i/ogr2ogr ] ; then
		OGR_AVAILABLE=1
                THE_OGR_PATH="$i/ogr2ogr"
		break
	    fi
     done

# has a custom  ogr2ogr path already been provided on this machine (like in previous GRASS sessions) ? 
# in any case, if the user explicitly provides a ogr2ogr path from the command line,
# this one will override any defaults or previous settings

 PREVIOUS_SESSION_OGR=`g.gisenv get="GML_OGR_PATH"`

if [ "${PREVIOUS_SESSION_OGR}" ] ; then
   # if a ogr setting has been stored from former sessions then use it.
   THE_OGR_PATH=${PREVIOUS_SESSION_OGR}

   OGR_PATH_USER_OVERRIDE
   #Even if we have a path to OGR provided by the system, the user can override it.
else

 OGR_PATH_USER_OVERRIDE
  # this might be the first session ever, so lets stick to the user-provided path 

  if [ "${THE_OGR_PATH}" == "" ]; then
   error_routine "  ogr2ogr is not found in your default search-path. Is it installed ? You might provide a path to ogr2ogr as a second argument to this program."
  fi

 ################################
 #So we have ogr2ogr, but can it deal with KML ?

  echo "$THE_OGR_PATH --formats"
  OGR_KML=`$THE_OGR_PATH --formats |grep "KML"`

  if [ -z "$OGR_KML" ]; then
     error_routine "  $THE_OGR_PATH is lacking KML support." 
    
  fi

fi

#############################################################################################
# Setting the Line/Poly flags

# Only one of both flags can be set:
if [ "${FLAG_FORCE_LINE_EXPORT}" = 1 ] && [ "${FLAG_FORCE_POLYGON_EXPORT}" = 1 ] ; then
   error_routine "Conflicting flag settings: -l and -y can not be used together."   
fi

#################################
# Get the name of the vector layer to be converted
THE_VECTOR=${OPT_MAP}

# create a name fpr the temporary location
TEMP_LOCATION=latlon_location_$$

# Create a new temporary latlon location
g.proj -c proj4='+init=epsg:4326' location=$TEMP_LOCATION

#Set variables
GISDBASE=`g.gisenv get=GISDBASE`
OUTER_LOCATION=`g.gisenv get=LOCATION_NAME`
OUTER_MAPSET=`g.gisenv get=MAPSET`

#Keep the path to the settings file for the original location
export OUTER_GISRC=$GISRC

########################################
##generate GRASS_settings-file for lat lon location:

echo "GISDBASE: $GISDBASE " > $TMPDIR/.grassrc6_$TEMP_LOCATION
echo "LOCATION_NAME: $TEMP_LOCATION " >> $TMPDIR/.grassrc6_$TEMP_LOCATION
echo "MAPSET: PERMANENT " >>  $TMPDIR/.grassrc6_$TEMP_LOCATION
echo "GRASS_GUI: text " >>  $TMPDIR/.grassrc6_$TEMP_LOCATION

########################################
##switch over to lat lon location

export GISRC=$TMPDIR/.grassrc6_$TEMP_LOCATION

#use process ID (PID) as lock file number:
export GIS_LOCK=$$

# Import the vector data into the lat lon location
v.proj input=$THE_VECTOR location=$OUTER_LOCATION mapset=$OUTER_MAPSET

#
## VECTOR FEATURE EXPORT OR POLYGON FEATURE EXPORT
#


if [ "${FLAG_FORCE_LINE_EXPORT}" == 1 ] ; then
    GEOMETRY="kernel,line,boundary"   
fi


if [ "${FLAG_FORCE_POLYGON_EXPORT}" == 1 ] ; then
    GEOMETRY="area"  
fi


if [ "${FLAG_POINT_EXPORT}" == 1 ] ; then
 if [ "$GEOMETRY" != "" ] ; then
   GEOMETRY="$GEOMETRY,point"
 else
   GEOMETRY="point"
 fi 
fi

v.out.ogr input=$THE_VECTOR type=$GEOMETRY dsn=. olayer=$THE_VECTOR

######################################################################################
#Switch back to the original location

export GISRC=$OUTER_GISRC 
GISRC=$OUTER_GISRC 

######################################################################################
#
### Shape to KML Conversion
#


echo "$OGR_PATH -f KML $VECTOR_KML.raw $THE_VECTOR.sh" 
`$THE_OGR_PATH -f KML $VECTOR_KML.raw $THE_VECTOR.shp` || error_routine "$OGR_PATH aborted."

######################################################################################
#
## Blend color, transparency and icons into the  KML by updating the style-tag
#

# create indicators for points and lines
cat $VECTOR_KML.raw | grep PolyStyle > $VECTOR_KML.cat_poly
cat $VECTOR_KML.raw | grep Point > $VECTOR_KML.cat_point


#
## Add colors and transparency for polygons and lines
#

if [ -s "$VECTOR_KML.cat_poly" ]; then
  sed "s/<color>........<\/color>/<size>${GMLSIZE}<\/size><color>${GMLTRANSPARENCY}${GMLBLUE}${GMLGREEN}${GMLRED}<\/color>/g" $VECTOR_KML.raw > $VECTOR_KML.raw2 
  sed "s/<fill>0<\/fill>/<color>${GMLFILLTRANSPARENCY}${GMLFILLBLUE}${GMLFILLGREEN}${GMLFILLRED}<\/color>/g" $VECTOR_KML.raw2 > $VECTOR_KML.prepoint

 else
  sed "s/<\/LineString>/<\/LineString><Style><LineStyle><size>${GMLSIZE}<\/size><color>${GMLTRANSPARENCY}${GMLBLUE}${GMLGREEN}${GMLRED}<\/color><\/LineStyle><\/Style>/g" $VECTOR_KML.raw > $VECTOR_KML.prepoint
fi


#
##  Add color, transparency and icon for points
#

if [ -s "$VECTOR_KML.cat_point" ] &&  [ "${GIS_FLAG_P}" = 1 ] ; then
# There are point-vectors in the file AND we want to deal with them

  POINT_BEGIN="<Style><IconStyle><color>${GMLICONTRANSPARENCY}${GMLICONBLUE}${GMLICONGREEN}${GMLICONRED}<\/color><Icon><href>"
  POINT_END="<\/href><\/Icon><\/IconStyle><\/Style>"

    if [ "${OPT_ICON_URL}" ] ; then 
      # an URL has been provided by the user
      ICONURL=` echo ${OPT_ICON_URL} | sed "s|\/|\\\\\/|g"`
      POINT_STYLE="${POINT_BEGIN}${ICONURL}${POINT_END}"
      sed "s/<\/Point>/<\/Point>${POINT_STYLE}/g" $VECTOR_KML.prepoint > $VECTOR_KML
    else
          if [ -z "${OPT_ICON_CODE}" ] || [ -z "${OPT_ICON_PALETTE}" ] ; then 
              error_routine "GML ICON PROBLEM: ICON=${OPT_ICON_CODE} PALETTE=${OPT_ICON_PALETTE}."
          fi

          if [ "${OPT_ICON_CODE}" -a "${OPT_ICON_PALETTE}" ] ; then 
              ICONURL="http:\/\/maps.google.com\/mapfiles\/kml\/pal${OPT_ICON_PALETTE}\/icon${OPT_ICON_CODE}.png"
              POINT_STYLE="${POINT_BEGIN}${ICONURL}${POINT_END}"
              sed "s/<\/Point>/<\/Point>${POINT_STYLE}/g" $VECTOR_KML.prepoint > $VECTOR_KML
          else
              cp  $VECTOR_KML.prepoint $VECTOR_KML	
              # let handle googleearth the icon rendering      
          fi
    fi
     
else
 #no points around so the results from the line/polygon-conversion are to be used
 cp  $VECTOR_KML.prepoint  $VECTOR_KML
fi  # cat_points && gis_flag_p  ende

########################################################################################################
## The files for the transparenices have to be defined prior to pumping the awk-content 
## into the strings -> the transparency values are integrated into the awk-strings

 if [ "${OPT_COLUMN_LINE_TRANS}" != "" ] ; then
# ENSURE_COLUMN "${OPT_COLUMN_LINE_TRANS}" 
   AWK_LINE_TRANS_QUERY="/^.*${OPT_COLUMN_LINE_TRANS}.*$/ { parse_event=1; print \$0; split(\$2,a1,\">\"); split(a1[2],a2,\"<\"); LINETRANS=a2[1];} "
 else
   AWK_LINE_TRANS_QUERY=""
 fi

 if [ "${OPT_COLUMN_FILL_TRANS}" != "" ] ; then

 # a database column for line-transparency has explicitly been set
 #  ENSURE_COLUMN "${OPT_COLUMN_FILL_TRANS}"
   AWK_FILL_TRANS_QUERY="/^.*${OPT_COLUMN_FILL_TRANS}.*$/ { parse_event=1; print \$0; split(\$2,a1,\">\"); split(a1[2],a2,\"<\"); FILLTRANS=a2[1];} "

 else
  AWK_FILL_TRANS_QUERY=""
 fi

#
################### AWK-Code for LINE ####################################
#

awktemp_line=/tmp/awk.prog.line.$$
cat > $awktemp_line <<END
BEGIN {
       hex_fallback=sprintf("%2.2x%2.2x%2.2x",16,16,16);
       hex_line_trans=LINETRANS;
      }

/^.*$OPT_COLUMN_LINE_COLOR.*$/ {
                        print \$0;
                        parse_event=1; 
                        rgb_provided=1;
                        split(\$2,array1,">");
                        split(array1[2],array2,"<");
                        grassrgb=array2[1];           
                        split(grassrgb,colors,":");
                        hex_rgb=sprintf("%2.2x%2.2x%2.2x",colors[1],colors[2],colors[3]);          
  
                        }
$AWK_LINE_TRANS_QUERY
/^.*<Style>.*$/         {
                        
                        if (rgb_provided == 1)
                           {
                            the_rgb=hex_rgb;
                            rgb_provided=0;
                           
                           }  
                         else 
                           {
                            the_rgb=hex_fallback; 
                           
                           }        
                        
                        # LINETRANS can either be inserted from the GRASS_DB by a $AWK_LINE_TRANS_QUERY or when the script is called up.
                        parse_event=1;
                        the_line=\$0;                        
                        gsub(/\<color\>........\<\/color\>\<\/LineStyle\>/,"<color>"hex_line_trans the_rgb"</color></LineStyle>", the_line);
                      
                        print the_line;
                        }

                        {if (parse_event == 0) {print \$0;}   
			  else { parse_event=0; } 
                        }

END
#
##################### AWK-Code for FILL:###################################
#

awktemp_fill=/tmp/awk.prog.fill.$$
cat > $awktemp_fill <<END
BEGIN                   {
                         hex_fallback=sprintf("%2.2x%2.2x%2.2x",32,32,32);    
                         hex_fill_trans=FILLTRANS;    
                        }
/^.*$OPT_COLUMN_FILL_COLOR.*$/ {
                        
                        parse_event=1; 
                        rgb_provided=1;
                        split(\$2,array1,">");
                        split(array1[2],array2,"<");
                        grassrgb=array2[1];                                                 
                        split(grassrgb,colors,":");
                        hex_rgb=sprintf("%2.2x%2.2x%2.2x",colors[1],colors[2],colors[3]);
                       
                        }

$AWK_FILL_TRANS_QUERY
/^.*<Style>.*$/         {
                        parse_event=1
                        the_line=\$0;
			
                        if (rgb_provided == 1)
                           {
                            the_rgb=hex_rgb;
                            rgb_provided=0;
                           }  
                         else 
                           {
                            the_rgb=hex_fallback; 
                           }        
                   
                        gsub(/\<color\>........\<\/color\>\<\/PolyStyle\>/,"<color>"hex_fill_trans the_rgb"</color></PolyStyle>",the_line);                       
                        print the_line;
                         
                        }

                        {if (parse_event == 0) {print \$0;}   
			  else { parse_event=0; } 
                        }

END
#
#########################################################################
#apply AWK-Codes if necessary (aka database columns have been provided):

   if [ "${OPT_COLUMN_LINE_COLOR}" != "" ] ; then
     AWK_LINE_RGB=${OPT_COLUMN_LINE_COLOR}
      
     awk -f $awktemp_line -v LINETRANS=$GMLTRANSPARENCY  $VECTOR_KML > $VECTOR_KML.awk
     echo "awk -f $awktemp_line -v LINETRANS=$GMLTRANSPARENCY  $VECTOR_KML > $VECTOR_KML.awk"
     mv $VECTOR_KML  $VECTOR_KML.preline
     mv $VECTOR_KML.awk $VECTOR_KML
   fi
  
   if [ "${OPT_COLUMN_FILL_COLOR}" != "" ] ; then
      # a column for fill colors has been explicitly set
     AWK_FILL_RGB=${OPT_COLUMN_FILL_COLOR}

     echo "awk -f $awktemp_fill -v FILLTRANS=$GMLFILLTRANSPARENCY  $VECTOR_KML > $VECTOR_KML.awk"
     awk -f $awktemp_fill -v FILLTRANS=$GMLFILLTRANSPARENCY  $VECTOR_KML > $VECTOR_KML.awk
     mv $VECTOR_KML  $VECTOR_KML.prefill
     mv $VECTOR_KML.awk $VECTOR_KML
   fi

########################################
#cleanup: remove location & files

CLEANUP_TEMPFILES

########################################
#That's all, folks. (PL)

