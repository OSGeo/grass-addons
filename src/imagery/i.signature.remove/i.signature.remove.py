#!/usr/bin/env python
#
############################################################################
#
# MODULE:	i.signature.remove
# AUTHOR(S):	Luca Delucchi
#
# PURPOSE:	Removes signature file from a group/subgroup
# COPYRIGHT:	(C) 2018 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %module
# % description: Removes signature file in a group/subgroup.
# % keyword: imagery
# % keyword: map management
# % keyword: remove
# % keyword: signature
# % keyword: group
# %end

# %flag
# % key: f
# % description: Force removal (required for actual deletion of files)
# %end

# %option G_OPT_I_GROUP
# % description: Group used to print signature file
# % required : no
# %end

# %option G_OPT_I_SUBGROUP
# % description: Subroup used to print signature file
# % required : no
# %end

# %option
# % key: signature
# % type: string
# % gisprompt: old,sig,sigfile
# % label: Input signature file
# % description: The name of the input signature file to copy
# % multiple: yes
# % required: yes
# %end

import os
import sys
import grass.script as grass


def main():
    group = options["group"]
    sub = options["subgroup"]
    signs = options["signature"]
    rem = flags["f"]

    gisenv = grass.gisenv()

    try:
        name, mapset = group.split("@", 1)
    except ValueError:
        name = group
        mapset = gisenv["MAPSET"]

    output_str = "The following signature files would be deleted:\n"
    for sign in signs.split(","):
        path = os.path.join(gisenv["GISDBASE"], gisenv["LOCATION_NAME"])
        path = os.path.join(path, mapset, "group", name, "subgroup", sub, "sig", sign)
        if not os.path.exists(path):
            grass.fatal(
                _(
                    "Signature file <{pa}> does not exist for group "
                    "<{gr}> and subgroup <{su}>".format(pa=sign, gr=group, su=sub)
                )
            )
        if rem:
            try:
                os.remove(path)
                print(_("Removing signature file <{si}>".format(si=sign)))
            except:
                grass.warning(
                    _("Signature file <{pa}> was not " "removed".format(pa=sign))
                )
        else:
            output_str += "{gr}/{su}/{sig}\n".format(gr=group, su=sub, sig=sign)

    if not rem:
        print(output_str.rstrip())
        grass.warning(
            _(
                "Nothing removed. You must use the force flag (-f) "
                "to actually remove them. Exiting."
            )
        )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
