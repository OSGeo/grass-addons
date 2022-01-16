#!/usr/bin/env python3

############################################################################
#
# MODULE:	    Test for performance of r.mapcalc.tiled
# AUTHOR(S):	Anika Bettge, mundialis
#
# PURPOSE:	    Run r.mapcalc vs r.mapcalc.tiled with different parameters
# COPYRIGHT:	(C) 2020 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#############################################################################

# python3 test.py config.ini

import configparser
import csv
import grass.script as grass
import os
import sys
import time

if len(sys.argv) == 1:
    configfile = "config.ini"
else:
    configfile = sys.argv[1]
    if not os.path.isfile(configfile):
        grass.fatal("%s is no file and cannot be used as config file" % configfile)

# get config
config = configparser.ConfigParser()
config.read(configfile)

conf = {
    "regionmap": "ortho_2001_t792_1m",
    "expression": "bright_pixels = if(ortho_2001_t792_1m > 200, 1, 0)",
    "nprocs": "3",
    "resolution": [1],
    "wh": [1000],
    "csvfile": "rmapcalctiled_test.csv",
}

if config.has_section("GENERAL"):
    if config.has_option("GENERAL", "regionmap"):
        conf["regionmap"] = config.get("GENERAL", "regionmap")
    if config.has_option("GENERAL", "expression"):
        conf["expression"] = config.get("GENERAL", "expression")
    if config.has_option("GENERAL", "nprocs"):
        conf["nprocs"] = config.get("GENERAL", "nprocs")

if config.has_section("TESTPARAMETERS"):
    if config.has_option("TESTPARAMETERS", "resolution"):
        conf["resolution"] = config.get("TESTPARAMETERS", "resolution").split(",")
    if config.has_option("TESTPARAMETERS", "wh"):
        conf["wh"] = config.get("TESTPARAMETERS", "wh").split(",")
    if config.has_option("TESTPARAMETERS", "csvfile"):
        conf["csvfile"] = config.get("TESTPARAMETERS", "csvfile")

fieldnames = [
    "nprocs",
    "resolution",
    "weight-height",
    "number of cells",
    "time_rmapcalc",
    "time_rmapcalctiled",
]
with open(conf["csvfile"], "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for res in conf["resolution"]:
        # set region (resolution)
        print("set resolution to %s" % (res))
        grass.run_command("g.region", raster=conf["regionmap"], res=res)
        cells = str(grass.region()["cells"])
        # compute r.mapcalc
        print("compute r.mapcalc for resolution: %s" % str(res))
        name = "test_%s_%s_rmapcalc" % (conf["expression"].split("=")[0].strip(), cells)
        expression = "%s = %s" % (name, "=".join(conf["expression"].split("=")[1:]))
        start = time.time()
        grass.run_command("r.mapcalc", expression=conf["expression"], overwrite=True)
        end = time.time()
        time_rmapcalc = str(end - start)
        print("r.mapcalc time %s" % str(time_rmapcalc))
        # Sync. all buffers to disk i.e force write everything to disk using os.sync() method
        if not sys.platform == "win32":
            os.sync()
            print(
                "Force of writing everything to disk to minimize caching affecting the benchmarks"
            )
        grass.run_command("g.remove", flags="f", type="raster", name=name)
        for wh in conf["wh"]:
            # compute r.mapcalc.tiled
            print(
                "compute r.mapcalc.tiled for resolution: %s and weidth-heigth: %s"
                % (res, wh)
            )
            name = "test_%s_%s_%s" % (
                conf["expression"].split("=")[0].strip(),
                cells,
                str(wh),
            )
            expression = "%s = %s" % (name, "=".join(conf["expression"].split("=")[1:]))
            start = time.time()
            grass.run_command(
                "r.mapcalc.tiled",
                expression=expression,
                width=wh,
                height=wh,
                nprocs=conf["nprocs"],
                overwrite=True,
            )
            end = time.time()
            time_rmapcalctiled = str(end - start)
            print("r.mapcalc.tiled time %s" % str(time_rmapcalctiled))
            # Sync. all buffers to disk i.e force write everything to disk using os.sync() method
            if not sys.platform == "win32":
                os.sync()
                print(
                    "Force of writing everything to disk to minimize caching affecting the benchmarks"
                )
            grass.run_command("g.remove", flags="f", type="raster", name=name)
            # write csv
            with open(conf["csvfile"], "a", newline="") as f:
                writer.writerow(
                    {
                        "nprocs": conf["nprocs"],
                        "resolution": res,
                        "weight-height": wh,
                        "number of cells": cells,
                        "time_rmapcalc": time_rmapcalc,
                        "time_rmapcalctiled": time_rmapcalctiled,
                    }
                )

print("<%s> created" % conf["csvfile"])
