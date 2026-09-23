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
# COPYRIGHT:    (c) 2012, 2014, 2015, 2026 Andrew Wickert
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
# Started 11 March 2012 as a GRASS interface for Flexure (now gFlex)
# Revised 15--?? November 2014 after significantly improving the model
# by Andy Wickert

# %module
# % description: Computes lithospheric flexural isostasy
# % keyword: raster
# % keyword: geophysics
# %end

# %flag
# %  key: l
# %  description: Allows running in lat/lon: dx is f(lat) at grid N-S midpoint
# %end

# %option
# %  key: method
# %  type: string
# %  description: fd (finite diff), fft (spectral), or sas (superposition)
# %  options: fd, fft, sas
# %  required : yes
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  type: string
# %  description: Raster map of loads (thickness * density * g) [Pa]
# %  required : yes
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  type: string
# %  description: Output raster map of vertical deflections [m]
# %  required : yes
# %end

# %option G_OPT_R_INPUT
# %  key: te
# %  type: string
# %  description: Elastic thickness: scalar (any solution method) or raster (FD only)
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

# %option
# %  key: northbc
# %  type: string
# %  description: Northern boundary condition (FD and FFT)
# %  options: clamped, pinned, free, mirror, periodic, infinite
# %  answer: infinite
# %  required : no
# %  guisection: Boundary conditions
# %end

# %option
# %  key: southbc
# %  type: string
# %  description: Southern boundary condition (FD and FFT)
# %  options: clamped, pinned, free, mirror, periodic, infinite
# %  answer: infinite
# %  required : no
# %  guisection: Boundary conditions
# %end

# %option
# %  key: westbc
# %  type: string
# %  description: Western boundary condition (FD and FFT)
# %  options: clamped, pinned, free, mirror, periodic, infinite
# %  answer: infinite
# %  required : no
# %  guisection: Boundary conditions
# %end

# %option
# %  key: eastbc
# %  type: string
# %  description: Eastern boundary condition (FD and FFT)
# %  options: clamped, pinned, free, mirror, periodic, infinite
# %  answer: infinite
# %  required : no
# %  guisection: Boundary conditions
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

# %option
# %  key: sigma_xx
# %  type: double
# %  description: In-plane normal stress in the x-direction [Pa]; FD and FFT only
# %  answer: 0
# %  required : no
# %  guisection: In-plane stresses
# %end

# %option
# %  key: sigma_yy
# %  type: double
# %  description: In-plane normal stress in the y-direction [Pa]; FD and FFT only
# %  answer: 0
# %  required : no
# %  guisection: In-plane stresses
# %end

# %option
# %  key: sigma_xy
# %  type: double
# %  description: In-plane shear stress [Pa]; FD and FFT only
# %  answer: 0
# %  required : no
# %  guisection: In-plane stresses
# %end

##################
# IMPORT MODULES #
##################

# PYTHON
import warnings

import numpy as np

# GRASS
import grass.script as gs
import grass.script.array as garray

############################
# PASS VARIABLES AND SOLVE #
############################


def main():
    """
    Gridded flexural isostatic solutions
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
            _("r.flexure requires gFlex >= 2.0.0; installed: ") + gflex.__version__
        )

    # This code is for 2D flexural isostasy
    flex = gflex.F2D()
    # And show that it is coming from GRASS GIS
    flex.grass = True

    # Flags
    latlon_override = flags["l"]

    # Inputs
    # Solution selection
    flex.method = options["method"].lower()
    # Parameters that are often changed for the solution
    flex.qs = garray.array(options["input"])
    # Elastic thickness
    try:
        flex.T_e = float(options["te"])
    except ValueError:
        flex.T_e = np.array(garray.array(options["te"]))
    if options["te_units"] == "km":
        flex.T_e *= 1000
    elif options["te_units"] == "m":
        pass
    # Parameters that often stay at their default values
    flex.g = float(options["g"])
    flex.E = float(
        options["ym"]
    )  # Can't just use "E" because reserved for "east", I think
    flex.nu = float(options["nu"])
    flex.rho_m = float(options["rho_m"])
    flex.rho_fill = float(options["rho_fill"])
    # In-plane stresses (FD and FFT only; gFlex ignores for other methods)
    flex.sigma_xx = float(options["sigma_xx"])
    flex.sigma_yy = float(options["sigma_yy"])
    flex.sigma_xy = float(options["sigma_xy"])
    # FD and FFT: pass user BCs through; SAS ignores BCs (always no_outside_loads).
    # 'infinite' is a native gFlex alias for no_outside_loads.
    if flex.method in ("fd", "fft"):
        flex.bc_north = options["northbc"]
        flex.bc_south = options["southbc"]
        flex.bc_west = options["westbc"]
        flex.bc_east = options["eastbc"]

    # gFlex defaults to quiet (WARNING log level); opt in at --verbose (level 3).
    # GRASS default verbosity is 2; level 3 is --verbose; there is no level 4.
    if gs.verbosity() >= 3:
        flex.verbose = True
        flex.quiet = False

    # First check if output exists
    if len(gs.parse_command("g.list", type="rast", pattern=options["output"])):
        if not gs.overwrite():
            gs.fatal(
                _("Raster map <%s> already exists. Use '--o' to overwrite.")
                % options["output"]
            )

    # Get grid spacing from GRASS
    # Check if lat/lon and proceed as directed
    if gs.region_env()[6] == "3":
        if latlon_override:
            if flex.verbose:
                gs.message(_("Latitude/longitude grid."))
                gs.message(_("Based on r_Earth = 6371 km"))
                gs.message(_("Setting y-resolution [m] to 111,195 * [degrees]"))
            flex.dy = gs.region()["nsres"] * 111195.0
            NSmid = (gs.region()["n"] + gs.region()["s"]) / 2.0
            dx_at_mid_latitude = (
                (3.14159 / 180.0) * 6371000.0 * np.cos(np.deg2rad(NSmid))
            )
            if flex.verbose:
                gs.message(
                    _("Setting x-resolution [m] to %.2f * [degrees]")
                    % dx_at_mid_latitude
                )
            flex.dx = gs.region()["ewres"] * dx_at_mid_latitude
        else:
            gs.fatal(_("Need the '-l' flag to enable lat/lon solution approximation."))
    # Otherwise straightforward
    else:
        flex.dx = gs.region()["ewres"]
        flex.dy = gs.region()["nsres"]

    # CALCULATE!
    gs.message(_("Computing deflections..."))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        flex.initialize()
        flex.run()
        # finalize() deletes flex.w in gFlex v2, so read it first
        w = flex.w
        flex.finalize()
    for warninfo in caught:
        gs.warning(str(warninfo.message))

    # Write to GRASS
    # Create a new garray buffer and write to it
    outbuffer = garray.array()  # Instantiate output buffer
    outbuffer[...] = w
    outbuffer.write(
        options["output"], overwrite=gs.overwrite()
    )  # Write it with the desired name
    # And create a nice colormap!
    gs.run_command("r.colors", map=options["output"], color="differences", quiet=True)


if __name__ == "__main__":
    main()
