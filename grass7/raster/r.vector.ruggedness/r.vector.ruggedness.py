#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Vector Ruggedness Measure
#
# AUTHOR(S):    Adaption of original Sappington et al. (2007) script
#               by Steven Pawley
#
# PURPOSE:      This tool measures terrain ruggedness by calculating the vector
#               ruggedness measure described in Sappington, J.M., K.M. Longshore,
#               and D.B. Thomson. 2007. Quantifiying Landscape Ruggedness for
#               Animal Habitat Analysis: A case Study Using Bighorn Sheep in
#               the Mojave Desert.
#               Journal of Wildlife Management. 71(5): 1419 -1426.
#
# COPYRIGHT:    (C) 2016 Steven Pawley, and by the GRASS Development Team
#
# DATE:         30 June 2016
#
##############################################################################

#%module
#% description: Vector Ruggedness Measure
#%end

import grass.script as grass
import random
import string
import atexit
import copy
import multiprocessing as mp
from grass.pygrass.modules import Module, ParallelModuleQueue

#%option G_OPT_R_INPUTS
#% key: elevation
#% label: DEM Raster Input
#% description: GRASS raster elevation map
#%end

#%option
#% key: size
#% type: integer
#% label: Size of neighbourhood
#% description: Size of neighbourhood to calculate the vector dispersion over. Multiple sizes are accepted to more efficiently calculate the VRM over different scales.
#% answer: 3
#% multiple: yes
#% guisection: Required
#%end

#%option G_OPT_R_OUTPUTS
#% key: output
#% label: Vector Ruggedness Measure Output
#%end

#%option G_OPT_R_INPUT
#% label: Optional slope raster map
#% description: Optional slope raster map. If not supplied, then a slope map will be calculated internally.
#% key: slope
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_R_INPUT
#% label: Optional aspect raster map
#% description: Optional aspect raster map. If not supplied, then an aspect map will be calculated internally.
#% key: aspect
#% required: no
#% guisection: Optional
#%end

#%option
#% key: nprocs
#% type: integer
#% label: The maximum number of cores to use for multiprocessing
#% description: The maximum number of cores to use for multiprocessing. -1 uses all cores, -2 uses n_cores-1 etc.
#% answer: -1
#% guisection: Optional
#%end


tmp_rast = []


def cleanup():
    for rast in tmp_rast:
        grass.run_command("g.remove", name=rast, type="raster", flags="fb", quiet=True)


def create_tempname(prefix):
    name = prefix + "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(8)]
    )
    tmp_rast.append(name)

    return name


def main():
    # user specified variables
    dem = options["elevation"]
    slope = options["slope"]
    aspect = options["aspect"]
    neighborhood_size = options["size"]
    output = options["output"]
    nprocs = int(options["nprocs"])

    # check for valid neighborhood sizes
    neighborhood_size = neighborhood_size.split(",")
    neighborhood_size = [int(i) for i in neighborhood_size]

    if any([True for i in neighborhood_size if i % 2 == 0]):
        grass.fatal("Invalid size - neighborhood sizes have to consist of odd numbers")

    if min(neighborhood_size) == 1:
        grass.fatal("Neighborhood sizes have to be > 1")

    # determine nprocs
    if nprocs < 0:
        n_cores = mp.cpu_count()
        nprocs = n_cores - (nprocs + 1)

    # temporary raster map names for slope, aspect, x, y, z components
    if slope == "":
        slope_raster = create_tempname("tmpSlope_")
    else:
        slope_raster = slope

    if aspect == "":
        aspect_raster = create_tempname("tmpAspect_")
    else:
        aspect_raster = aspect

    z_raster = create_tempname("tmpzRaster_")
    x_raster = create_tempname("tmpxRaster_")
    y_raster = create_tempname("tmpyRaster_")

    # create slope and aspect rasters
    if slope == "" or aspect == "":
        grass.message("Calculating slope and aspect...")
        grass.run_command(
            "r.slope.aspect",
            elevation=dem,
            slope=slope_raster,
            aspect=aspect_raster,
            format="degrees",
            precision="FCELL",
            zscale=1.0,
            min_slope=0.0,
            quiet=True,
        )

    # calculate x y and z rasters
    # note - GRASS sin/cos functions differ from ArcGIS which expects input grid in radians
    # whereas GRASS functions expect degrees
    # no need to convert slope and aspect to radians as in the original ArcGIS script
    x_expr = "{x} = float( sin({a}) * sin({b}) )".format(
        x=x_raster, a=aspect_raster, b=slope_raster
    )

    y_expr = "{y} = float( cos({a}) * sin({b}) )".format(
        y=y_raster, a=aspect_raster, b=slope_raster
    )

    z_expr = "{z} = float( cos({a}) )".format(
        z=z_raster,
        a=slope_raster
    )

    # calculate x, y, z components (parallel)
    grass.message("Calculating x, y, and z rasters...")

    mapcalc = Module("r.mapcalc", run_=False)
    queue = ParallelModuleQueue(nprocs=nprocs)

    mapcalc1 = copy.deepcopy(mapcalc)
    m = mapcalc1(expression=x_expr)
    queue.put(m)

    mapcalc2 = copy.deepcopy(mapcalc)
    m = mapcalc2(expression=y_expr)
    queue.put(m)

    mapcalc3 = copy.deepcopy(mapcalc)
    m = mapcalc3(expression=z_expr)
    queue.put(m)

    queue.wait()

    # calculate x, y, z neighborhood sums (parallel)
    grass.message(
        "Calculating sums of x, y, and z rasters in selected neighborhoods..."
    )

    x_sum_list = []
    y_sum_list = []
    z_sum_list = []

    neighbors = Module("r.neighbors", overwrite=True, run_=False)
    queue = ParallelModuleQueue(nprocs=nprocs)

    for size in neighborhood_size:
        # create temporary raster names for neighborhood x, y, z sums
        x_sum_raster = create_tempname("tmpxSumRaster_")
        x_sum_list.append(x_sum_raster)

        y_sum_raster = create_tempname("tmpySumRaster_")
        y_sum_list.append(y_sum_raster)

        z_sum_raster = create_tempname("tmpzSumRaster_")
        z_sum_list.append(z_sum_raster)

        # queue jobs for x, y, z neighborhood sums
        neighbors_xsum = copy.deepcopy(neighbors)
        n = neighbors_xsum(
            input=x_raster, output=x_sum_raster, method="average", size=size
        )
        queue.put(n)

        neighbors_ysum = copy.deepcopy(neighbors)
        n = neighbors_ysum(
            input=y_raster, output=y_sum_raster, method="average", size=size
        )
        queue.put(n)

        neighbors_zsum = copy.deepcopy(neighbors)
        n = neighbors_zsum(
            input=z_raster, output=z_sum_raster, method="average", size=size
        )
        queue.put(n)

    queue.wait()

    # calculate the resultant vector and final ruggedness raster
    # modified from the original script to multiple each SumRaster by the n neighborhood cells to get the sum
    grass.message("Calculating the final ruggedness rasters...")

    mapcalc = Module("r.mapcalc", run_=False)
    queue = ParallelModuleQueue(nprocs=nprocs)
    vrm_list = []

    for x_sum_raster, y_sum_raster, z_sum_raster, size in zip(
        x_sum_list, y_sum_list, z_sum_list, neighborhood_size
    ):

        if len(neighborhood_size) > 1:
            vrm_name = "_".join([output, str(size)])
        else:
            vrm_name = output

        vrm_list.append(vrm_name)

        vrm_expr = "{x} = float(1-( (sqrt(({a}*{d})^2 + ({b}*{d})^2 + ({c}*{d})^2) / {d})))".format(
            x=vrm_name,
            a=x_sum_raster,
            b=y_sum_raster,
            c=z_sum_raster,
            d=int(size) * int(size),
        )
        mapcalc1 = copy.deepcopy(mapcalc)
        m = mapcalc1(expression=vrm_expr)
        queue.put(m)

    queue.wait()

    # set colors
    grass.run_command("r.colors", flags="e", map=vrm_list, color="ryb")

    # set metadata
    for vrm, size in zip(vrm_list, neighborhood_size):
        title = "Vector Ruggedness Measure (size={size})".format(size=size)
        grass.run_command("r.support", map=vrm, title=title)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
