#!/usr/bin/env python3

############################################################################
#
# MODULE:	r.neighbors.tiled
# AUTHOR(S):	Steven Pawley
#
# PURPOSE:	Run r.neighbors over tiles of the input map to allow parallel
#           processing
# COPYRIGHT:	(C) 1997-2020 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#############################################################################

#%Module
#% description: Runs r.neighbors in parallel over tiles
#% keyword: raster
#% keyword: neighborhood
#% keyword: focal
#% keyword: tiled
#% keyword: parallel
#%end

#%option G_OPT_R_INPUT
#% required: yes
#%end

#%option G_OPT_R_BASENAME_OUTPUT
#% required: yes
#%end

#%option
#% key: method
#% type: string
#% description: Neighborhood operation.
#% required: yes
#% multiple: no
#% options: average,median,mode,minimum,maximum,range,stddev,sum,count,variance,diversity,interspersion,quart1,quart3,perc90,quantile
#% answer: average
#%end

#%option
#% key: size
#% type: integer
#% description: The size of moving window (odd and >= 3)
#% answer: 3
#% required: yes
#%end

#%option G_OPT_R_INPUT
#% key: selection
#% description: Name of an input raster to select the cells that should be processed
#% required: no
#%end

#%option
#% key: title
#% type: string
#% description: Title for the output map
#% required: no
#%end

#%option G_OPT_F_INPUT
#% key: weight
#% description: Text file containing weights
#% required: no
#%end

#%option
#% key: gauss
#% type: double
#% description: Sigma (in cells) for Gaussian filter
#% required: no
#%end

#%option
#% key: quantile
#% type: double
#% description: Quantile to calculate for method=quantile (>=0 and <= 1)
#% required: no
#% end

#%option
#% key: width
#% type: integer
#% description: Width of tiles
#% answer: 1000
#% required: yes
#%end

#%option
#% key: height
#% type: integer
#% description: Height of tiles
#% answer: 1000
#% required: yes
#%end

#%option
#% key: processes
#% type: integer
#% description: Number of parallel processes (<0 uses all available cores -1, -2 etc.)
#% answer: 1
#% required: yes
#%end

#%option
#% key: mapset_prefix
#% type: string
#% description: Mapset prefix
#% required: no
#%end

#%flag
#% key: c
#% description: Use a circular neighborhood
#%end

#%flag
#% key: a
#% description: Do not align output with input
#%end

import math
import grass.script as gs
# from grass.pygrass.modules.grid.grid import (
#     split_region_tiles,
#     Location,
#     rpatch_map,
#     GridModule,
# )


# class GridModuleMulti(GridModule):
#     """inherit GridModule, but handle the specific output naming of r.neighbors"""

#     def patch(self):
#         """Patch the final results."""
#         bboxes = split_region_tiles(width=self.width, height=self.height)
#         loc = Location()

#         mset = loc[self.mset.name]
#         mset.visible.extend(loc.mapsets())

#         otm = self.module.outputs.pop("output")
#         rpatch_map(
#             otm.value,
#             self.mset.name,
#             self.msetstr,
#             bboxes,
#             self.module.flags.overwrite,
#             self.start_row,
#             self.start_col,
#             self.out_prefix,
#         )

# options = {}
# options["input"] = "esrd_dem_bathy_100m"
# options["output"] = "tmp"
# options["size"] = "3"
# options["method"] = "average"
# options["weight"] = None
# options["selection"] = None
# options["title"] = None
# options["quantile"] = None
# options["gauss"] = None
# options["mapset_prefix"] = None
# options["width"] = 5000
# options["height"] = 5000
# options["processes"] = 1
# flags = {}
# flags["a"] = None
# flags["c"] = None

def main():
    inputraster = options["input"]
    outputraster = options["output"]
    size = int(options["size"])
    method = options["method"]
    weight = options["weight"]
    selection = options["selection"]
    title = options["title"]
    
    gauss = None
    if options["gauss"]:
        gauss = float(options["gauss"])

    quantile = None
    if options["quantile"]:
        quantile = float(options["quantile"])
    
    opts = ""
    if flags["a"]:
        opts = opts + "a"
    
    if flags["c"]:
        opts = opts + "cs"

    mapset_prefix = options["mapset_prefix"]
    width = int(options["width"])
    height = int(options["height"])
    overlap = math.ceil(size / 2.0)
    processes = int(options["processes"])

    kwargs = {
        "input": inputraster,
        "output": outputraster,
        "size": size,
        "method": method,
        "weight": weight,
        "gauss": gauss,
        "quantile": quantile,
        "selection": selection,
        "title": title,
        "flags": flags,
        "quiet": True,
    }

    grd = GridModuleMulti(
        cmd="r.neighbors",
        width=width,
        height=height,
        overlap=overlap,
        processes=processes,
        split=False,
        mapset_prefix=mapset_prefix,
        **kwargs
    )
    param = grd.module.outputs["output"]
    param.multiple = False
    param.value = param.value[0]
    grd.run()



if __name__ == "__main__":
    options, flags = gs.parser()
    main()
