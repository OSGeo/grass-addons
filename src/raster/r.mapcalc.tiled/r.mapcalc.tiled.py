#!/usr/bin/env python

############################################################################
#
# MODULE:	r.mapcalc.tiled
# AUTHOR(S):	Moritz Lennert
#
# PURPOSE:	Run r.mapcalc over tiles of the input map
#               to allow parallel processing
# COPYRIGHT:	(C) 2019 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#############################################################################

# %Module
# % description: Runs r.mapcalc in parallel over tiles.
# % keyword: raster
# % keyword: algebra
# % keyword: tiling
# %end
#
# %option
# % key: expression
# % type: string
# % description: Expression to send to r.mapcalc
# % required: yes
# %end
#
# %option G_OPT_R_OUTPUT
# % description: Name of raster output map resulting from expression
# % key: output
# % required : no
# %end
#
# %option
# % key: width
# % type: integer
# % description: Width of tiles (columns)
# % required: no
# %end
#
# %option
# % key: height
# % type: integer
# % description: Height of tiles (rows)
# % required: no
# %end
#
# %option
# % key: overlap
# % type: integer
# % description: Overlap of tiles
# % answer: 0
# % required: yes
# %end
#
# %option
# % key: nprocs
# % type: integer
# % description: Number of r.mapcalc processes to run in parallel
# % required: no
# % options: 1-
# %end
#
# %option
# % key: processes
# % type: integer
# % description: Number of r.mapcalc processes to run in parallel, use nprocs option instead
# % label: This option is obsolete and replaced by nprocs
# % required: no
# % options: 1-
# %end
#
# %option
# % key: mapset_prefix
# % type: string
# % description: Mapset prefix
# % required: no
# %end
#
# %option
# % key: patch_backend
# % type: string
# % label: Backend for patching computed tiles
# % description: If backend is not specified, original serial implementation with RasterRow is used
# % options: RasterRow,r.patch
# % descriptions: RasterRow; serial patching with PyGRASS RasterRow; r.patch; parallelized r.patch (with zero overlap only)
# % required: no
# %end
#
# %rules
# % exclusive: processes,nprocs
# %end

import grass.script as gscript
from grass.pygrass.modules.grid.grid import (
    GridModule,
    Location,
    split_region_tiles,
    rpatch_map,
)

try:
    parallel_rpatch_available = True
    from grass.pygrass.modules.grid.grid import rpatch_map_r_patch_backend
except ImportError:
    parallel_rpatch_available = False


class MyGridModule(GridModule):
    """inherit GridModule, but handle the fact that the output name is in the expression"""

    def patch(self):
        """Patch the final results."""
        bboxes = split_region_tiles(width=self.width, height=self.height)
        loc = Location()
        mset = loc[self.mset.name]
        mset.visible.extend(loc.mapsets())
        output_map = self.out_prefix[:]
        self.out_prefix = ""
        if self.patch_backend == "RasterRow":
            rpatch_map(
                raster=output_map,
                mapset=self.mset.name,
                mset_str=self.msetstr,
                bbox_list=bboxes,
                overwrite=self.module.flags.overwrite,
                start_row=self.start_row,
                start_col=self.start_col,
                prefix=self.out_prefix,
            )
        else:
            rpatch_map_r_patch_backend(
                raster=output_map,
                mset_str=self.msetstr,
                bbox_list=bboxes,
                overwrite=self.module.flags.overwrite,
                start_row=self.start_row,
                start_col=self.start_col,
                prefix=self.out_prefix,
                processes=self.processes,
            )


def main():

    expression = options["expression"]
    width = options["width"]
    height = options["height"]
    # v8.2 GridModule doesn't require tile size anymore
    # this is proxy for v8.2
    # can be removed in v9.0
    if not parallel_rpatch_available:
        warning = False
        if not width:
            width = 1000
            warning = True
        else:
            width = int(width)
        if not height:
            height = 1000
            warning = True
        else:
            height = int(height)
        if warning:
            # square tiles tend to be slower than horizontal slices
            gscript.warning(
                _(
                    "No tile width or height provided, default tile size set: {h} rows x {w} cols."
                ).format(h=height, w=width)
            )
    overlap = int(options["overlap"])
    processes = options["nprocs"]
    patch_backend = options["patch_backend"]
    if not processes:
        processes = options["processes"]
        if processes:
            gscript.warning(_("Option processes is obsolete, use nprocs instead."))
    try:
        processes = int(processes)
    except ValueError:
        processes = 1

    output = None
    if options["output"]:
        output = options["output"]
    mapset_prefix = None
    if options["mapset_prefix"]:
        mapset_prefix = options["mapset_prefix"]

    kwargs = {"expression": expression, "quiet": True}

    if not parallel_rpatch_available and patch_backend == "r.patch":
        gs.warning(
            _(
                "r.patch backend is not available in this version of GRASS GIS, using RasterRow"
            )
        )
    if patch_backend == "r.patch" and overlap > 0:
        gs.fatal(_("Patching backend 'r.patch' doesn't work for overlap > 0"))
    if parallel_rpatch_available:
        kwargs["patch_backend"] = patch_backend

    if output:
        output_mapname = output
    else:
        output_mapname = expression.split("=")[0].strip()

    grd = MyGridModule(
        "r.mapcalc",
        width=width,
        height=height,
        overlap=overlap,
        processes=processes,
        split=False,
        mapset_prefix=mapset_prefix,
        out_prefix=output_mapname,
        **kwargs,
    )
    grd.run()


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
