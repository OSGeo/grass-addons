#!/bin/bash

#!/bin/bash

############################################################################
#
# MODULE:  	script to uninstall "P.A.S.T.R.O." on GRASS 6.4 (GRASS Shell Script)											
# AUTHOR:  	Tiziano Cosso (tiziano.cosso@gter.it)
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


#rm the fortran codes
rm "$GISBASE/etc/fortran_code"/profilo_pastro  
rm "$GISBASE/etc/fortran_code"/distanze_pastro 
#rm profilo_pastro
#rm distanze_pastro 

rm "$GISBASE/scripts"/r.pastro
rm "$GISBASE/scripts"/sheltgar.sh 
rm "$GISBASE/scripts"/pathgar.sh 
rm "$GISBASE/scripts"/stragfinder.sh 
rm "$GISBASE/scripts"/point2point.sh 
rm "$GISBASE/scripts"/point2path.sh
rm "$GISBASE/scripts"/path_profile.sh 
rm "$GISBASE/scripts"/region_layout.sh  
rm "$GISBASE/scripts"/region_zoom.sh 
rm "$GISBASE/scripts"/digit_input.sh
rm "$GISBASE/scripts"/grafico.p
rm "$GISBASE/scripts"/space2tab.py
rm "$GISBASE/scripts"/velocity.py
