#!/usr/bin/env python
#
############################################################################
#
# MODULE:	r.droka
# AUTHOR(S):	original idea by: HUNGR (1993)
# 		implementation by:
#               Andrea Filipello -filipello@provincia.verbania.it
#               Daniele Strigaro - daniele.strigaro@gmail.com
# PURPOSE:	Calculates run-out distance of a falling rock mass
# COPYRIGHT:	(C) 2009 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################
#%Module
#% description: Calculates run-out distance of a falling rock mass
#% keyword: rock mass
#% keyword: rockfall
#%End
#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% description: Digital Elevation Model
#% required: yes
#%end
#%option
#% key: start
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of starting points map
#% required : yes
#%end
#%option
#% key: ang
#% type: double
#% description: Shadow angle
#% required: yes
#%end
#%option
#% key: red
#% type: double
#% description: Reduction value
#% answer: 0.9
#% options : 0-1
#% required: yes
#%end
#%option
#% key: m
#% type: double
#% description: Value of rock mass (kg)
#% required: yes
#%end
#% option
#% key: num
#% type: integer
#% description: Number of boulders (>=1)
#% required: yes
#%end
#%option
#% key: prefix
#% type: string
#% gisprompt: new,cell,raster
#% key_desc: name
#% description: Prefix for output raster maps
#% required: yes
#%end
#%option
#% key: n
#% type: integer
#% description: Buffer distance (meters)
#% required: no
#%end

import os
import sys
import time
import math
import string
import re
from grass.script import array as garray
import numpy as np

try:
    import grass.script as grass
except:
    try:
        from grass.script import core as grass

        # from grass.script import core as gcore
    except:
        sys.exit("grass.script can't be imported.")

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main():

    # Read variables
    r_elevation = options["dem"].split("@")[0]
    mapname = options["dem"].replace("@", " ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".", "_")
    start = options["start"]
    start_ = start.split("@")[0]
    gfile = grass.find_file(start, element="vector")
    if not gfile["name"]:
        grass.fatal(_("Vector map <%s> not found") % infile)

    # x = options['x']
    # y = options['y']
    # z = options['z']
    ang = options["ang"]
    red = options["red"]
    m = options["m"]
    num = options["num"]

    n = options["n"]

    # if n == '':
    #    n = 1
    # else:
    #    n = float(n)

    grass.message("Setting variables...")
    prefix = options["prefix"]
    rocks = prefix + "_propagation"
    v = prefix + "_vel"
    vMax = v + "_max"
    vMean = v + "_mean"
    e = prefix + "_en"
    eMax = e + "_max"
    eMean = e + "_mean"

    gregion = grass.region()
    PixelWidth = gregion["ewres"]

    if n == "":
        n = 1
        d_buff = (float(num) * PixelWidth) / 2
    else:
        n = float(n)
        d_buff = n

    # d_buff = (n * PixelWidth)/2

    grass.message("Defining starting points...")
    if int(num) == 1:
        grass.run_command("g.copy", vector=start + ",start_points_", quiet=True)
    else:
        grass.run_command(
            "v.buffer",
            input=start,
            type="point",
            output="start_buffer_",
            distance=d_buff,
            quiet=True,
        )

        grass.run_command(
            "v.random",
            input="start_buffer_",
            npoints=num,
            output="start_random_",
            flags="a",
            quiet=True,
        )

        grass.run_command(
            "v.patch",
            input=start + ",start_random_",
            output="start_points_",
            quiet=True,
        )

    # v.buffer input=punto type=point output=punti_buffer distance=$cellsize
    # v.random -a output=random n=$numero input=punti_buffer
    # v.patch input=punto,random output=patch1

    # Create raster (which will be the input DEM) with value 1
    grass.mapcalc("uno=$dem*0+1", dem=r_elevation, quiet=True)
    what = grass.read_command(
        "r.what",
        map=r_elevation,
        points="start_points_",
        null_value="-9999",  # TODO: a better test for points outside the current region is needed
        quiet=True,
    )
    quota = what.split("\n")

    # Array for the sum of boulders
    tot = garray.array(r_elevation)
    tot[...] = (tot * 0.0).astype(float)

    # Array for velocity
    velMax = garray.array()
    velMean = garray.array()

    # Array for energy
    enMax = garray.array()
    enMean = garray.array()
    grass.message("Waiting...")
    for i in xrange(len(quota) - 1):
        grass.message("Shoot number: " + str(i + 1))
        z = float(quota[i].split("||")[1])
        point = quota[i].split("||")[0]
        x = float(point.split("|")[0])
        y = float(point.split("|")[1])
        # print x,y,z
        # Cost calculation (split and use the starting points in start_raster
        # at the start_coordinates parameter in r.cost call)
        grass.run_command(
            "r.cost",
            flags="k",
            input="uno",
            output="costo",
            start_coordinates=str(x) + "," + str(y),
            quiet=True,
            overwrite=True,
        )

        # Transform cell distance values into metric values using raster resolution
        grass.mapcalc("costo_m=costo*(ewres()+nsres())/2", overwrite=True)

        # Calculate A=tangent of visual angle (INPUT) * cost in meters
        grass.mapcalc("A=tan($ang)*costo_m", ang=ang, overwrite=True)
        grass.mapcalc("C=$z-A", z=z, overwrite=True)
        grass.mapcalc("D=C-$dem", dem=r_elevation, overwrite=True)
        # Area of propagation
        grass.mapcalc("E=if(D>0,1,null())", overwrite=True)
        # delatH value (F)
        grass.mapcalc("F=D*E", overwrite=True)

        # Calculation of velocity
        grass.mapcalc("vel = $red*sqrt(2*9.8*F)", red=red, overwrite=True)
        velocity = garray.array("vel")
        velMax[...] = (np.where(velocity > velMax, velocity, velMax)).astype(float)
        velMean[...] = (velocity + velMean).astype(float)

        # Calculation of the number of boulders
        grass.mapcalc("somma=if(vel>0,1,0)", overwrite=True)
        somma = garray.array("somma")
        tot[...] = (somma + tot).astype(float)

        # Calculation of energy
        grass.mapcalc("en=$m*9.8*F/1000", m=m, overwrite=True)
        energy = garray.array("en")
        enMax[...] = (np.where(energy > enMax, energy, enMax)).astype(float)
        enMean[...] = (energy + enMean).astype(float)
    grass.message("Create output maps...")
    tot.write(rocks)
    velMax.write(vMax)
    velMean[...] = (velMean / i).astype(float)
    velMean.write(vMean)
    enMax.write(eMax)
    enMean[...] = (enMean / i).astype(float)
    enMean.write(eMean)
    # grass.run_command('d.mon',
    #    start = 'wx0')
    # grass.run_command('d.rast' ,
    #    map=vMax)
    # grass.run_command('d.rast' ,
    #    map=vMean)
    # grass.run_command('d.rast' ,
    #    map=eMax)
    # grass.run_command('d.rast' ,
    #    map=eMean)
    if int(num) == 1:
        grass.run_command(
            "g.remove", flags="f", type="vector", name=("start_points_"), quiet=True
        )
    else:
        grass.run_command(
            "g.rename", vect="start_points_," + prefix + "_starting", quiet=True
        )
        grass.run_command(
            "g.remove",
            flags="f",
            type="vector",
            name=("start_buffer_", "start_random_"),
            quiet=True,
        )
    grass.run_command(
        "g.remove",
        flags="f",
        type="raster",
        name=("uno", "costo", "costo_m", "A", "C", "D", "E", "F", "en", "vel", "somma"),
        quiet=True,
    )
    grass.message("Done!")


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
