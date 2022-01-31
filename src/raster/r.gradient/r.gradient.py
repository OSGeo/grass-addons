#!/usr/bin/env python


############################################################################
#
# MODULE:        r.gradient
# AUTHOR(S):     Luca Delucchi
# PURPOSE:       r.gradient create a gradient map
#
# COPYRIGHT:        (C) 2014 by Luca Delucchi
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Create a gradient map
# % keyword: raster
# % keyword: gradient
# %end

# %option G_OPT_R_OUTPUT
# %end

# %option
# % key: direction
# % type: string
# % label: The direction of gradient
# % options: N-S, S-N, W-E, E-W, NW-SE, NE-SW
# % required: yes
# %end
# %option
# % key: range
# % type: integer
# % label: Minimum and maximum values of gradient
# % required: yes
# % multiple: yes
# %end
# %option
# % key: percentile
# % type: double
# % label: Percentile to calculate (only for oblique gradient)
# % options: 0-100
# % required: no
# %end


# TODO add support for SW-NE, SE-NW direction

# import library
import sys
import grass.script as grass
from grass.pygrass.raster import RasterRow
from grass.pygrass.raster.buffer import Buffer


def calculateOblique(reg, mi, ma, perc):
    """Calculate the oblique gradient"""
    cols = reg["cols"]
    rows = reg["rows"]
    first_perc = ma * float(perc) / 100.0
    dif_cols_first = (first_perc - mi) / float(cols - 1)
    dif_rows_first = (first_perc - mi) / float(rows - 1)
    dif_rows_last = (ma - first_perc) / float(rows - 1)
    matrix = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if r == 0 and c == 0:
                row.append(mi)
            elif r == 0 and not c == 0:
                val = row[c - 1] + dif_cols_first
                row.append(val)
            elif c == 0 and not r == 0:
                val = matrix[r - 1][0] + dif_rows_first
                row.append(val)
            else:
                val = row[c - 1] + dif_rows_last
                row.append(val)
        matrix.append(row)
    return matrix


def createRast(name, matrix, inverse=False):
    """Create the new raster map using the output matrix of calculateOblique"""
    newscratch = RasterRow(name)
    newscratch.open("w", overwrite=True)
    try:
        for r in matrix:
            if inverse:
                r.reverse()
            newrow = Buffer((len(r),), mtype="FCELL")
            for c in range(len(r)):
                newrow[c] = r[c]
            newscratch.put_row(newrow)
        newscratch.close()
        return True
    except:
        return False


def checkPercentile(per, di):
    """Check if percentile option is set with the oblique directions"""
    if not per and di in ["NW-SE", "NE-SW", "SW-NE", "SE-NW"]:
        grass.fatal(
            "Percentile option has to be set with {dire} direction".format(dire=di)
        )


def main():
    """Main function"""
    regiondict = grass.region()

    output = options["output"]
    values = options["range"].split(",")
    NewMin = int(values[0].strip())
    NewMax = int(values[1].strip())
    percentile = options["percentile"]
    direction = options["direction"]

    checkPercentile(percentile, direction)
    # And now we can calculate the graded rasters
    # for gradient of rows
    if direction == "N-S":
        grass.mapcalc(
            "$newmap = (((row() - $OldMin) * ($NewMax - $NewMin)) / "
            "($OldMax - $OldMin)) + $NewMin",
            newmap=output,
            NewMin=NewMin,
            NewMax=NewMax,
            OldMin=1,
            OldMax=regiondict["rows"],
            overwrite=True,
        )
    elif direction == "S-N":
        grass.mapcalc(
            "$newmap = (((row() - $OldMin) * ($NewMax - $NewMin)) / "
            "($OldMax - $OldMin)) + $NewMin",
            newmap=output,
            NewMin=NewMax,
            NewMax=NewMin,
            OldMin=1,
            OldMax=regiondict["rows"],
            overwrite=True,
        )
    elif direction == "W-E":
        grass.mapcalc(
            "$newmap = (((col() - $OldMin) * ($NewMax - $NewMin)) / "
            "($OldMax - $OldMin)) + $NewMin",
            newmap=output,
            NewMin=NewMin,
            NewMax=NewMax,
            OldMin=1,
            OldMax=regiondict["cols"],
            overwrite=True,
        )
    elif direction == "E-W":
        grass.mapcalc(
            "$newmap = (((col() - $OldMin) * ($NewMax - $NewMin)) / "
            "($OldMax - $OldMin)) + $NewMin",
            newmap=output,
            NewMin=NewMax,
            NewMax=NewMin,
            OldMin=1,
            OldMax=regiondict["cols"],
            overwrite=True,
        )
    elif direction == "NW-SE":
        mat = calculateOblique(regiondict, NewMin, NewMax, percentile)
        createRast(output, mat)
    elif direction == "NE-SW":
        mat = calculateOblique(regiondict, NewMin, NewMax, percentile)
        createRast(output, mat, True)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
