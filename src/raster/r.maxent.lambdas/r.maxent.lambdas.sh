#!/bin/sh 
# 
############################################################################ 
# 
# MODULE:       r.maxent.lambdas 
# AUTHOR(S):    Stefan Blumentrath <stefan dot blumentrath at nina dot no >
#               Proposed small change in how raw features are extracted 
#               from the lambdas file as this didn't work in original
#               code (Paulo van Breugel)
# PURPOSE:      Compute raw and/or logistic prediction maps from a lambdas
#               file produced with MaxEnt 3.3.3e. 
#
#               !!!This script works only if the input data to MaxEnt 
#               are accessible from the current region.!!!
# 
#               This script will parse the specified lambdas-file from 
#               MaxEnt 3.3.3e (see http://biodiversityinformatics.amnh.org/open_source/maxent/) 
#               and translate it into an r.mapcalc-expression which is then stored
#               in a temporary file and finally piped to r.mapcalc.
#               If alias names had been used in MaxEnt, these alias names can 
#               automatically be replaced according to a  CSV-like file provided 
#               by the user. This file should contain alias names in the first 
#               column and map names in the second column, seperated by comma, 
#               without header. It should look e.g. like this:
#               
#               alias_1,map_1
#               alias_2,map_2
#               ...,...
#               
#               If such a CSV-file with alias names used in MaxEnt is provided, 
#               the alias names from MaxEnt are replaced by map names. 
#
#               A raw output map is always computed from the MaxEnt model
#               as a first step. If logistic output is requested, the raw output
#               map can be deleted by the script ( using the l-flag). The 
#               production of logistic output can be omitted. The logistic map  
#               can be produced as an integer map. To do so the user has to specify
#               the number of digits after comma, that should be preserved in 
#               integer output.   
#               Optionally the map calculator expressions can be saved in a text 
#               file, as especially the one for the raw output is likely to exceed 
#               the space in the map history.
#               Due to conversion from double to floating-point in exp()-function, a 
#               loss of precision from the 7th digit onwards is possible in the 
#               logistic output.
# 
# COPYRIGHT:    (C) 2011 by the Norwegian Institute for Nature Research (NINA)
#               http://www.nina.no
# 
#               This program is free software under the GNU General Public 
#               License (>=v2). Read the file COPYING that comes with GRASS 
#               for details. 
# 
############################################################################# 
#
# REQUIREMENTS:
# awk
#
#%Module 
#% description: Computes raw and/or logistic prediction maps from MaxEnt lambdas files 
#%End 
#
#%flag
#%  key: r
#%  description: Produce only raw output (both are computed by default).
#%end
#
#%flag
#%  key: l
#%  description: Produce only logistic output (both are computed by default).
#%end
#
#%option 
#% key: lambdas_file
#% type: string
#% description: MaxEnt lambdas-file to compute distribution-model from
#% required : yes
#% gisprompt: old_file,file,input
#%end
# 
#%option 
#% key: output_prefix
#% type: string 
#% description: Prefix for output raster maps 
#% required : yes
#% gisprompt: new,cell,raster
#%end 
#
#%option 
#% key: alias_file
#% type: string
#% description: CSV-file to replace alias names from MaxEnt by GRASS map names
#% required : no
#% gisprompt: old_file,file,input
#%end
# 
#%option 
#% key: integer_output
#% type: integer
#% description: Produce logistic integer output with this number of digits preserved
#% required : no
#% answer : 0
#%end
# 
#%option 
#% key: output_mapcalc
#% type: string 
#% description: Save r.mapcalc expression to file 
#% required : no
#% gisprompt: new_file,file,output
#%end 
#
#
FLAG_ONLY_RAW=${GIS_FLAG_R}
FLAG_ONLY_LOGISTIC=${GIS_FLAG_L}
LAMBDAS_FILE="${GIS_OPT_LAMBDAS_FILE}"
INTEGER_OUTPUT=${GIS_OPT_INTEGER_OUTPUT}
#
ALIAS_FILE="${GIS_OPT_ALIAS_FILE}"
#
OUTPUT_PREFIX="${GIS_OPT_OUTPUT_PREFIX}"
OUTPUT_MAPCALC="${GIS_OPT_OUTPUT_MAPCALC}"
#
#Check if script is started from within GRASS
if [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program." 1>&2
    exit 1
fi
#
#Check if awk is installed
	if [ ! -x "`which awk`" ] ; then
	    g.message -e "awk is required, please install awk or gawk first" 
	    exit 1
	fi
#Set environment so that awk works properly in all languages
	unset LC_ALL
	LC_NUMERIC=C
	export LC_NUMERIC
#
#Pass evtl. command line arguments to gui and start it 
if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi
#
#Check if input file exists
if [ ! -r "$LAMBDAS_FILE" ] ; then 
	g.message -e "MaxEnt lambdas-file could not be found or is not readable."
	exit 1
fi 
#
#Check if raw output files exists 
eval `g.findfile element=cell file=${OUTPUT_PREFIX}_raw` 
if [ -n "$name" ] ; then 
	g.message -e  "Raw output file already exists."
	exit 1
fi
#
#Check if logistic output files exists when requestd
if [ "${FLAG_ONLY_RAW}" -ne 1 ] ; then
	eval `g.findfile element=cell file=${OUTPUT_PREFIX}_logistic` 
	if [ -n "$name" ] ; then 
		g.message -e  "Logistic output file already exists."
		exit 1
	fi
fi
#
#Check if output flags are set properly 
if [ "${FLAG_ONLY_RAW}" -eq 1 -a "${FLAG_ONLY_LOGISTIC}" -eq 1 ] ; then
	g.message -e  "The r and l flags are exclusive. Do not tick both!"
	rm "$temp1"
	exit 1
fi
#
###Save r.mapcalc expression to file if requested, else to tmp-file
if [ -z "$OUTPUT_MAPCALC" ] ; then
	#
	#Create tempfile
	temp1=`g.tempfile pid=$$`
	if [ $? -ne 0 ] || [ -z "$temp1" ] ; then
			g.message -e "ERROR: unable to create temporary files"
			exit 1
	fi
else
	temp1="$OUTPUT_MAPCALC"
fi
#
###Parse lambdas-file and translate it to a mapcalculator expression (safed in temporary file)
###Get variables linearPredictorNormalizer, densityNormalizer and entropy from lambdas-file
linearPredictorNormalizer=$(cat ${LAMBDAS_FILE} | grep linearPredictorNormalizer | sed 's/ //g' | tr -d '\r' | cut -f2 -d",")
densityNormalizer=$(cat ${LAMBDAS_FILE} | grep densityNormalizer | sed 's/ //g' | tr -d '\r' | cut -f2 -d",")
entropy=$(cat ${LAMBDAS_FILE} | grep entropy | sed 's/ //g' | tr -d '\r' | cut -f2 -d",")
###Create file with initial part of mapcalc-expression
echo "${OUTPUT_PREFIX}_raw = exp(((\\" > "$temp1"
###Extract raw features
cat -v "${LAMBDAS_FILE}" | awk '$0 !~ /\^|\(|\*/' | grep -vP "\`" | grep -vP "\'" | sed 's/\^M//g' | sed 's/,//g' | awk 'NF==4{print "if(isnull(" $1 "),0,(" $2 "*(" $1 "-" $3 ")/(" $4 "-" $3 ")))" "+" "\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Extract quadratic features
cat -v "${LAMBDAS_FILE}" | grep '\^2' | sed 's/\^M//g' | sed 's/,//g' | sed 's/\^2//g' | awk '{print "if(isnull(" $1 "),0,((" $2 "*(" $1 "*" $1 "-" $3 "))/" "(" $4 "-" $3 ")))" "+" "\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Extract product features
cat -v "${LAMBDAS_FILE}" | grep '*' | sed 's/\^M//g' | sed 's/,//g' | tr '*' ' ' | awk '{print "if((isnull(" $1 ")||isnull(" $2 ")),0,(" $3 "*(" $1 "*" $2 "-" $4 ")/(" $5 "-" $4 ")))+\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Extract forward hinge features
cat -v "${LAMBDAS_FILE}" | grep -P "\'" | sed 's/\^M//g' | sed 's/,//g' | cut -b 2- | tr '<' ' ' | awk '{print "if(isnull(" $1 "),0,if(" $1 ">=" $3 ",(" $2 "*(" $1 "-" $3 ")/(" $4 "-" $3 ")),0.0))+\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Extract reverse hinge features
cat -v "${LAMBDAS_FILE}" | grep -P "\`" | sed 's/\^M//g' | sed 's/,//g' | cut -b 2- | tr '<' ' ' | awk '{print "if(isnull(" $1 "),0,if(" $1 "<" $4 ",(" $2 "*(" $4 "-" $1 ")/(" $4 "-" $3 ")),0.0))+\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Extract threshold features
cat -v "${LAMBDAS_FILE}" | grep '(' | grep -v '=' | sed 's/\^M//g' | sed 's/,//g' | sed 's/(//g' | sed 's/)//g' | tr '<' ' ' | awk '{print "if(isnull(" $2 "),0,if(" $2 ">=" $1 "," $3 "))" "+\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Extract categoric features
cat -v "${LAMBDAS_FILE}" | grep '(' | grep '=' | sed 's/\^M//g' | sed 's/,//g' | sed 's/(//g' | sed 's/)//g' | tr '=' ' ' | awk '{print "if(isnull(" $1 "),0,if(" $1 "==" $2 "," $3 "))" "+\\"}' | sed 's/--/+/g' | sed 's/+-/-/g' >> $temp1
###Replace last '\' by tail part of mapcalc-expression
sed -i '$s/..$/\\/' "$temp1"
echo ")-${linearPredictorNormalizer}))/${densityNormalizer}" >> "$temp1"
###Replace possible repetitions of mathmatical signs
sed -i 's/--/+/g' "$temp1"
sed -i 's/+-/-/g' "$temp1"
#
#Check if alias file is provided and readable
if [ -n "$ALIAS_FILE" ] ; then
	if [ ! -r "$ALIAS_FILE" ] ; then 
		g.message -e "Alias file could not be found or is not readable."
		exit 1
	else
		#Parse alias-file to replace MaxEnt alias names by GRASS map names (including mapset specification)
		alias_names=$(cat $ALIAS_FILE | cut -f1 -d",")
		for a in $alias_names
		do
		m=$(cat $ALIAS_FILE | grep -w "${a}" | cut -f2 -d",")
		#
		g.message -v "Map name for alias $a is $m"
		#
		sed -i "s/(${a}-/(${m}-/" "$temp1"
		sed -i "s/(${a}+/(${m}+/" "$temp1"
		sed -i "s/(${a}>/(${m}>/" "$temp1"
		sed -i "s/(${a}</(${m}</" "$temp1"
		sed -i "s/(${a}=/(${m}=/" "$temp1"
		sed -i "s/(${a}\*/(${m}\*/" "$temp1"
		#
		sed -i "s/-${a})/-${m})/" "$temp1"
		sed -i "s/+${a})/+${m})/" "$temp1"
		sed -i "s/>${a})/>${m})/" "$temp1"
		sed -i "s/<${a})/<${m})/" "$temp1"
		sed -i "s/=${a})/=${m})/" "$temp1"
		sed -i "s/\*${a}-/\*${m}-/" "$temp1"
		sed -i "s/\*${a}+/\*${m}+/" "$temp1"
		done
		#
	fi 
fi
#
###Compute raw output map by sending expression saved in file temporary file to r.mapcalc
cat "$temp1" | r.mapcalc
#
###Compute logistic output map if not suppressed
if [ "${FLAG_ONLY_RAW}" -eq 0 ] ; then
	if  [ "${INTEGER_OUTPUT}" -le 0 ] ; then
		echo "${OUTPUT_PREFIX}_logistic = (${OUTPUT_PREFIX}_raw*exp(${entropy}))/(1.0+(${OUTPUT_PREFIX}_raw*exp(${entropy})))" >> "$temp1"
		r.mapcalc "${OUTPUT_PREFIX}_logistic = (${OUTPUT_PREFIX}_raw*exp(${entropy}))/(1.0+(${OUTPUT_PREFIX}_raw*exp(${entropy})))"
	else
		if  [ "${INTEGER_OUTPUT}" -lt 5 ] ; then
			echo "${OUTPUT_PREFIX}_logistic = round(((${OUTPUT_PREFIX}_raw*exp(${entropy}))/(1.0+(${OUTPUT_PREFIX}_raw*exp(${entropy}))))*(10^${INTEGER_OUTPUT}))" >> "$temp1"
			r.mapcalc "${OUTPUT_PREFIX}_logistic = round(((${OUTPUT_PREFIX}_raw*exp(${entropy}))/(1.0+(${OUTPUT_PREFIX}_raw*exp(${entropy}))))*(10^${INTEGER_OUTPUT}))"
		else
			echo "${OUTPUT_PREFIX}_logistic = round(((${OUTPUT_PREFIX}_raw*exp(${entropy}))/(1.0+(${OUTPUT_PREFIX}_raw*exp(${entropy}))))*100000.0)" >> "$temp1"
			r.mapcalc "${OUTPUT_PREFIX}_logistic = round(((${OUTPUT_PREFIX}_raw*exp(${entropy}))/(1.0+(${OUTPUT_PREFIX}_raw*exp(${entropy}))))*100000.0)"
		fi
	fi
fi
###Remove raw output map if requested
if [ "${FLAG_ONLY_LOGISTIC}" -eq 1 ] ; then
	g.remove -f type='rast' name="${OUTPUT_PREFIX}"_raw
fi
###Remove tmp-file containing r.mapcalc expressions (if save to file not requested)
if [ -z "$OUTPUT_MAPCALC" ] ; then
	rm -f "$temp1"
fi

g.message "Done"
