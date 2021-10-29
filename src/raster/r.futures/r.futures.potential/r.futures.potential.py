#!/usr/bin/env python3
#
##############################################################################
#
# MODULE:       r.futures.potential
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      FUTURES Potential submodel
#
# COPYRIGHT:    (C) 2016-2020 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

#%module
#% description: Module for computing development potential as input to r.futures.pga
#% keyword: raster
#% keyword: statistics
#%end
#%option G_OPT_V_INPUT
#%end
#%option G_OPT_F_OUTPUT
#% description: Output Potential file
#%end
#%option G_OPT_F_SEP
#% label: Separator used in output file
#% answer: comma
#%end
#%option G_OPT_DB_COLUMNS
#% description: Names of attribute columns representing sampled predictors
#% required: yes
#%end
#%option G_OPT_DB_COLUMN
#% key: developed_column
#% description: Name of attribute column representing development
#% required: yes
#%end
#%option G_OPT_DB_COLUMN
#% key: subregions_column
#% description: Name of attribute column representing subregions
#% required: yes
#%end
#%option
#% type: string
#% key: fixed_columns
#% description: Predictor columns that will be used for all models when dredging
#% required: no
#% multiple: yes
#% guisection: Dredge
#%end
#%option
#% type: integer
#% key: min_variables
#% description: Minimum number of predictors considered
#% required: no
#% answer: 1
#% options: 1-20
#% guisection: Dredge
#%end
#%option
#% type: integer
#% key: max_variables
#% description: Maximum number of predictors considered
#% required: no
#% options: 1-20
#% guisection: Dredge
#%end
#%flag
#% key: d
#% description: Use dredge fuction to find best model
#% guisection: Dredge
#%end
#%option
#% type: integer
#% key: nprocs
#% description: Number of parallel processes for dredging
#% required: yes
#% answer: 1
#% options: 1-50
#% guisection: Dredge
#%end
#%option G_OPT_F_OUTPUT
#% required: no
#% key: dredge_output
#% description: Output CSV file summarizing all models
#% guisection: Dredge
#%end

import sys
import atexit
import subprocess
import grass.script as gscript
import grass.script.utils as gutils


rscript = """
# load required libraries
for (package in c("MuMIn", "lme4", "optparse")) {
    if (!(is.element(package, installed.packages()[,1]) ))
        stop(paste("Package", package, " not found"))
    }
suppressPackageStartupMessages(library(MuMIn))
suppressPackageStartupMessages(library(lme4))
suppressPackageStartupMessages(library(optparse))

option_list = list(
  make_option(c("-i","--input"), action="store", default=NA, type='character', help="input CSV file"),
  make_option(c("-o","--output"), action="store", default=NA, type='character', help="output CSV file"),
  make_option(c("-l","--level"), action="store", default=NA, type='character', help="level variable name"),
  make_option(c("-r","--response"), action="store", default=NA, type='character', help="binary response variable name"),
  make_option(c("-p","--predictors"), action="store", default=NA, type='character', help="predictors"),
  make_option(c("-d","--usedredge"), action="store", default=FALSE, type='logical', help="use dredge to find best model"),
  make_option(c("-m","--minimum"), action="store", default=NA, type='integer', help="minimum number of variables for dredge"),
  make_option(c("-x","--maximum"), action="store", default=NA, type='integer', help="maximum number of variables for dredge"),
  make_option(c("-n","--nprocs"), action="store", default=1, type='integer', help="number of processes for dredge"),
  make_option(c("-f","--fixed"), action="store", default=NA, type='character', help="fixed predictors for dredge"),
  make_option(c("-e","--export_dredge"), action="store", default=NA, type='character', help="output CSV file of all models (when using dredge)")
)
opt = parse_args(OptionParser(option_list=option_list))

if (opt$usedredge) {
    if (!(is.element("snow", installed.packages()[,1]) ))
        stop(paste("Package", "snow", " not found"))
    suppressPackageStartupMessages(library(snow))
}
# import data
input_data = read.csv(opt$input)
input_data <- na.omit(input_data)
# create global model with all variables
if (is.na(opt$predictors)) {
    predictors <- names(input_data)
} else {
    predictors <- strsplit(opt$predictors, ",")[[1]]
}
if (!is.na(opt$level)) {
    predictors <- predictors[predictors != opt$level]
}
predictors <- predictors[predictors != opt$response]

if (is.na(opt$level)) {
    fmla <- as.formula(paste(opt$response, " ~ ", paste(c(predictors), collapse= "+")))
    model = glm(formula=fmla, family = binomial, data=input_data, na.action = "na.fail")
} else {
    interc <- paste("(1|", opt$level, ")")
    fmla <- as.formula(paste(opt$response, " ~ ", paste(c(predictors, interc), collapse= "+")))
    model = glmer(formula=fmla, family = binomial, data=input_data, na.action = "na.fail")
}

if(opt$usedredge) {
    clust <- makeCluster(getOption("cl.cores", opt$nprocs), type="SOCK")
    clusterEvalQ(clust, library(lme4))
    clusterExport(clust, "input_data")
    if ( ! is.na(opt$fixed)) {
        fixed <- strsplit(opt$fixed, ",")[[1]]
        fixed <- paste(c(fixed), collapse= "+")
        if (is.na(opt$level)) {
            fixed <- paste(" ~ ",  fixed)
        }
        else {
            fixed <- paste(" ~ ",  fixed, " + ", paste("(1|", opt$level, ")", sep=""))
        }
        fmla_fixed <- as.formula(fixed)
    }
    else {
        fmla_fixed = NULL
    }
    #create all possible models, always include county as the level
    if (is.na(opt$level)) {
        select.model <- pdredge(model, clust, evaluate=TRUE, rank="AIC", fixed=fmla_fixed, m.lim=c(opt$minimum, opt$maximum), trace=FALSE)
    } else {
        select.model <- pdredge(model, clust, evaluate=TRUE, rank="AIC", fixed=fmla_fixed, m.lim=c(opt$minimum, opt$maximum), trace=FALSE)
    }
    # save the best model
    if (! is.na(opt$export_dredge)) {
        allmodels = as.data.frame(select.model)
        write.table(cbind(rownames(allmodels), allmodels), opt$export_dredge, row.names=FALSE, sep=",")
    }
    model.best <- get.models(select.model, 1)
    if (is.na(opt$level)) {
        model = glm(formula(model.best[[1]]), family = binomial, data=input_data, na.action = "na.fail")
    } else {
        model = glmer(formula(model.best[[1]]), family = binomial, data=input_data, na.action = "na.fail")
    }
}
print(summary(model))
if (is.na(opt$level)) {
    coefs <- t(as.data.frame(coef(model)))
} else {
    coefs <- as.data.frame(coef(model)[[1]])
}
write.table(cbind(rownames(coefs), coefs), opt$output, row.names=FALSE, sep="\t")
"""

TMP_CSV = None
TMP_POT = None
TMP_DREDGE = None
TMP_RSCRIPT = None


def cleanup():
    gscript.try_remove(TMP_CSV)
    gscript.try_remove(TMP_POT)
    gscript.try_remove(TMP_DREDGE)
    gscript.try_remove(TMP_RSCRIPT)


def main():
    vinput = options["input"]
    columns = options["columns"].split(",")
    binary = options["developed_column"]
    level = options["subregions_column"]
    sep = gutils.separator(options["separator"])
    minim = int(options["min_variables"])
    dredge = flags["d"]
    nprocs = int(options["nprocs"])
    fixed_columns = (
        options["fixed_columns"].split(",") if options["fixed_columns"] else []
    )

    for each in fixed_columns:
        if each not in columns:
            gscript.fatal(
                _(
                    "Fixed predictor {} not among predictors specified in option 'columns'"
                ).format(each)
            )
    if options["max_variables"]:
        maxv = int(options["max_variables"])
    else:
        maxv = len(columns)
    if dredge and minim > maxv:
        gscript.fatal(
            _("Minimum number of predictor variables is larger than maximum number")
        )

    if not gscript.find_program("Rscript", "--version"):
        gscript.fatal(
            _(
                "Rscript required for running r.futures.potential, but not found. "
                "Make sure you have R installed and added to the PATH."
            )
        )

    global TMP_CSV, TMP_RSCRIPT, TMP_POT, TMP_DREDGE
    TMP_CSV = gscript.tempfile(create=False) + ".csv"
    TMP_RSCRIPT = gscript.tempfile()
    include_level = True
    distinct = gscript.read_command(
        "v.db.select",
        flags="c",
        map=vinput,
        columns="distinct {level}".format(level=level),
    ).strip()
    if len(distinct.splitlines()) <= 1:
        include_level = False
        single_level = distinct.splitlines()[0]
    with open(TMP_RSCRIPT, "w") as f:
        f.write(rscript)
    TMP_POT = gscript.tempfile(create=False) + "_potential.csv"
    TMP_DREDGE = gscript.tempfile(create=False) + "_dredge.csv"
    columns += [binary]
    if include_level:
        columns += [level]
    where = "{c} IS NOT NULL".format(c=columns[0])
    for c in columns[1:]:
        where += " AND {c} IS NOT NULL".format(c=c)
    gscript.run_command(
        "v.db.select",
        map=vinput,
        columns=columns,
        separator="comma",
        where=where,
        file=TMP_CSV,
    )

    if dredge:
        gscript.info(_("Running automatic model selection ..."))
    else:
        gscript.info(_("Computing model..."))

    cmd = [
        "Rscript",
        TMP_RSCRIPT,
        "-i",
        TMP_CSV,
        "-r",
        binary,
        "-o",
        TMP_POT,
        "-p",
        ",".join(columns),
        "-m",
        str(minim),
        "-x",
        str(maxv),
        "-d",
        "TRUE" if dredge else "FALSE",
        "-n",
        str(nprocs),
    ]
    if include_level:
        cmd += ["-l", level]
    if dredge and fixed_columns:
        cmd += ["-f", ",".join(fixed_columns)]
    if dredge and options["dredge_output"]:
        cmd += ["-e", TMP_DREDGE]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if stderr:
        gscript.warning(gscript.decode(stderr))
    if p.returncode != 0:
        gscript.fatal(_("Running R script failed, check messages above"))

    gscript.info(_("Best model summary:"))
    gscript.info("-------------------------")
    gscript.message(gscript.decode(stdout))

    with open(TMP_POT, "r") as fin, open(options["output"], "w") as fout:
        i = 0
        for line in fin.readlines():
            row = line.strip().split("\t")
            row = [each.strip('"') for each in row]
            if i == 0:
                row[0] = "ID"
                row[1] = "Intercept"
            if i == 1 and not include_level:
                row[0] = single_level
            fout.write(sep.join(row))
            fout.write("\n")
            i += 1
    if options["dredge_output"]:
        with open(TMP_DREDGE, "r") as fin, open(options["dredge_output"], "w") as fout:
            i = 0
            for line in fin.readlines():
                row = line.strip().split(",")
                row = [each.strip('"') for each in row]
                if i == 0:
                    row[0] = "ID"
                    row[1] = "Intercept"
                fout.write(sep.join(row))
                fout.write("\n")
                i += 1


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())
