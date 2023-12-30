#!/usr/bin/env python
# -*- coding: utf-8
import os
import sys
import argparse
import string
import random
import math
import timeit
import time
import atexit
import shutil
import csv
import glob
import re
from collections import defaultdict
from datetime import datetime, timedelta
from math import sin, cos, atan2, degrees, radians, tan, sqrt, fabs

from grass.script import core as grass
from grass.exceptions import CalledModuleError

##########################################################
################## guisection: required ##################
##########################################################
# %module
# % description: Module for working with microwave links
# % keyword: raster
# % keyword: microwave
# %end

# %option
# % key: database
# % type: string
# % key_desc : name
# % gisprompt: old_dbname,dbname,dbname
# % description: PostgreSQL database containing input data
# % guisection: Database
# % required : yes
# %end


##########################################################
############## guisection: Baseline #################
##########################################################
# %option
# % key: statfce
# % label: Choose method for compute bs from time intervals
# % options: avg,mode,quantile

# % answer: mode

# % guisection: Baseline
# %end

# %option
# % key: quantile
# % label: Set quantile
# % type: integer
# % guisection: Baseline
# % answer: 96
# %end

# %option
# % key: roundm
# % label: Round to "m" decimal places for computing mode
# % type: integer
# % guisection: Baseline
# % answer: 3
# %end

# %option
# % key: aw
# % label: aw value
# % description: Wetting antenna value Aw[dB]
# % type: double
# % guisection: Baseline
# % answer: 1.5
# %end
# %option G_OPT_F_INPUT
# % key: baseltime
# % label: Set interval or just time when not raining (see the manual)
# % guisection: Baseline
# % required: no
# %end

# %option G_OPT_F_INPUT
# % key: baselfile
# % label: Baseline values in format "linkid,baseline"
# % guisection: Baseline
# % required: no
# %end


##########################################################
################# guisection: Timewindows ##############
##########################################################
# %option
# % key: interval
# % label: Summing precipitation per
# % options: minute, hour, day
# % guisection: Time-windows
# % answer: minute
# %end

# %option
# % key: fromtime
# % label: First timestamp "YYYY-MM-DD H:M:S"
# % description: Set first timestamp to create timewindows
# % type: string
# % guisection: Time-windows
# %end

# %option
# % key: totime
# % label: Last timestamp "YYYY-MM-DD H:M:S"
# % description: Set last timestamp to create timewindows
# % type: string
# % guisection: Time-windows
# %end


# %option G_OPT_F_INPUT
# % key: lignore
# % label: Linkid ignore list
# % guisection: Time-windows
# % required: no
# %end


# %option G_OPT_M_DIR
# % key: rgauges
# % label: Path to folder with rain rauge files
# % guisection:Time-windows
# % required: no
# %end

##########################################################
################# guisection: Interpolation ##############
##########################################################

# %flag
# % key:g
# % description: Run GRASS analysis
# % guisection: Interpolation
# %end

# %option
# % key: interpolation
# % label: Type of interpolation
# % options: bspline, idw, rst
# % guisection: Interpolation
# % answer: rst
# %end


# %option
# % key: isettings
# % label: Interpolation command string
# % description: Additional settings for choosen interpolation (see manual)
# % type: string
# % guisection: Interpolation
# %end


# %flag
# % key:q
# % description: Do not set region from modul settings
# % guisection: Interpolation
# %end


# %option
# % key: pmethod
# % label: Type of interpolation
# % options: permeter, count
# % guisection: Interpolation
# % answer: count
# %end

# %option
# % key: step
# % label: Setting for parameter pmethod
# % type: integer
# % guisection: Interpolation
# % answer: 1
# %end

# %option G_OPT_F_INPUT
# % key: color
# % label: Set color table
# % guisection: Interpolation
# % required: no
# %end


##########################################################
############## guisection: database work #################
##########################################################

# %option
# % key: user
# % type: string
# % label: User name
# % description: Connect to the database as the user username instead of the default.
# % guisection: Database
# % required : no
# %end

# %option
# % key: password
# % type: string
# % label: Password
# % description: Password will be stored in file!
# % guisection: Database
# % required : no
# %end

##########################################################
############### guisection: optional #####################
##########################################################
# %flag
# % key:p
# % description: Print info about timestamp(first,last) in db
# %end

# %flag
# % key:r
# % description: Remove temporary working schema and data folder
# %end


# %option
# % key: schema
# % type: string
# % label: Name of db schema for results
# % answer: temp4
# %end


# EXAMPLE
# r.mvprecip.py -g database=letnany baseline=1 fromtime=2013-09-10 04:00:00 totime=2013-09-11 04:00:00 schema=temp6


path = ""
view = "view"
view_statement = "TABLE"
# new scheme, no source
record_tb_name = "record"
comp_precip = "computed_precip"
comp_precip_gauge = "rgauge_rec"
R = 6371
mesuretime = 0
restime = 0
temp_windows_names = []
schema_name = ""


###########################
##   Point-link interpolation


def intrpolatePoints(db):
    print_message("Interpolating points along lines...")

    step = options["step"]  # interpolation step per meters
    step = float(step)
    sql = "select ST_AsText(link.geom),ST_Length(link.geom,false), linkid from link"
    resu = db.executeSql(
        sql, True, True
    )  # values from table link include geom, lenght and linkid

    nametable = "linkpoints" + str(step).replace(
        ".0", ""
    )  # create name for table with interopol. points.
    sql = "DROP TABLE IF EXISTS %s.%s" % (
        schema_name,
        nametable,
    )  # if table exist than drop
    db.executeSql(sql, False, True)

    try:  # open file for interpol. points.
        io = open(os.path.join(path, "linkpointsname"), "wr")
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))
    io.write(nametable)
    io.close

    sql = (
        "create table %s.%s (linkid integer,long real,lat real,point_id serial PRIMARY KEY) "
        % (schema_name, nametable)
    )  # create table where will be intrpol. points.
    db.executeSql(sql, False, True)

    latlong = []  # list of  [lon1 lat1 lon2 lat2]
    dist = []  # list of distances between nodes on one link
    linkid = []  # linkid value

    a = 0  # index of latlong row
    x = 0  # id in table with interpol. points

    try:
        io = open(os.path.join(path, "linknode"), "wr")
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    temp = []
    for record in resu:
        tmp = record[0]
        tmp = tmp.replace("LINESTRING(", "")
        tmp = tmp.replace(" ", ",")
        tmp = tmp.replace(")", "")
        tmp = tmp.split(",")
        latlong.append(tmp)  # add [lon1 lat1 lon2 lat2] to list latlong

        lon1 = latlong[a][0]
        lat1 = latlong[a][1]
        lon2 = latlong[a][2]
        lat2 = latlong[a][3]

        dist = record[1]  # distance between nodes on current link
        linkid = record[2]  # linkid value

        az = bearing(lat1, lon1, lat2, lon2)  # compute approx. azimut on sphere
        a += 1

        if options["pmethod"].find("p") != -1:  # compute per distance interval
            while (
                abs(dist) > step
            ):  # compute points per step while is not achieve second node on link
                lat1, lon1, az, backBrg = destinationPointWGS(
                    lat1, lon1, az, step
                )  # return interpol. point and set current point as starting point(for next loop), also return azimut for next point
                dist -= step  # reduce distance
                x += 1
                out = (
                    str(linkid)
                    + "|"
                    + str(lon1)
                    + "|"
                    + str(lat1)
                    + "|"
                    + str(x)
                    + "\n"
                )  # set string for one row in table with interpol points
                temp.append(out)

        else:  # compute by dividing distance to sub-distances
            step1 = dist / (step + 1)
            for i in range(
                0, int(step)
            ):  # compute points per step while is not achieve second node on link
                lat1, lon1, az, backBrg = destinationPointWGS(
                    lat1, lon1, az, step1
                )  # return interpol. point and set current point as starting point(for next loop), also return azimut for next point
                x += 1
                out = (
                    str(linkid)
                    + "|"
                    + str(lon1)
                    + "|"
                    + str(lat1)
                    + "|"
                    + str(x)
                    + "\n"
                )  # set string for one row in table with interpol points
                temp.append(out)

    io.writelines(temp)  # write interpolated points to flat file
    io.flush()
    io.close()

    io1 = open(os.path.join(path, "linknode"), "r")
    db.copyfrom(
        io1, "%s.%s" % (schema_name, nametable)
    )  # write interpoalted points to database from temp flat file
    io1.close()

    sql = "SELECT AddGeometryColumn  ('%s','%s','geom',4326,'POINT',2); " % (
        schema_name,
        nametable,
    )  # add geometry column for computed interpolated points
    db.executeSql(sql, False, True)

    sql = (
        "UPDATE %s.%s SET geom = \
    (ST_SetSRID(ST_MakePoint(long, lat),4326)); "
        % (schema_name, nametable)
    )  # make geometry for computed interpolated points
    db.executeSql(sql, False, True)

    sql = "alter table %s.%s drop column lat" % (
        schema_name,
        nametable,
    )  # remove latitde column from table
    db.executeSql(sql, False, True)
    sql = "alter table %s.%s drop column long" % (
        schema_name,
        nametable,
    )  # remove longtitude column from table
    db.executeSql(sql, False, True)


def destinationPointWGS(lat1, lon1, brng, s):
    a = 6378137
    b = 6356752.3142
    f = 1 / 298.257223563
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    brg = math.radians(float(brng))

    sb = sin(brg)
    cb = cos(brg)
    tu1 = (1 - f) * tan(lat1)
    cu1 = 1 / sqrt((1 + tu1 * tu1))
    su1 = tu1 * cu1
    s2 = atan2(tu1, cb)
    sa = cu1 * sb
    csa = 1 - sa * sa
    us = csa * (a * a - b * b) / (b * b)
    A = 1 + us / 16384 * (4096 + us * (-768 + us * (320 - 175 * us)))
    B = us / 1024 * (256 + us * (-128 + us * (74 - 47 * us)))
    s1 = s / (b * A)
    s1p = 2 * math.pi
    # Loop through the following while condition is true.
    while abs(s1 - s1p) > 1e-12:
        cs1m = cos(2 * s2 + s1)
        ss1 = sin(s1)
        cs1 = cos(s1)
        ds1 = (
            B
            * ss1
            * (
                cs1m
                + B
                / 4
                * (
                    cs1 * (-1 + 2 * cs1m * cs1m)
                    - B / 6 * cs1m * (-3 + 4 * ss1 * ss1) * (-3 + 4 * cs1m * cs1m)
                )
            )
        )
        s1p = s1
        s1 = s / (b * A) + ds1
    # Continue calculation after the loop.
    t = su1 * ss1 - cu1 * cs1 * cb
    lat2 = atan2(su1 * cs1 + cu1 * ss1 * cb, (1 - f) * sqrt(sa * sa + t * t))
    l2 = atan2(ss1 * sb, cu1 * cs1 - su1 * ss1 * cb)
    c = f / 16 * csa * (4 + f * (4 - 3 * csa))
    l = l2 - (1 - c) * f * sa * (
        s1 + c * ss1 * (cs1m + c * cs1 * (-1 + 2 * cs1m * cs1m))
    )
    d = atan2(sa, -t)
    finalBrg = d + 2 * math.pi
    backBrg = d + math.pi
    lon2 = lon1 + l
    # Convert lat2, lon2, finalBrg and backBrg to degrees
    lat2 = degrees(lat2)
    lon2 = degrees(lon2)
    finalBrg = degrees(finalBrg)
    backBrg = degrees(backBrg)
    # b = a - (a/flat)
    # flat = a / (a - b)
    finalBrg = (finalBrg + 360) % 360
    backBrg = (backBrg + 360) % 360

    return (lat2, lon2, finalBrg, backBrg)


def bearing(lat1, lon1, lat2, lon2):
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))
    dLon = lon2 - lon1

    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dLon
    )
    brng = math.degrees(math.atan2(y, x))

    return (brng + 360) % 360


###########################
## Miscellaneous
def isTimeValid(time):
    RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$")
    return bool(RE.search(time))


def print_message(msg):
    grass.message(msg)
    grass.message("-" * 60)


def randomWord(length):
    return "".join(random.choice(string.lowercase) for i in range(length))


def st(mes=True):
    if mes:
        global mesuretime
        global restime
        mesuretime = time.time()
    else:
        restime = time.time() - mesuretime
        print("time is: ", restime)


def getFilesInFoldr(fpath):
    lis = os.listdir(fpath)
    tmp = []
    for path in lis:
        if path.find("~") == -1:
            tmp.append(path)

    return tmp


###########################
##   optional


def removeTemp(db):
    sql = "drop schema IF EXISTS %s CASCADE" % schema_name
    db.executeSql(sql, False, True)
    shutil.rmtree(path)
    print_message("Folder and schema removed")
    sys.exit()


def printTime(db):
    sql = "create view tt as select time from %s order by time" % record_tb_name
    db.executeSql(sql, False, True)
    # get first timestamp
    sql = "select time from tt limit 1"
    timestamp_min = db.executeSql(sql, True, True)[0][0]
    print_message("First timestamp is %s" % timestamp_min)
    record_num = db.count(record_tb_name)

    # get last timestep
    sql = "select time from  tt offset %s" % (record_num - 1)
    timestamp_max = db.executeSql(sql, True, True)[0][0]
    print_message("Last timestamp is %s" % timestamp_max)
    sql = "drop view tt"
    db.executeSql(sql, False, True)
    sys.exit()


###########################
##   database work


def firstRun(db):
    print_message("Preparing database...")

    print_message("1/16 Create extension")
    sql = "CREATE EXTENSION postgis;"
    db.executeSql(sql, False, True)

    print_message("2/16 Add geometry column to node")
    sql = "SELECT AddGeometryColumn   ('public','node','geom',4326,'POINT',2); "
    db.executeSql(sql, False, True)

    print_message("3/16 Add geometry column to link")
    sql = "SELECT AddGeometryColumn  ('public','link','geom',4326,'LINESTRING',2); "
    db.executeSql(sql, False, True)

    print_message("4/16 Make geometry for points")
    sql = "UPDATE node SET geom = ST_SetSRID(ST_MakePoint(long, lat), 4326); "
    db.executeSql(sql, False, True)

    print_message("5/16 Make geometry for links")
    sql = "UPDATE link SET geom = st_makeline(n1.geom,n2.geom) \
        FROM node AS n1 JOIN link AS l ON n1.nodeid = fromnodeid JOIN node AS n2 ON n2.nodeid = tonodeid WHERE link.linkid = l.linkid; "
    db.executeSql(sql, False, True)

    print_message("6/16 Add column polarization")
    sql = "alter table record add column polarization char(1); "
    db.executeSql(sql, False, True)

    print_message("7/16 Add colum lenght")
    sql = "alter table record add column lenght real; "
    db.executeSql(sql, False, True)

    print_message("8/16 Add column precip")
    sql = "alter table record add column precip real; "
    db.executeSql(sql, False, True)

    print_message("9/16 Connect table polarization to record")
    sql = "update record  set polarization=link.polarization from link where record.linkid=link.linkid;"
    db.executeSql(sql, False, True)

    print_message("10/16 Update record lenght")
    sql = "update record  set lenght=ST_Length(link.geom,false) from link where record.linkid=link.linkid;"
    db.executeSql(sql, False, True)

    print_message("11/16 Create sequence")
    sql = "CREATE SEQUENCE serial START 1; "
    db.executeSql(sql, False, True)

    print_message("12/16 Add column record")
    sql = "alter table record add column recordid integer default nextval('serial'); "
    db.executeSql(sql, False, True)

    print_message("13/16 Create index on recordid")
    sql = "CREATE INDEX idindex ON record USING btree(recordid); "
    db.executeSql(sql, False, True)

    print_message("14/16 Create index on time")
    sql = "CREATE INDEX timeindex ON record USING btree (time); "
    db.executeSql(sql, False, True)

    print_message("15/16 Add function for compute mode")
    sql = "CREATE OR REPLACE FUNCTION _final_mode(anyarray) RETURNS anyelement AS $BODY$ SELECT a FROM unnest($1)\
        a GROUP BY 1  ORDER BY COUNT(1) DESC, 1 LIMIT 1; $BODY$ LANGUAGE 'sql' IMMUTABLE;"
    db.executeSql(sql, False, True)
    sql = "CREATE AGGREGATE mode(anyelement) (\
            SFUNC=array_append, \
            STYPE=anyarray,\
            FINALFUNC=_final_mode, \
            INITCOND='{}');"
    db.executeSql(sql, False, True)

    print_message("16/16 Remove links where data is missing '-99.9'")
    sql = "DELETE from record where rxpower<-99.9 "
    db.executeSql(sql, False, True)


def dbConnGrass(database, user, password):
    print_message("Connecting to db-GRASS...")
    # Unfortunately we cannot test untill user/password is set
    if user or password:
        try:
            grass.run_command(
                "db.login", driver="pg", database=database, user=user, password=password
            )
        except CalledModuleError:
            grass.fatal("Cannot login")

    # Try to connect
    try:
        grass.run_command(
            "db.select",
            quiet=True,
            flags="c",
            driver="pg",
            database=database,
            sql="select version()",
        )
    except CalledModuleError:
        if user or password:
            print_message("Deleting login (db.login) ...")
            try:
                grass.run_command(
                    "db.login",
                    quiet=True,
                    driver="pg",
                    database=database,
                    user="",
                    password="",
                )
            except CalledModuleError:
                print_message("Cannot delete login.")
        grass.fatal("Cannot connect to database.")

    try:
        grass.run_command("db.connect", driver="pg", database=database)
    except CalledModuleError:
        grass.fatal("Cannot connect to database.")


def dbConnPy():
    import psycopg2

    # print_message("Connecting to database by Psycopg driver...")
    db_name = options["database"]
    db_user = options["user"]
    db_password = options["password"]

    try:
        sys.path.insert(
            0, os.path.join(os.environ["GRASS_ADDON_BASE"], "etc", "r.mwprecip")
        )
        from pgwrapper import pgwrapper as pg
    except ImportError:
        sys.exit("Cannot find 'pgwrapper' Python module")

    try:
        conninfo = {"dbname": db_name}
        if db_user:
            conninfo["user"] = db_user
        if db_password:
            conninfo["passwd"] = db_password

        db = pg(**conninfo)

    except psycopg2.OperationalError as e:
        grass.fatal("Unable to connect to the database <%s>. %s" % (db_name, e))

    return db


def isAttributExist(db, schema, table, columns):
    sql = (
        "SELECT EXISTS( SELECT * FROM information_schema.columns WHERE \
         table_schema = '%s' AND \
         table_name = '%s' AND\
         column_name='%s');"
        % (schema, table, columns)
    )
    return db.executeSql(sql, True, True)[0][0]


def isTableExist(db, schema, table):
    sql = (
        "SELECT EXISTS( SELECT * \
         FROM information_schema.tables \
         WHERE \
         table_schema = '%s' AND \
         table_name = '%s');"
        % (schema, table)
    )
    return db.executeSql(sql, True, True)[0][0]


def removeLines(old_file, new_file, start, end):
    data_list = open(old_file, "r").readlines()
    temp_list = data_list[0:start]
    temp_list[len(temp_list) :] = data_list[end : len(data_list)]
    open(new_file, "wr").writelines(temp_list)


def readRaingauge(db, path_file):
    schema_name = options["schema"]
    rgpath = path_file

    lines = open(rgpath).readlines()
    ##get metadata from raingauge file
    try:
        with open(rgpath, "rb") as f:
            gaugeid = f.next()
            lat = f.next()
            lon = f.next()
        f.close()
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    ##make new file and remove metadata
    # no_extension=('.').join(path.split('.')[:-1])
    # print_message(no_extension)

    removeLines(rgpath, os.path.join(path, "gauge_tmp"), 0, 3)
    gid = int(gaugeid)
    la = float(lat)
    lo = float(lon)
    ##prepare list of string for copy to database
    try:
        with open(os.path.join(path, "gauge_tmp"), "rb") as f:
            data = f.readlines()
            tmp = []
            for line in data:
                stri = str(gid) + "," + line
                tmp.append(stri)
            f.close()

    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    ## write list of string to database
    try:
        with open(os.path.join(path, "gauge_tmp"), "wr") as x:
            x.writelines(tmp)
            x.close()
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    if not isTableExist(db, schema_name, "rgauge"):
        ##create table for raingauge id
        sql = (
            "create table %s.%s (gaugeid integer PRIMARY KEY,lat real,long real ) "
            % (schema_name, "rgauge")
        )
        db.executeSql(sql, False, True)

        ## create table for rain gauge records
        sql = (
            ' CREATE TABLE %s.%s \
              (gaugeid integer NOT NULL,\
              "time" timestamp without time zone NOT NULL,\
              precip real,\
              CONSTRAINT recordrg PRIMARY KEY (gaugeid, "time"),\
              CONSTRAINT fk_record_rgague FOREIGN KEY (gaugeid)\
              REFERENCES %s.rgauge (gaugeid) MATCH SIMPLE\
              ON UPDATE NO ACTION ON DELETE NO ACTION)'
            % (schema_name, comp_precip_gauge, schema_name)
        )
        db.executeSql(sql, False, True)

        ##crate geometry column
        sql = "SELECT AddGeometryColumn('%s','%s','geom',4326,'POINT',2); " % (
            schema_name,
            "rgauge",
        )
        db.executeSql(sql, False, True)

    sql = "Insert into %s.%s ( gaugeid , lat , long) values (%s , %s , %s) " % (
        schema_name,
        "rgauge",
        gid,
        la,
        lo,
    )
    db.executeSql(sql, False, True)

    ## copy records in database
    io1 = open(os.path.join(path, "gauge_tmp"), "r")
    db.copyfrom(io1, "%s.%s" % (schema_name, "rgauge_rec"), ",")
    io1.close()

    ## make geom from long lat
    sql = "UPDATE %s.%s SET geom = ST_SetSRID(ST_MakePoint(long, lat), 4326); " % (
        schema_name,
        "rgauge",
    )
    db.executeSql(sql, False, True)
    os.remove(os.path.join(path, "gauge_tmp"))


###########################
##  status


def isCurrSetT():
    curr_timewindow_config = "null"
    try:
        io1 = open(os.path.join(path, "time_window_info"), "r")
        curr_timewindow_config = io1.readline()
        io1.close
    except:
        pass

    # compare current and new settings
    new_timewindow_config = (
        options["interval"]
        + "|"
        + options["fromtime"]
        + "|"
        + options["totime"]
        + options["lignore"]
    )
    if (
        curr_timewindow_config != new_timewindow_config
        or not (
            options["interval"]
            or options["fromtime"]
            or options["totime"]
            or options["lignore"]
        )
        or options["rgauges"]
    ):
        return False
    else:
        return True


def isCurrSetP():
    ##  chceck if current settings is same like settings from computing before. return True or False
    curr_precip_conf = ""
    new_precip_conf = ""
    try:
        io0 = open(os.path.join(path, "compute_precip_info"), "r")
        curr_precip_conf = io0.readline()
        io0.close()
    except IOError:
        pass

    if options["baseltime"]:
        bpath = options["baseltime"]
        try:
            f = open(bpath, "r")
            for line in f:
                new_precip_conf += line.replace("\n", "")

            new_precip_conf += "|" + options["aw"]
        except:
            pass

    elif options["baselfile"]:
        new_precip_conf = "fromfile|" + options["aw"]

    if curr_precip_conf != new_precip_conf:
        return False
    else:
        return True


###########################
##   baseline compute


def getBaselDict(db):
    ## choose baseline compute method that set user and call that function, return distionary key:linkid,

    if options["baselfile"]:
        links_dict = readBaselineFromText(options["baselfile"])
        try:
            io1 = open(os.path.join(path, "compute_precip_info"), "wr")
            io1.write("fromfile|" + options["aw"])
            io1.close
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

    elif options["baseltime"]:
        print_message(
            'Computing baselines "time interval" "%s"...' % options["statfce"]
        )
        computeBaselineFromTime(db)
        links_dict = readBaselineFromText(os.path.join(path, "baseline"))

    return links_dict


def computeBaselinFromMode(db, linktb, recordtb):
    sql = "SELECT linkid from %s group by 1" % linktb
    linksid = db.executeSql(sql, True, True)
    tmp = []
    schema_name = options["schema"]
    # round value
    sql = (
        "create table %s.tempround as select round(a::numeric,%s) as a, linkid from %s"
        % (schema_name, options["roundm"], recordtb)
    )
    db.executeSql(sql, False, True)
    # compute mode for current link
    for linkid in linksid:
        linkid = linkid[0]

        sql = "SELECT mode(a) AS modal_value FROM %s.tempround where linkid=%s;" % (
            schema_name,
            linkid,
        )
        resu = db.executeSql(sql, True, True)[0][0]
        tmp.append(str(linkid) + "," + str(resu) + "\n")

    sql = "drop table %s.tempround" % (schema_name)
    db.executeSql(sql, False, True)
    try:
        io0 = open(os.path.join(path, "baseline"), "wr")
        io0.writelines(tmp)
        io0.close()
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    try:
        io1 = open(os.path.join(path, "compute_precip_info"), "wr")
        io1.write("mode|" + options["aw"])
        io1.close
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))


def computeBaselineFromTime(db):
    #################################################################
    ##@function for reading file of intervals or just one moments when dont raining.##
    ##@format of input file(with key interval):
    ##  interval
    ##  2013-09-10 04:00:00
    ##  2013-09-11 04:00:00
    ##
    ##@just one moment or moments
    ##  2013-09-11 04:00:00
    ##  2013-09-11 04:00:00
    ################################################################
    ##@typestr choose statistical method for baseline computing.
    ## typestr='avg'
    ## typestr='mode'
    ## typestr='quantile'
    ################################################################
    bpath = options["baseltime"]
    interval = False
    tmp = []
    mark = []
    st = ""

    ############### AVG ####################
    if options["statfce"] == "avg":
        try:
            f = open(bpath, "r")
            ##parse input file
            for line in f:
                st = st + line.replace("\n", "")
                if "i" in line.split("\n")[0]:  # get baseline form interval

                    fromt = f.next()
                    st += fromt.replace("\n", "")
                    tot = f.next()
                    ##validate input data
                    if not isTimeValid(fromt) or not isTimeValid(tot):
                        grass.fatal("Input data is not valid. Parameter 'baselitime'")
                    st += tot.replace("\n", "")
                    sql = (
                        "select linkid, avg(txpower-rxpower)as a from record where time >='%s' and time<='%s' group by linkid order by 1"
                        % (fromt, tot)
                    )
                    resu = db.executeSql(sql, True, True)
                    tmp.append(resu)

                else:  # get baseline one moment
                    time = line.split("\n")[0]
                    ##validate input data
                    if not isTimeValid(time):
                        grass.fatal("Input data is not valid. Parameter 'baselitime'")
                    time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                    st += str(time).replace("\n", "")
                    fromt = time + timedelta(seconds=-60)
                    tot = time + timedelta(seconds=+60)
                    sql = (
                        "select linkid, avg(txpower-rxpower)as a from record where time >='%s' and time<='%s' group by linkid order by 1"
                        % (fromt, tot)
                    )
                    resu = db.executeSql(sql, True, True)
                    tmp.append(resu)

                    continue
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

        mydict = {}
        mydict1 = {}
        i = True
        ## sum all baseline per every linkid from get baseline dataset(next step avg)
        for dataset in tmp:
            mydict = {int(rows[0]): float(rows[1]) for rows in dataset}
            if i:
                mydict1 = mydict
                i = False
                continue
            for link, a in dataset:
                mydict1[link] += mydict[link]

        length = len(tmp)
        links = len(tmp[0])
        i = 0
        ##compute avq(divide sum by num of datasets)
        for dataset in tmp:
            for link, a in dataset:
                i += 1
                mydict1[link] = mydict1[link] / length
                if i == links:
                    break
            break

        ##write values to baseline file
        writer = csv.writer(open(os.path.join(path, "baseline"), "wr"))
        for key, value in mydict1.items():
            writer.writerow([key, value])

    ############### MODE or QUANTILE ####################
    elif options["statfce"] == "mode" or options["statfce"] == "quantile":
        try:
            f = open(bpath, "r")
            ##parse input file

            for line in f:

                # print_message(line)
                st = st + line.replace("\n", "")
                if "i" in line.split("\n")[0]:  # get baseline form interval

                    fromt = f.next()
                    st += fromt.replace("\n", "")
                    tot = f.next()

                    ##validate input data
                    if not isTimeValid(fromt) or not isTimeValid(tot):
                        grass.fatal("Input data is not valid. Parameter 'baselitime'")
                    st += tot.replace("\n", "")
                    sql = (
                        "select linkid, txpower-rxpower as a from record where time >='%s' and time<='%s'"
                        % (fromt, tot)
                    )
                    resu = db.executeSql(sql, True, True)
                    resu += resu

                else:  # get baseline one moment
                    time = line.split("\n")[0]
                    if not isTimeValid(time):
                        grass.fatal("Input data is not valid. Parameter 'baselitime'")
                    time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                    st += str(time).replace("\n", "")
                    fromt = time + timedelta(seconds=-60)
                    tot = time + timedelta(seconds=+60)

                    sql = (
                        "select linkid, txpower-rxpower as a from record where time >='%s' and time<='%s'"
                        % (fromt, tot)
                    )
                    resu = db.executeSql(sql, True, True)

                    resu += resu

                    continue
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

        tmp.append(resu)
        table_mode_tmp = "mode_tmp"
        sql = "create table %s.%s ( linkid integer,a real);" % (
            schema_name,
            table_mode_tmp,
        )
        db.executeSql(sql, False, True)
        c = 0
        ##write values to flat file
        try:
            io = open(os.path.join(path, "mode_tmp"), "wr")
            c = 0
            for it in tmp:
                for i in it:
                    a = str(i[0]) + "|" + str(i[1]) + "\n"
                    io.write(a)
                    c += 1
            io.close()
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

        ##update table
        try:
            io1 = open(os.path.join(path, "mode_tmp"), "r")
            db.copyfrom(io1, "%s.%s" % (schema_name, table_mode_tmp))
            io1.close()
            os.remove(os.path.join(path, "mode_tmp"))
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

        recname = schema_name + "." + table_mode_tmp

        if options["statfce"] == "mode":
            computeBaselinFromMode(db, recname, recname)

        if options["statfce"] == "quantile":
            computeBaselineFromQuentile(db, recname, recname)

        sql = "drop table %s.%s" % (schema_name, table_mode_tmp)
        db.executeSql(sql, False, True)

    ##write  unique mark to file
    try:
        io1 = open(os.path.join(path, "compute_precip_info"), "wr")
        st = st + "|" + options["aw"]
        io1.write(st)
        io1.close
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))


def computeBaselineFromQuentile(db, linktb, recordtb):
    quantile = options["quantile"]
    link_num = db.count("link")
    sql = "SELECT linkid from %s group by linkid" % linktb
    linksid = db.executeSql(sql, True, True)
    tmp = []
    # for each link  compute baseline
    for linkid in linksid:
        linkid = linkid[0]
        sql = (
            "Select\
            max(a) as maxAmount\
            , avg(a) as avgAmount\
            ,quartile\
            FROM (SELECT a, ntile(%s) over (order by a) as quartile\
            FROM %s where linkid=%s ) x\
            GROUP BY quartile\
            ORDER BY quartile\
            limit 1"
            % (quantile, recordtb, linkid)
        )

        resu = db.executeSql(sql, True, True)[0][0]
        tmp.append(str(linkid) + "," + str(resu) + "\n")

    try:
        io0 = open(os.path.join(path, "baseline"), "wr")
        io0.writelines(tmp)
        io0.close()
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    try:
        io1 = open(os.path.join(path, "compute_precip_info"), "wr")
        io1.write("quantile" + quantile + "|" + options["aw"])
        io1.close
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))


def readBaselineFromText(pathh):
    with open(pathh, mode="r") as infile:
        reader = csv.reader(infile, delimiter=",")
        mydict = {float(rows[0]): float(rows[1]) for rows in reader}
    return mydict


###########################
##   GRASS work


def grassWork():
    database = options["database"]
    user = options["user"]
    password = options["password"]
    mapset = grass.gisenv()["MAPSET"]

    dbConnGrass(database, user, password)

    try:
        io = open(os.path.join(path, "linkpointsname"), "r")
        points = io.read()
        io.close
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    points_schema = schema_name + "." + points
    points_ogr = points + "_ogr"

    grass.run_command(
        "v.in.ogr",
        input="PG:",
        layer=points_schema,
        output=points_ogr,
        overwrite=True,
        flags="t",
        type="point",
        key="linkid",
        quiet=True,
    )

    points_nat = points + "_nat"

    # if vector already exits, remove dblink (original table)
    if grass.find_file(points_nat, element="vector")["fullname"]:
        grass.run_command(
            "v.db.connect", map=points_nat, flags="d", layer="1", quiet=True
        )
        grass.run_command(
            "v.db.connect", map=points_nat, flags="d", layer="2", quiet=True
        )

    grass.run_command(
        "v.category",
        input=points_ogr,
        output=points_nat,
        option="transfer",
        overwrite=True,
        layer="1,2",
        quiet=True,
    )

    grass.run_command(
        "v.db.connect",
        map=points_nat,
        table=points_schema,
        key="linkid",
        layer="2",
        quiet=True,
    )

    if not flags["q"]:
        grass.run_command(
            "v.in.ogr",
            input="PG:",
            layer="link",
            output="link",
            flags="t",
            type="line",
            quiet=True,
        )

        grass.run_command(
            "g.region",
            vect="link",
            res="00:00:01",
            n="n+ 00:00:20",
            w="w-00:00:20",
            e="e+00:00:20",
            s="s-00:00:20",
            quiet=True,
        )
    # 00:00:1
    try:
        with open(os.path.join(path, "l_timewindow"), "r") as f:
            for win in f.read().splitlines():

                win = schema_name + "." + win
                grass.run_command(
                    "v.db.connect",
                    map=points_nat,
                    table=win,
                    key="linkid",
                    layer="1",
                    quiet=True,
                )
                # sys.exit()
                if options["isettings"]:
                    precipInterpolationCustom(points_nat, win)
                else:
                    precipInterpolationDefault(points_nat, win)

                # remove connection to 2. layer
                grass.run_command(
                    "v.db.connect", map=points_nat, layer="1", flags="d", quiet=True
                )

    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))


def precipInterpolationCustom(points_nat, win):
    # grass.run_command('v.surf.rst',input=points_nat,zcolumn = attribute_col,elevation=out, overwrite=True)
    itype = options["interpolation"]
    attribute_col = "precip_mm_h"
    out = win + "_" + itype + "_custom"
    istring = options["isettings"]
    eval(istring)
    grass.run_command("r.colors", map=out, rules=options["color"], quiet=True)


def precipInterpolationDefault(points_nat, win):
    itype = options["interpolation"]
    attribute_col = "precip_mm_h"
    out = win + "_" + itype

    if itype == "rst":
        grass.run_command(
            "v.surf.rst",
            input=points_nat,
            zcolumn=attribute_col,
            elevation=out,
            overwrite=True,
            quiet=True,
        )

    elif itype == "bspline":
        grass.run_command(
            "v.surf.bspline",
            input=points_nat,
            column=attribute_col,
            raster_output=out,
            overwrite=True,
            quiet=True,
        )
    else:
        grass.run_command(
            "v.surf.idw",
            input=points_nat,
            column=attribute_col,
            output=out,
            overwrite=True,
            quiet=True,
        )

    grass.run_command("r.colors", map=out, rules=options["color"], quiet=True)

    # grass.mapcalc("$out1=if($out2<0,null(),$out3)",out1=out,out2=out,out3=out,
    #                    overwrite=True)


###########################
##   Precipitation compute


def computePrecip(db):
    print_message("Preparing database for computing precipitation...")
    Awx = options["aw"]
    Aw = float(Awx)
    ##nuber of link and record in table link
    xx = db.count("record")
    link_num = db.count("link")
    ##select values for computing
    sql = (
        " select time, txpower-rxpower as a,lenght,polarization,frequency,linkid from %s order by recordid limit %d ; "
        % (record_tb_name, xx)
    )
    resu = db.executeSql(sql, True, True)

    sql = "create table %s.%s ( linkid integer,time timestamp, precip real);" % (
        schema_name,
        comp_precip,
    )
    db.executeSql(sql, False, True)

    # save name of result table for next run without compute precip

    ##optimalization of commits
    db.setIsoLvl(0)

    try:
        io = open(os.path.join(path, "precip"), "wr")
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    ##choose baseline source (quantile, user values, ) get dict linkid, baseline
    links_dict = getBaselDict(db)
    ##check if baseline from text is correct
    if len(links_dict) < link_num:

        sql = "select linkid from link"
        links = db.executeSql(sql, True, True)
        for link in links:
            # print_message(type(link))
            if not link[0] in links_dict:
                print_message("Linkid= %s is missing in txtfile" % str(link[0]))
                print_message("Link not included in computation")
        print_message(
            'HINT-> Missing values "linkid,baseline," in text file. Link probably getting ERROR "-99.9" in selected time interval\n or you omitted values in input  text. You can add value manualy into the file and than use method "read baseline from file"'
        )

    print_message("Computing precipitation...")

    recordid = 1
    temp = []
    for record in resu:
        # if missing baseline. Link will be skip
        if record[5] in links_dict and (record[4] / 1000000) > 10:
            # coef_a_k[alpha, k]
            coef_a_k = computeAlphaK(record[4], record[3])

            # read value from dictionary
            baseline_decibel = links_dict[record[5]]
            # final precipiatation is R1
            Ar = record[1] - baseline_decibel - Aw
            if Ar > 0:

                yr = Ar / (record[2] / 1000)
                R1 = (yr / coef_a_k[1]) ** (1 / coef_a_k[0])
            else:
                R1 = 0
            # string for output flatfile

            out = str(record[5]) + "|" + str(record[0]) + "|" + str(R1) + "\n"
            temp.append(out)
            recordid += 1

    ##write values to flat file
    try:
        io.writelines(temp)
        io.close()
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e))

    print_message("Writing precipitation to database...")
    io1 = open(os.path.join(path, "precip"), "r")
    db.copyfrom(io1, "%s.%s" % (schema_name, comp_precip))
    io1.close()
    os.remove(os.path.join(path, "precip"))


def makeTimeWin(db, typeid, table):
    print_message("Creating time windows %s..." % typeid)
    # @function sumPrecip make db views for all timestamps

    sum_precip = options["interval"]
    if sum_precip == "minute":
        tcc = 60
    elif sum_precip == "hour":
        tcc = 3600
    else:
        tcc = 86400

    ##summing values per (->user)timestep interval
    view_db = typeid + "_" + randomWord(3)
    sql = "CREATE %s %s.%s as select\
        %s ,round(avg(precip)::numeric,3) as precip_mm_h, date_trunc('%s',time)\
        as time  FROM %s.%s GROUP BY %s, date_trunc('%s',time)\
        ORDER BY time" % (
        view_statement,
        schema_name,
        view_db,
        typeid,
        sum_precip,
        schema_name,
        table,
        typeid,
        sum_precip,
    )
    data = db.executeSql(sql, False, True)
    stamp = ""
    stamp1 = ""

    ##remove ignored linkid

    #    if options['lignore'] and not isTableExist(db,schema_name,'rgauge'):
    if options["lignore"]:
        lipath = options["lignore"]
        stamp = lipath
        try:
            with open(lipath, "r") as f:
                for link in f.read().splitlines():
                    sql = "DELETE from %s.%s where %s=%s " % (
                        schema_name,
                        view_db,
                        typeid,
                        link,
                    )
                    db.executeSql(sql, False, True)

        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

    ##num of rows
    record_num = db.count("%s.%s" % (schema_name, view_db))
    ##set first and last timestamp
    # get first timestamp
    sql = "select time from %s.%s limit 1" % (schema_name, view_db)
    timestamp_min = db.executeSql(sql)[0][0]
    # get last timestep
    sql = "select time from  %s.%s offset %s" % (schema_name, view_db, record_num - 1)
    timestamp_max = db.executeSql(sql)[0][0]

    ##check if set time by user is in dataset time interval
    if options["fromtime"]:
        from_time = datetime.strptime(options["fromtime"], "%Y-%m-%d %H:%M:%S")
        if timestamp_min > from_time:
            print_message("'Fromtime' value is not in dataset time interval")
        else:
            timestamp_min = from_time

    if options["totime"]:
        to_time = datetime.strptime(options["totime"], "%Y-%m-%d %H:%M:%S")
        if timestamp_max < to_time:
            print_message("'Totime' value is not in dataset time interval")
        else:
            timestamp_max = to_time

    ##save first and last timewindow to file. On first line file include time step "minute","hour"etc
    if typeid == "linkid":
        try:
            io1 = open(os.path.join(path, "time_window_info"), "wr")
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))
        io1.write(
            sum_precip
            + "|"
            + str(timestamp_min)
            + "|"
            + str(timestamp_max)
            + stamp
            + stamp1
        )
        io1.close

    time_const = 0
    i = 0
    temp = []
    tgrass_interpol = []
    tgrass_vector = []
    # set prefix
    prefix = "l"
    if typeid == "gaugeid":
        prefix = "g"

    cur_timestamp = timestamp_min
    print_message(
        "from "
        + str(timestamp_min)
        + " to "
        + str(timestamp_max)
        + " per "
        + options["interval"]
        + ". It can take a time..."
    )

    ##make timewindows from time interval
    ###############################################
    while cur_timestamp <= timestamp_max:

        # create name of view
        a = time.strftime(
            "%Y_%m_%d_%H_%M", time.strptime(str(cur_timestamp), "%Y-%m-%d %H:%M:%S")
        )
        view_name = "%s%s%s" % (prefix, view, a)
        vw = view_name + "\n"
        temp.append(vw)

        # format for t.register ( temporal grass)
        if typeid == "linkid":
            tgrass = (
                schema_name
                + "."
                + view_name
                + "_"
                + options["interpolation"]
                + "|"
                + str(cur_timestamp)
                + "\n"
            )
            tgrass_interpol.append(tgrass)

            tgrass = view_name + "|" + str(cur_timestamp) + "\n"
            tgrass_vector.append(tgrass)

        else:

            tgrass = view_name + "|" + str(cur_timestamp) + "\n"
            tgrass_vector.append(tgrass)

        # create view
        sql = (
            "CREATE table %s.%s as select * from %s.%s where time=(timestamp'%s'+ %s * interval '1 second')"
            % (schema_name, view_name, schema_name, view_db, timestamp_min, time_const)
        )
        data = db.executeSql(sql, False, True)

        # compute cur_timestamp (need for loop)
        sql = "select (timestamp'%s')+ %s* interval '1 second'" % (cur_timestamp, tcc)
        cur_timestamp = db.executeSql(sql)[0][0]

        # go to next time interval
        time_const += tcc

    ##write values to flat file
    if typeid == "linkid":
        try:
            io2 = open(os.path.join(path, "l_timewindow"), "wr")
            io2.writelines(temp)
            io2.close()
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))
    else:
        try:
            io2 = open(os.path.join(path, "g_timewindow"), "wr")
            io2.writelines(temp)
            io2.close()
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

    # make textfile for t.register input
    if typeid == "linkid":
        filename = (
            "timewin_%s" % prefix
            + "_"
            + str(timestamp_min).replace(" ", "_")
            + "|"
            + str(timestamp_max).replace(" ", "_")
        )
        try:
            io3 = open(os.path.join(path, filename), "wr")
            io3.writelines(tgrass_interpol)
            io3.close()
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

        filename = (
            "timewin_%s" % prefix
            + "vec_"
            + str(timestamp_min).replace(" ", "_")
            + "|"
            + str(timestamp_max).replace(" ", "_")
        )
        try:
            io3 = open(os.path.join(path, filename), "wr")
            io3.writelines(tgrass_vector)
            io3.close()
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

    else:
        filename = (
            "timewin_%s" % prefix
            + "vec_"
            + str(timestamp_min).replace(" ", "_")
            + "|"
            + str(timestamp_max).replace(" ", "_")
        )
        try:
            io4 = open(os.path.join(path, filename), "wr")
            io4.writelines(tgrass_vector)
            io4.close()
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e))

    ##drop temp table

    sql = "drop table %s.%s" % (schema_name, view_db)


def computeAlphaK(freq, polarization):
    """@RECOMMENDATION ITU-R P.838-3
    Specific attenuation model for rain for use in prediction methods
    γR = kR^α
    return kv and αv (vertical polarization)
    return kh and αh (horizontal polarization)
    """
    freq /= 1000000
    if freq < 10 or freq > 100:
        print_message(freq)
        print_message(polarization)

    if polarization == "h":
        # Coefficients for kH    1

        aj_kh = (-5.33980, -0.35351, -0.23789, -0.94158)
        bj_kh = (-0.10008, 1.26970, 0.86036, 0.64552)
        cj_kh = (1.13098, 0.45400, 0.15354, 0.16817)
        mk_kh = -0.18961
        ck_kh = 0.71147

        # Coefficients for αH    3
        aj_ah = (-0.14318, 0.29591, 0.32177, -5.37610, 16.1721)
        bj_ah = (1.82442, 0.77564, 0.63773, -0.96230, -3.29980)
        cj_ah = (-0.55187, 0.19822, 0.13164, 1.47828, 3.43990)
        ma_ah = 0.67849
        ca_ah = -1.95537
        kh = 0
        ah = 0
        # kh.. coefficient k of horizontal polarization
        for j in range(0, len(aj_kh)):
            frac_kh = -math.pow(((math.log10(freq) - bj_kh[j]) / cj_kh[j]), 2)
            kh += aj_kh[j] * math.exp(frac_kh)

        kh = 10 ** (kh + mk_kh * math.log10(freq) + ck_kh)

        # ah.. coefficient α of horizontal polarization
        for j in range(0, len(aj_ah)):
            frac_ah = -math.pow(((math.log10(freq) - bj_ah[j]) / cj_ah[j]), 2)
            ah += aj_ah[j] * math.exp(frac_ah)

        ah = ah + ma_ah * math.log10(freq) + ca_ah

        return (ah, kh)
    else:
        # Coefficients for kV    2
        aj_kv = [-3.80595, -3.44965, -0.39902, 0.50167]
        bj_kv = [0.56934, -0.22911, 0.73042, 1.07319]
        cj_kv = [0.81061, 0.51059, 0.11899, 0.27195]
        mk_kv = -0.16398
        ck_kv = 0.63297

        # Coefficients for αV   4
        aj_av = [-0.07771, 0.56727, -0.20238, -48.2991, 48.5833]
        bj_av = [2.33840, 0.95545, 1.14520, 0.791669, 0.791459]
        cj_av = [-0.76284, 0.54039, 0.26809, 0.116226, 0.116479]
        ma_av = -0.053739
        ca_av = 0.83433
        kv = 0
        av = 0
        # kv.. coefficient k of vertical polarization
        for j in range(0, len(aj_kv)):
            frac_kv = -math.pow(((math.log10(freq) - bj_kv[j]) / cj_kv[j]), 2)
            kv += aj_kv[j] * math.exp(frac_kv)

        kv = 10 ** (kv + mk_kv * math.log10(freq) + ck_kv)

        # av.. coefficient α of vertical polarization
        for j in range(0, len(aj_av)):
            frac_av = -math.pow(((math.log10(freq) - bj_av[j]) / cj_av[j]), 2)
            av += aj_av[j] * math.exp(frac_av)

        av = av + ma_av * math.log10(freq) + ca_av

        return (av, kv)


###########################
##   main


def main():
    global schema_name, path
    schema_name = options["schema"]
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "tmp_%s" % schema_name
    )

    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

    ##connect to database by python lib psycopg
    db = dbConnPy()

    # check database if is prepare
    if not isAttributExist(db, "public", "link", "geom"):
        firstRun(db)

    ##drop working schema and remove temp folder
    if flags["r"]:
        removeTemp(db)

    ##print first and last timestamp
    if flags["p"]:
        printTime(db)

    ##check if timestamp is in valid format
    if options["fromtime"]:
        if not isTimeValid(options["fromtime"]):
            grass.fatal(
                "Timestamp 'fromtime' is not valid. Use format'YYYY-MM-DD H:M:S' "
            )

    if options["totime"]:
        if not isTimeValid(options["totime"]):
            grass.fatal(
                "Timestamp 'fromtime' is not valid. Use format'YYYY-MM-DD H:M:S' "
            )

    ##check settings of baseline is valid
    if (
        not options["baseltime"]
        and not options["baselfile"]
        and not (flags["p"] or flags["r"])
    ):
        grass.fatal(
            "For compute precipitation is necessity to set parametr 'baseltime' or 'baselfile'"
        )

    ##compute precipitation
    if not isCurrSetP():
        sql = "drop schema IF EXISTS %s CASCADE" % schema_name
        shutil.rmtree(path)
        os.makedirs(path)
        db.executeSql(sql, False, True)
        sql = "CREATE SCHEMA %s" % schema_name
        db.executeSql(sql, False, True)
        computePrecip(db)

    ##make time windows

    if not isCurrSetT():
        ##import raingauges
        if options["rgauges"]:
            print_message("Reading rain gauges files")
            sql = "CREATE SCHEMA  if not exists %s " % schema_name
            db.executeSql(sql, False, True)
            file_list = getFilesInFoldr(options["rgauges"])
            for fil in file_list:
                path1 = os.path.join(options["rgauges"], fil)
                print_message(path1)
                readRaingauge(db, path1)

        if os.path.exists(os.path.join(path, "l_timewindow")):
            with open(os.path.join(path, "l_timewindow"), "r") as f:
                for win in f.read().splitlines():
                    sql = "drop table IF EXISTS %s.%s " % (schema_name, win)
                    db.executeSql(sql, False, True)

        if os.path.exists(os.path.join(path, "l_timewindow")):
            with open(os.path.join(path, "g_timewindow"), "r") as f:
                for win in f.read().splitlines():
                    sql = "drop table IF EXISTS %s.%s " % (schema_name, win)
                    db.executeSql(sql, False, True)

        makeTimeWin(db, "linkid", comp_precip)
        if isTableExist(db, schema_name, "rgauge"):
            makeTimeWin(db, "gaugeid", comp_precip_gauge)

    ##interpol. points
    step = options["step"]  # interpolation step per meters
    step = float(step)
    new_table_name = "linkpoints" + str(step).replace(".0", "")
    curr_table_name = ""
    try:
        io2 = open(os.path.join(path, "linkpointsname"), "r")
        curr_table_name = io2.readline()
        io2.close
    except:
        pass
    # check if table exist or if exist with different step or if -> interpol. one more time
    if (
        not (isTableExist(db, schema_name, curr_table_name))
        or new_table_name != curr_table_name
    ):
        if not options["step"]:
            grass.fatal('Missing value for "step" for interpolation')
        intrpolatePoints(db)

    ##grass work
    if flags["g"]:
        grassWork()

    print_message("DONE")


if __name__ == "__main__":
    options, flags = grass.parser()

main()
