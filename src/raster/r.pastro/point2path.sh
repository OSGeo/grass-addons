#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODULE:  "POINT2PATH SH" per GRASS 6.4 (GRASS Shell Script)				          #
#											          #
# AUTHOR:  Andrea Cervetto (cervoz@hotmail.com)						          #
#	   Damiano Natali (damiano.natali@gmail.com)					          #
#	   Roberto Marzocchi (roberto.marzocchi@gmail.com)									          	  #
# PURPOSE: Individua il percorso ottimale tra da due punti e ne calcola il tempo di percorrenza	  #
#	   Il presente modulo viene solitamente lanciato dallo script pastro.sh.	  	  #
#											  	  #
# This program is free software under the GNU General Public License (>=v2). 		  	  #
# Read the file COPYING that comes with GRASS for details.				  	  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#nome della cartella delle mappe
#mappe='/home/damiano/spin-off/provincia_spezia/webgis/mappe'

#nome della cartella temporanea
#percorso='/home/damiano/spin-off/provincia_spezia/webgis/tmp'

# creazione di un report relativo alla regione corrente
#FILELOG='/home/damiano/spin-off/provincia_spezia/webgis/tmp/filelog/sheltgar.txt'
FILELOG="$folder/sheltgar.txt"


# valutazione del percorso della location
eval `g.gisenv`
: ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}
LOCATION="$GISDBASE/$LOCATION_NAME/$MAPSET"

clear
g.message -i "|************************************************************|"
g.message -i "|.......................POINT2PATH.SH........................|"
g.message -i "| Calcolo del percorso ottimale tra un sentiero ed un punto  |"
g.message -i "|************************************************************|"	


# zoommiamo sull'area di interesse attraverso uno script apposito
#region_zoom.sh



########################################################################################################################################
##### DA QUA PULITO
########################################################################################################################################
# Creazione della mappa delle friction
v.to.rast input=$paths output=tmp_rast$paths use=val type=line --overwrite --quiet
r.slope.aspect elevation=$dtm slope=tmp_slope_percentuale aspect=tmp_aspect format=percent prec=float zfactor=1.0 min_slp_allowed=0.0 --overwrite --quiet

#r.mapcalc 'tmp_friction_offroad=if(!isnull(frane),2,if(!isnull(no_guado),5,if(slope_percentuale>0.77,5,1)))'
r.mapcalc 'tmp_friction_offroad=if(tmp_slope_percentuale>77,5,if(!isnull(tmp_no_guado),5,if(!isnull(tmp_frane),2,1)))'
#r.mapcalc "tmp_friction_offroad=if(tmp_slope_percentuale>0.77,5,1)" # carta temporanea
r.mapcalc "tmp_friction=if(!isnull(tmp_rast$paths),0,tmp_friction_offroad)"

# calcolo mappa di costo
r.walk -k elevation=$dtm friction=tmp_friction output=tmp_walkout start_points=$partenza max_cost=0 percent_memory=100 nseg=4 walk_coeff=$a,$b,$c,$d lambda=1.0 slope_factor=$s_f --overwrite --quiet
r.fill.dir -f input=tmp_walkout elevation=tmp_walkout_filled direction=tmp_walkout_dir areas=tmp_areas_walkout --overwrite --quiet

r.mapcalc "tmp_walkout_min=tmp_walkout/60"


# ritagliamo la mappa di costo sul vettoriale dei sentieri e troviamone il minimo
r.mapcalc "tmp_costo_sentiero=if(!isnull(tmp_rast$paths),tmp_walkout,null())"
#echo 'costo_sentiero=if(!isnull(tmp_$paths_rast),tmp_walkout,null())' | r.mapcalc
r.info -r map=tmp_costo_sentiero > $folder/info1
cut $folder/info1 -d \= -f 2 > $folder/info2
ris=$(cat $folder/info2)
min=$(echo $ris | cut -d ' ' -f 1)
cost_max=$(echo $ris | cut -d ' ' -f 2)
min1=$(echo $min | cut -d \. -f 1)
min_approx=$(expr $min1 + 1)
r.mapcalc "tmp_punto_minimo_rast=if(tmp_costo_sentiero<=$min_approx,tmp_costo_sentiero,null())"
# echo 'tmp_punto_minimo_rast=if(costo_sentiero<='$min_approx',tmp_costo_sentiero,null())'|r.mapcalc

# trasformiamo il punto di minimo da raster a vettoriale
r.to.vect input=tmp_punto_minimo_rast output=tmp_stop_point feature=point --overwrite --quiet 

# calcola il percorso a minima energia
r.drain -c input=tmp_walkout_filled output=tmp_drainout vector_points=tmp_stop_point --overwrite --quiet
g.remove rast=tmp_walkout_filled,tmp_walkout_dir,tmp_areas_walkout --quiet

# creazione del vettoriale del percorso
r.thin input=tmp_drainout output=tmp_thinout iterations=200 --overwrite	--quiet
r.to.vect -s input=tmp_thinout output=tmp_sentiero_trovato feature=line --overwrite --quiet

# creiamo il profilo del sentiero e stampiamolo con gnuplot, salvando poi l'immagine: tutto questo attraverso un modulo dedicato
path_profile.sh
# visualizziamo a monitor le mappe create, dando la possibilità di interrogarle, e le salviamo nella cartella 
region_layout2.sh

# Esportiamo quanto visualizzato sul monitor come immagine, in modo che possa essere visualizzata ad esempio su un browser
#rm $folder/immagini/immagine.png
#d.out.file output=$folder/immagini/immagine format=png resolution=2 compression=9 quality=75 paper=a4 ps_level=2

g.remove rast=tmp_walkout,tmp_walkout_min,tmp_friction,tmp_friction_offroad,tmp_rast$paths,tmp_slope_percentuale,tmp_aspect --quiet
g.remove rast=tmp_drainout,tmp_thinout,tmp_punto_minimo_rast,tmp_costo_sentiero vect=tmp_stop_point,tmp_frane,tmp_no_guado --quiet
g.rename vect=tmp_sentiero_trovato,$output --quiet
g.remove vect=tmp_partenza --quiet

g.message -i "Il modulo POINT2PATH e' terminato correttamente"
g.message -i "_______________________________________________"
# torniamo al menù principale
#pastro.sh
