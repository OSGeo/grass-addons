#!/usr/bin/env python


########################################################################
#
# MODULE:       r.recode_attribute
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
# PURPOSE:      Recode raster to one or more new layers using an
#               attribute table (csv file) as input
#
# COPYRIGHT: (C) 2015 Paulo van Breugel
#            http://ecodiv.org
#            http://pvanb.wordpress.com/
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Recode raster using attribute table (csv file) as input.
# % keyword: raster
# % keyword: recode
# %End

# %option
# % key: input
# % type: string
# % gisprompt: old,cell,raster
# % description: Input map
# % key_desc: name
# % required: yes
# % multiple: no
# %end

# %option
# % key: output
# % type: string
# % gisprompt: old,cell,raster
# % description: name(s) output layer(s)
# % key_desc: name
# % required: yes
# % multiple: no
# %end

# %option G_OPT_F_INPUT
# % key: rules
# % label: Full path to rules file
# % required: yes
# %end

# %flag:
# % key: a
# % description: Align the current region to the input raster map
# %end

# import libraries
import os
import sys
import numpy as np
import tempfile
import grass.script as grass

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

# main function
def main():

    # check if GISBASE is set
    if "GISBASE" not in os.environ:
        # return an error advice
        grass.fatal("You must be in GRASS GIS to run this program")

    # input raster map and parameters
    inputmap = options["input"]
    outBase = options["output"]
    rules = options["rules"]
    outNames = outBase.split(",")
    lengthNames = len(outNames)
    flag_a = flags["a"]

    # Get attribute data
    myData = np.genfromtxt(rules, delimiter=",", skip_header=1)
    nmsData = np.genfromtxt(rules, delimiter=",", names=True)
    dimData = myData.shape
    nmsData = nmsData.dtype.names

    # Create recode maps
    numVar = xrange(dimData[1] - 1)
    for x in numVar:
        y = x + 1
        myRecode = np.column_stack((myData[:, 0], myData[:, 0], myData[:, y]))

        fd1, tmpname = tempfile.mkstemp()
        np.savetxt(tmpname, myRecode, delimiter=":")

        if len(numVar) == lengthNames:
            nmOutput = outNames[x]
        else:
            nmOutput = outNames[0] + "_" + nmsData[y]

        cf = grass.find_file(
            name=nmOutput, element="cell", mapset=grass.gisenv()["MAPSET"]
        )
        if cf["fullname"] != "":
            grass.fatal("The layer " + nmOutput + " already exist in this mapset")

        if flag_a:
            grass.run_command(
                "r.recode", input=inputmap, output=nmOutput, rules=tmpname, flags="a"
            )
        else:
            grass.run_command(
                "r.recode", input=inputmap, output=nmOutput, rules=tmpname
            )
        os.close(fd1)
        os.remove(tmpname)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
