#!/usr/bin/python
#-*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       v_in_postgis_tests.py
# AUTHOR(S):	Mathieu Grelier, 2009 (greliermathieu@gmail.com)
# PURPOSE:		An attempt of a GRASS module unit test for v_in_postgis
# COPYRIGHT:	(C) 2009 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

import sys
import os
import re

##see http://trac.osgeo.org/grass/browser/grass/trunk/lib/python
from grass import core as grass
##only needed to use debugger with Komodo IDE. See http://aspn.activestate.com/ASPN/Downloads/Komodo/RemoteDebugging
from dbgp.client import brk
##see http://pyunit.sourceforge.net/
import unittest
##see http://initd.org/pub/software/psycopg/
import psycopg2 as dbapi2

importer = None
db = None
cursor = None
host = None
dbname = None
user = None
pwd = None
query = None
testTableName = None
queryTableName = None
geometryField = None
geoparams = None

class v_in_postgis_sqlquery_tests(unittest.TestCase):
    
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
        """Test if overwrite is working correctly"""
        from v_in_postgis import GrassPostGisImporterError
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
        except Exception:
            self.fail("CheckLayers was expected to be successful with --o flag.")
        pass
    
    def testCheckComment(self):
        """Test that we can't drop a table with the output name if it was not created by the importer."""
        ##a table that was not tagged by the importer should not be overwritten
        from v_in_postgis import GrassPostGisImporterError
        os.environ['GRASS_OVERWRITE'] = '1'
        self.assertRaises(GrassPostGisImporterError, importer.checkComment, testTableName)
        pass
    
    def testImportGrassLayer(self):
        """Test import sequence result in GRASS"""
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
        """Test that we correctly retrieve geometry parameters from PostGis result table"""
        createQueryTable()
        params = importer.getGeometryInfo(queryTableName, geometryField)
        self.assertEquals(params['type'], geoparams['type'])
        self.assertEquals(params['ndims'], geoparams['ndims'])
        self.assertEquals(params['srid'], geoparams['srid'])
        ##needed
        importer.commitChanges()
    
    def testAddingCategoryWithPgDriverIsNecessary(self):
        """Test is the cat column addition is working and is still necessary with pg driver import
        
        cat column is necessary for GRASS to store categories.
        For now, the pg driver for v.in.ogr doesn't doesn't add automatically this
        cat column, whereas the dbf driver does. So the importer has a specific addCategory()
        method, which necessity is tested here.
        """
        ##starting with postgis to dbf import : no need to use the addCategory() method is expected
        from v_in_postgis import GrassPostGisImporterError
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
        """Test that we need to use the postGis' AddGeometryColumn function"""
        createQueryTable()
        importer.addCategory(queryTableName)
        importer.commitChanges()
        from v_in_postgis import GrassPostGisImporterError
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
        except Exception:
            self.fail("Both operations are for now expected to be necessary.")
        pass

def createQueryTable():
    importer.createPostgresTableFromQuery(queryTableName, query)
    importer.commitChanges()
    
def cleanUpQueryTable():
    db.rollback()
    try:
        importer.executeCommand("g.remove", vect = queryTableName, quiet = True)
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
        cursor.execute('DROP TABLE ' + testTableName)
    except:
        pass
    try:
        cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = '" + testTableName + "'")
    except:
        pass
    db.commit()
    
def suite():
    alltests = unittest.TestSuite()
    alltests.addTest(unittest.findTestCases(module))
    return alltests

if __name__ == '__main__':
    ### DEBUG : uncomment to start local debugging session
    #brk(host="localhost", port=9000)
    currentDirectory = os.path.split(__file__)[0]
    sys.path.append(currentDirectory)
    from v_in_postgis import GrassPostGisImporter
    ##test configuration
    options = {'query':'', 'geometryfield':'', 'output':''}
    flags = {'d':0, 'z':0, 'o':0, 'g':0, 'l':0}
    importer = GrassPostGisImporter(options, flags)
    module = __import__('v_in_postgis_tests')
    host = 'localhost'
    dbname = 'yourdb'
    user = 'postgresuser'
    pwd = 'yourpwd'
    db = dbapi2.connect(host=host, database=dbname, user=user, password=pwd)
    cursor = db.cursor()
    testTableName = 'test_grass_import'
    queryTableName = 'test_query'
    geometryField = 'the_geom'
    srid = '2154'
    geoparams = {'type':'MULTIPOLYGON', 'ndims':'2', 'srid': srid}
    query = 'select * from ' + testTableName + ' where id>1'
    ##give access to test elements to module
    module.importer = importer
    module.db = db
    module.cursor = cursor
    module.host = host
    module.dbname = dbname
    module.user = user
    module.pwd = pwd
    module.testTableName = testTableName
    module.queryTableName = queryTableName
    module.geometryField = geometryField
    module.geoparams = geoparams
    module.query = query
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
        unittest.main(defaultTest='suite')
    finally:
        module.cleanUp()
        sys.exit(0)
