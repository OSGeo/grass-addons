#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##############################################################################
#
# MODULE:       r.futures.potential
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      FUTURES Potential submodel
#
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
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
#% type: integer
#% key: min_variables
#% description: Minimum number of predictors considered
#% required: no
#% answer: 1
#% options: 1-20
#%end
#%option
#% type: integer
#% key: max_variables
#% description: Maximum number of predictors considered
#% required: no
#% options: 1-20
#%end
#%flag
#% key: d
#% description: Use dredge fuction to find best model
#%end

import sys
import atexit
import subprocess
import grass.script as gscript


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
  make_option(c("-d","--usedredge"), action="store", default=NA, type='logical', help="use dredge to find best model"),
  make_option(c("-m","--minimum"), action="store", default=NA, type='integer', help="minimum number of variables for dredge"),
  make_option(c("-x","--maximum"), action="store", default=NA, type='integer', help="maximum number of variables for dredge")
)

opt = parse_args(OptionParser(option_list=option_list))

# import data
input_data = read.csv(opt$input)
# create global model with all variables
predictors <- names(input_data)
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
    #create all possible models, always include county as the level
    if (is.na(opt$level)) {
        select.model <- dredge(model, evaluate=TRUE, rank="AIC", m.lim=c(opt$minimum, opt$maximum), trace=FALSE)
    } else {
        select.model <- dredge(model, evaluate=TRUE, rank="AIC", fixed=~(1|opt$level), m.lim=c(opt$minimum, opt$maximum), trace=FALSE)
    }
    # save the best model
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
TMP_RSCRIPT = None


def cleanup():
    gscript.try_remove(TMP_CSV)
    gscript.try_remove(TMP_POT)
    gscript.try_remove(TMP_RSCRIPT)


def main():
    vinput = options['input']
    columns = options['columns'].split(',')
    binary = options['developed_column']
    level = options['subregions_column']
    minim = int(options['min_variables'])
    dredge = flags['d']
    if options['max_variables']:
        maxv = int(options['max_variables'])
    else:
        maxv = len(columns)
    if dredge and minim > maxv:
        gscript.fatal(_("Minimum number of predictor variables is larger than maximum number"))

    global TMP_CSV, TMP_RSCRIPT, TMP_POT
    TMP_CSV = gscript.tempfile(create=False) + '.csv'
    TMP_RSCRIPT = gscript.tempfile()
    include_level = True
    distinct = gscript.read_command('v.db.select', flags='c', map=vinput,
                                    columns="distinct {l}".format(l=level)).strip()
    if len(distinct.splitlines()) <= 1:
        include_level = False
        single_level = distinct.splitlines()[0]
    with open(TMP_RSCRIPT, 'w') as f:
        f.write(rscript)
    TMP_POT = gscript.tempfile(create=False) + '_potential.csv'
    columns += [binary]
    if include_level:
        columns += [level]
    where = "{c} IS NOT NULL".format(c=columns[0])
    for c in columns[1:]:
        where += " AND {c} IS NOT NULL".format(c=c)
    gscript.run_command('v.db.select', map=vinput, columns=columns, separator='comma', where=where, file=TMP_CSV)

    if dredge:
        gscript.info(_("Running automatic model selection ..."))
    else:
        gscript.info(_("Computing model..."))

    cmd = ['Rscript', TMP_RSCRIPT, '-i', TMP_CSV,  '-r', binary,
               '-m', str(minim), '-x', str(maxv), '-o', TMP_POT, '-d', 'TRUE' if dredge else 'FALSE']
    if include_level:
        cmd += [ '-l', level]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print(gscript.decode(stderr))
    if p.returncode != 0:
        print(gscript.decode(stderr))
        gscript.fatal(_("Running R script failed, check messages above"))

    gscript.info(_("Best model summary:"))
    gscript.info("-------------------------")
    print(gscript.decode(stdout))

    with open(TMP_POT, 'r') as fin, open(options['output'], 'w') as fout:
        i = 0
        for line in fin.readlines():
            row = line.strip().split('\t')
            row = [each.strip('"') for each in row]
            if i == 0:
                row[0] = "ID"
                row[1] = "Intercept"
            if i == 1 and not include_level:
                row[0] = single_level
            fout.write('\t'.join(row))
            fout.write('\n')
            i += 1


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())

