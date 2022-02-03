#!/usr/bin/env python
############################################################################
#
# MODULE:       v.faultdirections
# AUTHOR:       Moritz Lennert
# PURPOSE:      Creates a polar plot of fault directions
#
# COPYRIGHT:    (c) 2016 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Creates a polar plot of fault directions
# % keyword: display
# % keyword: vector
# % keyword: geology
# %end
# %option G_OPT_V_MAP
# %end
# %option G_OPT_DB_COLUMN
# % key: column
# % description: Attribute column containing azimuth
# % required: yes
# %end
# %option
# % key: step
# % type: integer
# % description: Step of binning (in degrees)
# % answer: 10
# % required: no
# %end
# %option
# % key: legend_angle
# % type: double
# % description: Angle at which to put the axis labels
# % answer: 0.0
# % required: no
# %end
# %flag
# % key: a
# % description: Use absolute values in legend, instead of percentages
# %end


import sys
import numpy as np
import grass.script as gscript


def main():
    import matplotlib  # required by windows

    matplotlib.use("wxAGG")  # required by windows
    import matplotlib.pyplot as plt

    vector = options["map"]
    column = options["column"]
    step = int(options["step"])
    legend_angle = float(options["legend_angle"])

    azimuth = []
    for line in gscript.read_command(
        "v.db.select", map_=vector, column=column, flags="c"
    ).splitlines():
        azimuth.append(float(line))

    bins = 360 / step
    az_bins = np.histogram(azimuth, bins=bins, range=(0, 360))
    if flags["a"]:
        radii = az_bins[0]
        label = ""
    else:
        radii = [100.0 * x / sum(az_bins[0]) for x in az_bins[0]]
        label = "%"
    theta = az_bins[1][:-1]
    theta = theta * (np.pi / 180)
    width = 2 * np.pi / bins

    ax = plt.subplot(111, projection="polar")
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2.0)
    unique_radii = [x for x in set(radii) if x > 0]
    range_radii = max(radii) - min(radii)
    if range_radii > 4:
        base = 5 if max(radii) > 10 else 2
        labelstep = np.ceil((range_radii) / 5)
        labelstep = int(base * round(labelstep / base))
        labelradii = [
            x for x in np.arange(0, int(np.ceil(max(radii))), labelstep) if x > 0
        ]
    else:
        labelradii = unique_radii
    ax.set_rgrids(labelradii, angle=legend_angle)
    ax.text(legend_angle * (np.pi / 180), max(radii) * 1.1, label)
    bars = ax.bar(theta, radii, width=width, bottom=0.0)

    # Use custom colors and opacity
    for r, bar in zip(radii, bars):
        bar.set_alpha(0.5)

    plt.show()


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
