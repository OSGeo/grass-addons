#!/usr/bin/env python3

#%module
#% description: Calculates the multiscale topographic position index
#% keyword: raster
#%end

#%option G_OPT_R_INPUT
#% key: input
#% label: Elevation
#% description: Input DEM from which to calculate mTPI
#% required : yes
#% multiple: no
#%end

#%option
#% key: minradius
#% type: integer
#% label: Smoothing neighborhood radius size (minimum)
#% description: Minimum neighborhood radius in pixels for DEM smoothing
#% answer: 1
#% required: yes
#%end

#%option
#% key: maxradius
#% type: integer
#% label: Smoothing neighborhood radius size (maximum)
#% description: Maximum neighborhood radius in pixels for DEM smoothing
#% answer: 11
#% required: yes
#%end

#%option
#% key: steps
#% type: integer
#% label: Number of scaling steps
#% description: Number of steps to use for DEM generalization between minradius and maxradius
#% answer: 3
#% required: yes
#%end

#%option
#% key: processes
#% type: integer
#% description: Number of parallel processes for tiled calculation (<0 is all cpus -1, -2 etc.)
#% answer: 1
#% required: no
#%end

#%option
#% key: width
#% type: integer
#% description: Width of tiles
#% answer: 1000
#% required: no
#%end

#%option
#% key: height
#% type: integer
#% description: Height of tiles
#% answer: 1000
#% required: no
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% description: Multi-scale topographic position index
#% required: yes
#%end

import atexit
import math
import multiprocessing as mp
import random
import string
import sys
from subprocess import PIPE

import grass.script as gs
import numpy as np
from grass.pygrass.modules.grid.grid import GridModule
from grass.pygrass.modules.shortcuts import general as gg
from grass.pygrass.modules.shortcuts import raster as gr
from grass.script import parse_key_val

RAST_REMOVE = []


def cleanup():
    for ras in RAST_REMOVE:
        gg.remove(flags="f", type="raster", name=ras, quiet=True)


def get_temp(prefix=None):
    if prefix is None:
        prefix = "tmp"

    rand_id = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(8)]
    )
    tmp = "_".join([prefix, rand_id])
    return tmp


def tile_shape(region, n_jobs):
    """Calculates the number of tiles required for one tile per cpu

    Parameters
    ----------
    region : pygrass.gis.region.Region
        The computational region object.
    
    n_jobs : int
        The number of processing cores.
    
    Returns
    -------
    width, height : tuple
        The width and height of each tile.
    """
    n = math.sqrt(n_jobs)
    width = int(math.ceil(region.cols / n))
    height = int(math.ceil(region.rows / n))

    return width, height


def main():
    # options and flags
    options, flags = gs.parser()
    input_raster = options["input"]
    minradius = int(options["minradius"])
    maxradius = int(options["maxradius"])
    steps = int(options["steps"])
    output_raster = options["output"]

    processes = int(options["processes"])
    width = int(options["width"])
    height = int(options["height"])

    # some checks
    if "@" in output_raster:
        output_raster = output_raster.split("@")[0]

    if maxradius <= minradius:
        gs.fatal("maxradius must be greater than minradius")

    if steps < 2:
        gs.fatal("steps must be greater than 1")

    if processes == 0:
        gs.fatal("Number of processing cores for parallel computation must not equal 0")

    if processes < 0:
        system_cores = mp.cpu_count()
        processes = system_cores + processes + 1

    # calculate radi for generalization
    radi = np.linspace(minradius, maxradius, steps, dtype="int")
    radi = np.unique(radi)[::-1]
    sizes = radi * 2 + 1

    # multiscale calculation
    ztpi_maps = list()

    for i, (size, radius) in enumerate(zip(sizes, radi)):
        # generalize the dem
        gs.message("Generalizing DEM at scale step {r}".format(r=radius))
        generalized_raster = get_temp("generalized")
        RAST_REMOVE.append(generalized_raster)

        if processes > 1:
            grd = GridModule(
                cmd="r.neighbors",
                width=width,
                height=height,
                overlap=radius + 1,
                processes=processes,
                split=False,
                input=input_raster,
                output=generalized_raster,
                method="average",
                size=size,
                flags="c",
            )

            # set module output to single
            param = grd.module.outputs["output"]
            param.multiple = False
            param.value = param.value[0]
            grd.run()

        else:
            gr.neighbors(
                input=input_raster,
                output=generalized_raster,
                method="average",
                size=size,
                flags="c",
            )

        # topographic position index
        gs.message("Calculating the TPI at scale step {r}".format(r=radius))
        tpi = get_temp("tpi")
        expr = "{x} = {a} - {b}".format(x=tpi, a=input_raster, b=generalized_raster)
        gs.mapcalc(expr)
        RAST_REMOVE.append(tpi)

        # standardize the tpi
        gs.message("Standardizing the TPI at scale step {r}".format(r=radius))
        raster_stats = gr.univar(map=tpi, flags="g", stdout_=PIPE).outputs.stdout
        raster_stats = parse_key_val(raster_stats)
        tpi_mean = float(raster_stats["mean"])
        tpi_std = float(raster_stats["stddev"])

        ztpi = get_temp("ztpi")
        expr = "{x} = ({a} - {mean})/{std}".format(
            x=ztpi, a=tpi, mean=tpi_mean, std=tpi_std
        )
        gs.mapcalc(expr)
        ztpi_maps.append(ztpi)

        # integrate
        if i == 0:
            tpi_updated1 = ztpi
        else:
            gs.message("Integrating the TPI at scale steps {r}".format(r=radius))
            tpi_updated2 = get_temp("integral")
            expr = "{x} = if(abs({a}) > abs({b}), {a}, {b})".format(
                a=ztpi_maps[i], b=tpi_updated1, x=tpi_updated2
            )
            gr.mapcalc(expr, overwrite=True)
            gg.remove(type="raster", name=ztpi_maps[i - 1], flags="f", quiet=True)

            if i > 1:
                gg.remove(type="raster", name=tpi_updated1, flags="f", quiet=True)

            tpi_updated1 = tpi_updated2

    gg.rename(raster=(tpi_updated2, output_raster), quiet=True)
    gg.remove(type="raster", name=ztpi, flags="f", quiet=True)
    gr.colors(map=output_raster, color="haxby", flags="e", quiet=True)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
