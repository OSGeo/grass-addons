#!/usr/bin/env python3

"""
 MODULE:       r.buildvrt.gdal
 AUTHOR(S):    Stefan Blumentrath
 PURPOSE:      Build GDAL Virtual Rasters (VRT) over GRASS GIS raster maps
 COPYRIGHT:    (C) 2024 by stefan.blumentrath, and the GRASS Development Team

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

"""

# %module
# % description: Build GDAL Virtual Rasters (VRT) over GRASS GIS raster maps
# % keyword: raster
# % keyword: virtual
# % keyword: gdal
# % keyword: patch
# %end

# %option G_OPT_R_INPUTS
# % key: input
# % type: string
# % required: no
# % multiple: yes
# %end

# %option G_OPT_F_INPUT
# % key: file
# % required: no
# %end

# %option G_OPT_M_DIR
# % key: vrt_directory
# % description: Directory to store GDAL VRT files in. Default is: $GISDBASE/$PROJECT/$MAPSET/gdal
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# %end

# %flag
# % key: m
# % label: Read data range from metadata
# % description: WARNING: metadata are sometimes approximations with wrong data range
# %end

# %flag
# % key: r
# % label: Create fast link without data range
# % description: WARNING: some modules do not work correctly without known data range
# %end

# %rules
# % required: input,file
# % exclusive: input,file
# % exclusive: -m,-r
# %end


import json
import sys

from pathlib import Path

import grass.script as gs


def get_raster_gdalpath(
    map_name, check_linked=True, has_grassdriver=False, gis_env=None
):
    """Get the GDAL-readable path to a GRASS GIS raster map

    Returns either the link stored in the GDAL-link file in the cell_misc
    directory for raster maps linked with r.external or r.external.out
    - if requested - or the path to the header of the GRASS GIS raster
    map"""
    if check_linked:
        # Check GDAL link header
        map_info = gs.find_file(map_name)
        header_path = (
            Path(gis_env["GISDBASE"])
            / gis_env["LOCATION_NAME"]
            / map_info["mapset"]
            / "cell_misc"
            / map_info["name"]
            / "gdal"
        )
        if header_path.is_file():
            gdal_path = Path(
                gs.parse_key_val(header_path.read_text(), sep=": ")["file"]
            )
            if gdal_path.exists():
                return str(gdal_path)

    # Get native GRASS GIS format header
    if not has_grassdriver:
        gs.fatal(
            _(
                "The GDAL-GRASS GIS driver is unavailable. "
                "Cannot create GDAL VRTs for map <{}>. "
                "Please install the GDAL-GRASS plugin."
            ).format(map_name)
        )

    gdal_path = Path(gs.find_file(map_name)["file"].replace("/cell/", "/cellhd/"))
    if gdal_path.is_file():
        return gdal_path

    # Fail if file path cannot be determined
    gs.fatal(_("Cannot determine GDAL readable path to raster map {}").format(map_name))


def main():
    """run the main workflow"""
    options, flags = gs.parser()

    # lazy imports
    global gdal
    try:
        from osgeo import gdal

        gdal.UseExceptions()
    except ImportError:
        gs.fatal(
            _(
                "Unable to load GDAL Python bindings (requires "
                "package 'python-gdal' or Python library GDAL "
                "to be installed)."
            )
        )

    # Check if GRASS GIS driver is available
    has_grassdriver = True
    if not gdal.GetDriverByName("GRASS"):
        has_grassdriver = False

    # Get GRASS GIS environment info
    gisenv = gs.gisenv()

    # Get inputs
    if options["input"]:
        inputs = options["input"].split(",")
    else:
        inputs = Path(options["file"]).read_text(encoding="UTF8").strip().split("\n")

    if len(inputs) < 1:
        gs.fatal(_("At least one input map is required".format(inputs[0])))

    inputs = [
        get_raster_gdalpath(raster_map, has_grassdriver=has_grassdriver, gis_env=gisenv)
        for raster_map in inputs
    ]

    # Get output
    output = options["output"]

    # Create a directory to place GDAL VRTs in
    if options["vrt_directory"]:
        vrt_dir = Path(options["vrt_directory"])
    else:
        vrt_dir = Path(gisenv["GISDBASE"]).joinpath(
            gisenv["LOCATION_NAME"], gisenv["MAPSET"], "gdal"
        )
    vrt_dir.mkdir(exist_ok=True, parents=True)

    # Create GDAL VRT
    vrt_path = str(vrt_dir / f"{output}.vrt")
    gs.verbose(_("Creating GDAL VRT '{}'.").format(vrt_path))
    try:
        gdal.BuildVRT(vrt_path, inputs)
    except OSError:
        gs.fatal(
            _("Failed to build VRT {vrt} with inputs <{in_files}>").format(
                vrt=vrt_path, in_file=", ".join(inputs)
            )
        )

    # Import (link) GDAL VRT
    gs.run_command(
        "r.external",
        quiet=True,
        flags=f"oa{''.join([key for key, val in flags.items() if val])}",
        input=str(vrt_path),
        output=output,
    )
    gs.raster_history(output, overwrite=True)


if __name__ == "__main__":

    sys.exit(main())
