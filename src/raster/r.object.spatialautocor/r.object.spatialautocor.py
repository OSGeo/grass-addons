#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.object.spatialautocor
# AUTHOR(S):    Moritz Lennert
#
# PURPOSE:      Calculates global spatial autocorrelation on raster objects
# COPYRIGHT:    (C) 1997-2017 by the GRASS Development Team
#
#       This program is free software under the GNU General Public
#       License (>=v2). Read the file COPYING that comes with GRASS
#       for details.
#
#############################################################################
# References:
#
# Moran, P.A.P., 1950. Notes on Continuous Stochastic Phenomena. Biometrika 37,
# 17-23. https://dx.doi.org/10.2307%2F2332142
# Geary, R.C., 1954. The Contiguity Ratio and Statistical Mapping. The
# Incorporated Statistician 5, 115. https://dx.doi.org/10.2307%2F2986645
#############################################################################

# %Module
# % description: Spatial autocorrelation of raster objects
# % keyword: raster
# % keyword: statistics
# % keyword: spatial autocorrelation
# %end
#
# %option G_OPT_R_INPUT
# % key: object_map
# % description: Raster input map with objects
# % required : yes
# %end
#
# %option G_OPT_R_INPUT
# % key: variable_map
# % description: Raster input map with variable
# % required : yes
# %end
#
# %option
# % key: method
# % type: string
# % description: Method for spatial autocorrelation
# % options: moran,geary
# % multiple: no
# % required: yes
# %end
#
# %flag
# % key: d
# % description: Also take into account diagonal neighbors
# %end

from __future__ import print_function
import sys
import grass.script as gscript

# check requirements
def check_progs():
    found_missing = False
    for prog in ["r.neighborhoodmatrix"]:
        if not gscript.find_program(prog, "--help"):
            found_missing = True
            gscript.warning(
                _("'%s' required. Please install '%s' first using 'g.extension %s'")
                % (prog, prog, prog)
            )
    if found_missing:
        gscript.fatal(_("An ERROR occurred running i.segment.uspo"))


def get_nb_matrix(mapname, diagonal):
    """Create a dictionary with neighbors per segment"""

    if diagonal:
        res = gscript.read_command(
            "r.neighborhoodmatrix",
            input_=mapname,
            output="-",
            sep="comma",
            flags="d",
            quiet=True,
        )
    else:
        res = gscript.read_command(
            "r.neighborhoodmatrix", input_=mapname, output="-", sep="comma", quiet=True
        )

    neighbordict = {}
    for line in res.splitlines():
        n1 = line.split(",")[0]
        n2 = line.split(",")[1]
        if n1 in neighbordict:
            neighbordict[n1].append(n2)
        else:
            neighbordict[n1] = [n2]

    return neighbordict


def get_autocorrelation(mapname, raster, neighbordict, method):
    """Calculate either Moran's I or Geary's C for values of the given raster"""

    raster_vars = gscript.parse_command("r.univar", map_=raster, flags="g", quiet=True)
    global_mean = float(raster_vars["mean"])

    univar_res = gscript.read_command(
        "r.univar",
        flags="t",
        map_=raster,
        zones=mapname,
        out="-",
        sep="comma",
        quiet=True,
    )

    means = {}
    mean_diffs = {}
    firstline = True
    for line in univar_res.splitlines():
        l = line.split(",")
        if firstline:
            i = l.index("mean")
            firstline = False
        else:
            means[l[0]] = float(l[i])
            mean_diffs[l[0]] = float(l[i]) - global_mean

    sum_sq_mean_diffs = sum(x ** 2 for x in mean_diffs.values())

    total_nb_neighbors = 0
    for region in neighbordict:
        total_nb_neighbors += len(neighbordict[region])

    N = len(means)
    sum_products = 0
    sum_squared_differences = 0
    for region in neighbordict:
        region_value = means[region] - global_mean
        neighbors = neighbordict[region]
        nb_neighbors = len(neighbors)
        for neighbor in neighbors:
            neighbor_value = means[neighbor] - global_mean
            sum_products += region_value * neighbor_value
            sum_squared_differences = (means[region] - means[neighbor]) ** 2

    if method == "moran":
        autocor = (float(N) / total_nb_neighbors) * (
            float(sum_products) / sum_sq_mean_diffs
        )
    elif method == "geary":
        autocor = (float(N - 1) / (2 * total_nb_neighbors)) * (
            float(sum_squared_differences) / sum_sq_mean_diffs
        )

    return autocor


def main():

    check_progs()

    object_map = options["object_map"]
    variable_map = options["variable_map"]
    method = options["method"]
    diagonal = flags["d"]

    nb_matrix = get_nb_matrix(object_map, diagonal)
    autocor = get_autocorrelation(object_map, variable_map, nb_matrix, method)
    print("%.7f" % autocor)


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
