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

#%module
#% description: Module for validating land change simulation on a grid
#% keyword: raster
#% keyword: statistics
#% keyword: accuracy
#% keyword: validation
#%end
#%option G_OPT_R_INPUT
#% key: simulated
#% description: Simulated land use raster
#% required: yes
#%end
#%option G_OPT_R_INPUT
#% key: reference
#% description: Reference land use raster
#% required: yes
#%end
#%option G_OPT_R_INPUT
#% key: original
#% label: Original land use raster
#% description: Required for kappa simulation
#% required: no
#%end
#%option G_OPT_R_OUTPUT
#% key: allocation_disagreement
#% required: no
#% description: Output total allocation disagreement raster
#%end
#%option G_OPT_R_BASENAME_OUTPUT
#% key: allocation_disagreement_basename
#% description: Basename for per class allocation disagreement raster
#% required: no
#%end
#%option G_OPT_R_OUTPUT
#% key: quantity_disagreement
#% description: Output total quantity disagreement raster
#% required: no
#%end
#%option G_OPT_R_BASENAME_OUTPUT
#% key: quantity_disagreement_basename
#% description: Basename for per class quantity disagreement raster
#% required: no
#%end
#%option G_OPT_R_OUTPUT
#% key: kappa
#% description: Output Cohen's kappa raster
#% required: no
#%end
#%option G_OPT_R_OUTPUT
#% key: kappasimulation
#% description: Output kappa simulation raster
#% required: no
#%end
#%option G_OPT_M_REGION
#% required: yes
#%end
#%option
#% key: nprocs
#% type: integer
#% description: Number of parallel processes
#% required: yes
#% answer: 1
#%end
#%rules
#% required: allocation_disagreement, quantity_disagreement, kappasimulation
#%end
#%rules
#% requires: kappasimulation, original
#%end


import os
import sys
import json
from multiprocessing import Pool
import grass.script as gs


def compute(params):
    env = os.environ.copy()
    region = params.pop("region")
    env["GRASS_REGION"] = gs.region_env(**region)
    results = gs.read_command(
        "r.futures.validation", format="json", env=env, quiet=True, **params
    )
    results = json.loads(results)
    reg = gs.region(env=env)
    results["n"] = (reg["n"] + reg["s"]) / 2
    results["e"] = (reg["e"] + reg["w"]) / 2
    return results


def main():
    options, flags = gs.parser()
    simulated = options["simulated"]
    original = options["original"]
    reference = options["reference"]
    kappa = options["kappa"]
    kappasimulation = options["kappasimulation"]
    quantity_disagreement = options["quantity_disagreement"]
    allocation_disagreement = options["allocation_disagreement"]
    quantity_disagreement_basename = options["quantity_disagreement_basename"]
    allocation_disagreement_basename = options["allocation_disagreement_basename"]
    input_region = options["region"]
    nprocs = int(options["nprocs"])

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
    results = []
    params = []
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

    with Pool(processes=nprocs) as pool:
        results = pool.map_async(compute, params).get()
    outputs = {}
    if kappa:
        outputs["kappa"] = {"name": kappa, "param": "kappa", "inp": ""}
    if kappasimulation:
        outputs["kappasim"] = {
            "name": kappasimulation,
            "param": "kappasimulation",
            "inp": "",
        }
    if quantity_disagreement:
        outputs["quantity_disagreement"] = {
            "name": quantity_disagreement,
            "param": "total_quantity",
            "inp": "",
        }
    if allocation_disagreement:
        outputs["allocation_disagreement"] = {
            "name": allocation_disagreement,
            "param": "total_allocation",
            "inp": "",
        }
    env = os.environ.copy()
    env["GRASS_REGION"] = gs.region_env(region=input_region)
    for r in results:
        for key in r.keys():
            if allocation_disagreement_basename and "allocation_class_" in key:
                cl = key.replace("allocation_class_", "")
                if cl not in outputs:
                    outputs[cl] = {
                        "name": allocation_disagreement_basename + "_" + cl,
                        "param": key,
                        "inp": "",
                    }
            if quantity_disagreement_basename and "quantity_class_" in key:
                cl = key.replace("quantity_class_", "")
                if cl not in outputs:
                    outputs[cl] = {
                        "name": quantity_disagreement_basename + "_" + cl,
                        "param": key,
                        "inp": "",
                    }
        for k in outputs:
            if outputs[k]["param"] in r and r[outputs[k]["param"]] is not None:
                outputs[k]["inp"] += f"{r['e']},{r['n']},{r[outputs[k]['param']]}\n"
    for k in outputs:
        gs.write_command(
            "r.in.xyz",
            input="-",
            stdin=outputs[k]["inp"],
            output=outputs[k]["name"],
            method="mean",
            separator="comma",
            env=env,
            quiet=True,
        )
        gs.raster_history(outputs[k]["name"])


if __name__ == "__main__":
    sys.exit(main())
