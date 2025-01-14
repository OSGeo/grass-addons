#!/usr/bin/env python3
#
############################################################################
#
# MODULE:       r.slopeunits.metrics for GRASS 8
# AUTHOR(S):    Ivan Marchesini, Massimiliano Alvioli, Carmen Tawalika
#               (Translation to python)
# PURPOSE:      Create metrics for slope units
# COPYRIGHT:    (C) 2004-2024 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# %module
# % description: Create metrics for slope units
# % keywords: raster
# % keywords: elevation
# % keywords: slopeunits
# %end

# %option G_OPT_V_INPUT
# % key: basin
# % description: Input basin
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: demmap
# % description: Input digital elevation model
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: slumapclean
# % description: Output Slope Units layer, cleaned (the main output)
# % required: yes
# %end

# %option
# % key: cleansize
# % type: double
# % answer: 25000
# % description: Slope Units size to be removed
# % required: yes
# %end

# %option
# % key: areamin
# % type: double
# % description: Minimum area (m^2) below which the slope unit is not further segmented
# % required: yes
# %end

# %option
# % key: cvmin
# % type: double
# % description: Minimum value of the circular variance (0.0-1.0) below which the slope unit is not further segmented
# % required: yes
# %end

# %option
# % key: resolution
# % type: double
# % description: Resolution
# % required: yes
# %end

# %option G_OPT_F_OUTPUT
# % key: outfile
# % description: Output file with metrics
# % required: no
# %end

import atexit
import os
import sys

import grass.script as grass

# initialize global vars
rm_rasters = []
rm_vectors = []


def cleanup():
    """Cleanup function"""
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="cell")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)
    for rmvect in rm_vectors:
        if grass.find_file(name=rmvect, element="vector")["file"]:
            grass.run_command("g.remove", type="vector", name=rmvect, **kwargs)

    if grass.find_file("MASK")["file"]:
        # grass.run_command('r.mask', flags='r')
        grass.run_command(
            "g.remove", type="raster", name="MASK", flags="f", quiet=True
        )


def calculate_metrics(basin, dem, slumapclean, cleansize, resolution):
    """Calculate metric"""

    global rm_rasters, rm_vectors
    sucl = slumapclean
    thr_clean = cleansize
    res = resolution

    grass.run_command("g.region", vect=basin, align=dem)
    if grass.find_file("MASK")["file"]:
        grass.run_command(
            "g.remove", type="raster", name="MASK", flags="f", quiet=True
        )
    grass.run_command("r.mask", vect=basin, overwrite=True)
    grass.run_command("g.remove", type="vector", name="su_segm", flags="f")
    grass.run_command("g.copy", vect=f"{sucl},su_segm", overwrite=True)
    grass.run_command(
        "v.db.dropcolumn", map="su_segm", columns="value,label,area"
    )
    grass.run_command("v.db.addcolumn", map="su_segm", columns="area real")
    grass.run_command(
        "v.to.db", map="su_segm", option="area", columns="area", overwrite=True
    )
    grass.run_command(
        "db.execute", sql=f"delete from su_segm where area<{thr_clean}"
    )
    grass.run_command(
        "v.clean",
        input="su_segm",
        type="area",
        output="su_ok",
        tool="rmarea",
        threshold=thr_clean,
        overwrite=True,
    )
    grass.run_command("g.rename", vect="su_ok,su_segm", overwrite=True)

    ##############################################################
    #
    # Calculation of the procedure proposed in
    # [1] Espindola et al., Int. J. Remote Sens. 27, 3035-3040 (2006)
    # and adapted for our case in
    # [2] Alvioli, Marchesini et al., Geosci. Mod. Dev. 9, 3975-3991 (2016)
    # and
    # [3] Alvioli, Guzzetti, Marchesini, Geomorphology 358, 107124 (2020)
    # [4] Alvioli, Marchesini et al., Journal of Maps, 18, 300-313 (2021)
    #

    if grass.find_file("MASK")["file"]:
        grass.run_command(
            "g.remove", type="raster", name="MASK", flags="f", quiet=True
        )
    grass.run_command("r.mask", vect="su_segm", overwrite=True)
    grass.run_command(
        "v.to.rast",
        input="su_segm",
        output="su_segm",
        use="cat",
        overwrite=True,
    )

    onecell = res * res

    grass.message(_("r.slope.aspect ..."))
    grass.run_command(
        "r.slope.aspect", elevation=dem, aspect="aspect", overwrite=True
    )
    grass.run_command("r.colors", map="aspect", color="aspectcolr")
    grass.message(_("circular variance ..."))
    # aspect in degrees - mapcalc's cos(x) wants x in degrees -- OK
    grass.run_command(
        "r.mapcalc", expression="cos=cos(aspect)", overwrite=True
    )
    # aspect in degrees - mapcalc's sin(x) wants x in degrees -- OK
    grass.run_command(
        "r.mapcalc", expression="sin=sin(aspect)", overwrite=True
    )

    grass.message(_("r.statistics 1 ..."))
    grass.run_command(
        "r.stats.zonal",
        base="su_segm",
        cover="su_segm",
        method="count",
        output="numero",
        overwrite=True,
    )
    grass.message(_("r.statistics 2 ..."))
    grass.run_command(
        "r.stats.zonal",
        base="su_segm",
        cover="cos",
        method="sum",
        output="sumcos",
        overwrite=True,
    )
    grass.message(_("r.statistics 3 ..."))
    grass.run_command(
        "r.stats.zonal",
        base="su_segm",
        cover="sin",
        method="sum",
        output="sumsin",
        overwrite=True,
    )
    grass.run_command(
        "r.mapcalc",
        expression="v_i = 1-((sqrt((sumsin)^2 + (sumcos)^2))/numero)",
        overwrite=True,
    )

    grass.message(_("r.statistics 4 ..."))
    grass.run_command(
        "r.mapcalc", expression=f"base = int({dem}/{dem})", overwrite=True
    )
    grass.run_command(
        "r.stats.zonal",
        base="base",
        cover="cos",
        method="sum",
        output="sumcos_all",
        overwrite=True,
    )
    grass.run_command(
        "r.stats.zonal",
        base="base",
        cover="sin",
        method="sum",
        output="sumsin_all",
        overwrite=True,
    )

    grass.message(_("v.category edges ..."))
    grass.run_command(
        "g.remove", type="vector", name="su_segm_edges", flags="f"
    )
    grass.run_command(
        "v.category",
        input="su_segm",
        output="su_segm_edges",
        layer=2,
        type="boundary",
        option="add",
        overwrite=True,
    )
    grass.run_command(
        "v.db.addtable",
        map="su_segm_edges",
        layer=2,
        col="left integer,right integer,lunghezza real",
    )
    grass.run_command(
        "v.to.db",
        map="su_segm_edges",
        option="sides",
        columns="left,right",
        layer=2,
        type="boundary",
        overwrite=True,
    )
    grass.run_command(
        "v.to.db",
        map="su_segm_edges",
        option="length",
        columns="lunghezza",
        layer=2,
        type="boundary",
        overwrite=True,
    )

    # mapcalc's atan(x,y) returns result in degrees ..
    grass.run_command(
        "r.mapcalc", expression="a_i = atan(sumsin,sumcos)", overwrite=True
    )
    grass.run_command(
        "r.mapcalc",
        expression="a_all = atan(sumsin_all,sumcos_all)",
        overwrite=True,
    )
    # .. but we need maps in radians, as needed by bc in bash
    pii = 3.14159265359
    grass.run_command(
        "r.mapcalc", expression=f"a_irad = a_i*{pii}/180", overwrite=True
    )
    grass.run_command(
        "r.mapcalc", expression=f"a_allrad = a_all*{pii}/180", overwrite=True
    )

    grass.message(_("v.rast.stats 1 ..."))
    grass.run_command(
        "v.rast.stats",
        map="su_segm_edges",
        raster="a_irad",
        column_prefix="a_i",
        method="average",
    )
    grass.run_command(
        "v.db.renamecolumn", map="su_segm_edges", column="a_i_average,a_i"
    )

    grass.message(_("v.rast.stats 2 ..."))
    grass.run_command(
        "v.rast.stats",
        map="su_segm_edges",
        raster="a_allrad",
        column_prefix="a_all",
        method="average",
    )
    grass.run_command(
        "v.db.renamecolumn", map="su_segm_edges", column="a_all_average,a_all"
    )

    grass.message(_("v.rast.stats 3 ..."))
    grass.run_command(
        "v.rast.stats",
        map="su_segm_edges",
        raster="v_i",
        column_prefix="v_i",
        method="average",
    )
    grass.run_command(
        "v.db.renamecolumn", map="su_segm_edges", column="v_i_average,v_i"
    )

    # fix problems
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges set v_i = (select coalesce(0,v_i) "
            "as v_i from su_segm_edges) where v_i is null"
        ),
    )
    grass.run_command(
        "v.extract",
        input="su_segm_edges",
        where="v_i>=0",
        output="su_segm",
        overwrite=True,
    )
    grass.run_command(
        "v.db.addtable", map="su_segm", table="su_segm_edges_2", layer=2
    )

    # calcolo V - metodo RASTER
    grass.message(_("-- calcolo V --"))
    grass.run_command(
        "r.mapcalc", expression=f"num = {onecell}*v_i", overwrite=True
    )
    grass.run_command(
        "r.mapcalc", expression=f"den = {onecell}", overwrite=True
    )
    numvar = grass.parse_command(
        "r.univar",
        map="num",
        quiet=True,
        parse=(grass.core.parse_key_val, {"sep": ":"}),
    )
    denvar = grass.parse_command(
        "r.univar",
        map="den",
        quiet=True,
        parse=(grass.core.parse_key_val, {"sep": ":"}),
    )
    v_fin = float(numvar["sum"]) / float(denvar["sum"])
    grass.message(_(f"Vfin: {v_fin}"))

    #
    # calcolo I
    #
    grass.message(_("-- calcolo I -- ALT2 procedure"))

    grass.run_command(
        "v.db.addcolumn",
        map="su_segm",
        layer=2,
        columns=(
            "ai real, aj real, aall real, ci real, "
            "si real, cj real, sj real, num real"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set ai = "
            "(select a_i from su_segm where cat=su_segm_edges_2.left)"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set aj = "
            "(select a_i from su_segm where cat=su_segm_edges_2.right)"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set aall = "
            "(select a_all from su_segm where cat=su_segm_edges_2.right)"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set ci = "
            "cos(atan((sin(ai)+sin(aall))/(cos(ai)+cos(aall))))"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set si = "
            "sin(atan((sin(ai)+sin(aall))/(cos(ai)+cos(aall))))"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set cj = "
            "cos(atan((sin(aj)+sin(aall))/(cos(aj)+cos(aall))))"
        ),
    )
    grass.run_command(
        "db.execute",
        sql=(
            "update su_segm_edges_2 set sj = "
            "sin(atan((sin(aj)+sin(aall))/(cos(aj)+cos(aall))))"
        ),
    )
    grass.run_command(
        "db.execute",
        sql="update su_segm_edges_2 set num = ci*cj+si*sj",
    )

    num = grass.parse_command(
        "db.select",
        flags="c",
        sql="select sum(num) from su_segm_edges_2 where left<>-1 and right<>-1",
    )
    den = grass.parse_command(
        "db.select",
        flags="c",
        sql="select count(*) from su_segm_edges_2 where left<>-1 and right<>-1",
    )
    num_float = float(next(iter(num.keys())))
    den_float = float(next(iter(den.keys())))
    grass.message(_(num_float))
    grass.message(_(den_float))
    i_fin = float(num_float) / float(den_float)
    grass.message(_(f"Ifin: {i_fin}"))

    grass.run_command(
        "g.remove",
        type="raster",
        name=(
            "a_all,a_allrad,a_i,a_irad,areamap,aspect,base,basin_chk,cos,den,"
            "num,numero,sin,sumcos,sumcos_all,sumsin,sumsin_all,v_i,su_segm"
        ),
        flags="f",
    )
    grass.run_command(
        "g.remove", type="vector", name="su_segm,su_segm_edges", flags="f"
    )
    if grass.find_file("MASK")["file"]:
        grass.run_command(
            "g.remove", type="raster", name="MASK", flags="f", quiet=True
        )

    grass.message("Metrics calculated.")

    return v_fin, i_fin


def main():
    """Main function of r.slopeunits.metrics"""
    global rm_rasters, rm_vectors

    basin = options["basin"]
    dem = options["demmap"]
    slumapclean = options["slumapclean"]
    cleansize = float(options["cleansize"])
    resolution = float(options["resolution"])

    areamin = float(options["areamin"])
    cvmin = float(options["cvmin"])
    if options["outfile"]:
        outfile = options["outfile"]

    v_fin, i_fin = calculate_metrics(
        basin,
        dem,
        slumapclean,
        cleansize,
        resolution,
    )
    grass.message("Calculating metrics finished.")

    output = f"{areamin} {cvmin} {v_fin} {i_fin}"

    sys.stdout.write(f"areamin={areamin}\n")
    sys.stdout.write(f"cvmin={cvmin}\n")
    sys.stdout.write(f"v_fin={v_fin}\n")
    sys.stdout.write(f"i_fin={i_fin}\n")

    if options["outfile"]:
        grass.debug("Writing output to file")
        grass.debug(output)
        with open(outfile, "a") as file:
            file.write(output)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
