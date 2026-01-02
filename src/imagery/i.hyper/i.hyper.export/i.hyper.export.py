#!/usr/bin/env python

##############################################################################
# MODULE:    i.hyper.export
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Export 3D hyperspectral 3D raster map.
# COPYRIGHT: (C) 2025 by Alen Mangafic and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Export 3D hyperspectral 3D raster map (for now, only available compressed multi-band GeoTIFF)
# % keyword: raster3d
# % keyword: export
# %end

# %option G_OPT_R3_INPUT
# % required: yes
# % description: Input 3D raster map
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % required: yes
# % description: Output file name
# % guisection: Output
# %end

import sys
import grass.script as gs


def main():
    options, flags = gs.parser()
    input_3d_full = options["input"]
    output_file = options["output"]

    input_3d = input_3d_full.split("@")[0]
    base = f"{input_3d}_slice"

    # Set region to match 3D raster
    gs.run_command("g.region", raster_3d=input_3d_full)

    # Convert 3D raster to 2D slices
    gs.run_command("r3.to.rast", input=input_3d_full, output=base, quiet=True)

    # Get the list of slices
    raster_list = gs.parse_command(
        "g.list", type="raster", pattern=f"{base}_*", flags="m"
    )

    def _get_index(rname):
        r = rname.split("@")[0]
        return int(r[len(base) + 1 :])

    raster_list = sorted(raster_list, key=_get_index)

    if not raster_list:
        gs.fatal(f"No valid slice maps found with base name {base}_*")

    # Create imagery group
    group_name = f"{input_3d}_export_group"
    gs.run_command("i.group", group=group_name, input=",".join(raster_list), quiet=True)

    # Set region to the first raster for export
    gs.run_command("g.region", raster=raster_list[0], align=raster_list[0], quiet=True)

    # Export the group as a multi-band GeoTIFF
    gs.run_command(
        "r.out.gdal",
        input=group_name,
        output=output_file,
        format="GTiff",
        createopt="COMPRESS=DEFLATE,PREDICTOR=3,BIGTIFF=YES,INTERLEAVE=BAND",
        nodata=-9999,
        flags="c",
        overwrite=True,
        superquiet=True,
    )

    # Clean up temporary rasters and group
    gs.run_command("g.remove", type="raster", name=raster_list, flags="f", quiet=True)
    gs.run_command("g.remove", type="group", name=group_name, flags="f", quiet=True)

    gs.message(f"Exported {input_3d_full} to {output_file} as multi-band GeoTIFF")


if __name__ == "__main__":
    sys.exit(main())
