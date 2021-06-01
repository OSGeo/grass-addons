#!/bin/bash

############################################################################
#
# MODULE:  	script to install "P.A.S.T.R.O." on GRASS 6.4 (GRASS Shell Script)											
# AUTHOR:  	Andrea Cervetto (cervoz@hotmail.com)						
#	   	Damiano Natali (damiano.natali@gmail.com)
#		Tiziano Cosso (tiziano.cosso@gter.it)
#		Roberto Marzocchi (roberto.marzocchi@gmail.com)										
# PURPOSE: 	Utility di calcolo dell'accessibilità in ambito montano	 		
# COPYRIGHT:	This program is free software under the 
#		GNU General Public License (>=v2). 		
# 		Read the file COPYING that comes with GRASS for details.			
#
############################################################################


if  [ -z "$GISBASE" ]
then
	echo ""
	echo "You must be in GRASS GIS to run this program"
	echo ""
	exit 1
fi

if [ -d "$GISBASE/etc/fortran_code" ]
then
 	echo "The directory $GISBASE/etc/fortran_code already exists'"
else 
	echo "The directory $GISBASE/etc/fortran_code do not yet exists. Created!"	
	mkdir "$GISBASE/etc"/fortran_code
fi


#compilo i codici fortan e li copio nella cartella opportuna
gfortran-4.6 -o profilo_pastro profilo.f90
gfortran-4.6 -o distanze_pastro distanze.f90
sudo cp profilo_pastro "$GISBASE/etc/fortran_code"  
sudo cp distanze_pastro "$GISBASE/etc/fortran_code" 
rm profilo_pastro
rm distanze_pastro 
  
#copio i vari scripts nella cartella degli scripts GRASS
sudo cp r.pastro "$GISBASE/scripts"
sudo cp sheltgar.sh "$GISBASE/scripts" 
sudo cp pathgar.sh "$GISBASE/scripts" 
sudo cp stragfinder.sh "$GISBASE/scripts" 
sudo cp point2point.sh "$GISBASE/scripts" 
sudo cp point2path.sh "$GISBASE/scripts"
sudo cp path_profile.sh "$GISBASE/scripts" 
sudo cp region_layout.sh  "$GISBASE/scripts" 
sudo cp region_zoom.sh "$GISBASE/scripts" 
sudo cp digit_input.sh "$GISBASE/scripts"
sudo cp grafico.p "$GISBASE/scripts"
sudo cp space2tab.py "$GISBASE/scripts"
sudo cp velocity.py "$GISBASE/scripts"



sudo chmod 777 "$GISBASE/scripts"/r.pastro
sudo chmod 777 "$GISBASE/scripts"/sheltgar.sh 
sudo chmod 777 "$GISBASE/scripts"/pathgar.sh 
sudo chmod 777 "$GISBASE/scripts"/stragfinder.sh 
sudo chmod 777 "$GISBASE/scripts"/point2point.sh 
sudo chmod 777 "$GISBASE/scripts"/point2path.sh
sudo chmod 777 "$GISBASE/scripts"/path_profile.sh 
sudo chmod 777 "$GISBASE/scripts"/region_layout.sh  
sudo chmod 777 "$GISBASE/scripts"/region_zoom.sh 
sudo chmod 777 "$GISBASE/scripts"/digit_input.sh
sudo chmod 777 "$GISBASE/scripts"/grafico.p
sudo chmod 777 "$GISBASE/scripts"/space2tab.py
sudo chmod 777 "$GISBASE/scripts"/velocity.py
