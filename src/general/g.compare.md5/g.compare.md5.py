#!/usr/bin/env python

################################################################################
#
# MODULE:       g.md5sum.py
#
# AUTHOR(S):    Luca Delucchi <lucadeluge@gmail.com>
#
# PURPOSE:      Check if two GRASS maps are the same
#
# COPYRIGHT:    (c) 2012-2020 by Luca Delucchi and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
################################################################################

# %module
# % description: Checks if two GRASS GIS maps are identical.
# % keyword: general
# % keyword: map management
# % keyword: list
# %end
# %flag
# % key: g
# % description: Return output in shell script style (0 fail, 1 success)
# %end
# %flag
# % key: c
# % description: Does not consider the color table for raster
# %end
# %flag
# % key: t
# % description: Does not consider the topology for vector
# %end
# %option
# % key: ainput
# % type: string
# % gisprompt: old,file,file
# % description: Name of first map to check
# % key_desc: name
# % required : yes
# %end
# %option
# % key: binput
# % type: string
# % gisprompt: old,file,file
# % description: Name of second map to check
# % required : yes
# %end
# %option G_OPT_M_DATATYPE
# % key: type
# % options: raster,vector
# % answer: raster
# %end

import os
import sys
import hashlib
import grass.script as grass


def md5(fileName, excludeLine="", includeLine=""):
    """Compute md5 hash of the specified file"""
    m = hashlib.md5()
    try:
        fd = open(fileName, "rb")
    except IOError:
        print("Unable to open the file in read mode")
        return
    content = fd.readlines()
    fd.close()
    for eachLine in content:
        if excludeLine and eachLine.startswith(excludeLine):
            continue
        m.update(eachLine)
    m.update(includeLine.encode("utf-8"))
    return m.hexdigest()


def checkfile(name, formatt, shell):
    """Check if the input file exists"""
    if formatt == "raster":
        typ = "Raster"
        inp = grass.find_file(name)
    elif formatt == "vector":
        typ = "Vector"
        inp = grass.find_file(name, formatt)
    if inp["name"] == "":
        if shell:
            grass.message(0)
            return
        else:
            grass.fatal(_("%s %s does not exists" % (typ, name)))
    else:
        return inp


def checkmd5(a, b, shell):
    """Check if md5 is the same for both files"""
    # check if the files exist and if the user have permission to read them
    if os.path.exists(a) and os.path.exists(b):
        if not os.access(a, os.R_OK):
            if shell:
                grass.message(0)
                return
            else:
                grass.fatal(_("You have no permission to read %s file" % a))
        if not os.access(b, os.R_OK):
            if shell:
                grass.message(0)
                return
            else:
                grass.fatal(_("You have no permission to read %s file" % b))
        # calculate the md5
        amd5 = md5(a)
        bmd5 = md5(b)
        # check if md5 is the same
        if amd5 == bmd5:
            return 1
        else:
            return 0
    # if both files doesn't exist this is good
    elif not os.path.exists(a) and not os.path.exists(b):
        return 1
    # one file exists and the other not, this is not good result
    else:
        # if some files could be not exist add here other elif condition
        return 0


def main():
    # check if we are in grass
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        grass.fatal(_("$GISBASE not defined"))
        return 0
    # check if shell script output is required
    if flags["g"]:
        shell = True
        err = 0
        good = 1
    else:
        shell = False
        err = _("The two maps are different")
        good = _("The two maps are identical")
    # options
    typ = options["type"]
    ainp = checkfile(options["ainput"], typ, shell)
    binp = checkfile(options["binput"], typ, shell)
    variables = grass.core.gisenv()
    # files to investigate to check identity
    # for now color2 is ignored
    raster_folder = ["cats", "cell", "cellhd", "cell_misc", "fcell", "colr", "hist"]
    if flags["c"]:
        raster_folder.remove("colr")
    vector_folder = ["coor", "head", "topo"]
    if flags["t"]:
        vector_folder.remove("topo")
    # path to the mapsets
    aloc = os.path.join(
        variables["GISDBASE"], variables["LOCATION_NAME"], ainp["mapset"]
    )
    bloc = os.path.join(
        variables["GISDBASE"], variables["LOCATION_NAME"], binp["mapset"]
    )
    # variable for color table
    md5color = 1
    # start analysis for raster
    if typ == "raster":
        # for each folder
        for fold in raster_folder:
            # create the path to folder
            apath = os.path.join(aloc, fold, ainp["name"])
            bpath = os.path.join(bloc, fold, binp["name"])
            # if folder is cell_misc it check the into files inside cell_misc folder
            if fold == "cell_misc":
                adirlist = os.listdir(apath)
                bdirlist = os.listdir(bpath)
                # if the files are the same check md5sum for each file
                if adirlist == bdirlist:
                    for i in adirlist:
                        apath = os.path.join(apath, i)
                        bpath = os.path.join(bpath, i)
                        if not checkmd5(apath, bpath, shell):
                            grass.message(err)
                            return
                # if the files are different return false
                else:
                    grass.message(err)
                    return
            # check md5sum for each file
            else:
                if not checkmd5(apath, bpath, shell):
                    grass.message(err)
                    return
        grass.message(good)
        return
    # start analysis for vector
    elif typ == "vector":
        for fold in vector_folder:
            apath = os.path.join(aloc, "vector", ainp["name"], fold)
            bpath = os.path.join(bloc, "vector", binp["name"], fold)
            if not checkmd5(apath, bpath, shell):
                grass.message(err)
                return
        grass.message(good)
        return


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
