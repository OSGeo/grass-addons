#!/usr/bin/env python3

# %module
# % description: Calculates the multiscale topographic position index
# % keyword: raster
# % keyword: surface
# % keyword: terrain
# % keyword: topography
# %end

# %option G_OPT_R_INPUT
# % key: input
# % label: Elevation
# % description: Input DEM from which to calculate mTPI
# % required : yes
# % multiple: no
# %end

# %option
# % key: minradius
# % type: integer
# % label: Smoothing neighborhood radius size (minimum)
# % description: Minimum neighborhood radius in cells for DEM smoothing
# % answer: 1
# % required: yes
# %end

# %option
# % key: maxradius
# % type: integer
# % label: Smoothing neighborhood radius size (maximum)
# % description: Maximum neighborhood radius in cells for DEM smoothing
# % answer: 31
# % required: yes
# %end

# %option
# % key: steps
# % type: integer
# % label: Number of scaling steps
# % description: Number of steps to use for DEM generalization between minradius and maxradius
# % answer: 5
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Multi-scale topographic position index
# % required: yes
# %end

import atexit
import sys
from subprocess import PIPE

import grass.script as gs
import numpy as np
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import general as gg
from grass.pygrass.modules.shortcuts import raster as gr
from grass.pygrass.raster import RasterRow
from grass.script import parse_key_val

RAST_REMOVE = []


def cleanup():
    for ras in RAST_REMOVE:
        gg.remove(flags="f", type="raster", name=ras, quiet=True)


def main():
    # options and flags
    options, flags = gs.parser()
    input_raster = options["input"]
    minradius = int(options["minradius"])
    maxradius = int(options["maxradius"])
    steps = int(options["steps"])
    output_raster = options["output"]

    region = Region()
    res = np.mean([region.nsres, region.ewres])

    # some checks
    if "@" in output_raster:
        output_raster = output_raster.split("@")[0]

    if maxradius <= minradius:
        gs.fatal("maxradius must be greater than minradius")

    if steps < 2:
        gs.fatal("steps must be greater than 1")

    # calculate radi for generalization
    radi = np.logspace(
        np.log(minradius), np.log(maxradius), steps, base=np.exp(1), dtype=np.int
    )
    radi = np.unique(radi)
    sizes = radi * 2 + 1

    # multiscale calculation
    ztpi_maps = list()

    for step, (radius, size) in enumerate(zip(radi[::-1], sizes[::-1])):
        gs.message("Calculating the TPI at radius {radius}".format(radius=radius))

        # generalize the dem
        step_res = res * size
        step_res_pretty = str(step_res).replace(".", "_")
        generalized_dem = gs.tempname(4)

        if size > 15:
            step_dem = gs.tempname(4)
            gg.region(res=str(step_res))
            gr.resamp_stats(
                input=input_raster,
                output=step_dem,
                method="average",
                flags="w",
            )
            gr.resamp_rst(
                input=step_dem,
                ew_res=res,
                ns_res=res,
                elevation=generalized_dem,
                quiet=True,
            )
            region.write()
            gg.remove(type="raster", name=step_dem, flags="f", quiet=True)
        else:
            gr.neighbors(input=input_raster, output=generalized_dem, size=size)

        # calculate the tpi
        tpi = gs.tempname(4)
        gr.mapcalc(
            expression="{x} = {a} - {b}".format(
                x=tpi, a=input_raster, b=generalized_dem
            )
        )
        gg.remove(type="raster", name=generalized_dem, flags="f", quiet=True)

        # standardize the tpi
        raster_stats = gr.univar(map=tpi, flags="g", stdout_=PIPE).outputs.stdout
        raster_stats = parse_key_val(raster_stats)
        tpi_mean = float(raster_stats["mean"])
        tpi_std = float(raster_stats["stddev"])
        ztpi = gs.tempname(4)
        ztpi_maps.append(ztpi)
        RAST_REMOVE.append(ztpi)

        gr.mapcalc(
            expression="{x} = ({a} - {mean})/{std}".format(
                x=ztpi, a=tpi, mean=tpi_mean, std=tpi_std
            )
        )
        gg.remove(type="raster", name=tpi, flags="f", quiet=True)

        # integrate
        if step > 1:
            tpi_updated2 = gs.tempname(4)
            gr.mapcalc(
                "{x} = if(abs({a}) > abs({b}), {a}, {b})".format(
                    a=ztpi_maps[step], b=tpi_updated1, x=tpi_updated2
                )
            )
            RAST_REMOVE.append(tpi_updated2)
            tpi_updated1 = tpi_updated2
        else:
            tpi_updated1 = ztpi_maps[0]

    RAST_REMOVE.pop()
    gg.rename(raster=(tpi_updated2, output_raster), quiet=True)

    # set color theme
    with RasterRow(output_raster) as src:
        color_rules = """{minv} blue
            -1 0:34:198
            0 255:255:255
            1 255:0:0
            {maxv} 110:15:0
            """
        color_rules = color_rules.format(minv=src.info.min, maxv=src.info.max)
        gr.colors(map=output_raster, rules="-", stdin_=color_rules, quiet=True)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
