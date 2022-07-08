#!/usr/bin/env python
# -*- coding: utf-8

from math import sin, cos, atan2, degrees, tan, sqrt
from datetime import datetime
from datetime import timedelta
import shutil
import importlib
import time
import math
import sys
import os
from subprocess import PIPE

from pgwrapper import pgwrapper as pg
from core.gcmd import RunCommand
from grass.pygrass.modules import Module
import grass.script as grass
from mw_util import *

timeMes = MeasureTime()
import logging

logger = logging.getLogger("mwprecip.Computing")


class PointInterpolation:
    try:
        psycopg2 = importlib.import_module("psycopg2")
    except ModuleNotFoundError as e:
        msg = e.msg
        grass.fatal(
            _(
                "Unable to load python <{0}> lib (requires lib "
                "<{0}> being installed).".format(msg.split("'")[-2])
            )
        )

    def __init__(self, database, step, methodDist=False):
        timeMes.timeMsg("Interpolating points along lines...")
        self.step = float(step)
        self.database = database
        self.method = methodDist  # 'p' - points, else distance

        nametable = self.database.linkPointsVecName + str(step).replace(
            ".0", ""
        )  # create name for table with interopol. points.
        sql = "DROP TABLE IF EXISTS %s.%s" % (
            self.database.schema,
            nametable,
        )  # if table exist than drop
        self.database.connection.executeSql(sql, False, True)

        sql = (
            "CREATE table %s.%s "
            "(linkid integer,long real,lat real,point_id serial PRIMARY KEY) "
            % (self.database.schema, nametable)
        )  # create table where will be intrpol. points.
        self.database.connection.executeSql(sql, False, True)
        a = 0  # index of latlong
        x = 0  # id in table with interpol. points

        points = []
        vecLoader = VectorLoader(self.database)
        linksPoints = vecLoader.selectLinks(True)
        for record in linksPoints:
            # latlong.append(tmp)  # add [lon1 lat1 lon2 lat2] to list latlong
            linkid = record[0]  # linkid value
            dist = record[1] * 1000  # distance between nodes on current link
            lat1 = record[3]
            lon1 = record[2]
            lat2 = record[5]
            lon2 = record[4]
            az = self.bearing(
                lat1, lon1, lat2, lon2
            )  # compute approx. azimut on sphere
            a += 1

            point = list()
            if self.method:  # #compute per distance interval(points)
                while (
                    abs(dist) > step
                ):  # compute points per step while is not achieve second node on link
                    lat1, lon1, az, backBrg = self.destinationPointWGS(
                        lat1, lon1, az, step
                    )  # return interpol. point and set current point as starting point(for next loop), also return azimut for next point
                    dist -= step  # reduce distance
                    x += 1

                    point.append(linkid)
                    point.append(lon1)
                    point.append(lat1)
                    point.append(x)

                    points.append(point)

            else:  # # compute by dividing distance to sub-distances
                step1 = dist / (step + 1)
                for i in range(
                    0, int(step)
                ):  # compute points per step while is not achieve second node on link
                    lat1, lon1, az, backBrg = self.destinationPointWGS(
                        lat1, lon1, az, step1
                    )
                    # return interpol. point and set current point as starting point(for next loop), also return azimut for next point
                    x += 1

                    point.append(linkid)
                    point.append(lon1)
                    point.append(lat1)
                    point.append(x)

                    points.append(point)

        resultPointsAlongLines = vecLoader.getASCIInodes(points)
        vecLoader.grass_vinASCII(
            resultPointsAlongLines, self.database.linkPointsVecName
        )

        sql = "ALTER TABLE %s.%s DROP COLUMN lat" % (
            self.database.schema,
            nametable,
        )  # remove latitde column from table
        self.database.connection.executeSql(sql, False, True)
        sql = "alter table %s.%s drop column long" % (
            self.database.schema,
            nametable,
        )  # remove longtitude column from table
        self.database.connection.executeSql(sql, False, True)
        timeMes.timeMsg("Interpolating points along lines-done")

    def destinationPointWGS(self, lat1, lon1, brng, s):
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

    def bearing(self, lat1, lon1, lat2, lon2):
        lat1 = math.radians(float(lat1))
        lon1 = math.radians(float(lon1))
        lat2 = math.radians(float(lat2))
        lon2 = math.radians(float(lon2))
        dLon = lon2 - lon1

        y = math.sin(dLon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
            lat2
        ) * math.cos(dLon)
        brng = math.degrees(math.atan2(y, x))

        return (brng + 360) % 360


class VectorLoader:
    def __init__(self, database):
        self.db = database

    def selectNodes(self):
        sql = "SELECT nodeid, lat, long FROM %s.node;" % self.db.dataSchema
        return self.db.connection.executeSql(sql, True, True)

    def selectRainGagues(self):
        sql = "SELECT gaugeid, lat, long FROM %s.%s;" % (
            self.db.dataSchema,
            self.db.rgaugeTableName,
        )
        return self.db.connection.executeSql(sql, True, True)

    def getASCIInodes(self, selectedPoints):
        newline = "\n"
        pointsASCI = "VERTI:\n"
        for point in selectedPoints:
            pointsASCI += (
                "P 1 1" + newline
            )  # primitive P(point), num of coordinates,num of categories
            pointsASCI += (
                str(point[2]) + " " + str(point[1]) + newline
            )  # coordination of point
            pointsASCI += (
                "1" + " " + str(point[0]) + newline
            )  # first layer, cat=id of point(nodeid)
        return pointsASCI

    def selectLinks(self, distance=False):
        if not distance:
            sql = (
                "SELECT l.linkid, n1.lat, n1.long ,n2.lat, n2.long \
                FROM %s.node as n1\
                JOIN %s.link as l \
                ON n1.nodeid=fromnodeid\
                JOIN %s.node as n2 \
                ON n2.nodeid= tonodeid;"
                % (self.db.dataSchema, self.db.dataSchema, self.db.dataSchema)
            )
        else:
            sql = (
                "SELECT l.linkid,l.lenght, n1.lat, n1.long ,n2.lat, n2.long \
                FROM %s.node as n1\
                JOIN %s.link as l \
                ON n1.nodeid=fromnodeid\
                JOIN %s.node as n2 \
                ON n2.nodeid= tonodeid;"
                % (self.db.dataSchema, self.db.dataSchema, self.db.dataSchema)
            )
        return self.db.connection.executeSql(sql, True, True)

    def getASCIIlinks(self, selectedLinks):
        newline = "\n"
        linksASCII = "VERTI:\n"
        for link in selectedLinks:
            linksASCII += (
                "L 2 1" + newline
            )  # primitive L(line), num of coordinates,num of categories
            linksASCII += str(link[2]) + " " + str(link[1]) + newline
            linksASCII += str(link[4]) + " " + str(link[3]) + newline
            linksASCII += (
                "1" + " " + str(link[0]) + newline
            )  # first layer, cat=id of point(nodeid)
        return linksASCII

    def grass_vinASCII(self, asciiStr, outMapName):
        currDir = os.path.dirname(os.path.realpath(__file__))
        tmpFile = os.path.join(currDir, "tmp")
        f = open(tmpFile, "w+")
        f.write(asciiStr)
        f.close()
        grass.run_command(
            "v.in.ascii",
            input=tmpFile,
            format="standard",
            output=outMapName,
            quiet=True,
            overwrite=True,
        )
        os.remove(tmpFile)


class RainGauge:
    def __init__(self, database, pathfile):
        self.db = database
        self.rgpath = pathfile
        self.schemaPath = database.pathworkSchemaDir
        self.schema = database.schema
        self.gaugeid = None
        self.lat = None
        self.lon = None

        file_list = getFilesInFoldr(self.rgpath)
        for file in file_list:
            path = os.path.join(self.rgpath, file)
            self.readRaingauge(path)

    def readRaingauge(self, path):
        # get coordinates from header and id
        try:
            with open(path, "rb") as f:
                self.gaugeid = int(f.next())
                self.lat = float(f.next())
                self.lon = float(f.next())
            f.close()
        except IOError as e:
            grass.error("I/O error({}): {}".format(e.errno, e))

        gaugeTMPfile = "gauge_tmp"
        removeLines(
            old_file=path,
            new_file=os.path.join(self.schemaPath, gaugeTMPfile),
            start=0,
            end=3,
        )
        # #prepare list of string for copy to database
        try:
            with open(os.path.join(self.schemaPath, gaugeTMPfile), "rb") as f:
                data = f.readlines()
                tmp = []
                for line in data:
                    stri = str(self.gaugeid) + "," + line
                    tmp.append(stri)
                f.close()
        except IOError as e:
            grass.error("I/O error({0}): {1}".format(errno, strerror))

        # write list of string to database
        try:
            with open(os.path.join(self.schemaPath, gaugeTMPfile), "w+") as io:
                io.writelines(tmp)
                io.close()
        except IOError as e:
            grass.error("I/O error({0}): {1}".format(errno, strerror))

        if not isTableExist(self.db.connection, self.schema, self.db.rgaugeTableName):
            # #create table for raingauge stations
            sql = (
                "create table %s.%s (gaugeid integer PRIMARY KEY,lat real,long real ) "
                % (self.schema, self.db.rgaugeTableName)
            )
            self.db.connection.executeSql(sql, False, True)

            # # create table for rain gauge records
            sql = (
                ' CREATE TABLE %s.%s \
                  (gaugeid integer NOT NULL,\
                  "time" timestamp without time zone NOT NULL,\
                  precip real,\
                  CONSTRAINT recordrg PRIMARY KEY (gaugeid, "time"),\
                  CONSTRAINT fk_record_rgague FOREIGN KEY (gaugeid)\
                  REFERENCES %s.%s (gaugeid) MATCH SIMPLE\
                  ON UPDATE NO ACTION ON DELETE NO ACTION)'
                % (self.schema, self.db.rgaugRecord, self.schema, self.db.rgaugRecord)
            )
            self.db.connection.executeSql(sql, False, True)

            # insert rain gauge station to table
            sql = "Insert into %s.%s ( gaugeid , lat , long) values (%s , %s , %s) " % (
                self.schema,
                self.db.rgaugeTableName,
                self.gaugeid,
                self.lat,
                self.lon,
            )
            self.db.executeSql(sql, False, True)
            # copy records in database
            io = open(os.path.join(self.schemaPath, gaugeTMPfile), "r")
            self.db.copyfrom(io, "%s.%s" % (self.schema, self.db.rgaugRecord), ",")
            io.close()
            os.remove(os.path.join(self.schemaPath, gaugeTMPfile))


class Baseline:
    def __init__(
        self,
        type="noDryWin",
        pathToFile=None,
        statFce="quantile",
        quantile=97,
        roundMode=3,
        aw=0,
    ):
        if quantile is None:
            quantile = 97
            logger.info("Quantile is not defined. Default is 97")
        self.quantile = quantile
        if roundMode is None:
            roundMode = 3
            logger.info("Round is not defined. Default is 3 decimal places")
        self.roundMode = roundMode
        if aw is None:
            aw = 0
            logger.info("Antena wetting value is not defined. Default is 0")
        self.aw = aw
        self.pathToFile = pathToFile
        self.type = type
        self.statFce = statFce


class TimeWindows:
    def __init__(
        self,
        database,
        IDtype,
        sumStep,
        startTime=None,
        endTime=None,
        linksIgnored=False,
        linksOnly=False,
        links=None,
        linksMap=None,
    ):
        self.linksMap = linksMap  # name of map  selected by user. in this case the links vector map is changed
        self.startTime = startTime
        self.endTime = endTime
        self.sumStep = sumStep
        self.database = database
        self.db = database.connection
        self.path = database.pathworkSchemaDir
        self.schema = database.schema
        self.typeID = IDtype
        self.viewStatement = database.viewStatement
        self.tbName = database.computedPrecip
        self.links = links  #
        self.linksIgnored = linksIgnored  # if true: remove self.link else:
        self.linksOnly = linksOnly  # compute only links

        self.status = {}
        self.status["bool"] = False
        self.status["msg"] = "Done"

        self.viewDB = None
        self.intervalStr = None
        self.timestamp_max = None
        self.timestamp_min = None
        self.temporalRegPath = None
        self.numWindows = 0

        if self.sumStep == "minute":
            self.intervalStr = 60

        elif self.sumStep == "hour":
            self.intervalStr = 3600
        else:
            self.intervalStr = 86400

    def createWin(self):
        self.sumValues()
        # self.setTimestamp()

        if self.linksMap is not None:
            self.database.linkVecMapName = self.linksMap
        elif self.linksIgnored:
            self.removeLinksIgnore()
        elif self.linksOnly:
            self.removeLinksOthers()
        self.crateTimeWin()

    def sumValues(self):
        ##summing values per (->user)timestep interval
        self.viewDB = "computed_precip_sum"
        sql = (
            "CREATE %s %s.%s as  \
               SELECT %s ,round(avg(precip)::numeric,3) as %s, date_trunc('%s',time)as time  \
               FROM %s.%s \
               GROUP BY %s, date_trunc('%s',time)\
               ORDER BY time"
            % (
                self.viewStatement,
                self.schema,
                self.viewDB,
                self.typeID,
                self.database.precipColName,
                self.sumStep,
                self.schema,
                self.tbName,
                self.typeID,
                self.sumStep,
            )
        )
        self.database.connection.executeSql(sql, False, True)

        sql = (
            "ALTER %s %s.%s\
                ADD %s VARCHAR(11) "
            % (self.viewStatement, self.schema, self.viewDB, self.database.colorCol)
        )
        self.database.connection.executeSql(sql, False, True)

    def setTimestamp(self):
        self.timestamp_min = self.database.minTimestamp()
        self.timestamp_max = self.database.maxTimestamp()

        # check if set time by user is in dataset time interval
        if self.startTime is not None:
            self.startTime = datetime.strptime(str(self.startTime), "%Y-%m-%d %H:%M:%S")

            if self.timestamp_min > self.startTime:
                self.logMsg("'startTime' value is not in temporal dataset ")
                return False
            else:
                self.timestamp_min = self.startTime
        self.timestamp_min = roundTime(self.timestamp_min, self.intervalStr)

        if self.endTime is not None:
            self.endTime = datetime.strptime(str(self.endTime), "%Y-%m-%d %H:%M:%S")
            if self.timestamp_max < self.endTime:
                self.logMsg("'endTime' value is not in temporal dataset")
                return False
            else:
                self.timestamp_max = self.endTime
        self.timestamp_max = roundTime(self.timestamp_max, self.intervalStr)

        return True

    def removeLinksIgnore(self):
        """Remove ignored links"""
        """
        try:
            with open(self.ignoredIDpath, 'r') as f:
                for link in f.read().splitlines():
                    sql = "DELETE FROM %s.%s WHERE %s=%s " % (self.schema, self.viewDB, self.typeID, link)
                    self.database.connection.executeSql(sql, False, True)
        except IOError as e:
            grass.fatal('Cannot open file with ingored files')
        """
        for link in self.links.split(","):
            sql = "DELETE FROM %s.%s WHERE %s=%s " % (
                self.schema,
                self.viewDB,
                self.typeID,
                link,
            )
            self.database.connection.executeSql(sql, False, True)

    def removeLinksOthers(self):
        """Remove not selected links"""
        sql = "CREATE TABLE %s.linktmp(linkid int NOT NULL PRIMARY KEY) " % self.schema
        self.database.connection.executeSql(sql, False, True)

        for link in self.links.split(","):
            sql = "INSERT INTO  %s.linktmp values (%s);" % (
                self.schema,
                link,
            )  # TODO OPTIMALIZE
            self.database.connection.executeSql(sql, False, False)

        sql = "DROP TABLE %s.linktmp " % self.schema
        self.database.connection.executeSql(sql, False, True)

        sql = (
            "DELETE FROM %s.%s WHERE NOT EXISTS\
              (SELECT %s FROM   %s.linktmp \
               WHERE %s.%s.%s=linksonly.%s)"
            % (
                self.schema,
                self.viewDB,
                self.typeID,
                self.schema,
                self.schema,
                self.viewDB,
                self.typeID,
                self.typeID,
            )
        )
        self.database.connection.executeSql(sql, False, True)

    def crateTimeWin(self):
        timeMes.timeMsg("creating time windows")
        # timeMes.timeMsg()
        time_const = 0
        nameList = []
        tgrass_vector = []
        cur_timestamp = self.timestamp_min
        prefix = "l"
        if self.typeID == "gaugeid":
            prefix = "g"

        timeMes.timeMsg(
            "from "
            + str(self.timestamp_min)
            + " to "
            + str(self.timestamp_max)
            + " per "
            + self.sumStep
        )
        # make timewindows from time interval
        while cur_timestamp < self.timestamp_max:
            self.numWindows += 1
            # create name of
            a = time.strftime(
                "%Y_%m_%d_%H_%M", time.strptime(str(cur_timestamp), "%Y-%m-%d %H:%M:%S")
            )
            view_name = "%s%s%s" % (prefix, self.database.viewStatement, a)
            vw = view_name + "\n"
            nameList.append(vw)

            # text format for t.register ( temporal grass)
            if self.typeID == "linkid":
                tgrass = view_name + "|" + str(cur_timestamp) + "\n"
                tgrass_vector.append(tgrass)
            else:
                tgrass = view_name + "|" + str(cur_timestamp) + "\n"
                tgrass_vector.append(tgrass)

            sql = (
                "CREATE TABLE %s.%s as\
                   SELECT * from %s.%s \
                   WHERE time=(timestamp'%s'+ %s * interval '1 second')"
                % (
                    self.schema,
                    view_name,
                    self.schema,
                    self.viewDB,
                    self.timestamp_min,
                    time_const,
                )
            )

            data = self.database.connection.executeSql(sql, False, True)
            # compute current timestamp (need for loop)

            # sql = "SELECT (timestamp'%s')+ %s* interval '1 second'" % (cur_timestamp, self.intervalStr)
            # cur_timestamp = self.database.connection.executeSql(sql)[0][0]
            # rint cur_timestamp

            cur_timestamp = cur_timestamp + self.intervalStr * timedelta(seconds=1)

            # go to next time interval
            time_const += self.intervalStr

        if self.typeID == "linkid":
            TMPname = "l_timewindow"
        else:
            TMPname = "g_timewindow"
        try:
            io2 = open(os.path.join(self.path, TMPname), "w+")
            io2.writelines(nameList)
            io2.close()
        except IOError as e:
            grass.warning(
                "Cannot write temporal registration file  %s"
                % os.path.join(self.path, TMPname)
            )

        timeMes.timeMsg("creating time windows-done")

    def logMsg(self, msg):
        if self.status.get("msg") == "Done":
            self.status["msg"] = ""
        self.status["msg"] += msg + "\n"
        grass.warning(msg)


class Computor:
    try:
        np = importlib.import_module("numpy")
    except ModuleNotFoundError as e:
        msg = e.msg
        grass.fatal(
            _(
                "Unable to load python <{0}> lib (requires lib "
                "<{0}> being installed).".format(msg.split("'")[-2])
            )
        )

    def __init__(self, baseline, timeWin, database, exportData):
        self.awConst = baseline.aw
        self.database = database
        self.baseline = baseline
        self.timeWin = timeWin
        self.baselineDict = None
        self.status = {}
        self.status["bool"] = False
        self.status["msg"] = "Done"

        self.cleanDatabase()

        if self.computePrecip(
            exportData["getData"], exportData["dataOnly"]
        ):  # if export data only
            self.timeWin.createWin()
            self.status["bool"] = True

    def GetStatus(self):
        return self.status.get("bool"), self.status.get("msg")

    def ExportData(self):
        pass

    def cleanDatabase(self):
        sql = "DROP schema IF EXISTS %s CASCADE" % self.database.schema
        shutil.rmtree(self.database.pathworkSchemaDir)
        os.makedirs(self.database.pathworkSchemaDir)
        self.database.connection.executeSql(sql, False, True)
        sql = "CREATE schema %s" % self.database.schema
        self.database.connection.executeSql(sql, False, True)

    def getBaselDict(self):
        """@note  returns disct - key:linkid"""
        baseline = self.baseline
        database = self.database
        tMin = self.timeWin.timestamp_min
        tMax = self.timeWin.timestamp_max
        startTime = self.timeWin.startTime
        endTime = self.timeWin.endTime

        def computeBaselinFromMode(recordTable):
            sql = "SELECT linkid from %s group by 1" % recordTable
            linksid = database.connection.executeSql(sql, True, True)

            # round value
            sql = (
                "CREATE TABLE %s.tempround as SELECT round(a::numeric,%s) as a, linkid FROM %s"
                % (database.schema, baseline.roundMode, recordTable)
            )
            database.connection.executeSql(sql, False, True)

            # compute mode for current link
            tmp = []
            for linkid in linksid:
                linkid = linkid[0]
                sql = (
                    "SELECT mode(a) AS modal_value FROM %s.tempround where linkid=%s;"
                    % (database.schema, linkid)
                )
                resu = database.connection.executeSql(sql, True, True)[0][0]
                tmp.append(str(linkid) + "," + str(resu) + "\n")

            sql = "DROP TABLE %s.tempround" % database.schema
            database.connection.executeSql(sql, False, True)
            io0 = open(os.path.join(database.pathworkSchemaDir, "baseline"), "w+")
            io0.writelines(tmp)
            io0.close()

            # io1 = open(os.path.join(database.pathworkSchemaDir, "compute_precip_info"), 'w+')
            # io1.write('mode|' + str(baseline.aw))
            # io1.close

        def computeBaselineFromTime():
            def chckTimeValidity(tIn):
                # print tIn
                tIn = str(tIn).replace("\n", "")
                try:
                    tIn = datetime.strptime(tIn, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.info("Wrong datetime format")
                    return False
                if tIn > tMax or tIn < tMin:
                    return False
                return True

            # ################################
            # @function for reading file of intervals or just one moments when dont raining.#
            # @format of input file(with key interval):
            # interval
            # 2013-09-10 04:00:00
            # 2013-09-11 04:00:00
            #
            # @just one moment or moments
            # 2013-09-11 04:00:00
            # 2013-09-11 04:00:00
            # ###############################
            # @typestr choose statistical method for baseline computing.
            # typestr='avg'
            # typestr='mode'
            # typestr='quantile'
            ################################
            tmp = []
            st = ""
            # print baseline.statFce
            ######## AVG #########
            if baseline.statFce == "avg":

                if baseline.type == "noDryWin":
                    if baseline.statFce == "avg":
                        sql = (
                            "SELECT linkid, avg(a) FROM %s.record \
                               WHERE time >='%s' AND time<='%s' group by linkid order by 1"
                            % (database.schema, startTime, endTime)
                        )
                        resu = database.connection.executeSql(sql, True, True)
                        tmp.append(resu)
                else:
                    try:
                        # print baseline.pathToFile
                        f = open(baseline.pathToFile, "r")
                    except IOError as e:
                        # print baseline.pathToFile
                        grass.warning(
                            "Path to file with dry-window definiton not exist; %s"
                            % baseline.pathTofile
                        )
                    for line in f:
                        st += line.replace("\n", "")
                        if "i" in line.split("\n")[0]:  # get baseline form interval
                            fromt = f.next()
                            if not chckTimeValidity(fromt):
                                return False
                            st += fromt.replace("\n", "")
                            tot = f.next()
                            if not chckTimeValidity(tot):
                                return False
                            # validate input data
                            if not isTimeValid(fromt) or not isTimeValid(tot):
                                grass.warning(
                                    "Input data are not valid. Parameter 'baselitime'"
                                )
                                return False

                            st += tot.replace("\n", "")
                            sql = (
                                "SELECT linkid, avg(a) FROM %s.record \
                                   WHERE time >='%s' AND time<='%s' group by linkid order by 1"
                                % (database.schema, fromt, tot)
                            )
                            resu = database.connection.executeSql(sql, True, True)
                            tmp.append(resu)

                        else:  # baseline one moment
                            time = line.split("\n")[0]
                            # validate input data
                            if not isTimeValid(time):
                                grass.warning(
                                    "Input data are not valid. Parameter 'baselitime'"
                                )
                                return False
                            try:
                                time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                logger.info("Wrong datetime format")
                                return False
                            st += str(time).replace("\n", "")
                            fromt = time + timedelta(seconds=-60)
                            if not chckTimeValidity(fromt):
                                return False
                            tot = time + timedelta(seconds=+60)
                            if not chckTimeValidity(tot):
                                return False
                            sql = (
                                "SELECT linkid, avg(a) FROM %s.record \
                                   WHERE time >='%s' AND time<='%s' group by linkid order by 1"
                                % (database.schema, fromt, tot)
                            )
                            resu = database.connection.executeSql(sql, True, True)
                            tmp.append(resu)
                            continue

                mydict1 = {}
                i = True
                # print(tmp)
                # sum all baseline per every linkid from get baseline dataset(next step avg)
                for dataset in tmp:
                    mydict = {int(rows[0]): float(rows[1]) for rows in dataset}
                    if i is True:
                        mydict1 = mydict
                        i = False
                        continue
                    for link in dataset:
                        mydict1[link] += mydict[link]

                length = len(tmp)
                links = len(tmp[0])
                i = 0
                # print mydict1
                # compute avg(divide sum by num of datasets)
                for dataset in tmp:
                    for link in dataset:
                        i += 1
                        # print link
                        # print mydict1[link]#TODO chck
                        mydict1[link[0]] /= length
                        if i == links:
                            break
                    break

                # write values to baseline file
                writer = csv.writer(
                    open(os.path.join(database.pathworkSchemaDir, "baseline"), "w+")
                )
                for key, value in mydict1.items():
                    writer.writerow([key, value])

            ######## MODE or QUANTILE ##########
            elif baseline.statFce == "mode" or baseline.statFce == "quantile":
                # print 'mode***'

                # parse input file
                if baseline.type == "noDryWin":
                    sql = (
                        "SELECT linkid, a from  %s.record WHERE time >='%s' and time<='%s'"
                        % (database.schema, startTime, endTime)
                    )
                    resu = database.connection.executeSql(sql, True, True)
                    database.connection.executeSql(sql, False, True)
                else:
                    try:
                        # print baseline.pathToFile
                        f = open(baseline.pathToFile, "r")
                    except IOError as e:
                        grass.warning(
                            "Path to file with dry-window definiton not exist"
                        )
                        return False
                    for line in f:
                        st += line.replace("\n", "")
                        if "i" in line.split("\n")[0]:  # get baseline  intervals
                            fromt = f.next()
                            if not chckTimeValidity(fromt):
                                return False
                            st += fromt.replace("\n", "")
                            tot = f.next()
                            if not chckTimeValidity(tot):
                                return False
                            # validate input data
                            if not isTimeValid(fromt) or not isTimeValid(tot):
                                grass.warning(
                                    "Input data are not valid. Parameter 'baselitime'"
                                )
                                return False
                            st += tot.replace("\n", "")
                            sql = (
                                "SELECT linkid, a from  %s.record WHERE time >='%s' and time<='%s'"
                                % (database.schema, fromt, tot)
                            )
                            resu = database.connection.executeSql(sql, True, True)
                            resu += resu

                        else:  # get baseline one moment
                            time = line.split("\n")[0]
                            if not isTimeValid(time):
                                grass.warning(
                                    "Input data are not valid. Parameter 'baselitime'"
                                )
                                return False
                            try:
                                time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                logger.info("Wrong datetime format")
                                return False
                            st += str(time).replace("\n", "")
                            fromt = time + timedelta(seconds=-60)
                            if not chckTimeValidity(fromt):
                                return False
                            tot = time + timedelta(seconds=+60)
                            if not chckTimeValidity(tot):
                                return False

                            sql = (
                                "SELECT linkid,  a from %s.record WHERE time >='%s' and time<='%s'"
                                % (database.schema, fromt, tot)
                            )
                            resu = database.connection.executeSql(sql, True, True)
                            resu += resu
                            continue
                tmp.append(resu)
                table_tmp = baseline.statFce + "_tmp"
                sql = "CREATE TABLE %s.%s ( linkid integer,a real);" % (
                    database.schema,
                    table_tmp,
                )
                database.connection.executeSql(sql, False, True)

                # write values to flat file
                io = open(os.path.join(database.pathworkSchemaDir, table_tmp), "w+")
                c = 0
                for it in tmp:
                    for i in it:
                        a = str(i[0]) + "|" + str(i[1]) + "\n"
                        io.write(a)
                        c += 1
                io.close()

                # update table
                try:
                    io1 = open(os.path.join(database.pathworkSchemaDir, table_tmp), "r")
                    database.connection.copyfrom(
                        io1, "%s.%s" % (database.schema, table_tmp)
                    )
                    io1.close()
                    os.remove(os.path.join(database.pathworkSchemaDir, table_tmp))
                except IOError as e:
                    grass.warning("Cannot open <%s> file" % table_tmp)
                    return False

                recname = database.schema + "." + table_tmp

                if baseline.statFce == "mode":
                    computeBaselinFromMode(recname)

                if baseline.statFce == "quantile":
                    computeBaselineFromQuentile(recname)

                sql = "DROP TABLE %s.%s" % (database.schema, table_tmp)
                database.connection.executeSql(sql, False, True)

            return True

        """
        def computeBaselineFromQuentile(recordTable):
            sql = "SELECT linkid from %s group by linkid" % recordTable
            linksid = database.connection.executeSql(sql, True, True)
            tmp = []
            # for each link  compute baseline
            for linkid in linksid:
                linkid = linkid[0]
                sql = "SELECT\
                        max(a) as maxAmount,\
                        avg(a) as avgAmount,\
                        quartile\
                        FROM (SELECT a, ntile(%s) OVER (order by a) as quartile\
                        FROM %s where linkid=%s ) x\
                        GROUP BY quartile\
                        ORDER BY quartile\
                        limit 1" % (baseline.quantile, recordTable, linkid)


                resu = database.connection.executeSql(sql, True, True)

                resu = resu[0][0]
                tmp.append(str(linkid) + ',' + str(resu) + '\n')

            io0 = open(os.path.join(database.pathworkSchemaDir, "baseline"), 'w+')
            io0.writelines(tmp)
            io0.close()
        """

        def Quantile(data, q, precision=1.0):
            """
            Returns the q'th percentile of the distribution given in the argument
            'data'. Uses the 'precision' parameter to control the noise level.
            """
            # data = self.np.random.normal(size=2000000)
            q = float(q) / 100
            N, bins = self.np.histogram(data, bins=precision * self.np.sqrt(len(data)))
            norm_cumul = 1.0 * N.cumsum() / len(data)
            ret = bins[norm_cumul > q][0]
            # print "error in  %s quantile"%q, ((1.0*(data < ret).sum() / len(data)) -q)

            return ret

        def computeBaselineFromQuentile(recordTable):
            sql = "SELECT linkid from %s group by linkid" % recordTable
            linksid = database.connection.executeSql(sql, True, True)
            tmp = []
            # for each link  compute baseline
            for linkid in linksid:
                linkid = linkid[0]
                sql = "SELECT a from %s where linkid=%s" % (recordTable, linkid)
                resu = database.connection.executeSql(sql, True, True)
                data = self.np.array(resu)
                # data=[item for sublist in data for item in sublist]#merge lists
                # print data
                # quantileRes=Quantile(data, baseline.quantile)

                quantileRes = self.np.percentile(
                    data, (100 - float(baseline.quantile)) / 100
                )
                tmp.append(str(linkid) + "," + str(quantileRes) + "\n")
            io0 = open(os.path.join(database.pathworkSchemaDir, "baseline"), "w+")
            io0.writelines(tmp)
            io0.close()

        def readBaselineFromText(path):
            with open(path, mode="r") as infile:
                reader = csv.reader(infile, delimiter=",")
                mydict = {float(rows[0]): float(rows[1]) for rows in reader}
            return mydict

        if self.baseline.type == "values":
            # print 'valuesDirectly'
            self.baselineDict = readBaselineFromText(self.baseline.pathTofile)

        elif self.baseline.type == "fromDryWin":
            logger.info(
                'Computing baselines "dry window" "%s"...' % self.baseline.statFce
            )
            if computeBaselineFromTime():
                self.baselineDict = readBaselineFromText(
                    os.path.join(database.pathworkSchemaDir, "baseline")
                )
                return True
            else:
                return False

        elif self.baseline.type == "noDryWin":
            logger.info(
                'Computing baselines "no dry window" "%s"...' % self.baseline.statFce
            )
            if computeBaselineFromTime():
                self.baselineDict = readBaselineFromText(
                    os.path.join(database.pathworkSchemaDir, "baseline")
                )
                return True
            else:
                return False

    def logMsg(self, msg, err=False):
        if self.status.get("msg") == "Done":
            self.status["msg"] = ""
        self.status["msg"] += msg + "\n"
        if not err:
            grass.warning(msg)
        else:
            grass.fatal(msg)

    def computePrecip(self, getData=False, dataOnly=False):
        def checkValidity(freq, polarization):
            if freq < 10000000:
                return False

            if polarization is "V" or polarization is "H":
                return True
            return False

        if self.baseline.aw is None:
            self.baseline.aw = 0
        Aw = float(self.baseline.aw)

        link_num = self.database.connection.count("link")
        compPrecTab = "%s.%s" % (self.database.schema, self.database.computedPrecip)
        # self.timeWin.sumValues()
        if not self.timeWin.setTimestamp():
            self.logMsg("Out of available time interval", 1)
            return False
        timeMes.timeMsg("Quering data")

        sql = (
            "SELECT linkid,lenght,polarization,frequency \
                FROM %s.link"
            % self.database.dataSchema
        )
        linkResu = self.database.connection.executeSql(sql, True, True)
        linksDict = {}

        # fill dict by links metadata-> much faster than tables join
        for link, leng, pol, freq in linkResu:
            linksInfo = []
            linksInfo.append(leng)
            linksInfo.append(pol)
            linksInfo.append(freq)
            linksDict[link] = linksInfo

        """
        sql = "SELECT linkid,time,txpower-rxpower as a \
              FROM %s.record \
              WHERE time >= '%s' AND\
                    time <= '%s' \
                    ORDER by recordid;" % \
              (self.database.dataSchema,
               self.timeWin.timestamp_min,
               self.timeWin.timestamp_max)
        resu = self.database.connection.executeSql(sql, True, True)
        """
        sql = (
            "CREATE TABLE %s.record AS (SELECT linkid,time,txpower-rxpower as a \
              FROM %s.record \
              WHERE time >= '%s' AND\
                    time <= '%s' \
                    ORDER by recordid);"
            % (
                self.database.schema,
                self.database.dataSchema,
                self.timeWin.timestamp_min,
                self.timeWin.timestamp_max,
            )
        )
        self.database.connection.executeSql(sql, False, True)

        sql = "SELECT * from %s.record" % self.database.schema
        resu = self.database.connection.executeSql(sql, True, True)

        timeMes.timeMsg("Quering data-done")
        """
        sql = "SELECT n2.time, n2.txpower-n2.rxpower as a,n1.lenght,n1.polarization,n1.frequency,n1.linkid\
                FROM %s.link AS n1 \
                JOIN %s.record AS n2 ON n1.linkid = n2.linkid \
                WHERE n2.linkid = n1.linkid AND\
                time >= '%s' AND\
                time <= '%s' \
                ORDER by n2.recordid;" % \
              (self.database.dataSchema,
               self.database.dataSchema,
               self.timeWin.timestamp_min,
               self.timeWin.timestamp_max)

        resu = self.database.connection.executeSql(sql, True, True)
        """

        sql = (
            "CREATE TABLE %s ( linkid integer,time timestamp, precip real);"
            % compPrecTab
        )
        self.database.connection.executeSql(sql, False, True)

        # optimalization of commits
        # self.database.connection.setIsoLvl(0)  #TODO dont know what is that

        # choose baseline source (quantile, user values, ) get dict linkid, baseline
        timeMes.timeMsg("Computing baseline")
        if not self.getBaselDict():
            self.logMsg("Dry interval is out of defined time interval(from,to)", 1)
            return False
        if len(self.baselineDict) == 0:
            self.logMsg("Baselines coputation faild. Check dry windows", 1)
            return False
        timeMes.timeMsg("Computing baseline-done")

        # check if baseline from text is correct
        if len(self.baselineDict) < link_num:
            sql = "SELECT linkid FROM link"
            links = self.database.connection.executeSql(sql, True, True)
            for link in links:
                # logger.info(type(link))
                if not link[0] in self.baselineDict:
                    logger.info("Linkid= %s is missing in txtfile" % str(link[0]))
            logger.info(
                'Missing values "linkid,baseline," in text file. Data are not available in dry interval(baseline) .'
            )

        temp = []
        errLinkList = []
        timeMes.timeMsg("Computing precipitation")
        skippedList = []
        for record in resu:
            curLinkData = linksDict[record[0]]  # record[0] is linkid
            if curLinkData[1] is None:
                if not record[0] in skippedList:
                    curLinkData[1] = "V"  # TODO REMOVE THIS!!!!!!!!!!!!!!!!

            if record[0] in self.baselineDict:
                """
                coef_a_k[alpha, k]
                record[0] is linkid
                record[1] is time
                record[2] is tx-rx
                curLinkData[0] is lenght
                curLinkData[1] is polarization
                curLinkData[2] is frequency HZ
                """
                if checkValidity(curLinkData[2], curLinkData[1]):
                    coef_a_k = self.computeAlphaK(curLinkData[2], curLinkData[1])
                else:
                    if record[0] not in errLinkList:
                        errLinkList.append(record[0])
                        self.logMsg("Data of link <%s> are not valid" % record[0])
                        continue

                # read value from dictionary
                baseline_decibel = self.baselineDict[record[0]]

                # final precipiatation is R1
                Am = record[2] - baseline_decibel - Aw
                yl = Am / curLinkData[0]
                aa = yl / coef_a_k[1]
                if aa < 0:
                    aa *= -1
                    R1 = aa ** (1 / coef_a_k[0])
                    R1 *= -1
                else:
                    R1 = aa ** (1 / coef_a_k[0])

                # string for output flatfile
                out = str(record[0]) + "|" + str(record[1]) + "|" + str(R1) + "\n"
                temp.append(out)

        timeMes.timeMsg("Computing precipitation-done")
        pathExp = os.path.join(self.database.pathworkSchemaDir, "precip")
        io = open(pathExp, "w+")
        io.writelines(temp)
        io.close()
        # if getData:
        logger.info("Computed data has been saved to <%s>" % pathExp)
        logger.info("File structure is <linkid> <time> <precipitation>")

        logger.info("Writing computed precipitation to database...")
        io1 = open(os.path.join(self.database.pathworkSchemaDir, "precip"), "r")
        self.database.connection.copyfrom(io1, compPrecTab)

        if dataOnly:
            return False

        return True

    def computeAlphaK(self, freq, polarization):
        """@RECOMMENDATION ITU-R P.838-3
        Specific attenuation model for rain for use in prediction methods
        γR = kR^α
        return kv and αv (vertical polarization)
        return kh and αh (horizontal polarization)
        """
        freq /= 1000000

        if polarization == "H":
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

            return ah, kh

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

            return av, kv


class GrassLayerMgr:
    def __init__(self, database, color=None, rules=None):
        self.color = color
        self.rules = rules
        self.database = database
        map = self.connectDBaLayers()

        if color is not None or rules is not None:
            self.makeRGB(map)

    def makeRGB(self, map):
        timeMes.timeMsg("Creating RGB column in database")
        try:
            if self.rules not in [None, ""]:
                for lay in range(1, self.getNumLayer(self.database.linkVecMapName), 1):
                    Module(
                        "v.colors",
                        map=map,
                        use="attr",
                        column=self.database.precipColName,
                        rules=self.rules,
                        rgb_column=self.database.colorCol,
                        quiet=True,
                        layer=lay,
                    )

            if self.color not in [None, ""]:
                for lay in range(1, self.getNumLayer(self.database.linkVecMapName), 1):
                    Module(
                        "v.colors",
                        map=map,
                        use="attr",
                        column=self.database.precipColName,
                        color=self.color,
                        rgb_column=self.database.colorCol,
                        quiet=True,
                        layer=lay,
                    )

            timeMes.timeMsg("Creating RGB column in database-done")
        except Exception as e:
            grass.warning("v.color error < %s>" % e)

    def getNumLayer(self, map):
        numLay = Module(
            "v.category", input=map, option="layers", quiet=True, stdout_=PIPE
        )

        return len(numLay.outputs.stdout.splitlines())

    def getNumLinks(self, map):
        numLink = Module("v.db.connect", map=map, quiet=True, flags="g", stdout_=PIPE)
        return len(numLink.outputs.stdout.splitlines())

    def unlinkLayer(self, map):
        for l in range(1, int(self.getNumLinks(map)), 1):
            RunCommand("v.db.connect", map=map, flags="d", layer=l, quiet=True)

        for l in range(1, int(self.getNumLayer(map)), 1):
            RunCommand(
                "v.edit",
                map=map,
                tool="catdel",
                layer=l,
                cats="1-10000",  # TODO
                quiet=True,
            )

    def connectDBaLayers(self):
        timeMes.timeMsg("Connecting tables to maps")
        inputMap = self.database.linkVecMapName
        if "@" in self.database.linkVecMapName:
            self.database.linkVecMapName = self.database.linkVecMapName.split("@")[0]
        self.database.linkVecMapName += "_%s" % self.database.schema

        try:
            f = open(os.path.join(self.database.pathworkSchemaDir, "l_timewindow"), "r")
        except:
            grass.warning("Cannot connect tables(time-windows)  to vector layer")
            return None

        if grass.find_file(self.database.linkVecMapName, element="vector")["fullname"]:
            self.unlinkLayer(self.database.linkVecMapName)
        layerNum = 0
        layStr = ""
        for win in f.read().splitlines():
            layerNum += 1
            layStr += str(layerNum) + ","

        layStr = layStr[:-1]
        f.close()
        RunCommand(
            "v.category",
            input=inputMap,
            output=self.database.linkVecMapName,
            option="transfer",
            overwrite=True,
            layer=layStr,
            flags="t",
            quiet=True,
        )

        try:
            f = open(os.path.join(self.database.pathworkSchemaDir, "l_timewindow"), "r")
        except:
            grass.warning("Cannot connect tables(time-windows)  to vector layer")
        layerNum = 0
        for win in f.read().splitlines():
            layerNum += 1
            win = self.database.schema + "." + win
            logger.info(win)
            RunCommand(
                "v.db.connect",
                driver="pg",
                map=self.database.linkVecMapName,
                table=win,
                key="linkid",
                layer=layerNum,
                overwrite=True,
                quiet=True,
            )
        f.close()
        timeMes.timeMsg("Connecting tables to maps-done")
        return self.database.linkVecMapName


class GrassTemporalMgr:
    def __init__(self, database, timeWinConf):
        self.database = database
        self.timeWinConf = timeWinConf
        self.datasetName = database.schema
        self.datasetTitle = "MW time dataset"
        self.datasetTdescription = (
            " IDtype=%s,"
            "sumStep=%s,"
            "startTime=%s,"
            "endTime='%s"
            % (
                timeWinConf.typeID,
                timeWinConf.sumStep,
                timeWinConf.startTime,
                timeWinConf.endTime,
            )
        )
        self.createTimedataset()
        self.registerMaps()

    def createTimedataset(
        self,
        datasetName=None,
        datasetTitle=None,
        datasetTdescription=None,
        temporalType="absolute",
        semanticType="mean",
    ):
        if datasetName is not None:
            self.datasetName = datasetName
        if datasetTitle is not None:
            self.datasetTitle = datasetTitle
        if datasetTdescription is not None:
            self.datasetTdescription = datasetTdescription

        RunCommand(
            "t.create",
            type="stvds",
            output=self.datasetName,
            title=self.datasetTitle,
            description="test mw ",
            temporaltype=temporalType,
            semantictype=semanticType,
            overwrite=True,
        )
        # getErrorMsg=True)
        # print ret
        # print err

    def registerMaps(self):
        timeMes.timeMsg("Registring maps to temporal database")
        gisenv_grass = grass.gisenv()
        timeOfLay = self.timeWinConf.timestamp_min
        regTMP = ""
        regFilePath = os.path.join(self.database.pathworkSchemaDir, "temporal_reg_file")

        for layer in range(1, self.timeWinConf.numWindows + 1, 1):
            mapsName = str(
                self.database.linkVecMapName
                + ":"
                + str(layer)
                + "@"
                + gisenv_grass["MAPSET"]
            )
            timeOfLay += timedelta(seconds=self.timeWinConf.intervalStr)
            regTMP += mapsName + "|" + str(timeOfLay) + "\n"

        io1 = open(regFilePath, "w+")
        io1.writelines(regTMP), io1.close
        io1.close()
        logger.info("datasetName %s" % self.datasetName)
        logger.info(regFilePath)

        RunCommand(
            "t.register",
            input=self.datasetName,
            type="vector",
            file=regFilePath,
            overwrite=True,
        )

        timeMes.timeMsg("Registring maps to temporal database-done")


class Database:
    def __init__(
        self,
        name=None,
        user=None,
        password=None,
        host=None,
        port=None,
        nodeVecMapName="node",
        linkVecMapName="link",
        linkPointsVecName="linkPoints",
        workPath=None,
        workSchema=None,
        dataSchema=None,
    ):
        self.dbConnStr = name
        self.dbName = name
        self.user = user
        self.port = port
        self.password = password
        self.host = host
        if workSchema is None:
            workSchema = "tmp_" + randomWord(3)
        self.schema = workSchema
        if dataSchema is None:
            dataSchema = "public"
        self.dataSchema = dataSchema
        self.connection = None
        self.viewStatement = "table"
        self.recordTableName = "record"
        self.computedPrecip = "mw_computed_precip"
        self.computedPrecipGauge = "rgauge_computed_precip"
        self.rgaugRecord = "rgauge_record"
        self.rgaugeTableName = "rgauge"
        self.precipColName = "precip_mm_h"
        self.colorCol = "rgb"

        self.nodeVecMapName = nodeVecMapName
        self.linkVecMapName = linkVecMapName
        self.linkPointsVecName = linkPointsVecName

        self.pathworkSchemaDir = os.path.join(workPath, "profiles", "%s" % self.schema)

        self.pyConnection()
        self.grassConnectionRemote()
        self.grassTemporalConnection("postgres")
        # self.firstPreparation()
        # self.prepareDB()
        # self.prepareDir()

    def minTimestamp(self):
        sql = "SELECT min(time) FROM %s.%s" % (self.dataSchema, self.recordTableName)
        time = self.connection.executeSql(sql)[0][0]
        time = roundTime(time, 30)
        return time

    def maxTimestamp(self):
        sql = "SELECT max(time) FROM  %s.%s" % (self.dataSchema, self.recordTableName)
        time = self.connection.executeSql(sql)[0][0]
        time = roundTime(time, 30)
        return time

    def grassTemporalConnection(self, db="postgres"):
        grass.run_command("t.connect", flags="d")

        """
        if db == 'postgres':
            conninfo = 'dbname=' + self.dbName
            if self.user:
                conninfo += ' user=' + self.user
            if self.password:
                conninfo += ' password=' + self.password
            if self.host:
                conninfo += ' host=' + self.host
            if self.port:
                conninfo += ' port=' + str(self.port)

            if grass.run_command('t.connect',
                                 driver='pg',
                                 database=conninfo) != 0:
                grass.warning("Unable to connect to the database by temporal grass driver.")
                return False  # TODO
        if db == 'sql':
            grass.run_command('t.connect',
                              flags='d')
        """

    def grassConnectionRemote(self):
        self.dbConnStr = self.dbName

        if self.user and not self.password:
            grass.run_command(
                "db.login",
                driver="pg",
                database=self.dbName,
                user=self.user,
                password="",
                overwrite=True,
            )

        elif self.user and self.password:
            if self.port and self.host:
                grass.run_command(
                    "db.login",
                    driver="pg",
                    database=self.dbName,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    overwrite=True,
                )
            elif self.host:
                grass.run_command(
                    "db.login",
                    driver="pg",
                    database=self.dbName,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    overwrite=True,
                )
            else:
                grass.run_command(
                    "db.login",
                    driver="pg",
                    database=self.dbName,
                    user=self.user,
                    password=self.password,
                    overwrite=True,
                )
        else:
            grass.run_command(
                "db.login",
                driver="pg",
                database=self.dbName,
                user="",
                password="",
                overwrite=True,
            )

        if (
            grass.run_command(
                "db.connect", driver="pg", database=self.dbName, overwrite=True
            )
            != 0
        ):
            grass.warning("Unable to connect to the database by grass driver.")

    def pyConnection(self):
        try:
            conninfo = {"dbname": self.dbName}
            if self.user:
                conninfo["user"] = self.user
            if self.password:
                conninfo["passwd"] = self.password
            if self.host:
                conninfo["host"] = self.host
            if self.port:
                conninfo["port"] = self.port
            self.connection = pg(**conninfo)

        except self.psycopg2.OperationalError as e:
            grass.warning(
                "Unable to connect to the database <%s>. %s" % (self.dbName, e)
            )

    def firstPreparation(self):
        if not isAttributExist(self.connection, "public", "link", "lenght"):
            logger.info("Add colum lenght")
            sql = "ALTER TABLE link ADD COLUMN lenght real; "
            self.connection.executeSql(sql, False, True)

            # logger.info("Add colum frequency")
            # sql = "ALTER TABLE link ADD COLUMN frequency real; "
            # self.connection.executeSql(sql, False, True)

            # logger.info("Optimalization of frequency attribute")
            # sql = "UPDATE link\
            # SET frequency = record.frequency\
            # FROM record\
            #        WHERE record.linkid = link.linkid;"
            # self.connection.executeSql(sql, False, True)

            # sql = "ALTER TABLE record DROP COLUMN frequency;"
            # self.connection.executeSql(sql, False, True)

            logger.info("Add function for computing distance ")
            """
            sql=r"CREATE OR REPLACE FUNCTION get_earth_distance1
                (lon1 Float, lat1 Float, lon2 Float, lat2 Float, Radius Float DEFAULT 6387.7)
                RETURNS FLOAT AS '
                -- Convert degrees to radians
                DECLARE K FLOAT := 57.29577951; v_dist FLOAT;
                BEGIN
                -- calculate
                v_dist := (Radius * ACOS((SIN(Lat1 / K) * SIN(Lat2 / K))
                + (COS(Lat1 / K) * COS(Lat2 / K) * COS(Lon2 / K - Lon1 / K))));
                -- Return distance in Km
                RETURN round(CAST (v_dist AS Numeric),3);
                END;
                ' LANGUAGE 'plpgsql';"
            """
            sql = r"CREATE OR REPLACE FUNCTION get_earth_distance1 (lon1 Float, lat1 Float, lon2 Float, lat2 Float, Radius Float DEFAULT 6387.7) RETURNS FLOAT AS ' DECLARE K FLOAT := 57.29577951; v_dist FLOAT; BEGIN v_dist := (Radius * ACOS((SIN(Lat1 / K) * SIN(Lat2 / K)) + (COS(Lat1 / K) * COS(Lat2 / K) * COS(Lon2 / K - Lon1 / K)))); RETURN round(CAST (v_dist AS Numeric),3); END; ' LANGUAGE 'plpgsql';"
            self.connection.executeSql(sql, False, True)

            logger.info("Computing column lenght")
            sql = "UPDATE link SET lenght = get_earth_distance1(n1.long,n1.lat,n2.long,n2.lat) \
                    FROM node AS n1 JOIN \
                    link AS l ON n1.nodeid = fromnodeid \
                    JOIN node AS n2 ON n2.nodeid = tonodeid \
                    WHERE link.linkid = l.linkid; "
            self.connection.executeSql(sql, False, True)

            # logger.info("Add column precip")
            # sql = "ALTER TABLE record ADD COLUMN precip real; "
            # self.connection.executeSql(sql, False, True)

            logger.info("Create sequence")
            sql = "CREATE SEQUENCE serial START 1; "
            self.connection.executeSql(sql, False, True)

            logger.info("Add column recordid")
            sql = "ALTER TABLE record add column recordid integer default nextval('serial'); "
            self.connection.executeSql(sql, False, True)

            logger.info("Create index on recordid")
            sql = "CREATE INDEX idindex ON record USING btree(recordid); "
            self.connection.executeSql(sql, False, True)

            sql = "CREATE INDEX timeindex ON record USING btree (time); "
            self.connection.executeSql(sql, False, True)

            logger.info("Add mode function")
            sql = "CREATE OR REPLACE FUNCTION _final_mode(anyarray)\
                        RETURNS anyelement AS $BODY$ SELECT a FROM unnest($1)\
                        a GROUP BY 1  ORDER BY COUNT(1) DESC, 1 LIMIT 1;\
                        $BODY$ LANGUAGE 'sql' IMMUTABLE;"
            self.connection.executeSql(sql, False, True)

            sql = "CREATE AGGREGATE mode(anyelement) (\
                        SFUNC=array_append, \
                        STYPE=anyarray,\
                        FINALFUNC=_final_mode, \
                        INITCOND='{}');"
            self.connection.executeSql(sql, False, True)

    def prepareDB(self):
        sql = "DROP schema IF EXISTS %s CASCADE" % self.schema
        try:
            shutil.rmtree(self.pathworkSchemaDir)
        except:
            os.makedirs(self.pathworkSchemaDir)
        self.connection.executeSql(sql, False, True)
        sql = "CREATE schema %s" % self.schema
        self.connection.executeSql(sql, False, True)

    def prepareDir(self):
        try:
            os.makedirs(self.pathworkSchemaDir)
        except OSError:
            if not os.path.isdir(self.pathworkSchemaDir):
                raise


"""
def main():
    db = Database(name='tyden')
    convertor = VectorLoader(db)
    # create native vector map(nodes)
    pointsSQL = convertor.selectNodes()
    # print pointsSQL
    pointsASCII = convertor.getASCIInodes(pointsSQL)
    convertor.grass_vinASCII(pointsASCII, db.nodeVecMapName)

    # create native vector map(links)
    linksSQL = convertor.selectLinks()
    linksASCII = convertor.getASCIIlinks(linksSQL)
    convertor.grass_vinASCII(linksASCII, db.linkVecMapName)

    PointInterpolation(2, '', db)
    # sys.exit()
    twin = TimeWindows(IDtype='linkid',
                       sumStep='minute',
                       startTime='2014-10-20 01:00:00',
                       endTime='2014-10-20 04:00:00',  # TODO check input
                       # startTime='2013-09-09 00:00:00',
                       # endTime='2013-09-10 00:00:00',
                       database=db)

    baseline = Baseline(type='fromDryWin',
                        statFce='mode',
                        pathToFile='/home/matt/Dropbox/MV/test_suite/baseltime2.ref',
                        roundMode=3)

    Computor(baseline, twin, db)

    GrassLayerMgr(db)

    # sys.exit()
    GrassTemporalMgr(db, twin)


    #main()
"""
