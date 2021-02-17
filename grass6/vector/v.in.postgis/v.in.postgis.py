#!/usr/bin/python
#-*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       v.in.postgis
# AUTHOR(S):	Mathieu Grelier, 2009 (greliermathieu@gmail.com)
# PURPOSE:      GRASS layer creation from arbitrary PostGIS sql queries
# COPYRIGHT:	(C) 2009 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#%  description: Create a grass layer from any sql query in postgis 
#%  keywords: postgis, db, sql
#%End
#%option
#% key: query
#% type: string
#% description: Any sql query returning a recordset with geometry for each row 
#% required : no
#%end
#%option
#% key: geometryfield
#% type: string
#% answer: the_geom
#% description: Name of the source geometry field (usually defaults to the_geom)
#% required : no
#%end
#%option
#% key: output
#% type: string
#% answer: v_in_postgis
#% description: Name of the imported grass layer (do not use capital letters)
#% required : no
#%end
#%flag
#% key: t
#% description: Run tests and exit
#%end
#%flag
#% key: d
#% description: Import result in grass dbf format (no new table in postgis - if not set, new grass layer attributes will be connected to the result table)
#%end
#%flag
#% key: o
#% description: Use -o for v.in.ogr (override dataset projection)
#%end
#%flag
#% key: g
#% description: Add a gist index to the imported result table in postgis (useless with the d flag)
#%end
#%flag
#% key: l
#% description: Log process info to v.in.postgis.log
#%end

import sys
import os
import re
from subprocess import Popen, PIPE
import traceback

##see http://initd.org/pub/software/psycopg/
import psycopg2 as dbapi2
##see http://trac.osgeo.org/grass/browser/grass/trunk/lib/python
import grass.script as grass

##only needed to use Komodo debugger with Komodo IDE. See http://aspn.activestate.com/ASPN/Downloads/Komodo/RemoteDebugging
#from dbgp.client import brk
##see http://pyunit.sourceforge.net/
import unittest

class GrassPostGisImporter():

    def __init__(self, options, flags):
        ##options
        self.query = options['query']
        self.geometryfield = options['geometryfield'] if options['geometryfield'].strip() != '' else 'the_geom'
        self.output = options['output'] if options['output'].strip() != '' else 'postgis_import'
        ##flags
        self.dbfFlag = True if flags['d'] is True else False
        self.overrideprojFlag = True if flags['o'] is True else False
        self.gistindexFlag = True if flags['g'] is True else False
        self.logOutput = True if flags['l'] is True else False
        ##others
        logfilename = 'v.in.postgis.log'
        self.logfile = os.path.join(os.getenv('LOGDIR'),logfilename) if os.getenv('LOGDIR') else logfilename
        grass.try_remove(self.logfile)
        ##default for grass6 ; you may need to fix this path
        self.grassloginfile = os.path.join(os.getenv('HOME'),'.grasslogin6')
        ##retrieve connection parameters
        self.dbparams = self.__getDbInfos()
        ##set db connection
        self.db = dbapi2.connect(host=self.dbparams['host'], database=self.dbparams['db'], \
user=self.dbparams['user'], password=self.dbparams['pwd'])
        self.cursor = self.db.cursor()
        ## uncomment if not default
        #dbapi2.paramstyle = 'pyformat' 

    def __writeLog(self, log=''):
        """Write the 'log' string to log file."""
        if self.logfile is not None:
            fileHandle = open(self.logfile, 'a')
            log = log + '\n'
            fileHandle.write(log)
            fileHandle.close()

    def __getDbInfos(self):
        """Create a dictionnary with all db params needed by v.in.ogr."""
        try:
            dbString = grass.parse_key_val(grass.read_command('db.connect', flags = 'p'), sep = ':')['database']
            p = re.compile(',')
            dbElems = p.split(dbString)
            host = grass.parse_key_val(dbElems[0], sep = '=')['host']
            db = grass.parse_key_val(dbElems[1], sep = '=')['dbname']
            loginLine = self.executeCommand('sed -n "/pg ' + dbElems[0] + ','\
                                                + dbElems[1] + ' /p" ' + self.grassloginfile, toLog = False, shell = True)
            p = re.compile(' ')
            loginElems = p.split(loginLine)
            user = loginElems[-2].strip()
            password = loginElems[-1].strip()
            dbParamsDict = {'host':host, 'db':db, 'user':user, 'pwd':password}
            return dbParamsDict
        except:
            raise GrassPostGisImporterError("Error while trying to retrieve database information.")

    def executeCommand(self, *args, **kwargs):
        """Command execution method using Popen in two modes : shell mode or not."""
        p = None
        shell = True if 'shell' in kwargs and kwargs['shell'] is True else False
        toLog = True if 'toLog' in kwargs and kwargs['toLog'] is True \
                                                and self.logOutput is True else False
        ##now remove this key as it is not expected by grass.start_command
        if 'toLog' in kwargs:
            del kwargs['toLog']
        command = args[0]
        if shell is True:
            if toLog is True:
                command = command + ' >> ' +  self.logfile
            ##always use redirection on stdout only
            command = command + " 2>&1"
            p = Popen(command, shell = shell, stdout = PIPE)
        else:
            kwargs['stdout'] = PIPE
            kwargs['stderr'] = PIPE
            p = grass.start_command(*args, **kwargs)
        retcode = p.wait()
        message = ''
        if shell is True and toLog is True:
            message = 'Read logfile for details.'
        else:
            com = p.communicate()
            r = re.compile('\n')
            for std in com:
                if std is not None:
                    lines = r.split(std)
                    for elem in lines:
                        message += str(elem).strip() + "\n"
            if toLog is True:
                self.__writeLog(message)
        if retcode == 0:
            return message
        else:
            raise GrassPostGisImporterError(message)

    def printMessage(self, message, type = 'info'):
        """Call grass message function corresponding to type."""
        if type == 'error':
            grass.error(message)
        elif type == 'warning':
            grass.warning(message)
        elif type == 'info' and grass.gisenv()['GRASS_VERBOSE'] > 0:
            grass.info(message)
        if self.logOutput is True:
            self.__writeLog(message)

    def checkLayers(self, output):
        """Test if the grass layer 'output' already exists.
        Note : for this to work with grass6.3, in find_file function from core.py,
        command should be (n flag removed because 6.4 specific):
        s = read_command("g.findfile", element = element, file = name, mapset = mapset)
        """
        self.printMessage("Check layers:")
        ##Test if output vector map already exists.
        testOutput = grass.find_file(output, element = 'vector')
        if testOutput['fullname'] != '':
            if not grass.overwrite() is True:
                raise GrassPostGisImporterError("Vector map " + output + " already exists in mapset search path. \
#Use the --o flag to overwrite.")
            else:
                self.printMessage("Vector map " + output + " will be overwritten.", type = 'warning')
        return True

    def checkComment(self, output):
        """Test if a table with the 'output' existing in PostGis have been created by the importer."""
        testIfTableNameAlreadyExistsQuery = "SELECT CAST(tablename AS text) FROM pg_tables \
                                            WHERE schemaname='public' \
                                            AND CAST(tablename AS text)='" + output + "'"
        self.cursor.execute(testIfTableNameAlreadyExistsQuery)
        rows = self.cursor.fetchone()
        if rows is not None and len(rows) > 0:
            testCheckCommentQuery = "SELECT obj_description((SELECT c.oid FROM pg_catalog.pg_class c \
                                    WHERE c.relname='" + output + "'), 'pg_class') AS comment"
            self.cursor.execute(testCheckCommentQuery)
            comment = self.cursor.fetchone()
            if comment is not None and len(comment) == 1:
                comment = comment[0]
            if comment == "created with v.in.postgis.py":
                self.cursor.execute("DROP TABLE " + output)
            else:
                raise GrassPostGisImporterError("ERROR: a table with the name " + output + " already exists \
                                                and was not created by this script.")
        return True

    def createPostgresTableFromQuery(self, output, query):
        """Create a table in postgresql populated with results from the query, and tag it.
        We will later be able to figure out if this table was created by the importer (see checkLayers())
        """
        try:
            createTableQuery = "CREATE TABLE " + str(output) + " AS " + str(query)
            if self.logOutput is True:
                self.__writeLog("Try to import data:")
                self.__writeLog(createTableQuery)
            self.cursor.execute(createTableQuery)
            self.cursor.execute("SELECT COUNT (*) FROM " + output)
            rows = self.cursor.fetchall()[0][0]
            if rows == 0:
                raise GrassPostGisImporterError("Query returned no results.")
            addCommentQuery = "COMMENT ON TABLE " + output + " IS 'created with v.in.postgis.py'"
            self.cursor.execute(addCommentQuery)
        except GrassPostGisImporterError:
            ##no results
            raise
        except:
            ##query execution error
            raise GrassPostGisImporterError("An error occurred during sql import. Check your connection \
                                            to the database and your sql query.")

    def addCategory(self, output):
        """Add a category column in the result table.
        With the pg driver (not the dbf one), v.in.ogr need a 'cat' column for index creation 
        if -d flag wasn't not selected, can't import if query result already have a cat column
        todo : add cat_ column in this case, as v.in.ogr with dbf driver do
        """
        try:
            self.printMessage("Adding category column.")
            s = "ALTER TABLE " + str(output) + " ADD COLUMN cat serial NOT NULL"
            self.cursor.execute("ALTER TABLE " + str(output) + " ADD COLUMN cat serial NOT NULL")
            tmp_pkey_name = "tmp_pkey_" + str(output)
            self.cursor.execute("ALTER TABLE " + str(output) + " ADD CONSTRAINT " \
            + tmp_pkey_name + " PRIMARY KEY (cat)")
        except:
            raise GrassPostGisImporterError("Unable to add a 'cat' column. A column named 'CAT' \
                                            or 'cat' may be present in your input data. \
                                            This column is reserved for Grass to store categories.")

    def getGeometryInfo(self, output, geometryfield):
        """Retrieve geometry parameters of the result.
        We need to use the postgis AddGeometryColumn function so that v.in.ogr will work.
        This method aims to retrieve necessary info for AddGeometryColumn to work.
        Returns a dict with
        """
        self.printMessage("Retrieving geometry info.")
        ##if there is more than one geometry type in the query result table, we use the
        ##generic GEOMETRY type
        type="GEOMETRY"
        self.cursor.execute("SELECT DISTINCT GeometryType(" + geometryfield + ") FROM " + output)
        rows = self.cursor.fetchall()
        if rows is not None and len(rows) == 1:
            type = str(rows[0][0])
        if rows is None or len(rows) == 0:
            raise GrassPostGisImporterError("Unable to retrieve geometry type. Query result may have no geometry.")
        ##same thing with number of dimensions. If the query is syntactically correct but returns
        ##no geometry, this step will cause an error.
        ndims = 0
        self.cursor.execute("SELECT DISTINCT ndims(" + geometryfield + ") FROM " + output)
        rows = self.cursor.fetchall()
        if rows is not None and len(rows) == 1:
            ndims = str(rows[0][0])
            if self.logOutput is True:
                self.__writeLog("ndims=" + ndims)
        else:
            raise GrassPostGisImporterError("unable to retrieve a unique coordinates dimension for \
                                            this query or no geometry is present. Check your sql query.")
        ##srid
        srid="-1"
        self.cursor.execute("SELECT DISTINCT srid(" + geometryfield + ") FROM " + output)
        rows = self.cursor.fetchall()
        if rows is not None and len(rows[0]) == 1:
            srid = str(rows[0][0])
            if self.logOutput is True:
                self.__writeLog("srid=" + srid)
        elif rows is not None and len(rows[0]) > 1:
            if self.logOutput is True:
                self.__writeLog("Unable to retrieve a unique geometry srid for this query. \
                             Using undefined srid.")
        else:
            raise GrassPostGisImporterError("Unable to retrieve geometry parameters.")
        geoParamsDict = {'type':type, 'ndims':ndims, 'srid':srid}
        return geoParamsDict

    def addGeometry(self, output, geometryField, geoParams, addGistIndex=False):
        """Create geometry for result."""
        try:
            ##first we must remove other geometry columns than selected one that may be present in the query result,
            ##because v.in.ogr does not allow geometry columns selection
            ##v.in.ogr takes the first geometry column found in the table so if another geometry is present,
            ##as we use AddGeometryColumn fonction to copy selected geometry (see below), our geometry will
            ##appear after other geometries in the column list. In this case, v.in.ogr would not import the
            ##right geometry.
            self.printMessage("Checking for other geometries.")
            self.cursor.execute("SELECT column_name FROM(SELECT ordinal_position, column_name, udt_name \
                                FROM INFORMATION_SCHEMA.COLUMNS \
                                WHERE (TABLE_NAME='" + output + "') ORDER BY ordinal_position) AS info \
                                WHERE udt_name='geometry' AND NOT column_name='" + geometryField + "'")
            rows = self.cursor.fetchall()
            if rows is not None and len(rows) >= 1:
                for otherGeoColumn in rows:
                    if self.logOutput is True:
                        self.__writeLog("Found another geometry in the query result than selected one: "\
                                        + str(otherGeoColumn) + ". Column will be dropped.")
                    self.cursor.execute("ALTER TABLE " + output + " DROP COLUMN " + otherGeoColumn)
            ##we already inserted the geometry so we will recopy it in the newly created geometry column
            if self.logOutput is True:
                self.__writeLog("Create geometry column.")
            self.cursor.execute("ALTER TABLE " + output + " RENAME COLUMN " + geometryField + " TO the_geom_tmp")
            self.cursor.execute("SELECT AddGeometryColumn('', '" + output + "','" + geometryField + "',\
                                "+ geoParams['srid'] + ",'" + geoParams['type'] + "'," + geoParams['ndims'] + ");")
            self.cursor.execute("UPDATE " + output + " SET " + geometryField + " = the_geom_tmp")
            self.cursor.execute("ALTER TABLE " + output + " DROP COLUMN  the_geom_tmp")
            if addGistIndex is True:
                self.cursor.execute("CREATE INDEX " + output + "_index ON " + output + " \
                                    USING GIST (" + geometryField + " GIST_GEOMETRY_OPS);")
        except:
            raise GrassPostGisImporterError("An error occured during geometry insertion.")

    def importToGrass(self, output, geometryField, geoParams, toDbf = False, overrideProj = False):
        """Wrapper for import with v.in.ogr and db connection of the result.
        Note : for grass.gisenv() to work with grass6.3, in gisenv function from core.py,
        command should be (n flag removed because 6.4 specific):
        s = read_command("g.findfile", element = element, file = name, mapset = mapset)
        """
        ##dbf driver
        flags = ''
        outputname = output
        if toDbf is True:
            env = grass.gisenv()
            dbfFolderPath = os.path.join(env['GISDBASE'].strip(";'"), env['LOCATION_NAME'].strip(";'"), \
                                         env['MAPSET'].strip(";'"), 'dbf')
            if not os.path.exists(dbfFolderPath):
                os.mkdir(dbfFolderPath)
            grass.run_command("db.connect", driver = 'dbf', database = dbfFolderPath) 
        else:
            flags += ' -t'
        if overrideProj is True:
            flags += ' -o'

        ##finally call v.in.ogr
        self.printMessage("call v.in.ogr...")
        dsn="PG:host=" + self.dbparams['host'] + " dbname=" + self.dbparams['db'] \
        + " user=" + self.dbparams['user'] + " password=" + self.dbparams['pwd']
        layername = output
        ##we use the shell mode to be able to follow v.in.ogr progress in log file
        cmd = self.executeCommand('v.in.ogr' + flags + ' dsn="' + dsn + '" output=' + output + \
                                  ' layer=' + layername + ' --o', shell = True, toLog = True)
        if toDbf is True:
            grass.run_command("db.connect", driver = 'pg', database = 'host=' + self.dbparams['host'] + \
                              ",dbname=" + self.dbparams['db'])
            #self.cursor.execute('DROP TABLE ' + output)
            self.removeImportData(True, False)
        ##else we work directly with postgis so the connection between imported grass layer
        ##and postgres attribute table must be explicit
        else:
            ##can cause segfaults if mapset name is too long:
            cmd = self.executeCommand("v.db.connect", map = output, table = output, flags = 'o', \
                                      toLog = self.logOutput)

        ##delete temporary data in geometry_columns table
        #self.cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = '" + output + "'")
        self.removeImportData(False, True)
        pass

    def commitChanges(self):
        """Commit current transaction."""
        self.db.commit()

    def removeImportData(self, removeTable = True, removeGeometryColumnsRecord = True):
        """Cleanup method"""
        if removeTable is True:
            self.cursor.execute('DROP TABLE ' + self.output)
        if removeGeometryColumnsRecord is True:
            self.cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = '" + self.output + "'")
        self.commitChanges()

    def makeSqlImport(self):
        """GrassPostGisImporter main sequence."""
        ##1)check layers before starting
        self.checkLayers(self.output)
        ##2)query
        self.createPostgresTableFromQuery(self.output, self.query)
        ##3)cats
        if self.dbfFlag is False:
            self.addCategory(self.output)
        ##4)geometry parameters
        geoparams = self.getGeometryInfo(self.output, self.geometryfield)
        ##5)new geometry
        self.addGeometry(self.output, self.geometryfield, geoparams, self.gistindexFlag)
        ##we must commit before connecting to new table for import
        self.commitChanges()
        ##6)v.in.ogr
        self.importToGrass(self.output, self.geometryfield, geoparams, toDbf = self.dbfFlag, \
                            overrideProj = self.overrideprojFlag)
        ##process is ok
        self.commitChanges()

class GrassPostGisImporterError(Exception):
    """Errors specific to GrassPostGisImporter class."""
    def __init__(self, message=''):
        self.details = '\nDetails:\n'
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        self.details += repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
        self.message = message + "\n" + self.details

def main():
    exitStatus = 0
    try:
        postgisImporter = GrassPostGisImporter(options, flags)
        postgisImporter.makeSqlImport()
    except GrassPostGisImporterError, e1:
        postgisImporter.printMessage(e1.message, type = 'error')
        postgisImporter.removeImportData()
        exitStatus = 1
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        errorMessage = "Unexpected error \n:" + \
                       repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
        postgisImporter.printMessage(errorMessage, type = 'error')
        postgisImporter.removeImportData()
        exitStatus = 1
    else:
        postgisImporter.printMessage("Done", type = 'info')
    finally:
        sys.exit(exitStatus)

#############################################################################
#               A unit test for v.in.postgis
#############################################################################

options = {'query':'', 'geometryfield':'', 'output':''}
flags = {'d':0, 'z':0, 'o':0, 'g':0, 'l':0}
importer = GrassPostGisImporter(options, flags)
##test configuration
testsConfigOk = True
host = 'localhost'
dbname = 'yourdb'
user = 'pguser'
pwd = 'yourpwd'
try:
    db = dbapi2.connect(host=host, database=dbname, user=user, password=pwd)
    cursor = db.cursor()
except:
    testsConfigOk = False
testTableName = 'test_grass_import'
queryTableName = 'test_query'
geometryField = 'the_geom'
srid = '2154'
geoparams = {'type':'MULTIPOLYGON', 'ndims':'2', 'srid': srid}
query = 'select * from ' + testTableName + ' where id>1'

class GrassPostGisImporterTests(unittest.TestCase):

    def setUp(self): 
        grass.run_command("db.connect", driver = 'pg', database = 'host=' + host + ",dbname=" + dbname)

    def tearDown(self):
        cleanUpQueryTable()

    def testGetDbInfos(self):
        """Test if the importer is able to retrieve correctly the parameters dictionnary for current connection."""
        self.assertEqual(importer.dbparams['host'],host)
        self.assertEqual(importer.dbparams['db'],dbname)
        self.assertEqual(importer.dbparams['user'],user)
        self.assertEqual(importer.dbparams['pwd'],pwd)

    def testCheckLayers(self):
        """Test if overwrite is working correctly."""
        os.environ['GRASS_OVERWRITE'] = '0'
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, toDbf = False, overrideProj = True)
        importer.commitChanges()
        ##GRASS_OVERWRITE set to False, we can't import again the layer
        self.assertRaises(GrassPostGisImporterError, importer.checkLayers, queryTableName)
        cleanUpQueryTable()
        ##now set to True, it should be possible
        os.environ['GRASS_OVERWRITE'] = '1'
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, toDbf = False, overrideProj = True)
        importer.commitChanges()
        try:
            importer.checkLayers(queryTableName)
        except GrassPostGisImporterError:
            self.fail("CheckLayers was expected to be successful with --o flag.")

    def testNoResult(self):
        """Test if importer raise an error if query has no result."""
        noResultQuery = 'select * from ' + testTableName + ' where id>3'
        self.assertRaises(GrassPostGisImporterError, \
                          importer.createPostgresTableFromQuery, queryTableName, noResultQuery)
        ##needed
        importer.commitChanges()

    def testCheckComment(self):
        """Test that we can't drop a table with the output name if it was not created by the importer."""
        os.environ['GRASS_OVERWRITE'] = '1'
        self.assertRaises(GrassPostGisImporterError, importer.checkComment, testTableName)

    def testImportGrassLayer(self):
        """Test import sequence result in GRASS."""
        ##preparation
        importer.query = query
        importer.output = queryTableName
        importer.geometryfield = geometryField
        importer.gistindexFlag = True
        importer.overrideprojFlag = True
        importer.dbfFlag = False
        ##PostGIS import
        importer.makeSqlImport()
        testOutput = grass.find_file(queryTableName, element = 'vector')
        self.assertTrue(testOutput['fullname'] != '')
        pgdbconnectstring = "host=" + host + ",dbname=" + dbname
        cmd = importer.executeCommand("v.db.connect", flags = 'g', map = queryTableName, driver = 'pg')
        r = re.compile(' ')
        dbinfos = r.split(cmd)
        def trim(p): return str(p).strip()
        dbinfos = map(trim, dbinfos)
        self.assertEquals(dbinfos[0], '1')
        self.assertEquals(dbinfos[1], queryTableName)
        self.assertEquals(dbinfos[2], 'cat')
        self.assertEquals(dbinfos[3], pgdbconnectstring)
        self.assertEquals(dbinfos[4], 'pg')
        ##cast is necessary
        cmd = importer.executeCommand("echo 'SELECT CAST(COUNT (*) AS int) FROM " + queryTableName + "' | db.select -c", shell = True)
        self.assertEquals(int(cmd[0]), 2)
        cleanUpQueryTable()
        #Dbf import
        importer.dbfFlag = True
        importer.makeSqlImport()
        testOutput = grass.find_file(queryTableName, element = 'vector')
        self.assertTrue(testOutput['fullname'] != '')
        env = grass.gisenv()
        dbfDbPath = os.path.join(env['GISDBASE'].strip(";'"), env['LOCATION_NAME'].strip(";'"), \
                                         env['MAPSET'].strip(";'"), 'dbf')
        cmd = importer.executeCommand("v.db.connect", flags = 'g', map = queryTableName, driver = 'dbf')
        r = re.compile(' ')
        dbinfos = r.split(cmd)
        dbinfos = map(trim, dbinfos)
        self.assertEquals(dbinfos[0], '1')
        self.assertEquals(dbinfos[1], queryTableName)
        self.assertEquals(dbinfos[2], 'cat')
        self.assertEquals(dbinfos[3], dbfDbPath)
        self.assertEquals(dbinfos[4], 'dbf')
        cmd = importer.executeCommand("db.select", flags = 'c', table = queryTableName, \
                                      database = dbfDbPath, driver = 'dbf')
        r = re.compile('\n')
        lines = r.split(cmd)
        def validrecord(l): return len(str(l).strip()) > 0
        result = filter(validrecord, lines)
        self.assertEquals(len(result), 2)

    def testGetGeometryInfos(self):
        """Test that we correctly retrieve geometry parameters from PostGis result table."""
        createQueryTable()
        params = importer.getGeometryInfo(queryTableName, geometryField)
        self.assertEquals(params['type'], geoparams['type'])
        self.assertEquals(params['ndims'], geoparams['ndims'])
        self.assertEquals(params['srid'], geoparams['srid'])
        ##needed
        importer.commitChanges()

    def testAddingCategoryWithPgDriverIsNecessary(self):
        """Test is the cat column addition is working and is still necessary with pg driver import.

        cat column is necessary for GRASS to store categories.
        For now, the pg driver for v.in.ogr doesn't doesn't add automatically this
        cat column, whereas the dbf driver does. So the importer has a specific addCategory()
        method, which necessity is tested here.
        """
        ##starting with postgis to dbf import : no need to use the addCategory() method is expected
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, toDbf = True, overrideProj = True)
        importer.commitChanges()
        try:
            cmd = importer.executeCommand("v.univar", map = queryTableName, column = 'value')
        except GrassPostGisImporterError:
            self.fail("Categories should be retrieved with dbf driver.")
        cleanUpQueryTable()
        ##now same operations with pg driver : error is expected when GRASS use the cat column.
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, False, True)
        importer.commitChanges()
        self.assertRaises(GrassPostGisImporterError, \
                          importer.executeCommand, "v.univar", map = queryTableName, column = 'value')
        cleanUpQueryTable()
        ##now same operations with pg driver, after adding category column
        ##with the importer : error should not occur.
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.addCategory(queryTableName)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, False, True)
        importer.commitChanges()
        try:
            cmd = importer.executeCommand("v.univar", map = queryTableName, column = 'value')
        except GrassPostGisImporterError:
            self.fail("Categories should be retrieved with pg driver when categories are added.")

    def testGeometryDuplicationIsNecessary(self):
        """Test that we need to use the postGis' AddGeometryColumn function."""
        createQueryTable()
        importer.addCategory(queryTableName)
        importer.commitChanges()
        self.assertRaises(GrassPostGisImporterError, importer.importToGrass, queryTableName, \
                        geometryField, geoparams, False, True)
        cleanUpQueryTable()
        createQueryTable()
        ##now addGeometry:
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.addCategory(queryTableName)
        importer.commitChanges()
        try:
            importer.importToGrass(queryTableName, geometryField, geoparams, False, True)
        except GrassPostGisImporterError:
            self.fail("Both operations are for now expected to be necessary.")

def createQueryTable():
    importer.createPostgresTableFromQuery(queryTableName, query)
    importer.commitChanges()

def cleanUpQueryTable():
    db.rollback()
    try:
        importer.executeCommand("g.remove", vect = queryTableName, quiet = True)
    except:
        pass
    try:
        cursor.execute('DROP TABLE ' + queryTableName)
    except:
        pass
    try:
        cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = '" + queryTableName + "'")
    except:
        pass
    db.commit()

def cleanUp():
    db.rollback()
    cleanUpQueryTable()
    try:
        importer.executeCommand("g.remove", vect = testTableName, quiet = True)
    except:
        pass
    try:
        cursor.execute('DROP TABLE ' + testTableName)
    except:
        pass
    try:
        cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = '" + testTableName + "'")
    except:
        pass
    db.commit()

def tests():
    currentDirectory = os.path.split(__file__)[0]
    sys.path.append(currentDirectory)
    ##test geo table
    cursor.execute("CREATE TABLE " + testTableName + " ( id int4, label varchar(20), value real )")
    cursor.execute("SELECT AddGeometryColumn('', '" + testTableName + "','" + geometryField + "'," + srid + ",'MULTIPOLYGON',2)")
    cursor.execute("INSERT INTO " + testTableName + " (id, label, value, " + geometryField + ") VALUES (1, 'A Geometry', 10, \
                        GeomFromText('MULTIPOLYGON(((771825.9029201793 6880170.713342139,771861.2893824165 \
                        6880137.00894025,771853.633171779 6880129.128272728,771818.4675156211 \
                        6880162.7242448665,771825.9029201793 6880170.713342139)))', " + srid + "))")
    cursor.execute("INSERT INTO " + testTableName + " (id, label, value, " + geometryField + ") VALUES (2, 'Another Geometry', 20, \
                        GeomFromText('MULTIPOLYGON(((771853.633171779 6880129.128272728,771842.2964842085 \
                        6880117.197908178,771807.1308239839 6880150.79394592,771818.4675156211 \
                        6880162.7242448665,771853.633171779 6880129.128272728)))', " + srid + "))")
    cursor.execute("INSERT INTO " + testTableName + " (id, label, value, " + geometryField + ") VALUES (3, 'A last Geometry', 20, \
                        GeomFromText('MULTIPOLYGON(((771807.1308239839 6880150.79394592,771842.2964842085 \
                        6880117.197908178,771831.1791767566 6880105.270296125,771795.7209431691 \
                        6880138.862761175,771807.1308239839 6880150.79394592)))', " + srid + "))")
    cursor.execute("ALTER TABLE " + testTableName + " ADD CONSTRAINT test_pkey " + " PRIMARY KEY (id)")
    db.commit()
    os.environ['GRASS_VERBOSE'] = '0'
    try:
        runner = unittest.TextTestRunner()
        suite = unittest.TestSuite()
        suite.addTest(GrassPostGisImporterTests("testGetDbInfos"))
        suite.addTest(GrassPostGisImporterTests("testCheckLayers"))
        suite.addTest(GrassPostGisImporterTests("testNoResult"))
        suite.addTest(GrassPostGisImporterTests("testCheckComment"))
        suite.addTest(GrassPostGisImporterTests("testImportGrassLayer"))
        suite.addTest(GrassPostGisImporterTests("testGetGeometryInfos"))
        suite.addTest(GrassPostGisImporterTests("testAddingCategoryWithPgDriverIsNecessary"))
        suite.addTest(GrassPostGisImporterTests("testGeometryDuplicationIsNecessary"))
        runner.run(suite)
    finally:
        cleanUp()
        sys.exit(0)


if __name__ == "__main__":
    ### DEBUG : uncomment to start local debugging session
    #brk(host="localhost", port=9000)
    options, flags = grass.parser()
    if flags['t'] is True:
        if testsConfigOk is True:
            tests()
        else:
            grass.error("Could not connect to test database. Check the tests configuration.")
    else:
        main()


