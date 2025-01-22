#!/usr/bin/env python3
#
############################################################################
#
# MODULE:       r.slopeunits.clean for GRASS 8
# AUTHOR(S):    Ivan Marchesini, Massimiliano Alvioli, Markus Metz
#               (Refactoring, partly translation to python), Carmen Tawalika
#               (creation of extra addon)
# PURPOSE:      Clean slope units layer
# COPYRIGHT:    (C) 2004-2024 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# %module
# % description: Clean results of r.slopeunits.create
# % keywords: raster
# % keywords: elevation
# % keywords: slopeunits
# %end

# %option G_OPT_R_INPUT
# % key: demmap
# % description: Input digital elevation model
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: plainsmap
# % description: Input raster map of alluvial plains
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: slumap
# % description: Output Slope Units layer (the main output)
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: slumapclean
# % description: Output Slope Units layer, cleaned (the main output)
# % required: no
# %end

# %option
# % key: cleansize
# % type: double
# % answer: 25000
# % description: Slope Units size to be removed
# % required: yes
# %end

# %flag
# % key: m
# % description: Perform quick cleaning of small-sized areas and stripes
# % guisection: flags
# %end

# %flag
# % key: n
# % description: Perform detailed cleaning of small-sized areas (slow)
# % guisection: flags
# %end

# %rules
# % required: cleansize,slumapclean
# %end

# %rules
# % exclusive: -m,-n
# %end

# pylint: disable=C0302 (too-many-lines)

import atexit
import os

import grass.script as gs

# initialize global vars
rm_rasters = []
rm_vectors = []


def cleanup():
    """Cleanup function"""
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmrast in rm_rasters:
        if gs.find_file(name=rmrast, element="cell")["file"]:
            gs.run_command("g.remove", type="raster", name=rmrast, **kwargs)
    for rmvect in rm_vectors:
        if gs.find_file(name=rmvect, element="vector")["file"]:
            gs.run_command("g.remove", type="vector", name=rmvect, **kwargs)

    if gs.find_file("MASK")["file"]:
        # gs.run_command('r.mask', flags='r')
        gs.run_command("g.remove", type="raster", name="MASK", flags="f", quiet=True)


def clean_method_3(input_vect, output_vect, minarea):
    """Clean up"""
    region = gs.region()
    nsres = region["nsres"]
    ewres = region["ewres"]
    smarea = 10 * nsres * ewres

    gs.run_command(
        "v.clean",
        input=input_vect,
        output="slu_clean",
        tool="rmarea",
        threshold=smarea,
        quiet=True,
    )
    gs.run_command(
        "v.db.addcolumn",
        map="slu_clean",
        columns="area integer, perimetro integer",
        quiet=True,
    )
    gs.run_command(
        "v.to.db", map="slu_clean", option="area", columns="area", quiet=True
    )
    gs.run_command(
        "v.to.db",
        map="slu_clean",
        option="perimeter",
        columns="perimetro",
        quiet=True,
    )
    gs.run_command(
        "v.db.droprow",
        input="slu_clean",
        where="area is null",
        output="slu_area",
        quiet=True,
    )
    rm_vectors.append("slu_clean")

    key = gs.vector_db(map="slu_area")[1]["key"]
    lista = gs.read_command(
        "v.db.select",
        map="slu_area",
        columns=key,
        where=f"area <= {minarea}",
        flags="c",
    )
    lista = lista.splitlines()
    buchi = ",".join(lista)
    totalebuchi = len(lista)
    gs.run_command(
        "v.extract",
        input="slu_area",
        cats=buchi,
        output="slu_buchi",
        type="area",
        quiet=True,
    )
    gs.run_command(
        "v.to.rast",
        input="slu_buchi",
        output="slu_buchi",
        use="cat",
        overwrite=True,
    )

    key = gs.vector_db(map="slu_area")[1]["key"]
    lista = gs.read_command(
        "v.db.select",
        map="slu_area",
        columns=key,
        where=f"area > {minarea}",
        flags="c",
    )
    lista = lista.splitlines()
    nobuchi = ",".join(lista)
    gs.run_command(
        "v.extract",
        input="slu_area",
        cats=nobuchi,
        output="slu_nobuchi",
        type="area",
        quiet=True,
    )
    gs.run_command(
        "v.to.rast",
        input="slu_nobuchi",
        output="slu_nobuchi",
        use="cat",
        overwrite=True,
    )
    gs.run_command(
        "v.category",
        input="slu_area",
        output="slu_bordi",
        layer=2,
        type="boundary",
        option="add",
        quiet=True,
    )
    gs.run_command(
        "v.db.addtable",
        map="slu_bordi",
        layer=2,
        columns="left integer,right integer,lunghezza integer",
        quiet=True,
    )
    gs.run_command(
        "v.to.db",
        map="slu_bordi",
        option="sides",
        columns="left,right",
        layer=2,
        type="boundary",
        quiet=True,
    )
    gs.run_command(
        "v.to.db",
        map="slu_bordi",
        option="length",
        columns="lunghezza",
        layer=2,
        type="boundary",
        quiet=True,
    )
    gs.run_command(
        "v.to.rast", input="slu_area", output="slu_area", use="cat", quiet=True
    )
    # TODO: different names than coseno and seno, these rasters are already
    # created
    gs.mapcalc("coseno = cos(aspect_slu)", quiet=True)
    gs.mapcalc("seno = sin(aspect_slu)", quiet=True)

    gs.run_command(
        "r.stats.zonal",
        base="slu_area",
        cover="coseno",
        method="count",
        output="count",
        quiet=True,
    )
    gs.run_command(
        "r.stats.zonal",
        base="slu_area",
        cover="coseno",
        method="sum",
        output="cumcos",
        quiet=True,
    )
    gs.run_command(
        "r.stats.zonal",
        base="slu_area",
        cover="seno",
        method="sum",
        output="sumsin",
        quiet=True,
    )

    gs.mapcalc("cos_medio = sumcos / count", quiet=True)
    gs.mapcalc("sin_medio = sumsin / count", quiet=True)
    gs.run_command(
        "r.to.vect",
        input="cos_medio",
        output="cos_medio",
        type="area",
        quiet=True,
    )
    gs.run_command(
        "r.to.vect",
        input="sin_medio",
        output="sin_medio",
        type="area",
        quiet=True,
    )
    gs.run_command(
        "v.overlay",
        ainput="slu_area",
        binput="cos_medio",
        operator="and",
        atype="area",
        btype="area",
        output="cos_medio_over",
        quiet=True,
    )
    gs.run_command(
        "v.overlay",
        ainput="slu_area",
        binput="sin_medio",
        operator="and",
        atype="area",
        btype="area",
        output="sin_medio_over",
        quiet=True,
    )

    pulire = gs.read_command(
        "v.category", input="slu_buchi", option="print", quiet=True
    )
    pulire = pulire.splitlines()

    gs.run_command("g.copy", vector=f"slu_area,{output_vect}", quiet=True)

    ico = 1
    for i in pulire:
        inti = int(i)
        lista1 = gs.read_command(
            "db.select",
            sql=(
                "select b2.right from slu_bordi_2 b2 "
                f"where b2.left = {i} and b2.right <> -1"
            ),
            flags="c",
        )
        lista2 = gs.read_command(
            "db.select",
            sql=(
                "select b2.left from slu_bordi_2 b2 "
                f"where b2.left <> -1 and b2.right = {inti}"
            ),
            flags="c",
        )
        vicini = lista1.splitlines()
        vicini.extend(lista2.splitlines)
        vicini = sorted(set(vicini))
        if len(vicini) > 0:
            gs.message(
                f" --- --- -- buco numero {ico} di {totalebuchi}, "
                "cat: {i}, vicini: {vicini}"
            )
            ico = ico + 1
            gs.message(f"vicini: {vicini}")
            gs.run_command(
                "v.extract",
                input=output_vect,
                cats=",".join(vicini),
                output="intorno",
                type="area",
                quiet=True,
            )
            chk_intorno = gs.read_command(
                "v.category",
                input="intorno",
                type="centroid",
                option="print",
                quiet=True,
            )
            chk_intorno = chk_intorno.splitlines()
            if len(chk_intorno) > 0:
                # potrei voler cambiare questo perche' quando ci sono buchi
                # contigui fa un po' di casino
                gs.run_command(
                    "v.overlay",
                    ainput="intorno",
                    binput="slu_nobuchi",
                    output="intorno_OK",
                    atype="area",
                    btype="area",
                    olayer="0,1,0",
                    operator="and",
                    quiet=True,
                )

                cos_buco = gs.read_command(
                    "v.db.select",
                    map="cos_medio_over",
                    where=f"a_cat={i}",
                    columns="b_value",
                    flags="c",
                    quiet=True,
                )
                sin_buco = gs.read_command(
                    "v.db.select",
                    map="sin_medio_over",
                    where=f"a_cat={i}",
                    columns="b_value",
                    flags="c",
                    quiet=True,
                )
                gs.message(f"buco cat {i}: cos={cos_buco} sin={sin_buco}")
                massimo = -10000
                jmax = 0
                loop = gs.read_command(
                    "v.category",
                    input="intorno_OK",
                    option="print",
                    quiet=True,
                )
                loop = loop.splitlines()
                for j in loop:
                    j = int(j)
                    cos_j = gs.read_command(
                        "v.db.select",
                        map="cos_medio_over",
                        where=f"a_cat={j}",
                        columns="b_value",
                        flags="c",
                        quiet=True,
                    )
                    sin_j = gs.read_command(
                        "v.db.select",
                        map="sin_medio_over",
                        where=f"a_cat={j}",
                        columns="b_value",
                        flags="c",
                        quiet=True,
                    )
                    dotpr = (
                        float(cos_buco) * float(cos_j) + float(sin_buco) * float(sin_j)
                    ) * 10000
                    if dotpr >= massimo and dotpr > 0:
                        massimo = dotpr
                        jmax = j

                    gs.message(
                        f"i: {i} j: {j} cos_j: {cos_j} sin_j: {sin_j} "
                        "dotpr: {dotpr} jmax: {jmax}"
                    )

                gs.message(f"massimo: {massimo} per j={jmax}")
                if jmax > 0:
                    lunghezza = gs.read_command(
                        "db.select",
                        sql=(
                            "select b2.lunghezza from slu_bordi_2 b2 where "
                            f"(b2.left={i} and b2.right={jmax}) "
                            f"or (b2.left={jmax} and b2.right={i})"
                        ),
                        flags="c",
                        quiet=True,
                    )
                    perimetro = gs.read_command(
                        "v.db.select",
                        map="slu_clean",
                        columns="perimetro",
                        where=f"cat={i}",
                        flags="c",
                        quiet=True,
                    )
                    lunghezza = float(lunghezza)
                    perimetro = float(perimetro)
                    if lunghezza > 0 and perimetro > 0:
                        frazione = lunghezza / perimetro * 10000
                        if frazione > 500:
                            gs.message(
                                f"lungh: {lunghezza}; perim: {perimetro}; "
                                f"fract: {frazione}"
                            )
                            gs.run_command(
                                "v.extract",
                                input=output_vect,
                                output="slu_i",
                                cats=f"{i},{jmax}",
                                new={jmax},
                                flags="d",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.overlay",
                                ainput=output_vect,
                                binput="slu_i",
                                atype="area",
                                btype="area",
                                operator="not",
                                olayer="0,1,0",
                                output="slu_j",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.overlay",
                                ainput="slu_i",
                                binput="slu_j",
                                atype="area",
                                btype="area",
                                operator="or",
                                output="slu_k",
                                olayer="1,0,0",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.db.addcolumn",
                                map="slu_k",
                                column="newcat integer",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.db.update",
                                map="slu_k",
                                layer=1,
                                column="newcat",
                                qcolumn="a_cat",
                                where="a_cat is not null",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.db.update",
                                map="slu_k",
                                layer=1,
                                column="newcat",
                                qcolumn="b_cat",
                                where="b_cat is not null",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.reclass",
                                input="slu_k",
                                output=output_vect,
                                column="newcat",
                                quiet=True,
                            )
                            gs.run_command("v.db.addtable", map=output_vect, quiet=True)
                            gs.run_command(
                                "v.db.addcolumn",
                                map=output_vect,
                                columns="area integer",
                                quiet=True,
                            )
                            gs.run_command(
                                "v.to.db",
                                map=output_vect,
                                option="area",
                                columns="area",
                                quiet=True,
                            )
                            gs.run_command(
                                "g.remove",
                                type="vector",
                                name="slu_i,slu_j,slu_k",
                                flags="f",
                                quiet=True,
                            )
                    # lunghezza and perimetro
                # jmax
                gs.run_command(
                    "g.remove",
                    type="vector",
                    name="intorno_OK",
                    flags="f",
                    quiet=True,
                )
            # chk_category
            gs.run_command(
                "g.remove",
                type="vector",
                name="intorno",
                flags="f",
                quiet=True,
            )
        # vicini
    # pulire


def clean_small_areas(dem, slumap, plains, cleansize, slumapclean):
    """Cleaning of small areas"""
    region = gs.region()
    nsres = region["nsres"]
    ewres = region["ewres"]

    if not flags["n"]:
        if not flags["m"]:
            gs.message(" -- we want QUICK cleaning of small-sized areas: METHOD 1 --")

        exp = "$out = if(isnull($mask), null(), 1)"
        gs.mapcalc(exp, out="MASK", mask=dem, quiet=True)
        areamap = "areamap"

        gs.run_command("r.clump", input=slumap, output="slu_clump", quiet=True)
        rm_rasters.append("slu_clump")

        gs.run_command(
            "r.stats.zonal",
            base="slu_clump",
            cover="slu_clump",
            method="count",
            output="slu_count",
            quiet=True,
        )
        rm_rasters.append("slu_count")

        exp = "$out = $a * $b * $c"
        gs.mapcalc(
            exp,
            out=areamap,
            a="slu_count",
            b=nsres,
            c=ewres,
            quiet=True,
        )
        rm_rasters.append(areamap)

        exp = "$out = if($a > $b, $c, null())"
        gs.mapcalc(
            exp,
            out="slu_r_clean",
            a=areamap,
            b=cleansize,
            c=slumap,
            quiet=True,
        )
        rm_rasters.append("slu_r_clean")

        cleansize = cleansize / (nsres * ewres)
        growdist = int((10 * cleansize / 3.14) ** 0.5)
        gs.run_command(
            "r.grow",
            input="slu_r_clean",
            output="slu_r_grow",
            radius=growdist,
            quiet=True,
        )
        rm_rasters.append("slu_r_grow")

    if flags["m"]:
        gs.message(" -- we want QUICK cleaning of small-sized areas: METHOD 2 --")
        clean_input = "slu_r_grow"
        clean_output = "slu_no_stripes"
        gs.run_command(
            "r.neighbors",
            input=clean_input,
            output="slu_diversity",
            method="diversity",
            size=5,
            quiet=True,
        )
        rm_rasters.append("slu_diversity")

        exp = "$out = if($a == 1, 1, null())"
        gs.mapcalc(
            exp,
            out="slu_diversity_nobordi",
            a="slu_diversity",
            quiet=True,
        )
        rm_rasters.append("slu_diversity_nobordi")

        gs.run_command(
            "r.grow",
            input="slu_diversity_nobordi",
            output="slu_diversity_nobordi_grow",
            radius=1.01,
            quiet=True,
        )
        rm_rasters.append("slu_diversity_nobordi_grow")

        exp = "$out = if(isnull($a), null(), $b)"
        gs.mapcalc(
            exp,
            out="slu_finale_nobordi",
            a="slu_diversity_nobordi_grow",
            b=clean_input,
            quiet=True,
        )
        rm_rasters.append("slu_finale_nobordi")

        # TODO: fixed radius ?
        gs.run_command(
            "r.grow",
            input="slu_finale_nobordi",
            output=clean_output,
            radius=1000,
            quiet=True,
        )
        rm_rasters.append(clean_output)

        exp = "$out = int($a)"
        # output="slu_r_grow" exists already
        gs.run_command(
            "g.remove", type="raster", name=clean_input, flags="f", quiet=True
        )
        gs.mapcalc(exp, out=clean_input, a=clean_output, quiet=True)
        gs.run_command(
            "g.remove",
            type="raster",
            name=(
                "slu_diversity,slu_diversity_nobordi,"
                "slu_diversity_nobordi_grow,slu_finale_nobordi,slu_no_stripes"
            ),
            flags="f",
            quiet=True,
        )

    if flags["n"]:
        gs.message(" -- we want DETAILED cleaning of small-sized areas: METHOD 3 --")
        gs.run_command(
            "r.to.vect",
            input=slumap,
            output="slu_v_grow",
            type="area",
            quiet=True,
        )
        rm_vectors.append("slu_v_grow")
        # TODO: include in new fn clean_method_3
        gs.run_command(
            "r.slope.aspect",
            elevation=dem,
            aspect="aspect_slu",
            quiet=True,
        )
        rm_rasters.append("aspect_slu")

        clean_method_3("slu_v_grow", "vect2", cleansize)

        # applying method 2 at the end
        gs.run_command(
            "v.to.rast",
            input="vect2",
            output="rast2",
            use="cat",
            quiet=True,
        )
        rm_rasters.append("rast2")

        clean_input = "rast2"
        clean_output = "slu_r_grow"
        gs.run_command(
            "r.neighbors",
            input=clean_input,
            output="slu_diversity",
            method="diversity",
            size=5,
            quiet=True,
        )
        rm_rasters.append("slu_diversity")

        exp = "$out = if($a == 1, 1, null())"
        gs.mapcalc(
            exp,
            out="slu_diversity_nobordi",
            a="slu_diversity",
            quiet=True,
        )
        rm_rasters.append("slu_diversity_nobordi")

        gs.run_command(
            "r.grow",
            input="slu_diversity_nobordi",
            output="slu_diversity_nobordi_grow",
            radius=1.01,
            quiet=True,
        )
        rm_rasters.append("slu_diversity_nobordi_grow")

        exp = "$out = if(isnull($a), null(), $b)"
        gs.mapcalc(
            exp,
            out="slu_finale_nobordi",
            a="slu_diversity_nobordi_grow",
            b=clean_input,
            quiet=True,
        )
        rm_rasters.append("slu_finale_nobordi")

        gs.run_command(
            "r.grow",
            input="slu_finale_nobordi",
            output=clean_output,
            radius=1000,
            quiet=True,
        )
        rm_rasters.append(clean_output)

        exp = "$out = int($a)"
        # output="slu_r_grow" exists already
        gs.run_command(
            "g.remove", type="raster", name=clean_input, flags="f", quiet=True
        )
        gs.mapcalc(exp, out=clean_input, a=clean_output, quiet=True)
        rm_rasters.append(clean_input)

        gs.run_command(
            "g.remove",
            type="raster",
            name=(
                "slu_diversity,slu_diversity_nobordi,"
                "slu_diversity_nobordi_grow,slu_finale_nobordi,rast2"
            ),
            flags="f",
            quiet=True,
        )

        gs.run_command(
            "g.remove",
            type="vector",
            name="slu_v_grow,vect2",
            flags="f",
            quiet=True,
        )

    if options["plainsmap"]:
        exp = "$out = if(isnull($b), if(isnull($c), null(), int($a)), null())"
        gs.mapcalc(
            exp,
            out=slumapclean,
            a="slu_r_grow",
            b=plains,
            c=dem,
            quiet=True,
        )
    else:
        exp = "$out = if(isnull($c), null(), int($a))"
        gs.mapcalc(exp, out=slumapclean, a="slu_r_grow", c=dem, quiet=True)

    gs.run_command("r.colors", map=slumapclean, color="random", quiet=True)

    gs.message("Cleaning of small areas finished.")


def main():
    """Main function of r.slopeunits"""
    global rm_rasters, rm_vectors

    dem = options["demmap"]
    slumap = options["slumap"]
    plains = None
    if options["plainsmap"]:
        plains = options["plainsmap"]
    cleansize = int(options["cleansize"])
    slumapclean = options["slumapclean"]

    if cleansize > 0:
        clean_small_areas(dem, slumap, plains, cleansize, slumapclean)
    else:
        gs.fatal("Cleansize cannot be a negative value.")

    gs.message("Slope units cleaned.")


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
