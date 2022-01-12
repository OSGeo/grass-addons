#!/usr/bin/env python

############################################################################
#
# MODULE:       cloud_unpack.py
# AUTHOR(S):    Luca Delucchi
# PURPOSE:      It is used to unpack raster and vector maps by g.cloud module
#
# COPYRIGHT:    (C) 2011 by Luca Delucchi
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

import glob
import os
import sys
import tarfile
import logging
import cloud_which as which
from grass.exceptions import CalledModuleError

# the home of the user
homeServer = os.getcwd()

f = open(os.path.join(homeServer, "unpackwrite.log"), "w")

LOG_FILENAME = os.path.join(homeServer, "unpack.log")
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG, format=LOGGING_FORMAT)

if len(sys.argv) != 2:
    logging.error("Usage: python %s GISDBASE" % sys.argv[0])
    f.write("Usage: python %s GISDBASE" % sys.argv[0])

# the full path to GISDBASE, LOCATION_NAME, MAPSET
dbaselocatmap = sys.argv[1].strip("").rstrip("\/")
mapset = os.path.split(dbaselocatmap)[1]
location = os.path.split(os.path.split(dbaselocatmap)[0])[1]
dbase = os.path.split(os.path.split(dbaselocatmap)[0])[0]

logging.debug("Unpacking in <%s/%s/%s>" % (dbase, location, mapset))
f.write("Unpacking in <%s/%s/%s>" % (dbase, location, mapset))

# read for grass executable the path to gisbase
for line in open(which.which("grass")).readlines():
    if line.startswith('    gisbase = "'):
        gisbase = line.split("=")[-1].split('"')[1]
# look for raster and vector pack
raster = glob.glob1(homeServer, "rastertarpack")
vector = glob.glob1(homeServer, "vectortarpack")

logging.debug("Found: %s raster pack, %s vector pack" % (raster, vector))
f.write("Found: %s raster pack, %s vector pack" % (raster, vector))
## add some environment variables
os.environ["GISBASE"] = gisbase

sys.path.append(os.path.join(gisbase, "etc", "python"))

import grass.script as grass
import grass.script.setup as gsetup

gsetup.init(gisbase, dbase, location, mapset)

grass.run_command("db.connect", flags="p")
kv = grass.db_connection()
database = kv["database"]
driver = kv["driver"]
logging.debug("db.connect: driver: %s, database %s" % (driver, database))

# unpack raster and vector maps
if len(raster) != 0:
    try:
        tar = tarfile.TarFile.open(name="rastertarpack", mode="r")
        tar.extractall()
        rasters = glob.glob1(homeServer, "*.rasterpack")
    except:
        logging.error("Error unpacking rastertarpack")
        f.write("Error unpacking rastertarpack")
    for i in rasters:
        logging.debug("Unpacking raster map <%s>" % os.path.join(homeServer, i))
        try:
            grass.run_command("r.unpack", input=os.path.join(homeServer, i))
        except CalledModuleError:
            logging.error(
                "Error unpacking raster map <%s>" % os.path.join(homeServer, i)
            )
        # os.remove(os.path.join(homeServer,i)) TO UNCOMMENT WHEN ALL WILL BE OK

if len(vector) != 0:
    try:
        tar = tarfile.TarFile.open(name="vectortarpack", mode="r")
        tar.extractall()
        vectors = glob.glob1(homeServer, "*.vectorpack")
    except:
        logging.error("Error unpacking vectortarpack")
        f.write("Error unpacking vectortarpack")

    for i in vectors:
        logging.debug("Unpacking vector map <%s>" % os.path.join(homeServer, i))
        try:
            grass.run_command("v.unpack", input=os.path.join(homeServer, i))
        except CalledModuleError:
            logging.error(
                "Error unpacking raster map <%s>" % os.path.join(homeServer, i)
            )
        # os.remove(os.path.join(homeServer,i)) TO UNCOMMENT WHEN ALL WILL BE OK
