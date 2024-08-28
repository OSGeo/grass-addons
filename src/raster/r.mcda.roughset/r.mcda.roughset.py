#!/usr/bin/env python
############################################################################
#
# MODULE:	   r.mcda.roughset
# AUTHOR:	   Gianluca Massei - Antonio Boggia
# PURPOSE:	  Generate a MCDA map from several criteria maps using Dominance Rough Set Approach - DRSA
# 					   (DOMLEM algorithm proposed by  (S. Greco, B. Matarazzo, R. Slowinski)
# COPYRIGHT:  c) 2010 Gianluca Massei, Antonio Boggia  and the GRASS
# 					   Development Team. This program is free software under the
# 					   GNU General PublicLicense (>=v2). Read the file COPYING
# 					   that comes with GRASS for details.
#
#############################################################################

# %Module
# % description: Generates a MCDA map from several criteria maps using Dominance Rough Set Approach.
# % keyword: raster
# % keyword: Dominance Rough Set Approach
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
# % description: gain,cost
# % required: yes
# %end
# %option
# % key: decision
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of decision raster map
# % required: yes
# %end
# %option
# % key: outputMap
# % type: string
# % gisprompt: new_file,cell,output
# % description: Output classified raster map
# % required: yes
# %end
# %option
# % key: outputTxt
# % type: string
# % gisprompt: new_file,file,output
# % key_desc: name
# % description: Name for output files (base for *.isf  and *.rls files)
# % answer:infosys
# % required: yes
# %end
# %flag
# % key: l
# % description: do not remove single rules in vector format
# %end
# %flag
# % key: n
# % description: compute null value as zero
# %end

import sys
import copy
import numpy as np
from time import time, ctime
import grass.script as grass
import grass.script.array as garray
from functools import reduce


def BuildFileISF(attributes, preferences, decision, outputMap, outputTxt):
    outputTxt = outputTxt + ".isf"
    outf = open(outputTxt, "w")
    outf.write("**ATTRIBUTES\n")
    for i in range(len(attributes)):
        outf.write("+ %s: (continuous)\n" % attributes[i])
    outf.write("+ %s: [" % decision)
    value = []
    value = grass.read_command("r.describe", flags="1n", map=decision)
    v = value.split()

    for i in range(len(v) - 1):
        outf.write("%s, " % str(v[i]))
    outf.write("%s]\n" % str(v[len(v) - 1]))
    outf.write("decision: %s\n" % decision)

    outf.write("\n**PREFERENCES\n")
    for i in range(len(attributes)):
        if preferences[i] == "":
            preferences[i] = "none"
        outf.write("%s: %s\n" % (attributes[i], preferences[i]))
    outf.write("%s: gain\n" % decision)

    if flags["n"]:
        for i in range(len(attributes)):
            print("%s - convert null to 0" % str(attributes[i]))
            grass.run_command("r.null", map=attributes[i], null=0)

    outf.write("\n**EXAMPLES\n")
    examples = []
    MATRIX = []

    for i in range(len(attributes)):
        grass.mapcalc(
            "rast=if(isnull(${decision})==0,${attribute},null())",
            rast="rast",
            decision=decision,
            attribute=attributes[i],
        )
        tmp = grass.read_command("r.stats", flags="1n", nv="?", input="rast")
        example = tmp.split()
        examples.append(example)
    tmp = grass.read_command("r.stats", flags="1n", nv="?", input=decision)
    example = tmp.split()
    examples.append(example)

    MATRIX = list(map(list, list(zip(*examples))))
    MATRIX = [r for r in MATRIX if "?" not in r]  # remove all rows with almost one "?"
    MATRIX = [
        list(i) for i in set(tuple(j) for j in MATRIX)
    ]  # remove duplicate example

    for r in range(len(MATRIX)):
        for c in range(len(MATRIX[0])):
            outf.write("%s " % (MATRIX[r][c]))
        # 			outf.write("%s " % round(float(MATRIX[r][c]), 2))
        outf.write("\n")

    outf.write("**END")
    outf.close()
    return outputTxt


def collect_attributes(data):
    "Collects the values of header files isf, puts them in an array of dictionaries"
    header = []
    attribute = dict()
    j = 0
    start = data.index(["**ATTRIBUTES"]) + 1
    end = data.index(["**PREFERENCES"]) - 1
    for r in range(start, end):
        attribute = {"name": data[r][1].strip("+:")}
        header.append(attribute)
    decision = data[end - 1][1]
    end = data.index(["**EXAMPLES"])

    start = data.index(["**PREFERENCES"]) + 1
    for r in header:
        r["preference"] = data[start + j][1]
        j = j + 1
    return header


def collect_examples(data):
    "Collect examples values and put them in a matrix (list of lists)"

    matrix = []
    data = [r for r in data if "?" not in r]  # filter objects with " ?"
    # 	data=[data.remove(r) for r in data if data.count(r)>1]
    start = data.index(["**EXAMPLES"]) + 1
    end = data.index(["**END"])
    for i in range(start, end):
        data[i] = list(map(float, data[i]))
        matrix.append(data[i])
    i = 1
    for r in matrix:
        r.insert(0, str(i))
        i = i + 1
    ##	matrix=[list(i) for i in set(tuple(j) for j in matrix)] #remove duplicate example
    return matrix


def FileToInfoSystem(isf):
    "Read *.isf file and copy it's values in Infosystem dictionary"
    data = []
    try:
        infile = open(isf, "r")
        rows = infile.readlines()
        for line in rows:
            line = line.split()
            if len(line) > 0:
                data.append(line)
        infile.close()
        infosystem = {
            "attributes": collect_attributes(data),
            "examples": collect_examples(data),
        }
    except TypeError:
        print(
            "\n\n Computing error or input file %s is not readeable. Exiting gracefully"
            % isf
        )
        sys.exit(0)

    return infosystem


def UnionOfClasses(infosystem):
    "Find upward and downward union for all classes and put it in a dictionary"
    DecisionClass = []
    AllClasses = []
    matrix = infosystem["examples"]
    for r in matrix:
        DecisionClass.append(int(r[-1]))
    DecisionClass = list(set(DecisionClass))
    for c in range(len(DecisionClass)):
        tmplist = [r for r in matrix if int(r[-1]) == DecisionClass[c]]
        AllClasses.append(tmplist)

    return AllClasses


def DownwardUnionsOfClasses(infosystem):
    "For each decision class, downward union corresponding to a decision class\
    is composed of this class and all worse classes (<=)"

    DownwardUnionClass = []
    DecisionClass = []
    matrix = infosystem["examples"]
    for r in matrix:
        DecisionClass.append(int(r[-1]))
    DecisionClass = list(set(DecisionClass))
    for c in DecisionClass:
        tmplist = [r for r in matrix if int(r[-1]) <= c]
        DownwardUnionClass.append(tmplist)
        # label=[row[0] for row in tmplist]
    return DownwardUnionClass


def UpwardUnionsOfClasses(infosystem):
    "For each decision class, upward union corresponding to a decision class \
    is composed of this class and all better classes.(>=)"

    UpwardUnionClass = []
    DecisionClass = []
    matrix = infosystem["examples"]
    for r in matrix:
        DecisionClass.append(int(r[-1]))
    DecisionClass = list(set(DecisionClass))
    for c in DecisionClass:
        tmplist = [r for r in matrix if int(r[-1]) >= c]
        UpwardUnionClass.append(tmplist)
        # label=[row[0] for row in tmplist]
    return UpwardUnionClass


###############################
def is_better(r1, r2, preference):
    "Check if r1 is better than r2"
    return all(
        ((x >= y and p == "gain") or (x <= y and p == "cost"))
        for x, y, p in zip(r1, r2, preference)
    )


def is_worst(r1, r2, preference):
    "Check if r1 is worst than r2"
    return all(
        ((x <= y and p == "gain") or (x >= y and p == "cost"))
        for x, y, p in zip(r1, r2, preference)
    )


#################################


def DominatingSet(infosystem):
    "Find P-dominating set"
    matrix = infosystem["examples"]
    preference = [s["preference"] for s in infosystem["attributes"]]
    Dominating = []
    for row in matrix:
        examples = [r for r in matrix if is_better(r[1:-1], row[1:-1], preference)]
        Dominating.append(
            {
                "object": row[0],
                "dominance": [i[0] for i in examples],
                "examples": examples,
            }
        )
    ##	for dom in Dominating:
    ##		print  dom['dominance'] ,' dominating ', dom['object']
    return Dominating


def DominatedSet(infosystem):
    "Find P-Dominated set"
    matrix = infosystem["examples"]
    preference = [s["preference"] for s in infosystem["attributes"]]
    Dominated = []
    for row in matrix:
        examples = [r for r in matrix if is_worst(r[1:-1], row[1:-1], preference[:-1])]
        Dominated.append(
            {
                "object": row[0],
                "dominance": [i[0] for i in examples],
                "examples": examples,
            }
        )
    ##	for dom in Dominated:
    ##		print  dom['dominance'] ,' is dominated by ', dom['object']
    return Dominated


def LowerApproximation(UnionClasses, Dom):
    "Find Lower approximation and return a dictionaries list"
    c = 1
    LowApprox = []
    single = dict()
    for union in UnionClasses:
        tmp = []
        UClass = set([row[0] for row in union])
        for d in Dom:
            if UClass.issuperset(
                set(d["dominance"])
            ):  # if Union class is a superse of dominating/dominated set, =>single Loer approx.
                tmp.append(d["object"])
        single = {"class": c, "objects": tmp}  # dictionary for lower approximation  --
        LowApprox.append(single)  # insert all Lower approximation in a list
        c += 1
    return LowApprox


def UpperApproximation(UnionClasses, Dom):
    "Find Upper approximation and return a dictionaries list"
    c = 1
    UppApprox = []
    single = dict()
    for union in UnionClasses:
        UnClass = [row[0] for row in union]  # single union class
        s = []
        for d in Dom:
            if len(set(d["dominance"]) & set(UnClass)) > 0:
                s.append(d["object"])
        # 			   print set(s)
        single = {"class": c, "objects": list(set(s))}
        UppApprox.append(single)
        c += 1

    return UppApprox


def Boundaries(UppApprox, LowApprox):
    "Find Boundaries like doubtful regions"
    Boundary = []
    single = dict()

    for i in range(len(UppApprox)):
        single = {
            "class": i,
            "objects": list(
                set(UppApprox[i]["objects"]) - set(LowApprox[i]["objects"])
            ),
        }
        Boundary.append(single)

    return Boundary


def AccuracyOfApproximation(UppApprox, LowApprox):
    "Define the accuracy of approximation of Upward and downward approximation class"
    return len(LowApprox) / len(UppApprox)


def QualityOfQpproximation(DownwardBoundary, infosystem):
    "Defines the quality of approximation of the partition Cl or, briefly, the quality of sorting"
    UnionBoundary = set()
    U = set([i[0] for i in infosystem["examples"]])
    for b in DownwardBoundary:
        UnionBoundary = set(UnionBoundary) | set(b["objects"])
    return float(len(U - UnionBoundary)) / float(len(U))


def FindObjectCovered(rules, selected):
    "Find objects covered by a single rule and return\
    all related examples covered"
    obj = []
    examples = []

    for rule in rules:
        examples.append(rule["objectsCovered"])

    if len(examples) > 0:
        examples = reduce(
            set.intersection, list(map(set, examples))
        )  # functional approach: intersect all lists if example is not empty
        examples = list(set(examples) & set([r[0] for r in selected]))
    return examples  # all examples covered from a single rule


def Evaluate(elem, rules, G, selected, infosystem):
    "Calcolate first and second evaluate index, according with original DOMLEM Algorithm"
    tmpRules = copy.deepcopy(rules)
    tmpElem = copy.deepcopy(elem)
    tmpRules.append(tmpElem)
    Object = []
    Object = FindObjectCovered(tmpRules, selected)
    if (float(len(Object))) > 0:
        firstEvaluate = float(len(set(G) & set(Object))) / float(len(Object))
        secondEvaluate = float(len(set(G) & set(Object)))
    else:
        firstEvaluate = 0
        secondEvaluate = 0

    return firstEvaluate, secondEvaluate


def FindBestCondition(best, elem, rules, selected, G, infosystem):
    "Choose the best condition"

    firstElem, secondElem = Evaluate(elem, rules, G, selected, infosystem)
    firstBest, secondBest = Evaluate(best, rules, G, selected, infosystem)

    if (firstElem > firstBest) or (firstElem == firstBest and secondElem >= secondBest):
        best = copy.deepcopy(elem)
    else:
        best = best

    return best


def Type_one_rule(c, e, preference, matrix):
    elem = {
        "criterion": c,
        "condition": e,
        "sign": preference[c - 1],
        "class": "",
        "objectsCovered": [
            r[0]
            for r in matrix
            if (
                ((r[c] >= e) and (preference[c - 1] == "gain"))
                or ((r[c] <= e) and (preference[c - 1] == "cost"))
            )
        ],
        "label": "",
    }
    return elem


def Type_three_rule(c, e, preference, matrix):
    elem = {
        "criterion": c,
        "condition": e,
        "sign": preference[c - 1],
        "class": "",
        "objectsCovered": [
            r[0]
            for r in matrix
            if (
                ((r[c] <= e) and (preference[c - 1] == "gain"))
                or ((r[c] >= e) and (preference[c - 1] == "cost"))
            )
        ],
        "label": "",
    }
    return elem


def Find_rules(B, infosystem, type_rule):
    "Search rule from a family of lower approximation of upward unions \
    of decision classes"
    start = time()
    matrix = copy.deepcopy(infosystem["examples"])
    criteria_num = len(infosystem["attributes"])
    criteria = [r[1:-1] for r in matrix]
    preference = [
        s["preference"] for s in infosystem["attributes"]
    ]  # extract preference label
    num_rules = 0  # total rules number for each lower approximation
    G = copy.deepcopy(B)  # a set of objects from the given approximation
    E = []  # a set  of rules covering set B (is a list of dictionary)
    all_obj_cov_by_rules = []  # all objects covered by all rules in E
    selected = copy.deepcopy(
        matrix
    )  # storage reduct matrix by single elementary condition
    while len(G) != 0:
        rules = []  # starting comples (single rule built from elementary conditions  )
        S = copy.deepcopy(G)  # set of objects currently covered by rule
        control = 0
        while len(rules) == 0 or set(obj_cov_by_rules).issubset(B) is False:
            obj_cov_by_rules = []  # set covered by rules
            best = {
                "criterion": "",
                "condition": "",
                "sign": "",
                "class": "",
                "objectsCovered": "",
                "label": "",
                "type": "",
            }  # best candidate for elementary condition - start as empty
            for c in range(1, criteria_num):
                Cond = [
                    r[c] for r in selected if r[0] in S
                ]  # for each positive object from S create an elementary condition
                for e in Cond:
                    if type_rule == "one":
                        elem = Type_one_rule(c, e, preference, matrix)
                    elif type_rule == "three":
                        elem = Type_three_rule(c, e, preference, matrix)
                    else:
                        elem = {
                            "criterion": "",
                            "condition": "",
                            "sign": "",
                            "class": "",
                            "objectsCovered": "",
                            "label": "",
                            "type": "",
                        }
                    best = FindBestCondition(best, elem, rules, selected, G, infosystem)
            if best not in rules:
                rules.append(best)  # add the best condition to the complex

            for r in rules:
                obj_cov_by_rules.append(r["objectsCovered"])
            obj_cov_by_rules = list(
                (reduce(set.intersection, list(map(set, obj_cov_by_rules))))
            )  # reduce():Apply function of two arguments cumulatively to the items of iterable, from left to right, so as to reduce the iterable to a single value.

            S = list(set(S) & set(best["objectsCovered"]))
            control += 1

        # 		rules=CheckMinimalCondition (rules,B,matrix)

        if rules not in E:
            E.append(rules)  # add the induced rule
            num_rules += 1
        all_obj_cov_by_rules = list(set(all_obj_cov_by_rules) | set(obj_cov_by_rules))

        G = list(
            set(B) - set(all_obj_cov_by_rules)
        )  # remove example coverred by all finded rule -- this operation is a set difference
        selected = [
            o for o in selected if not o[0] in all_obj_cov_by_rules
        ]  # reduct matrix, remove object coverred by all finded rule
        num_rules += 1

    return E


def Domlem(Lu, Ld, infosystem):
    "DOMLEM algoritm \
    (An algorithm for induction of decision rules consistent with the dominance\
    principle - Greco S., Matarazzo, B., Slowinski R., Stefanowski J.)"
    attributes = infosystem["attributes"]

    RULES = []

    ##  *** AT MOST {<= Class} - Type 3 rules ***"
    for b in Ld[:-1]:
        B = b["objects"]
        E = Find_rules(B, infosystem, "three")
        for e in E:
            for i in e:
                i["class"] = b["class"]
                i["label"] = attributes[i["criterion"] - 1]["name"]
                i["type"] = "at_most"
                if attributes[i["criterion"] - 1]["preference"] == "gain":
                    i["sign"] = "<="
                else:
                    i["sign"] = ">="
            RULES.append(e)

    ## *** AT LEAST {>= Class} - Type 1 rules *** "
    for a in Lu[1:]:
        B = a["objects"]
        E = Find_rules(B, infosystem, "one")
        for e in E:
            for i in e:
                i["class"] = a["class"]
                i["label"] = attributes[i["criterion"] - 1]["name"]
                i["type"] = "at_least"
                if attributes[i["criterion"] - 1]["preference"] == "gain":
                    i["sign"] = ">="
                else:
                    i["sign"] = "<="
            RULES.append(e)

    return RULES


def Print_rules(RULES, outputTxt):
    "Print rls output file"
    i = 1
    outfile = open(outputTxt + ".rls", "w")
    outfile.write("[RULES]\n")

    for R in RULES:
        outfile.write(
            "%d: " % i,
        )
        for e in R:
            outfile.write("( %s %s %.3f )" % (e["label"], e["sign"], e["condition"]))
        outfile.write("=> ( class %s , %s )\n" % (e["type"], e["class"]))
        i += 1
    outfile.close()
    return 0


def Parser_mapcalc(RULES, outputMap):
    "Parser to build a formula to be included  in mapcalc command"
    i = 1
    category = []
    maps = []
    stringa = []

    for R in RULES:
        formula = "if("
        for e in R[:-1]:  # build a mapcalc formula
            formula += "(%s %s %.4f ) && " % (e["label"], e["sign"], e["condition"])
        formula += "(%s %s %.4f ),%d,null())" % (
            R[-1]["label"],
            R[-1]["sign"],
            R[-1]["condition"],
            i,
        )
        mappa = "r%d_%s_%d" % (
            i,
            R[0]["type"],
            R[0]["class"],
        )  # build map name for mapcalc output
        category.append(
            {"id": i, "type": R[0]["type"], "class": R[0]["class"]}
        )  # extract category name
        maps.append(mappa)  # extract maps name
        grass.mapcalc(mappa + "=" + formula)
        i += 1
    mapstring = ",".join(maps)

    # make one layer for each label rule
    labels = ["_".join(m.split("_")[1:]) for m in maps]
    labels = list(set(labels))
    for l in labels:
        print("mapping %s rule" % str(l))
        map_synth = []
        for m in maps:
            if l == "_".join(m.split("_")[1:]):
                map_synth.append(m)
        if len(map_synth) > 1:
            grass.run_command(
                "r.patch", overwrite="True", input=(",".join(map_synth)), output=l
            )
        else:
            grass.run_command("g.copy", raster=(str(map_synth), l))
        print("__", str(map_synth), l)
        grass.run_command(
            "r.to.vect", overwrite="True", flags="s", input=l, output=l, feature="area"
        )
        grass.run_command("v.db.addcol", map=l, columns="rule varchar(25)")
        grass.run_command("v.db.update", map=l, column="rule", value=l)
        grass.run_command("v.db.update", map=l, column="label", value=l)
    mapslabels = ",".join(labels)

    if len(maps) > 1:
        grass.run_command(
            "v.patch", overwrite="True", flags="e", input=mapslabels, output=outputMap
        )
    else:
        grass.run_command("g.copy", vector=(mapslabels, outputMap))

    if not flags["l"]:
        grass.run_command("g.remove", flags="f", type="raster", name=mapstring)
        grass.run_command("g.remove", flags="f", type="vector", name=mapstring)

    return 0


def main():
    "main function for DOMLEM algorithm"
    # try:
    start = time()
    attributes = options["criteria"].split(",")
    preferences = options["preferences"].split(",")
    decision = options["decision"]
    outputMap = options["outputMap"]
    outputTxt = options["outputTxt"]
    out = BuildFileISF(attributes, preferences, decision, outputMap, outputTxt)
    infosystem = FileToInfoSystem(out)

    UnionOfClasses(infosystem)
    DownwardUnionClass = DownwardUnionsOfClasses(infosystem)
    UpwardUnionClass = UpwardUnionsOfClasses(infosystem)
    Dominating = DominatingSet(infosystem)
    Dominated = DominatedSet(infosystem)
    ##	upward union class
    print("elaborate upward union")
    Lu = LowerApproximation(
        UpwardUnionClass, Dominating
    )  # lower approximation of upward union for type 1 rules
    Uu = UpperApproximation(
        UpwardUnionClass, Dominated
    )  # upper approximation of upward union
    UpwardBoundary = Boundaries(Uu, Lu)
    ##	downward union class
    print("elaborate downward union")
    Ld = LowerApproximation(
        DownwardUnionClass, Dominated
    )  # lower approximation of  downward union for type 3 rules
    Ud = UpperApproximation(
        DownwardUnionClass, Dominating
    )  # upper approximation of  downward union
    DownwardBoundary = Boundaries(Ud, Ld)
    QualityOfQpproximation(DownwardBoundary, infosystem)
    print("RULES extraction (*)")
    RULES = Domlem(Lu, Ld, infosystem)
    Parser_mapcalc(RULES, outputMap)
    Print_rules(RULES, outputTxt)
    end = time()
    print("Time computing-> %.4f s" % (end - start))
    return 0
    # except:
    # print "ERROR! Rules does not generated!"
    # sys.exit()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
