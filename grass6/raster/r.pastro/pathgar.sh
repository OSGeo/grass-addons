#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODULE:  "PATHGAR SH" per GRASS 6.4 (GRASS Shell Script)				  #
#											  #
# AUTHOR:  Andrea Cervetto (cervoz@hotmail.com)			 			  #
#	   Damiano Natali(damiano.natali@gmail.com)					  #
#	   Roberto Marzocchi (roberto.marzocchi@gmail.com)			          #
# PURPOSE: Calcolo del presidio del territorio offerto dalla rete sentieristica presente; #
#	   Il presente modulo viene solitamente lanciato dallo script pastro.sh.	  #
#											  #
# This program is free software under the GNU General Public License (>=v2). 		  #
# Read the file COPYING that comes with GRASS for details.				  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#nome della cartella delle mappe
#mappe='/home/damiano/spin-off/provincia_spezia/webgis/mappe'

#nome della cartella temporanea
#percorso='/home/damiano/spin-off/provincia_spezia/webgis/tmp'

# creazione di un report relativo alla regione corrente
#FILELOG='/home/damiano/spin-off/provincia_spezia/webgis/tmp/filelog/sheltgar.txt'
FILELOG="$folder/pathgar.txt"

# valutazione del percorso della location
eval `g.gisenv`
: ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}
LOCATION="$GISDBASE/$LOCATION_NAME/$MAPSET"

clear

g.message -i "********************************************************************************"
g.message -i "|                                   PATHGAR. SH                                |"
g.message -i "| Calcolo del presidio del territorio offertodalla rete sentieristica presente |"
g.message -i "********************************************************************************"	




################################################################################################
###   e' realmente necessario????
################################################################################################
# zoommiamo sull'area di interesse attraverso uno script apposito
#region_zoom.sh

# conversione del file vettoriale rappresentante la rete sentieristica da tipo linea a tipo punti:
# 1) rasterizzazione della mappa dei sentieri
v.to.rast input=$paths output="tmp_rast"$paths use=val type=line --overwrite --quiet
# 2) vettorializzazione della mappa dei sentieri come punti
#r.to.vect input="tmp_rast"$paths output="tmp_punti"$paths feature=point --overwrite --quiet
# cosi' si velocizza molto il procedimento
#point_dist=$(($res_calcolo*4))
#if [$point_dist > 50 ]
#then
#	point_dist=50	
#fi
point_dist=50
v.to.points input=$paths output="tmp_punti"$paths type=line dmax=$point_dist --overwrite --quiet

# Creazione della mappa delle friction
r.slope.aspect elevation=$dtm slope=tmp_slope_percentuale aspect=tmp_aspect format=percent prec=float zfactor=1.0 min_slp_allowed=0.0 --overwrite --quiet 
# echo 'friction_pendenze=if(slope_percentuale<0.32,2,if(0.32<=slope_percentuale<=0.56,7.5,20))' | r.mapcalc

##############################################################################################################
## frane e no_guado devono essere definite ??? obbligatori opzionali????
##############################################################################################################

#r.mapcalc 'tmp_friction_offroad=if(!isnull(tmp_frane),2,if(!isnull(tmp_no_guado),5,if(tmp_slope_percentuale>77,5,1)))'
r.mapcalc 'tmp_friction_offroad=if(tmp_slope_percentuale>77,5,if(!isnull(tmp_no_guado),5,if(!isnull(tmp_frane),2,1)))'
#r.mapcalc "tmp_friction_offroad=if(tmp_slope_percentuale>0.77,5,1)" # carta temporanea
# echo 'friction=if(!isnull("tmp_"$paths"rast"),0,friction_offroad)' | r.mapcalc
r.mapcalc "tmp_friction=if(!isnull(tmp_rast$paths),0,tmp_friction_offroad)"
# Calcolo delle aree raggiungibili a partire dai ripari esistenti in meno di tot minuti
#echo 
#while ! [ $tmax ]
#   do echo -n 'Digita la distanza massima in minuti a partire dalla rete sentieristica esistente che si desidera considerare: '
#   read tmax
#done
g.message -i "La distanza massima dai sentieri e' pari a $tmax minuti, ossia $(($tmax*60)) s"


r.walk -k elevation=$dtm friction=tmp_friction output=tmp_walkout start_points=tmp_punti$paths max_cost=$(($tmax*60)) percent_memory=10 walk_coeff=$a,$b,$c,$d lambda=1.0 slope_factor=$s_f --overwrite --quiet

#echo 'tmp_walkout=if(tmp_walkout<='$((tmax*60))',tmp_walkout,null())'|r.mapcalc
#echo 'tmp_walkout_min=walkout/60' | r.mapcalc

r.mapcalc 'tmp_walkout=if(tmp_walkout>'$(($tmax*60))',null(),tmp_walkout)'
#r.mapcalc 'tmp_walkout=if(tmp_walkout<='$(($tmax*60.0))',tmp_walkout,null())'
r.mapcalc 'tmp_walkout_min=tmp_walkout/60.0'


# visualizziamo a monitor le mappe create, dando la possibilità di interrogarle, e le salviamo nella cartella 
# /home/damiano/searching/gis&web/mobilita_ambito_montano/tmp
#region_layout.sh

g.remove rast=tmp_walkout,tmp_friction,tmp_friction_offroad,"tmp_rast"$paths,tmp_slope_percentuale,tmp_aspect,tmp_frane,tmp_no_guado vect="tmp_punti"$paths --quiet
g.rename rast=tmp_walkout_min,$output --quiet

#g.message -i "PATHGAR module correctly termined"
g.message -i "Il modulo PATHGAR e' terminato correttamente"
g.message -i "____________________________________________"
# torniamo al menù principale
#pastro.sh
