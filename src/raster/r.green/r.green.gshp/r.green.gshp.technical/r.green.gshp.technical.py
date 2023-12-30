#!/usr/bin/env python

#
############################################################################
#
# MODULE:      r.green.gshp.technical
# AUTHOR(S):   Pietro Zambelli
# PURPOSE:     Calculate the ground source heat pump technical potential using
#              the ASHRAE method
# COPYRIGHT:   (C) 2017 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

# %module
# % description: Calculate the Ground Source Heat Pump technical potential using the ASHRAE method.
# % keyword: raster
# % keyword: geothermal
# % keyword: renewable energy
# %end

##
## REQUIRED INPUTS
##
# %option G_OPT_R_INPUT
# % key: ground_conductivity
# % description: Raster with depth-averaged ground thermal conductivity lambda [W m-1 K-1]
# % required: yes
# %end

##
## OPTIONAL INPUTS
##

#######################
## Ground properties ##
#######################
# %option G_OPT_R_INPUT
# % key: ground_diffusivity_rast
# % description: Raster with depth-averaged ground diffusivity [m2 day-1]
# % required: no
# % guisection: Ground
# %end
# %option
# % key: ground_diffusivity_value
# % type: double
# % key_desc: double
# % description: Value with depth-averaged ground diffusivity  [m2 day-1]
# % required: no
# % answer: 0.086
# % guisection: Ground
# %end

# %option G_OPT_R_INPUT
# % key: ground_temp_rast
# % description: Raster with the initial ground temperature T0 [degrees C]
# % required: no
# % guisection: Ground
# %end
# %option
# % key: ground_temp_value
# % type: double
# % key_desc: double
# % description: Value with the initial ground temperature T0 [degrees C]
# % required: no
# % answer: 10.
# % guisection: Ground
# %end


#############################
## Ground loads properties ##
#############################
# %option G_OPT_R_INPUT
# % key: g_loads_6h_rast
# % description: Peak of the maximum 6 hourly ground loads [W]
# % required: no
# % guisection: Ground loads
# %end
# %option
# % key: g_loads_6h_value
# % type: double
# % key_desc: double
# % description: Peak of the maximum 6 hourly ground loads [W]
# % required: no
# % answer: 60.
# % guisection: Ground loads
# %end

# %option G_OPT_R_INPUT
# % key: g_loads_1m_rast
# % description: Month with the maximum ground loads [W]
# % required: no
# % guisection: Ground loads
# %end
# %option
# % key: g_loads_1m_value
# % type: double
# % key_desc: double
# % description: Month with the maximum ground loads [W]
# % required: no
# % answer: 15.
# % guisection: Ground loads
# %end

# %option G_OPT_R_INPUT
# % key: g_loads_1y_rast
# % description: Yearly average ground loads [W]
# % required: no
# % guisection: Ground loads
# %end
# %option
# % key: g_loads_1y_value
# % type: double
# % key_desc: double
# % description: Yearly average ground loads [W]
# % required: no
# % answer: 5.
# % guisection: Ground loads
# %end

######################
## Fluid properties ##
######################
# %option
# % key: fluid_capacity
# % type: double
# % key_desc: double
# % description: Fluid capacity Cp [J kg-1 K-1]
# % required: no
# % answer: 4200.
# % guisection: Fluid
# %end
# %option
# % key: fluid_massflow
# % type: double
# % key_desc: double
# % description: Fluid massflow  [kg s-1 kW-1]
# % required: no
# % answer: 0.050
# % guisection: Fluid
# %end
# %option
# % key: fluid_inlettemp
# % type: double
# % key_desc: double
# % description: Inlet temperature  [degrees C]
# % required: no
# % answer: 2.
# % guisection: Fluid
# %end


#########################
## Borehole properties ##
#########################
# %option
# % key: bh_radius
# % type: double
# % key_desc: double
# % description: Borehole radius [m]
# % required: no
# % answer: 0.06
# % guisection: Borehole
# %end
# %option
# % key: bh_convection
# % type: double
# % key_desc: double
# % description: Internal convection coefficient [W m-2 K-1]
# % required: no
# % answer: 1.52
# % guisection: Borehole
# %end
# %option
# % key: bh_resistence
# % type: double
# % key_desc: double
# % description: Borehole thermal resistence [m K W-1]
# % required: no
# % answer: nan
# % guisection: Borehole
# %end

# %option
# % key: pipe_inner_radius
# % type: double
# % key_desc: double
# % description: Borehole pipe inner radius [m]
# % required: no
# % answer: 0.01365
# % guisection: Borehole
# %end
# %option
# % key: pipe_outer_radius
# % type: double
# % key_desc: double
# % description: Borehole pipe outer radius [m]
# % required: no
# % answer: 0.0167
# % guisection: Borehole
# %end
# %option
# % key: pipe_distance
# % type: double
# % key_desc: double
# % description: Center-to-center distance between pipes [m]
# % required: no
# % answer: 0.0511
# % guisection: Borehole
# %end
# %option
# % key: k_pipe
# % type: double
# % key_desc: double
# % description: Pipe thermal conductivity [W m-1 K-1]
# % required: no
# % answer: 0.42
# % guisection: Borehole
# %end
# %option
# % key: k_grout
# % type: double
# % key_desc: double
# % description: Grout thermal conductivity [W m-1 K-1]
# % required: no
# % answer: 1.52
# % guisection: Borehole
# %end


###############################
## Borehole filed properties ##
###############################
# %option
# % key: field_distance
# % type: double
# % key_desc: double
# % description: Distance between boreholes heat exchanger
# % required: no
# % answer: 6.1
# % guisection: BHE Field
# %end
# %option
# % key: field_number
# % type: integer
# % key_desc: integer
# % description: Number of borehole heat exchanger
# % required: no
# % answer: 2
# % guisection: BHE Field
# %end
# %option
# % key: field_ratio
# % type: double
# % key_desc: double
# % description: Borefield aspect ratio
# % required: no
# % answer: 1.2
# % guisection: BHE Field
# %end


#############
## Outputs ##
#############
# %option G_OPT_R_OUTPUT
# % key: bhe_length
# % type: string
# % key_desc: name
# % description: Name of output raster map with the geothermal length of the BHE [m]
# % required: no
# %end
# %option G_OPT_R_OUTPUT
# % key: bhe_field_length
# % type: string
# % key_desc: name
# % description: Name of output raster map with the geothermal length of the BHE field [m]
# % required: no
# %end

# %flag
# % key: d
# % description: Debug with intermediate maps
# %end

from __future__ import print_function

import atexit
import os
import sys

from grass.script import core as gcore
from grass.script.utils import set_path

try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libgshp", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libgreen.utils import cleanup, rast_or_numb
    from libgshp.ashrae import (
        GroundProperties,
        GroundLoads,
        FluidProperties,
        Borehole,
        BoreholeExchanger,
        BoreholeField,
        get_vars,
        r_bhe_length,
        r_field_length,
    )
except ImportError:
    try:
        set_path("r.green", "libgshp", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libgreen.utils import cleanup, rast_or_numb
        from libgshp.ashrae import (
            GroundProperties,
            GroundLoads,
            FluidProperties,
            Borehole,
            BoreholeExchanger,
            BoreholeField,
            get_vars,
            r_bhe_length,
            r_field_length,
        )
    except ImportError:
        gcore.warning("libgreen and libgshp not in the python path!")


def main(opts, flgs):
    """
    Parameters
    ----------

    ground_conductivity: k [W m-1 K-1]
        thermal conductivity
    ground_diffusivity: α [m2 day-1]
        thermal diffusivity
    ground_temperature: Tg [degrees C]
        Undisturbed ground temperature
    g_loads_6h [W]
        Peak of 6 hours ground load
    g_loads_1m:  [W]
        Maximum monthly ground load
    g_loads_1y: qy [W]
        Average ground load
    fluid_capacity: Cp [J kg-1 K-1]
        Thermal heat capacity of the fluid
    fluid_massflow: mfls [kg s-1 kW-1]
        total mass flow rate per kW of peak hourly ground load
    fluid_inlettemp: TinHP [degrees C]
        max/min heat pump inlet temperature
    bh_radius: radius [m]
        borehole radius
    bh_convection: hconv [W m-2 K-1]
        Internal convection coefficient
    pipe_inner: rpin [m]
        pipe inner radius
    pipe_outer: rpext [m]
        pipe outer radius
    pipe_distance: LU [m]
        center-to-center distance between pipes
    k_pipe: kpipe [W m-1 K-1]
        pipe thermal conductivity
    k_grout: kgrout [W m-1 K-1]
        grout thermal conductivity
    distance_bhe: B [m]
        distance between boreholes (BHE)
    number_bhe: [n]
        number of boreholes (BHE)
    ratio_bhe: [-]
        borefield aspect ratio

    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly='g_loads_6h',
    ...                                    monthly='g_loads_1m',
    ...                                    yearly='g_loads_1y'),
    ...           ground=GroundProperties(conductivity='g_conductivity',
    ...                                   diffusivity='g_diffusivity',
    ...                                   temperature='g_temperature'),
    ...           fluid=FluidProperties(capacity=4200, massflow=0.050,
    ...                                 inlettemp=40.2),
    ...           borehole=Borehole(radius=0.06,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...                             convection=1000.)
    ...           )
    >>> infovars = InfoVars('l_term', 'm_term', 's_term', 'f_temp', 'res')
    >>> r_bhe_length('bhe_length', bhe, infovars, execute=False)
    """
    DEBUG = flags["d"]
    OVER = gcore.overwrite()
    tmpbase = "tmprgreen_%i" % os.getpid()
    atexit.register(cleanup, pattern=(tmpbase + "*"), debug=DEBUG)

    # ================================================
    # GROUND
    # get raster or scalar value
    ground = GroundProperties(
        opts["ground_conductivity"],
        rast_or_numb("ground_diffusivity_rast", "ground_diffusivity_value", opts),
        rast_or_numb("ground_temp_rast", "ground_temp_value", opts),
    )

    # ================================================
    # GROUND LOADS
    ground_loads = GroundLoads(
        rast_or_numb("g_loads_6h_rast", "g_loads_6h_value", opts),
        rast_or_numb("g_loads_1m_rast", "g_loads_1m_value", opts),
        rast_or_numb("g_loads_1y_rast", "g_loads_1y_value", opts),
    )

    # ================================================
    # FLUID
    fluid = FluidProperties(
        float(opts["fluid_capacity"]),
        float(opts["fluid_massflow"]),
        float(opts["fluid_inlettemp"]),
    )

    # ================================================
    # BOREHOLE
    borehole = Borehole(
        radius=float(opts["bh_radius"]),
        pipe_inner_radius=float(opts["pipe_inner_radius"]),
        pipe_outer_radius=float(opts["pipe_outer_radius"]),
        k_pipe=float(opts["k_pipe"]),
        k_grout=float(opts["k_grout"]),
        distance=float(opts["pipe_distance"]),
        convection=float(opts["bh_convection"]),
    )

    bhe = BoreholeExchanger(ground_loads, ground, fluid, borehole)

    field = BoreholeField(
        float(opts["field_distance"]),
        float(opts["field_number"]),
        float(opts["field_ratio"]),
        bhe,
    )

    # ================================================
    # START COMPUTATIONS
    infovars = get_vars(opts["bhe_length"], bhe, tmpbase, execute=True, overwrite=OVER)

    r_bhe_length(opts["bhe_length"], bhe, infovars, execute=True, overwrite=OVER)
    r_field_length(
        opts["bhe_field_length"],
        field,
        infovars,
        basename=tmpbase,
        length_single=opts["bhe_length"],
        execute=True,
        overwrite=OVER,
    )


if __name__ == "__main__":
    options, flags = gcore.parser()
    main(options, flags)
    sys.exit(0)
