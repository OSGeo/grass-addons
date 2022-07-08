#!/usr/bin/env python
############################################################################
#
# MODULE:       r.mcda.ahp
# AUTHOR:       Gianluca Massei - Antonio Boggia
# PURPOSE:      Generate a raster map classified with  analytic hierarchy process (AHP) [Saaty, 1977 and Saaty & Vargas, 1991]
# COPYRIGHT:    c) 2010 Gianluca Massei, Antonio Boggia  and the GRASS
#                       Development Team. This program is free software under the
#                       GNU General PublicLicense (>=v2). Read the file COPYING
#                       that comes with GRASS for details.
#
#############################################################################


# %Module
# % description: Generates a raster map classified with analytic hierarchy process (AHP).
# % keyword: raster
# % keyword: Analytic Hierarchy Process (AHP)
# % keyword: Multi Criteria Decision Analysis (MCDA)
# %End
# %option
# % key: criteria
# % type: string
# % multiple: yes
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of criteria raster maps
# % required: yes
# %end
# %option
# % key: pairwise
# % type: string
# % gisprompt: old,file,input
# % description: Pairwise comparison matrix
# % required: yes
# %end
# %option
# % key: output
# % type: string
# % gisprompt: new_file,cell,output
# % description: output classified raster map
# % required: yes
# %end
# %flag
# % key:k
# % description:build a void pairwise comparison matrix and exit (no yet implemented)
# %end

import sys
import grass.script as grass
import numpy as np
import warnings


def calculateWeight(pairwise):
    "Define vector of weight based on eigenvector and eigenvalues"
    pairwise = np.genfromtxt(pairwise, delimiter=",")
    warnings.simplefilter("ignore", np.ComplexWarning)
    eigenvalues, eigenvector = np.linalg.eig(pairwise)
    maxindex = np.argmax(eigenvalues)
    eigenvalues = np.float32(eigenvalues)
    eigenvector = np.float32(eigenvector)
    weight = eigenvector[
        :, maxindex
    ]  # extract vector from eigenvector with max vaue in eigenvalues
    weight.tolist()  # convert array(numpy)  to vector
    weight = [w / sum(weight) for w in weight]
    return weight, eigenvalues, eigenvector


def calculateMap(criteria, weight, outputMap):
    "Parser a formula for mapcalc and run grass.mapcalc"
    formula = ""
    for i in range(len(criteria) - 1):
        formula += "%s*%s + " % (criteria[i], weight[i])
    formula += "%s*%s " % (criteria[len(criteria) - 1], weight[len(criteria) - 1])
    grass.mapcalc(outputMap + "=" + formula)
    return 0


def Consistency(weight, eigenvalues):
    "Calculete Consistency index in accord with Saaty (1977)"
    RI = [
        0.00,
        0.00,
        0.00,
        0.52,
        0.90,
        1.12,
        1.24,
        1.32,
        1.41,
    ]  # order of matrix: 0,1,2,3,4,5,6,7,8
    order = len(weight)
    CI = (np.max(eigenvalues) - order) / (order - 1)
    return CI / RI[order - 1]


def ReportLog(eigenvalues, eigenvector, weight, consistency):
    "Make a log file"
    log = open("log.txt", "w")
    log.write("eigenvalues:\n%s" % eigenvalues)
    log.write("\neigenvector:\n%s" % eigenvector)
    log.write("\nweight:\n%s" % weight)
    log.write("\nconsistency:\n%s" % consistency)
    log.close()
    return 0


def main():
    "main"
    criteria = options["criteria"].split(",")
    pairwise = options["pairwise"]
    outputMap = options["output"]
    gregion = grass.region()
    nrows = gregion["rows"]
    ncols = gregion["cols"]
    ewres = int(gregion["ewres"])
    nsres = int(gregion["nsres"])
    weight, eigenvalues, eigenvector = calculateWeight(pairwise)
    calculateMap(criteria, weight, outputMap)
    consistency = Consistency(weight, eigenvalues)
    ReportLog(eigenvalues, eigenvector, weight, consistency)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
