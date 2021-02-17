#!/usr/bin/env python
#-*- coding:utf-8 -*-
#
############################################################################
#
# MODULE:       
# AUTHOR(S):    Roberto Marzocchi (roberto.marzocchi@gter.it)           
# PURPOSE:	create a shapefile with a polyline with velocity evaluated with the r.walk grass command 
# COPYLEFT:     
# COMMENT:      ...a lot of comments to be easy-to-read for/by beginners
#
#############################################################################


import os,sys,shutil,re,glob
import math
space = re.compile(r'\s+')
multiSpace = re.compile(r"\s\s+") 

# come dipendenze scarica e installa (sudo python setup.py install) la libreria pyshp
# Pure Python read/write support for ESRI Shapefile format
# http://pypi.python.org/pypi/pyshp
import shapefile


nomefile1="per_plot2"
nomefile2="sentiero"

# legge dal file coordinate 
E=[]
N=[]
z=[]
costo=[]

for riga in file(nomefile1): # modifica con nome generico 
    #print riga
    line = riga
    a = space.split(line.strip())
    # print a
    E.append(float(a[0]))
    N.append(float(a[1]))
    z.append(float(a[2]))
    costo.append(float(a[3]))

dist=[]
vel=[]
dif_costo=[]
i=0
while i<len(E):
    if i==0:
        dist.append(0.0)
        vel.append(0.0)
        dif_costo.append(0.0)
        i+=1
        # print dist_progr
    else: 
        dist.append( math.sqrt( (E[i]-E[i-1])**2+ (N[i]-N[i-1])**2 + (z[i]-z[i-1])**2 ) )
        dif_costo.append(costo[i]-costo[i-1])
        vel.append(min(9.99,3.6*dist[i]/dif_costo[i]))
        i+=1




w = shapefile.Writer(shapefile.POLYLINE)
w.field("ID","N",8,0)
w.field("V_km_h","N",8,2)
# Create new shapefile
# Add points to line
#lon_idx, lat_idx = header['Longitude'], header['Latitude']
k=1
while k<len(E)-1:
    #scrivi = "%d %d %d" % E_point[k], % N_point[k], % res[k]
    #print "%.2f %.2f %.2f\n" % (round(E_point[k],2),round(N_point[k],2),round(res[k],2))
    E1=E[k-1]
    N1=N[k-1]
    E2=E[k]
    N2=N[k]
    w.line(parts=[[[E1,N1],[E2,N2]]])
    vv=round(vel[k],2)
    w.record(ID=k,V_km_h=vv)
    k+=1
    #print k,E2,vv

#print "ok"

w.save(nomefile2)	




