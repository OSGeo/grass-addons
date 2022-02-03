#!/usr/bin/env python
# -*- coding: utf-8  -*-
#
############################################################################
#
# MODULE:       r.series.decompose
#
# AUTHOR(S):    Dmitry Kolesov <kolesov.dm@gmail.com>
#
# PURPOSE:      Perform decomposition of time series X :
#               X(t) = b0 + b1 *t + sin(2*pi*t/N) + cos(2*pi*t/N) + ... + sin(2*pi*t/k*N) + cos(2*pi*t/k*N)
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %Module
# % description: Calculates decomposition of time series X.
# % overwrite: yes
# % keyword: raster
# % keyword: statistics
# % keyword: series
# % keyword: decomposition
# %End
# %option
# % key: input
# % type: string
# % gisprompt: list of raster names
# % description: Raster names of equally spaced time series.
# % required : yes
# % multiple: yes
# %end
# %option
# % key: result_prefix
# % type: string
# % gisprompt: prefix of result raster names
# % description: Prefix for raster names of filterd X(t)
# % required : yes
# % multiple: no
# %end
# %option
# % key: coef_prefix
# % type: string
# % gisprompt: prefix for raster names of decomposition coefficients
# % description: Prefix for names of result raster (rasters of coefficients)
# % required : yes
# % multiple: no
# %end
# %option
# % key:  timevar_prefix
# % type: string
# % gisprompt: prefix for raster names of time variables
# % description: Prefix for names of result raster (rasters of time variables)
# % required : yes
# % multiple: no
# %end
# %option
# % key: freq
# % type: double
# % gisprompt: list of used frequiences
# % description:  List of frequencies for sin and cos functions
# % required : yes
# % multiple: yes
# %end


import os
import sys
import csv
import uuid

from math import pi, degrees

if "GISBASE" not in os.environ:
    sys.stderr.write("You must be in GRASS GIS to run this program.\n")
    sys.exit(1)

import grass.script as grass


def get_time(N, t, deg=True):
    """Returns point number t from linspace [0, 2*pi]
    if deg == True, return degrees
    """

    step = 2 * pi / N
    x = step * t
    if deg:
        x = degrees(x)
    return x


def _freq_to_name(freq):
    return "_fr%s" % (freq)


def _time_to_name(time):
    return "_t%04d" % (time,)


def _generate_time(N, prefix):
    """Generate (constant) rasters of time line
        t0, t1, t2, ..., t_{N-1})
        where t0 = 0, t_{N-1} = 2*pi

    N -- count of result rasters
    prefix -- prefix for the raster names

    return list of names for the result rasters
    """
    assert N > 1
    names = dict()
    for i in range(N):
        output = prefix + _time_to_name(i)
        t = get_time(N, i, deg=True)
        grass.mapcalc(
            "${out} = ${t}", out=output, t=t, quiet=True, overwrite=grass.overwrite()
        )
        names[i] = output

    return names


def _generate_harmonics(time_names, freq, prefix):
    """Generate (constant) rasters of harmonics
        t0, t1, t2, ..., t_{N-1})
        where t0 = 0, t_{N-1} = 2*pi

    freq -- frequencies for sin() and cos() rasters
    prefix -- prefix for the raster names

    return list of names for the result rasters
    """
    names = dict()
    for i in time_names:
        harm = dict()
        t = get_time(len(time_names), i)
        for f in freq:
            sin_output = prefix + "sin" + _time_to_name(i) + _freq_to_name(f)
            grass.mapcalc(
                "${out} = sin(${f} * ${t})",
                out=sin_output,
                t=t,
                f=f,
                quiet=True,
                overwrite=grass.overwrite(),
            )

            cos_output = prefix + "cos" + _time_to_name(i) + _freq_to_name(f)
            grass.mapcalc(
                "${out} = cos(${f} * ${t})",
                out=cos_output,
                t=t,
                f=f,
                quiet=True,
                overwrite=grass.overwrite(),
            )
            harm[f] = dict(sin=sin_output, cos=cos_output)

        names[i] = harm

    return names


def _generate_const(prefix):
    output = prefix + "const"
    grass.mapcalc("${out} = 1.0", out=output, quiet=True, overwrite=grass.overwrite())
    return output


def generate_vars(time_count, freq, prefix):
    """Generate time_count sets of variables."""
    const_name = _generate_const(prefix)
    time_names = _generate_time(time_count, prefix)
    harm_names = _generate_harmonics(time_names, freq, prefix)

    return const_name, time_names, harm_names


def _generate_sample_descr(fileobj, freq, xnames, const_name, time_names, harm_names):
    """Generate settings file for r.mregression.series"""
    freq_names = []
    for f in freq:
        freq_names.append("sin" + _freq_to_name(f))
        freq_names.append("cos" + _freq_to_name(f))
    header = ["x", "const", "time"] + freq_names

    writer = csv.writer(fileobj, delimiter=",")
    writer.writerow(header)

    size = len(xnames)
    for i in range(size):
        row = [xnames[i], const_name, time_names[i]]
        f_name = harm_names[i]
        for f in freq:
            sin_name = f_name[f]["sin"]
            cos_name = f_name[f]["cos"]
            row.append(sin_name)
            row.append(cos_name)
        writer.writerow(row)


def regression(settings_name, coef_prefix):
    grass.run_command(
        "r.mregression.series",
        samples=settings_name,
        result_prefix=coef_prefix,
        overwrite=grass.overwrite(),
    )


def inverse_transform(settings_name, coef_prefix, result_prefix="res."):
    reader = csv.reader(open(settings_name), delimiter=",")
    header = reader.next()

    data_names = [coef_prefix + name for name in header[1:]]

    for row in reader:
        s = "%s%s = " % (result_prefix, row[0])
        sums = []
        for i in range(len(data_names)):
            sums.append("%s*%s" % (data_names[i], row[i + 1]))
        s += " + ".join(sums)

        grass.mapcalc(s, overwrite=grass.overwrite(), quite=True)


def main(options, flags):
    xnames = options["input"]
    coef_pref = options["coef_prefix"]
    timevar_pref = options["timevar_prefix"]
    result_pref = options["result_prefix"]
    freq = options["freq"]
    freq = [float(f) for f in freq.split(",")]

    xnames = xnames.split(",")

    N = len(xnames)
    if len(freq) >= (N - 1) / 2:
        grass.error("Count of used harmonics is to large. Reduce the paramether.")
        sys.exit(1)

    const_name, time_names, harm_names = generate_vars(N, freq, timevar_pref)

    settings_name = uuid.uuid4().hex
    settings = open(settings_name, "w")
    _generate_sample_descr(settings, freq, xnames, const_name, time_names, harm_names)
    settings.close()
    regression(settings_name, coef_pref)
    inverse_transform(settings_name, coef_pref, result_pref)
    os.unlink(settings_name)


if __name__ == "__main__":
    options, flags = grass.parser()
    main(options, flags)
