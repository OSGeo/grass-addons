#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODULE:  "REGION_ZOOM SH" per GRASS 6.4 (GRASS Shell Script)				          #
#											          #
# AUTHOR:  Damiano Natali (damiano.natali@gmail.com)					          #
#										          	  #
# PURPOSE: Script di servizio che gestisce il dialogo per l'individuazione della regione attiva   #
#											  	  #
# This program is free software under the GNU General Public License (>=v2). 		  	  #
# Read the file COPYING that comes with GRASS for details.				  	  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

echo "Usa il mouse per selezionare l'area di interesse"
echo

d.zoom -f
while [ "$RISP" != "s" ]
   do echo
   echo -n "La regione selezionata è quella desiderata? [s/n] "
   if [ "$RISP" == "n" ]
      then d.zoom -f
   fi
   read RISP
done
echo
echo 'La regione attuale ha queste caratteristiche'
echo
g.region -p
echo

# Valutiamo i parametri della nuova regione
# eval `g.region -g`
# : ${n?} ${s?} ${w?} ${e?} ${nsres?}

# echo -n 'Limite nord della nuova regione? '
# read lim_n
# if ! [ $lim_n ]
#    then lim_n=$n
# fi
# echo -n 'Limite sud della nuova regione? '
# read lim_s
# if ! [ $lim_s ]
#    then lim_s=$s
# fi
# echo -n 'Limite est della nuova regione? '
# read lim_e
# if ! [ $lim_e ]
#    then lim_e=$e
# fi
# echo -n 'Limite ovest della nuova regione? '
# read lim_w
# if ! [ $lim_w ]
#    then lim_w=$w
# fi

while ! [ $RISOL ]; do
   echo -n 'Risoluzione della nuova regione? '
   read RISOL
done

echo
echo 'La regione di calcolo è'
g.region -p res=$RISOL
# g.region -p n=$lim_n s=$lim_s e=$lim_e w=$lim_w res=$risol
echo

exit 0
