#!/bin/bash
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# MODULE:  "digit_input.sh" per GRASS 6.4 (GRASS Shell Script)				
#											
# AUTHOR:	roberto marzocchi(roberto.marzocchi@gmail.com)				
#											
# PURPOSE: 		
#	   Il presente modulo viene solitamente lanciato dallo script pastro.sh.	
#											
# This program is free software under the GNU General Public License (>=v2). 		
# Read the file COPYING that comes with GRASS for details.				
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

d.mon stop=x4 --quiet
d.mon start=x4
if (check_image=1); then
	#v.digit -n map=$input bgcmd="d.shadedmap reliefmap=temp_shade drapemap=$dtm;d.vect map=$paths display=shape type=line layer=1 color=red fcolor=255:255:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c;d.vect map=$shelters display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c"	
	d.shadedmap reliefmap=temp_shade drapemap=$dtm
	d.vect map=$paths display=shape type=line layer=1 color=red fcolor=255:255:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
	#if [! -z $shelters]
	d.vect map=$shelters display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
	#fi
else
	#v.digit -n map=$input bgcmd="d.rast map=$image;d.vect map=$paths display=shape type=line layer=1 color=red fcolor=255:255:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c;d.vect map=$shelters display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c"
	d.rast map=$image
	d.vect map=$paths display=shape type=line layer=1 color=red fcolor=255:255:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
	#if [! -z $shelters]
	d.vect map=$shelters display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
	#fi		
fi

g.message -i "*******************************************************"
g.message -i "....Digita un punto con il tasto sinistro del mouse...."
g.message -i "...............Con il sinistro esci...................."
g.message -i "_______________________________________________________"

d.where --quiet >.tmp_coord.txt
space2tab.py
# sed 's/^[ \t]*//;s/[ \t]*$//;s/    /|/' .tmp_coord.txt > tmp_coord2.txt
v.in.ascii input=tmp_coord2.txt output=digitato fs="|" x=1 y=2 --overwrite --quiet
rm .tmp_coord.txt
rm tmp_coord2.txt
d.mon stop=x4


exit 1 


