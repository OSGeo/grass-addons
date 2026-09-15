#!/usr/bin/env python
############################################################################
#
# MODULE:       r.fusion
#
# AUTHOR(S):    Markus Metz, mundialis
#
# PURPOSE:      Image fusion: similar to pan-sharpening, but more general
#               burn the spatial detail of a high-res raster into a
#               low-res raster, preserving the values of the low-res raster
#
# COPYRIGHT:    (c) 2023 Markus Metz and the GRASS development team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#

# %module
# % description: image fusion, generalized pan-sharpening
# % keyword: raster
# % keyword: imagery
# % keyword: fusion
# % keyword: sharpen
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  description: Low-resolution raster to be enhanced
# %  required: yes
# %end

# %option G_OPT_R_INPUT
# %  key: highres
# %  description: High-resolution raster with spatial detail
# %  required: yes
# %end

# %option
# %  key: method
# %  type: string
# %  description: Solution method: Finite Diff. or Superpos. of analytical sol'ns
# %  options: difference,proportion
# %  answer: difference
# %  required: no
# %end

# %option G_OPT_R_OUTPUT
# %end

# %flag
# %  key: r
# %  label: Restrict output value range to input value range
# %  description: Recommended for imagery with a defined valid value range, e.g. [0, 255]
# %end


import atexit
import os
import sys

import grass.script as gs

# initialize global vars
rm_rasters = []


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}

    # remove temporary raster maps
    for rmrast in rm_rasters:
        if gs.find_file(name=rmrast, element="cell")["file"]:
            gs.run_command("g.remove", type="raster", name=rmrast, **kwargs)


def main():
    lowres_map = options["input"]
    highres_map = options["highres"]
    output_map = options["output"]
    fusion_method = options["method"]
    fit_range = flags["r"]

    gs.use_temp_region()
    current_region = gs.region()

    # get range of lowres raster
    gs.run_command("g.region", align=lowres_map)
    statslr = gs.parse_command(
        "r.univar",
        map=lowres_map,
        flags="g",
    )
    # get info of lowres raster
    infolr = gs.raster_info(lowres_map)

    # get range of highres raster
    gs.run_command(
        "g.region",
        w=current_region["w"],
        s=current_region["s"],
        e=current_region["e"],
        n=current_region["n"],
        ewres=current_region["ewres"],
        nsres=current_region["nsres"],
        quiet=True,
    )
    gs.run_command("g.region", align=highres_map)
    statshr = gs.parse_command(
        "r.univar",
        map=highres_map,
        flags="g",
    )
    # get info of highres raster
    infohr = gs.raster_info(highres_map)

    lrmin = float(statslr["min"])
    lrmax = float(statslr["max"])
    hrmin = float(statshr["min"])
    hrmax = float(statshr["max"])

    # check input for method proportion
    if fusion_method == "proportion":
        if hrmin <= 0:
            gs.fatal(
                "High resolution map must have only positive values for method 'proportion'"
            )
        if lrmin < 0:
            gs.fatal(
                "Low resolution map must have only non-geative values for method 'proportion'"
            )

    last_result = highres_map

    if fusion_method == "difference":
        gs.message(_("Scaling highres map to range of lowres map..."))
        # rescale highres raster to lowres raster
        scale_factor = (lrmax - lrmin) / (hrmax - hrmin)
        # formula: rescaled = (highres - hrmin) * scale_factor + lrmin
        highres_map_scaled = gs.append_node_pid("highres_map_scaled_tmp")
        exp = f"{highres_map_scaled} = ({highres_map} - {hrmin}) * {scale_factor} + {lrmin}"
        gs.mapcalc(exp)
        rm_rasters.append(highres_map_scaled)
        last_result = highres_map_scaled

    # resample highres raster to resolution of lowres raster
    gs.run_command(
        "g.region",
        w=current_region["w"],
        s=current_region["s"],
        e=current_region["e"],
        n=current_region["n"],
        ewres=current_region["ewres"],
        nsres=current_region["nsres"],
        quiet=True,
    )
    gs.run_command("g.region", align=lowres_map)
    highres_map_low = gs.append_node_pid("highres_map_low_tmp")
    gs.run_command(
        "r.resamp.stats", input=last_result, output=highres_map_low, method="median"
    )
    rm_rasters.append(highres_map_low)

    if fusion_method == "difference":
        # difference method: A - B + B = A
        gs.message(_("Applying difference method..."))
        hig_low_diff = gs.append_node_pid("hig_low_diff_tmp")
        exp = f"{hig_low_diff} = {lowres_map} - {highres_map_low}"
        gs.mapcalc(exp)
        rm_rasters.append(hig_low_diff)

        gs.run_command(
            "g.region",
            w=current_region["w"],
            s=current_region["s"],
            e=current_region["e"],
            n=current_region["n"],
            ewres=current_region["ewres"],
            nsres=current_region["nsres"],
            quiet=True,
        )
        gs.run_command("g.region", align=highres_map)

        # interpolate differences
        radius1 = 1.5 * (infolr["nsres"] + infolr["ewres"]) / 2.0
        radius2 = 3.0 * (infolr["nsres"] + infolr["ewres"]) / 2.0
        hig_low_diff_high = gs.append_node_pid("hig_low_diff_high_tmp")
        gs.run_command(
            "r.resamp.filter",
            input=hig_low_diff,
            output=hig_low_diff_high,
            filter="gauss,box",
            radius=f"{radius1},{radius2}",
        )
        rm_rasters.append(hig_low_diff_high)

        # add the interpolated difference to the highres map
        lowres_high = gs.append_node_pid("lowres_high_tmp")
        exp = f"{lowres_high} = {hig_low_diff_high} + {last_result}"
        gs.mapcalc(exp)
        rm_rasters.append(lowres_high)
        last_result = lowres_high
    else:
        # proportion method: A / B * B = A
        gs.message(_("Applying proportion method..."))
        hig_low_prop = gs.append_node_pid("hig_low_prop_tmp")
        exp = f"{hig_low_prop} = float({lowres_map}) / {highres_map_low}"
        gs.mapcalc(exp)
        rm_rasters.append(hig_low_prop)

        gs.run_command(
            "g.region",
            w=current_region["w"],
            s=current_region["s"],
            e=current_region["e"],
            n=current_region["n"],
            ewres=current_region["ewres"],
            nsres=current_region["nsres"],
            quiet=True,
        )
        gs.run_command("g.region", align=highres_map)

        # interpolate proportions
        radius1 = 1.5 * (infolr["nsres"] + infolr["ewres"]) / 2.0
        radius2 = 3.0 * (infolr["nsres"] + infolr["ewres"]) / 2.0
        hig_low_prop_high = gs.append_node_pid("hig_low_prop_high_tmp")
        gs.run_command(
            "r.resamp.filter",
            input=hig_low_prop,
            output=hig_low_prop_high,
            filter="gauss,box",
            radius=f"{radius1},{radius2}",
        )
        rm_rasters.append(hig_low_prop_high)

        # multiply the interpolated proportions with the highres map
        lowres_high = gs.append_node_pid("lowres_high_tmp")
        exp = f"{lowres_high} = {hig_low_prop_high} * {last_result}"
        gs.mapcalc(exp)
        rm_rasters.append(lowres_high)
        last_result = lowres_high

    if fit_range:
        stats_fused = gs.parse_command(
            "r.univar",
            map=lowres_high,
            flags="g",
        )
        stats_fused["min"] = float(stats_fused["min"])
        stats_fused["max"] = float(stats_fused["max"])

        gs.debug(
            "fused min: %f, fused max: %f" % (stats_fused["min"], stats_fused["max"])
        )

        # fit output value range to input value range if need be
        perc_values = None
        if stats_fused["min"] < lrmin or stats_fused["max"] > lrmax:
            percentiles = "1,2,5,10,15,20,25,75,80,85,90,95,98,99"
            perc_values_list = list(
                gs.parse_command(
                    "r.quantile",
                    input=last_result,
                    percentile=percentiles,
                    quiet=True,
                ).keys()
            )
            perc_values = [float(item.split(":")[2]) for item in perc_values_list]

        if stats_fused["min"] < lrmin:
            gs.message(_("Rescaling low outliers..."))
            use_perc = None
            for i in range(7):
                if perc_values[i] > lrmin:
                    use_perc = perc_values[i]
                    break
            if not use_perc:
                gs.warning(
                    "Unable to find a suitable percentile to rescale "
                    "low outliers in the result"
                )
            else:
                # scale output values in the range [outmin, use_perc]
                # to the range [inmin, use_perc]
                fused_min = stats_fused["min"]
                # scale_factor = (use_perc - lrmin) / (use_perc - fused_min)
                out_minscaled = gs.append_node_pid("out_minscaled")

                # linear scaling, creates some artefacts in the histogram
                # exp = (
                #     f"{out_minscaled} = if({lowres_high} < {use_perc}, "
                #     f"double({lowres_high} - {use_perc}) * {scale_factor} + {use_perc}, "
                #     f"{lowres_high})"
                # )

                # exponential scaling, reduces artefacts in the histogram
                exp = (
                    f"{out_minscaled} = if({lowres_high} < {use_perc}, "
                    f"{use_perc} - pow(double({use_perc} - {lowres_high}) / ({use_perc} - {fused_min}), 0.7)  * ({use_perc} - {lrmin}), "
                    f"{lowres_high})"
                )

                gs.mapcalc(exp)
                rm_rasters.append(out_minscaled)
                last_result = out_minscaled

        if stats_fused["max"] > lrmax:
            gs.message(_("Rescaling high outliers..."))
            use_perc = None
            for i in range(13, 6, -1):
                if perc_values[i] < lrmax:
                    use_perc = perc_values[i]
                    break
            if not use_perc:
                gs.warning(
                    "Unable to find a suitable percentile to rescale "
                    "high outliers in the result"
                )
            else:
                # scale output values in the range [use_perc, outmax]
                # to the range [use_perc, inmax]
                fused_max = stats_fused["max"]
                # scale_factor = (lrmax - use_perc) / (fused_max - use_perc)
                out_maxscaled = gs.append_node_pid("out_maxscaled")

                # linear scaling, creates some artefacts in the histogram
                # exp = (
                #     f"{out_maxscaled} = if({last_result} > {use_perc}, "
                #     f"double({last_result} - {use_perc}) * {scale_factor} + {use_perc}, "
                #     f"{last_result})"
                # )

                # exponential scaling, reduces artefacts in the histogram
                exp = (
                    f"{out_maxscaled} = if({last_result} > {use_perc}, "
                    f"{use_perc} + pow(double({last_result} - {use_perc}) / ({fused_max} - {use_perc}), 0.7) * ({lrmax} - {use_perc}), "
                    f"{last_result})"
                )

                gs.mapcalc(exp)
                rm_rasters.append(out_maxscaled)
                last_result = out_maxscaled

    # convert output to input data type
    # preliminary output is DCELL
    gs.message(_("Creating final output map <{}>...").format(output_map))
    if infolr["datatype"] == "CELL":
        exp = f"{output_map} = round({last_result})"
        gs.mapcalc(exp)
    elif infolr["datatype"] == "FCELL":
        exp = f"{output_map} = float({last_result})"
        gs.mapcalc(exp)
    else:
        gs.run_command("g.copy", raster=f"{last_result},{output_map}")

    # copy color rules from input to output
    gs.run_command("r.colors", map=output_map, raster=lowres_map)

    gs.message(
        _("Fusion of <{lowres_map}> with <{highres_map}> finished.").format(
            lowres_map=lowres_map, highres_map=highres_map
        )
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
