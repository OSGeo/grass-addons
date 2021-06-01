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

# Visualizziamo su un monitor la mappa di sfondo comune a tutti i moduli, ovvero l'ortofoto
d.mon stop=x3 --quiet
d.mon start=x3
d.erase
############################################################################################
# se non c'e' l'ortofoto si potrebbe mettere l'aspect sotto al dtm con una trasparenza
############################################################################################
if (check_image=1); then	
	d.shadedmap reliefmap=temp_shade drapemap=$dtm
else
	d.rast map=$image			
fi

# Visualizziamo le altre mappe in base al modulo che si è lanciato
if [ "$FUNCTION" = "1" ]||[ "$FUNCTION" = "2" ]
   	then d.rast -o map=tmp_walkout_min
   	d.vect map=$paths display=shape type=line layer=1 color=red fcolor=255:165:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red    bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
   	d.vect map=$shelters display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
elif [ "$FUNCTION" = "3" ]
   	then d.rast -o map=tmp_walkout
   	d.vect map=$paths type=line color=255:165:0 width=1
   	d.vect map=$shelters display=shape type=point layer=1 color=blue fcolor=0:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
   	d.vect map=$last_obs type=point width=2 color=0:0:0 fcolor=255:255:0 icon=basic/circle size=8
	rm $folder/immagini/immagine_stragfinder.png
	d.out.file output=$folder/immagini/immagine_stragfinder format=png resolution=2 compression=9 quality=75 paper=a4 ps_level=2 --quiet
elif [ "$FUNCTION" = "5" ]
   	then d.vect map=$partenza display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
  	d.vect map=$paths display=shape type=line layer=1 color=red fcolor=255:165:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
   	d.vect map=tmp_sentiero_trovato display=shape type=line layer=1 color=green fcolor=255:255:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
	rm $folder/immagini/immagine_point2path.png
	d.out.file output=$folder/immagini/immagine_point2path format=png resolution=2 compression=9 quality=75 paper=a4 ps_level=2 --quiet
### caso 4 
else 
	d.vect map=$partenza display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
   	d.vect map=$arrivo display=shape type=point layer=1 color=blue fcolor=255:255:0 rgb_column=GRASSRGB zcolor=terrain width=0 wscale=1 icon=basic/circle size=8 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
   	d.vect map=tmp_sentiero_trovato display=shape type=line layer=1 color=black fcolor=255:255:0 width=2 wscale=1 icon=basic/x size=5 llayer=1 lcolor=red bgcolor=none bcolor=none lsize=8 xref=left yref=center render=c
	# Esportiamo quanto visualizzato sul monitor come immagine, in modo che possa essere visualizzata ad esempio su un browser
	rm $folder/immagini/immagine_point2point.png
	d.out.file output=$folder/immagini/immagine_point2point format=png resolution=2 compression=9 quality=75 paper=a4 ps_level=2 --quiet
fi

# visualizziamo la barra di scala
d.barscale bcolor=white tcolor=black at=0.2,90

# interroghiamo la mappa (annesse le istruzioni per ogni caso---> da conrollare se van bene)
#echo
if [ "$FUNCTION" = "1" ]
	then 
	g.message -i "E' ora possibile interrogare la mappa sul display X3 e avere il valore in minuti di percorrenza dal piu' vicino riparo"
	d.text -b text="sheltgar output" bgcolor=yellow
elif [ "$FUNCTION" = "2" ]
	then 
	g.message -i "E' ora possibile interrogare la mappa sul display X3 e avere il valore in minuti di percorrenza dal sentiero piu' vicino"
	d.text -b text="Pathgar output" bgcolor=yellow
elif [ "$FUNCTION" = "3" ]
	then  
	g.message -i "Sono visibili sul diplay X3 le aree raggiungibili dal disperso di $giorno alle $ora:$minuti"
	g.message -i "E' possibile interrogare la mappa sul display X3 e avere il valore in minuti percorribile" 
	d.text -b text="Stragfinder output" bgcolor=yellow
elif [ "$FUNCTION" = "4" ]
	then 
        g.message -i "E' visualizzato sulla mappa il percorso ottimale fra i 2 punti prescelti"
	g.message -i "Interrrogando la mappa sul display X3 si puo' avere il valore in minuti di percorrenza dal punto di partenza" ## da verificare che sia questo 
	d.text -b text="point2point output" bgcolor=yellow
else 
	g.message -i "E' visualizzato sulla mappa il percorso ottimale fra il punto di partenza scelto e la rete sentieristica"
	g.message -i "Interrrogando la mappa sul display X3 si puo' avere il valore in minuti di percorrenza dal punto di partenza" ## da verificare che sia questo 
	d.text -b text="point2path output" bgcolor=yellow
fi
d.what.rast map=tmp_walkout_min

###################################################################################################################
#####                 DISCUTERE SE SERVE E EVENTUALMENTE COME METTERLO 
###################################################################################################################
#while [ "$RISP" != "u" ]
#   do echo
#   echo -n 'Vuoi cambiare regione? ("s" per cambiare regione, "u" per uscire e salvare la mappa) '
#   read RISP
#   if [ "$RISP" == "s" ]
#      then d.zoom -f
#     d.what.rast map=walkout_min   
#   fi
#done

# Esportiamo, nei casi in cui ciò serve, il sentiero trovato come file .gpx da caricare direttamente su un ricevitore
if [ "$FUNCTION" = "4" ]||[ "$FUNCTION" = "5" ]; then	
	rm $folder/TRACK.gpx
   	v.out.gpsbabel -t input=tmp_sentiero_trovato type=line output=$folder/TRACK.gpx --quiet
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
