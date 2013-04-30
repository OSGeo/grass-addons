#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# MODULE:  "REGION_LAYOUT SH" per GRASS 6.4 (GRASS Shell Script)				  #
#											          #
# AUTHOR:  Damiano Natali (damiano.natali@gmail.com)					          #
#	   Roberto Marzocchi (roberto.marzocchi@gmail.com)			          	  #
# PURPOSE: Script di servizio che gestisce il dialogo per la visualizzazione, l'interrogazione    #
#	   ed il salvataggio delle mappe							  #
#											  	  #
# This program is free software under the GNU General Public License (>=v2). 		  	  #
# Read the file COPYING that comes with GRASS for details.				  	  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



# Esportiamo, nei casi in cui ciò serve, il sentiero trovato come file .gpx da caricare direttamente su un ricevitore
if [ "$FUNCTION" = "4" ]||[ "$FUNCTION" = "5" ]; then	
	rm $folder/TRACK.gml
	rm $folder/TRACK.xsd
   	#v.out.gpsbabel -t input=tmp_sentiero_trovato type=line output=$folder/TRACK.gpx --quiet
	v.out.ogr format=GML type=line input=tmp_sentiero_trovato dsn=$folder/TRACK.gml --quiet
	# Esportiamo quanto visualizzato sul monitor come immagine, in modo che possa essere visualizzata ad esempio su un browser
	###########################################################################################################################
	### planimetria? non si capisce a cosa si riferisce (distinguere caso 3 da 4???)
	###########################################################################################################################
	rm $folder/immagini/planimetria_sentiero.png
	g.region save=temp_calcoli --overwrite
	g.region vect=tmp_sentiero_trovato save=tmp2_pastro res=$res_calcolo --overwrite
	d.out.file output=$folder/immagini/planimetria_sentiero format=png resolution=2 compression=9 quality=75 paper=a4 ps_level=2 --quiet	
	g.region region=temp_calcoli
	g.remove region=tmp2_pastro --quiet
	g.remove region=temp_calcoli --quiet
fi

# torniamo al menù principale
# d.mon stop=x3
#exit 0
