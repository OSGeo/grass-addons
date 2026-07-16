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
# SPDX-FileCopyrightText: 2016-2021 Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
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
    misses=None,
    hits=None,
    false_alarms=None,
    null_successes=None,
    initially_developed=None,
    figure_of_merit=None,
    producer=None,
    user=None,
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
        if misses is not None:
            print(
                _(
                    "Observed change simulated as persistance (misses): {misses:.2f} %"
                ).format(misses=misses * 100)
            )
        if hits is not None:
            print(
                _("Observed change simulated as change (hits): {hits:.2f} %").format(
                    hits=hits * 100
                )
            )
        if false_alarms is not None:
            print(
                _(
                    "Observed persistance simulated as change (false alarms): {false_alarms:.2f} %"
                ).format(false_alarms=false_alarms * 100)
            )
        if null_successes is not None:
            print(
                _(
                    "Observed persistance simulated as persistance: {null_successes:.2f} %"
                ).format(null_successes=null_successes * 100)
            )
        if initially_developed is not None:
            print(
                _(
                    "Excluded as initially developed: {initially_developed:.2f} %"
                ).format(initially_developed=initially_developed * 100)
            )
        if figure_of_merit is not None:
            print(
                _("Figure of merit: {figure_of_merit:.4f}").format(
                    figure_of_merit=figure_of_merit
                )
            )
        if producer is not None:
            print(_("Producer's accuracy: {producer:.4f}").format(producer=producer))
        if user is not None:
            print(_("User's accuracy: {user:.4f}").format(user=user))

    elif formatting == "shell":

        def format_value(val):
            return f"{val:.6f}" if val is not None else ""

        for i, c in enumerate(cats):
            print(f"quantity_class_{c}={quantity[i]:.6f}")
        print(f"total_quantity={format_value(total_quantity)}")
        for i, c in enumerate(cats):
            print(f"allocation_class_{c}={allocation[i]:.6f}")
        print(f"total_allocation={format_value(total_allocation)}")
        print(f"kappa={format_value(kappa)}")
        if kappasim is not None:
            print(f"kappasimulation={kappasim:.6f}")
        if misses is not None:
            print(f"misses={misses:.6f}")
        if hits is not None:
            print(f"hits={hits:.6f}")
        if false_alarms is not None:
            print(f"false_alarms={false_alarms:.6f}")
        if null_successes is not None:
            print(f"null_successes={null_successes:.6f}")
        if figure_of_merit is not None:
            print(f"figure_of_merit={figure_of_merit:.6f}")
        if producer is not None:
            print(f"producer={producer:.6f}")
        if user is not None:
            print(f"user={user:.6f}")
        if initially_developed is not None:
            print(f"initially_developed={initially_developed:.6f}")
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
        out["misses"] = misses
        out["hits"] = hits
        out["false_alarms"] = false_alarms
        out["null_successes"] = null_successes
        out["figure_of_merit"] = figure_of_merit
        out["producer"] = producer
        out["user"] = user
        out["initially_developed"] = initially_developed
        print(
            json.dumps(
                json.loads(json.dumps(out), parse_float=lambda x: round(float(x), 6))
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
            results["misses"] = None
            results["hits"] = None
            results["false_alarms"] = None
            results["null_successes"] = None
            results["figure_of_merit"] = None
            results["producer"] = None
            results["user"] = None
            results["initially_developed"] = None
        return cats, results

    n_cats = len(cats)
    ref_sim = np.zeros((n_cats, n_cats))
    orig_sim = np.zeros((n_cats, n_cats))
    orig_ref = np.zeros((n_cats, n_cats))
    binary_cats = set(cats) == {0, 1}
    if original and not binary_cats:
        gs.verbose(
            _(
                "Change detection metrics (hits, misses, false alarms, figure of merit) "
                "require binary categories (0 and 1). Skipping these metrics."
            )
        )
    hits = false_alarms = misses = null_successes = initially_developed = 0
    for line in data.splitlines():
        line = [int(n) for n in line.strip().split()]
        if original:
            orig_idx = cats.index(line[0])
            ref_idx = cats.index(line[1])
            sim_idx = cats.index(line[2])
            ref_sim[sim_idx, ref_idx] += line[3]
            orig_sim[orig_idx, sim_idx] += line[3]
            orig_ref[orig_idx, ref_idx] += line[3]

            if binary_cats:
                # Pontius 2008
                # relies on 0 and 1 cats
                if orig_idx == 0:
                    if ref_idx == 0 and sim_idx == 1:
                        false_alarms += line[3]
                    elif ref_idx == 1 and sim_idx == 0:
                        misses += line[3]
                    elif ref_idx == 1 and sim_idx == 1:
                        hits += line[3]
                    elif ref_idx == 0 and sim_idx == 0:
                        null_successes += line[3]
                else:
                    initially_developed += line[3]
        else:
            ref_idx = cats.index(line[0])
            sim_idx = cats.index(line[1])
            ref_sim[sim_idx, ref_idx] += line[2]

    if original and binary_cats:
        total = misses + hits + false_alarms + null_successes + initially_developed
        results["misses"] = misses / total if total else None
        results["hits"] = hits / total if total else None
        results["false_alarms"] = false_alarms / total if total else None
        results["null_successes"] = null_successes / total if total else None
        results["figure_of_merit"] = (
            hits / (misses + hits + false_alarms) if misses + hits + false_alarms else 0
        )
        results["producer"] = hits / (misses + hits) if misses + hits else 0
        results["user"] = hits / (hits + false_alarms) if hits + false_alarms else 0
        results["initially_developed"] = initially_developed / total if total else None
    elif original:
        for key in [
            "misses",
            "hits",
            "false_alarms",
            "null_successes",
            "figure_of_merit",
            "producer",
            "user",
            "initially_developed",
        ]:
            results[key] = None
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
        # Suppress 0/0 warnings for categories absent in original; NaN handled by nansum
        with np.errstate(invalid="ignore"):
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

