#!/usr/bin/env python

#
##############################################################################
#
# MODULE:       r.patch.smooth
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      Patch raster and smooth along edges
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

# %module
# % description: Module for patching rasters with smoothing along edges
# % keyword: raster
# % keyword: patch
# %end
# %option G_OPT_R_INPUT
# % key: input_a
# % label: Name for input raster map A
# %end
# %option G_OPT_R_INPUT
# % key: input_b
# % label: Name for input raster map B
# %end
# %option G_OPT_R_OUTPUT
# %end
# %option G_OPT_R_OUTPUT
# % key: overlap
# % label: Name for raster map of spatially variable overlap
# % required: no
# %end
# %option
# % type: string
# % key: blend_mask
# % label: Raster containing edge of raster A which is not to be blended
# % description: Useful when raster A has common edge with raster B
# % required: no
# % guisection: Settings
# %end
# %option
# % type: double
# % key: smooth_dist
# % description: Smoothing distance in map units
# % required: no
# % guisection: Settings
# %end
# %option
# % type: double
# % key: transition_angle
# % label: Angle of transition for spatially variable overlap
# % description: Recommended values between 1 and 5 degrees
# % required: no
# % guisection: Settings
# %end
# %option
# % type: integer
# % key: parallel_smoothing
# % label: Size of smoothing window for smoothing edges of spatially variable overlap zone
# % description: Small value results in more rugged shape of the overlap zone, large values result in spatially non-variable overlap zone. Requires odd values.
# % answer: 9
# % options: 3-99
# % required: no
# % guisection: Settings
# %end
# %option
# % type: integer
# % key: difference_reach
# % label: Look for maximum difference between surfaces in surrounding n cells from the edge
# % description: Recommended values between 3 and 9
# % answer: 3
# % options: 2-100
# % required: no
# % guisection: Settings
# %end
# %flag
# % key: s
# % description: Use spatially variable overlap
# % guisection: Settings
# %end
# %rules
# % collective: -s,transition_angle
# % exclusive: transition_angle,smooth_dist
# % required: -s,smooth_dist
# % excludes: smooth_dist,overlap
# %end

import os
import sys
import atexit

import grass.script as gscript


TMP = []


def cleanup():
    gscript.run_command(
        "g.remove", flags="f", type=["raster", "vector"], name=TMP, quiet=True
    )


def main():
    input_A = options["input_a"]
    input_B = options["input_b"]
    output = options["output"]
    overlap = options["overlap"]
    smooth_dist = options["smooth_dist"]
    angle = options["transition_angle"]
    blend_mask = options["blend_mask"]
    simple = not flags["s"]
    # smooth values of closest difference
    smooth_closest_difference_size = int(options["parallel_smoothing"])
    if smooth_closest_difference_size % 2 == 0:
        gscript.fatal(_("Option 'parallel_smoothing' requires odd number"))
    difference_reach = int(options["difference_reach"])

    postfix = str(os.getpid())
    tmp_absdiff = "tmp_absdiff_" + postfix
    tmp_absdiff_smooth = "tmp_absdiff_smooth" + postfix
    tmp_grow = "tmp_grow" + postfix
    tmp_diff_overlap_1px = "tmp_diff_overlap_1px" + postfix
    tmp_value = "tmp_value" + postfix
    tmp_value_smooth = "tmp_value_smooth" + postfix
    tmp_stretch_dist = "tmp_stretch_dist" + postfix
    tmp_overlap = "tmp_overlap" + postfix
    TMP.extend(
        [
            tmp_absdiff,
            tmp_absdiff_smooth,
            tmp_grow,
            tmp_diff_overlap_1px,
            tmp_value,
            tmp_value_smooth,
            tmp_stretch_dist,
            tmp_overlap,
        ]
    )

    gscript.run_command("r.grow.distance", flags="n", input=input_A, distance=tmp_grow)
    if simple and blend_mask:
        tmp_mask1 = "tmp_mask1"
        tmp_mask2 = "tmp_mask2"
        tmp_mask3 = "tmp_mask3"
        tmp_mask4 = "tmp_mask4"
        TMP.extend([tmp_mask1, tmp_mask2, tmp_mask3, tmp_mask4])
        # derive 1-pixel wide edge of A inside of the provided mask
        gscript.mapcalc(
            "{new} = if ({dist} > 0 && {dist} <= 1.5*nsres() && ! isnull({blend_mask}), 1, null())".format(
                new=tmp_mask1, dist=tmp_grow, blend_mask=blend_mask
            )
        )
        # create buffer around it
        gscript.run_command(
            "r.grow",
            input=tmp_mask1,
            output=tmp_mask2,
            flags="m",
            radius=smooth_dist,
            old=1,
            new=1,
        )
        # patch the buffer and A
        gscript.mapcalc(
            "{new} = if(! isnull({mask2}) || ! isnull({A}), 1, null())".format(
                A=input_A, mask2=tmp_mask2, new=tmp_mask3
            )
        )
        # inner grow
        gscript.run_command(
            "r.grow.distance", flags="n", input=tmp_mask3, distance=tmp_mask4
        )
        # replace the distance inside the buffered area with 0
        gscript.mapcalc(
            "{new} = if(! isnull({A}), {m4}, 0)".format(
                new=tmp_grow, A=input_A, m4=tmp_mask4
            ),
            overwrite=True,
        )

    if simple:
        gscript.mapcalc(
            "{out} = if({grow} > {smooth}, {A}, if({grow} == 0, {B},"
            "if (isnull({B}) && ! isnull({A}), {A},"
            "(1 - {grow}/{smooth}) * {B} + ({grow}/{smooth} * {A}))))".format(
                out=output, grow=tmp_grow, smooth=smooth_dist, A=input_A, B=input_B
            )
        )
        return

    # difference
    gscript.mapcalc(
        "{new} = abs({A} - {B})".format(new=tmp_absdiff, A=input_A, B=input_B)
    )

    # take maximum difference from near cells
    difference_reach = (difference_reach - 1) * 2 + 1
    gscript.run_command(
        "r.neighbors",
        flags="c",
        input=tmp_absdiff,
        output=tmp_absdiff_smooth,
        method="maximum",
        size=difference_reach,
    )

    # closest value of difference
    if blend_mask:
        # set the edge pixels to almost 0 where the mask is, results in no blending
        gscript.mapcalc(
            "{new} = if ({dist} > 0 && {dist} <= 1.5*nsres(), if(isnull({blend_mask}), {diff}, 0.00001), null())".format(
                new=tmp_diff_overlap_1px,
                dist=tmp_grow,
                diff=tmp_absdiff_smooth,
                blend_mask=blend_mask,
            )
        )
    else:
        gscript.mapcalc(
            "{new} = if ({dist} > 0 && {dist} <= 1.5*nsres(), {diff}, null())".format(
                new=tmp_diff_overlap_1px, dist=tmp_grow, diff=tmp_absdiff_smooth
            )
        )
    # closest value of difference
    gscript.run_command("r.grow.distance", input=tmp_diff_overlap_1px, value=tmp_value)

    # smooth closest value
    gscript.run_command(
        "r.neighbors",
        flags="c",
        input=tmp_value,
        output=tmp_value_smooth,
        method="average",
        size=smooth_closest_difference_size,
    )

    # stretch 10cm height difference per 5 meters
    gscript.mapcalc(
        "{stretch} = {value}/tan({alpha})".format(
            stretch=tmp_stretch_dist, value=tmp_value_smooth, alpha=angle
        )
    )

    # spatially variable overlap width s
    gscript.mapcalc(
        "{s} = if (isnull({B}) && ! isnull({A}), 1, {dist} / {stretch})".format(
            s=tmp_overlap, B=input_B, A=input_A, dist=tmp_grow, stretch=tmp_stretch_dist
        )
    )
    # fusion
    gscript.mapcalc(
        "{fused} = if({s} >= 1, {A} , if({s} == 0,  {B},  (1 - {s}) * {B} +  {A} * {s}))".format(
            fused=output, s=tmp_overlap, B=input_B, A=input_A
        )
    )
    # visualize overlap
    if overlap:
        gscript.mapcalc(
            "{s_trim} = if ({s}>=1, null(), if({s}<=0, null(), {s}))".format(
                s_trim=overlap, s=tmp_overlap
            )
        )


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())
