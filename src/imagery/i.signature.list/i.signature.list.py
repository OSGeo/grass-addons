#!/usr/bin/env python
#
############################################################################
#
# MODULE:	i.signature.list
# AUTHOR(S):	Luca Delucchi
#
# PURPOSE:	Lists signature file for a group/subgroup
# COPYRIGHT:	(C) 2018 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %module
# % description: Lists signature file of a group/subgroup.
# % keyword: imagery
# % keyword: map management
# % keyword: list
# % keyword: signature
# % keyword: group
# % keyword: search
# %end

# %flag
# % key: g
# % description: Return in shell script style, it require group and subgroup options
# %end

# %option G_OPT_I_GROUP
# % description: Group used to print signature file
# % required : no
# %end

# %option G_OPT_I_SUBGROUP
# % description: Subroup used to print signature file
# % required : no
# %end

import os
import sys
import grass.script as grass


def main():
    group = options["group"]
    sub = options["subgroup"]
    flagg = flags["g"]

    if flagg and not (group and sub):
        grass.fatal(_("'g' flag requires group and subgroup options"))

    gisenv = grass.gisenv()

    path = os.path.join(gisenv["GISDBASE"], gisenv["LOCATION_NAME"])

    if group:
        try:
            name, mapset = group.split("@", 1)
        except ValueError:
            name = group
            mapset = gisenv["MAPSET"]
        if not flagg:
            print("Group: {}".format(name))
        path = os.path.join(path, mapset, "group", name)
        if not os.path.exists(path):
            grass.fatal(
                _(
                    "No groups with name {na} in LOCATION {loc}, MAPSET"
                    " {ma}".format(na=name, loc=gisenv["LOCATION_NAME"], ma=mapset)
                )
            )
        if sub:
            path = os.path.join(path, "subgroup", sub, "sig")
            if not os.path.exists(path):
                grass.fatal(
                    _(
                        "No subgroups with name {na} in group "
                        "{gr}".format(na=sub, gr=name)
                    )
                )
            if not flagg:
                print("    Subgroup: {}".format(sub))
            for sig in os.listdir(path):
                if sig != "REF":
                    if flagg:
                        print(sig)
                    else:
                        print("        {}".format(sig))
        else:
            path = os.path.join(path, "subgroup")
            if not os.path.exists(path):
                grass.fatal(_("No subgroups for group {gr}".format(gr=name)))
            for di in os.listdir(path):
                print("    Subgroup: {}".format(di))
                for sig in os.listdir(os.path.join(path, di, "sig")):
                    if sig != "REF":
                        print("        {}".format(sig))
    else:
        path = os.path.join(path, gisenv["MAPSET"], "group")
        if not os.path.exists(path):
            grass.fatal(
                _(
                    "No groups in LOCATION {loc}, MAPSET "
                    "{ma}".format(loc=gisenv["LOCATION_NAME"], ma=gisenv["MAPSET"])
                )
            )
        for gr in os.listdir(path):
            print("Group: {}".format(gr))
            if not os.path.exists(os.path.join(path, gr, "subgroup")):
                grass.warning(_("No subgroups for group {gr}".format(gr=name)))
                continue
            for di in os.listdir(os.path.join(path, gr, "subgroup")):
                print("    Subgroup: {}".format(di))
                for sig in os.listdir(os.path.join(path, gr, "subgroup", di, "sig")):
                    if sig != "REF":
                        print("        {}".format(sig))

    return


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
