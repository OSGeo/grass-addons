#!/usr/bin/env python
"""
MODULE:       i.sentinel.mask
AUTHOR(S):    Roberta Fagandini, Moritz Lennert, Roberto Marzocchi
PURPOSE:      Creates clouds and shadows masks for Sentinel-2 images
COPYRIGHT:    (C) 2018-2023 by Roberta Fagandini, and the GRASS Development Team
              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

# %Module
# % description: Creates clouds and shadows masks for Sentinel-2 images.
# % keyword: imagery
# % keyword: satellite
# % keyword: Sentinel
# % keyword: cloud detection
# % keyword: shadow
# % keyword: reflectance
# %End

# %option G_OPT_F_INPUT
# % key: input_file
# % description: Name of the .txt file with listed input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: blue
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: green
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: red
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: nir
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: nir8a
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: swir11
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_R_INPUT
# % key: swir12
# % description: Input bands
# % required : no
# % guisection: Required
# %end

# %option G_OPT_V_OUTPUT
# % key: cloud_mask
# % description: Name of output vector cloud mask
# % required : no
# % guisection: Output
# %end

# %option G_OPT_R_OUTPUT
# % key: cloud_raster
# % description: Name of output raster cloud mask
# % required : no
# % guisection: Output
# %end

# %option G_OPT_V_OUTPUT
# % key: shadow_mask
# % description: Name of output vector shadow mask
# % required : no
# % guisection: Output
# %end

# %option G_OPT_R_OUTPUT
# % key: shadow_raster
# % description: Name of output raster shadow mask
# % required : no
# % guisection: Output
# %end

# %option
# % key: cloud_threshold
# % type: integer
# % description: Threshold for cleaning small areas from cloud mask (in square meters)
# % required : yes
# % answer: 50000
# % guisection: Output
# %end

# %option
# % key: shadow_threshold
# % type: integer
# % description: Threshold for cleaning small areas from shadow mask (in square meters)
# % required : yes
# % answer: 10000
# % guisection: Output
# %end

# %option
# % key: sun_position
# % type: string
# % description: Comma separted pair of values for mean sun zenith and mean sun azimuth as reported in metadata
# % required : no
# % guisection: Metadata
# %end

# %option G_OPT_F_INPUT
# % key: mtd_file
# % description: Name of the image metadata file (MTD_TL.xml)
# % required : no
# % guisection: Metadata
# %end

# %option G_OPT_F_INPUT
# % key: metadata
# % label: Name of Sentinel metadata json file
# % description: Default is LOCATION/MAPSET/cell_misc/BAND/description.json
# % answer: default
# % required : no
# % guisection: Metadata
# %end

# %option
# % key: scale_fac
# % type: integer
# % description: Rescale factor
# % required : no
# % answer: 10000
# % guisection: Rescale
# %end

# %flag
# % key: r
# % description: Set computational region to maximum image extent
# %end

# %flag
# % key: t
# % description: Do not delete temporary files
# %end

# %flag
# % key: s
# % description: Rescale input bands
# % guisection: Rescale
# %end

# %flag
# % key: c
# % description: Compute only the cloud mask
# %end

# %rules
# % collective: blue,green,red,nir,nir8a,swir11,swir12
# % excludes: mtd_file,metadata,sun_position
# % required: cloud_mask,cloud_raster,shadow_mask,shadow_raster
# % excludes: -c,shadow_mask,shadow_raster
# % required: input_file,blue,green,red,nir,nir8a,swir11,swir12,mtd_file
# % excludes: input_file,blue,green,red,nir,nir8a,swir11,swir12,mtd_file
# %end

import atexit

# import glob
import math
import json

# import os
# import re
# import shutil
# import subprocess
# import sys
# import time
import xml.etree.ElementTree as et

from pathlib import Path

import numpy as np

import grass.script as gs

REQUIRED_BANDS = ["blue", "green", "red", "nir", "nir8a", "swir11", "swir12"]
TMP_NAME = gs.tempname(12)


def get_sun_position(module_options):
    """Get sun position (zenith and azimuth from input options"""
    if module_options["mtd_file"]:
        gs.verbose(
            _(
                "Reading mean sun zenith and azimuth from metadata file to compute clouds shift"
            )
        )
        try:
            xml_tree = et.parse(module_options["mtd_file"])
            root = xml_tree.getroot()
            ZA = []
            try:
                for elem in root[1]:
                    for subelem in elem[1]:
                        ZA.append(subelem.text)
                if ZA == ["0", "0"]:
                    zenith_val = (
                        root[1]
                        .find("Tile_Angles")
                        .find("Sun_Angles_Grid")
                        .find("Zenith")
                        .find("Values_List")
                    )
                    ZA[0] = np.mean(
                        [
                            np.array(elem.text.split(" "), dtype=np.float)
                            for elem in zenith_val
                        ]
                    )
                    azimuth_val = (
                        root[1]
                        .find("Tile_Angles")
                        .find("Sun_Angles_Grid")
                        .find("Azimuth")
                        .find("Values_List")
                    )
                    ZA[1] = np.mean(
                        [
                            np.array(elem.text.split(" "), dtype=np.float)
                            for elem in azimuth_val
                        ]
                    )
                zenith = float(ZA[0])
                azimuth = float(ZA[1])
                gs.verbose(_("the mean sun Zenith is: {:.3f} deg").format(zenith))
                gs.verbose(_("the mean sun Azimuth is: {:.3f} deg").format(azimuth))
                return zenith, azimuth
            except ValueError:
                gs.fatal(
                    _(
                        "The selected input metadata file is not the right one. Please check the manual page."
                    )
                )
        except ValueError:
            gs.fatal(
                _(
                    "The selected input metadata file is not an .xml file. Please check the manual page."
                )
            )
    elif module_options["metadata_file"]:
        if module_options["metadata_file"] != "default":
            metadata_file = module_options["metadata_file"]
        else:
            # use default json
            env = gs.gisenv()
            json_standard_folder = (
                Path(env["GISDBASE"])
                / env["LOCATION_NAME"]
                / env["MAPSET"]
                / "cell_misc"
            )
            for key, value in bands.items():
                metadata_file = json_standard_folder / value / "description.json"
                if metadata_file.is_file():
                    break
                metadata_file = None
            if not metadata_file:
                gs.fatal(
                    "No default metadata files found. Did you use -j in i.sentinel.import?"
                )
        try:
            with open(str(metadata_file)) as json_file:
                data = json.load(json_file)
            return float(data["MEAN_SUN_ZENITH_ANGLE"]), float(
                data["MEAN_SUN_AZIMUTH_ANGLE"]
            )
        except OSError:
            gs.fatal(
                _(
                    "Unable to get MEAN_SUN_ZENITH_ANGLE and MEAN_SUN_AZIMUTH_ANGLE from metadata file {}."
                ).format(metadata_file)
            )
    elif module_options["sun_position"]:
        try:
            zenith, azimuth = list(
                map(float, module_options["sun_position"].split(","))
            )
            return zenith, azimuth
        except ValueError:
            gs.fatal(
                _(
                    "Invalid input in sun_position option: {}.Two comma separated float values required"
                ).format(module_options["sun_position"])
            )
    gs.fatal(
        _(
            "Could not determine sun position for cloud shadow detection from given input."
        )
    )


def get_overlap(clouds, dark_pixels, old_region, new_region):
    """Compute overlap between two rasters after shifting"""
    # move map
    gs.run_command(
        "r.region",
        map=clouds,
        n=new_region["n"],
        s=new_region["s"],
        e=new_region["e"],
        w=new_region["w"],
    )
    # measure overlap
    overlap = int(
        gs.read_command(
            "r.stats",
            flags="c",
            input=f"{clouds},{dark_pixels}",
            separator=",",
        )
        .strip()
        .split(",")[2]
    )
    # move map back
    gs.run_command(
        "r.region",
        map=clouds,
        n=old_region["n"],
        s=old_region["s"],
        e=old_region["e"],
        w=old_region["w"],
    )

    return overlap


def cleanup():
    """Remove all maps with TMP_NAME prefix"""
    gs.run_command(
        "g.remove", type="raster", pattern=f"{TMP_NAME}*", flags="f", quiet=True
    )


def main():
    """Do the main work"""

    output = options["output"]
    clouds = options["clouds"]
    dark_pixels = options["dark_pixels"]
    height_minimum = options["height_minimum"]
    height_maximum = options["height_maximum"]
    height_steps = options["height_steps"]

    f_bands = {}
    scale_fac = options["scale_fac"]
    cloud_size_threshold = options["cloud_threshold"]
    shadow_size_threshold = options["shadow_threshold"]
    raster_max = {}

    cloud_raster = options["cloud_raster"] or f"{TMP_NAME}_cloud_raster"
    cloud_mask = options["cloud_mask"] or f"{TMP_NAME}_cloud_mask"
    if gs.utils.legalize_vector_name(cloud_mask, fallback_prefix="x") != cloud_mask:
        gs.fatal(
            _(
                "Name for cloud_mask output \
                           is not SQL compliant"
            ).format(options["cloud_mask"])
        )
    shadow_mask = options["shadow_mask"] or f"{TMP_NAME}_shadow_mask"
    if gs.utils.legalize_vector_name(shadow_mask, fallback_prefix="x") != shadow_mask:
        gs.fatal(
            _(
                "Name for shadow_mask output \
                           is not SQL compliant"
            ).format(options["shadow_mask"])
        )
    shadow_raster = options["shadow_raster"] or f"{TMP_NAME}_shadow_raster"

    # Check if all required input bands are specified in the text file
    if all(band in bands and bands[band] for band in REQUIRED_BANDS):
        gs.fatal(
            _(
                "All input bands (blue, green, red, nir, nir8a, swir11, swir12) are required."
            )
        )

    # Check if input bands exist
    for key, value in bands.items():
        if not gs.find_file(value, element="cell", mapset=mapset)["file"]:
            gs.fatal(_("Raster map <{}> not found.").format(value))

    if flags["r"]:
        gs.use_temp_region()
        gs.run_command("g.region", rast=bands.values(), flags="a")
        gs.verbose(
            _("The computational region has been temporarily set to image max extent")
        )
    else:
        gs.warning(
            _(
                "All subsequent operations will be limited to the current computational region"
            )
        )

    if flags["s"]:
        gs.verbose(_("Start rescaling bands"))
        check_b = 0
        for key, b in bands.items():
            gs.verbose(b)
            b = gs.find_file(b, element="cell")["name"]
            band_double = f"{TMP_NAME}_band_{check_b}_double"
            gs.mapcalc(f"{band_double} = 1.0 * ({b})/{scale_fac}")
            f_bands[key] = band_double
            check_b += 1
        gs.verbose(f_bands.values())
        gs.verbose(_("All bands have been rescaled"))
    else:
        gs.warning(_("No rescale factor has been applied"))
        for key, b in bands.items():
            if (
                gs.raster_info(b)["datatype"] != "DCELL"
                and gs.raster_info(b)["datatype"] != "FCELL"
            ):
                gs.fatal("Raster maps must be DCELL or FCELL")
        f_bands = bands

    gs.verbose(_("Start computing maximum values of bands"))
    stats_module = "r.univar"
    stats_flags = "g"
    if flags["r"]:
        stats_module = "r.info"
        stats_flags = "gr"
    for key, fb in f_bands.items():
        gs.verbose(fb)
        stats = gs.parse_command(stats_module, flags=stats_flags, map=fb)
        raster_max[key] = float(stats["max"])
    gs.verbose(_("Computed maximum values: {}").format(", ".join(raster_max.values())))
    gs.verbose(_("Statistics have been computed!"))

    # Start of Clouds detection  (some rules from litterature)
    gs.verbose(_("Start clouds detection procedure"))
    gs.verbose(_("Computing cloud mask..."))
    first_rule = "(({} > (0.08*{})) && ({} > (0.08*{})) && ({} > (0.08*{})))".format(
        f_bands["blue"],
        raster_max["blue"],
        f_bands["green"],
        raster_max["green"],
        f_bands["red"],
        raster_max["red"],
    )
    second_rule = "(({} < ((0.08*{})*1.5)) && ({} > {}*1.3))".format(
        f_bands["red"], raster_max["red"], f_bands["red"], f_bands["swir12"]
    )
    third_rule = "(({} < (0.1*{})) && ({} < (0.1*{})))".format(
        f_bands["swir11"], raster_max["swir11"], f_bands["swir12"], raster_max["swir12"]
    )
    fourth_rule = "(if({} == max({}, 2 * {}, 2 * {}, 2 * {})))".format(
        f_bands["nir8a"],
        f_bands["nir8a"],
        f_bands["blue"],
        f_bands["green"],
        f_bands["red"],
    )
    fifth_rule = "({} > 0.2)".format(f_bands["blue"])
    cloud_rules = (
        "({} == 1) && ({} == 0) && ({} == 0) && ({} == 0) && ({} == 1)".format(
            first_rule, second_rule, third_rule, fourth_rule, fifth_rule
        )
    )
    mapcalc_expression = f"{TMP_NAME}_clouds = if({cloud_rules}, 0, null())"

    if options["shadow_mask"] or options["shadow_raster"]:
        # Start of shadows detection
        gs.verbose(_("Start shadows detection procedure"))
        gs.verbose(_("Computing shadow mask..."))
        sixth_rule = "((({} > {}) && ({} < {}) && ({} < 0.1) && ({} < 0.1)) \
        || (({} < {}) && ({} < {}) && ({} < 0.1) && ({} < 0.1) && ({} < 0.1)))".format(
            f_bands["blue"],
            f_bands["swir12"],
            f_bands["blue"],
            f_bands["nir"],
            f_bands["blue"],
            f_bands["swir12"],
            f_bands["blue"],
            f_bands["swir12"],
            f_bands["blue"],
            f_bands["nir"],
            f_bands["blue"],
            f_bands["swir12"],
            f_bands["nir"],
        )
        seventh_rule = f"({f_bands['green']} - {f_bands['blue']})"
        shadow_rules = f"(({sixth_rule} == 1) && ({seventh_rule} < 0.007))"
        mapcalc_expression = f"{mapcalc_expression}\n{TMP_NAME}_dark_pixels = if({shadow_rules}, 0, null())"

    gs.mapcalc(mapcalc_expression, overwrite=True)

    if cloud_size_threshold and int(cloud_size_threshold) > 0:
        gs.run_command(
            "r.reclass.area",
            input=f"{TMP_NAME}_clouds",
            output=cloud_raster,
            mode="greater",
            value=cloud_size_threshold,
        )
        clouds = f"{TMP_NAME}_clouds"

    if options["cloud_mask"]:
        gs.verbose(_("Converting raster cloud mask into vector map"))
        gs.run_command(
            "r.to.vect",
            input=cloud_raster,
            output=options["cloud_mask"],
            type="area",
            flags="s",
        )
        info_c = gs.parse_command("v.info", map=options["cloud_mask"], flags="t")
        if info_c["areas"] == "0":
            gs.warning(_("No clouds have been detected"))
    gs.verbose(_("Finish cloud detection procedure"))
    # End of Clouds detection

    if options["shadow_raster"] or options["shadow_mask"]:
        dark_pixels = f"{TMP_NAME}_dark_pixels"
        if shadow_size_threshold and int(shadow_size_threshold) > 0:
            gs.run_command(
                "r.reclass.area",
                input=f"{TMP_NAME}_dark_pixels",
                output=f"{TMP_NAME}_shadows",
                mode="greater",
                value=shadow_size_threshold,
            )
            dark_pixels = f"{TMP_NAME}_shadows"

        gs.verbose(_("Finish cloud shadow detection procedure"))
        # End of shadows detection

        # START shadows cleaning Procedure (remove shadows misclassification)

        # End cloud mask preparation
        # Shift cloud mask using dE e dN
        # Start reading mean sun zenith and azimuth from xml file to compute
        # dE and dN automatically
        sun_zenith, sun_azimuth = get_sun_position(options)

        # Stop reading mean sun zenith and azimuth from xml file to compute dE
        # and dN automatically
        # Start computing the east and north shift for clouds and the
        # overlapping area between clouds and shadows at steps of 100m
        gs.verbose(
            _(
                "Start computing the east and north clouds shift at steps of 100m of clouds height"
            )
        )

        # Start computing the east and north shift for clouds and the
        # overlapping area between clouds and dark_pixels at user given steps
        gs.verbose(
            _(
                "Start computing the east and north clouds shift at steps of {}m of clouds height"
            ).format(height_steps)
        )
        height_minimum = 100
        height_maximum = 1000
        height_steps = 100
        height = height_minimum
        gs.run_command("g.copy", raster=f"{clouds},{TMP_NAME}", quiet=True)
        map_region = gs.raster.raster_info(TMP_NAME)
        heights = []
        shifts = []
        overlap_areas = []
        while height <= height_maximum:
            z_deg_to_rad = math.radians(sun_zenith)
            tan_z = math.tan(z_deg_to_rad)
            a_deg_to_rad = math.radians(sun_azimuth)
            cos_a = math.cos(a_deg_to_rad)
            sin_a = math.sin(a_deg_to_rad)

            e_shift = -height * tan_z * sin_a
            n_shift = -height * tan_z * cos_a

            new_region = {
                "n": float(map_region["n"]) + n_shift,
                "s": float(map_region["s"]) + n_shift,
                "e": float(map_region["e"]) + e_shift,
                "w": float(map_region["w"]) + e_shift,
            }

            shifts.append(tuple(e_shift, n_shift))
            heights.append(height)
            height = height + height_steps

            overlap_areas.append(
                get_overlap(TMP_NAME, dark_pixels, map_region, new_region)
            )

        # Find the maximum overlapping area between clouds and dark_pixels
        index_max_overlap = np.argmax(overlap_areas)

        gs.verbose(
            _("the estimated clouds height is: {} m").format(heights[index_max_overlap])
        )
        gs.verbose(
            _("the estimated east shift is: {:.2f} m").format(
                shifts[index_max_overlap][0]
            )
        )
        gs.verbose(
            _("the estimated north shift is: {:.2f} m").format(
                shifts[index_max_overlap][1]
            )
        )

        # Clouds are shifted using the clouds height corresponding to the
        # maximum overlapping area then are intersect with dark_pixels
        gs.run_command(
            "r.region",
            map=TMP_NAME,
            n=float(map_region["n"]) + shifts[index_max_overlap][1],
            s=float(map_region["s"]) + shifts[index_max_overlap][1],
            e=float(map_region["e"]) + shifts[index_max_overlap][0],
            w=float(map_region["w"]) + shifts[index_max_overlap][0],
        )

        gs.mapcalc(
            f"{output}=if(isnull({cloud}),if(isnull({TMP_NAME}),if(isnull({shadow}),null(),3),2),1)"
        )

    if options["shadow_mask"]:
        gs.verbose(_("Converting raster shadow mask into vector map"))
        gs.run_command(
            "r.to.vect",
            input=shadow_raster,
            output=options["shadow_mask"],
            type="area",
            flags="s",
            overwrite=True,
        )
        info_s = gs.parse_command("v.info", map=options["shadow_mask"], flags="t")
        if info_s["areas"] == "0":
            gs.warning(_("No shadows have been detected"))

    gs.raster_history(cloud_raster)
    gs.raster_history(shadow_raster)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
