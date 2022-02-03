#!/usr/bin/env python3
#
##############################################################################
#
# MODULE:       r.futures.validation
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      Validation metrics (Quantity/Allocation Disagreement, Kappa Simulation)
#
# COPYRIGHT:    (C) 2016-2021 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

# %module
# % description: Module for land change simulation validation and accuracy assessment
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
# %option
# % key: format
# % type: string
# % description: Output format
# % options: plain,shell,json
# % required: no
# % answer: plain
# %end


import sys
import json
import numpy as np
import grass.script as gs


def print_results(
    formatting,
    cats,
    quantity,
    total_quantity,
    allocation,
    total_allocation,
    kappa,
    kappasim=None,
):
    if formatting == "plain":
        if total_quantity is None:
            print(_("No data found in current region"))
            return
        for i, c in enumerate(cats):
            print(
                _("Quantity disagreement for class {c}: {q:.2f} %").format(
                    c=c, q=quantity[i] * 100
                )
            )
        print(
            _("Total quantity disagreement: {q:.2f} %").format(q=total_quantity * 100)
        )
        for i, c in enumerate(cats):
            print(
                _("Allocation disagreement for class {c}: {q:.2f} %").format(
                    c=c, q=allocation[i] * 100
                )
            )
        print(
            _("Total allocation disagreement: {q:.2f} %").format(
                q=total_allocation * 100
            )
        )
        if kappa is not None:
            print(_("Kappa: {kappa:.4f}").format(kappa=kappa))
        if kappasim is not None:
            print(_("Kappa simulation: {kappasim:.4f}").format(kappasim=kappasim))
    elif formatting == "shell":

        def format_value(val):
            return f"{val:.4f}" if val is not None else ""

        for i, c in enumerate(cats):
            print(f"quantity_class_{c}={quantity[i]:.4f}")
        print(f"total_quantity={format_value(total_quantity)}")
        for i, c in enumerate(cats):
            print(f"allocation_class_{c}={allocation[i]:.4f}")
        print(f"total_allocation={format_value(total_allocation)}")
        print(f"kappa={format_value(kappa)}")
        if kappasim is not None:
            print(f"kappasimulation={kappasim:.4f}")
    elif formatting == "json":
        # export everything even when None
        # for automated processing
        out = {}
        for i, c in enumerate(cats):
            out[f"quantity_class_{c}"] = quantity[i]
        for i, c in enumerate(cats):
            out[f"allocation_class_{c}"] = allocation[i]
        out["total_quantity"] = total_quantity
        out["total_allocation"] = total_allocation
        out["kappa"] = kappa
        out["kappasimulation"] = kappasim
        print(
            json.dumps(
                json.loads(json.dumps(out), parse_float=lambda x: round(float(x), 4))
            )
        )


def compute(reference, simulated, original):
    results = {}
    if original:
        input_maps = [original, reference, simulated]
    else:
        input_maps = [reference, simulated]
    data = gs.read_command("r.stats", flags="cn", input=input_maps).strip()
    cats = []
    for line in data.splitlines():
        line = [int(n) for n in line.strip().split()]
        cats.extend(line[:-1])
    cats = sorted(list(set(cats)))
    if not cats:
        results["quantity"] = None
        results["total_quantity"] = None
        results["allocation"] = None
        results["total_allocation"] = None
        results["kappa"] = None
        if original:
            results["kappasim"] = None
        return cats, results

    n_cats = len(cats)
    ref_sim = np.zeros((n_cats, n_cats))
    orig_sim = np.zeros((n_cats, n_cats))
    orig_ref = np.zeros((n_cats, n_cats))
    for line in data.splitlines():
        line = [int(n) for n in line.strip().split()]
        if original:
            orig_idx = cats.index(line[0])
            ref_idx = cats.index(line[1])
            sim_idx = cats.index(line[2])
            ref_sim[sim_idx, ref_idx] += line[3]
            orig_sim[orig_idx, sim_idx] += line[3]
            orig_ref[orig_idx, ref_idx] += line[3]
        else:
            ref_idx = cats.index(line[0])
            sim_idx = cats.index(line[1])
            ref_sim[sim_idx, ref_idx] += line[2]
    # quantity disagreement
    quantity = np.abs(ref_sim.sum(axis=0) - ref_sim.sum(axis=1)) / ref_sim.sum()
    total_quantity = quantity.sum() / 2
    results["quantity"] = quantity
    results["total_quantity"] = total_quantity
    # allocation disagreement
    allocation = (
        2
        * np.minimum(
            ref_sim.sum(axis=0) - ref_sim.diagonal(),
            ref_sim.sum(axis=1) - ref_sim.diagonal(),
        )
        / ref_sim.sum()
    )
    total_allocation = allocation.sum() / 2
    results["allocation"] = allocation
    results["total_allocation"] = total_allocation
    # kappa
    p_0 = ref_sim.diagonal().sum() / ref_sim.sum()
    p_e = np.multiply(
        ref_sim.sum(axis=0) / ref_sim.sum(), ref_sim.sum(axis=1) / ref_sim.sum()
    ).sum()
    with np.errstate(all="raise"):
        try:
            kappa = (p_0 - p_e) / (1 - p_e)
            results["kappa"] = kappa
        except FloatingPointError:
            gs.warning(_("Kappa could not be computed due to division by zero"))
            results["kappa"] = None
    # kappa simulation
    if original:
        a = orig_sim / orig_sim.sum(axis=1)[:, None]
        b = orig_ref / orig_ref.sum(axis=1)[:, None]
        c = np.multiply(a, b)
        d = orig_sim.sum(axis=1) / orig_sim.sum()
        e = np.multiply(c.sum(axis=1), d)
        p_e = np.nansum(e)
        with np.errstate(all="raise"):
            try:
                kappasim = (p_0 - p_e) / (1 - p_e)
                results["kappasim"] = kappasim
            except FloatingPointError:
                gs.warning(
                    _("Kappa simulation could not be computed due to division by zero")
                )
                results["kappasim"] = None
    return cats, results


def main():
    options, flags = gs.parser()
    simulated = options["simulated"]
    original = options["original"]
    reference = options["reference"]
    oformat = options["format"]
    cats, results = compute(reference, simulated, original)
    print_results(oformat, cats, **results)


if __name__ == "__main__":
    sys.exit(main())
