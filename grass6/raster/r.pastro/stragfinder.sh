#!/bin/sh

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# MODULE:  "STRAGFINDER SH" per GRASS 6.4 (GRASS Shell Script)				
#											
# AUTHOR:	Damiano Natali (damiano.natali@gmail.com)	
#		Tiziano Cosso (tiziano.cosso@gter.it)				
#											
# PURPOSE: Calcolo dell'area raggiungibile in tot tempo da una persona a piedi.		
#	   Il presente modulo viene solitamente lanciato dallo script pastro.sh.	
#											
# This program is free software under the GNU General Public License (>=v2). 		
# Read the file COPYING that comes with GRASS for details.				
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


#°°°°°°DA VERIFICARE SE SERVE E NEL CASO RENDERLI PERCORSI GENERICI°°°°°#
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

g.message -i "*******************************************************************"
g.message -i "|                          STRAGFINDER.SH                         |"
g.message -i "| 	         Utility per il ritrovamento di dispersi             |"
g.message -i "*******************************************************************"	
#testa inputs obbligatori





#echo -n "Ora approssimativa dell'ultimo avvistamento? [ora.minuti] "
#echo
#°°°°°°°°°°°°°°°°°°PUNTO DI ULTIMO AVVISTAMENTO - TIZIANO°°°°°°°°°°°°°°°°°
# secondo me non serve c'e gia' nella gUI
#if [ -n "$GIS_OPT_IMAGE" ]
#then
#  image="$GIS_OPT_IMAGE"
#else
#  image="$GIS_OPT_DTM"
#fi   




#### verifica se serve (mi sembra un po inutile messo qua)
#d.rast.leg map=$dtm
# image solo se c'è 
#d.rast map=$image 




#read ora_minuti
################################################################################################
#### non so perche ma non funziona (risolto nella GUI se non ci piace vediamo di farlo funzionare)
#ora=${ora_minuti:0:2}
#minuti=${ora_minuti:3:2}
################################################################################################

# messo nella GUI
#while [ "$giorno" != "oggi" ] && [ "$giorno" != "ieri" ] && [ "$giorno" != "altroieri" ]; do
#   echo -n "di che giorno? [oggi/ieri/altroieri] "
#   read giorno
#done

if [ "$giorno" = "oggi" ]
   then stringa_old=$(date +%Y-%m-%d' '$ora:$minuti':00 UTC')
elif [ "$giorno" = "ieri" ]
   then stringa_old=$(date --date=yesterday +%Y-%m-%d' '$ora:$minuti':00 UTC')
elif [ "$giorno" = "altroieri" ]
   then stringa_old=$(date --date='today - 2 days' +%Y-%m-%d|echo' '$ora:$minuti':00 UTC')
fi

# echo $stringa_old
# read
#calcolo il tempo in secondi che intercorre fra l'ultimo avvistamento e l'ora attuale
sec_old=$(date --date="$stringa_old" +%s)
stringa_new=$(date +%Y-%m-%d' '%H:%M:%S' UTC')
sec_new=$(date --date="$stringa_new" +%s)
delta_t=$(($sec_new-$sec_old))

g.message -i "L'ultimo avvistamento e' avvenuto $giorno alle $ora:$minuti , ossia $delta_t secondi fa"


if [ "$delta_t" -lt 0 ] ; then
	g.message -e "The last sighting  is after the actual date and time"
	g.message -e "Please check the input date and time"
	exit 1
fi



#°°°°°°°°GIA' MESSO NELLA GUI°°°°°°°°°
# Impostazione della risoluzione di calcolo
#echo -n "A quale risoluzione vuoi effettuare il calcolo? [m]"
#echo
#read res_calcolo
#g.region res=$res_calcolo

# creazione della mappa delle friction
v.to.rast input=$paths output="tmp_rast"$paths use=val type=line --overwrite --quiet
r.slope.aspect elevation=$dtm slope=tmp_slope_percentuale aspect=tmp_aspect format=percent prec=float zfactor=1.0 min_slp_allowed=0.0 --overwrite --quiet 



#r.mapcalc 'tmp_friction_offroad=if(!isnull(frane),2,if(tmp_slope_percentuale>0.77,5,1))'
r.mapcalc 'tmp_friction_offroad=if(tmp_slope_percentuale>77,5,if(!isnull(tmp_no_guado),5,if(!isnull(tmp_frane),2,1)))'
#r.mapcalc "tmp_friction_offroad=if(tmp_slope_percentuale>0.77,5,1)" # carta temporanea
r.mapcalc "tmp_friction=if(!isnull(tmp_rast$paths),0,tmp_friction_offroad)"
#echo 'friction_offroad=if(!isnull(frane),2,if(slope_percentuale>0.77,5,1))' | r.mapcalc
#echo 'friction=if(!isnull(tmp_rast"$paths"),0,friction_offroad)' | r.mapcalc


# calcolo delle aree raggiungibili a partire dal punto selezionato fino a questo momento
r.walk -k elevation=$dtm friction=tmp_friction output=tmp_walkout start_points=$last_obs max_cost=$delta_t walk_coeff=$a,$b,$c,$d lambda=1.0 slope_factor=$s_f --overwrite --quiet

r.mapcalc 'tmp_walkout_min=tmp_walkout/60.0'

###########################################################################################################################
# questa volta non lo faccio in minuti ma solo in secondi...e' corretto o e' una dimenticanza
###########################################################################################################################

# visualizziamo a monitor le mappe create, dando la possibilità di interrogarle, e le salviamo nella cartella 
# /home/damiano/searching/gis&web/mobilita_ambito_montano/tmp
region_layout.sh
g.rename rast=tmp_walkout_min,$output --quiet
g.remove rast=tmp_friction,tmp_friction_offroad,tmp_rast$paths,tmp_slope_percentuale,tmp_aspect,tmp_frane,tmp_no_guado,tmp_walkout --quiet
g.message -i "Il modulo STRAGFINDER e' terminato correttamente"
g.message -i "________________________________________________"
# torniamo al menù principale
#pastro.sh

exit 0
