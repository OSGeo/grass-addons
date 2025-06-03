#!/usr/bin/env python

##############################################################################
# MODULE:    r.gravity.terrain
#
# AUTHOR(S): David Farris <farrisd19@ecu.edu>
#
# PURPOSE:   A GRASS tool to calculate gravity terrain corrections
#
# COPYRIGHT: (C) 2025 by David Farris and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""A GRASS tool to calculate gravity terrain corrections"""

# %module
# % description: A GRASS tool to calculate gravity terrain corrections
# % keyword: raster
# % keyword: algebra
# % keyword: random
# %end
# %option G_OPT_R_ELEV
# %end
# %option G_OPT_V_INPUT
# % key: points
# % description: Input vector map of points containing the gravity stations
# %end
# %option G_OPT_F_OUTPUT
# %end
# %option
# % key: minimum_distance
# % type: double
# % required: yes
# % multiple: no
# % description: Minimum distance from gravity station to calculate terrain correction
# %end
# %option
# % key: maximum_distance
# % type: double
# % required: yes
# % multiple: no
# % description: Maximum distance from gravity station to calculate terrain correction
# %end
# %option
# % key: crustal_density
# % type: double
# % required: yes
# % multiple: no
# % answer: 2670
# % description: Crustal density in kg/m^3 used in the terrain correction (e.g.2670 kg/m^3)
# %end
# %option G_OPT_M_NPROCS
# %end

import sys
import atexit
from multiprocessing import Pool
import grass.script as gs


def clean(name):
    gs.run_command(
        "g.remove", type="raster", pattern=f"{name}_*", flags="f", superquiet=True
    )


def correction(
    point,
    minimum_distance,
    maximum_distance,
    elevation,
    temporary_basename,
    crustal_density,
):
    x, y, z, cat = point.split(",")
    gs.mapcalc(
        f"{temporary_basename}_{cat} = eval(dist = sqrt(((x() - {x}) * (x() - {x})) + ((y() - {y}) * (y() - {y}))), "
        f"dz = abs({elevation} - {z}), "
        f"d_prime = sqrt(dist * dist + dz * dz), "
        f"if(dist >= {minimum_distance} && dist < {maximum_distance}, 100000 * (0.000000000066743) * {crustal_density} * area() * ((1 / dist)-(1 / d_prime)), 0))"
    )

    # Calculate total terrain correction. Use cat here!
    return (
        cat,
        gs.parse_command("r.univar", map=f"{temporary_basename}_{cat}", flags="g")[
            "sum"
        ],
    )


def main():
    # get input options
    options, flags = gs.parser()
    elevation = options["elevation"]
    points = options["points"]
    output = options["output"]
    minimum_distance = options["minimum_distance"]
    maximum_distance = options["maximum_distance"]
    crustal_density = options["crustal_density"]
    n_processes = int(options["nprocs"])

    info = gs.vector_info_topo(points)
    if not info["map3d"]:
        gs.fatal(_("Input vector map is not 3D"))
    if not info["points"]:
        gs.fatal(_("Input vector map does not contain points"))

    points = gs.read_command(
        "v.out.ascii", input=points, format="point", separator="comma"
    ).splitlines()

    temporary_basename = gs.append_node_pid("r.gravity.terrain")
    atexit.register(clean, temporary_basename)

    args = [
        (
            point,
            minimum_distance,
            maximum_distance,
            elevation,
            temporary_basename,
            crustal_density,
        )
        for point in points
    ]
    with Pool(processes=n_processes) as pool:
        results = pool.starmap(correction, args)

    with open(output, "w") as f:
        f.write("category,correction\n")
        for result in results:
            f.write(f"{result[0]},{result[1]}\n")


if __name__ == "__main__":
    sys.exit(main())
