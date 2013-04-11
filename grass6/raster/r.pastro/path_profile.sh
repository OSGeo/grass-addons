#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODULE:  "PATH_PROFILE SH" per GRASS 6.4 (GRASS Shell Script)				          #
#											          #
# AUTHOR:  Damiano Natali (damiano.natali@gmail.com)					          #
#	   Roberto Marzocchi (roberto.marzocchi@gmail.com)			          	  #
# PURPOSE: Script che fornisce l'immagine del profilo altimetrico di un PERCORSO di tracciato     #
#	   vettoriale imposto dall'utente							  #
#											  	  #
# This program is free software under the GNU General Public License (>=v2). 		  	  #
# Read the file COPYING that comes with GRASS for details.				  	  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# ritagliamo il dtm e la mappa di costo sul PERCORSO del sentiero
#echo 'profilo_dtm=if(!isnull(drainout),dtm10,null())' | r.mapcalc
#echo 'profilo_costo=if(!isnull(drainout),walkout,null())' | r.mapcalc
r.mapcalc "tmp_profilo_dtm=if(!isnull(tmp_drainout),$dtm,null())"
r.mapcalc "tmp_profilo_costo=if(!isnull(tmp_drainout),tmp_walkout,null())"
r.mapcalc "tmp_profilo_costo_min=if(!isnull(tmp_drainout),int(tmp_walkout_min),null())"

#r.thin input=tmp_profilo_costo_min output=tmp_thinout2 iterations=200 --overwrite --quiet	
#r.to.vect -s -v input=tmp_thinout2 output=prova_sentiero_costo feature=line --overwrite --quiet
#g.remove rast=tmp_thinout2
#v.out.ogr format=GML type=line input=prova_sentiero_costo dsn=$folder/costo.gml --quiet
#g.remove vect=prova_sentiero_costo

pref=`mcookie`  # magic cookie di 32-caratteri.

# esportiamo il profilo altimetrico e di costo lungo il sentiero
#g.region res=$res_calcolo
r.out.xyz input=tmp_profilo_dtm output=$folder/profilo_dtm fs="|" --quiet
r.out.xyz input=tmp_profilo_costo output=$folder/costo_profilo fs="|" --quiet
#g.region -a res=$res_calcolo

# prendiamo solamente la parte di file che ci interessa, ovvero la colonna col valore dei raster
cat $folder/profilo_dtm | cut -d '|' -f 1 > $folder/profilo_N
cat $folder/profilo_dtm | cut -d '|' -f 2 > $folder/profilo_E
cat $folder/profilo_dtm | cut -d '|' -f 3 > $folder/profilo_h
cat $folder/costo_profilo | cut -d '|' -f 3 > $folder/profilo_costo

# troviamo il punto più alto del PERCORSO (secondo me non lo fa?????)

# uniamo i due file in uno unico che abbini l'informazione altimetrica a quella di costo, attraverso un eseguibile in fortran compilato con gfortran e ordiniamolo in base al costo

# unisco i files di output e creo un file con 4 colonne (N,E,h,costo)
################################################################################################################################
# quando si installa il file si compilano i files fortran con la seguente sintassi...
# volendo si potrebbero riscrivere in python ?? che non ha il problema della compilazione ed è anche piu multipiattaforma.. 
# gfortran -o profilo_pastro profilo.f90
# gfortran -o distanze_pastro distanze.f90
################################################################################################################################
cp "$GISBASE/etc/fortran_code"/profilo_pastro  "$folder"
cp "$GISBASE/etc/fortran_code"/distanze_pastro  "$folder"
cp "$GISBASE/scripts"/grafico.p "$folder"
cd $folder
touch per_plot
./profilo_pastro

#ordino il file in funzione del costo
sort -n -k 4,4 per_plot > per_plot2
touch per_plot3
touch info_sentiero
touch sentiero.txt
./distanze_pastro

# output informativo
g.message -i "*****************************************************************"
g.message -i "*             CARATTERISTICHE DEL SENTIERO TROVATO              *"
g.message -i "*                                                               *"
g.message -i "*                                                               *"
cat info_sentiero

# chiamo uno script python che inserisco tra gli script di grass che mi crea uno shapefile con una polilinea e,
# per ogni tratto di sentiero, la corrispondente velocita' in km/h
velocity.py
v.in.ogr -o -e dsn=sentiero.shp output=tmp_sentiero_trovato --overwrite --quiet


# stampiamo l'andamento altimetrico usando gnuplot
#cd $folder
gnuplot grafico.p
#echo "load 'grafico.p'"|gnuplot
#echo 'exit'|gnuplot
eog immagini/profilo_altimetrico.gif
cd ..
g.remove rast=tmp_profilo_dtm,tmp_profilo_costo --quiet
