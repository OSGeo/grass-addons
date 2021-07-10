#!/usr/bin/env python

############################################################################
# MODULE:         Locate suitable regions
# AUTHOR(S):      Paulo van Breugel
# PURPOSE:        From suitability map to suitable regions
# COPYRIGHT: (C) 2021 by Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
##############################################################################

#%module
#% description: From suitability map to suitable regions
#%end

#%option G_OPT_R_INPUT
#% label: Suitability raster
#% description: Raster layer represting suitability (0-1)
#% required: yes
#% multiple: no
#% guisection: Input
#%end

#%option G_OPT_R_OUTPUT
#% label: Output raster
#% description: Raster with candidate regions for conservation
#% required: yes
#% multiple: no
#% guisection: Input
#%end

#%option
#% key: suitability_threshold
#% description: Threshold value above which areas are considered suitable
#% required: yes
#% type: string
#% key_desc: float
#% guisection: Input
#%end

#%option
#% key: minimum_size
#% description: Minimum area (in hectares) limit for fragments
#% required: yes
#% type: string
#% key_desc: float
#% guisection: Input
#%end

#%option
#% key: minimum_suitability
#% description: Threshold below which cells are marked as fully unsuitable
#% required: no
#% type: string
#% key_desc: float
#% guisection: Input
#%end

#%flag
#% key: d
#% description: Diagonally neighboring cells are considerd part of the same region
#% guisection: Optional
#%end

#%option
#% key: radius
#% description: Radius for focal stat
#% required: no
#% type: integer
#% answer: 1
#% guisection: Focal stats
#%end

#%flag
#% key: c
#% description: Use circular neighborhood for focal statistic
#% guisection: Focal stats
#%end

#%option
#% key: focal_statistic
#% description: Neighborhood operation (focal statistic)
#% required: no
#% type: string
#% answer: median
#% options:maximum,median,quart1,quart3
#% guisection: Focal stats
#%end

#%option
#% key: maximum_gap
#% description: Maximum gap size (in hectares) to remove
#% required: no
#% type: string
#% answer: 0
#% key_desc: float
#% guisection: Remove gaps
#%end

#%flag
#% key: z
#% description: Compute map with average suitability per region
#% guisection: Reporting stats
#%end

#%flag
#% key: a
#% description: Calculates area of clumped areas (hectares)
#% guisection: Reporting stats
#%end

#%flag
#% key: k
#% description: Keep map that show suitable areas (irrespective of clump size)
#% guisection: Optional
#%end

#%flag
#% key: f
#% description: Keep suitabiliyt based on focal statistics
#% guisection: Optional
#%end

#%flag
#% key: v
#% description: Create vector layer with suitabilty and compactness statistics
#% guisection: Optional
#%end

#%flag
#% key: m
#% description: Compute compactness of selected areas
#% guisection: Optional
#%end


import sys
import atexit
import uuid
import grass.script as gs

CLEAN_LAY = []
try:
    from grass.script import append_node_pid as create_unique_name
except ImportError:

    def create_unique_name(name):
        """Generate a tmp name which contains prefix
        Store the name in the global list.
        Use only for raster maps.
        """
        return name + str(uuid.uuid4().hex)


def create_temporary_name(prefix):
    tmpf = create_unique_name(prefix)
    CLEAN_LAY.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_LAY))
    for rast in cleanrast:
        ffile = gs.find_file(name=rast, element="cell", mapset=gs.gisenv()["MAPSET"])
        if ffile["file"]:
            gs.run_command("g.remove", flags="f", type="raster", name=rast, quiet=True)


def tmpmask(raster, absolute_minimum):
    """Create tmp mask"""
    rules = "*:{}:1".format(absolute_minimum)
    tmprecode = create_temporary_name("tmprecode")
    gs.write_command(
        "r.recode", input=raster, output=tmprecode, rule="-", stdin=rules, quiet=True
    )
    return tmprecode


def main(options, flags):

    # Variables
    in_filename = options["input"]
    out_filename = options["output"]
    suitability_threshold = float(options["suitability_threshold"])
    minimum_suitability = options["minimum_suitability"]
    minimum_size = float(options["minimum_size"])
    radius = int(options["radius"])
    if (radius % 2) == 0:
        gs.fatal("Radius should be an odd positive number")
    focal_statistic = options["focal_statistic"]
    maximum_gap = float(options["maximum_gap"])

    # Flags
    if flags["c"]:
        neighbor_flag = "c"
    else:
        neighbor_flag = ""
    if flags["d"]:
        clump_flag = "d"
    else:
        clump_flag = ""
    region_suitability_flag = flags["z"]
    keep_suitable_cells_flag = flags["k"]
    keep_focal_stats_flag = flags["f"]
    clump_areas_flag = flags["a"]

    # Compute neighborhood statistic
    if radius > 1 and len(minimum_suitability) == 0:
        gs.message("Computing neighborhood statistic")
        gs.message("================================\n")
        tmp00 = create_temporary_name("tmp00")
        gs.run_command(
            "r.neighbors",
            flags=neighbor_flag,
            input=in_filename,
            output=tmp00,
            method=focal_statistic,
            size=radius,
        )
        tmp02 = create_temporary_name("tmp02")
        gs.run_command(
            "r.series", input=[in_filename, tmp00], method="maximum", output=tmp02
        )
    elif radius > 1:
        gs.message("Computing neighborhood statistic")
        gs.message("================================\n")
        try:
            float(minimum_suitability)
        except TypeError:
            gs.fatal("minimum_suitability must be numeric or left empty")
        tmp01 = create_temporary_name("tmp01")
        gs.run_command(
            "r.neighbors",
            flags=neighbor_flag,
            input=in_filename,
            output=tmp01,
            method=focal_statistic,
            size=radius,
        )
        tmp00 = create_temporary_name("tmp00")
        gs.run_command(
            "r.series", input=[in_filename, tmp01], method="maximum", output=tmp00
        )
        tmp02 = create_temporary_name("tmp02")
        gs.run_command(
            "r.mapcalc",
            expression=(
                "{0} = if({1} > {2},{3},null())".format(
                    tmp02, in_filename, minimum_suitability, tmp00
                )
            ),
        )
    else:
        tmp02 = create_temporary_name("tmp02")
        gs.run_command("g.copy", raster=[in_filename, tmp02], quiet=True)

    # Convert suitability to boolean: suitable (1) or not (nodata)
    gs.message("Creating boolean map suitable/none-suitable")
    gs.message("===========================================\n")
    tmp03 = create_temporary_name("tmp03")
    gs.run_command(
        "r.mapcalc",
        expression=(
            "{} = if({} >= {},1,null())".format(tmp03, tmp02, suitability_threshold)
        ),
    )

    # Clump contiguous cells (adjacent celss with same value) and
    # remove clumps that are below user provided size
    gs.message("Clumping continuous cells and removing small fragments")
    gs.message("======================================================\n")
    tmp04 = create_temporary_name("tmp04")
    gs.run_command(
        "r.reclass.area",
        flags=clump_flag,
        input=tmp03,
        output=tmp04,
        value=minimum_size,
        mode="greater",
        method="reclass",
    )

    # Remove gaps within suitable regions with size smaller than maxgap
    # Note, in the reclass.area module below mode 'greater' is used because
    # 1/nodata is reversed. The last step (clump) is to assign unique values
    # to the clumps, which makes it easier to filter and analyse results
    if maximum_gap > 0:
        gs.message("Removing small gaps of non-suitable areas - step 1")
        gs.message("==================================================\n")
        tmp05 = create_temporary_name("tmp05")
        expr = "{} = if(isnull({}),1,null())".format(tmp05, tmp04)
        gs.run_command("r.mapcalc", expression=expr)
        gs.message("Removing small gaps of non-suitable areas - step 2")
        gs.message("==================================================\n")
        tmp06 = create_temporary_name("tmp06")
        gs.run_command(
            "r.reclass.area",
            input=tmp05,
            output=tmp06,
            value=maximum_gap,
            mode="greater",
            method="reclass",
        )
        gs.message("Removing small gaps of non-suitable areas - step 3")
        gs.message("==================================================\n")
        tmp08 = create_temporary_name("tmp08")
        expr3 = "{} = int(if(isnull({}),1,null()))".format(tmp08, tmp06)
        gs.run_command("r.mapcalc", expression=expr3)
        tmp09 = create_temporary_name("tmp09")
        if len(minimum_suitability) > 0:
            bumask = tmpmask(raster=in_filename, absolute_minimum=minimum_suitability)
            gs.run_command(
                "r.mapcalc",
                expression=(
                    "{} = if(isnull({}), {}, null())".format(tmp09, bumask, tmp08)
                ),
            )
        else:
            gs.run_command("g.rename", raster=[tmp08, tmp09], quiet=True)

        # Create map with category clump-suitable, clump-unsuitable
        gs.message("Create map with category clump-suitable, clump-unsuitable")
        gs.message("=======================================================\n")
        filledgaps = "{}_filledgaps".format(out_filename)
        gs.run_command(
            "r.series",
            output=filledgaps,
            input=[tmp04, tmp09],
            method="sum",
        )
        RECLASS_FILLEDGAPS = """
        1:filled gaps\n2:suitable areas
        """.strip()
        gs.write_command(
            "r.category",
            map=filledgaps,
            rules="-",
            separator=":",
            stdin=RECLASS_FILLEDGAPS,
        )

        # Assign unique ids to clumps
        gs.message("Assigning unique id's to clumps")
        gs.message("==============================\n")
        gs.run_command("r.clump", flags=clump_flag, input=tmp09, output=out_filename)
        gs.run_command(
            "r.support",
            map=filledgaps,
            title="Regions + filled gaps",
            units="2 = suitable, 1 = filled gaps",
            description=(
                "Map indicating which cells of the",
                "\nidentified regions are suitable,",
                "\nand which are gaps included\n",
            ),
        )
        COLORS_FILLEDGAPS = """
        1 241:241:114
        2 139:205:85
        """.strip()
        gs.write_command("r.colors", rules="-", map=filledgaps, stdin=COLORS_FILLEDGAPS)

    else:
        # Assign unique ids to clumps
        gs.message("Assigning unique id's to clumps")
        gs.message("================================\n")
        gs.run_command("r.clump", flags=clump_flag, input=tmp04, output=out_filename)
    gs.run_command(
        "r.support",
        map=out_filename,
        title="Suitable regions",
        units="IDs of suitable regions",
        description=(
            "Map with potential areas for conservation"
            "\n, Based on the suitability layer {}\n".format(in_filename)
        ),
    )
    # Keep map with all suitable areas
    if clump_areas_flag:
        gs.message("Compute area per clump")
        gs.message("====================\n")
        areastat = "{}_clumpsize".format(out_filename)
        tmp10 = create_temporary_name("tmp10")
        gs.run_command("r.area", input=out_filename, output=tmp10)
        gs.run_command(
            "r.mapcalc",
            expression=("{} = {} * area()/10000".format(areastat, tmp10)),
        )

    # Zonal statistics
    if region_suitability_flag:
        gs.message("Compute average suitability per clump")
        gs.message("=====================================\n")
        zonstat = "{}_averagesuitability".format(out_filename)
        gs.run_command(
            "r.stats.zonal",
            base=out_filename,
            cover=in_filename,
            method="average",
            output=zonstat,
        )
        gs.run_command("r.colors", map=zonstat, color="bgyr")
    gs.message("Done")

    # Vector as output
    if flags["v"]:
        gs.message("Compute vector with statistis")
        gs.message("===========================\n")
        zonstat = "{}_averagesuitability".format(out_filename)
        gs.run_command(
            "r.to.vect",
            flags="v",
            input=out_filename,
            output=out_filename,
            type="area",
        )
        gs.run_command("v.to.db", map=out_filename, option="area", columns="area")
        gs.run_command(
            "v.to.db", map=out_filename, option="compact", columns="compactness"
        )
        gs.run_command("v.to.db", map=out_filename, option="fd", columns="fd")
        gs.run_command(
            "v.rast.stats",
            map=out_filename,
            raster=in_filename,
            column_prefix="AA",
            method="average",
        )
        gs.run_command(
            "v.db.renamecolumn",
            map=out_filename,
            column="{},{}".format("AA_average", "mean_suitability"),
        )

    # Compactness
    if flags["m"]:
        gs.message("compactness, fractal dimension and average suitability")
        gs.message("====================================================\n")
        compactness = "{}_compactness".format(out_filename)
        if flags["v"]:
            gs.run_command(
                "v.to.rast",
                input=out_filename,
                output=compactness,
                use="attr",
                attribute_column="compactness",
            )
        else:
            tmp11 = create_temporary_name("tmp11")
            gs.run_command(
                "r.to.vect", flags="v", input=out_filename, output=tmp11, type="area"
            )
            gs.run_command(
                "v.to.db", map=tmp11, option="compact", columns="compactness"
            )
            gs.run_command(
                "v.to.rast",
                input=tmp11,
                output=compactness,
                use="attr",
                attribute_column="compactness",
            )
            gs.run_command(
                "g.remove",
                type="vector",
                name=tmp11,
                flags="f",
                quiet=True,
            )

    # Keep map with all suitable areas
    if keep_suitable_cells_flag:
        rname = "{}_allsuitableareas".format(out_filename)
        gs.run_command("g.rename", raster=[tmp03, rname], quiet=True)
        COLORS_ALLSUITABLEAREAS = """
        1 230:230:230
        """.strip()
        gs.write_command(
            "r.colors", rules="-", map=rname, stdin=COLORS_ALLSUITABLEAREAS
        )

    # Keep suitability map based on focal statistic
    if keep_focal_stats_flag:
        rname2 = "{}_focalsuitability".format(out_filename)
        gs.run_command("g.rename", raster=[tmp02, rname2], quiet=True)
        gs.run_command("r.colors", map=rname2, raster=in_filename)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
