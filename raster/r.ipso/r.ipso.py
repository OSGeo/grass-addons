#!/usr/bin/env python
################################################################################
#
# MODULE:       r.ipso.py
#
# AUTHOR(S):    Massimo Di Stefano, Francesco Di Stefano 2010-02-7
#               
#
# PURPOSE:      Output a Ipsometric and ipsographic graph 
#
# COPYRIGHT:    (c) 2010 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# REQUIRES:     Matplotlib
#                 http://matplotlib.sourceforge.net/
#               
#
################################################################################
#%module
#% description: 
#% keywords: raster
#%end
#%option
#% key: map
#% type: string
#% gisprompt: old,raster,raster
#% key_desc: name
#% description: Name of raster map 
#% required: yes
#%end
#%option
#% key: image
#% type: string
#% gisprompt: new_file,file,input
#% key_desc: image
#% description: output graph
#% required: yes
#%end
#%flag
#% key: a
#% description: generate ipsometric curve
#%END
#%flag
#% key: b
#% description: generate ipsographic curve
#%END

import sys
import os
import matplotlib.pyplot as plt
import grass.script as grass
import numpy as np

def main():
    stats = grass.read_command('r.stats', input = options['map'], fs = 'space', nv = '*', nsteps = '255', flags = 'inc').split('\n')[:-1]
    res = float(grass.read_command('g.region', rast = options['map'], flags = 'm').strip().split('\n')[4].split('=')[1])
    zn = np.zeros((len(stats),6),float)
    kl = np.zeros((len(stats),2),float)
    prc = np.zeros((9,2),float)
    for i in range(len(stats)):
        if i == 0:
            zn[i,0], zn[i, 1] = map(float, stats[i].split(' '))
            zn[i,2] = zn[i,1]
        if i != 0:
            zn[i,0], zn[i, 1] = map(float, stats[i].split(' '))
            zn[i,2] = zn[i,1] + zn[i-1,2]
    totcell = sum(zn[:,1])
    for i in range(len(stats)):
        zn[i,3] = 1 - (zn[i,2] / sum(zn[:,1]))
        zn[i,4] = zn[i,3] * (((res**2)/1000000)*sum(zn[:,1]))
        zn[i,5] = ((zn[i,0] - min(zn[:,0])) / (max(zn[:,0]) - min(zn[:,0])) )
        kl[i,0] = zn[i,0]
        kl[i,1] = 1 - (zn[i,2] / totcell)
    prc[0,0] , prc[0,1] = findint(kl,0.025) , 0.025
    prc[1,0] , prc[1,1] = findint(kl,0.05) , 0.05
    prc[2,0] , prc[2,1] = findint(kl,0.1) , 0.1
    prc[3,0] , prc[3,1] = findint(kl,0.25) , 0.25
    prc[4,0] , prc[4,1] = findint(kl,0.5) , 0.5
    prc[5,0] , prc[5,1] = findint(kl,0.75) , 0.75
    prc[6,0] , prc[6,1] = findint(kl,0.9) , 0.9
    prc[7,0] , prc[7,1] = findint(kl,0.95) , 0.95
    prc[8,0] , prc[8,1] = findint(kl,0.975) , 0.975
    if flags['a']:
        plotImage(zn[:,3], zn[:,5],options['image']+'_Ipsometric.png','-','A(i) / A','Z(i) / Zmax','Ipsometric Curve')
    if flags['b']:
        plotImage(zn[:,4], zn[:,0],options['image']+'_Ipsographic.png','-','A [km^2]','Z [m.slm]','Ipsographic Curve')
    print prc


def findint(kl,f):
    Xf = np.abs(kl-f); Xf = np.where(Xf==Xf.min())
    z1 , z2 , f1 , f2 = kl[float(Xf[0])][0] , kl[float(Xf[0]-1)][0] , kl[float(Xf[0])][1] , kl[float(Xf[0]-1)][1]
    z = z1 + ((z2 - z1) / (f2 - f1)) * (f - f1)
    return z

def plotImage(x,y,image,type,xlabel,ylabel,title):
    plt.plot(x, y, type)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.xlim( min(x), max(x) )
    plt.ylim( min(y), max(y) )
    plt.title(title)
    plt.grid(True)
    plt.savefig(image)
    plt.close('all') 
    
if __name__ == "__main__":
	options, flags = grass.parser()
	sys.exit(main())


