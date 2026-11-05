#!/usr/bin/env python
############################################################################
#
# MODULE:       v.flexure
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Calculate flexure of the lithosphere under a specified
#               set of loads and with a given elastic thickness (scalar)
#
# COPYRIGHT:    (c) 2014, 2015, 2026 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  gFlex: https://github.com/awickert/gFlex

# More information
# Started 20 Jan 2015 to add GRASS GIS support for distributed point loads
# and their effects on lithospheric flexure

# %module
# % description: Lithospheric flexure: gridded deflections from scattered point loads
# % keyword: vector
# % keyword: geophysics
# %end

# %option G_OPT_V_INPUT
# %  key: input
# %  description: Vector map of loads (thickness * area * density * g) [N]
# %  guidependency: layer,column
# %end

# %option G_OPT_V_FIELD
# %  key: layer
# %  description: Layer containing load values
# %  guidependency: column
# %end

# %option G_OPT_DB_COLUMN
# %  key: column
# %  description: Column containing load values [N]
# %  required : yes
# %end

# %option
# %  key: te
# %  type: double
# %  description: Elastic thickness: scalar; units chosen in "te_units"
# %  required : yes
# %end

# %option
# %  key: te_units
# %  type: string
# %  description: Units for elastic thickness
# %  options: m, km
# %  answer: km
# %  required : no
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  description: Output raster map of vertical deflections [m]
# %  required : yes
# %end

# %option G_OPT_V_MAP
# %  key: w_points
# %  description: Existing vector points map to receive deflection values
# %  required : no
# %  guisection: Output
# %end

# %option G_OPT_DB_COLUMN
# %  key: w_column
# %  description: Column in w_points map to write deflection values [m]
# %  answer: w
# %  required : no
# %  guisection: Output
# %end

# %option
# %  key: g
# %  type: double
# %  description: gravitational acceleration at surface [m/s^2]
# %  answer: 9.8
# %  required : no
# %  guisection: Material properties
# %end

# %option
# %  key: ym
# %  type: double
# %  description: Young's Modulus [Pa]
# %  answer: 65E9
# %  required : no
# %  guisection: Material properties
# %end

# %option
# %  key: nu
# %  type: double
# %  description: Poisson's ratio
# %  answer: 0.25
# %  required : no
# %  guisection: Material properties
# %end

# %option
# %  key: rho_fill
# %  type: double
# %  description: Density of material that fills flexural depressions [kg/m^3]
# %  answer: 0
# %  required : no
# %  guisection: Material properties
# %end

# %option
# %  key: rho_m
# %  type: double
# %  description: Mantle density [kg/m^3]
# %  answer: 3300
# %  required : no
# %  guisection: Material properties
# %end


##################
# IMPORT MODULES #
##################

# PYTHON
import os
import tempfile
import warnings

import numpy as np

# GRASS
import grass.script as gs


####################
# UTILITY FUNCTION #
####################


def get_points_xy(vect_name):
    """Return (x, y) coordinate arrays for all points in a vector map."""
    out = gs.read_command(
        "v.out.ascii", input=vect_name, format="point", separator="space", quiet=True
    )
    rows = [line.split() for line in out.strip().splitlines() if line.strip()]
    if not rows:
        return np.array([]), np.array([])
    coords = np.array([[float(r[0]), float(r[1])] for r in rows], dtype=float)
    return coords[:, 0], coords[:, 1]  # x, y


############################
# PASS VARIABLES AND SOLVE #
############################


def main():
    """
    Superposition of analytical solutions in gFlex for flexural isostasy in
    GRASS GIS
    """

    options, flags = gs.parser()
    # if just interface description is requested, it will not get to this point
    # so gflex will not be needed

    # Import gFlex only after we know we will actually do the computation
    try:
        # cmcrameri is an optional plotting dependency; GRASS never uses
        # gFlex's plots, so suppress the missing-package warning at import.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="cmcrameri is not installed", category=UserWarning
            )
            import gflex
    except ImportError:
        gs.fatal(
            _(
                "Cannot import gFlex. Install it from source with:\n"
                "  pip install -e /path/to/gFlex\n"
                "or see https://github.com/awickert/gFlex for details."
            )
        )

    _gver = tuple(
        int(x.split("a")[0].split("b")[0].split("rc")[0])
        for x in gflex.__version__.split(".")[:3]
    )
    if _gver < (2, 0, 0):
        gs.fatal(
            _("v.flexure requires gFlex >= 2.0.0; installed: ") + gflex.__version__
        )

    ##########
    # SET-UP #
    ##########

    # This code is for 2D flexural isostasy
    flex = gflex.F2D()
    # And show that it is coming from GRASS GIS
    flex.grass = True

    # Method
    flex.method = "sas_ng"

    # Parameters that are often changed for the solution
    ######################################################

    # x, y, q — load point coordinates and magnitudes
    flex.x, flex.y = get_points_xy(options["input"])
    if len(flex.x) == 0:
        gs.fatal(_("Input vector map <%s> contains no points.") % options["input"])
    vect_db = gs.vector_db_select(options["input"])
    col_names = np.array(vect_db["columns"])
    q_col = col_names == options["column"]
    if np.sum(q_col):
        col_values = np.array(list(vect_db["values"].values())).astype(float)
        flex.q = col_values[:, q_col].reshape(-1)  # always 1-D, even for a single point
    else:
        gs.fatal(
            _("Column <%s> not found in vector map <%s>.")
            % (options["column"], options["input"])
        )

    # Overwrite check for raster output
    if len(gs.parse_command("g.list", type="rast", pattern=options["output"])):
        if not gs.overwrite():
            gs.fatal(
                _("Raster map <%s> already exists. Use '--o' to overwrite.")
                % options["output"]
            )

    # Build the output coordinate arrays.
    # The raster grid is always needed; w_points coordinates (if provided) are
    # appended so both are evaluated in a single gFlex solve.
    _tmp_vect = "tmp_vflex_{}".format(os.getpid())
    gs.run_command("v.mkgrid", map=_tmp_vect, type="point", overwrite=True, quiet=True)
    gs.run_command(
        "v.db.addcolumn", map=_tmp_vect, columns="w double precision", quiet=True
    )
    grid_x, grid_y = get_points_xy(_tmp_vect)
    n_grid = len(grid_x)

    if options["w_points"]:
        pts_x, pts_y = get_points_xy(options["w_points"])
        flex.xw = np.concatenate([grid_x, pts_x])
        flex.yw = np.concatenate([grid_y, pts_y])
    else:
        flex.xw = grid_x
        flex.yw = grid_y
    # Elastic thickness
    flex.T_e = float(options["te"])
    if options["te_units"] == "km":
        flex.T_e *= 1000
    elif options["te_units"] == "m":
        pass
    else:
        gs.fatal(_("Inappropriate te_units; this should not be reachable."))
    flex.rho_fill = float(options["rho_fill"])

    # Parameters that often stay at their default values
    ######################################################
    flex.g = float(options["g"])
    flex.E = float(
        options["ym"]
    )  # Can't just use "E" because reserved for "east", I think
    flex.nu = float(options["nu"])
    flex.rho_m = float(options["rho_m"])

    # gFlex defaults to quiet (WARNING log level); opt in at --verbose (level 3).
    if gs.verbosity() >= 3:
        flex.verbose = True
        flex.quiet = False

    # Check if lat/lon and let user know if verbosity is True
    if gs.region_env()[6] == "3":
        flex.latlon = True
        flex.planetary_radius = float(gs.parse_command("g.proj", flags="j")["+a"])
        if flex.verbose:
            gs.message(_("Latitude/longitude grid."))
            gs.message(_("Based on r_Earth = 6371 km"))
            gs.message(
                _("Computing distances between load points using great circle paths")
            )

    ##########
    # SOLVE! #
    ##########

    gs.message(_("Computing deflections..."))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        flex.initialize()
        flex.run()
        # finalize() deletes flex.w in gFlex v2, so capture it first
        w_out = np.array(flex.w)
        flex.finalize()
    for warninfo in caught:
        gs.warning(str(warninfo.message))

    # Split results: first n_grid values go to the raster grid
    w_grid = w_out[:n_grid]

    # Write grid deflections to the temporary vector, then rasterise
    # v.mkgrid assigns sequential cats (1, 2, ...) in row-major order
    sql_lines = [
        "UPDATE {t} SET w = {val} WHERE cat = {cat};".format(
            t=_tmp_vect, val=float(w_grid[i]), cat=i + 1
        )
        for i in range(n_grid)
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write("\n".join(sql_lines))
        sql_file = f.name
    try:
        gs.run_command("db.execute", input=sql_file, quiet=True)
    finally:
        os.unlink(sql_file)
    gs.run_command("v.build", map=_tmp_vect, quiet=True)

    # Raster output (primary, required)
    gs.run_command(
        "v.to.rast",
        input=_tmp_vect,
        output=options["output"],
        use="attr",
        attribute_column="w",
        type="point",
        overwrite=gs.overwrite(),
        quiet=True,
    )
    gs.run_command("r.colors", map=options["output"], color="differences", quiet=True)
    gs.run_command("g.remove", flags="f", type="vector", name=_tmp_vect, quiet=True)

    # Write deflection values to the user-supplied w_points map
    if options["w_points"]:
        w_pts = w_out[n_grid:]
        col = options["w_column"]
        # Add column if it does not already exist
        existing_cols = [
            c.lower() for c in gs.vector_db_select(options["w_points"])["columns"]
        ]
        if col.lower() not in existing_cols:
            gs.run_command(
                "v.db.addcolumn",
                map=options["w_points"],
                columns="{} double precision".format(col),
                quiet=True,
            )
        pts_cats = list(gs.vector_db_select(options["w_points"])["values"].keys())
        sql_lines = [
            "UPDATE {t} SET {col} = {val} WHERE cat = {cat};".format(
                t=options["w_points"].split("@")[0],
                col=col,
                val=float(w_pts[i]),
                cat=pts_cats[i],
            )
            for i in range(len(w_pts))
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write("\n".join(sql_lines))
            sql_file = f.name
        try:
            gs.run_command("db.execute", input=sql_file, quiet=True)
        finally:
            os.unlink(sql_file)
        gs.run_command("v.build", map=options["w_points"], quiet=True)


if __name__ == "__main__":
    main()
