#!/usr/bin/env python
#-*- coding:utf-8 -*-
#
############################################################################
#
# MODULE:       
# AUTHOR(S):    Roberto Marzocchi (roberto.marzocchi@gmail.com)           
# PURPOSE:	text file formatting
# COPYLEFT:     
# COMMENT:      ...a lot of comments to be easy-to-read for/by beginners
#
#############################################################################


import os,sys,shutil,re,glob
space = re.compile(r'\s+')
multiSpace = re.compile(r"\s\s+") 

nomefile1=".tmp_coord.txt"
nomefile2="tmp_coord2.txt"

# legge dal file coordinate 
E=[]
N=[]

for riga in file(nomefile1): # modifica con nome generico 
    #print riga
    line = riga
    a = space.split(line.strip())
    # print a
    E.append(float(a[0]))
    N.append(float(a[1]))

k=0
miofile = open(nomefile2,'w')
while k<len(E):
    #scrivi = "%d %d %d" % E_point[k], % N_point[k], % res[k]
    #print "%.2f %.2f %.2f\n" % (round(E_point[k],2),round(N_point[k],2),round(res[k],2))
    miofile.write("%.2f|%.2f\n" % (round(E[k],2),round(N[k],2)))
    k+=1
miofile.close()
