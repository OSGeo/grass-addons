#!/usr/bin/env python
############################################################################
#
# MODULE:       v.stream.profiler
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Build long profiles and slope--area diagrams of a river network
#
# COPYRIGHT:    (c) 2016-2018 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  uses inputs from r.stream.extract

# More information
# Started 14 October 2016
#%module
#% description: Build a linked stream network: each link knows its downstream link
#% keyword: vector
#% keyword: stream network
#% keyword: hydrology
#% keyword: geomorphology
#%end
#%option
#%  key: cat
#%  label: Starting line segment category
#%  required: yes
#%  guidependency: layer,column
#%end
#%option G_OPT_V_INPUT
#%  key: streams
#%  label: Vector input of stream network created by r.stream.extract
#%  required: yes
#%end
#%option G_OPT_V_OUTPUT
#%  key: outstream
#%  label: Vector output stream
#%  required: no
#%end
#%option
#%  key: direction
#%  type: string
#%  label: Which directon to march: up or down
#%  options: upstream,downstream
#%  answer: downstream
#%  required: no
#%end
#%option G_OPT_R_INPUT
#%  key: elevation
#%  label: Topography (DEM)
#%  required: no
#%end
#%option G_OPT_R_INPUT
#%  key: accumulation
#%  label: Flow accumulation raster
#%  required: no
#%end
#%option G_OPT_R_INPUT
#%  key: slope
#%  label: Map of slope created by r.slope.area
#%  required: no
#%end
#%option
#%  key: units
#%  type: string
#%  label: Flow accumulation units
#%  options: m2, km2, cumecs, cfs
#%  required: no
#%end
#%option
#%  key: accum_mult
#%  type: double
#%  label: Multiplier to convert flow accumulation to your chosen unit
#%  answer: 1
#%  required: no
#%end
#%option G_OPT_R_INPUT
#%  key: window
#%  label: Averaging distance [map units]
#%  required: no
#%end
#%option
#%  key: plots
#%  type: string
#%  label: Plots to generate
#%  options: LongProfile,SlopeAccum,SlopeDistance,AccumDistance
#%  required: no
#%  multiple: yes
#%end
#%option
#%  key: outfile_original
#%  type: string
#%  label: output file for data on original grid
#%  required: no
#%end
#%option
#%  key: outfile_smoothed
#%  type: string
#%  label: output file for data on smoothed grid
#%  required: no
#%end

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np
import sys

# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.gis import region
from grass.pygrass import vector  # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript
from grass.pygrass.vector.geometry import Point

###################
# UTILITY MODULES #
###################


def moving_average(x, y, window):
    """
    Create a moving average every <window/2> points with an averaging
    distance of <window>, but including the the first point + window/2
    and the last point - window/2
    (so distance to last point could be irregular)
    """
    x = np.array(x)
    y = np.array(y)
    out_x = np.arange(x[0] + window / 2.0, x[-1] - window / 2.0, window)
    out_x = np.hstack((out_x, x[-1] - window / 2.0))
    out_y = []
    for _x in out_x:
        out_y.append(np.mean(y[(x < _x + window / 2.0) * (x > _x - window / 2.0)]))
    return out_x, out_y


###############
# MAIN MODULE #
###############


def main():
    """
    Links each river segment to the next downstream segment in a tributary
    network by referencing its category (cat) number in a new column. "0"
    means that the river exits the map.
    """
    try:
        import matplotlib

        matplotlib.use("WXAgg")
        from matplotlib import pyplot as plt
    except ImportError as e:
        raise ImportError(
            _(
                'v.stream.profiler needs the "matplotlib" '
                "(python-matplotlib) package to be installed. {0}"
            ).format(e)
        )

    options, flags = gscript.parser()

    # Parsing
    window = float(options["window"])
    accum_mult = float(options["accum_mult"])
    if options["units"] == "m2":
        accum_label = "Drainage area [m$^2$]"
    elif options["units"] == "km2":
        accum_label = "Drainage area [km$^2$]"
    elif options["units"] == "cumecs":
        accum_label = "Water discharge [m$^3$ s$^{-1}$]"
    elif options["units"] == "cfs":
        accum_label = "Water discharge [cfs]"
    else:
        accum_label = "Flow accumulation [$-$]"
    plots = options["plots"].split(",")

    # Attributes of streams
    colNames = np.array(vector_db_select(options["streams"])["columns"])
    colValues = np.array(vector_db_select(options["streams"])["values"].values())
    tostream = colValues[:, colNames == "tostream"].astype(int).squeeze()
    cats = colValues[:, colNames == "cat"].astype(int).squeeze()  # = "fromstream"

    # We can loop over this list to get the shape of the full river network.
    selected_cats = []
    segment = int(options["cat"])
    selected_cats.append(segment)
    x = []
    z = []
    if options["direction"] == "downstream":
        # Get network
        gscript.message("Network")
        while selected_cats[-1] != 0:
            selected_cats.append(int(tostream[cats == selected_cats[-1]]))
        x.append(selected_cats[-1])
        selected_cats = selected_cats[:-1]  # remove 0 at end

        # Extract x points in network
        data = vector.VectorTopo(options["streams"])  # Create a VectorTopo object
        data.open("r")  # Open this object for reading

        coords = []
        _i = 0
        for i in range(len(data)):
            if isinstance(data.read(i + 1), vector.geometry.Line):
                if data.read(i + 1).cat in selected_cats:
                    coords.append(data.read(i + 1).to_array())
                    gscript.core.percent(
                        _i, len(selected_cats), 100.0 / len(selected_cats)
                    )
                    _i += 1
        gscript.core.percent(1, 1, 1)
        coords = np.vstack(np.array(coords))

        _dx = np.diff(coords[:, 0])
        _dy = np.diff(coords[:, 1])
        x_downstream_0 = np.hstack((0, np.cumsum((_dx ** 2 + _dy ** 2) ** 0.5)))
        x_downstream = x_downstream_0.copy()

    elif options["direction"] == "upstream":
        # terminalCATS = list(options['cat'])
        # while terminalCATS:
        #
        print("Upstream direction not yet active!")
        return
        """
        # Add new lists for each successive upstream river
        river_is_upstream =
        while
        full_river_cats
        """

    # Network extraction
    if options["outstream"] is not "":
        selected_cats_str = list(np.array(selected_cats).astype(str))
        selected_cats_csv = ",".join(selected_cats_str)
        v.extract(
            input=options["streams"],
            output=options["outstream"],
            cats=selected_cats_csv,
            overwrite=gscript.overwrite(),
        )

    # Analysis
    gscript.message("Elevation")
    if options["elevation"]:
        _include_z = True
        DEM = RasterRow(options["elevation"])
        DEM.open("r")
        z = []
        _i = 0
        _lasti = 0
        for row in coords:
            z.append(DEM.get_value(Point(row[0], row[1])))
            if float(_i) / len(coords) > float(_lasti) / len(coords):
                gscript.core.percent(_i, len(coords), np.floor(_i - _lasti))
            _lasti = _i
            _i += 1
        DEM.close()
        z = np.array(z)
        if options["window"] is not "":
            x_downstream, z = moving_average(x_downstream_0, z, window)
        gscript.core.percent(1, 1, 1)
    else:
        _include_z = False
    gscript.message("Slope")
    if options["slope"]:
        _include_S = True
        slope = RasterRow(options["slope"])
        slope.open("r")
        S = []
        _i = 0
        _lasti = 0
        for row in coords:
            S.append(slope.get_value(Point(row[0], row[1])))
            if float(_i) / len(coords) > float(_lasti) / len(coords):
                gscript.core.percent(_i, len(coords), np.floor(_i - _lasti))
            _lasti = _i
            _i += 1
        slope.close()
        S = np.array(S)
        S_0 = S.copy()
        if options["window"] is not "":
            x_downstream, S = moving_average(x_downstream_0, S, window)
        gscript.core.percent(1, 1, 1)
    else:
        _include_S = False
    gscript.message("Accumulation")
    if options["accumulation"]:
        _include_A = True
        accumulation = RasterRow(options["accumulation"])
        accumulation.open("r")
        A = []
        _i = 0
        _lasti = 0
        for row in coords:
            A.append(accumulation.get_value(Point(row[0], row[1])) * accum_mult)
            if float(_i) / len(coords) > float(_lasti) / len(coords):
                gscript.core.percent(_i, len(coords), np.floor(_i - _lasti))
            _lasti = _i
            _i += 1
        accumulation.close()
        A = np.array(A)
        A_0 = A.copy()
        if options["window"] is not "":
            x_downstream, A = moving_average(x_downstream_0, A, window)
        gscript.core.percent(1, 1, 1)
    else:
        _include_A = False

    # Plotting
    if "LongProfile" in plots:
        plt.figure()
        plt.plot(x_downstream / 1000.0, z, "k-", linewidth=2)
        plt.xlabel("Distance downstream [km]", fontsize=16)
        plt.ylabel("Elevation [m]", fontsize=20)
        plt.tight_layout()
    if "SlopeAccum" in plots:
        plt.figure()
        plt.loglog(A, S, "ko", linewidth=2)
        plt.xlabel(accum_label, fontsize=20)
        plt.ylabel("Slope [$-$]", fontsize=20)
        plt.tight_layout()
    if "SlopeDistance" in plots:
        plt.figure()
        plt.plot(x_downstream / 1000.0, S, "k-", linewidth=2)
        plt.xlabel("Distance downstream [km]", fontsize=16)
        plt.ylabel("Slope [$-$]", fontsize=20)
        plt.tight_layout()
    if "AccumDistance" in plots:
        plt.figure()
        plt.plot(x_downstream / 1000.0, A, "k-", linewidth=2)
        plt.xlabel("Distance downstream [km]", fontsize=16)
        plt.ylabel(accum_label, fontsize=20)
        plt.tight_layout()
    plt.show()

    # Saving data
    if options["outfile_original"] is not "":
        header = ["x_downstream", "E", "N"]
        outfile = np.hstack((np.expand_dims(x_downstream_0, axis=1), coords))
        if _include_S:
            header.append("slope")
            outfile = np.hstack((outfile, np.expand_dims(S_0, axis=1)))
        if _include_A:
            if (options["units"] == "m2") or (options["units"] == "km2"):
                header.append("drainage_area_" + options["units"])
            elif (options["units"] == "cumecs") or (options["units"] == "cfs"):
                header.append("water_discharge_" + options["units"])
            else:
                header.append("flow_accumulation_arbitrary_units")
            outfile = np.hstack((outfile, np.expand_dims(A_0, axis=1)))
        header = np.array(header)
        outfile = np.vstack((header, outfile))
        np.savetxt(options["outfile_original"], outfile, "%s")
    if options["outfile_smoothed"] is not "":
        header = ["x_downstream", "E", "N"]
        # E, N on smoothed grid
        x_downstream, E = moving_average(x_downstream_0, coords[:, 0], window)
        x_downstream, N = moving_average(x_downstream_0, coords[:, 1], window)
        # Back to output
        outfile = np.hstack(
            (
                np.expand_dims(x_downstream, axis=1),
                np.expand_dims(E, axis=1),
                np.expand_dims(N, axis=1),
            )
        )
        if _include_S:
            header.append("slope")
            outfile = np.hstack((outfile, np.expand_dims(S, axis=1)))
        if _include_A:
            if (options["units"] == "m2") or (options["units"] == "km2"):
                header.append("drainage_area_" + options["units"])
            elif (options["units"] == "cumecs") or (options["units"] == "cfs"):
                header.append("water_discharge_" + options["units"])
            else:
                header.append("flow_accumulation_arbitrary_units")
            outfile = np.hstack((outfile, np.expand_dims(A, axis=1)))
        header = np.array(header)
        outfile = np.vstack((header, outfile))
        np.savetxt(options["outfile_smoothed"], outfile, "%s")


if __name__ == "__main__":
    main()
