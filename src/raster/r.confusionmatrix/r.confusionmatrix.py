#!/usr/bin/env python

############################################################################
#
# MODULE:	 r.confusionmatrix
#
# AUTHOR(S): Anika Weinmann <weinmann at mundialis.de>
#
# PURPOSE:   Calculates a confusion matrix and accuracies for a given classification using r.kappa.
#
# COPYRIGHT: (C) 2020-2023 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %Module
# % description: Calculates a confusion matrix and accuracies for a given classification using r.kappa.
# % keyword: raster
# % keyword: statistics
# % keyword: accuracy
# % keyword: classification
# %end

# %option G_OPT_R_INPUT
# % key: classification
# % required: no
# % description: Name of raster map containing classification result
# %end

# %option G_OPT_R_INPUT
# % key: raster_reference
# % required: no
# % description: Name of raster map containing reference classes
# %end

# %option G_OPT_V_INPUT
# % key: vector_reference
# % required: no
# % description: Name of vector map containing reference classes
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % required: no
# % description: Name of column in the vector map containing reference classes
# %end

# %option
# % key: label_column
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Name of column used as raster category labels
# %end

# %option G_OPT_F_OUTPUT
# % key: csvfile
# % required: no
# % label: Name for output csv file containing confusion matrix and accuracies
# % description: If not given write to standard output
# %end

# %flag
# % key: d
# % description: Description of the accuracies
# %end

# %flag
# % key: m
# % description: Print output as a matrix
# %end

import atexit
import csv
from math import nan
import numpy as np
import os
import sys
import grass.script as grass

# initialize global vars
rm_files = []


def cleanup():
    grass.message(_("Cleaning up..."))
    for rm_f in rm_files:
        if os.path.isfile(rm_f):
            os.remove(rm_f)


def print_descriptions():
    # http://gis.humboldt.edu/OLM/Courses/GSP_216_Online/lesson6-2/metrics.html

    # http://web.pdx.edu/~nauna/resources/9-accuracyassessment.pdf
    oa = "Overall accuracy\nNumber of correct pixels / total number of pixels"
    ua = (
        "User Accuracy\n"
        + "* From the perspective of the user of the classified map, how accurate is the map?\n"
        + "* For a given class, how many of the pixels on the map are actually what they say they are?\n"
        + "* Calculated as: Number correctly identified in a given map class / Number claimed to be in that map class\n"
    )
    pa = (
        "Producer Accuracy\n"
        + "* From the perspective of the maker of the classified map, how accurate is the map?\n"
        + "* For a given class in reference plots, how many of the pixels on the map are labeled correctly?\n"
        + "* Calculated as: Number correctly identified in ref. plots of a given class / Number actually in that reference class\n"
    )

    # http://gis.humboldt.edu/OLM/Courses/GSP_216_Online/lesson6-2/metrics.html
    om = (
        "Omission Error\n"
        + "Omission error refers to reference sites that were left out "
        + "(or omitted) from the correct class in the classified map. The real"
        + " land cover type was left out or omitted from the classified map.\n"
        + "Omission Error = 100 % - Producer Accuracy"
    )
    com = (
        "Commission Error\n"
        + "Commission error refers to sites that are classified as to reference sites that were "
        + "left out (or omitted) from the correct class in the classified map. "
        + "Commission errors are calculated by reviewing the classified sites "
        + "for incorrect classifications.\n"
        + "Commission Error = 100 % - User Accuracy"
    )

    # http://www.iww.forst.uni-goettingen.de/doc/ckleinn/lehre/waldmess/Material/rs_06_accuracy%20assessment.pdf
    kap = (
        "Kappa coefficient\n"
        + "It characterizes the degree of matching between reference data set and classification.\n"
        # + "In fact, it is a statistic that compares two matrices: here, it describes the difference between the agreement found in the actual matrix and the chance agreement given the same marginal frequencies:"
        + "Kappa = 0: indicates that obtained agreement equals chance agreement.\n"
        + "Kappa > 0: indicates that obtained agreement is greater than chance agreement.\n"
        + "Kappa < 0: indicates that obtained agreement is smaller than chance agreement.\n"
        + "Kappa = 1: is perfect agreement.\n"
    )

    # print descriptions
    grass.message(oa)
    grass.message("\n")
    grass.message(ua)
    grass.message("\n")
    grass.message(pa)
    grass.message("\n")
    grass.message(com)
    grass.message("\n")
    grass.message(om)
    grass.message("\n")
    grass.message(kap)
    grass.message("\n")


def set_reference(descriptionflag=None):
    if options["raster_reference"]:
        reference = options["raster_reference"]
        refname = reference
    elif options["vector_reference"] and options["column"]:
        savedregion = grass.tempname(12)
        grass.run_command("g.region", save=savedregion)
        grass.run_command("g.region", raster=options["classification"])
        reference = grass.tempname(12)
        kwargs = {
            "input": options["vector_reference"],
            "output": reference,
            "use": "attr",
            "attribute_column": options["column"],
        }
        if options["label_column"]:
            kwargs["label_column"] = options["label_column"]
        grass.run_command("v.to.rast", quiet=True, **kwargs)
        refname = options["vector_reference"] + " with column " + options["column"]
        # reset region
        grass.run_command("g.region", region=savedregion, quiet=True)
        # remove region
        grass.run_command(
            "g.remove", flags="f", type="region", name=savedregion, quiet=True
        )
    else:
        if not descriptionflag:
            grass.fatal(
                "Either <raster_reference> or <vector_reference> and <column> must be indicated"
            )
    return reference, refname


def get_r_kappa(classification, reference):
    tmp_csv = grass.tempfile()
    os.remove(tmp_csv)
    rm_files.append(tmp_csv)

    grass.run_command(
        "r.kappa",
        flags="wmh",
        classification=classification,
        reference=reference,
        output=tmp_csv,
        quiet=True,
    )
    # read csv: error matrix
    errorlist = None
    with open(tmp_csv) as csvfile:
        csvreader = csv.reader(csvfile, delimiter="	")
        num_rows = 0
        classified_classes = []
        for row in csvreader:
            if num_rows == 0:
                ref_classes = []
                for x, i in zip(row[1:-1], range(len(row[1:-1]))):
                    if x != "NULL":
                        ref_classes.append(x)
                    else:
                        ref_classes.append("Class_" + str(i))
            elif num_rows == 1:
                errorlist = [[int(x) for x in row[1:]]]
            elif num_rows > 1 and len(row) > 0:
                errorlist.append([int(x) for x in row[1:]])
            if num_rows > 0 and len(row) > 0:
                if row[0] != "NULL":
                    classified_classes.append(row[0])
                else:
                    classified_classes.append("Class_" + str(num_rows - 1))
            num_rows += 1
    classified_classes = classified_classes[:-1]

    errormatrix = np.matrix(errorlist)

    return errormatrix, classified_classes, ref_classes


def convert_output(
    classified_classes,
    ref_classes,
    confusionmatrix,
    overall_accuracy,
    user_accuracy,
    producer_accuracy,
    commission,
    omission,
    kappa,
    classification,
    refname,
):
    line1 = ["", ""]
    ref_header = list(ref_classes)
    ref_header.extend(["User Accuracy", "Commission Error"])
    line1.extend(ref_header)

    line2 = ["Classified Map", classified_classes[0]]
    line2.extend(confusionmatrix[0, :].tolist()[0])
    line2.extend(
        [user_accuracy[classified_classes[0]], commission[classified_classes[0]]]
    )

    if len(ref_classes) == 1:
        line3 = [classification, "", "", "", ""]
    else:
        line3 = [classification, classified_classes[1]]
        line3.extend(confusionmatrix[1, :].tolist()[0])
        line3.extend(
            [user_accuracy[classified_classes[1]], commission[classified_classes[1]]]
        )

    lines = [["", "", "Reference Map", refname], line1, line2, line3]
    for i in range(2, confusionmatrix.shape[0]):
        linei = ["", classified_classes[i]]
        linei.extend(confusionmatrix[i, :].tolist()[0])
        linei.extend(
            [user_accuracy[classified_classes[i]], commission[classified_classes[i]]]
        )
        lines.append(linei)
    producer_accuracy_list = [producer_accuracy[rc] for rc in ref_classes]
    # commission_list = [commission[rc] for rc in classified_classes]
    lineend1 = ["", "Producer Accuracy"]
    lineend1.extend(producer_accuracy_list)
    lineend1.extend(["Overall Accuracy", overall_accuracy])
    lineend2 = ["", "Omission Error"]
    omission_list = [omission[rc] for rc in ref_classes]
    lineend2.extend(omission_list)
    lineend2.extend(["Kappa coefficient", kappa])
    lines.append(lineend1)
    lines.append(lineend2)
    return lines


def main():

    global rm_files

    # parameters
    classification = options["classification"]
    csv_filename = options["csvfile"]
    descriptionflag = flags["d"]

    # reference as raster
    reference, refname = set_reference(descriptionflag)

    # descriptions
    if descriptionflag:
        print_descriptions()
        if not (classification and reference):
            return
    elif not (classification and reference):
        grass.fatal(
            _(
                "If <-d> is not set, <classification> and <raster_reference> or <vector_reference> with <column> must be set."
            )
        )

    # r.kappa to get the errormatrix
    errormatrix, classified_classes, ref_classes = get_r_kappa(
        classification, reference
    )

    # confusionmatrix
    confusionmatrix = errormatrix[:-1, :-1]
    if not flags["m"]:
        grass.message("\nConfusion matrix:\n%s" % str(confusionmatrix))

    # Overall accuracy
    diag = [errormatrix[i, i] for i in range(errormatrix.shape[0] - 1)]
    overall_accuracy = np.sum(diag) / errormatrix[-1, -1] * 100
    if not flags["m"]:
        grass.message("\nOverall accuracy: %f" % overall_accuracy)

    # User Accuracy and Commission
    user_accuracy = {}
    commission = {}
    for i in range(errormatrix.shape[0] - 1):
        classname = classified_classes[i]
        dg = diag[i]
        if dg == 0:
            user_accuracy[classname] = 0.0
        elif errormatrix[i, -1] == 0:
            user_accuracy[classname] = nan
        else:
            user_accuracy[classname] = dg / errormatrix[i, -1] * 100
        commission[classname] = 100 - user_accuracy[classname]

    # print  User Accuracy and Commission
    if not flags["m"]:
        grass.message("\nUser Accuracy: ")
    for key, item in user_accuracy.items():
        if not flags["m"]:
            grass.message("%s: %f" % (key, item))
    if not flags["m"]:
        grass.message("\nCommission error: ")
    for key, item in commission.items():
        if not flags["m"]:
            grass.message("%s: %f" % (key, item))

    # Producer Accuracy and Omission
    producer_accuracy = {}
    omission = {}
    # diag / unten
    for i in range(errormatrix.shape[0] - 1):
        classname = ref_classes[i]
        dg = diag[i]
        u = errormatrix[-1, i]
        if dg == 0:
            producer_accuracy[classname] = 0.0
        elif errormatrix[-1, i] == 0:
            producer_accuracy[classname] = nan
        else:
            producer_accuracy[classname] = dg / errormatrix[-1, i] * 100
        omission[classname] = 100 - producer_accuracy[classname]

    # print Producer Accuracy and Omission
    if not flags["m"]:
        grass.message("\nProducer Accuracy: ")
        for key, item in producer_accuracy.items():
            grass.message("%s: %f" % (key, item))
    if not flags["m"]:
        grass.message("\nOmission error: ")
        for key, item in omission.items():
            grass.message("%s: %f" % (key, item))

    # Kappa coefficient
    pc = 0
    for i in range(errormatrix.shape[0] - 1):
        pc += errormatrix[i, -1] * errormatrix[-1, i]
    pc *= 1 / (errormatrix[-1, -1] * errormatrix[-1, -1])
    kappa = (overall_accuracy / 100 - pc) / (1 - pc)
    if not flags["m"]:
        grass.message("\nKappa coefficient: %f" % kappa)

    # round values to two digits
    for item in user_accuracy.items():
        user_accuracy[item[0]] = round(item[1], 2)
    for item in producer_accuracy.items():
        producer_accuracy[item[0]] = round(item[1], 2)
    for item in commission.items():
        commission[item[0]] = round(item[1], 2)
    for item in omission.items():
        omission[item[0]] = round(item[1], 2)
    overall_accuracy = round(overall_accuracy, 2)
    kappa = round(kappa, 2)
    # in matrix style
    if flags["m"] or options["csvfile"]:
        lines = convert_output(
            classified_classes,
            ref_classes,
            confusionmatrix,
            overall_accuracy,
            user_accuracy,
            producer_accuracy,
            commission,
            omission,
            kappa,
            classification,
            refname,
        )

    # write csv file
    if csv_filename:
        with open(csv_filename, "w") as file:
            writer = csv.writer(file, lineterminator="\n")
            for line in lines:
                writer.writerow(line)
    if flags["m"]:
        for line in lines:
            print(line)

    if len(ref_classes) == 1:
        grass.warning(_("Only one class in reference dataset."))

    # cleanup
    if options["vector_reference"]:
        grass.run_command(
            "g.remove", type="raster", name=reference, flags="f", quiet=True
        )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
