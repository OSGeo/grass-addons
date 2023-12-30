#!/usr/bin/env python


################################################
#
# MODULE:       t.rast.kappa
# AUTHOR(S):    Luca Delucchi
# PURPOSE:      t.rast.kappa calculate kappa parameter for accuracy
#               assessment in a space time raster dataset
#
# COPYRIGHT:        (C) 2017 by Luca Delucchi
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
################################################

# %module
# % description: Calculate kappa parameter in a space time raster dataset
# % keyword: temporal
# % keyword: raster
# % keyword: statistics
# %end

# %flag
# % key: k
# % description: Use r.kappa module instead SciKit-Learn Laboratory metrics.kappa
# %end

# %flag
# % key: l
# % label: Use memory swap
# % guisection: Optional
# %end

# %flag
# % key: p
# % label: Pixel by pixel analysis along different years
# % guisection: Optional
# %end

# %option G_OPT_STRDS_INPUT
# % key: strds
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# % description: Name for the output file or "-" in case stdout should be used
# % answer: -
# %end

# %option
# % key: weight
# % type: string
# % label: Specifies the weight matrix for the calculation
# % multiple: no
# % required: no
# % options: linear, quadratic
# %end

# %option G_OPT_T_WHERE
# %end

# %option
# % key: splittingday
# % type: string
# % label: Specifies the day to split the space time raster dataset in two groups, isotime format
# % multiple: no
# % required: no
# %end

# %option G_OPT_F_SEP
# %end

import sys
import grass.script as gscript
import grass.temporal as tgis
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.script.utils import separator

try:
    from collections import OrderedDict
except:
    from types import DictType as OrderedDic
import numpy as np


def _load_skll():
    try:
        from sklearn.metrics import cohen_kappa_score

        return False
    except ImportError:
        gscript.warning(_(""))
        return True


def _split_maps(maps, splitting):
    from datetime import datetime

    before = OrderedDic()
    after = OrderedDic()
    split = None
    if splitting.count("T") == 0:
        try:
            split = datetime.strptime(splitting, "%Y-%m-%d")
        except ValueError:
            pass
    else:
        try:
            split = datetime.strptime(splitting, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass
    if not split:
        gscript.fatal(
            _(
                "It is not possible to parse splittingday value. "
                "Please you one of the two supported format: "
                "'%Y-%m-%d' or '%Y-%m-%dT%H:%M:%S'"
            )
        )
    for mapp in maps:
        tempext = mapp.get_temporal_extent()
        raster = RasterRow(mapp.get_name())
        raster.open("r")
        array = np.array(raster)
        if tempext.start_time <= split:
            before[mapp.get_name()] = array
        else:
            after[mapp.get_name()] = array
    return before, after


def _kappa_pixel(maps1, maps2, out, method, over):
    from grass.pygrass.raster.buffer import Buffer
    import sklearn

    rasterout = RasterRow(out, overwrite=over)
    rasterout.open("w", "DCELL")
    array1 = maps1.values()[0]
    for row in range(len(array1)):
        newrow = Buffer((len(array1[row]),), mtype="DCELL")
        for col in range(len(array1[row])):
            vals1 = np.ndarray(len(maps1.values()))
            vals2 = np.ndarray(len(maps2.values()))
            x = 0
            for value in maps1.values():
                vals1[x] = value[row][col]
                x += 1
            x = 0
            for value in maps2.values():
                vals2[x] = value[row][col]
                x += 1
            if sklearn.__version__ >= "0.18":
                outval = sklearn.metrics.cohen_kappa_score(vals1, vals2, weights=method)
            else:
                outval = sklearn.metrics.cohen_kappa_score(vals1, vals2)
            newrow[col] = outval
        rasterout.put_row(newrow)
    rasterout.close()
    return


def _kappa_skll(map1, map2, lowmem, method):
    import sklearn

    raster1 = RasterRow(map1)
    raster2 = RasterRow(map2)
    raster1.open("r")
    raster2.open("r")
    if lowmem is False:
        array1 = np.array(raster1).reshape(-1)
        array2 = np.array(raster2).reshape(-1)
    else:
        import tempfile

        current = Region()
        array1 = np.memmap(
            tempfile.NamedTemporaryFile(),
            dtype="float32",
            mode="w+",
            shape=(current.rows, current.cols),
        )
        array1[:] = np.array(raster1).reshape(-1)
        array2 = np.memmap(
            tempfile.NamedTemporaryFile(),
            dtype="float32",
            mode="w+",
            shape=(current.rows, current.cols),
        )
        array2[:] = np.array(raster2).reshape(-1)
    raster1.close()
    raster2.close()
    if sklearn.__version__ >= "0.18":
        return sklearn.metrics.cohen_kappa_score(array1, array2, weights=method)
    else:
        return sklearn.metrics.cohen_kappa_score(array1, array2)


def _kappa_grass(map1, map2):
    return gscript.read_command(
        "r.kappa", classification=map1, reference=map2, quiet=True
    )


def main():
    strds = options["strds"]
    out_name = options["output"]
    if options["weight"] == "":
        method = None
    else:
        method = options["weight"]
    where = options["where"]
    sep = separator(options["separator"])
    if flags["p"] and not options["splittingday"]:
        gscript.fatal(_("'p' flag required to set also 'splittingday' option"))
    elif flags["p"] and options["splittingday"] and out_name == "-":
        gscript.fatal(_("'output' option is required with 'p' flag"))

    if flags["k"] and flags["p"]:
        gscript.fatal(_("It is not possible to use 'k' and 'p' flag together"))
    elif flags["k"] and not method:
        rkappa = True
    elif flags["k"] and method:
        gscript.message(
            _("If method is different from 'no' it is not possible" " to use r.kappa")
        )
        rkappa = _load_skll()
    else:
        rkappa = _load_skll()

    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    sp = tgis.open_old_stds(strds, "strds", dbif)
    maps = sp.get_registered_maps_as_objects(where, "start_time", None)
    if maps is None:
        gscript.fatal(
            _("Space time raster dataset {st} seems to be " "empty".format(st=strds))
        )
        return 1

    if flags["p"]:
        before, after = _split_maps(maps, options["splittingday"])
        _kappa_pixel(before, after, out_name, method, gscript.overwrite())
        return

    mapnames = [mapp.get_name() for mapp in maps]
    if not rkappa:
        if out_name != "-":
            fi = open(out_name, "w")
        else:
            fi = sys.stdout
    for i1 in range(len(mapnames)):
        for i2 in range(i1 + 1, len(mapnames)):
            map1 = mapnames[i1]
            map2 = mapnames[i2]
            if map1 != map2:
                if not rkappa:
                    fi.write(
                        "{}-{}{}{}\n".format(
                            map1, map2, sep, _kappa_skll(map1, map2, flags["l"], method)
                        )
                    )
                else:
                    if out_name != "-":
                        fi = open("{}_{}_{}".format(out_name, map1, map2), "w")
                    else:
                        fi = sys.stdout
                    fi.write("{}".format(_kappa_grass(map1, map2)))
                    if out_name != "-":
                        fi.close()
    if not rkappa:
        fi.close()

    gscript.message(_("All data have analyzed"))


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
