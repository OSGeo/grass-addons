#!/usr/bin/env python3
#
##############################################################################
#
# MODULE:       r.futures.demand
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      create demand table for FUTURES
#
# COPYRIGHT:    (C) 2015-2020 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (version 2). Read the file COPYING that comes with GRASS
# 		for details.
#
##############################################################################

# %module
# % description: Script for creating demand table which determines the quantity of land change expected.
# % keyword: raster
# % keyword: demand
# %end
# %option G_OPT_R_INPUTS
# % key: development
# % description: Names of input binary raster maps representing development
# % guisection: Input maps
# %end
# %option G_OPT_R_INPUT
# % key: subregions
# % description: Raster map of subregions
# % guisection: Input maps
# %end
# %option G_OPT_F_INPUT
# % key: observed_population
# % description: CSV file with observed population in subregions at certain times
# % guisection: Input population
# %end
# %option G_OPT_F_INPUT
# % key: projected_population
# % description: CSV file with projected population in subregions at certain times
# % guisection: Input population
# %end
# %option
# % type: integer
# % key: simulation_times
# % multiple: yes
# % required: yes
# % description: For which times demand is projected
# % guisection: Output
# %end
# %option
# % type: string
# % key: method
# % multiple: yes
# % required: yes
# % description: Relationship between developed cells (dependent) and population (explanatory)
# % options: linear, logarithmic, exponential, exp_approach, logarithmic2
# % descriptions:linear;y = A + Bx;logarithmic;y = A + Bln(x);exponential;y = Ae^(BX);exp_approach;y = (1 - e^(-A(x - B))) + C   (SciPy);logarithmic2;y = A + B * ln(x - C)   (SciPy)
# % answer: linear,logarithmic
# % guisection: Optional
# %end
# %option G_OPT_F_OUTPUT
# % key: plot
# % required: no
# % label: Save plotted relationship between developed cells and population into a file
# % description: File type is given by extension (.pdf, .png, .svg)
# % guisection: Output
# %end
# %option G_OPT_F_OUTPUT
# % key: demand
# % description: Output CSV file with demand (times as rows, regions as columns)
# % guisection: Output
# %end
# %option G_OPT_F_SEP
# % label: Separator used in CSV files
# % guisection: Optional
# % answer: comma
# %end


import sys
import math
import numpy as np

import grass.script.core as gcore
import grass.script.utils as gutils


def exp_approach(x, a, b, c):
    return (1 - np.exp(-a * (x - b))) + c


def logarithmic2(x, a, b, c):
    return a + b * np.log(x - c)


def logarithmic(x, a, b):
    return a + b * np.log(x)


def magnitude(x):
    return int(math.log10(x))


def main():
    developments = options["development"].split(",")
    observed_popul_file = options["observed_population"]
    projected_popul_file = options["projected_population"]
    sep = gutils.separator(options["separator"])
    subregions = options["subregions"]
    methods = options["method"].split(",")
    plot = options["plot"]
    simulation_times = [float(each) for each in options["simulation_times"].split(",")]

    for each in methods:
        if each in ("exp_approach", "logarithmic2"):
            try:
                from scipy.optimize import curve_fit
            except ImportError:
                gcore.fatal(
                    _("Importing scipy failed. Method '{m}' is not available").format(
                        m=each
                    )
                )

    # exp approach needs at least 3 data points
    if len(developments) <= 2 and (
        "exp_approach" in methods or "logarithmic2" in methods
    ):
        gcore.fatal(_("Not enough data for method 'exp_approach'"))
    if len(developments) == 3 and (
        "exp_approach" in methods and "logarithmic2" in methods
    ):
        gcore.warning(
            _(
                "Can't decide between 'exp_approach' and 'logarithmic2' methods"
                " because both methods can have exact solutions for 3 data points resulting in RMSE = 0"
            )
        )
    observed_popul = np.genfromtxt(
        observed_popul_file, dtype=float, delimiter=sep, names=True
    )
    projected_popul = np.genfromtxt(
        projected_popul_file, dtype=float, delimiter=sep, names=True
    )
    year_col = observed_popul.dtype.names[0]
    observed_times = observed_popul[year_col]
    year_col = projected_popul.dtype.names[0]
    projected_times = projected_popul[year_col]

    if len(developments) != len(observed_times):
        gcore.fatal(
            _(
                "Number of development raster maps does not correspond to the number of observed times"
            )
        )

    # gather developed cells in subregions
    gcore.info(_("Computing number of developed cells..."))
    table_developed = {}
    subregionIds = set()
    for i in range(len(observed_times)):
        gcore.percent(i, len(observed_times), 1)
        data = gcore.read_command(
            "r.univar", flags="gt", zones=subregions, map=developments[i]
        )
        for line in data.splitlines():
            stats = line.split("|")
            if stats[0] == "zone":
                continue
            subregionId, developed_cells = stats[0], int(stats[12])
            subregionIds.add(subregionId)
            if i == 0:
                table_developed[subregionId] = []
            table_developed[subregionId].append(developed_cells)
        gcore.percent(1, 1, 1)
    subregionIds = sorted(list(subregionIds))
    # linear interpolation between population points
    population_for_simulated_times = {}
    for subregionId in table_developed.keys():
        population_for_simulated_times[subregionId] = np.interp(
            x=simulation_times,
            xp=np.append(observed_times, projected_times),
            fp=np.append(observed_popul[subregionId], projected_popul[subregionId]),
        )
    # regression
    demand = {}
    i = 0
    if plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        n_plots = int(np.ceil(np.sqrt(len(subregionIds))))
        fig = plt.figure(figsize=(5 * n_plots, 5 * n_plots))

    for subregionId in subregionIds:
        i += 1
        rmse = dict()
        predicted = dict()
        simulated = dict()
        coeff = dict()
        for method in methods:
            # observed population points for subregion
            reg_pop = observed_popul[subregionId]
            simulated[method] = np.array(population_for_simulated_times[subregionId])

            if method in ("exp_approach", "logarithmic2"):
                # we have to scale it first
                y = np.array(table_developed[subregionId])
                magn = float(
                    np.power(10, max(magnitude(np.max(reg_pop)), magnitude(np.max(y))))
                )
                x = reg_pop / magn
                y = y / magn
                if method == "exp_approach":
                    initial = (
                        0.5,
                        np.mean(x),
                        np.mean(y),
                    )  # this seems to work best for our data for exp_approach
                elif method == "logarithmic2":
                    popt, pcov = curve_fit(logarithmic, x, y)
                    initial = (popt[0], popt[1], 0)
                with np.errstate(
                    invalid="warn"
                ):  # when 'raise' it stops every time on FloatingPointError
                    try:
                        popt, pcov = curve_fit(globals()[method], x, y, p0=initial)
                        if np.isnan(popt).any():
                            raise RuntimeError
                        # would result in nans in predicted
                        if method == "logarithmic2" and np.any(
                            simulated[method] / magn <= popt[-1]
                        ):
                            raise RuntimeError
                    except (FloatingPointError, RuntimeError):
                        gcore.warning(
                            _(
                                "Method '{m}' cannot converge for subregion {reg}".format(
                                    m=method, reg=subregionId
                                )
                            )
                        )
                        rmse[method] = sys.maxsize  # so that other method is selected
                        coeff[method] = (np.nan, np.nan, np.nan)
                        predicted[method] = np.zeros(len(simulated[method]))
                        if len(methods) == 1:
                            gcore.warning(
                                _(
                                    "Method '{m}' failed for subregion {reg},"
                                    " please consider selecting at least one other method"
                                ).format(m=method, reg=subregionId)
                            )
                    else:
                        predicted[method] = (
                            globals()[method](simulated[method] / magn, *popt) * magn
                        )
                        r = (
                            globals()[method](x, *popt) * magn
                            - table_developed[subregionId]
                        )
                        coeff[method] = popt
                        if len(reg_pop) > 3:
                            rmse[method] = np.sqrt((np.sum(r * r) / (len(reg_pop) - 3)))
                        else:
                            rmse[method] = 0
            else:
                if method == "logarithmic":
                    reg_pop = np.log(reg_pop)
                if method == "exponential":
                    y = np.log(table_developed[subregionId])
                else:
                    y = table_developed[subregionId]
                A = np.vstack((reg_pop, np.ones(len(reg_pop)))).T
                npversion = [int(x) for x in np.__version__.split(".")]
                if npversion >= [1, 14, 0]:
                    rcond = None
                else:
                    rcond = -1
                # if 0 in pop data, filter them out
                y = np.array(y)
                y = y[~np.isinf(A).any(axis=1)]
                A = A[~np.isinf(A).any(axis=1)]
                m, c = np.linalg.lstsq(A, y, rcond=rcond)[0]  # y = mx + c
                coeff[method] = m, c

                if method == "logarithmic":
                    with np.errstate(invalid="ignore", divide="ignore"):
                        predicted[method] = np.where(
                            simulated[method] > 1, np.log(simulated[method]) * m + c, 0
                        )
                    predicted[method] = np.where(
                        predicted[method] > 0, predicted[method], 0
                    )
                    r = (reg_pop * m + c) - table_developed[subregionId]
                elif method == "exponential":
                    predicted[method] = np.exp(m * simulated[method] + c)
                    r = np.exp(m * reg_pop + c) - table_developed[subregionId]
                else:  # linear
                    predicted[method] = simulated[method] * m + c
                    r = (reg_pop * m + c) - table_developed[subregionId]
                # RMSE
                if len(reg_pop) > 2:
                    rmse[method] = np.sqrt((np.sum(r * r) / (len(reg_pop) - 2)))
                else:
                    rmse[method] = 0
            # if inverse, create a fallback method that keeps
            # the latest population density
            # TODO: revise the other fallback method below
            if (
                method in ("linear", "logarithmic", "exp_approach")
                and coeff[method][0] < 0
            ) or (method == "logarithmic2" and coeff[method][1] < 0):
                method = "fallback"
                c = 0
                m = table_developed[subregionId][-1] / observed_popul[subregionId][-1]
                coeff[method] = m, c
                rmse[method] = -1
                simulated[method] = np.array(
                    population_for_simulated_times[subregionId]
                )
                predicted[method] = simulated[method] * m + c

        method = min(rmse, key=rmse.get)
        gcore.verbose(
            _("Method '{meth}' was selected for subregion {reg}").format(
                meth=method, reg=subregionId
            )
        )
        # write demand
        demand[subregionId] = predicted[method]
        demand[subregionId] = np.diff(demand[subregionId])
        if np.any(demand[subregionId] < 0):
            gcore.warning(
                _(
                    "Subregion {sub} has negative numbers"
                    " of newly developed cells, changing to zero".format(
                        sub=subregionId
                    )
                )
            )
            demand[subregionId][demand[subregionId] < 0] = 0
        if coeff[method][0] < 0 or np.isnan(coeff[method][0]):
            # couldn't establish reliable population-area
            # project by number of developed pixels in analyzed period
            range_developed = (
                table_developed[subregionId][-1] - table_developed[subregionId][0]
            )
            range_times = observed_times[-1] - observed_times[0]
            dev_per_step = math.ceil(range_developed / float(range_times))
            # this assumes demand is projected yearly
            demand[subregionId].fill(dev_per_step if dev_per_step > 0 else 0)
            gcore.warning(
                _(
                    "For subregion {sub} population and development are inversely proportional,"
                    " demand will be interpolated based on prior change in development only.".format(
                        sub=subregionId
                    )
                )
            )

        # draw
        if plot:
            ax = fig.add_subplot(n_plots, n_plots, i)
            ax.set_title(
                "{sid}, RMSE: {rmse:.3f}".format(sid=subregionId, rmse=rmse[method])
            )
            ax.set_xlabel("population")
            ax.set_ylabel("developed cells")
            # plot known points
            x = np.array(observed_popul[subregionId])
            y = np.array(table_developed[subregionId])
            ax.plot(x, y, marker="o", linestyle="", markersize=8)
            # plot predicted curve
            x_pred = np.linspace(
                np.min(x),
                np.max(np.array(population_for_simulated_times[subregionId])),
                30,
            )
            cf = coeff[method]
            if not np.isnan(cf[0]):
                if method in ("linear", "fallback"):
                    line = x_pred * cf[0] + cf[1]
                    label = "$y = {c:.3f} + {m:.3f} x$".format(m=cf[0], c=cf[1])
                elif method == "logarithmic":
                    line = np.log(x_pred) * cf[0] + cf[1]
                    label = "$y = {c:.3f} + {m:.3f} \ln(x)$".format(m=cf[0], c=cf[1])
                elif method == "exponential":
                    line = np.exp(x_pred * cf[0] + cf[1])
                    label = "$y = {c:.3f} e^{{{m:.3f}x}}$".format(
                        m=cf[0], c=np.exp(cf[1])
                    )
                elif method == "exp_approach":
                    line = exp_approach(x_pred / magn, *cf) * magn
                    label = "$y = (1 -  e^{{-{A:.3f}(x-{B:.3f})}}) + {C:.3f}$".format(
                        A=cf[0], B=cf[1], C=cf[2]
                    )
                elif method == "logarithmic2":
                    line = logarithmic2(x_pred / magn, *cf) * magn
                    label = "$y = {A:.3f} + {B:.3f} \ln(x-{C:.3f})$".format(
                        A=cf[0], B=cf[1], C=cf[2]
                    )
                ax.plot(x_pred, line, label=label)

            ax.plot(
                simulated[method],
                predicted[method],
                linestyle="",
                marker="o",
                markerfacecolor="None",
            )
            plt.legend(loc=0)
            labels = ax.get_xticklabels()
            plt.setp(labels, rotation=30)
    if plot:
        plt.tight_layout()
        fig.savefig(plot)

    # write demand
    with open(options["demand"], "w") as f:
        header = observed_popul.dtype.names  # the order is kept here
        header = [header[0]] + [sub for sub in header[1:] if sub in subregionIds]
        f.write(sep.join(header))
        f.write("\n")
        i = 0
        for time in simulation_times[1:]:
            f.write(str(int(time)))
            f.write(sep)
            # put 0 where there are more counties but are not in region
            for sub in header[1:]:  # to keep order of subregions
                f.write(str(int(demand[sub][i])))
                if sub != header[-1]:
                    f.write(sep)
            f.write("\n")
            i += 1


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main())
