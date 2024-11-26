#!/usr/bin/env python3

########################################################################
#
# MODULE:       r.recode_attribute
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
# PURPOSE:      Recode raster to one or more new layers using an
#               attribute table (csv file) as input
#
# COPYRIGHT: (C) 2015-2024 by Paulo van Breugel
#            and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Recode raster based on the values in one or more columns in a csv file.
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

# %option G_OPT_F_SEP
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
import grass.script as gs

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range


def get_delimiter(separator_option):
    """
    Function to replace the description of the delimiter with the actual character
    """
    separator_mapping = {
        "comma": ",",
        "pipe": "|",
        "space": " ",
        "tab": "\t",
        "newline": "\n",
    }
    if separator_option in list(separator_mapping.keys()):
        return separator_mapping.get(separator_option, None)
    else:
        return separator_option


def main(options, flags):
    """
    Recodes a raster layer based on the values in one or more columns
    in a supplied csv file.
    """

    # input raster map and parameters
    inputmap = options["input"]
    outBase = options["output"]
    rules = options["rules"]
    separator = get_delimiter(options["separator"])
    outNames = outBase.split(",")
    lengthNames = len(outNames)
    flag_a = flags["a"]

    # Get attribute data
    try:
        myData = np.genfromtxt(rules, delimiter=separator, skip_header=1)
    except Exception as e:
        gs.fatal(_("Error loading data with delimiter '{}': {}".format(separator, e)))
    nmsData = np.genfromtxt(rules, delimiter=separator, names=True)
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

        cf = gs.find_file(name=nmOutput, element="cell", mapset=gs.gisenv()["MAPSET"])
        if cf["fullname"] != "":
            gs.fatal("The layer " + nmOutput + " already exist in this mapset")

        if flag_a:
            gs.run_command(
                "r.recode", input=inputmap, output=nmOutput, rules=tmpname, flags="a"
            )
        else:
            gs.run_command("r.recode", input=inputmap, output=nmOutput, rules=tmpname)
        os.close(fd1)
        os.remove(tmpname)


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
