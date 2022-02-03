#!/usr/bin/env python

##############################################################################
#
# MODULE:       Unsupervised nested-means algorithm for terrain classification
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Divides topography based on terrain texture and curvature.
#               Based on the methodology of Iwahashi & Pike (2007)
#               Automated classifications of topography from DEMs by an unsupervised
#               nested-means algorithm and a three-part geometric signature.
#               Geomorphology. 86, 409-440
#
# COPYRIGHT:    (C) 2017 Steven Pawley and by the GRASS Development Team
#
##############################################################################

# %module
# % description: Unsupervised nested-means algorithm for terrain classification
# % keyword: raster
# % keyword: terrain
# % keyword: classification
# %end

# %option G_OPT_R_INPUT
# % description: Input elevation raster:
# % key: elevation
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % description: Input slope raster:
# % key: slope
# % required: no
# %end

# %option
# % key: flat_thres
# % type: double
# % description: Height threshold for pit and peak detection:
# % answer: 1
# % required: no
# %end

# %option
# % key: curv_thres
# % type: double
# % description: Curvature threshold for convexity and concavity detection:
# % answer: 0
# % required: no
# %end

# %option
# % key: filter_size
# % type: integer
# % description: Size of smoothing filter window:
# % answer: 3
# % guisection: Optional
# %end

# %option
# % key: counting_size
# % type: integer
# % description: Size of counting window:
# % answer: 21
# % guisection: Optional
# %end

# %option
# % key: classes
# % type: integer
# % description: Number of classes in nested terrain classification:
# % options: 8,12,16
# % answer: 8
# % guisection: Optional
# %end

# %option G_OPT_R_OUTPUT
# % description: Output terrain texture:
# % key: texture
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % description: Output terrain convexity:
# % key: convexity
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % description: Output terrain concavity:
# % key: concavity
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % description: Output terrain classification:
# % key: features
# % required : no
# %end


import os
import sys
import random
import string
import math
import numpy as np
from subprocess import PIPE
import atexit
import grass.script as gs
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.script.utils import parse_key_val

TMP_RAST = []


def cleanup():
    gs.message("Deleting intermediate files...")

    for f in TMP_RAST:
        gs.run_command("g.remove", type="raster", name=f, flags="bf", quiet=True)

    g.region(**current_reg)

    if mask_test:
        r.mask(original_mask, overwrite=True, quiet=True)


def temp_map(name):
    tmp = name + "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(4)]
    )
    TMP_RAST.append(tmp)

    return tmp


def parse_tiles(tiles):
    # convert r.tileset output into list of dicts
    tiles = [i.split(";") for i in tiles]
    tiles = [[parse_key_val(i) for i in t] for t in tiles]

    tiles_reg = []
    for index, tile in enumerate(tiles):
        tiles_reg.append({})
        for param in tile:
            tiles_reg[index].update(param)

    return tiles_reg


def laplacian_matrix(w):
    s = """TITLE Laplacian filter
    MATRIX {w}
    """.format(
        w=w
    )

    x = np.zeros((w, w))
    x[:] = -1
    x[np.floor(w / 2).astype("int"), np.floor(w / 2).astype("int")] = (np.square(w)) - 1
    x_str = str(x)
    x_str = x_str.replace(" [", "")
    x_str = x_str.replace("[", "")
    x_str = x_str.replace("]", "")
    x_str = x_str.replace(".", "")
    s += x_str
    s += """
    DIVISOR 1
    TYPE P"""
    return s


def categories(nclasses):
    if nclasses == 8:
        s = """1|steep, high convexity, fine-textured
        2|steep, high convexity, coarse-textured
        3|steep, low convexity, fine-textured
        4|steep, low convexity, coarse-textured
        5|gentle, high convexity, fine-textured
        6|gentle, high convexity, coarse-textured
        7|gentle, low convexity, fine-textured
        8|gentle, low convexity, coarse-textured"""
    elif nclasses == 12:
        s = """1|steep, high convexity, fine-textured
        2|steep, high convexity, coarse-textured
        3|steep, low convexity, fine-textured
        4|steep, low convexity, coarse-textured
        5|moderately steep, high convexity, fine-textured
        6|moderately steep, high convexity, coarse-textured
        7|moderately steep, low convexity, fine-textured
        8|moderately steep, low convexity, coarse-textured
        9|gentle, high convexity, fine-textured
        10|gentle, high convexity, coarse-textured
        11|gentle, low convexity, fine-textured
        12|gentle, low convexity, coarse-textured"""
    elif nclasses == 16:
        s = """1|steep, high convexity, fine-textured
        2|steep, high convexity, coarse-textured
        3|steep, low convexity, fine-textured
        4|steep, low convexity, coarse-textured
        5|moderately steep, high convexity, fine-textured
        6|moderately steep, high convexity, coarse-textured
        7|moderately steep, low convexity, fine-textured
        8|moderately steep, low convexity, coarse-textured
        9|slightly steep, high convexity, fine-textured
        10|slightly steep, high convexity, coarse-textured
        11|slightly steep, low convexity, fine-textured
        12|slightly steep, low convexity, coarse-textured
        13|gentle, high convexity, fine-textured
        14|gentle, high convexity, coarse-textured
        15|gentle, low convexity, fine-textured
        16|gentle, low convexity, coarse-textured"""
    return s


def colors(nclasses):
    if nclasses == 8:
        s = """
        1 139:92:20
        2 255:0:0
        3 255:165:0
        4 255:255:0
        5 0:0:255
        6 30:144:255
        7 0:128:0
        8 0:255:3
        nv 255:255:255
        default 255:255:255
        """
    elif nclasses == 12:
        s = """
        1 165:42:42
        2 255:0:0
        3 255:165:0
        4 255:255:0
        5 0:128:0
        6 11:249:11
        7 144:238:144
        8 227:255:227
        9 0:0:255
        10 30:144:255
        11 0:255:231
        12 173:216:230
        nv 255:255:255
        default 255:255:255
        """
    elif nclasses == 16:
        s = """
        1 165:42:42
        2 255:0:0
        3 255:165:0
        4 255:255:0
        5 0:128:0
        6 11:249:11
        7 144:238:144
        8 227:255:227
        9 128:0:128
        10 244:7:212
        11 234:109:161
        12 231:190:225
        13 0:0:255
        14 30:144:255
        15 0:255:231
        16 173:216:230
        nv 255:255:255
        default 255:255:255
        """
    return s


def string_to_rules(string):
    # Converts a string to a file for input as a GRASS Rules File

    tmp = gs.tempfile()
    f = open("%s" % (tmp), "wt")
    f.write(string)
    f.close()

    return tmp


def classification(level, slope, smean, texture, tmean, convexity, cmean, classif):
    # Classification scheme according to Iwahashi and Pike (2007)
    # Simple decision tree that classifies terrain features
    # (slope, texture, convexity) relative to central tendency of features
    #
    # Args:
    #   level: Nested classification level
    #   slope: String, name of slope raster
    #   smean: Float, mean of slope raster for the remaining level partition
    #   texture: String, name of terrain texture raster
    #   tmean: Float, mean of texture raster for remaining level partition
    #   convexity: String, name of convexity raster
    #   cmean: Float, mean of convexity raster for remaining level partition
    #   classif: String, name of map to store classification

    incr = (4 * level) - 4
    expr = "{x} = if({s}>{smean}, if({c}>{cmean}, if({t}<{tmean}, {i}+1, {i}+2), if({t}<{tmean}, {i}+3, {i}+4)), if({c}>{cmean}, if({t}<{tmean}, {i}+5, {i}+6), if({t}<{tmean}, {i}+7, {i}+8)))".format(
        x=classif,
        i=incr,
        s=slope,
        smean=smean,
        t=texture,
        tmean=tmean,
        c=convexity,
        cmean=cmean,
    )
    r.mapcalc(expression=expr)

    return 0


def main():

    elevation = options["elevation"]
    slope = options["slope"]
    flat_thres = float(options["flat_thres"])
    curv_thres = float(options["curv_thres"])
    filter_size = int(options["filter_size"])
    counting_size = int(options["counting_size"])
    nclasses = int(options["classes"])
    texture = options["texture"]
    convexity = options["convexity"]
    concavity = options["concavity"]
    features = options["features"]

    # remove mapset from output name in case of overwriting existing map
    texture = texture.split("@")[0]
    convexity = convexity.split("@")[0]
    concavity = concavity.split("@")[0]
    features = features.split("@")[0]

    # store current region settings
    global current_reg
    current_reg = parse_key_val(g.region(flags="pg", stdout_=PIPE).outputs.stdout)
    del current_reg["projection"]
    del current_reg["zone"]
    del current_reg["cells"]

    # check for existing mask and backup if found
    global mask_test
    mask_test = gs.list_grouped(type="rast", pattern="MASK")[gs.gisenv()["MAPSET"]]
    if mask_test:
        global original_mask
        original_mask = temp_map("tmp_original_mask")
        g.copy(raster=["MASK", original_mask])

    # error checking
    if flat_thres < 0:
        gs.fatal("Parameter thres cannot be negative")

    if filter_size % 2 == 0 or counting_size % 2 == 0:
        gs.fatal("Filter or counting windows require an odd-numbered window size")

    if filter_size >= counting_size:
        gs.fatal("Filter size needs to be smaller than the counting window size")

    if features != "" and slope == "":
        gs.fatal(
            "Need to supply a slope raster in order to produce the terrain classification"
        )

    # Terrain Surface Texture -------------------------------------------------
    # smooth the dem
    gs.message("Calculating terrain surface texture...")
    gs.message(
        "1. Smoothing input DEM with a {n}x{n} median filter...".format(n=filter_size)
    )
    filtered_dem = temp_map("tmp_filtered_dem")
    gs.run_command(
        "r.neighbors",
        input=elevation,
        method="median",
        size=filter_size,
        output=filtered_dem,
        flags="c",
        quiet=True,
    )

    # extract the pits and peaks based on the threshold
    pitpeaks = temp_map("tmp_pitpeaks")
    gs.message("2. Extracting pits and peaks with difference > thres...")
    r.mapcalc(
        expression="{x} = if ( abs({dem}-{median})>{thres}, 1, 0)".format(
            x=pitpeaks, dem=elevation, thres=flat_thres, median=filtered_dem
        ),
        quiet=True,
    )

    # calculate density of pits and peaks
    gs.message("3. Using resampling filter to create terrain texture...")
    window_radius = (counting_size - 1) / 2
    y_radius = float(current_reg["ewres"]) * window_radius
    x_radius = float(current_reg["nsres"]) * window_radius
    resample = temp_map("tmp_density")
    r.resamp_filter(
        input=pitpeaks,
        output=resample,
        filter=["bartlett", "gauss"],
        radius=[x_radius, y_radius],
        quiet=True,
    )

    # convert to percentage
    gs.message("4. Converting to percentage...")
    r.mask(raster=elevation, overwrite=True, quiet=True)
    r.mapcalc(
        expression="{x} = float({y} * 100)".format(x=texture, y=resample), quiet=True
    )
    r.mask(flags="r", quiet=True)
    r.colors(map=texture, color="haxby", quiet=True)

    # Terrain convexity/concavity ---------------------------------------------
    # surface curvature using lacplacian filter
    gs.message("Calculating terrain convexity and concavity...")
    gs.message("1. Calculating terrain curvature using laplacian filter...")

    # grow the map to remove border effects and run laplacian filter
    dem_grown = temp_map("tmp_elevation_grown")
    laplacian = temp_map("tmp_laplacian")
    g.region(
        n=float(current_reg["n"]) + (float(current_reg["nsres"]) * filter_size),
        s=float(current_reg["s"]) - (float(current_reg["nsres"]) * filter_size),
        w=float(current_reg["w"]) - (float(current_reg["ewres"]) * filter_size),
        e=float(current_reg["e"]) + (float(current_reg["ewres"]) * filter_size),
    )

    r.grow(input=elevation, output=dem_grown, radius=filter_size, quiet=True)
    r.mfilter(
        input=dem_grown,
        output=laplacian,
        filter=string_to_rules(laplacian_matrix(filter_size)),
        quiet=True,
    )

    # extract convex and concave pixels
    gs.message("2. Extracting convexities and concavities...")
    convexities = temp_map("tmp_convexities")
    concavities = temp_map("tmp_concavities")

    r.mapcalc(
        expression="{x} = if({laplacian}>{thres}, 1, 0)".format(
            x=convexities, laplacian=laplacian, thres=curv_thres
        ),
        quiet=True,
    )
    r.mapcalc(
        expression="{x} = if({laplacian}<-{thres}, 1, 0)".format(
            x=concavities, laplacian=laplacian, thres=curv_thres
        ),
        quiet=True,
    )

    # calculate density of convexities and concavities
    gs.message("3. Using resampling filter to create surface convexity/concavity...")
    resample_convex = temp_map("tmp_convex")
    resample_concav = temp_map("tmp_concav")
    r.resamp_filter(
        input=convexities,
        output=resample_convex,
        filter=["bartlett", "gauss"],
        radius=[x_radius, y_radius],
        quiet=True,
    )
    r.resamp_filter(
        input=concavities,
        output=resample_concav,
        filter=["bartlett", "gauss"],
        radius=[x_radius, y_radius],
        quiet=True,
    )

    # convert to percentages
    gs.message("4. Converting to percentages...")
    g.region(**current_reg)
    r.mask(raster=elevation, overwrite=True, quiet=True)
    r.mapcalc(
        expression="{x} = float({y} * 100)".format(x=convexity, y=resample_convex),
        quiet=True,
    )
    r.mapcalc(
        expression="{x} = float({y} * 100)".format(x=concavity, y=resample_concav),
        quiet=True,
    )
    r.mask(flags="r", quiet=True)

    # set colors
    r.colors_stddev(map=convexity, quiet=True)
    r.colors_stddev(map=concavity, quiet=True)

    # Terrain classification Flowchart-----------------------------------------
    if features != "":
        gs.message("Performing terrain surface classification...")
        # level 1 produces classes 1 thru 8
        # level 2 produces classes 5 thru 12
        # level 3 produces classes 9 thru 16
        if nclasses == 8:
            levels = 1
        if nclasses == 12:
            levels = 2
        if nclasses == 16:
            levels = 3

        classif = []
        for level in range(levels):
            # mask previous classes x:x+4
            if level != 0:
                min_cla = (4 * (level + 1)) - 4
                clf_msk = temp_map("tmp_clf_mask")
                rules = "1:{0}:1".format(min_cla)
                r.recode(
                    input=classif[level - 1],
                    output=clf_msk,
                    rules=string_to_rules(rules),
                    overwrite=True,
                )
                r.mask(raster=clf_msk, flags="i", quiet=True, overwrite=True)

            # image statistics
            smean = r.univar(map=slope, flags="g", stdout_=PIPE).outputs.stdout.split(
                os.linesep
            )
            smean = [i for i in smean if i.startswith("mean=") is True][0].split("=")[1]

            cmean = r.univar(
                map=convexity, flags="g", stdout_=PIPE
            ).outputs.stdout.split(os.linesep)
            cmean = [i for i in cmean if i.startswith("mean=") is True][0].split("=")[1]

            tmean = r.univar(map=texture, flags="g", stdout_=PIPE).outputs.stdout.split(
                os.linesep
            )
            tmean = [i for i in tmean if i.startswith("mean=") is True][0].split("=")[1]
            classif.append(temp_map("tmp_classes"))

            if level != 0:
                r.mask(flags="r", quiet=True)

            classification(
                level + 1,
                slope,
                smean,
                texture,
                tmean,
                convexity,
                cmean,
                classif[level],
            )

        # combine decision trees
        merged = []
        for level in range(0, levels):
            if level > 0:
                min_cla = (4 * (level + 1)) - 4
                merged.append(temp_map("tmp_merged"))
                r.mapcalc(
                    expression="{x} = if({a}>{min}, {b}, {a})".format(
                        x=merged[level],
                        min=min_cla,
                        a=merged[level - 1],
                        b=classif[level],
                    )
                )
            else:
                merged.append(classif[level])
        g.rename(raster=[merged[-1], features], quiet=True)
        del TMP_RAST[-1]

    # Write metadata ----------------------------------------------------------
    history = "r.terrain.texture "
    for key, val in options.items():
        history += key + "=" + str(val) + " "

    r.support(
        map=texture,
        title=texture,
        description="generated by r.terrain.texture",
        history=history,
    )
    r.support(
        map=convexity,
        title=convexity,
        description="generated by r.terrain.texture",
        history=history,
    )
    r.support(
        map=concavity,
        title=concavity,
        description="generated by r.terrain.texture",
        history=history,
    )

    if features != "":
        r.support(
            map=features,
            title=features,
            description="generated by r.terrain.texture",
            history=history,
        )

        # write color and category rules to tempfiles
        r.category(
            map=features, rules=string_to_rules(categories(nclasses)), separator="pipe"
        )
        r.colors(map=features, rules=string_to_rules(colors(nclasses)), quiet=True)

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
