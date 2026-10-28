#!/usr/bin/env python3
# %module
# % description: Collection of terrain-analysis modules wrapping RichDEM.
# % keyword: raster
# % keyword: hydrology
# % keyword: terrain
# % keyword: elevation
# %end

import grass.script as gs


def main():
    gs.message(
        "r.richdem is a collection of seven terrain-analysis modules\n"
        "wrapping the RichDEM library. Run each module individually:\n\n"
        "  r.richdem.filldepressions  - fill depressions (Priority-Flood)\n"
        "  r.richdem.breachdepressions - breach depressions\n"
        "  r.richdem.resolveflats     - impose epsilon gradient on flat areas\n"
        "  r.richdem.flowaccumulation - flow accumulation (D8, D-inf, ...)\n"
        "  r.richdem.terrainattribute - slope, aspect, curvature\n"
        "  r.richdem.dephier          - compute depression hierarchy\n"
        "  r.richdem.fsm              - Fill-Spill-Merge surface-water routing"
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
