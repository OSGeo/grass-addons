#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODULE:  "POINT2POINT SH" per GRASS 6.4 (GRASS Shell Script)				          #
#											          #
# AUTHOR:  Andrea Cervetto (cervoz@hotmail.com)						          #
#	   Damiano Natali (damiano.natali@gmail.com)					          #
#	   Roberto Marzocchi (roberto.marzocchi@gmail.com)			          	  #
# PURPOSE: Individua il PERCORSO ottimale tra da due punti e ne calcola il tempo di percorrenza	  #
#	   Il presente modulo viene solitamente lanciato dallo script pastro.sh.	  	  #
#											  	  #
# This program is free software under the GNU General Public License (>=v2). 		  	  #
# Read the file COPYING that comes with GRASS for details.				  	  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



# creazione di un report relativo alla regione corrente
#FILELOG='/home/damiano/spin-off/provincia_spezia/webgis/tmp/filelog/sheltgar.txt'
FILELOG="$folder/sheltgar.txt"

# valutazione del percorso della location
eval `g.gisenv`
: ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}
LOCATION="$GISDBASE/$LOCATION_NAME/$MAPSET"

clear

g.message -i "*********************************"
g.message -i "|        POINT2POINT.SH         |"
g.message -i "| Calcolo del PERCORSO ottimale |"
g.message -i "|     tra due punti imposti     |"
g.message -i "*********************************"	





########################################################################################################################################
##### DA QUA PULITO
########################################################################################################################################

# creazione della mappa delle friction
v.to.rast input=$paths output=tmp_rast$paths use=val type=line --overwrite --quiet
r.slope.aspect elevation=$dtm slope=tmp_slope_percentuale aspect=tmp_aspect format=percent prec=float zfactor=1.0 min_slp_allowed=0.0 --overwrite --quiet 


#r.mapcalc 'tmp_friction_offroad=if(!isnull(frane),2,if(tmp_slope_percentuale>0.77,5,1))'
r.mapcalc 'tmp_friction_offroad=if(tmp_slope_percentuale>77,5,if(!isnull(tmp_no_guado),5,if(!isnull(tmp_frane),2,1)))'
#r.mapcalc "tmp_friction_offroad=if(tmp_slope_percentuale>0.77,5,1)" # carta temporanea
r.mapcalc "tmp_friction=if(!isnull(tmp_rast$paths),0,tmp_friction_offroad)"
# echo 'tmp_friction_offroad=if(tmp_slope_percentuale>0.77,5,1)' | r.mapcalc
# echo 'tmp_friction=if(!isnull(tmp_sentieri_rast),0,tmp_friction_offroad)' | r.mapcalc


#####DEBUG ROBERTO #########
#conviene aggiungere un filling perche' per percorsi lunghi i sink del dtm creano dei problemi...
#direi che ora funziona tutto bene
r.fill.dir -f input=$dtm elevation=tmp_dtm_filled direction=tmp_dtm_dir areas=tmp_areas_dtm --overwrite --quiet


# calcolo mappa di costo in secondi e in minuti
#r.walk -k elevation=$dtm friction=tmp_friction output=tmp_walkout start_points=$partenza stop_points=$arrivo max_cost=0 percent_memory=100 nseg=4 walk_coeff=$a,$b,$c,$d lambda=1.0 slope_factor=$s_f --overwrite --quiet

r.mapcalc "tmp_friction2=tmp_friction*30"
r.walk -k elevation=tmp_dtm_filled friction=tmp_friction output=tmp_walkout start_points=$partenza stop_points=$arrivo max_cost=0 percent_memory=100 nseg=4 walk_coeff=$a,$b,$c,$d lambda=1.0 slope_factor=$s_f --overwrite --quiet

g.remove rast=tmp_dtm_filled,tmp_dtm_dir,tmp_areas_dtm --quiet

#####DEBUG ROBERTO ######### 
#conviene aggiungere un filling perche' per percorsi lunghi sembrano crearsi dei sink...la ragione non e' chiarissima --> forse e' il caso di approfondire
#r.fill.dir input=tmp_walkout elevation=tmp_walkout_filled direction=tmp_walkout_dir --overwrite --quiet

r.mapcalc 'tmp_walkout_min=tmp_walkout/60'
#echo 'walkout_min=walkout/60' | r.mapcalc
 
# calcola il PERCORSO a minima energia
#nuovo filling (solo sulle unrisolved areas!!!)
r.fill.dir -f input=tmp_walkout elevation=tmp_walkout_filled direction=tmp_walkout_dir areas=tmp_areas_walkout --overwrite --quiet
r.drain -c input=tmp_walkout_filled output=tmp_drainout vector_points=$arrivo --overwrite --quiet
g.remove rast=tmp_walkout_filled,tmp_walkout_dir,tmp_areas_walkout --quiet

r.mapcalc "tmp_drainout2=if(!isnull(tmp_drainout),if(!isnull(tmp_rast$paths),1,2),null())"

# creazione del vettoriale del PERCORSO (messo dentro path_profile.sh)
#r.thin input=tmp_drainout2 output=tmp_thinout iterations=200 --overwrite --quiet
#r.to.vect -s -v input=tmp_thinout output=tmp_sentiero_trovato feature=line --overwrite --quiet

# creiamo il profilo del sentiero e stampiamolo con gnuplot, salvando poi l'immagine: tutto questo attraverso un modulo dedicato
path_profile.sh

# visualizziamo a monitor le mappe create, dando la possibilità di interrogarle, e le salviamo nella cartella 
# $folder/tmp
region_layout.sh


g.remove rast=tmp_walkout,tmp_walkout_min,tmp_friction,tmp_friction_offroad --quiet
g.remove  rast="tmp_rast"$paths,tmp_slope_percentuale,tmp_aspect,tmp_drainout,tmp_thinout,tmp_frane,tmp_no_guado --quiet
g.remove vect=tmp_arrivo,tmp_partenza --quiet

g.rename vect=tmp_sentiero_trovato,$output --quiet --overwrite

g.message -i "Il modulo POINT2POINT e' terminato correttamente"
g.message -i "________________________________________________"
# torniamo al menù principale
#pastro.sh
