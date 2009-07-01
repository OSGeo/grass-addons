#!/usr/bin/python
#-*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       v_in_postgis_sqlquery_tests.py
# AUTHOR(S):	Mathieu Grelier, 2009 (greliermathieu@gmail.com)
# PURPOSE:		An attempt of a GRASS module unit test
# COPYRIGHT:	(C) 2009 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

import sys
import os

##see http://trac.osgeo.org/grass/browser/grass/trunk/lib/python
from grass import core as grass
##only needed to use debugger. See http://aspn.activestate.com/ASPN/Downloads/Komodo/RemoteDebugging
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
        """
        Test if the importer is able to retrieve correctly the parameters dictionnary for current connection.
        """
        self.assertEqual(importer.dbparams['host'],host)
        self.assertEqual(importer.dbparams['db'],dbname)
        self.assertEqual(importer.dbparams['user'],user)
        self.assertEqual(importer.dbparams['pwd'],pwd)
    
    def testCheckLayers(self):
        """
        !Test if overwrite is working correctly
        """
        from v_in_postgis_sqlquery import GrassPostGisImporterError
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
        """
        !Test that we can't drop a table with the output name if it was not created by the importer.
        """
        ##a table that was not tagged by the importer should not be overwritten
        from v_in_postgis_sqlquery import GrassPostGisImporterError
        os.environ['GRASS_OVERWRITE'] = '1'
        self.assertRaises(GrassPostGisImporterError, importer.checkComment, testTableName)
        pass
    
    def testCreateTable(self):
        pass
    
    def testAddingCategoryWithPgDriverIsNecessary(self):
        """!Test is the cat column addition is working and is still necessary with pg driver import
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
        cmd = importer.executeCommand("v.univar", map = queryTableName, column = 'value')
        self.assertEqual(cmd['return_code'], 0)
        cleanUpQueryTable()
        ##now same operations with pg driver : error is expected when GRASS use the cat column.
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, False, True)
        importer.commitChanges()
        cmd = importer.executeCommand("v.univar", map = queryTableName, column = 'value')
        self.assertNotEqual(cmd['return_code'], 0)
        cleanUpQueryTable()
        ##now same operations with pg driver, after adding category column
        ##with the importer : error should not occur.
        createQueryTable()
        importer.addGeometry(queryTableName, geometryField, geoparams, False)
        importer.addCategory(queryTableName)
        importer.commitChanges()
        importer.importToGrass(queryTableName, geometryField, geoparams, False, True)
        importer.commitChanges()
        cmd = importer.executeCommand("v.univar", map = queryTableName, column = 'value')
        self.assertEqual(cmd['return_code'], 0)
        
    def testGeometryDuplicationIsNecessary(self):
        """!Test that we need to use the postGis' AddGeometryColumn function"""
        createQueryTable()
        importer.addCategory(queryTableName)
        importer.commitChanges()
        from v_in_postgis_sqlquery import GrassPostGisImporterError
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
    importer.createPostgresTableFromQuery(queryTableName, 'select * from ' + testTableName + ' where id=1')
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
    from v_in_postgis_sqlquery import GrassPostGisImporter
    ##test configuration
    options = {'sqlquery':'', 'geometryfield':'', 'output':''}
    flags = {'d':0, 'z':0, 'o':0, 'g':0, 'l':0}
    importer = GrassPostGisImporter(options, flags)
    module = __import__('v_in_postgis_sqlquery_tests')
    host = 'localhost'
    dbname = 'yourdb'
    user = 'postgres'
    pwd = 'yourpwd'
    db = dbapi2.connect(host=host, database=dbname, user=user, password=pwd)
    cursor = db.cursor()
    testTableName = 'test_grass_import'
    queryTableName = 'test_query'
    geometryField = 'the_geom'
    geoparams = {'type':'POLYGON', 'ndims':'2', 'srid':'-1'}
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
    ##test geo table
    cursor.execute("CREATE TABLE " + testTableName + " ( id int4, label varchar(20), value real )")
    cursor.execute("SELECT AddGeometryColumn('', '" + testTableName + "','" + geometryField + "',-1,'POLYGON',2)")
    cursor.execute("INSERT INTO " + testTableName + " (id, label, value, " + geometryField + ") VALUES (1, 'A Geometry', 10, \
                        GeomFromText('POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))', -1))")
    cursor.execute("INSERT INTO " + testTableName + " (id, label, value, " + geometryField + ") VALUES (2, 'Another Geometry', 20, \
                        GeomFromText('POLYGON((0 0, 0 20, 20 20, 20 0, 0 0))', -1))")
    cursor.execute("ALTER TABLE " + testTableName + " ADD CONSTRAINT test_pkey " + " PRIMARY KEY (id)")
    db.commit()
    os.environ['GRASS_VERBOSE'] = '0'
    try:
        unittest.main(defaultTest='suite')
    finally:
        module.cleanUp()
        sys.exit(0)
