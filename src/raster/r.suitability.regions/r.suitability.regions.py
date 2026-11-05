#!/usr/bin/env python

############################################################################
# MODULE:         Locate suitable regions
# AUTHOR(S):      Paulo van Breugel
# PURPOSE:        From suitability map to suitable regions
# COPYRIGHT: (C) 2021-2026 by Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
##############################################################################

# %module
# % description: From suitability map to suitable regions
# %end

# %option G_OPT_R_INPUT
# % label: Suitability raster
# % description: Raster layer represting suitability (0-1)
# % required: yes
# % multiple: no
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % label: Output raster
# % description: Raster with candidate regions for conservation
# % required: yes
# % multiple: no
# % guisection: Input
# %end

# %option
# % key: suitability_threshold
# % label: Threshold suitability score
# % description: The minimum suitability score to be included. For example, with a threshold of 0.7, all raster cells with a suitability of 0.7 are used as input in the delineation of contiguous suitable regions.
# % type: string
# % key_desc: float
# % guisection: Input
# %end

# %option
# % key: percentile_threshold
# % label: Percentile threshold (deprecated)
# % description: Percentile above which suitability scores are included in the search for suitable regions. For example, using a 0.95 percentile means that the raster cells with the 5% highest suitability scores are are used as input in the delineation of contiguous suitable regions (deprecated, use percentage instead).
# % type: string
# % key_desc: percentile
# %end

# %option
# % key: percentage
# % label: Percentage to select
# % description: The percentage of raster cells with the highest suitability scores that are to be used as input in the delineation of contiguous suitable regions.
# % type: string
# % key_desc: percentage
# % guisection: Input
# %end

# %rules
# % required: suitability_threshold,percentage,percentile_threshold
# % exclusive: suitability_threshold,percentage,percentile_threshold
# %end

# %option
# % key: minimum_size
# % label: Minimum area (in hectares)
# % description: Contiguous regions need to have a minimum area to be included.
# % required: yes
# % type: string
# % key_desc: float
# % guisection: Input
# %end

# %option
# % key: minimum_suitability
# % label: Threshold for unsuitable areas
# % description: This option can be used to mark cells with a suitability equal or less than the given threshold as unsuitable. Can be used in conjuction with the 'focal statistics' option to ensure that those cells are marked as unsuitable (barriers), irrespective of the suitability scores of the surrounding cells.
# % required: no
# % type: string
# % key_desc: float
# % guisection: Input
# %end

# %flag
# % key: d
# % label: Clumps including diagonal neighbors
# % description: Diagonal neighboring cells are considerd to be connected, and will therefore be consiered part of the same region.
# % guisection: Optional
# %end

# %option
# % key: size
# % label: Neighborhood size
# % description: The neighborhood size specifies which cells surrounding any given cell fall into the neighborhood for that cell. The size must be an odd integer and represent the length of one of moving window edges in cells. See the manual page of r.neighbors for more details
# % required: no
# % type: integer
# % answer: 1
# % guisection: Focal stats
# %end

# %flag
# % key: c
# % label: Circular neighborhood for focal statistics
# % description: Use circular neighborhood when computing the focal statistic
# % guisection: Focal stats
# %end

# %option
# % key: focal_statistic
# % Label: Neighborhood operation (focal statistic)
# % description: The median, maximum, first or 3rd quartile of the cells in a neighborhood of user-defined size is computed. This aggregated suitability score is used instead of the original suitability score to determine which raster cells are used as input in the delineation of contiguous suitable regions.
# % required: no
# % type: string
# % answer: median
# % options:maximum,median,quart1,quart3
# % guisection: Focal stats
# %end

# %option
# % key: maximum_gap
# % label: Maximum gap size (hectares)
# % description: Fill only enclosed unsuitable gaps up to this size (hectares). Gaps connected to the computational region boundary, containing input NoData, or containing excluded barrier cells are not filled.
# % required: no
# % type: string
# % answer: 0
# % key_desc: float
# % guisection: Remove gaps
# %end

# %flag
# % key: z
# % label: Average suitability per region
# % description: Create a map in which each region has a value corresponding to the average suitability of that region.
# % guisection: Reporting stats
# %end

# %flag
# % key: a
# % label: Area of the regions
# % description: Create a map in which each region has a value corresponding to the surface area (hectares) of that region.
# % guisection: Reporting stats
# %end

# %flag
# % key: k
# % label: Suitable areas
# % description: Map showing all raster cells with a suitability equal or above the user-defined threshold
# % guisection: Optional
# %end

# %flag
# % key: f
# % label: Suitable areas (focal statistics)
# % description: Map showing all raster cells with an aggregated suitability score based on a user-defined neighhborhood size that is equal or above a user-defined minimum_suitability threshold.
# % guisection: Optional
# %end

# %flag
# % key: v
# % label: Vector output layer
# % description: Create vector layer with suitabilty and compactness statistics
# % guisection: Optional
# %end

# %flag
# % key: m
# % description: Compactness
# % description: Compute compactness of selected suitable regions.
# % guisection: Optional
# %end

# %option G_OPT_M_NPROCS
# %end

# %option G_OPT_MEMORYMB
# %end

import sys
import atexit
import uuid
import grass.script as gs

CLEAN_LAY = []


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


def main(options, flags):
    # Variables
    in_filename = options["input"]
    out_filename = options["output"]
    suitability_threshold = options["suitability_threshold"]
    percentile_threshold = options["percentile_threshold"]
    if options["percentage"]:
        percentile_threshold = 100 - float(options["percentage"])
    minimum_suitability = options["minimum_suitability"]
    minimum_size = float(options["minimum_size"])
    size = int(options["size"])
    if (size % 2) == 0:
        gs.fatal("size should be an odd positive number")
    focal_statistic = options["focal_statistic"]
    maximum_gap = float(options["maximum_gap"])
    memory = options["memory"]
    nprocs = options["nprocs"]

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
    if size > 1 and len(minimum_suitability) == 0:
        gs.message(_("Computing neighborhood statistic"))
        gs.message(_("================================\n"))
        tmp00 = create_temporary_name("tmp00")
        gs.run_command(
            "r.neighbors",
            flags=neighbor_flag,
            input=in_filename,
            output=tmp00,
            method=focal_statistic,
            size=size,
            nprocs=nprocs,
            memory=memory,
        )
        tmp02 = create_temporary_name("tmp02")
        gs.run_command(
            "r.series",
            input=[in_filename, tmp00],
            method="maximum",
            output=tmp02,
            nprocs=nprocs,
            memory=memory,
        )
    elif size > 1:
        gs.message(_("Computing neighborhood statistic"))
        gs.message(_("================================\n"))
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
            size=size,
            nprocs=nprocs,
            memory=memory,
        )
        tmp00 = create_temporary_name("tmp00")
        gs.run_command(
            "r.series",
            input=[in_filename, tmp01],
            method="maximum",
            output=tmp00,
            nprocs=nprocs,
            memory=memory,
        )
        tmp02 = create_temporary_name("tmp02")
        gs.run_command(
            "r.mapcalc",
            expression=(
                "{0} = if({1} > {2},{3},null())".format(
                    tmp02, in_filename, minimum_suitability, tmp00
                )
            ),
            nprocs=nprocs,
        )
    else:
        tmp02 = create_temporary_name("tmp02")
        gs.run_command("g.copy", raster=[in_filename, tmp02], quiet=True)

    # Convert suitability to boolean: suitable (1) or not (nodata)
    gs.message(_("Creating boolean map suitable/none-suitable"))
    gs.message(_("===========================================\n"))

    if suitability_threshold == "":
        qrule = (
            gs.read_command(
                "r.quantile",
                input=in_filename,
                percentiles=percentile_threshold,
                quiet=True,
            )
            .replace("\n", "")
            .split(":")[2]
        )
        suitability_threshold = float(qrule)
    else:
        suitability_threshold = float(suitability_threshold)

    tmp03 = create_temporary_name("tmp03")
    gs.run_command(
        "r.mapcalc",
        expression=(
            "{} = if({} >= {},1,null())".format(tmp03, tmp02, suitability_threshold)
        ),
        nprocs=nprocs,
    )

    # Clump contiguous cells (adjacent celss with same value) and
    # remove clumps that are below user provided size
    gs.message(_("Clumping continuous cells and removing small fragments"))
    gs.message(_("======================================================\n"))
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

    # Fill only enclosed gaps within the retained suitable regions.
    # The background of tmp04 also contains original input NULL cells and cells
    # discarded by minimum_size. Inverting the small-area filter alone
    # inadvertently include open background
    # patches and introduce isolated cells into the result.
    if maximum_gap > 0:
        gs.message(_("Identifying enclosed gaps within suitable regions"))
        gs.message(_("=================================================\n"))

        # Label entire connected background components, including input NULLs.
        # Use the same -d choice as for the suitable regions (clump_flag), so
        # "connected" means the same thing on both sides of the boundary.
        background = create_temporary_name("tmp_background")
        gs.run_command(
            "r.mapcalc",
            expression="{} = if(isnull({}), 1, null())".format(background, tmp04),
            nprocs=nprocs,
        )
        background_clumps = create_temporary_name("tmp_background_clumps")
        gs.run_command(
            "r.clump", flags=clump_flag, input=background, output=background_clumps
        )

        # Select complete background components no larger than maximum_gap ha.
        # -c tells r.reclass.area that the input already contains clump IDs.
        small_gaps = create_temporary_name("tmp_small_gaps")
        gs.run_command(
            "r.reclass.area",
            flags="c",
            input=background_clumps,
            output=small_gaps,
            value=maximum_gap,
            mode="lesser",
            method="reclass",
        )

        # A gap will not be filled part of explicitly excluded barrier,
        # or when it touches the computational region's boundary.
        # Flag such cells with 1 and all other cells with 0 (including
        # cells outside the candidate gaps).
        if minimum_suitability:
            try:
                barrier_threshold = float(minimum_suitability)
            except ValueError:
                gs.fatal(_("minimum_suitability must be numeric or left empty"))
            invalid_input = "if({} <= {}, 1, 0)".format(in_filename, barrier_threshold)
        else:
            invalid_input = "0"
        excluded_cells = create_temporary_name("tmp_excluded_cells")
        gs.run_command(
            "r.mapcalc",
            expression=(
                "{} = if(row() == 1 || row() == nrows() || "
                "col() == 1 || col() == ncols(), 1, "
                "if(isnull({}), 1, {}))"
            ).format(excluded_cells, in_filename, invalid_input),
            nprocs=nprocs,
        )

        # A zonal maximum of 0 means that the whole connected component is
        # enclosed and eligible; 1 means it intersects a forbidden cell.
        excluded_by_gap = create_temporary_name("tmp_excluded_by_gap")
        gs.run_command(
            "r.stats.zonal",
            base=small_gaps,
            cover=excluded_cells,
            method="max",
            output=excluded_by_gap,
        )
        valid_gaps = create_temporary_name("tmp_valid_gaps")
        gs.run_command(
            "r.mapcalc",
            expression="{} = if({} == 0, 1, null())".format(
                valid_gaps, excluded_by_gap
            ),
            nprocs=nprocs,
        )

        # Merge only accepted holes with the original, size-filtered regions.
        # No input NULL or barrier cell may be introduced.
        merged_regions = create_temporary_name("tmp_merged_regions")
        gs.run_command(
            "r.mapcalc",
            expression="{} = if(isnull({}), {}, 1)".format(
                merged_regions, tmp04, valid_gaps
            ),
            nprocs=nprocs,
        )

        # Apply minimum_size again to the actual final mask, avoiding any
        # undersized fragments, including if an unexpected partial gap remains.
        final_regions = create_temporary_name("tmp_final_regions")
        gs.run_command(
            "r.reclass.area",
            flags=clump_flag,
            input=merged_regions,
            output=final_regions,
            value=minimum_size,
            mode="greater",
            method="reclass",
        )

        # Diagnostic: 1 denotes added gap cells; 2 denotes original suitable
        # cells. Do not display cells absent from the final region output.
        filledgaps = "{}_filledgaps".format(out_filename)
        gs.run_command(
            "r.mapcalc",
            expression="{} = if(isnull({}), null(), if(isnull({}), 1, 2))".format(
                filledgaps, final_regions, tmp04
            ),
            nprocs=nprocs,
        )
        RECLASS_FILLEDGAPS = "1:filled gaps\n2:suitable areas"
        gs.write_command(
            "r.category",
            map=filledgaps,
            rules="-",
            separator=":",
            stdin=RECLASS_FILLEDGAPS,
        )

        # Assign unique IDs only after both minimum-size filters are applied.
        gs.message(_("Assigning unique IDs to final regions"))
        gs.message(_("=====================================\n"))
        gs.run_command(
            "r.clump", flags=clump_flag, input=final_regions, output=out_filename
        )
        gs.run_command(
            "r.support",
            map=filledgaps,
            title="Regions + filled gaps",
            units="2 = suitable, 1 = filled gaps",
            description=(
                "Map indicating which cells of the final regions were originally "
                "suitable (2) or were enclosed gaps added to the regions (1)"
            ),
        )
        COLORS_FILLEDGAPS = "1 241:241:114\n2 139:205:85"
        gs.write_command("r.colors", rules="-", map=filledgaps, stdin=COLORS_FILLEDGAPS)

    else:
        # Assign unique ids to clumps
        gs.message(_("Assigning unique id's to clumps"))
        gs.message(_("================================\n"))
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
        gs.message(_("Compute area per clump"))
        gs.message(_("====================\n"))
        areastat = "{}_clumpsize".format(out_filename)
        tmp10 = create_temporary_name("tmp10")
        gs.run_command("r.area", input=out_filename, output=tmp10)
        gs.run_command(
            "r.mapcalc",
            expression=("{} = {} * area()/10000".format(areastat, tmp10)),
            nprocs=nprocs,
        )

    # Zonal statistics
    if region_suitability_flag:
        gs.message(_("Compute average suitability per clump"))
        gs.message(_("=====================================\n"))
        zonstat = "{}_averagesuitability".format(out_filename)
        gs.run_command(
            "r.stats.zonal",
            base=out_filename,
            cover=in_filename,
            method="average",
            output=zonstat,
        )
        gs.run_command("r.colors", map=zonstat, color="bgyr")
    gs.message(_("Done"))

    # Vector as output
    if flags["v"]:
        gs.message(_("Compute vector with statistis"))
        gs.message(_("===========================\n"))
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
        gs.message(_("compactness, fractal dimension and average suitability"))
        gs.message(_("====================================================\n"))
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

    if options["suitability_threshold"] == "":
        gs.message(_("\n---------------------------------------------------\n"))
        gs.message(_("Suitability threshold = {}").format(suitability_threshold))
        gs.message(_("Minimum area = {} hectares").format(minimum_size))
        gs.message(_("\n\n"))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
