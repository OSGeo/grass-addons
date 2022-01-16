#!/usr/bin/env python
############################################################################
#
# MODULE:       r.flexure
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Calculate flexure of the lithosphere under a specified
#               set of loads and with a given elastic thickness (scalar
#               or array)
#
# COPYRIGHT:    (c) 2012, 2014, 2015 Andrew Wickert
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
# Started 11 March 2012 as a GRASS interface for Flexure (now gFlex)
# Revised 15--?? November 2014 after significantly improving the model
# by Andy Wickert

#%module
#% description: Computes lithospheric flexural isostasy
#% keyword: raster
#% keyword: geophysics
#%end

#%flag
#%  key: l
#%  description: Allows running in lat/lon: dx is f(lat) at grid N-S midpoint
#%end

#%option
#%  key: method
#%  type: string
#%  description: Solution method: Finite Diff. or Superpos. of analytical sol'ns
#%  options: FD, SAS
#%  required : yes
#%end

#%option G_OPT_R_INPUT
#%  key: input
#%  type: string
#%  description: Raster map of loads (thickness * density * g) [Pa]
#%  required : yes
#%end

#%option G_OPT_R_INPUT
#%  key: te
#%  type: string
#%  description: Elastic thickness: scalar or raster; unis chosen in "te_units"
#%  required : yes
#%end

#%option
#%  key: te_units
#%  type: string
#%  description: Units for elastic thickness
#%  options: m, km
#%  required : yes
#%end

#%option G_OPT_R_OUTPUT
#%  key: output
#%  type: string
#%  description: Output raster map of vertical deflections [m]
#%  required : yes
#%end

#%option
#%  key: solver
#%  type: string
#%  description: Solver type
#%  options: direct, iterative
#%  answer: direct
#%  required : no
#%end

#%option
#%  key: tolerance
#%  type: double
#%  description: Convergence tolerance (between iterations) for iterative solver
#%  answer: 1E-3
#%  required : no
#%end

#%option
#%  key: northbc
#%  type: string
#%  description: Northern boundary condition
#%  options: 0Displacement0Slope, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic, NoOutsideLoads
#%  answer: NoOutsideLoads
#%  required : no
#%end

#%option
#%  key: southbc
#%  type: string
#%  description: Southern boundary condition
#%  options: 0Displacement0Slope, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic, NoOutsideLoads
#%  answer: NoOutsideLoads
#%  required : no
#%end

#%option
#%  key: westbc
#%  type: string
#%  description: Western boundary condition
#%  options: 0Displacement0Slope, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic, NoOutsideLoads
#%  answer: NoOutsideLoads
#%  required : no
#%end

#%option
#%  key: eastbc
#%  type: string
#%  description: Eastern boundary condition
#%  options: 0Displacement0Slope, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic, NoOutsideLoads
#%  answer: NoOutsideLoads
#%  required : no
#%end

#%option
#%  key: g
#%  type: double
#%  description: gravitational acceleration at surface [m/s^2]
#%  answer: 9.8
#%  required : no
#%end

#%option
#%  key: ym
#%  type: double
#%  description: Young's Modulus [Pa]
#%  answer: 65E9
#%  required : no
#%end

#%option
#%  key: nu
#%  type: double
#%  description: Poisson's ratio
#%  answer: 0.25
#%  required : no
#%end

#%option
#%  key: rho_fill
#%  type: double
#%  description: Density of material that fills flexural depressions [kg/m^3]
#%  answer: 0
#%  required : no
#%end

#%option
#%  key: rho_m
#%  type: double
#%  description: Mantle density [kg/m^3]
#%  answer: 3300
#%  required : no
#%end

##################
# IMPORT MODULES #
##################

# PYTHON
import numpy as np

# GRASS
import grass.script as grass
import grass.script.array as garray

############################
# PASS VARIABLES AND SOLVE #
############################


def main():
    """
    Gridded flexural isostatic solutions
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
        print("https://github.com/awickert/gFlex.")
        print("Installation instructions are available on the page.")
        grass.fatal("Software dependency must be installed.")

    # This code is for 2D flexural isostasy
    flex = gflex.F2D()
    # And show that it is coming from GRASS GIS
    flex.grass = True

    # Flags
    latlon_override = flags["l"]

    # Inputs
    # Solution selection
    flex.Method = options["method"]
    if flex.Method == "FD":
        flex.Solver = options["solver"]
        if flex.Solver:
            flex.ConvergenceTolerance = options["tolerance"]
        # Always use the van Wees and Cloetingh (1994) solution type.
        # It is the best.
        flex.PlateSolutionType = "vWC1994"
    # Parameters that are often changed for the solution
    qs = options["input"]
    flex.qs = garray.array(qs)
    # Elastic thickness
    try:
        flex.Te = float(options["te"])
    except:
        flex.Te = garray.array(
            options["te"]
        )  # FlexureTe is the one that is used by Flexure
        flex.Te = np.array(flex.Te)
    if options["te_units"] == "km":
        flex.Te *= 1000
    elif options["te_units"] == "m":
        pass
    # No "else"; shouldn't happen
    flex.rho_fill = float(options["rho_fill"])
    # Parameters that often stay at their default values
    flex.g = float(options["g"])
    flex.E = float(
        options["ym"]
    )  # Can't just use "E" because reserved for "east", I think
    flex.nu = float(options["nu"])
    flex.rho_m = float(options["rho_m"])
    # Solver type and iteration tolerance
    flex.Solver = options["solver"]
    flex.ConvergenceTolerance = float(options["tolerance"])
    # Boundary conditions
    flex.BC_N = options["northbc"]
    flex.BC_S = options["southbc"]
    flex.BC_W = options["westbc"]
    flex.BC_E = options["eastbc"]

    # Set verbosity
    if grass.verbosity() >= 2:
        flex.Verbose = True
    if grass.verbosity() >= 3:
        flex.Debug = True
    elif grass.verbosity() == 0:
        flex.Quiet = True

    # First check if output exists
    if len(grass.parse_command("g.list", type="rast", pattern=options["output"])):
        if not grass.overwrite():
            grass.fatal(
                "Raster map '"
                + options["output"]
                + "' already exists. Use '--o' to overwrite."
            )

    # Get grid spacing from GRASS
    # Check if lat/lon and proceed as directed
    if grass.region_env()[6] == "3":
        if latlon_override:
            if flex.Verbose:
                print("Latitude/longitude grid.")
                print("Based on r_Earth = 6371 km")
                print("Setting y-resolution [m] to 111,195 * [degrees]")
            flex.dy = grass.region()["nsres"] * 111195.0
            NSmid = (grass.region()["n"] + grass.region()["s"]) / 2.0
            dx_at_mid_latitude = (
                (3.14159 / 180.0) * 6371000.0 * np.cos(np.deg2rad(NSmid))
            )
            if flex.Verbose:
                print(
                    "Setting x-resolution [m] to "
                    + "%.2f" % dx_at_mid_latitude
                    + " * [degrees]"
                )
            flex.dx = grass.region()["ewres"] * dx_at_mid_latitude
        else:
            grass.fatal("Need the '-l' flag to enable lat/lon solution approximation.")
    # Otherwise straightforward
    else:
        flex.dx = grass.region()["ewres"]
        flex.dy = grass.region()["nsres"]

    # CALCULATE!
    flex.initialize()
    flex.run()
    flex.finalize()

    # Write to GRASS
    # Create a new garray buffer and write to it
    outbuffer = garray.array()  # Instantiate output buffer
    outbuffer[...] = flex.w
    outbuffer.write(
        options["output"], overwrite=grass.overwrite()
    )  # Write it with the desired name
    # And create a nice colormap!
    grass.run_command(
        "r.colors", map=options["output"], color="differences", quiet=True
    )

    # Reinstate this with a flag or output filename
    # But I think better to let interpolation happen a posteriori
    # So the user knows what the solution is and what it isn't
    # grass.run_command('r.resamp.interp', input=output, output=output + '_interp', method='lanczos', overwrite=True, quiet=True)
    # grass.run_command('r.colors', map=output + '_interp', color='rainbow', quiet=True)#, flags='e')


def install_dependencies():
    print("PLACEHOLDER")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--install-dependencies":
        install_dependencies()
    else:
        main()
