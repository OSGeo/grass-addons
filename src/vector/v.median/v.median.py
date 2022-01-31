#!/usr/bin/env python

############################################################################
#
# MODULE:       v.median
# AUTHOR(S):    Luca Delucchi, Fondazione E. Mach (Italy)
#
# PURPOSE:      Return the barycenter of a cloud of point
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################
# %module
# % description: Return the barycenter of a cloud of point.
# % keyword: vector
# %end
# %option
# % key: input
# % type: string
# % gisprompt: old,vector,vector
# % description: Name of vector map to pack up
# % key_desc: name
# % required : yes
# %end
# %option
# % key: output
# % type: string
# % gisprompt: new_file,file,output
# % description: Name for output file ('-' for standard output)
# % answer: -
# % required : no
# %end

import sys
import os
from grass.script.utils import try_remove
from grass.script import core as grass
from grass.exceptions import CalledModuleError
from numpy import transpose, genfromtxt, median


def point_med(filetmp):
    # function to return the median point, x and y
    point_list = transpose(genfromtxt(filetmp, delimiter="|", usecols=(0, 1)))
    return median(point_list[0]), median(point_list[1])


def main():
    # check if input file exists
    infile = options["input"]
    gfile = grass.find_file(infile, element="vector")
    if not gfile["name"]:
        grass.fatal(_("Vector map <%s> not found") % infile)
    # create tempfile and write ascii file of input
    temp_in = grass.tempfile()
    try:
        grass.run_command(
            "v.out.ascii", overwrite=True, input=gfile["name"], output=temp_in
        )
    except CalledModuleError:
        grass.fatal(_("Failed to export vector in a temporary file"))
    # x and y of median point
    medx, medy = point_med(temp_in)
    try_remove(temp_in)
    # prepare the output
    output = "%f|%f" % (medx, medy)
    map_name = options["output"]
    overwrite = os.getenv("GRASS_OVERWRITE")
    # if output is not set return to stdout
    if map_name == "-":
        grass.message(output)
    # else
    else:
        # output file
        goutfile = grass.find_file(name=map_name, element="vector", mapset=".")
        # output tempfile
        temp_out = grass.tempfile()
        file_out = open(temp_out, "w")
        file_out.write(output)
        file_out.close()
        # output file exists and not overwrite
        if goutfile["file"] and overwrite != "1":
            grass.fatal(_("Vector map <%s> already exists") % map_name)
        # output file exists and overwrite
        elif goutfile["file"] and overwrite == "1":
            grass.warning(
                _("Vector map <%s> already exists and will be overwritten") % map_name
            )
            grass.run_command(
                "v.in.ascii", overwrite=True, input=temp_out, output=map_name
            )
        # output file not exists
        else:
            grass.run_command("v.in.ascii", input=temp_out, output=map_name)
        try_remove(temp_out)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
