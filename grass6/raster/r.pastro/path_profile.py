#!/usr/bin/env python

############################################################################
#
# MODULE:       path_profile.py
# AUTHOR(S):	Damiano Natali (damiano.natali@gmail.com)					          #
#	   	Roberto Marzocchi (roberto.marzocchi@gmail.com)
#               Converted to Python by Roberto Marzocchi
# PURPOSE:	Script che fornisce l'immagine del profilo altimetrico di un PERCORSO di tracciato 
# COPYRIGHT:	(C) 2011 GTER 
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################
#

##################################################
# librerie chiamate da python
import sys
import os
import string
import time
import shutil,re,glob
import grass.script as grass

space = re.compile(r'\s+')
multiSpace = re.compile(r"\s\s+")
##################################################


# gli passo le variabili d'ambiente che attualmente sono definite da script di shell e non da script python!!! sara' da cambiare nella conversione definitiva a python!!!
dtm=os.getenv('dtm')
folder=os.getenv('folder')

processid = "%.7f" % time.time()

def main():
    #r.mapcalc "tmp_profilo_dtm=if(!isnull(tmp_drainout),$dtm,null())"
    grass.mapcalc("${out} = if(!isnull(${rast1}),${rast2},null())",
              out = tmp_profilo_dtm,
              rast1 = dtm,
              rast2 = tmp_walkout)
    #r.mapcalc "tmp_profilo_costo=if(!isnull(tmp_drainout),tmp_walkout,null())"
    grass.mapcalc("${out} = if(!isnull(${rast1}),${rast2},null())",
              out = tmp_profilo_costo,
              rast1 = tmp_drainout,
              rast2 = tmp_walkout)
    #r.mapcalc "tmp_profilo_costo_min=if(!isnull(tmp_drainout),int(tmp_walkout_min),null())"  
    grass.mapcalc("${out} = if(!isnull(${rast1}),${rast2},null())",
              out = tmp_profilo_costo_min,
              rast1 = tmp_drainout,
              rast2 = tmp_walkout_min)

    grass.run_command('r.thin', input = tmp_profilo_costo_min, output=tmp_thinout2, iterations=200 , overwrite = True, quiet = True)

    grass.run_command('r.to.vect', flags='sv' ,input=tmp_thinout2, output = prova_sentiero_costo, feature = line, verwrite = True, quiet = True) 

    grass.run_command('g.remove', rast=tmp_thinout2, quiet = True)

    profilo_dtm=processid + "_profilo_dtm"
    costo_profilo=processid + "_costo_profilo"
    grass.run_command('r.out.xyz', input=tmp_profilo_dtm, output=folder/profilo_dtm, fs="  ", quiet = True)
    grass.run_command('r.out.xyz', input=tmp_profilo_costo, output=folder/costo_profilo, fs=" ", quiet = True) 


    E=[]
    N=[]
    h=[]
    costo=[]

    for riga in file("profilo_dtm"):  
        #print riga
        line = riga
        a = space.split(line.strip())
        # print a
        E.append(float(a[0]))
        N.append(float(a[1]))
        h.append(float(a[2]))
    for riga in file("costo_profilo"):  
        #print riga
        line = riga
        a = space.split(line.strip())
        # print a
        costo.append(float(a[2])) 

    zipped=zip(costo,E,N,h)
    zipped2=sorted(zipped, key=lambda zipped:zipped[0])   # sort by costo
    costo1, E1, N1, h1 = zip(*zipped2)



    # distanza tra i punti del profilo
    dist=[]
    dist_or=[]
    dist_progr=[]
    pendenza=[]

    from math import sqrt
    i=0
    while i<len(E):
        if i==0:
            dist.append(0.0)
            dist_progr.append(0.0)
            dist_or.append(0.0)
            pendenza.append(0.0)
            i+=1
            # print dist_progr
        else: 
            dist.append( sqrt( (E1[i]-E1[i-1])**2+ (N1[i]-N1[i-1])**2 + (h1[i]-h1[i-1])**2 ) )
            dist_or.append( sqrt( (E1[i]-E1[i-1])**2+ (N1[i]-N1[i-1])**2 ) )
            dist_progr.append(dist_progr[i-1] + dist[i])
            pendenza.append( (h1[i]-h1[i-1])/dist_or[i] )
            #print h1[1]
            #print i,h1[i],h1[i-1],dist_or[i],pendenza[i]
            if i==(len(E)-1):
                dist_finale=dist_progr/1000.0 #distanza in km
            i+=1

    profilo_grafico=processid + "_profilo_grafico"

    miofile = open(profilo_grafico,'w')
    k=0
    while k<len(E):
        miofile.write("%.2f %.2f %.2f\n" % (round(dist_progr[k],2),round(h1[k],2),round(pendenza[k],2)))
        #miofile.write("%.2f %.2f %.2f %.2f %.2f\n" % (round(dist[k],2),round(dist_progr[k],2),round(dist_or[k],2),round(h[k],2),round(pendenza[k],2)))
        k+=1
    miofile.close()	

    # cerco la massima pendenza (secondo me non e' il massimo--> discutere con tiziano)
    pend= max(pendenza)*100

    ####################################################################################
    #export grafico profilo
    grafico.gp=processid + "grafico.gp"
    miofile2 = open(grafico.gp,'w')

    miofile2.write("set grid\n")
    miofile2.write("set xlabel 'distanza'\n")
    miofile2.write("set ylabel 'H'\n")
    miofile2.write("set style line 2 lt 2 lw 2\n")
    miofile2.write("set terminal gif notransparent size 1200,300\n")
    miofile2.write("set nokey\n")
    miofile2.write("set output 'profilo_altimetrico.gif'\n")
    miofile2.write("plot '%s_profilo_grafico' using 1:2 with line ls 2\n" % processid)


    os.getenv('gnuplot' 'miofile')   ###check
    ####################################################################################
    # info sentiero
    # export xml file con le informanzioni sul sentiero profilo

    # output informativo
    grass.message("*****************************************************************")
    grass.message("*             CARATTERISTICHE DEL SENTIERO TROVATO              *")
    grass.message("*                                                               *")
    grass.message("*    Tempo stimato: %d minuti circa                             *"%(M))
    grass.message("*    Lunghezza percorso:%.1f km circa                           *"%dist_finale)
    grass.message("*    Pendenza massima: %.0f%% circa                             *"%pend)
    grass.message("*                                                               *") 	            
    grass.message("*****************************************************************")


    miofile3 = open(info_sentiero.xml,'w')
    miofile3.write("<documentbody>\n")
    miofile3.write("*****************************************************************\n")
    miofile3.write("*             CARATTERISTICHE DEL SENTIERO TROVATO              *\n")
    miofile3.write("*                                                               *\n")
    miofile3.write("*    Tempo stimato: %d minuti circa                             *\n"%(M))
    miofile3.write("*    Lunghezza percorso:%.1f km circa                           *\n"%dist_finale)
    miofile3.write("*    Pendenza massima: %.0f%% circa                             *\n"%pend)
    miofile3.write("*                                                               *\n") 	            
    miofile3.write("*****************************************************************\n")
    miofile3.write("</documentbody>")



    # write cmd history:
    #grass.raster_history(output)
