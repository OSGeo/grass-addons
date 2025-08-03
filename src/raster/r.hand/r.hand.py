#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.hand
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Performs Height Above Nearest Drainage (HAND) analysis.
# COPYRIGHT:    (C) 2025 OpenPlains Inc. and the GRASS Development Team
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Performs Height Above Nearest Drainage (HAND) analysis and flood inundation mapping with HAND method.
# % keyword: raster
# % keyword: hydrology
# % keyword: flood
# % keyword: inundation
# % keyword: json
# %end

# %option G_OPT_R_ELEV
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: streams
# % label: Stream raster map
# % required: no
# % description: Name of the stream raster map
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: direction
# % label: Flow direction raster map
# % type: string
# % required: no
# % description: Name of the flow direction raster map
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % key: inundation_raster
# % required: no
# % description: Name of the output inundation raster map
# % guisection: Output
# %end

# %option G_OPT_R_OUTPUT
# % key: hand
# % label: Height above nearest drainage raster map
# % type: string
# % required: no
# % description: Name of the output HAND raster map
# % guisection: Output
# %end

# %option G_OPT_STRDS_OUTPUT
# % key: inundation_strds
# % required: no
# % description: Name of the output inundation STRDS.
# % guisection: Output
# %end

# %option
# % key: threshold
# % type: integer
# % required: no
# % description: Basin threshold value
# % answer: 10000
# % guisection: Parameters
# %end

# %option
# % key: depth
# % type: double
# % required: no
# % description: Inundation depth (single output)
# % guisection: Parameters
# %end

# %option
# % key: start_water_level
# % type: double
# % required: no
# % description: Start water level for flooding simulation
# % guisection: Parameters
# %end

# %option
# % key: end_water_level
# % type: double
# % required: no
# % description: End water level for flooding simulation
# % guisection: Parameters
# %end

# %option
# % key: water_level_step
# % type: double
# % required: no
# % description: Step increment for water level in flooding simulation
# % answer: 1
# % guisection: Parameters
# %end

# %option G_OPT_MEMORYMB
# %end

# %flag
# % key: t
# % description: Generate inundation raster maps for a series of water levels
# % guisection: Output
# %end

# %flag
# % key: m
# % description: Use memory swap (operation is slow)
# %end

import sys
import atexit
import uuid
import grass.script as gs
import grass.script.core as gcore
from grass.exceptions import CalledModuleError

tmp_raster_list = []


def cleanup():
    """ "Remove temporary raster maps"""
    if len(tmp_raster_list) > 0:
        gs.run_command(
            "g.remove",
            type="raster",
            name=",".join(tmp_raster_list),
            # pattern="tmp_*",
            flags="f",
            quiet=True,
        )


def check_addon_installed(addon: str, fatal=True) -> None:
    """Check if a GRASS GIS addon is installed"""
    if not gcore.find_program(addon, "--help"):
        call = gcore.fatal if fatal else gcore.warning
        call(
            _(
                "Addon {a} is not installed. Please install it using g.extension."
            ).format(a=addon)
        )


def run_r_watershed(
    elevation: str,
    streams: str,
    direction: str,
    threshold: int,
    memory: int,
    swap_mode_flag: str,
) -> None:
    """
    Run the GRASS GIS r.watershed module to generate streams and flow direction raster maps.

    Parameters:
    elevation (str): Name of the input elevation raster map.
    streams (str): Name of the output streams raster map.
    direction (str): Name of the output flow direction raster map.
    threshold (int): Minimum size of exterior watershed basin in cells. Must be greater than 0.
    memory (int): Maximum memory to be used in MB.
    swap_mode_flag (str): If provided, enables memory swap mode.

    Returns:
    None
    """

    if streams.startswith("tmp") and direction.startswith("tmp"):
        gs.message(_("Generating streams and flow direction raster maps"))
        if threshold <= 0:
            gs.fatal(_("Threshold must be greater than 0"))

        try:
            gs.run_command(
                "r.watershed",
                elevation=elevation,
                threshold=threshold,
                stream=streams,
                drainage=direction,
                memory=memory,
                flags=swap_mode_flag,
                quiet=True,
            )
        except CalledModuleError as e:
            gs.fatal(
                _("Error generating streams and flow direction raster maps: %s")
                % e.stderr
            )


def set_hand_colors(hand: str) -> None:
    """Set HAND raster colors based on Norbre et al. 2011"""
    hand_colors = """
        0 white
        5 #1d91c0
        15 #41ab5d
        100% #ec7014
        nv white
        default grey
    """
    try:
        gs.write_command("r.colors", map=hand, rules="-", stdin=hand_colors, quiet=True)
    except CalledModuleError as e:
        gs.fatal(_("Error setting HAND colors: %s") % e.stderr)


def set_hand_categories(hand: str) -> None:
    """Set HAND raster categories based on Nobre et al. 2011"""
    hand_cats = "-30000:0:no data\n1:5:Surface water table\n5:15:Shallow water table\n15:30000:Deep water table"
    try:
        with gs.feed_command(
            "r.category", map=hand, rules="-", separator=":", quiet=True
        ) as cmd:
            cmd.stdin.write(hand_cats.encode())
            cmd.stdin.close()
    except CalledModuleError as e:
        gs.fatal(_("Error setting HAND categories: %s") % e.stderr)


def run_stream_distance(
    streams: str,
    direction: str,
    elevation: str,
    hand: str,
    memory: int,
    swap_mode_flag: str,
) -> None:
    """
    Calculate the height above nearest drainage (HAND) using the r.stream.distance GRASS GIS module.

    Parameters:
    streams (str): Name of the input stream raster map.
    direction (str): Name of the input flow direction raster map.
    elevation (str): Name of the input elevation raster map.
    hand (str): Name of the output raster map to store the height above nearest drainage.
    memory (int): Maximum memory to be used by the module.
    swap_mode_flag (str): Use memory swap (operation is slow).

    Returns:
    None
    """
    gs.message(_("Calculating height above nearest drainage"))

    try:
        gs.run_command(
            "r.stream.distance",
            stream_rast=streams,
            direction=direction,
            elevation=elevation,
            method="downstream",  # Fixed to downstream for HAND analysis
            difference=hand,
            memory=memory,
            flags=swap_mode_flag,
            quiet=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Error calculating height above nearest drainage: %s") % e.stderr)


def run_r_lake(hand: str, depth: float, inundation: str, streams: str) -> None:
    """
    Generates an inundation raster map using the r.lake GRASS GIS module.

    Parameters:
    hand (str): The name of the elevation raster map.
    depth (float): The water level to be used for inundation. Must be greater than 0.
    inundation (str): The name of the output inundation raster map.
    streams (str): The name of the seed raster map indicating the starting points for inundation.

    Returns:
    None
    """

    gs.message(_("Generating inundation raster map"))
    if not depth or depth < 0:
        gs.fatal(_("Inundation depth must be greater than 0"))

    try:
        gs.run_command(
            "r.lake",
            elevation=hand,
            water_level=depth,
            lake=inundation,
            seed=streams,
            quiet=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Error generating inundation raster map: %s") % e.stderr)


def run_r_lake_series(
    hand: str,
    start_water_level: float,
    end_water_level: float,
    water_level_step: float,
    inundation_strds: str,
    streams: str,
) -> None:
    """
    Runs r.lake.series to generate inundation raster maps for a series of water levels.

    Parameters:
    hand (str): The name of the elevation raster map.
    start_water_level (float): The starting water level for the inundation series.
    end_water_level (float): The ending water level for the inundation series.
    water_level_step (float): The step increment for water levels between start and end.
    inundation_strds (str): The name of the output space-time raster dataset.
    streams (str): The name of the streams raster map used as seed points.

    Returns:
    None
    """
    """Runs r.lake.series to generate inundation raster maps for a series of water levels"""
    gs.message(_("Generating inundation raster maps"))

    if start_water_level is None:
        gs.fatal(_("Start water level must be provided"))

    if end_water_level is None:
        gs.fatal(_("End water level must be provided"))

    if start_water_level < 0:
        gs.fatal(_("Start water level must be greater than 0"))

    if start_water_level > end_water_level:
        gs.fatal(_("Start water level must be less than end water level"))

    if water_level_step < 0:
        gs.fatal(_("Water level step must be greater than 0"))
    try:
        gs.run_command(
            "r.lake.series",
            elevation=hand,
            start_water_level=start_water_level,
            end_water_level=end_water_level,
            water_level_step=water_level_step,
            output=inundation_strds,
            seed=streams,
            quiet=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Error generating inundation raster maps: %s") % e.stderr)


def generate_temp_raster_name(raster_name: str) -> str:
    """Generate a temporary raster name"""
    uuid_str = str(uuid.uuid4())
    tmp_raster_name = f"tmp_{raster_name}_{uuid_str}"
    gs.debug(_("Temporary raster name: %s") % tmp_raster_name)
    tmp_raster_list.append(tmp_raster_name)
    return tmp_raster_name


def check_raster_exists(raster: str) -> str:
    # check if input file exists
    if not gs.find_file(raster)["file"]:
        gs.fatal(_("Raster map %s not found") % raster)
    return raster


def main():
    # Required options
    elevation = check_raster_exists(options["elevation"])

    # Optional options
    streams = (
        options["streams"]
        if options["streams"]
        else generate_temp_raster_name("streams")
    )
    direction = (
        options["direction"]
        if options["direction"]
        else generate_temp_raster_name("direction")
    )
    hand = options["hand"] if options["hand"] else generate_temp_raster_name("hand")
    threshold = int(options["threshold"])

    # r.lake options
    depth = float(options["depth"]) if options["depth"] else None
    inundation_raster = options["inundation_raster"]

    # r.lake.series options
    inundation_series = flags["t"]
    start_water_level = (
        float(options["start_water_level"]) if options["start_water_level"] else None
    )
    end_water_level = (
        float(options["end_water_level"]) if options["end_water_level"] else None
    )
    water_level_step = float(options["water_level_step"])
    inundation_strds = options["inundation_strds"]

    # Compuational Options
    memory = options["memory"]
    swap_mode = flags["m"]
    swap_mode_flags = ""
    if swap_mode:
        gs.message(_("Using memory swap mode"))
        swap_mode_flags = "m"

    # Check if elevation, stram_rast, and direction are provided
    run_r_watershed(elevation, streams, direction, threshold, memory, swap_mode_flags)
    run_stream_distance(streams, direction, elevation, hand, memory, swap_mode_flags)
    set_hand_colors(hand)
    set_hand_categories(hand)

    if inundation_series:
        check_addon_installed("r.lake.series", fatal=False)
        run_r_lake_series(
            hand,
            start_water_level,
            end_water_level,
            water_level_step,
            inundation_strds,
            streams,
        )
    else:
        run_r_lake(hand, depth, inundation_raster, streams)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
