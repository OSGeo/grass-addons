#!/usr/bin/env python
################################################################################
#
# MODULE:       r.wf.py
#
# AUTHOR(S):    Massimo Di Stefano, Francesco Di Stefano, Margherita Di Leo 
#               
#
# PURPOSE:      The module produces the Width Function of a basin. The Width 
#               Function W(x) gives the number of the cells in a basin at a 
#               flow distance x from the outlet (distance-area function)
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
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Distance to outlet map (from r.stream.distance) 
#% required: yes
#%end
#%option
#% key: image
#% type: string
#% gisprompt: new_file,file,input
#% key_desc: image
#% description: output plot
#% required: yes
#%END


import sys
import os
import matplotlib #required by windows
matplotlib.use('wx') #required by windows
import matplotlib.pyplot as plt
import grass.script as grass
import numpy as np

def main():
    stats = grass.read_command('r.stats', input = options['map'], fs = 'space', nv = '*', nsteps = '255', flags = 'Anc').split('\n')[:-1]

    # res = cellsize
    res = float(grass.read_command('g.region', rast = options['map'], flags = 'm').strip().split('\n')[4].split('=')[1])    
    zn = np.zeros((len(stats),4),float)
    kl = np.zeros((len(stats),2),float)
    prc = np.zeros((9,2),float)

    for i in range(len(stats)):
        if i == 0:
            zn[i,0],  zn[i,1] = map(float, stats[i].split(' '))
            zn[i,1] = zn[i,1]
            zn[i,2] = zn[i,1] * res
        if i != 0:
            zn[i,0],  zn[i,1] = map(float, stats[i].split(' '))
            zn[i,2] = zn[i,1] + zn[i-1,2] 
            zn[i,3] = zn[i,1] * (res**2)

    totcell = sum(zn[:,1])
    print "Tot. cells", totcell
    totarea = totcell * (res**2)
    print "Tot. area", totarea
    maxdist = max(zn[:,0])
    print "Max distance", maxdist

    for i in range(len(stats)):
        kl[i,0] = zn[i,0] 
        kl[i,1] = zn[i,2] / totcell 

    # quantiles
    prc[0,0] , prc[0,1] = findint(kl,0.05) , 0.05   
    prc[1,0] , prc[1,1] = findint(kl,0.15) , 0.15    
    prc[2,0] , prc[2,1] = findint(kl,0.3) , 0.3
    prc[3,0] , prc[3,1] = findint(kl,0.4) , 0.4
    prc[4,0] , prc[4,1] = findint(kl,0.5) , 0.5
    prc[5,0] , prc[5,1] = findint(kl,0.6) , 0.6
    prc[6,0] , prc[6,1] = findint(kl,0.7) , 0.7
    prc[7,0] , prc[7,1] = findint(kl,0.85) , 0.85
    prc[8,0] , prc[8,1] = findint(kl,0.95) , 0.95

    # plot
    plotImage(zn[:,0], zn[:,3], options['image']+'_width_function.png','-','x','W(x)','Width Function')

    print "==========================="
    print "Whidth Function | quantiles"
    print "==========================="
    print '%.0f' %findint(kl,0.05) , "|", 0.05
    print '%.0f' %findint(kl,0.15) , "|", 0.15
    print '%.0f' %findint(kl,0.3) , "|", 0.3
    print '%.0f' %findint(kl,0.4) , "|", 0.4
    print '%.0f' %findint(kl,0.5) , "|", 0.5
    print '%.0f' %findint(kl,0.6) , "|", 0.6
    print '%.0f' %findint(kl,0.7) , "|", 0.7
    print '%.0f' %findint(kl,0.85) , "|", 0.85
    print '%.0f' %findint(kl,0.95) , "|", 0.95
    print '\n'
    print 'Done!'

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

def findint(kl,f):
    Xf = np.abs(kl-f); Xf = np.where(Xf==Xf.min())
    z1 , z2 , f1 , f2 = kl[float(Xf[0])][0] , kl[float(Xf[0]-1)][0] , kl[float(Xf[0])][1] , kl[float(Xf[0]-1)][1]
    z = z1 + ((z2 - z1) / (f2 - f1)) * (f - f1)
    return z


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

