#!/usr/bin/env python
# -*- coding: utf-8
import os
import sys
import argparse
import string
import random
import re

try:
    from grass.script import core as grass
except ImportError:
    sys.exit(
        "Cannot find 'grass' Python module. Python is supported by GRASS from version >= 6.4"
    )


##########################################################
################## guisection: required ##################
##########################################################
# %module
# % description: Links time-windows to vector link map.
# % keyword: vector
# %end


# %option
# % key: schema
# % type: string
# % label: Set schema name containing timewindows
# % required : yes
# %end


# %option
# % key: time
# % type: string
# % label: Set time "YYYY-MM-DD H:M:S"

# %end

# %option
# % key: type
# % label: Choose object type to connect
# % options: raingauge, links
# % multiple: yes
# % required : yes
# % answer: links
# %end

# %option
# % key: vector
# % label: Choose MV representation
# % options: lines, points
# % multiple: yes
# % required : yes
# % answer: points
# %end

# %flag
# % key:c
# % description: Create vector map
# %end

# %flag
# % key:a
# % description: Create vector maps for all timewin
# %end


# %option
# % key: layername
# % type: string
# % label: Name of points layer to connect
# %end

##########################################################
################## guisection: optional ##################
##########################################################
# %option G_OPT_F_INPUT
# % key: color
# % label: Set color table
# % required: no
# %end


# %flag
# % key:p
# % description: Print attribut table
# %end

# %flag
# % key:r
# % description: Remove temp file
# %end


schema = ""
time = ""
path = ""
ogr = ""
nat = ""
layer = ""
key = ""
prefix = ""
typ = ""
firstrun = ""
view = ""
filetimewin = ""


def print_message(msg):
    grass.message(msg)
    grass.message("-" * 60)


def setFirstRun():
    try:
        io = open(os.path.join(path, firstrun), "wr")
        io.write(options["type"])
        io.close
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))


def firstConnect():

    print_message("v.in.ogr")
    grass.run_command(
        "v.in.ogr",
        input="PG:",
        layer=layer,
        output=ogr,
        overwrite=True,
        flags="t",
        type=typ,
        quiet=True,
    )

    # if vector already exits, remove dblink (original table)
    if grass.find_file(nat, element="vector")["fullname"]:

        grass.run_command("v.db.connect", map=nat, flags="d", layer="1", quiet=True)

        grass.run_command("v.db.connect", map=nat, flags="d", layer="2", quiet=True)

    grass.run_command(
        "v.category",
        input=ogr,
        output=nat,
        option="transfer",
        overwrite=True,
        layer="1,2",
        quiet=True,
    )

    grass.run_command(
        "v.db.connect", map=nat, table=layer, key=key, layer="1", quiet=True
    )


def nextConnect():

    grass.run_command("v.db.connect", map=nat, layer="2", flags="d", quiet=True)

    grass.run_command(
        "v.db.connect", map=nat, table=view, key=key, layer="2", quiet=True
    )

    if options["color"]:
        setColor(nat)


def setColor(mapa):
    grass.run_command(
        "v.colors",
        map=mapa,
        use="attr",
        layer=2,
        column="precip_mm_h",
        rules=options["color"],
    )


def createVect(view_nat):

    grass.run_command(
        "v.in.ogr",
        input="PG:",
        layer=layer,
        output=ogr,
        overwrite=True,
        flags="t",
        key=key,
        type=typ,
        quiet=True,
    )

    # if vector already exits, remove dblink (original table)
    if grass.find_file(view_nat, element="vector")["fullname"]:
        grass.run_command(
            "v.db.connect", map=view_nat, flags="d", layer="1", quiet=True
        )

        grass.run_command(
            "v.db.connect", map=view_nat, flags="d", layer="2", quiet=True
        )

    grass.run_command(
        "v.category",
        input=ogr,
        output=view_nat,
        option="transfer",
        overwrite=True,
        layer="1,2",
        quiet=True,
    )

    grass.run_command(
        "v.db.connect", map=view_nat, table=layer, key=key, layer="1", quiet=True
    )

    grass.run_command(
        "v.db.connect", map=view_nat, table=view, key=key, layer="2", quiet=True
    )

    if options["color"]:
        setColor(view_nat)


def run():
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

    # dbConnGrass(options['database'],options['user'],options['password'])
    global view

    if not flags["c"] and not flags["a"]:
        view = (
            schema
            + ".%sview" % prefix
            + time.replace("-", "_").replace(":", "_").replace(" ", "_")
        )
        view = view[:-3]

        if not os.path.exists(os.path.join(path, firstrun)):
            setFirstRun()
            # print_message("first")
            firstConnect()
            nextConnect()
        else:
            # print_message("next")
            nextConnect()

    elif flags["c"]:

        view = (
            schema
            + ".%sview" % prefix
            + time.replace("-", "_").replace(":", "_").replace(" ", "_")
        )
        view = view[:-3]
        view_nat = "view" + time.replace("-", "_").replace(":", "_").replace(" ", "_")
        createVect(view_nat)

    elif flags["a"]:
        try:
            with open(os.path.join(path, filetimewin), "r") as f:
                for win in f.read().splitlines():
                    view = schema + ".%sview" % prefix + win[5:]

                    createVect(win)

        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

    if flags["p"]:

        sql = "select %s, precip_mm_h from %s " % (key, view)
        grass.run_command("db.select", sql=sql, separator="  ")


def isTimeValid(time):

    RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$")
    return bool(RE.search(time))


def main():

    global schema, time, path, ogr, nat, layer, key, prefix, typ, firstrun, filetimewin
    schema = options["schema"]

    time = options["time"]
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp_%s" % schema)

    ##remove schema and tempfile
    if flags["r"]:
        try:
            os.remove(os.path.join(path, "firstrunlink"))
            os.remove(os.path.join(path, "firstrungauge"))
        except:
            print_message("Temp file not exists")

    # for links
    if options["type"].find("l") != -1:
        if options["vector"].find("l") != -1:
            # connect to line layer
            ogr = "link_ogr"
            nat = "link_nat"
            layer = "link"
            key = "linkid"
            prefix = "l"
            typ = "line"
            firstrun = "firstrunlink"
            filetimewin = "l_timewindow"
            run()
        else:
            # connect to points layer
            if not options["layername"]:
                grass.fatal("set up name of points layer")
            else:
                ogr = "point_ogr"
                nat = "points_nat"
                layer = "%s.%s" % (schema, options["layername"])
                key = "linkid"
                prefix = "l"
                typ = "point"
                firstrun = "firstrunlink"
                filetimewin = "l_timewindow"
                run()

    # for rain gaugues
    if options["type"].find("r") != -1:
        ogr = "gauge_ogr"
        nat = "gauge_nat"
        layer = "%s.rgauge" % schema
        key = "gaugeid"
        prefix = "g"
        typ = "point"
        firstrun = "firstrungauge"
        filetimewin = "g_timewindow"
        run()

    print_message("DONE")


if __name__ == "__main__":
    options, flags = grass.parser()

main()
