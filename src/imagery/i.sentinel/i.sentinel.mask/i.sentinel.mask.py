#!/usr/bin/env python
"""
MODULE:       i.sentinel.mask
AUTHOR(S):    Roberta Fagandini, Moritz Lennert, Roberto Marzocchi
              Stefan Blumentrath (raster based cloud shadow identification)
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

# %option G_OPT_R_OUTPUT
# % description: Name of output raster cloud and shadow mask
# % required : no
# % guisection: Output
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
# % required: cloud_mask,cloud_raster,shadow_mask,shadow_raster,output
# % excludes: -c,shadow_mask,shadow_raster
# % required: input_file,blue,green,red,nir,nir8a,swir11,swir12,mtd_file
# % requires: output,mtd_file,metadata,input_file,sun_position
# % requires: shadow_raster,mtd_file,metadata,input_file,sun_position
# % requires: shadow_mask,mtd_file,metadata,input_file,sun_position
# % excludes: input_file,blue,green,red,nir,nir8a,swir11,swir12,mtd_file
# %end

import atexit
import math
import json
import sys

import xml.etree.ElementTree as et

from pathlib import Path

import numpy as np
import grass.script as gs

REQUIRED_BANDS = ["blue", "green", "red", "nir", "nir8a", "swir11", "swir12"]
TMP_NAME = gs.tempname(12)


def parse_input_file(module_options):
    """Extract bands and path to metadata file from input file"""
    if module_options["input_file"] == "":
        return {band: module_options[band] for band in REQUIRED_BANDS}, None
    input_bands = {}
    metadata_source = {}
    with open(module_options["input_file"], "r", encoding="UTF8") as input_file:
        for line in input_file:
            line_list = line.split("=")
            if len(line_list) != 2:
                gs.fatal(
                    _("Invalid syntax in input file <{}>").format(
                        module_options["input_file"]
                    )
                )
            elif line_list[0] == "MTD_TL.xml" and not module_options["mtd_file"]:
                metadata_source["mtd_file"] = line_list[1].strip()
            elif line_list[0] == "metadata" and not module_options["metadata"]:
                metadata_source["metadata"] = line_list[1].strip()
            elif line_list[0] in REQUIRED_BANDS:
                input_bands[line_list[0]] = line_list[1].strip()
        return input_bands, metadata_source


def get_sun_position(module_options, bands):
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
            zenith_azimuth = []
            for elem in root[1]:
                for subelem in elem[1]:
                    zenith_azimuth.append(float(subelem.text))

            if zenith_azimuth == [0.0, 0.0]:
                zenith_val = (
                    root[1]
                    .find("Tile_Angles")
                    .find("Sun_Angles_Grid")
                    .find("Zenith")
                    .find("Values_List")
                )
                zenith_azimuth[0] = float(
                    np.mean(
                        [
                            np.array(elem.text.split(" "), dtype=np.float)
                            for elem in zenith_val
                        ]
                    )
                )
                azimuth_val = (
                    root[1]
                    .find("Tile_Angles")
                    .find("Sun_Angles_Grid")
                    .find("Azimuth")
                    .find("Values_List")
                )
                zenith_azimuth[1] = float(
                    np.mean(
                        [
                            np.array(elem.text.split(" "), dtype=np.float)
                            for elem in azimuth_val
                        ]
                    )
                )
            gs.verbose(
                _("the mean sun Zenith is: {:.3f} deg").format(zenith_azimuth[0])
            )
            gs.verbose(
                _("the mean sun Azimuth is: {:.3f} deg").format(zenith_azimuth[1])
            )
        except ValueError:
            gs.fatal(
                _(
                    "Cannot get mean sun zenith and azimuth from metadata file <{}>."
                ).format(module_options["mtd_file"])
            )
        return tuple(zenith_azimuth)
    if module_options["sun_position"]:
        try:
            zenith_azimuth = tuple(
                map(float, module_options["sun_position"].split(","))
            )
        except ValueError:
            gs.fatal(
                _(
                    "Invalid input in sun_position option: {}.Two comma separated float values required"
                ).format(module_options["sun_position"])
            )
        return zenith_azimuth

    metadata_file = module_options["metadata"]
    if metadata_file == "default":
        # use default json
        env = gs.gisenv()
        json_standard_folder = (
            Path(env["GISDBASE"]) / env["LOCATION_NAME"] / env["MAPSET"] / "cell_misc"
        )
        for value in bands.values():
            metadata_file = json_standard_folder / value / "description.json"
            if metadata_file.is_file():
                break
            metadata_file = None
        if not metadata_file:
            gs.fatal(
                _(
                    "No default metadata files found. Did you use -j in i.sentinel.import?"
                )
            )
    try:
        with open(str(metadata_file), encoding="UTF8") as json_file:
            data = json.load(json_file)
        zenith_azimuth = tuple(
            (
                float(data["MEAN_SUN_ZENITH_ANGLE"]),
                float(data["MEAN_SUN_AZIMUTH_ANGLE"]),
            )
        )
    except OSError:
        gs.fatal(
            _(
                "Unable to get MEAN_SUN_ZENITH_ANGLE and MEAN_SUN_AZIMUTH_ANGLE from metadata file {}."
            ).format(metadata_file)
        )
    return zenith_azimuth


def get_overlap(clouds, dark_pixels, old_region, new_region):
    """Compute overlap between two rasters after shifting"""
    # move map
    gs.run_command(
        "r.region",
        quiet=True,
        map=clouds,
        n=new_region["north"],
        s=new_region["south"],
        e=new_region["east"],
        w=new_region["west"],
    )
    # measure overlap
    overlap = int(
        gs.read_command(
            "r.stats",
            quiet=True,
            flags="cn",
            input=f"{clouds},{dark_pixels}",
            separator=",",
        )
        .strip()
        .split(",")[2]
        .strip()
    )
    # move map back
    gs.run_command(
        "r.region",
        quiet=True,
        map=clouds,
        n=old_region["north"],
        s=old_region["south"],
        e=old_region["east"],
        w=old_region["west"],
    )

    return overlap


def is_decreasing(list_object):
    """Check if numeric elements in a list are decreasing"""
    return all(
        previous_element > current_element
        for previous_element, current_element in zip(list_object, list_object[1:])
    )


def cleanup():
    """Remove all maps with TMP_NAME prefix"""
    gs.run_command(
        "g.remove", type="raster", pattern=f"{TMP_NAME}*", flags="bf", quiet=True
    )


def compute_shadow_shift(clouds_map, dark_pixel_map, sun_zenith, sun_azimuth):
    """
    Start computing the east and north shift for clouds and the
    overlapping area between clouds and dark_pixels at user given steps
    """
    height_steps = 100
    height_minimum = 1000
    height_maximum = 4000
    height = height_minimum
    gs.verbose(
        _(
            "Computing the east and north shift of cloud shadows using height steps of {}m"
        ).format(height_steps)
    )
    gs.run_command("g.copy", raster=f"{clouds_map},{TMP_NAME}", quiet=True)
    map_region = gs.raster.raster_info(TMP_NAME)
    heights = []
    shifts = []
    overlap_areas = []
    tan_z = math.tan(math.radians(sun_zenith))
    a_deg_to_rad = math.radians(sun_azimuth)
    while height <= height_maximum:
        e_shift = -height * tan_z * math.sin(a_deg_to_rad)
        n_shift = -height * tan_z * math.cos(a_deg_to_rad)

        new_region = {
            "north": float(map_region["north"]) + n_shift,
            "south": float(map_region["south"]) + n_shift,
            "east": float(map_region["east"]) + e_shift,
            "west": float(map_region["west"]) + e_shift,
        }

        shifts.append((e_shift, n_shift))
        heights.append(height)
        height = height + height_steps

        overlap_areas.append(
            get_overlap(TMP_NAME, dark_pixel_map, map_region, new_region)
        )

        if len(overlap_areas) >= 4 and is_decreasing(overlap_areas[-4:]):
            break

    # Find the maximum overlapping area between clouds and dark_pixels
    index_max_overlap = np.argmax(overlap_areas)

    gs.verbose(
        _(
            "Estimated cloud shadow parameters as follows:\n"
            "clouds height is: {:.2f} m\n"
            "east shift is: {:.2f} m\nnorth shift is: {:.2f} m"
        ).format(heights[index_max_overlap], *shifts[index_max_overlap])
    )

    # Clouds are shifted using the clouds height corresponding to the
    # maximum overlapping area then are intersect with dark_pixels
    gs.run_command(
        "r.region",
        quiet=True,
        map=TMP_NAME,
        n=float(map_region["north"]) + shifts[index_max_overlap][1],
        s=float(map_region["south"]) + shifts[index_max_overlap][1],
        e=float(map_region["east"]) + shifts[index_max_overlap][0],
        w=float(map_region["west"]) + shifts[index_max_overlap][0],
    )
    return 0


def create_empty_maps(
    module_options, map_keys=("cloud_raster", "shadow_raster", "output")
):
    """Create empty maps for requested results that cannot be returned otherwise
    and exit"""
    for map_key in map_keys:
        if module_options[map_key]:
            null_value = "null()" if map_key != "output" else "0"
            gs.mapcalc(f"{module_options[map_key]}={null_value}", overwrite=True)
            gs.raster_history(module_options[map_key], overwrite=True)
    sys.exit(0)


def main():
    """Do the main work"""

    f_bands = {}
    cloud_size_threshold = (
        float(options["cloud_threshold"]) / 10000.0
        if options["cloud_threshold"]
        else 0.0
    )
    shadow_size_threshold = (
        float(options["shadow_threshold"]) / 10000.0
        if options["shadow_threshold"]
        else 0.0
    )
    raster_max = {}

    cloud_raster = options["cloud_raster"] or f"{TMP_NAME}_cloud_raster"
    if (
        options["cloud_mask"]
        and gs.utils.legalize_vector_name(options["cloud_mask"], fallback_prefix="x")
        != options["cloud_mask"]
    ):
        gs.fatal(
            _("Name for cloud_mask output <{}> is not SQL compliant").format(
                options["cloud_mask"]
            )
        )
    shadow_mask = options["shadow_mask"] or f"{TMP_NAME}_shadow_mask"
    if gs.utils.legalize_vector_name(shadow_mask, fallback_prefix="x") != shadow_mask:
        gs.fatal(
            _("Name for shadow_mask output is not SQL compliant").format(
                options["shadow_mask"]
            )
        )
    shadow_raster = options["shadow_raster"] or f"{TMP_NAME}_shadow_raster"

    output = options["output"] or None

    bands, metadta_option = parse_input_file(options)

    # Check if all required input bands are specified in the text file
    for band in REQUIRED_BANDS:
        if band not in bands:
            gs.fatal(
                _(
                    "All input bands ({required_bands}) are required., Missing {band} band."
                ).format(required_bands=REQUIRED_BANDS, band=band)
            )

    # Check if input bands exist
    for key, value in bands.items():
        if not gs.find_file(value, element="cell")["file"]:
            gs.fatal(_("Raster map <{}> not found.").format(value))

    if metadta_option and "metadtata" in metadta_option:
        options["metadtata"] = metadta_option["metadtata"]
    elif metadta_option and "mtd_file" in metadta_option:
        options["mtd_file"] = metadta_option["mtd_file"]

    sun_zenith, sun_azimuth = get_sun_position(options, bands)

    if flags["r"]:
        gs.use_temp_region()
        gs.run_command("g.region", rast=bands.values(), flags="a")

    if flags["s"]:
        gs.verbose(_("Start rescaling bands"))
        check_b = 0
        for key, band in bands.items():
            band = gs.find_file(band, element="cell")["name"]
            band_double = f"{TMP_NAME}_band_{check_b}_double"
            gs.mapcalc(f"{band_double} = 1.0 * ({band})/{options['scale_fac']}")
            f_bands[key] = band_double
            check_b += 1
    else:
        for key, band in bands.items():
            if (
                gs.raster_info(band)["datatype"] != "DCELL"
                and gs.raster_info(band)["datatype"] != "FCELL"
            ):
                gs.fatal(
                    "Raster maps must be DCELL or FCELL, please apply a scale factor"
                )
        f_bands = bands

    gs.verbose(_("Computing maximum values of bands"))
    stats_module = "r.univar"
    stats_flags = "g"
    if flags["r"]:
        stats_module = "r.info"
        stats_flags += "r"
    for key, fband in f_bands.items():
        stats = gs.parse_command(stats_module, flags=stats_flags, map=fband)
        raster_max[key] = float(stats["max"])

    # Start of Clouds detection  (some rules from litterature)
    first_rule = (
        f"(({f_bands['blue']} > (0.08*{raster_max['blue']})) && "
        f"({f_bands['green']} > (0.08*{raster_max['green']})) && "
        f"({f_bands['red']} > (0.08*{raster_max['red']})))"
    )
    second_rule = (
        f"(({f_bands['red']} < ((0.08*{raster_max['red']})*1.5)) && "
        f"({f_bands['red']} > {f_bands['swir12']}*1.3))"
    )
    third_rule = (
        f"(({f_bands['swir11']} < (0.1*{raster_max['swir11']})) && "
        f"({f_bands['swir12']} < (0.1*{raster_max['swir12']})))"
    )
    fourth_rule = (
        f"(if({f_bands['nir8a']} == max({f_bands['nir8a']}, "
        f"2 * {f_bands['blue']}, 2 * {f_bands['green']}, 2 * {f_bands['red']})))"
    )
    fifth_rule = f"({f_bands['blue']} > 0.2)"
    cloud_rules = (
        f"({first_rule} == 1) && "
        f"({second_rule} == 0) && "
        f"({third_rule} == 0) && "
        f"({fourth_rule} == 0) && "
        f"({fifth_rule} == 1)"
    )
    progress_message = "Computing cloud pixels"
    clouds = (
        cloud_raster
        if cloud_size_threshold <= 0.0 and options["cloud_raster"]
        else f"{TMP_NAME}_clouds"
    )
    mapcalc_expression = f"{clouds} = if({cloud_rules}, 0, null())"

    if options["shadow_mask"] or options["shadow_raster"] or options["output"]:
        # Start of shadows detection
        progress_message = "Computing cloud and shadow pixels"
        sixth_rule = (
            f"((({f_bands['blue']} > {f_bands['swir12']}) && "
            f"({f_bands['blue']} < {f_bands['nir']}) && "
            f"({f_bands['blue']} < 0.1) && ({f_bands['swir12']} < 0.1)) || "
            f"(({f_bands['blue']} < {f_bands['swir12']}) && "
            f"({f_bands['blue']} < {f_bands['nir']}) && "
            f"({f_bands['blue']} < 0.1) && ({f_bands['swir12']} < 0.1) && "
            f"({f_bands['nir']} < 0.1)))"
        )
        seventh_rule = f"({f_bands['green']} - {f_bands['blue']})"
        shadow_rules = f"(({sixth_rule} == 1) && ({seventh_rule} < 0.007))"
        dark_pixels = f"{TMP_NAME}_dark_pixels"
        mapcalc_expression = (
            f"{mapcalc_expression}\n{dark_pixels} = if({shadow_rules}, 0, null())"
        )

    gs.verbose(_(progress_message))
    gs.mapcalc(mapcalc_expression, overwrite=True)

    if cloud_size_threshold > 0:
        gs.verbose(
            _("Filtering clouds with less than {} ha size").format(cloud_size_threshold)
        )
        try:
            gs.run_command(
                "r.reclass.area",
                quiet=True,
                input=clouds,
                output=cloud_raster,
                mode="greater",
                value=cloud_size_threshold,
            )
            gs.raster_history(cloud_raster, overwrite=True)
        except Exception:
            gs.warning(_("No clouds have been detected"))
            create_empty_maps(
                options, map_keys=["cloud_raster", "shadow_raster", "output"]
            )

    if options["cloud_mask"] and gs.raster_info(cloud_raster)["max"] is not None:
        gs.verbose(_("Converting raster cloud mask into vector map"))
        gs.run_command(
            "r.to.vect",
            quiet=True,
            input=cloud_raster,
            output=options["cloud_mask"],
            type="area",
            flags="s",
        )

    # End of Clouds detection
    if (
        not options["shadow_raster"]
        and not options["shadow_mask"]
        and not options["output"]
    ):
        sys.exit(0)

    if shadow_size_threshold > 0:
        gs.verbose(
            _("Filtering cloud shadows with less than {} ha size").format(
                shadow_size_threshold
            )
        )
        try:
            gs.run_command(
                "r.reclass.area",
                quiet=True,
                input=dark_pixels,
                output=f"{TMP_NAME}_shadows",
                mode="greater",
                value=shadow_size_threshold,
            )
            dark_pixels = f"{TMP_NAME}_shadows"
        except Exception:
            gs.warning(_("No cloud shadows have been detected"))
            create_empty_maps(options, map_keys=["shadow_raster", "output"])

    # End of shadows detection

    # START shadows cleaning Procedure (remove shadows misclassification)

    # End cloud mask preparation
    # Shift cloud mask using dE e dN
    # Start reading mean sun zenith and azimuth from xml file to compute
    # dE and dN automatically

    # Stop reading mean sun zenith and azimuth from xml file to compute dE
    # and dN automatically
    # Start computing the east and north shift for clouds and the
    # overlapping area between clouds and shadows at steps of 100m

    # Start computing the east and north shift for clouds and the
    # overlapping area between clouds and dark_pixels at user given steps
    compute_shadow_shift(clouds, dark_pixels, sun_zenith, sun_azimuth)

    if shadow_size_threshold > 0:
        gs.run_command(
            "r.clump",
            quiet=True,
            input=dark_pixels,
            output=f"{dark_pixels}_clumped",
        )

        rules = np.genfromtxt(
            gs.decode(
                gs.read_command(
                    "r.stats",
                    quiet=True,
                    flags="na",
                    input=f"{dark_pixels}_clumped,{TMP_NAME}",
                    separator=",",
                )
            )
            .strip()
            .split("\n"),
            delimiter=",",
        )
        rules = rules[:, 0][np.where(rules[:, 2] > shadow_size_threshold)].astype(int)
        rules = "\n".join([f"{row}=0" for row in rules])

        gs.write_command(
            "r.reclass",
            quiet=True,
            input=f"{dark_pixels}_clumped",
            output=f"{TMP_NAME}_selected",
            rules="-",
            stdin=rules + "\n*=NULL\n",
        )

    if output:
        gs.mapcalc(
            f"{output}=if(isnull({clouds}),if(isnull({TMP_NAME}_selected),0,if(isnull({dark_pixels}),0,2)),1)"
        )
        gs.write_command(
            "r.category",
            map=output,
            rules="-",
            stdin="0\tNo clouds\n1\tCloud\n2\tCloud shadow\n",
        )
        gs.raster_history(output, overwrite=True)

    if options["shadow_raster"] or options["shadow_mask"]:
        if gs.raster_info(f"{TMP_NAME}_selected")["max"] is None:
            gs.warning(_("No shadows have been detected"))
            create_empty_maps(options, map_keys=["shadow_raster"])
        gs.mapcalc(
            f"{shadow_raster}=if(isnull({clouds}),if(isnull({TMP_NAME}_selected),null(),if(isnull({dark_pixels}),null(),1)),null())"
        )
        gs.raster_history(shadow_raster, overwrite=True)

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


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
