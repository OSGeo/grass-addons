#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# MODULE:  "SHELTGAR SH" per GRASS 6.4 (GRASS Shell Script)				#
#											#
# AUTHOR:  Andrea Cervetto (cervoz@hotmail.com)						#
#	   Damiano Natali (damiano.natali@gmail.com)					#
#	   Roberto Marzocchi (roberto.marzocchi@gmail.com)			        #
# PURPOSE: Calcolo del presidio del territorio offerto dai rifugi presenti;		#
#	   Il presente modulo viene solitamente lanciato dallo script pastro.sh.	#
#											#
# This program is free software under the GNU General Public License (>=v2). 		#
# Read the file COPYING that comes with GRASS for details.				#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#nome della cartella delle mappe
#mappe='/home/damiano/spin-off/provincia_spezia/webgis/mappe'

#nome della cartella temporanea
#percorso='/home/damiano/spin-off/provincia_spezia/webgis/tmp'

# creazione di un report relativo alla regione corrente
#FILELOG='/home/damiano/spin-off/provincia_spezia/webgis/tmp/filelog/sheltgar.txt'
#FILELOG="$folder/sheltgar.txt"

g.message -i "La cartella $folder e' stata creata"
# valutazione del percorso della location
eval `g.gisenv`
: ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}
LOCATION="$GISDBASE/$LOCATION_NAME/$MAPSET"

# redirigere lo standard output dallo schermo al file di log
exec 7>&1
exec > "$folder/sheltgar.txt"
#r.univar map=$output > "$folder/sheltgar.txt"
r.univar map=$dtm > "$folder/sheltgar.txt"

# redirigere lo standard output dal file di log allo schermo, chiudendo il file di log
exec 1<&7 7<&-

# redirigere lo standard input dalla tastiera al file di log
exec 6<&0
exec < "$folder/sheltgar.txt"
read -n31
read numero_celle_tot
read ; read ; read ; read ; read -n3
read numero_celle

# redirigere lo standard input dal file di log alla tastiera, chiudendo il file di log, e calcolo della percentuale di area coperta
exec 0<&6 6<&-
area_coperta=$(echo "scale=2; ($numero_celle/$numero_celle_tot)*100.0" | bc)

clear

g.message -i "*******************************************************************"
g.message -i "...........................SHELTGAR.SH............................."
g.message -i "..Calcolo del presidio del territorio offerto dai rifugi presenti.."
g.message -i "*******************************************************************"	



# zoommiamo sull'area di interesse attraverso uno script apposito
#region_zoom.sh

# creazione della mappa delle friction
v.to.rast input=$paths output="tmp_rast$paths" use=val type=line --overwrite --quiet
r.slope.aspect elevation=$dtm slope=tmp_slope_percentuale aspect=tmp_aspect format=percent prec=float zfactor=1.0 min_slp_allowed=0.0 --overwrite --quiet


# echo 'friction_pendenze=if(slope_percentuale<0.32,2,if(0.32<=slope_percentuale<=0.56,7.5,20))' | r.mapcalc
#echo 'tmp_friction_offroad=if(!isnull(frane),2,if(!isnull(no_guado),5,if(slope_percentuale>0.77,5,1)))' | r.mapcalc
#r.mapcalc 'tmp_friction_offroad=if(!isnull(frane),2,if(!isnull(no_guado),5,if(tmp_slope_percentuale>0.77,5,1)))'
r.mapcalc 'tmp_friction_offroad=if(tmp_slope_percentuale>77,5,if(!isnull(tmp_no_guado),5,if(!isnull(tmp_frane),2,1)))'
#r.mapcalc "tmp_friction_offroad=if(tmp_slope_percentuale>0.77,5,1)" # carta temporanea
#echo 'tmp_friction=if(!isnull("tmp"$path"_rast"),0,tmp_friction_offroad)' | r.mapcalc
r.mapcalc 'tmp_friction=if(!isnull(tmp_rast'$paths'),0,tmp_friction_offroad)'

# calcolo delle aree raggiungibili a partire dai ripari esistenti in meno di tot minuti (parametroda inserire nella pastro_GUI -->sezione sheltgar
#echo 
#while ! [ $tmax ]
#   do echo -n 'Digita la distanza massima in minuti a partire dai ripari esistenti che si desidera considerare: '
#   read tmax
#done


#g.message -i "The distance from the shelters is$(($tmax*60))s"
g.message -i "La distanza massima dai rifugi e' pari a $tmax minuti, ossia $(($tmax*60)) s"
#echo 'premi un tasto'
#read

r.walk -k --overwrite elevation=$dtm friction=tmp_friction output=tmp_walkout start_points=$shelters max_cost=$(($tmax*60)) walk_coeff=$a,$b,$c,$d lambda=1.0 slope_factor=$s_f --overwrite --quiet

#echo 'tmp_walkout=if(tmp_walkout>'$(($tmax*60))',null(),tmp_walkout)' | r.mapcalc
#echo 'tmp_walkout_min=tmp_walkout/60.0' | r.mapcalc

r.mapcalc 'tmp_walkout=if(tmp_walkout>'$(($tmax*60))',null(),tmp_walkout)'
r.mapcalc 'tmp_walkout_min=tmp_walkout/60.0'

#################################################################################################
#### si potrebbe fare un contour per facilitare la visione? o anche no... 
#################################################################################################

# visualizziamo a monitor le mappe create, dando la possibilità di interrogarle, e le salviamo nella cartella 
# /home/damiano/searching/gis&web/mobilita_ambito_montano/tmp
#region_layout.sh


g.rename rast=tmp_walkout_min,$output --quiet
g.remove rast=tmp_walkout,tmp_friction,tmp_friction_offroad,"tmp_rast"$paths,tmp_slope_percentuale,tmp_aspect,tmp_frane,tmp_no_guado --quiet
#g.message -i "SHELTGAR module correctly termined" 
g.message -i "il modulo SHELTGAR e' concluso correttamente"
g.message -i "____________________________________________"

# torniamo al menù principale
# pastro.sh

exit 0
