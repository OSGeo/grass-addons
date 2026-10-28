#!/usr/bin/env python3
#
##############################################################################
#
# MODULE:       r.futures.gridvalidation
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      Validation metrics computed on a grid
#               (Quantity/Allocation Disagreement, Kappa Simulation)
#
# COPYRIGHT:    (C) 2016-2021 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

# %module
# % description: Module for validating land change simulation on a grid
# % keyword: raster
# % keyword: statistics
# % keyword: accuracy
# % keyword: validation
# %end
# %option G_OPT_R_INPUT
# % key: simulated
# % description: Simulated land use raster
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: reference
# % description: Reference land use raster
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: original
# % label: Original land use raster
# % description: Required for kappa simulation
# % required: no
# %end
# %option G_OPT_V_OUTPUT
# % description: Vector output with values as attributes
# %end
# %option G_OPT_M_REGION
# % required: no
# %end
# %option G_OPT_V_INPUT
# % key: subregions
# % description: Vector areas for validation
# % required: no
# %end
# %option
# % key: nprocs
# % type: integer
# % description: Number of parallel processes
# % required: yes
# % answer: 1
# %end
# %rules
# % required: subregions,region
# %end
# %rules
# % exclusive: subregions,region
# %end


import os
import sys
import json
from multiprocessing import Pool
import grass.script as gs


def compute(params):
    env = os.environ.copy()
    use_region = False
    if "region" in params:
        use_region = True
        region = params.pop("region")
        env["GRASS_REGION"] = gs.region_env(**region)
        reg = gs.region(env=env)
    if "cat" in params:
        cat = params.pop("cat")
        subregions = params.pop("subregions")
        temp_map = f"rfuturesvalidation_{cat}"
        temp_map2 = f"rfuturesvalidation_{cat}_2"
        gs.run_command(
            "v.extract", input=subregions, cats=cat, type="area", output=temp_map
        )
        env["GRASS_REGION"] = gs.region_env(vector=temp_map, align=params["simulated"])
        gs.run_command(
            "v.to.rast",
            input=temp_map,
            output=temp_map,
            type="area",
            use="val",
            env=env,
        )
        gs.mapcalc(
            f"{temp_map2} = if({temp_map}, {params['simulated']}, null())", env=env
        )
        params["simulated"] = temp_map2

    results = gs.read_command(
        "r.futures.validation", format="json", env=env, quiet=True, **params
    )

    results = json.loads(results)
    if use_region:
        results["n"] = (reg["n"] + reg["s"]) / 2
        results["e"] = (reg["e"] + reg["w"]) / 2
    else:
        results["cat"] = cat
        gs.run_command(
            "g.remove",
            type=["raster", "vector"],
            name=[temp_map, temp_map2],
            flags="f",
            quiet=True,
        )
    return results


def main():
    options, flags = gs.parser()
    simulated = options["simulated"]
    original = options["original"]
    reference = options["reference"]
    input_region = options["region"]
    subregions = options["subregions"]
    nprocs = int(options["nprocs"])
    vector_output = options["output"]

    params = []
    if input_region:
        current = gs.region()
        region = gs.parse_command("g.region", flags="pug", region=input_region)
        regions = []
        for row in range(int(region["rows"])):
            for col in range(int(region["cols"])):
                s = float(region["s"]) + row * float(region["nsres"])
                n = float(region["s"]) + (row + 1) * float(region["nsres"])
                w = float(region["w"]) + col * float(region["ewres"])
                e = float(region["w"]) + (col + 1) * float(region["ewres"])
                regions.append(
                    {
                        "n": n,
                        "s": s,
                        "w": w,
                        "e": e,
                        "nsres": float(current["nsres"]),
                        "ewres": float(current["ewres"]),
                    }
                )

        for each in regions:
            if original:
                params.append(
                    {
                        "region": each,
                        "simulated": simulated,
                        "reference": reference,
                        "original": original,
                    }
                )
            else:
                params.append(
                    {"region": each, "simulated": simulated, "reference": reference}
                )
    if subregions:
        cats = (
            gs.read_command("v.category", input=subregions, option="print")
            .strip()
            .splitlines()
        )
        for cat in cats:
            if original:
                params.append(
                    {
                        "cat": cat,
                        "subregions": subregions,
                        "simulated": simulated,
                        "reference": reference,
                        "original": original,
                    }
                )
            else:
                params.append(
                    {
                        "cat": cat,
                        "subregions": subregions,
                        "simulated": simulated,
                        "reference": reference,
                    }
                )

    results = []
    with Pool(processes=nprocs) as pool:
        results = pool.map_async(compute, params).get()

    keys = max([r.keys() for r in results], key=len)
    if input_region:
        csv = ""
        table_header = "x double precision, y double precision"
        for k in keys:
            if k not in ("n", "e"):
                table_header += f", {k} double precision"
        for r in results:
            csv += f"{r['e']},{r['n']}"
            for k in keys:
                if k not in ("n", "e"):
                    try:
                        if r[k] is None:
                            csv += ","
                        else:
                            csv += f",{r[k]}"
                    except KeyError:
                        csv += ","
            csv += "\n"
        gs.write_command(
            "v.in.ascii",
            input="-",
            stdin=csv,
            output=vector_output,
            separator="comma",
            columns=table_header,
            x=1,
            y=2,
            format="point",
        )
    else:
        sql = ""
        table_header = "cat integer"
        for k in keys:
            if k != "cat":
                table_header += f", {k} double precision"
        gs.run_command("g.copy", vector=[subregions, vector_output])
        if gs.read_command("v.db.connect", map=vector_output, flags="g").strip():
            gs.run_command(
                "v.db.droptable", map=vector_output, flags="f", errors="ignore"
            )
        gs.run_command("v.db.addtable", map=vector_output, columns=table_header)
        for r in results:
            # UPDATE table SET attrib=5 WHERE cat=1"
            tmpsql = f"UPDATE {vector_output} SET "
            subsql = []
            for k in keys:
                if k not in ("cat"):
                    try:
                        if r[k] is None:
                            pass
                        else:
                            subsql.append(f"{k}={r[k]}")
                    except KeyError:
                        pass
            tmpsql += ",".join(subsql)
            tmpsql += f" WHERE cat={r['cat']};\n"
            if subsql:
                sql += tmpsql
        gs.write_command("db.execute", input="-", stdin=sql)


if __name__ == "__main__":
    sys.exit(main())
