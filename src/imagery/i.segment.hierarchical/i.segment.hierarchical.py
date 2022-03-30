#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:	    i.segment.hierarchical
#
# AUTHOR(S):   Pietro Zambelli (University of Trento)
#
# COPYRIGHT:	(C) 2013 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %Module
# % description: Hierarchical segmentation
# % keyword: imagery
# % keyword: segment
# % overwrite: yes
# %End
# %option G_OPT_I_GROUP
# % key: group
# % description: Name of input imagery group
# % required: yes
# %end
# %option
# % key: thresholds
# % type: double
# % multiple: yes
# % description: Segment thresholds
# % required: yes
# % answer: 0.02,0.05
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Name of output sement raster map
# % required: yes
# %end
# %option
# % key: outputs_prefix
# % type: string
# % description: Name for output raster maps from segment
# % required: no
# % answer: seg__%.2f
# %end
# %option
# % key: method
# % type: string
# % description: Segmentation method
# % required: no
# % answer: region_growing
# % guisection: Segment
# %end
# %option
# % key: similarity
# % type: string
# % description: Similarity calculation method
# % required: no
# % answer: euclidean
# % guisection: Segment
# %end
# %option
# % key: minsizes
# % type: integer
# % description: Minimum number of cells in a segment
# % multiple: yes
# % required: no
# % guisection: Segment
# %end
# %option
# % key: memory
# % type: integer
# % description: Memory in MB
# % required: no
# % answer: 300
# % guisection: Segment
# %end
# %option
# % key: iterations
# % type: integer
# % description: Maximum number of iterations
# % required: no
# % answer: 20
# % guisection: Segment
# %end
# %option G_OPT_R_INPUT
# % key: seeds
# % description: Name for input raster map with starting seeds
# % required: no
# % guisection: Segment
# %end
# %option G_OPT_R_INPUT
# % key: bounds
# % description: Name of input bounding/constraining raster map
# % required: no
# % guisection: Segment
# %end
# %option
# % key: width
# % description: Tile width in pixels
# % type: integer
# % required: no
# % guisection: Grid
# %end
# %option
# % key: height
# % description: Tile height in pixels
# % type: integer
# % required: no
# % guisection: Grid
# %end
# %option
# % key: overlap
# % description: Tile overlap in pixels
# % type: integer
# % required: no
# % answer: 0
# % guisection: Grid
# %end
# %option
# % key: processes
# % description: Number of concurrent processes
# % type: integer
# % required: no
# % guisection: Grid
# %end
# %option
# % key: move
# % description: Path where move and copy the mapset
# % type: string
# % required: no
# % guisection: Grid
# %end


from __future__ import print_function
import multiprocessing as mltp
import time
import sys

from grass.script.core import parser
from grass.pygrass.modules import Module
from grass.pygrass.modules.grid import GridModule
from grass.pygrass.modules.grid.grid import copy_rasters
from grass.pygrass.modules.grid.split import split_region_tiles

from grass.pygrass.gis import Location
from grass.pygrass.utils import set_path

set_path("i.segment.hierarchical")
from isegpatch import rpatch_map


DEBUG = False


class SegModule(GridModule):
    """Extend the GridModule class, modifying the patch method."""

    def __init__(self, *args, **kwargs):
        self.memory = kwargs["memory"]
        super(SegModule, self).__init__(*args, **kwargs)

    def patch(self):
        """Patch the final results."""
        # make all mapset in the location visible
        loc = Location()
        mset = loc[self.mset.name]
        mset.current()
        mset.visible.extend(loc.mapsets())
        # patch all the outputs
        bboxes = split_region_tiles(width=self.width, height=self.height)
        inputs = self.module.inputs
        print("Start patching the segments")
        start = time.time()
        rpatch_map(
            inputs.outputs_prefix % inputs.thresholds[-1],
            self.mset.name,
            self.msetstr,
            bboxes,
            self.module.flags.overwrite,
            self.start_row,
            self.start_col,
            self.out_prefix,
        )
        print("%s, required: %.2fs" % (OPTS["output"], time.time() - start))

        # segment
        print("Start running segment for the last time in the whole region")
        start = time.time()
        iseg = Module("i.segment")
        threshold = self.module.inputs.thresholds[-1]
        iseg(
            group=self.module.inputs.group,
            output=self.module.outputs.output,
            threshold=threshold,
            method=self.module.inputs.method,
            similarity=self.module.inputs.similarity,
            minsize=self.module.inputs.minsizes[-1],
            memory=self.memory,
            iterations=3,
            seeds=self.module.inputs.outputs_prefix % threshold,
        )
        print("%s, required: %.2fs" % (OPTS["output"], time.time() - start))

        self.mset.current()
        if self.move:
            copy_rasters(
                [
                    self.module.outputs.output,
                ],
                self.gisrc_dst,
                self.gisrc_src,
            )


def segment(thresholds, minsizes, output="seg__%.2f", **opts):
    """Call the i.segment module hierarchical"""
    iseg = Module("i.segment")
    seeds = opts["seeds"] if opts["seeds"] else None
    for thr, msize in zip(thresholds, minsizes):
        opts["threshold"] = thr
        opts["minsize"] = msize
        opts["seeds"] = seeds
        opts["flags"] = FLAGS
        opts["output"] = output % thr
        start = time.time()
        iseg(**opts)
        print("%s, required: %.2fs" % (opts["output"], time.time() - start))
        seeds = opts["output"]  # update seeds


if __name__ == "__main__":
    OPTS, FLAGS = parser()
    WIDTH = OPTS.pop("width")
    HEIGHT = OPTS.pop("height")
    OVERLAP = OPTS.pop("overlap")
    MOVE = OPTS.pop("move")
    MOVE = MOVE if MOVE else None
    PROCESSES = OPTS.pop("processes")
    PROCESSES = int(PROCESSES) if PROCESSES else mltp.cpu_count()
    MEMORY = int(OPTS["memory"])
    THRS = [float(thr) for thr in OPTS["thresholds"].split(",") if thr]
    if OPTS["minsizes"]:
        MINSIZES = [int(m) for m in OPTS["minsizes"].split(",") if m]
        if len(MINSIZES) != len(THRS):
            MINSIZES = [
                int(MINSIZES[0]),
            ] * len(THRS)
    else:
        MINSIZES = [
            1,
        ] * len(THRS)

    # define new cleaned parameters
    OPTS["thresholds"] = THRS
    OPTS["minsizes"] = MINSIZES
    OPTS["iterations"] = int(OPTS["iterations"])
    OPTS["memory"] = MEMORY / PROCESSES
    if WIDTH and HEIGHT:
        SEG = SegModule(
            "i.segment.hierarchical",
            width=int(WIDTH),
            height=int(HEIGHT),
            overlap=int(OVERLAP),
            processes=PROCESSES,
            move=MOVE,
            debug=DEBUG,
            **OPTS,
        )
        SEG.run()
    else:
        OPTS.pop("output")
        segment(
            OPTS.pop("thresholds"),
            OPTS.pop("minsizes"),
            output=OPTS.pop("outputs_prefix"),
            **OPTS,
        )
