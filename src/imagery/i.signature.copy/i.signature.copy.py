#!/usr/bin/env python
#
############################################################################
#
# MODULE:	i.signature.copy
# AUTHOR(S):	Luca Delucchi
#
# PURPOSE:	Copies signature file from a group/subgroup
# COPYRIGHT:	(C) 2018 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

# %module
# % description: Copies signature file from a group/subgroup to another group/subgroup.
# % keyword: imagery
# % keyword: map management
# % keyword: copy
# % keyword: signature
# % keyword: group
# %end

# %option G_OPT_I_GROUP
# % key: igroup
# % description: Input group for signature file to copy
# % required : yes
# %end

# %option G_OPT_I_SUBGROUP
# % key: isubgroup
# % description: Input subgroup for signature file to copy
# % required : yes
# %end

# %option
# % key: isignature
# % type: string
# % gisprompt: old,sig,sigfile
# % label: Input signature file
# % description: The name of the input signature file to copy
# % required: yes
# %end

# %option
# % key: ogroup
# % type: string
# % gisprompt: old,group,group
# % label: Output group where copy the signature file
# % required : yes
# %end

# %option
# % key: osubgroup
# % type: string
# % gisprompt: old,subgroup,subgroup
# % description: Output subgroup where copy the signature file
# % required : yes
# %end

# %option
# % key: osignature
# % type: string
# % label: Output signature file
# % description: The name of the output signature file
# % required: no
# %end

import os
import sys
import shutil
import grass.script as grass


def main():
    igroup = options["igroup"]
    isub = options["isubgroup"]
    isign = options["isignature"]
    ogroup = options["ogroup"]
    osub = options["osubgroup"]
    osign = options["osignature"]

    # check if output signature is set
    if not osign:
        osign = isign

    gisenv = grass.gisenv()

    # try to split input group and mapset
    try:
        name, mapset = igroup.split("@", 1)
    except ValueError:
        name = igroup
        mapset = gisenv["MAPSET"]

    ipath = os.path.join(
        gisenv["GISDBASE"],
        gisenv["LOCATION_NAME"],
        mapset,
        name,
        "subgroup",
        isub,
        "sig",
        isign,
    )
    if not os.path.exists(ipath):
        grass.fatal(_("Signature file <{}> does not exist".format(ipath)))

    # try to split output group and mapset
    try:
        oname, omapset = ogroup.split("@", 1)
    except ValueError:
        oname = ogroup
        omapset = gisenv["MAPSET"]

    opath = os.path.join(
        gisenv["GISDBASE"],
        gisenv["LOCATION_NAME"],
        omapset,
        oname,
        "subgroup",
        osub,
        "sig",
    )
    if not os.path.exists(opath):
        grass.fatal(
            _(
                "<{pa}> does not exist, do group <{gr}> and "
                "subgroup <{su}> exist?".format(pa=ipath, gr=ogroup, su=osub)
            )
        )
    else:
        opath = os.path.join(opath, osign)
        if os.path.exists(opath) and not grass.overwrite():
            grass.fatal(
                _(
                    "ERROR: option <osignature>: <{}> exists. To "
                    "overwrite, use the --overwrite flag".format(osign)
                )
            )
    # try to copy the signature file otherwise return an error
    try:
        shutil.copy2(ipath, opath)
        return
    except:
        grass.fatal(_("ERROR: copying {inp} to {oup}".format(inp=ipath, oup=opath)))


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
