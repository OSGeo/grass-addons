#!/usr/bin/env python
############################################################################
#
# MODULE:       r.mcda.output
# AUTHOR:       Gianluca Massei - Antonio Boggia
# PURPOSE:      Export criteria raster maps and decision raster map in a *.isf
#               file for dominance rough set approach analysis (DRSA)
#               Dominance Rough Set Analysis (e.g. 4eMka2,JAMM, jMAF).
# COPYRIGHT:    c) 2010 Gianluca Massei, Antonio Boggia  and the GRASS
#               Development Team. This program is free software under the
#               GNU General PublicLicense (>=v2). Read the file COPYING
#               that comes with GRASS for details.
#
#############################################################################

# %Module
# % description: Exports criteria raster maps and decision raster map in a *.isf file (e.g. 4eMka2, jMAF) for dominance rough set approach analysis.
# % keyword: raster
# % keyword: Dominance Rough Set Approach
# % keyword: Multi Criteria Decision Analysis (MCDA)
# %End
# %option
# % key: attributes
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
# % description: gain,cost,none
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
# % key: output
# % type: string
# % gisprompt: new_file,file,output
# % key_desc: name
# % description: Name for output file (*.isf file, Information System)
# % answer:infosys.isf
# % required: yes
# %end


import sys

##from grass.script import core as grass
import grass.script as grass


def main():
    attributes = options["attributes"].split(",")
    preferences = options["preferences"].split(",")
    decision = options["decision"]
    output = options["output"]

    gregion = grass.region()
    nrows = gregion["rows"]
    ncols = gregion["cols"]
    ewres = int(gregion["ewres"])
    nsres = int(gregion["nsres"])
    print(nrows, ncols, ewres, nsres)

    outf = open(output, "w")
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

    print("rows:%d - col:%d" % (len(MATRIX), len(MATRIX[0])))
    for r in range(len(MATRIX)):
        for c in range(len(MATRIX[0])):
            outf.write("%s " % str(MATRIX[r][c]))
        outf.write("\n")

    outf.write("**END")
    outf.close()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
