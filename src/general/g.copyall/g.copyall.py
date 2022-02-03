#!/usr/bin/env python

############################################################################
#
# MODULE:	    g.copyall
#
# AUTHOR(S):    Michael Barton (ASU)
#
# PURPOSE:	Copies all or a filtered subset of GRASS files of a selected type
#           from another mapset to the current working mapset
#
# COPYRIGHT:	(C) 2002-2012 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#
#############################################################################

# %Module
# % description: Copies all or a filtered subset of files of selected type from another mapset to the current working mapset.
# % keyword: copy
# % keyword: general
# % overwrite: yes
# %End
# %option G_OPT_M_MAPSET
# % key: mapset
# % description: Mapset to copy files from
# % required: yes
# %end
# %option
# % key: datatype
# % type: string
# % description: Choose type of GRASS data to copy
# % options: rast,vect,labels,rast3d,region,group
# % answer: rast
# % required: yes
# %end
# %option
# % key: filter
# % type: string
# % description: Search pattern to filter data files to copy
# % required : no
# %end
# %option
# % key: filter_type
# % type: string
# % description: Type of search pattern to use
# % options: select all, wildcards,regular expressions,extended regular expressions
# % answer: select all
# % required : no
# %end
# %option
# % key: output_prefix
# % type: string
# % description: Optional prefix for output raster maps
# % required : no
# %end
# % Flag
# % key: t
# % description: Update vector topology to match current GRASS version
# % End


import grass.script as grass


def main():
    #
    # define variables
    #

    overwrite = False
    mapset = options["mapset"]  # prefix for copied maps
    datatype = options["datatype"]  # prefix for copied maps
    filter = options["filter"]  # prefix for copied maps
    filter_type = options["filter_type"]  # prefix for copied maps
    prefix = options["output_prefix"]  # prefix for copied maps
    datalist = []  # list of GRASS data files to copy
    input = ""
    output = ""
    if grass.overwrite():
        overwrite = True

    if filter_type == "select all":
        filter = "*"

    filterflag = ""
    if filter_type == "regular expressions":
        filterflag = "r"
    if filter_type == "extended regular expressions":
        filterflag = "e"

    #
    # first run g.list to get list of maps to parse
    #
    l = grass.list_grouped(
        type=datatype, pattern=filter, check_search_path=True, flag=filterflag
    )
    if mapset not in l:
        grass.warning(
            _(
                "You do not have access to mapset %s. Run g.mapsets (under settings menu) to change mapset access"
            )
            % mapset
        )
        return

    datalist = l[mapset]

    #
    # then loop through the maps copying them with g.copy and optionally adding prefix
    #
    for input in datalist:
        if prefix:
            output = "%s_%s" % (prefix, input)
        else:
            output = input

        params = {datatype: "%s@%s,%s" % (input, mapset, output)}
        grass.run_command("g.copy", overwrite=overwrite, **params)

        if datatype == "vector" and flags["t"]:
            grass.run_command("v.build", map=output)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
