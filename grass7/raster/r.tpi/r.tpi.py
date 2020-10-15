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
#% answer: 5
#% required: yes
#%end

#%option
#% key: processes
#% type: integer
#% description: Number of parallel processes (<0 is all cpus -1, -2 etc.)
#% answer: 1
#% required: no
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% description: Multi-scale topographic position index
#% required: yes
#%end

import atexit
import multiprocessing as mp
import random
import string
import sys
from subprocess import PIPE

import grass.script as gs
import numpy as np
from grass.pygrass.modules.shortcuts import general as gg
from grass.pygrass.modules.shortcuts import raster as gr
from grass.script import parse_key_val
from grass.pygrass.modules import Module, ParallelModuleQueue

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


def main():
    # options and flags
    options, flags = gs.parser()
    input_raster = options["input"]
    minradius = int(options["minradius"])
    maxradius = int(options["maxradius"])
    steps = int(options["steps"])
    output_raster = options["output"]
    processes = int(options["processes"])

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
    radi = np.unique(radi)
    sizes = radi * 2 + 1

    # multiscale calculation
    ztpi_maps = list()

    # create module queue
    queue = ParallelModuleQueue(nprocs=processes)
    Module(
        cmd="r.neighbors", 
        input=input_raster,
        method="average",
        flags="c",
        run_=False
    )

    # create generalized rasters
    gs.message("Generalizing input raster at each scale step")
    queue = ParallelModuleQueue(nprocs=processes)
    generalized_maps = list()

    for i, (size, radius) in enumerate(zip(sizes, radi)):
        generalized_raster = get_temp("generalized")
        generalized_maps.append(generalized_raster)
        RAST_REMOVE.append(generalized_raster)
        mod = Module(
            cmd="r.neighbors", 
            input=input_raster,
            method="average",
            flags="c",
            size=size,
            output=generalized_raster,
            run_=False
        )
        queue.put(mod)
    queue.wait()

    # calculate the tpi indices
    gs.message("Calculating the TPI at each scale step")
    queue = ParallelModuleQueue(nprocs=processes)
    tpi_maps = list()

    for generalized in generalized_maps:
        tpi = get_temp("tpi")
        tpi_maps.append(tpi)
        RAST_REMOVE.append(tpi)
        mod = Module(
            cmd="r.mapcalc",
            expr="{x} = {a} - {b}".format(x=tpi, a=input_raster, b=generalized),
            run_=False
        )
        queue.put(mod)
    queue.wait()

    # standardize the tpi
    gs.message("Standardizing the TPI at each scale step")
    queue = ParallelModuleQueue(nprocs=processes)
    ztpi_maps = list()
    
    for tpi in ztpi_maps:
        raster_stats = gr.univar(map=tpi, flags="g", stdout_=PIPE).outputs.stdout
        raster_stats = parse_key_val(raster_stats)
        tpi_mean = float(raster_stats["mean"])
        tpi_std = float(raster_stats["stddev"])

        ztpi = get_temp("ztpi")
        ztpi_grids.append(ztpi)
        ztpi_maps.append(ztpi)
        expr = "{x} = ({a} - {mean})/{std}".format(
            x=ztpi, a=tpi, mean=tpi_mean, std=tpi_std
        )
        mod = Module(cmd="r.mapcalc", expr=expr, run_=False)
        queue.put(mod)
    queue.wait()

    # integrate
    for i, ztpi in enumerate(ztpi_grids):
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
