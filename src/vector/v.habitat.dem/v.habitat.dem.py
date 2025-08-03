#!/usr/bin/env python

"""
MODULE:    v.habitat.dem

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   DEM and solar derived characteristics of habitats

COPYRIGHT: (C) 2014 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: Calculates DEM derived characteristics of habitats.
# % keyword: vector
# % keyword: raster
# % keyword: terrain
# % keyword: statistics
# % keyword: sun
# % keyword: zonal statistics
# %end

# %option G_OPT_R_ELEV
# % key: elevation
# % description: Name of elevation raster map
# % required: yes
# %end

# %option G_OPT_V_INPUT
# % key: vector
# % description: Name of habitat vector map
# % required: yes
# %end

# %option G_OPT_DB_COLUMN
# % description: Name of attribute column with a unique habitat ID (must be numeric)
# % required: yes
# %end

# %option
# % key: prefix
# % type: string
# % key_desc: prefix
# % description: output prefix (must start with a letter)
# % required: yes
# %end

# %option G_OPT_M_DIR
# % key: dir
# % description: Directory where the output will be found
# % required : yes
# %end

# %option
# % key: region_extension
# % type: double
# % key_desc: float
# % description: region extension
# % required : no
# % answer: 5000
# %end

# %option
# % key: start_time
# % type: double
# % label: Start time of interval
# % description: Use up to 2 decimal places
# % options: 0-24
# % answer: 8
# %end

# %option
# % key: end_time
# % type: double
# % label: End time of interval
# % description: Use up to 2 decimal places
# % options: 0-24
# % answer: 18
# %end

# %option
# % key: time_step
# % type: double
# % label: Time step for running r.sun [decimal hours]
# % description: Use up to 2 decimal places
# % options: 0-24
# % answer: 1
# %end

# %option
# % key: day
# % type: integer
# % description: No. of day of the year
# % options: 1-365
# % answer: 172
# %end

# %option
# % key: year
# % type: integer
# % label: Year used for map registration into temporal dataset or r.timestamp
# % description: This value is not used in r.sun calculations
# % options: 1900-9999
# % answer: 2014
# %end

import sys
import os
import grass.script as gs
import math
from numpy import array
from numpy import zeros
import csv


def main():
    r_elevation = options["elevation"].split("@")[0]
    v_habitat = options["vector"].split("@")[0]
    v_column = options["column"]
    regext = options["region_extension"]
    directory = options["dir"]
    prefix = options["prefix"]
    r_accumulation = prefix + "_accumulation"
    r_drainage = prefix + "_drainage"
    r_tci = prefix + "_topographicindex"
    r_slope = prefix + "_slope"
    r_aspect = prefix + "_aspect"
    r_flow_accum = prefix + "_flow_accumulation"
    r_LS = prefix + "_LS_factor"
    r_habitat = prefix + "_" + v_habitat + "_rast"
    r_geomorphon = prefix + "_" + r_elevation + "_geomorphon"
    r_beam_rad = prefix + "_beam_rad"
    f_habitat_small_areas = prefix + "_small_areas.csv"
    f_habitat_geomorphons = prefix + "_habitat_geomorphons.csv"
    f_habitat_geomorphons_pivot = prefix + "_habitat_geomorphons_pivot.csv"
    f_LS_colorrules = prefix + "_LS_color.txt"
    t_habitat_geomorphons = prefix + "_habgeo_tab"
    t_habitat_geomorphons_pivot = prefix + "_habgeo_tab_pivot"
    d_start_time = options["start_time"]
    d_end_time = options["end_time"]
    d_time_step = options["time_step"]
    d_day = options["day"]
    d_year = options["year"]
    saved_region = prefix + "_region_ori"
    current_region = gs.region()
    X = float(regext)
    N = current_region["n"]
    S = current_region["s"]
    E = current_region["e"]
    W = current_region["w"]
    Yres = current_region["nsres"]
    Xres = current_region["ewres"]
    PixelArea = Xres * Yres
    global tmp

    ## check if r.sun.hourly addon is installed
    if not gs.find_program("r.sun.hourly", "--help"):
        gs.fatal(
            _("The 'r.sun.hourly' addon was not found, install it first:")
            + "\n"
            + "g.extension r.sun.hourly"
        )

    # Region settings
    gs.message("Current region will be saved and extended.")
    gs.message("----")

    # Print and save current region
    gs.message("Current region:")
    gs.message("n, s, e, w")
    gs.message([current_region[key] for key in "nsew"])
    gs.run_command("g.region", save=saved_region, overwrite=True)
    gs.message("Current region saved.")
    gs.message("----")

    # does vector map exist in CURRENT mapset?
    mapset = gs.gisenv()["MAPSET"]
    exists = bool(gs.find_file(v_habitat, element="vector", mapset=mapset)["file"])
    if not exists:
        gs.fatal(_("Vector map <%s> not found in current mapset") % v_habitat)

    # Align region to elevation raster and habitat vector
    gs.message("Align region to elevation raster and habitat vector ...")
    gs.run_command(
        "g.region", flags="a", rast=r_elevation, vect=v_habitat, align=r_elevation
    )
    gs.message("Alignment done.")

    aligned_region = gs.region()
    Naligned = aligned_region["n"]
    Saligned = aligned_region["s"]
    Ealigned = aligned_region["e"]
    Waligned = aligned_region["w"]

    gs.message("Aligned region:")
    gs.message("n, s, e, w")
    gs.message([aligned_region[key] for key in "nsew"])
    gs.message("----")

    # Extend region
    gs.message("Extend region by")
    gs.message(regext)
    gs.message("in all directions")

    gs.run_command(
        "g.region", n=Naligned + X, s=Saligned - X, e=Ealigned + X, w=Waligned - X
    )
    gs.message("Region extension done.")

    extended_region = gs.region()

    gs.message("Extended region:")
    gs.message("n, s, e, w")
    gs.message([extended_region[key] for key in "nsew"])
    gs.message("----")

    # Watershed calculation: accumulation, drainage direction, topographic index
    gs.message(
        "Calculation of accumulation, drainage direction, topographic index by r.watershed ..."
    )
    gs.run_command(
        "r.watershed",
        elevation=r_elevation,
        accumulation=r_accumulation,
        drainage=r_drainage,
        tci=r_tci,
        convergence=5,
        flags="am",
        overwrite=True,
    )
    gs.message("Calculation of accumulation, drainage direction, topographic done.")
    gs.message("----")

    # Calculation of slope and aspect maps
    gs.message("Calculation of slope and aspect by r.slope.aspect ...")
    gs.run_command(
        "r.slope.aspect",
        elevation=r_elevation,
        slope=r_slope,
        aspect=r_aspect,
        overwrite=True,
    )
    gs.message("Calculation of slope and aspect done.")
    gs.message("----")

    # Calculate pixel area by nsres x ewres
    gs.message("Pixel area:")
    gs.message(PixelArea)
    gs.message("----")

    # Calculate habitat area and populate it to the attribute table
    gs.message("Calculate habitat's areas and populate it to the attribute table ...")
    gs.run_command("v.db.addcolumn", map=v_habitat, layer=1, columns="habarea double")

    gs.run_command(
        "v.to.db",
        map=v_habitat,
        option="area",
        layer=1,
        columns="habarea",
        overwrite=True,
    )

    gs.message("Calculate habitat's areas done.")
    gs.message("----")

    # Show habitat areas smaller than Pixel Area
    gs.message("Habitat areas smaller than pixel area.")
    gs.run_command(
        "v.db.select",
        map=v_habitat,
        format="vertical",
        layer=1,
        columns=v_column,
        where="habarea < %s" % (PixelArea),
    )

    smallareacsv = os.path.join(directory, f_habitat_small_areas)

    gs.run_command(
        "v.db.select",
        map=v_habitat,
        format="vertical",
        layer=1,
        columns=v_column,
        file=smallareacsv,
        where="habarea < %s" % (PixelArea),
    )

    gs.message("A list of habitat areas smaller than pixel area can be found in: ")
    gs.message(smallareacsv)
    gs.message("----")

    # Mark habitats smaller than pixel area in attribute table
    gs.message("Mark habitats smaller than pixel area in attribute table ...")
    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_smallarea varchar(1)" % prefix,
    )
    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_smallarea" % (prefix),
        value="*",
        where="habarea < %s" % (PixelArea),
    )
    gs.message("See column")
    gs.message("%s_smallarea" % prefix)
    gs.message("marked by *.")
    gs.message("----")

    # Upload DEM zonal statistics to the attribute table
    gs.message("Upload DEM zonal statistics to the attribute table ...")
    gs.run_command(
        "v.rast.stats",
        map=v_habitat,
        flags="c",
        layer=1,
        raster=r_elevation,
        column_prefix=prefix + "_dem",
        method="minimum,maximum,range,average,median",
    )
    gs.message("Upload DEM zonal statistics done.")
    gs.message("----")

    # Upload slope zonal statistics to the attribute table
    gs.message("Upload slope zonal statistics to the attribute table ...")
    gs.run_command(
        "v.rast.stats",
        map=v_habitat,
        flags="c",
        layer=1,
        raster=r_slope,
        column_prefix=prefix + "_slope",
        method="minimum,maximum,range,average,median",
    )
    gs.message("Upload slope zonal statistics done.")
    gs.message("----")

    # Upload slope zonal statistics to the attribute table
    gs.message("Upload aspect zonal statistics to the attribute table ...")
    gs.run_command(
        "v.rast.stats",
        map=v_habitat,
        flags="c",
        layer=1,
        raster=r_aspect,
        column_prefix=prefix + "_aspect",
        method="minimum,maximum,range,average,median",
    )
    gs.message("Upload aspect zonal statistics done.")
    gs.message("----")

    # Do some simple checks	regarding aspect range
    gs.message(
        "Do some simple checks regarding aspect range and populate it to the attribute table..."
    )
    gs.message("aspect range 100-200 *")
    gs.message("aspect range 201-300 **")
    gs.message("aspect range >= 300 ***")
    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s varchar(3)" % (prefix + "_check_aspect_range"),
    )

    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET %s ='*' WHERE %s < 200 AND %s >= 100"
        % (
            v_habitat,
            prefix + "_check_aspect_range",
            prefix + "_aspect_range",
            prefix + "_aspect_range",
        ),
    )
    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET %s ='**' WHERE %s < 300 AND %s >= 200"
        % (
            v_habitat,
            prefix + "_check_aspect_range",
            prefix + "_aspect_range",
            prefix + "_aspect_range",
        ),
    )
    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET %s ='***' WHERE %s >= 300"
        % (v_habitat, prefix + "_check_aspect_range", prefix + "_aspect_range"),
    )

    gs.message("Simple checks regarding aspect range done.")
    gs.message("----")

    # Do some simple checks	regarding aspect and and slope
    gs.message(
        "Do some simple checks regarding aspect range and slope median and populate it to the attribute table..."
    )
    gs.message("aspect range 100-200 and median slope < 5 *")
    gs.message("aspect range 201-300 and median slope < 5 **")
    gs.message("aspect range >= 300 and median slope < 5 ***")
    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s varchar(3)" % (prefix + "_check_aspect_slope"),
    )

    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET %s ='*' WHERE (%s < 200 AND %s >= 100) AND %s < 5"
        % (
            v_habitat,
            prefix + "_check_aspect_slope",
            prefix + "_aspect_range",
            prefix + "_aspect_range",
            prefix + "_slope_median",
        ),
    )
    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET %s ='**' WHERE (%s < 300 AND %s >= 200) AND %s < 5"
        % (
            v_habitat,
            prefix + "_check_aspect_slope",
            prefix + "_aspect_range",
            prefix + "_aspect_range",
            prefix + "_slope_median",
        ),
    )
    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET %s ='***' WHERE %s >= 300 AND %s < 5"
        % (
            v_habitat,
            prefix + "_check_aspect_slope",
            prefix + "_aspect_range",
            prefix + "_slope_median",
        ),
    )

    gs.message("Simple checks regarding aspect range and median slope done.")
    gs.message("----")

    # Do some simple checks	regarding aspect and and slope
    gs.message("Convert habitat vector to raster ...")
    gs.run_command(
        "v.to.rast",
        input=v_habitat,
        layer=1,
        type="area",
        use="attr",
        attrcolumn=v_column,
        output=r_habitat,
    )
    gs.message("Conversion done.")
    gs.message("----")

    # Calculate the most common geomorphons
    gs.message("Calculate the most common geomorphons ...")
    gs.run_command(
        "r.geomorphon",
        elevation=r_elevation,
        skip=0,
        search=3,
        flat=1,
        dist=0,
        forms=r_geomorphon,
    )
    gs.message("Geomorphon calculations done.")
    gs.message("----")

    # Mutual occurrence (coincidence) of categories of habitats and geomorphons
    gs.message("Calculate mutual occurrences of habitats and geomorphons ...")
    gs.message("1 - flat")
    gs.message("2 - summit")
    gs.message("3 - ridge")
    gs.message("4 - shoulder")
    gs.message("5 - spur")
    gs.message("6 - slope")
    gs.message("7 - hollow")
    gs.message("8 - footslope")
    gs.message("9 - valley")
    gs.message("10 - depression")
    gs.message(" ")
    gs.message("Mutual occurrence in percent of the row")
    gs.run_command("r.coin", first=r_habitat, second=r_geomorphon, flags="w", units="y")
    gs.message("Calculations of mutual occurrences done.")
    gs.message("----")

    # Join geomorphons to habitat attribute table
    gs.message("Join geomorphon information to habitat attribute table ....")

    habgeocsv = os.path.join(directory, f_habitat_geomorphons)

    gs.run_command(
        "r.stats",
        input=[r_habitat, r_geomorphon],
        flags="aln",
        separator=";",
        output=habgeocsv,
    )

    gs.run_command("db.in.ogr", input=habgeocsv, output=t_habitat_geomorphons)

    gs.run_command(
        "db.dropcolumn", table=t_habitat_geomorphons, column="field_2", flags="f"
    )

    gs.run_command(
        "db.dropcolumn", table=t_habitat_geomorphons, column="field_3", flags="f"
    )

    habgeocsv_pivot = os.path.join(directory, f_habitat_geomorphons_pivot)

    gs.run_command(
        "db.select",
        separator=";",
        output=habgeocsv_pivot,
        sql="SELECT field_1, sum(case when field_4 = 'flat' then field_5 end) as flat, sum(case when field_4 = 'summit' then field_5 end) as summit, sum(case when field_4 = 'ridge' then field_5 end) as ridge, sum(case when field_4 = 'shoulder' then field_5 end) as shoulder, sum(case when field_4 = 'spur' then field_5 end) as spur, sum(case when field_4 = 'slope' then field_5 end) as slope, sum(case when field_4 = 'hollow' then field_5 end) as hollow, sum(case when field_4 = 'footslope' then field_5 end) as footslope, sum(case when field_4 = 'valley' then field_5 end) as valley, sum(case when field_4 = 'depression' then field_5 end) as depression , sum(field_5) as SubTotal FROM %s GROUP BY field_1"
        % t_habitat_geomorphons,
    )

    gs.run_command(
        "db.in.ogr", input=habgeocsv_pivot, output=t_habitat_geomorphons_pivot
    )

    gs.run_command(
        "v.db.join",
        map=v_habitat,
        column=v_column,
        other_table=t_habitat_geomorphons_pivot,
        other_column="field_1",
    )
    gs.message("Geomorphon information joint to habitat attribute table.")
    gs.message("...")
    gs.message("Calculating percent geomorphon of habitat area ...")
    # add column for percent geomorphon

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_flat double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_summit double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_ridge double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_shoulder double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_spur double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_slope double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_hollow double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_footslope double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_valley double precision" % prefix,
    )

    gs.run_command(
        "v.db.addcolumn",
        map=v_habitat,
        layer=1,
        columns="%s_perc_depression double precision" % prefix,
    )

    # calculate percent geomorphon

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_flat" % prefix,
        query_column="cast(flat AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_summit" % prefix,
        query_column="cast(summit AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_ridge" % prefix,
        query_column="cast(ridge AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_shoulder" % prefix,
        query_column="cast(shoulder AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_spur" % prefix,
        query_column="cast(spur AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_slope" % prefix,
        query_column="cast(slope AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_hollow" % prefix,
        query_column="cast(hollow AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_footslope" % prefix,
        query_column="cast(footslope AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_valley" % prefix,
        query_column="cast(valley AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.run_command(
        "v.db.update",
        map=v_habitat,
        layer=1,
        column="%s_perc_depression" % prefix,
        query_column="cast(depression AS real) / cast( SubTotal AS real) * 100.0",
    )

    gs.message(" ")
    gs.message("Calculating of percent geomorphon of habitat area done.")
    gs.message("----")

    # Give information where output files are
    gs.message("Geomorphon information:")
    gs.message(habgeocsv)
    gs.message("Geomorphon information in pivot format:")
    gs.message(habgeocsv_pivot)
    gs.message("----")

    # Calculate LS factor see Neteler & Mitasova 2008. Open Source GIS - A GRASS GIS Approach
    gs.message("Calculate LS factor ...")
    gs.run_command(
        "r.flow", elevation=r_elevation, aspect=r_aspect, flowaccumulation=r_flow_accum
    )

    gs.message("...")
    gs.mapcalc(
        "$outmap = 1.4 * exp($flowacc * $resolution / 22.1, 0.4) * exp(sin($slope) / 0.09, 1.2)",
        outmap=r_LS,
        flowacc=r_flow_accum,
        resolution=Xres,
        slope=r_slope,
    )

    # create and define color rules file for LS factor map
    ls_color_rules_out = os.path.join(directory, f_LS_colorrules)
    with open(ls_color_rules_out, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["0 white"])
        writer.writerow(["3 yellow"])
        writer.writerow(["6 orange"])
        writer.writerow(["10 red"])
        writer.writerow(["50 magenta"])
        writer.writerow(["100 violet"])

    gs.run_command("r.colors", map=r_LS, rules=ls_color_rules_out)

    gs.message("Calculation LS factor done.")
    gs.message("----")

    # Run r.sun.hourly in binary mode for light/shadow
    gs.message(
        "Run r.sun.hourly in binary mode for light/shadow for a certain day in the year ..."
    )
    gs.run_command(
        "r.sun.hourly",
        elevation=r_elevation,
        flags="tb",
        aspect=r_aspect,
        slope=r_slope,
        start_time=d_start_time,
        end_time=d_end_time,
        day=d_day,
        year=d_year,
        beam_rad_basename=r_beam_rad,
    )

    gs.message("----")
    gs.message("Light/shadow conditions calculated for year")
    gs.message(d_year)
    gs.message("and day")
    gs.message(d_day)
    gs.message("from")
    gs.message(d_start_time)
    gs.message("to")
    gs.message(d_end_time)
    gs.message("done.")
    gs.message("----")
    gs.run_command("t.info", flags="h", input=r_beam_rad)
    gs.message("----")

    # Set region to original
    gs.message("Restore original region settings:")
    gs.run_command("g.region", flags="p", region=saved_region)
    gs.message("----")

    # clean up some temporay files and maps
    gs.message("Some clean up ...")
    gs.run_command("g.remove", flags="f", type="region", name=saved_region)
    gs.run_command("g.remove", flags="f", type="raster", name=r_flow_accum)
    gs.run_command("g.remove", flags="f", type="raster", name=r_habitat)
    gs.run_command("db.droptable", flags="f", table=t_habitat_geomorphons)
    gs.run_command("db.droptable", flags="f", table=t_habitat_geomorphons_pivot)
    gs.run_command("db.dropcolumn", flags="f", table=v_habitat, column="field_1")
    gs.message("Clean up done.")
    gs.message("----")

    # v.habitat.dem done!
    gs.message("v.habitat.dem done!")


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
