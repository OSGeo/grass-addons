#!/usr/bin/env python3

############################################################################
#
# MODULE:	    Visualize test results
# AUTHOR(S):	Anika Bettge, mundialis
#
# PURPOSE:	    Visualize test results of test.py
# COPYRIGHT:	(C) 2020 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#############################################################################

# python3 visualization.py rmapcalctiled_test.csv images

import grass.script as grass
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys

if len(sys.argv) == 1:
    grass.fatal("No csv file and output folder given")
else:
    csvfile = sys.argv[1]
    if not os.path.isfile(csvfile):
        grass.fatal("%s is no file and cannot be used as csv file" % csvfile)

if len(sys.argv) < 3:
    grass.fatal("No output folder given")
else:
    outputfolder = sys.argv[2]
    if not os.path.isdir(outputfolder):
        os.makedirs(outputfolder)

df = pd.read_csv(csvfile)
df_numpy  = df.to_numpy()

# fieldnames = ['nprocs', 'resolution', 'weight-height', 'number of cells', 'time_rmapcalc', 'time_rmapcalctiled']
nprocs = df_numpy[0,0]
resolutions = df_numpy[:,1]
whs = df_numpy[:,2]
cells = df_numpy[:,3]
times_rmapcalc = df_numpy[:,4]
times_rmapcalctiled = df_numpy[:,5]

# cells images
whs_unique = np.unique(whs)
for wh in whs_unique:
    idx = np.where(whs == wh)
    x = cells[idx]
    y_tiled = times_rmapcalctiled[idx]
    y = times_rmapcalc[idx]
    plt.plot(x, y_tiled, label = "r.mapcalc.tiled (%s processes)" % str(int(nprocs)))
    plt.plot(x, y, label = "r.mapcalc")
    plt.xlabel('Number of cells')
    plt.ylabel('time [sec]')
    plt.title('r.mapcalc vs. r.mapcalc.tiled: number of cells (with width and height %s)' % str(int(wh)))
    plt.legend()
    img = os.path.join(outputfolder, 'rmapcalctiled_numberofcells_widthheight%s.png' % str(int(wh)))
    plt.savefig(img, bbox_inches='tight')
    plt.close()

# height-width images
cells_unique = np.unique(cells)
for c_u in cells_unique:
    idx = np.where(cells == c_u)
    x = whs[idx]
    y_tiled = times_rmapcalctiled[idx]
    plt.plot(x, y_tiled, label = "r.mapcalc.tiled (%s processes)" % str(int(nprocs)))
    plt.xlabel('Height - Weigth')
    plt.ylabel('time [sec]')
    plt.title('r.mapcalc.tiled: weight/height (with cells: %s)' % str(int(c_u)))
    plt.legend()
    img = os.path.join(outputfolder, 'rmapcalctiled_widthheight_numberofcells%s.png' % str(int(c_u)))
    plt.savefig(img, bbox_inches='tight')
    plt.close()
