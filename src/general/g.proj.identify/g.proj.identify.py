#!/usr/bin/env python
# -*- coding: utf-8
"""
@module  g.proj.identify
@brief   Module for automatic identification of EPSG from definition of projection in WKT format.

(C) 2014-2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
"""

# %module
# % description: Autoidentifies EPSG code from WKT CRS definition.
# % keyword: general
# % keyword: projection
# % keyword: EPSG
# % keyword: WKT
# % keyword: .prj
# %end

# %option G_OPT_F_INPUT
# % key: wkt
# % description: Name of input file with WKT definition
# % required: no
# %end

# %option
# % key: epsg
# % type: integer
# % description: Input EPSG code
# % required: no
# %end

# %flag
# % key: p
# % description: Print projection info in Proj4 format
# %end

# %flag
# % key: w
# % description: Print projection info in WKT format
# %end

# %flag
# % key: s
# % description: Save as default EPSG in the current location
# %end

import os
from subprocess import PIPE

from grass.script import core as grass
from grass.pygrass.modules import Module


def writeEPSGtoPEMANENT(epsg):
    env = grass.gisenv()
    gisdbase = env["GISDBASE"]
    location = env["LOCATION_NAME"]
    path = os.path.join(gisdbase, location, "PERMANENT", "PROJ_EPSG")
    if os.path.isfile(path):  # if already file exist
        if os.getenv("GRASS_OVERWRITE", False):
            try:
                io = open(path, "w")
                io.write("epsg: %s" % epsg)
                io.close()
                grass.message("EPSG code have been written to <%s>" % path)
            except IOError as e:
                grass.error("I/O error({0}): {1}".format(e.errno, e.strerror))

        else:
            grass.message("EPSG file already exist <%s>" % path)
    else:
        try:
            io = open(path, "w")
            io.write("epsg: %s" % epsg)
            io.close()
            grass.message("EPSG code have been written to <%s>" % path)
        except IOError as e:
            grass.error("I/O error({0}): {1}".format(e.errno, e.strerror))


def isPermanent():
    env = grass.gisenv()
    if env["MAPSET"] == "PERMANENT":
        return True
    return False


def grassEpsg():
    proj = Module("g.proj", flags="p", quiet=True, stdout_=PIPE)
    proj = proj.outputs.stdout
    lines = proj.splitlines()
    for e, line in enumerate(lines):
        if "EPSG" in line:
            epsg = lines[e + 1].split(":")[1].replace(" ", "")
            print("epsg=%s" % epsg)
            if flags["s"]:
                if isPermanent():
                    writeEPSGtoPEMANENT(epsg)
                else:
                    grass.warning("Unable to access PERMANENT mapset")
            return
    try:
        proj = Module("g.proj", flags="wf", quiet=True, stdout_=PIPE)
        proj = proj.outputs.stdout
        wkt2standards(proj)
    except:
        grass.error("WKT input error")


def wkt2standards(prj_txt):
    srs = osr.SpatialReference()
    srs.ImportFromESRI([prj_txt])
    if flags["w"]:
        print("wkt=%s" % srs.ExportToWkt())
    if flags["p"]:
        print("proj4=%s" % srs.ExportToProj4())
    srs.AutoIdentifyEPSG()
    try:
        int(srs.GetAuthorityCode(None))
        epsg = srs.GetAuthorityCode(None)
        print("epsg=%s" % epsg)
        if flags["s"]:
            if isPermanent():
                writeEPSGtoPEMANENT(epsg)
            else:
                grass.warning("Unable to access PERMANENT mapset")
    except:
        grass.error("EPSG code cannot be identified")


def epsg2standards(epsg):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(epsg))
    if flags["w"]:
        print("wkt=%s" % srs.ExportToWkt())
    if flags["p"]:
        print("proj4=%s" % srs.ExportToProj4())


def main():
    try:
        from osgeo import osr
    except ImportError:
        grass.fatal(
            _(
                "Unable to load GDAL Python bindings (requires package "
                "'python-gdal' being installed)"
            ),
        )

    epsg = options["epsg"]
    pathwkt = options["wkt"]

    if epsg and pathwkt:
        grass.error("Only one type of conversions can be processed concurrently")

    if epsg:
        epsg2standards(epsg)
    else:
        if pathwkt:
            try:
                io = open(pathwkt, "r")
                wkt = io.read().rstrip()
                wkt2standards(wkt)
            except IOError as e:
                grass.error("Unable to open file <%s>: %s" % (e.errno, e.strerror))
        else:
            grassEpsg()


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
