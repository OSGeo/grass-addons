#!/usr/bin/env python
############################################################################
#
# MODULE:		r.mcda.topsis
# AUTHOR:		Gianluca Massei - Antonio Boggia
# PURPOSE:		Generate a MCDA map based on TOPSIS algorthm.
# 				Based on Hwang C. L. and Yoon K. Multiple Objective Decision
# 				Making Methods and Applications, A State-of-the-Art Survey .
# 				Springer - Verlag , 1981.
# COPYRIGHT:  c) 2015 Gianluca Massei, Antonio Boggia  and the GRASS
# 				Development Team. This program is free software under the
# 				GNU General PublicLicense (>=v2). Read the file COPYING
# 				that comes with GRASS for details.
#
#############################################################################

# %Module
# % description: Generates a MCDA map based on TOPSIS algorthm.
# % keyword: raster
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
# % key: preferences
# % type: string
# % key_desc: character
# % description: preference (gain,cost)
# % required: yes
# %end
# %option
# % key: weights
# % type: double
# % description: weights (w1,w2,...,wn)
# % multiple: yes
# % required: yes
# %end
# %option
# % key: topsismap
# % type: string
# % gisprompt: new_file,cell,output
# % description: Ranked raster map
# % required: yes
# %end


import sys
import grass.script as gscript
from time import time


def standardizedNormalizedMatrix(attributes, weights):  # step1 and step2
    criteria = []
    for criterion, weight in zip(attributes, weights):
        gscript.mapcalc(
            "critPow=pow(${criterion},2)", criterion=criterion, overwrite="True"
        )
        stats = gscript.parse_command("r.univar", map="critPow", flags="g")
        nameMap = "_%s" % criterion
        gscript.mapcalc(
            "${nameMap}=(${criterion}/sqrt(${sum}))*${weight}",
            nameMap=nameMap,
            criterion=criterion,
            sum=stats["sum"],
            weight=weight,
            overwrite="True",
        )
        criteria.append(nameMap)
    return criteria


def idealPoints(criteria, preference):  # step3
    idelaPointsList = []
    for c, p in zip(criteria, preference):
        stats = gscript.parse_command("r.univar", map=c, flags="g")
        if p == "gain":
            ip = float(stats["max"])
        elif p == "cost":
            ip = float(stats["min"])
        else:
            ip = -9999
            print("warning! %s doesn't compliant" % p)
        idelaPointsList.append(ip)
    return idelaPointsList


def worstPoints(criteria, preference):
    worstPointsList = []
    for c, p in zip(criteria, preference):
        stats = gscript.parse_command("r.univar", map=c, flags="g")
        if p == "gain":
            wp = float(stats["min"])
        elif p == "cost":
            wp = float(stats["max"])
        else:
            wp = -9999
            print("warning! %s doesn't compliant" % p)
        worstPointsList.append(wp)
    return worstPointsList


def idealPointDistance(idelaPointsList, criteria):  # step4a
    distance = []
    i = 0
    for c, ip in zip(criteria, idelaPointsList):
        mapname = "tmap_%s" % i
        gscript.mapcalc(
            "${mapname}=pow((${c}-${ip}),2)",
            mapname=mapname,
            c=c,
            ip=ip,
            overwrite="True",
        )
        distance.append(mapname)
        i = i + 1
    mapalgebra2 = "IdealPointDistance=sqrt(%s)" % ("+".join(distance))
    gscript.mapcalc(mapalgebra2, overwrite="True")
    gscript.run_command("g.remove", flags="f", type="raster", name=",".join(distance))
    return 0


def worstPointDistance(worstPointsList, criteria):  # step4b
    distance = []
    i = 0
    for c, wp in zip(criteria, worstPointsList):
        mapname = "tmap_%s" % i
        gscript.mapcalc(
            "${mapname}=pow((${c}-${wp}),2)",
            mapname=mapname,
            c=c,
            wp=wp,
            overwrite="True",
        )
        distance.append(mapname)
        i = i + 1
    mapalgebra2 = "WorstPointDistance=sqrt(%s)" % ("+".join(distance))
    gscript.mapcalc(mapalgebra2, overwrite="True")
    gscript.run_command("g.remove", flags="f", type="raster", name=",".join(distance))


def relativeCloseness(topsismap):  # step5
    gscript.mapcalc(
        "${topsismap}=WorstPointDistance/(WorstPointDistance+IdealPointDistance)",
        topsismap=topsismap,
        overwrite="True",
    )


def main():
    "main function for TOPSIS algorithm"
    # try:
    start = time()
    attributes = options["criteria"].split(",")
    preferences = options["preferences"].split(",")
    weights = options["weights"].split(",")
    topsismap = options["topsismap"]

    criteria = standardizedNormalizedMatrix(attributes, weights)
    idelaPointsList = idealPoints(criteria, preferences)
    worstPointsList = worstPoints(criteria, preferences)

    idealPointDistance(idelaPointsList, criteria)
    worstPointDistance(worstPointsList, criteria)
    relativeCloseness(topsismap)
    gscript.run_command("g.remove", flags="f", type="raster", name=",".join(criteria))
    gscript.run_command(
        "g.remove",
        flags="f",
        type="raster",
        name="IdealPointDistance,WorstPointDistance,critPow",
    )
    end = time()
    print("Time computing-> %.4f s" % (end - start))


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
