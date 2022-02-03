#!/usr/bin/env python

############################################################################
#
# MODULE:	r.texture.tiled
# AUTHOR(S):	Moritz Lennert
#
# PURPOSE:	Run r.texture over tiles of the input map
#               to allow parallel processing
# COPYRIGHT:	(C) 1997-2018 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#############################################################################

# %Module
# % description: Runs r.texture in parallel over tiles
# % keyword: raster
# % keyword: texture
# % keyword: tiling
# %end
#
# %option G_OPT_R_INPUT
# % required: yes
# %end
#
# %option G_OPT_R_BASENAME_OUTPUT
# % required: yes
# %end
#
# %option
# % key: method
# % type: string
# % description: Texture method to apply
# % required: yes
# % multiple: no
# % options: asm,contrast,corr,var,idm,sa,sv,se,entr,dv,de,moc1,moc2
# %end
#
# %option
# % key: size
# % type: integer
# % description: The size of moving window (odd and >= 3)
# % answer: 3
# % required: yes
# %end
#
# %option
# % key: distance
# % type: integer
# % label: The distance between two samples (>= 1)
# % description: The distance must be smaller than the size of the moving window
# % answer: 1
# % required: yes
# %end
#
# %option
# % key: tile_width
# % type: integer
# % description: Width of tiles
# % answer: 1000
# % required: yes
# %end
#
# %option
# % key: tile_height
# % type: integer
# % description: Height of tiles
# % answer: 1000
# % required: yes
# %end
#
# %option
# % key: processes
# % type: integer
# % description: Number of parallel processes
# % answer: 1
# % required: yes
# %end
#
# %option
# % key: mapset_prefix
# % type: string
# % description: Mapset prefix
# % required: no
# %end


import math
import grass.script as gscript
from grass.pygrass.modules.grid.grid import *


class MyGridModule(GridModule):
    """inherit GridModule, but handle the specific output naming of r.texture"""

    def patch(self):
        """Patch the final results."""
        bboxes = split_region_tiles(width=self.width, height=self.height)
        loc = Location()
        methods_dic = {
            "asm": "ASM",
            "contrast": "Contr",
            "corr": "Corr",
            "var": "Var",
            "idm": "IDM",
            "sa": "SA",
            "sv": "SV",
            "se": "SE",
            "entr": "Entr",
            "dv": "DV",
            "de": "DE",
            "moc1": "MOC-1",
            "moc2": "MOC-2",
        }
        mset = loc[self.mset.name]
        mset.visible.extend(loc.mapsets())
        method = self.module.inputs["method"].value[0]
        for otmap in self.module.outputs:
            otm = self.module.outputs[otmap]
            if otm.typedesc == "raster" and otm.value:
                otm.value = "%s_%s" % (otm.value, methods_dic[method])
                rpatch_map(
                    otm.value,
                    self.mset.name,
                    self.msetstr,
                    bboxes,
                    self.module.flags.overwrite,
                    self.start_row,
                    self.start_col,
                    self.out_prefix,
                )


def main():

    inputraster = options["input"]
    outputprefix = options["output"]
    windowsize = int(options["size"])
    distance = int(options["distance"])
    texture_method = options["method"]
    width = int(options["tile_width"])
    height = int(options["tile_height"])
    overlap = math.ceil(windowsize / 2.0)
    processes = int(options["processes"])
    mapset_prefix = None
    if options["mapset_prefix"]:
        mapset_prefix = options["mapset_prefix"]

    kwargs = {
        "input": inputraster,
        "output": outputprefix,
        "size": windowsize,
        "distance": distance,
        "method": texture_method,
        "flags": "n",
        "quiet": True,
    }

    grd = MyGridModule(
        "r.texture",
        width=width,
        height=height,
        overlap=overlap,
        processes=processes,
        split=False,
        mapset_prefix=mapset_prefix,
        **kwargs
    )
    grd.run()


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
