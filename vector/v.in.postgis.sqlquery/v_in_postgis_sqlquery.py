#!/usr/bin/python
#-*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       v_in_postgis_sqlquery
# AUTHOR(S):	Mathieu Grelier, 2009 (greliermathieu@gmail.com)
# PURPOSE:		postgis data manipulation in grass from arbitrary sql queries
# COPYRIGHT:	(C) 2009 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#%  description: Create a grass layer from any sql query in postgis 
#%  keywords: postgis, grass layer, sql 
#%End
#%option
#% key: sqlquery
#% type: string
#% description: Any sql query returning a recordset with geometry for each row 
#% required : yes
#%end
#%option
#% key: geometryfield
#% type: string
#% answer: the_geom
#% description: Name of the source geometry field. Usually defaults to the_geom but needed if a geometry function was used (for example, centroid), or if the table has many geometry columns.
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% answer: postgis_sqlquery
#% description: Name of the geographic postgis table where to place the query results. Will be the name of the imported grass layer. If -d flag is set, this table is deleted and replaced by a dbf attribute table. Use a different name than the original. Do not use capital letters
#% required : no
#%end
#%flag
#% key: d
#% description: Import result in grass dbf format (no new table in postgis). If not set, the grass layer will be directly connected to the postgis new table
#%end
#%flag
#% key: o
#% description: Use -o for v.in.ogr (override dataset projection)
#%end
#%flag
#% key: g
#% description: Add a gist index to the imported table in postgis (useless with the d flag)
#%end
#%flag
#% key: l
#% description: Log process info to v.in.postgis.sqlquery.py.log. 
#%end

import sys
import os
import re
from subprocess import Popen, PIPE
import traceback

##see http://initd.org/pub/software/psycopg/
import psycopg2 as dbapi2
##see http://trac.osgeo.org/grass/browser/grass/trunk/lib/python
from grass import core as grass
##only needed to use debugger. See http://aspn.activestate.com/ASPN/Downloads/Komodo/RemoteDebugging
from dbgp.client import brk

class GrassPostGisImporter():
    
    def __init__(self, options, flags):
        ##options
        self.sqlquery = options['sqlquery']
        self.geometryfield = options['geometryfield'] if options['geometryfield'].strip() != '' else 'the_geom'
        self.output = options['output'] if options['output'].strip() != '' else 'postgis_import'
        ##flags
        self.dbfFlag = True if flags['d'] is True else False
        self.overrideprojFlag = True if flags['o'] is True else False
        self.gistindexFlag = True if flags['g'] is True else False
        self.logOutput = True if flags['l'] is True else False
        ##others
        logfilename = 'v.in.postgis.sqlquery.py.log'
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
    
    def __execShellCommand(self, command, stderrRedirection=False, logFile=False):
        """General purpose function, maybe should be added in some way to core.py """
        if logFile is not False:
            command = command + ' >> ' +  logFile
        if stderrRedirection is True:
            command = command + " 2>&1"
        p = Popen(command, shell=True, stdout=PIPE)
        retcode = p.wait()
        com = p.communicate()
        if retcode == 0:
            return com[0]
        else:
            errorMessage = ''
            for elem in com:
                errorMessage += str(elem) + "\n"
            raise GrassPostGisImporterError(errorMessage)
            
    def __writeLog(self, log=''):
        """Write the 'log' string to log file"""
        if self.logfile is not None:
            fileHandle = open(self.logfile, 'a')
            log = log + '\n'
            fileHandle.write(log)
            fileHandle.close()
            
    def __getDbInfos(self):
        """
        Create a dictionnary with all db params needed by v.in.ogr
        """
        try:
            dbString = grass.parse_key_val(grass.read_command('db.connect', flags = 'p'), sep = ':')['database']
            p = re.compile(',')
            dbElems = p.split(dbString)
            host = grass.parse_key_val(dbElems[0], sep = '=')['host']
            db = grass.parse_key_val(dbElems[1], sep = '=')['dbname']
            loginLine = self.__execShellCommand('sed -n "/pg ' + dbElems[0] + ',' + dbElems[1] + ' /p" ' + self.grassloginfile)
            p = re.compile(' ')
            loginElems = p.split(loginLine)
            user = loginElems[-2].strip()
            password = loginElems[-1].strip()
            dbParamsDict = {'host':host, 'db':db, 'user':user, 'pwd':password}
            return dbParamsDict
        except:
            raise GrassPostGisImporterError("Error while trying to retrieve database information.")
    
    def printMessage(self, message, type = 'info'):
        if type == 'error':
            grass.error(message)
        elif type == 'warning':
            grass.warning(message)
        elif type == 'info' and grass.gisenv()['GRASS_VERBOSE'] > 0:
            grass.info(message)
        if self.logOutput is True:
            self.__writeLog(message)
            
    def executeCommand(self, *args, **kwargs):
        """ """
        kwargs['stdout'] = PIPE
        kwargs['stderr'] = PIPE
        ps = grass.start_command(*args, **kwargs)
        retcode = ps.wait()
        log = ''
        for item in ps.communicate():
            log = log + item + '\n'
        if self.logOutput is True:
            self.__writeLog(log)
        result = {'return_code':retcode, 'output':log}
        return result
        
    def checkLayers(self, output):
        """
        !Preliminary checks before starting import.
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
        ##Previous script execution may have not removed temporary elements
        ##test if a table with the 'output' name already exists in PostGis.
        ##If so, was it created by this script ? If so, delete it.
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
            if comment == "created_with_v_in_postgis_sqlquery.py":
                self.cursor.execute("DROP TABLE " + output)
            else:
                raise GrassPostGisImporterError("ERROR: a table with the name " + output + " already exists \
                                                and was not created by this script.")
        return True
    
    def createPostgresTableFromQuery(self, output, sqlquery):
        """
        Create a table in postgresql populated with results from the sql query, and comment it so we
        will later be able to figure out if this table was created by this script (see checkLayers())
        """
        try:
            createTableQuery = "CREATE TABLE " + str(output) + " AS " + str(sqlquery)
            if self.logOutput is True:
                self.__writeLog("Try to import data:")
                self.__writeLog(createTableQuery)
            self.cursor.execute(createTableQuery)
            addCommentQuery = "COMMENT ON TABLE " + output + " IS 'created_with_v_in_postgis_sqlquery.py'"
            self.cursor.execute(addCommentQuery)
        except:
            raise GrassPostGisImporterError("An error occurred during sql import. Check your connection \
                                            to the database and your sql query.")
    
    def addCategory(self, output):
        """
        !Add a category column in the result table
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
        """
        !Retrieve geometry parameters of the result
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
            raise GrassPostGisImporterError("Unable to retrieve geometry type")
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
        """!Create geometry for result"""
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
        """!Wrapper for import and db connection of the result
        Note : for grass.gisenv() to work with grass6.3, in gisenv function from core.py,
        command should be (n flag removed because 6.4 specific):
        s = read_command("g.findfile", element = element, file = name, mapset = mapset)
        """
        ##dbf driver
        flags = ''
        outputname = output
        if toDbf is True:
            #we need 
            #outputname="tmpoutput"
            env = grass.gisenv()
            dbfFolderPath = os.path.join(env['GISDBASE'].strip(";'"), env['LOCATION_NAME'].strip(";'"), \
                                         env['MAPSET'].strip(";'"), 'dbf')
            if not os.path.exists(dbfFolderPath):
                os.mkdir(dbfFolderPath)
            grass.run_command("db.connect", driver = 'dbf', database = dbfFolderPath) 
        else:
            flags += 't'
        if overrideProj is True:
            flags += 'o'

        ##finally call v.in.ogr
        self.printMessage("call v.in.ogr...")
        dsn="PG:host=" + self.dbparams['host'] + " dbname=" + self.dbparams['db'] \
        + " user=" + self.dbparams['user'] + " password=" + self.dbparams['pwd']
        layername = output
        cmd = self.executeCommand("v.in.ogr", dsn = dsn, output = outputname, layer = layername, \
                          flags = flags, overwrite=True, quiet = False)
        if cmd['return_code'] != 0:
            raise GrassPostGisImporterError("v.in.ogr error:\n" + cmd['output'])
        ##if we import to grass dbf format, we must rename the dbf layer to match the given output name
        if toDbf is True:
            grass.run_command("db.connect", driver = 'pg', database = 'host=' + self.dbparams['host'] + \
                              ",dbname=" + self.dbparams['db'])
            self.cursor.execute('DROP TABLE ' + output)
        ##else we work directly with postgis so the connection between imported grass layer
        ##and postgres attribute table must be explicit
        else:
            ##can cause segfaults if mapset name is too long:
            cmd = self.executeCommand("v.db.connect", map = output, table = output, flags = 'o')
            if cmd['return_code'] != 0:
                raise GrassPostGisImporterError("v.db.connect error:\n" + cmd['output'])
        
        ##delete temporary data in geometry_columns table
        self.cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = '" + output + "'")
        pass
            
    def commitChanges(self):
        """!Commit current transaction"""
        self.db.commit()
    
    def makeSqlImport(self):
        """!GrassPostGisImporter main sequence"""
        ##1)check layers before starting
        self.checkLayers(self.output)
        ##2)query
        self.createPostgresTableFromQuery(self.output, self.sqlquery)
        ##3)cats
        if self.dbfFlag is False:
            self.addCategory(self.output)
        ##4)geometry parameters
        geoparams = self.getGeometryInfo(self.output, self.geometryfield)
        ##5)new geometry
        self.addGeometry(self.output, self.geometryfield, geoparams, self.gistindexFlag)
        self.commitChanges()
        ##6)v.in.ogr
        self.importToGrass(self.output, self.geometryfield, geoparams, toDbf = self.dbfFlag, \
                           overrideProj = self.overrideprojFlag)
        ##7)post-import operations
        self.commitChanges()
                                                                                  
class GrassPostGisImporterError(Exception):
    """Errors specific to GrassPostGisImporter class"""
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
        exitStatus = 1
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        errorMessage = "Unexpected error \n:" + \
                       repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
        postgisImporter.printMessage(errorMessage, type = 'error')
        exitStatus = 1
    else:
        postgisImporter.printMessage("Done", type = 'info')
    finally:
        sys.exit(exitStatus)

if __name__ == "__main__":
    ### DEBUG : uncomment to start local debugging session
    #brk(host="localhost", port=9000)
    options, flags = grass.parser()
    main()
