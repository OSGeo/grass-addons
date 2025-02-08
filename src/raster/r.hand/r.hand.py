#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.random.walk
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Performs Height Above Nearest Drainage (HAND) analysis.
# COPYRIGHT:    (C) 2025 OpenPlains Inc.
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#!/usr/bin/env python

# %module
# % description: Performs Height Above Nearest Drainage (HAND) analysis.
# % keyword: raster
# % keyword: hydrology
# % keyword: flood
# % keyword: inundation
# % keyword: json
# %end

# %option
# % key: stream_rast
# % type: string
# % required: yes
# % description: Name of the stream raster map
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: direction
# % type: string
# % required: yes
# % description: Name of the flow direction raster map
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: elevation
# % type: string
# % required: yes
# % description: Name of the elevation raster map
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % key: difference
# % type: string
# % required: yes
# % description: Name of the output difference raster map
# % guisection: Output
# %end

# %option G_OPT_R_OUTPUT
# % key: inundation
# % type: string
# % required: no
# % description: Name of the output inundation raster map
# % guisection: Output
# %end

# %option
# % key: start_water_level
# % type: double
# % required: no
# % description: Start water level for flooding simulation
# % answer: 0
# % guisection: Parameters
# %end

# %option
# % key: end_water_level
# % type: double
# % required: no
# % description: End water level for flooding simulation
# % answer: 5
# % guisection: Parameters
# %end

# %option
# % key: water_level_step
# % type: double
# % required: no
# % description: Step increment for water level in flooding simulation
# % answer: 0.5
# % guisection: Parameters
# %end


import sys
import grass.script as gs


def output_inundation_extent_graph():
    pass


def main():
    # Retrieve options from user input
    stream_rast = options["stream_rast"]
    direction = options["direction"]
    elevation = options["elevation"]
    difference = options["difference"]
    start_water_level = float(options["start_water_level"])
    end_water_level = float(options["end_water_level"])
    water_level_step = float(options["water_level_step"])
    output = options["output"]
    inundation = options["inundation"]

    # Calculate the height above nearest drainage
    gs.run_command(
        "r.stream.distance",
        stream_rast=stream_rast,
        direction=direction,
        elevation=elevation,
        method="downstream",  # Fixed to downstream for HAND analysis
        difference=difference,
    )

    # Run r.lake on a stream network
    gs.run_command(
        "r.lake",
        elevation=difference,
        water_level=start_water_level,
        lake=inundation,
        seed=stream_rast,
    )

    # Run r.lake.series on a stream network
    gs.run_command(
        "r.lake.series",
        elevation=difference,  # Using the output from r.stream.distance
        start_water_level=start_water_level,
        end_water_level=end_water_level,
        water_level_step=water_level_step,
        output=output,
        seed=stream_rast,
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
