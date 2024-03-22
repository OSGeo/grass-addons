#!/usr/bin/env python

############################################################################
#
# MODULE:       r.in.ahn
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Imports the 0.5 meter resolution dtm or dsm from the AHN
#               (Actueel Hoogtebestand Nederland (AHN), version 4.
#
# COPYRIGHT:    (c) 2024 Paulo van Breugel, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Imports the 0.5 meter resolution dtm or dsm from the AHN (Actueel Hoogtebestand Nederland (AHN), version 4.
# % keyword: dem
# % keyword: raster
# % keyword: import
# %end

# %option
# % key: product
# % type: string
# % label: product
# % description: Choose which product to download (dsm or dtm)
# % options: dsm, dtm
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# %end

# %flag
# % key: t
# % label: Download whole tiles
# % description: Download the selected product for the AHN tile that overlap with the current region. If enabled, a vector layer with the bounds of the AHN tiles will be saved, using the output name with as suffix _tiles
# %end

# %flag
# % key: g
# % label: Set to original computational region
# % description: After downloading and importing the requested layer, set the region back to the original computation region.
# %end


import atexit
import sys
import grass.script as gs
from math import floor

# create set to store names of temporary maps to be deleted upon exit
CLEAN_LAY = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    maps = reversed(CLEAN_LAY)
    mapset = gs.gisenv()["MAPSET"]
    for map_name in maps:
        for element in ("raster", "vector"):
            found = gs.find_file(name=map_name, element=element, mapset=mapset)
            if found["file"]:
                gs.run_command(
                    "g.remove", flags="f", type=element, name=map_name, quiet=True
                )
    gs.del_temp_region()


def create_temporary_name(prefix):
    tmpf = gs.append_node_pid(prefix)
    CLEAN_LAY.append(tmpf)
    return tmpf


def main(options, flags):
    """
    Download the dtm or dsm from AHN
    """

    # Check if the projection is RD New (EPSG:28992)
    proj_info = gs.parse_command("g.proj", flags="g")
    if proj_info["srid"] != "EPSG:28992" and proj_info["name"] != "Amersfoort / RD New":
        gs.fatal(_("This module only works with locations with projection EPSG=28992"))

    # Check if wcs addon is installed.
    try:
        gs.find_program("r.in.wcs")
    except Exception as e:
        gs.fatal(_("The addon r.in.wcs is not installed. Exit"))

    # Get coordinates current region extent
    if flags["g"]:
        gs.use_temp_region()
    region_current = gs.parse_command("g.region", flags="gu")

    # Create a polygon grid layer with cells that match the AHN  6.5x5 km 'kaartbladen'
    if flags["t"]:
        regionvector = create_temporary_name("regionvector_")
        tilesvector = create_temporary_name("tilesvector_")
        selectedtiles = f"{options['output']}_tiles"
        region_vector = gs.parse_command("v.in.region", output=regionvector)
        gs.run_command("g.region", n=618750, s=306250, w=10000, e=280000, res=0.5)
        gs.run_command("v.mkgrid", map=tilesvector, grid=[50, 54])
        gs.run_command(
            "v.select",
            ainput=tilesvector,
            binput=regionvector,
            output=selectedtiles,
            operator="overlap",
        )
        gs.run_command("g.region", vector=selectedtiles)
        gs.message(
            "Created the vector layer {} with AHN tiles overlapping with the current region."
            "\nThe region is set to match the extent of this layer".format(
                selectedtiles
            ),
        )
    else:
        # Set region to match that of the AHN tiles
        n = 618750 - floor(618750 - float(region_current["n"]))
        s = 306250 + floor(float(region_current["s"]) - 306250)
        w = 10000 + floor(float(region_current["w"]) - 10000)
        e = 280000 - floor(280000 - float(region_current["e"]))
        gs.run_command("g.region", n=n, s=s, e=e, w=w, res=0.5)
        gs.message(
            "The region's extent and resolution have been changed "
            "\nto match the extent and resolution of the requested "
            "\nAHN raster layer",
        )

    # Import the requested product (dtm or dsm)
    gs.message("Downloading and importing the requested raster layer ... ")
    gs.run_command(
        "r.in.wcs",
        url="https://service.pdok.nl/rws/ahn/wcs/v1_0?",
        coverage=f"{options['product']}_05m",
        urlparams="GetMetadata",
        output=options["output"],
    )
    gs.message("Creating the NULL values ...")
    expr = "{0} = if({0} > 999999, null(), {0})".format(options["output"])
    gs.run_command("r.mapcalc", expression=expr, overwrite=True)
    gs.run_command("r.colors", map=options["output"], color="elevation")
    gs.raster.raster_history(map=options["output"], overwrite=True)
    gs.run_command(
        "r.support",
        map=options["output"],
        title=f"{options['product']}_05m AHN version 4",
        units="meters",
        source1="https://www.ahn.nl/ahn-4",
    )
    gs.run_command(
        "r.support",
        map=options["output"],
        history="The main steps by r.in.ahn are:",
    )
    hist_wcs = (
        f"r.in.wcs url='https://service.pdok.nl/rws/ahn/wcs/v1_0?' "
        f"coverage={options['product']}_05m urlparams=GetMetadata output={options['output']}"
    )
    gs.run_command("r.support", map=options["output"], history=hist_wcs)
    hist_mapcalc = f"r.mapcalc expression={expr}"
    gs.run_command("r.support", map=options["output"], history=hist_mapcalc)
    gs.message(
        "The AHN {} has been downloaded and imported as {}".format(
            options["product"], options["output"]
        ),
    )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
