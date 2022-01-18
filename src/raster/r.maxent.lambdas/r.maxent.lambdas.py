#!/usr/bin/env python

"""
MODULE:       r.maxent.lambdas
AUTHOR(S):    Stefan Blumentrath <stefan dot blumentrath at nina dot no >
              Proposed small change in how raw features are extracted
              from the lambdas file as this didn't work in original
              code (Paulo van Breugel)
PURPOSE:      Compute raw and/or logistic prediction maps from a lambdas
              file produced with MaxEnt >= 3.3.3e.

              !!!This script works only if the input data to MaxEnt
              are accessible from the current mapset.!!!

              This script will parse the specified lambdas-file from
              MaxEnt >= 3.3.3e (see http://biodiversityinformatics.amnh.org/open_source/maxent/)
              and translate it into an r.mapcalc-expression which can be stored
              in a file.

              If alias names were used in MaxEnt, these alias names can
              automatically be replaced according to a  CSV-like file provided
              by the user. This file should contain alias names in the first
              column and map names in the second column, separated by comma,
              without header. It should look e.g. like this:

              alias_1,map_1
              alias_2,map_2
              ...,...

              A raw output map is always computed from the MaxEnt model
              as a first step. If only logistic output is requested, the raw output
              map will be deleted. The  production of logistic output can be omitted.

              The logistic map can be produced as an integer map. To do so the user
              has to specify the number of digits after comma, that should be preserved in
              integer output.

              Optionally the map calculator expressions can be saved in a text
              file, as especially the one for the raw output is likely to exceed
              the space in the map history.

              Due to conversion from double to floating-point in exp()-function, a
              loss of precision from the 7th digit onwards is possible in the
              logistic output.

COPYRIGHT:    (C) 2019-2022 by the Norwegian Institute for Nature Research
              http://www.nina.no, Stefan Bluentrath and the GRASS GIS
              Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

#%Module
#% description: Computes raw or logistic prediction maps from MaxEnt lambdas files
#% keyword: raster
#% keyword: maxent
#% keyword: ecology
#% keyword: niche
#%End

#%flag
#% key: p
#% label: Print only
#% description: Print mapcalculator expressions and exit
#%end

#%flag
#% key: n
#% label: Do not include cells where any variabel contains no data
#%end

#%flag
#% key: N
#% label: Do not include cells where all variabels contain no data
#%end

#%option G_OPT_F_INPUT
#% key: lambdas_file
#% description: MaxEnt lambdas-file to compute distribution-model from
#% required : yes
#%end

#%option G_OPT_F_INPUT
#% key: alias_file
#% description: CSV-file to replace alias names from MaxEnt by GRASS map names
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#% key: logistic
#% description: Raster map with logistic output
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#% key: raw
#% description: Raster map with raw output
#% required : no
#%end

#%option
#% key: ndigits
#% type: integer
#% description: Produce logistic output as integer map with this number of digits preserved
#% required : no
#% answer : 0
#%end

#%rules
#% required: logistic,raw
#% exclusive: logistic,raw
#% exclusive: -n,-N
#%end

import os

from grass.pygrass.raster import RasterAbstractBase
import grass.script as gscript
from grass.script.raster import mapcalc, raster_history


def parse_alias(alias_file):
    """Parse alias file if provided"""
    if alias_file:
        if not os.access(alias_file, os.R_OK):
            gscript.fatal(
                _("Alias file <{}> not found or not readable".format(alias_file))
            )

        with open(alias_file, "r") as a_f:
            alias_dict = gscript.parse_key_val(a_f.read(), sep=",")
    else:
        alias_dict = None

    if alias_dict:
        for alias in alias_dict:
            # Check if environmental parameter map(s) exist
            full_name = alias_dict[alias]
            if "@" in full_name:
                raster, mapset = full_name.split("@")
            else:
                raster, mapset = full_name, ""
            raster_map = RasterAbstractBase(raster, mapset)
            mapset = "." if not mapset else mapset
            if not raster_map.exist():
                gscript.fatal(
                    _(
                        "Could not find environmental parameter raster map <{}> in mapset <{}>.".format(
                            raster, mapset
                        )
                    )
                )

    return alias_dict


def parse_lambdas_row(row, coeff, alias_dict):
    """Translate Maxent function to mapcalc"""
    if "=" in row:  # categorical
        coeff = (
            row.lstrip("(")
            .replace(")", "")
            .replace(" ", "")
            .replace("=", ",")
            .split(",")
        )
        mc_row = [(coeff[0],), "if({0}=={1},{2},0)".format(*coeff)]
    elif row.startswith("("):  # threshold
        coeff = (
            row.lstrip("()")
            .replace(")", "")
            .replace("<", ",<,")
            .replace(">", ",>,")
            .split(",")
        )
        # if x < threshold then fx = 0 otherwise fx = lambda
        mc_row = [(coeff[0],), "if({0}{1}{2},{3},0)".format(*coeff)]
    elif "^" in row:  # quadratic
        mc_row = [(coeff[0],), "{1}*(({0})-{2})/({3}-{2})".format(*coeff)]
    elif "*" in row:  # product
        mc_row = [
            tuple(coeff[0].split("*")),
            "{1}*(({0})-{2})/({3}-{2})".format(*coeff),
        ]
    elif row.startswith("`"):  # reverse_hinge
        coeff = [coeff[0].lstrip("`")] + coeff[1:]
        mc_row = [
            (coeff[0],),
            "if({0}<{2},{1}*({0}-{2})/({3}-{2}),0.0)".format(*coeff),
        ]
    elif row.startswith("'"):  # forward_hinge
        coeff = [coeff[0].lstrip("'")] + coeff[1:]
        mc_row = [
            (coeff[0],),
            "if({0}<{2},0.0,{1}*({0}-{2})/({3}-{2}))".format(*coeff),
        ]
    else:  # 'linear'
        mc_row = [(coeff[0],), "{1}*({0}-{2})/({3}-{2})".format(*coeff)]
    if alias_dict:
        if not all(rmap in alias_dict for rmap in mc_row[0]):
            gscript.fatal(
                _(
                    "Invalid input: Variable {} not found in alias file".format(
                        mc_row[0]
                    )
                )
            )
        for rmap in mc_row[0]:
            mc_row[1] = mc_row[1].replace(rmap, alias_dict[rmap])
        mc_row[0] = (alias_dict[rmap] for rmap in mc_row[0])

    return mc_row


def main():
    """Do the main work"""
    lambdas_file = options["lambdas_file"]
    alias_file = options["alias_file"]

    if not options["ndigits"].isdigit():
        gscript.fatal(_("The ndigits option needs to be given as integer."))

    ndigits = int(options["ndigits"])

    if ndigits > 5 or ndigits < 0:
        gscript.warning(
            _(
                "Valid range for ndigits is 0 to 5. \
        Setting to closest bound."
            )
        )

    ndigits = max(0, min(ndigits, 5))

    raw = options["raw"]

    logistic = options["logistic"]

    # Check if input file exists and is readable
    if not os.access(lambdas_file, os.R_OK):
        gscript.fatal(_("MaxEnt lambdas-file could not be found or is not readable."))

    # Parse alias_file if provided
    alias_dict = parse_alias(alias_file)

    ###Parse lambdas-file and translate it to a mapcalculator expression
    ###Get variables linearPredictorNormalizer, densityNormalizer and entropy from lambdas-file
    with open(lambdas_file, "r") as l_f:
        mc_expression_parts = []
        for lrow in l_f:
            if (
                not lrow.strip()
                or lrow.startswith("numBackgroundPoints")
                or "," not in lrow
            ):
                continue
            coeff = lrow.replace(" ", "").rstrip("\n").split(",")
            if lrow.startswith("linearPredictorNormalizer"):
                linear_predictor_normalizer = coeff[1]
            elif lrow.startswith("densityNormalizer"):
                density_normalizer = coeff[1]
            # elif lrow.startswith("numBackgroundPoints"):
            # numBackgroundPoints = coeff[1]
            # continue
            elif lrow.startswith("entropy"):
                entropy = coeff[1]
            else:
                lrow = parse_lambdas_row(lrow, coeff, alias_dict)
                isnull = "|".join(["isnull({})".format(rmap) for rmap in lrow[0]])
                mc_expression_parts.append(
                    lrow[1] if flags["n"] else "if({0},0,{1})".format(isnull, lrow[1])
                )

    # Compile mapcalc-expression
    mc_expression_raw = "exp((("
    mc_expression_raw += "+".join(mc_expression_parts)
    mc_expression_raw += ")-{0}))/{1}".format(
        linear_predictor_normalizer, density_normalizer
    )

    ###Compute raw output map by sending expression saved in file temporary file to r.mapcalc
    if raw:
        raw_expr = "{out_map}_raw = {expr}".format(out_map=raw, expr=mc_expression_raw)
        if flags["p"]:
            print(raw_expr)
            return 0
        mapcalc(raw_expr)
        raster_history(raw, overwrite=True)

    ###Compute logistic output map if not suppressed
    if logistic:
        mc_expression_log = (
            "(({expr})*exp({entropy}))/(1.0+(({expr})*exp({entropy})))".format(
                expr=mc_expression_raw, entropy=entropy
            )
        )
        if ndigits > 0:
            mc_expression_log = "round(({expr})*(10^{ndigits}))".format(
                expr=mc_expression_log, ndigits=ndigits
            )
        log_expr = "{out_map}={expr}".format(out_map=logistic, expr=mc_expression_log)
        if flags["p"]:
            print(log_expr)
            return 0
        mapcalc(log_expr)
        if flags["N"]:
            gscript.run_command("r.null", map=logistic, setnull=0)
        raster_history(logistic, overwrite=True)
    return 0


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
