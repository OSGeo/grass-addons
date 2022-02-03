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
# COPYRIGHT:    (c) 2014, 2015 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  gFlex: http://csdms.colorado.edu/wiki/gFlex
#         (should be downloaded automatically along with the module)
#         github repository: https://github.com/awickert/gFlex

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

# %option G_OPT_DB_COLUMNS
# %  key: column
# %  description: Column containing load values [N]
# %  required : yes
# %end

# %option
# %  key: te
# %  type: double
# %  description: Elastic thicnkess: scalar; unis chosen in "te_units"
# %  required : yes
# %end

# %option
# %  key: te_units
# %  type: string
# %  description: Units for elastic thickness
# %  options: m, km
# %  required : yes
# %end

# %option G_OPT_V_OUTPUT
# %  key: output
# %  description: Output vector points map of vertical deflections [m]
# %  required : yes
# %end

# %option G_OPT_R_OUTPUT
# %  key: raster_output
# %  description: Output raster map of vertical deflections [m]
# %  required : no
# %end

# %option
# %  key: g
# %  type: double
# %  description: gravitational acceleration at surface [m/s^2]
# %  answer: 9.8
# %  required : no
# %end

# %option
# %  key: ym
# %  type: double
# %  description: Young's Modulus [Pa]
# %  answer: 65E9
# %  required : no
# %end

# %option
# %  key: nu
# %  type: double
# %  description: Poisson's ratio
# %  answer: 0.25
# %  required : no
# %end

# %option
# %  key: rho_fill
# %  type: double
# %  description: Density of material that fills flexural depressions [kg/m^3]
# %  answer: 0
# %  required : no
# %end

# %option
# %  key: rho_m
# %  type: double
# %  description: Mantle density [kg/m^3]
# %  answer: 3300
# %  required : no
# %end


##################
# IMPORT MODULES #
##################

# PYTHON
import numpy as np

# GRASS
import grass.script as grass
from grass.pygrass import vector


####################
# UTILITY FUNCTION #
####################


def get_points_xy(vect_name):
    """
    to find x and y using pygrass, see my (A. Wickert's) StackOverflow answer:
    http://gis.stackexchange.com/questions/28061/how-to-access-vector-coordinates-in-grass-gis-from-python
    """
    points = vector.VectorTopo(vect_name)
    points.open("r")
    coords = []
    for i in range(len(points)):
        coords.append(points.read(i + 1).coords())
    coords = np.array(coords)
    return coords[:, 0], coords[:, 1]  # x, y


############################
# PASS VARIABLES AND SOLVE #
############################


def main():
    """
    Superposition of analytical solutions in gFlex for flexural isostasy in
    GRASS GIS
    """

    options, flags = grass.parser()
    # if just interface description is requested, it will not get to this point
    # so gflex will not be needed

    # GFLEX
    # try to import gflex only after we know that
    # we will actually do the computation
    try:
        import gflex
    except:
        print("")
        print("MODULE IMPORT ERROR.")
        print("In order to run r.flexure or g.flexure, you must download and install")
        print("gFlex. The most recent development version is available from")
        print("https://github.com/awickert/gFlex")
        print("Installation instructions are available on the page.")
        grass.fatal("Software dependency must be installed.")

    ##########
    # SET-UP #
    ##########

    # This code is for 2D flexural isostasy
    flex = gflex.F2D()
    # And show that it is coming from GRASS GIS
    flex.grass = True

    # Method
    flex.Method = "SAS_NG"

    # Parameters that are often changed for the solution
    ######################################################

    # x, y, q
    flex.x, flex.y = get_points_xy(options["input"])
    # xw, yw: gridded output
    if len(grass.parse_command("g.list", type="vect", pattern=options["output"])):
        if not grass.overwrite():
            grass.fatal(
                "Vector map '"
                + options["output"]
                + "' already exists. Use '--o' to overwrite."
            )
    # Just check raster at the same time if it exists
    if len(
        grass.parse_command("g.list", type="rast", pattern=options["raster_output"])
    ):
        if not grass.overwrite():
            grass.fatal(
                "Raster map '"
                + options["raster_output"]
                + "' already exists. Use '--o' to overwrite."
            )
    grass.run_command(
        "v.mkgrid",
        map=options["output"],
        type="point",
        overwrite=grass.overwrite(),
        quiet=True,
    )
    grass.run_command(
        "v.db.addcolumn",
        map=options["output"],
        columns="w double precision",
        quiet=True,
    )
    flex.xw, flex.yw = get_points_xy(options["output"])  # gridded output coordinates
    vect_db = grass.vector_db_select(options["input"])
    col_names = np.array(vect_db["columns"])
    q_col = col_names == options["column"]
    if np.sum(q_col):
        col_values = np.array(list(vect_db["values"].values())).astype(float)
        flex.q = col_values[:, q_col].squeeze()  # Make it 1D for consistency w/ x, y
    else:
        grass.fatal(
            "provided column name, "
            + options["column"]
            + " does not match\nany column in "
            + options["q0"]
            + "."
        )
    # Elastic thickness
    flex.Te = float(options["te"])
    if options["te_units"] == "km":
        flex.Te *= 1000
    elif options["te_units"] == "m":
        pass
    else:
        grass.fatal("Inappropriate te_units. How? Options should be limited by GRASS.")
    flex.rho_fill = float(options["rho_fill"])

    # Parameters that often stay at their default values
    ######################################################
    flex.g = float(options["g"])
    flex.E = float(
        options["ym"]
    )  # Can't just use "E" because reserved for "east", I think
    flex.nu = float(options["nu"])
    flex.rho_m = float(options["rho_m"])

    # Set verbosity
    if grass.verbosity() >= 2:
        flex.Verbose = True
    if grass.verbosity() >= 3:
        flex.Debug = True
    elif grass.verbosity() == 0:
        flex.Quiet = True

    # Check if lat/lon and let user know if verbosity is True
    if grass.region_env()[6] == "3":
        flex.latlon = True
        flex.PlanetaryRadius = float(grass.parse_command("g.proj", flags="j")["+a"])
        if flex.Verbose:
            print("Latitude/longitude grid.")
            print("Based on r_Earth = 6371 km")
            print("Computing distances between load points using great circle paths")

    ##########
    # SOLVE! #
    ##########

    flex.initialize()
    flex.run()
    flex.finalize()

    # Now to use lower-level GRASS vector commands to work with the database
    # table and update its entries
    # See for help:
    # http://nbviewer.ipython.org/github/zarch/workshop-pygrass/blob/master/02_Vector.ipynb
    w = vector.VectorTopo(options["output"])
    w.open("rw")  # Get ready to read and write
    wdb = w.dblinks[0]
    wtable = wdb.table()
    col = int(
        (np.array(wtable.columns.names()) == "w").nonzero()[0]
    )  # update this column
    for i in range(1, len(w) + 1):
        # ignoring 1st column: assuming it will be category (always true here)
        wnewvalues = (
            list(w[i].attrs.values())[1:col]
            + tuple([flex.w[i - 1]])
            + list(w[i].attrs.values())[col + 1 :]
        )
        wtable.update(key=i, values=wnewvalues)
    wtable.conn.commit()  # Save this
    w.close(build=False)  # don't build here b/c it is always verbose
    grass.run_command("v.build", map=options["output"], quiet=True)

    # And raster export
    # "w" vector defined by raster resolution, so can do direct v.to.rast
    # though if this option isn't selected, the user can do a finer-grained
    # interpolation, which shouldn't introduce much error so long as these
    # outputs are spaced at << 1 flexural wavelength.
    if options["raster_output"]:
        grass.run_command(
            "v.to.rast",
            input=options["output"],
            output=options["raster_output"],
            use="attr",
            attribute_column="w",
            type="point",
            overwrite=grass.overwrite(),
            quiet=True,
        )
        # And create a nice colormap!
        grass.run_command(
            "r.colors", map=options["raster_output"], color="differences", quiet=True
        )


def install_dependencies():
    print("PLACEHOLDER")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--install-dependencies":
        install_dependencies()
    else:
        main()
