#!/usr/bin/env python

############################################################################
#
# MODULE:       v.in.geopaparazzi
# AUTHOR(S):    Luca Delucchi
#
# PURPOSE:      Import data from Geopaparazzi database
# COPYRIGHT:    (C) 2012 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################
# %module
# % description: Imports data from Geopaparazzi database.
# % keyword: vector
# %end
# %flag
# % key: b
# % description: Import bookmarks
# %end
# %flag
# % key: i
# % description: Import images
# %end
# %flag
# % key: n
# % description: Import notes
# %end
# %flag
# % key: t
# % description: Import tracks
# %end
# %flag
# % key: z
# % description: Create a 3D elements (not for bookmarks)
# %end
# %option G_OPT_DB_DATABASE
# % description: Input Geopaparazzi database
# % required : yes
# %end
# %option
# % key: basename
# % type: string
# % gisprompt: new_file,file,output
# % description: Base name for output file
# % required : yes
# %end

import json
import os
import shutil
import sys

from grass.exceptions import CalledModuleError
from grass.script import core as grass
from grass.script.utils import basename


def returnClear(c, query):
    """Funtion to return a list of value from a query"""
    c.execute(query)
    bad = c.fetchall()
    good = []
    for b in bad:
        good.append(b[0])
    return good


def returnAll(c, query):
    """Function to return all the values from a query"""
    c.execute(query)
    return c.fetchall()


def checkEle(c, table):
    """Function to return the number of elements in a table"""
    c.execute("select count(_id) from %s" % table)
    return c.fetchone()[0]


def checkForm(jsonn):
    """Function to check the forms"""
    try:
        form = jsonn["form"]
    except KeyError:
        try:
            form = jsonn["forms"]
        except KeyError:
            grass.fatal(_("Error importing notes"))
    if isinstance(form, dict):
        values = form["formitems"]
    elif isinstance(form, list) and len(form) == 1:
        values = form[0]["formitems"]
    elif isinstance(form, list) and len(form) > 1:
        grass.warning(_("Form contains more fields and it is no yet supported"))
    return values


def returnFormKeys(attr):
    """Function to return a string with the columns' name and type of form"""
    js = json.loads(attr[0][3])
    values = checkForm(js)
    res = ""
    for v in values:
        if v["type"].lower() == "double":
            typ = "double"
        elif v["type"].lower() == "int" or v["type"].lower() == "integer":
            typ = "int"
        elif v["type"].lower() == "boolean":
            typ = "boolean"
        else:
            typ = "text"
        res += ", %s %s" % (v["key"].replace(" ", "_"), typ)
    return res


def returnFormValues(attr):
    """Function to return a string with the values of form"""
    js = json.loads(attr)
    values = checkForm(js)
    return ",".join("'%s'" % v["value"] for v in values)


def importGeom(vname, typ, c, owrite, z, cat=None):
    psel = "SELECT lon, lat"
    if z == "z":
        psel += ", altim"
        zcol = 3
    else:
        zcol = 0
    psel += " from %s" % typ
    if cat:
        psel += " where cat = '%s' order by _id" % cat
    points = returnAll(c, psel)
    wpoi = "\n".join(["|".join([str(col) for col in row]) for row in points])
    # import points using v.in.ascii
    try:
        grass.write_command(
            "v.in.ascii",
            flags="t%s" % z,
            input="-",
            z=zcol,
            output=vname,
            stdin=wpoi,
            overwrite=owrite,
            quiet=True,
        )
    except CalledModuleError:
        grass.fatal(_("Error importing %s" % vname))
    return points


def main():
    indb = options["database"]
    prefix = options["basename"]
    env = grass.gisenv()
    # fix sqlite3 db field string multibyte character problem
    sys.setdefaultencoding("utf-8")
    # check if 3d or not
    if flags["z"]:
        d3 = "z"
    else:
        d3 = ""
    owrite = grass.overwrite()
    # check if location it is latlong
    if grass.locn_is_latlong():
        locn = True
    else:
        locn = False
    # connection to sqlite geopaparazzi database
    import sqlite3

    conn = sqlite3.connect(indb)
    curs = conn.cursor()
    # if it is not a latlong location create a latlong location on the fly
    if not locn:
        # create new location and move to it creating new gisrc file
        new_loc = basename(grass.tempfile(create=False))
        new_loc_name = "geopaparazzi_%s" % new_loc
        grass.create_location(
            dbase=env["GISDBASE"],
            epsg="4326",
            location=new_loc_name,
            desc="Temporary location for v.in.geopaparazzi",
        )
        grc = os.getenv("GISRC")
        shutil.copyfile(grc, grc + ".old")
        newrc = open(grc, "w")
        newrc.write("GISDBASE: %s\n" % env["GISDBASE"])
        newrc.write("LOCATION_NAME: %s\n" % new_loc_name)
        newrc.write("MAPSET: PERMANENT\n")
        newrc.write("GRASS_GUI: text\n")
        newrc.close()
        grass.run_command("db.connect", flags="d", quiet=True)

    # load bookmarks
    if flags["b"]:
        # check if elements in bookmarks table are more the 0
        if checkEle(curs, "bookmarks") != 0:
            bookname = prefix + "_book"
            pois = importGeom(bookname, "bookmarks", curs, owrite, "")
            sql = "CREATE TABLE %s (cat int, text text)" % bookname
            grass.write_command("db.execute", input="-", stdin=sql)
            # select attributes
            sql = "select text from bookmarks order by _id"
            allattri = returnClear(curs, sql)
            # add values using insert statement
            idcat = 1
            for row in allattri:
                values = "%d,'%s'" % (idcat, str(row))
                sql = "insert into %s values(%s)" % (bookname, values)
                grass.write_command("db.execute", input="-", stdin=sql)
                idcat += 1
            # at the end connect table to vector
            grass.run_command("v.db.connect", map=bookname, table=bookname, quiet=True)
        else:
            grass.warning(_("No bookmarks found, escape them"))
    # load images
    if flags["i"]:
        # check if elements in images table are more the 0
        if checkEle(curs, "images") != 0:
            imagename = prefix + "_image"
            pois = importGeom(imagename, "images", curs, owrite, d3)
            sql = "CREATE TABLE %s (cat int, azim int, " % imagename
            sql += "path text, ts text, text text)"
            grass.write_command("db.execute", input="-", stdin=sql)
            # select attributes
            sql = "select azim, path, ts, text from images order by _id"
            allattri = returnAll(curs, sql)
            # add values using insert statement
            idcat = 1
            for row in allattri:
                values = "%d,'%d','%s','%s','%s'" % (
                    idcat,
                    row[0],
                    str(row[1]),
                    str(row[2]),
                    str(row[3]),
                )
                sql = "insert into %s values(%s)" % (imagename, values)
                grass.write_command("db.execute", input="-", stdin=sql)
                idcat += 1
            # at the end connect table to vector
            grass.run_command(
                "v.db.connect", map=imagename, table=imagename, quiet=True
            )
        else:
            grass.warning(_("No images found, escape them"))
    # if tracks or nodes should be imported create a connection with sqlite3
    # load notes
    if flags["n"]:
        # check if elements in notes table are more the 0
        if checkEle(curs, "notes") != 0:
            # select each categories
            categories = returnClear(curs, "select cat from notes group by cat")
            # for each category
            for cat in categories:
                # select lat, lon for create point layer
                catname = prefix + "_notes_" + cat
                pois = importGeom(catname, "notes", curs, owrite, d3, cat)
                # select form to understand the number
                forms = returnClear(
                    curs,
                    "select _id from notes where cat = '%s' "
                    "and form is not null order by _id" % cat,
                )
                # if number of form is different from 0 and number of point
                # remove the vector because some form it is different
                if len(forms) != 0 and len(forms) != len(pois):
                    grass.run_command(
                        "g.remove", flags="f", type="vector", name=catname, quiet=True
                    )
                    grass.warning(
                        _(
                            "Vector %s not imported because number"
                            " of points and form is different"
                        )
                    )
                # if form it's 0 there is no form
                elif len(forms) == 0:
                    # create table without form
                    sql = "CREATE TABLE %s (cat int, ts text, " % catname
                    sql += "text text, geopap_cat text)"
                    grass.write_command("db.execute", input="-", stdin=sql)
                    # select attributes
                    sql = (
                        "select ts, text, cat from notes where "
                        "cat='%s' order by _id" % cat
                    )
                    allattri = returnAll(curs, sql)
                    # add values using insert statement
                    idcat = 1
                    for row in allattri:
                        values = "%d,'%s','%s','%s'" % (
                            idcat,
                            str(row[0]),
                            str(row[1]),
                            str(row[2]),
                        )
                        sql = "insert into %s values(%s)" % (catname, values)
                        grass.write_command("db.execute", input="-", stdin=sql)
                        idcat += 1
                    # at the end connect table to vector
                    grass.run_command(
                        "v.db.connect", map=catname, table=catname, quiet=True
                    )
                # create table with form
                else:
                    # select all the attribute
                    sql = (
                        "select ts, text, cat, form from notes where "
                        "cat='%s' order by _id" % cat
                    )
                    allattri = returnAll(curs, sql)
                    # return string of form's categories too create table
                    keys = returnFormKeys(allattri)
                    sql = "CREATE TABLE %s (cat int, ts text, " % catname
                    sql += "text text, geopap_cat text %s)" % keys
                    grass.write_command("db.execute", input="-", stdin=sql)
                    # it's for the number of categories
                    idcat = 1
                    # for each feature insert value
                    for row in allattri:
                        values = "%d,'%s','%s','%s'," % (
                            idcat,
                            str(row[0]),
                            str(row[1]),
                            str(row[2]),
                        )
                        values += returnFormValues(row[3])
                        sql = "insert into %s values(%s)" % (catname, values)
                        grass.write_command("db.execute", input="-", stdin=sql)
                        idcat += 1
                    # at the end connect table with vector
                    grass.run_command(
                        "v.db.connect", map=catname, table=catname, quiet=True
                    )
        else:
            grass.warning(_("No notes found, escape them"))
    # load tracks
    if flags["t"]:
        # check if elements in bookmarks table are more the 0
        if checkEle(curs, "gpslogs") != 0:
            tracksname = prefix + "_tracks"
            # define string for insert data at the end
            tracks = ""
            # return ids of tracks
            ids = returnClear(curs, "select _id from gpslogs")
            # for each track
            for i in ids:
                # select all the points coordinates
                tsel = "select lon, lat"
                if flags["z"]:
                    tsel += ", altim"
                tsel += " from gpslog_data where logid=%s order by _id" % i
                trackpoints = returnAll(curs, tsel)
                wpoi = "\n".join(
                    ["|".join([str(col) for col in row]) for row in trackpoints]
                )
                tracks += "%s\n" % wpoi
                if flags["z"]:
                    tracks += "NaN|NaN|Nan\n"
                else:
                    tracks += "NaN|Nan\n"
            # import lines
            try:
                grass.write_command(
                    "v.in.lines",
                    flags=d3,
                    input="-",
                    out=tracksname,
                    stdin=tracks,
                    overwrite=owrite,
                    quiet=True,
                )
            except CalledModuleError:
                grass.fatal(_("Error importing %s" % tracksname))
            # create table for line
            sql = "CREATE TABLE %s (cat int, startts text, " % tracksname
            sql += "endts text, text text, color text, width int)"
            grass.write_command("db.execute", input="-", stdin=sql)
            sql = (
                "select logid, startts, endts, text, color, width from"
                " gpslogs, gpslogsproperties where gpslogs._id="
                "gpslogsproperties.logid"
            )
            # return attributes
            allattri = returnAll(curs, sql)
            # for each line insert attribute
            for row in allattri:
                values = "%d,'%s','%s','%s','%s',%d" % (
                    row[0],
                    str(row[1]),
                    str(row[2]),
                    str(row[3]),
                    str(row[4]),
                    row[5],
                )
                sql = "insert into %s values(%s)" % (tracksname, values)
                grass.write_command("db.execute", input="-", stdin=sql)
            # at the end connect map with table
            grass.run_command(
                "v.db.connect", map=tracksname, table=tracksname, quiet=True
            )
        else:
            grass.warning(_("No tracks found, escape them"))
    # if location it's not latlong reproject it
    if not locn:
        # copy restore the original location
        shutil.copyfile(grc + ".old", grc)
        # reproject bookmarks
        if flags["b"] and checkEle(curs, "bookmarks") != 0:
            grass.run_command(
                "v.proj",
                quiet=True,
                input=bookname,
                location="geopaparazzi_%s" % new_loc,
                mapset="PERMANENT",
            )
        # reproject images
        if flags["i"] and checkEle(curs, "images") != 0:
            grass.run_command(
                "v.proj",
                quiet=True,
                input=imagename,
                location="geopaparazzi_%s" % new_loc,
                mapset="PERMANENT",
            )
        # reproject notes
        if flags["n"] and checkEle(curs, "notes") != 0:
            for cat in categories:
                catname = prefix + "_node_" + cat
                grass.run_command(
                    "v.proj",
                    quiet=True,
                    input=catname,
                    location="geopaparazzi_%s" % new_loc,
                    mapset="PERMANENT",
                )
        # reproject track
        if flags["t"] and checkEle(curs, "gpslogs") != 0:
            grass.run_command(
                "v.proj",
                quiet=True,
                input=tracksname,
                location="geopaparazzi_%s" % new_loc,
                mapset="PERMANENT",
            )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
