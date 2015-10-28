#!/usr/bin/env python
# -*- coding: utf-8
"""
@module  g.proj.identify
@brief   Module for automatic identification of EPSG from definition of projection in WKT format.

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
"""

#%module
#% description: Autoidentify of EPSG from WKT
#% keyword: EPSG
#% keyword: WKT
#% keyword: .prj
#%end

#%option G_OPT_F_INPUT
#% key: wkt
#% label: WKT prj input
#% required: no
#%end

#%option
#% key: epsg
#% type: integer
#% label: EPSG input
#% required: no
#%end

#%flag
#% key: p
#% label: Proj4
#% description: Print Proj4 format
#%end

#%flag
#% key: w
#% label: WKT
#% description: Print WKT
#%end

#%flag
#% key: s
#% label: save
#% description: Save as default EPSG
#%end
from grass.script import core as grass
from grass.pygrass.modules import Module
from subprocess import PIPE
from osgeo import osr
import os


def writeEPSGtoPEMANENT(epsg):
    env = grass.gisenv()
    gisdbase = env['GISDBASE']
    location = env['LOCATION_NAME']
    path = os.path.join(gisdbase, location, "PERMANENT","PROJ_EPSG")
    if os.path.isfile(path): #if already file exist
        if os.getenv('GRASS_OVERWRITE', False):
            try:
                io = open(path,'w')
                io.write("epsg: %s"%epsg )
                io.close()
                print("EPSG code have been written to < %s >"%path)
            except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)

        else:
            print("EPSG file already exist < %s >"%path)
    else:
        try:
            io = open(path,'w')
            io.write("epsg: %s"%epsg)
            io.close()
            print("EPSG code have been written to < %s >"%path)
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)

def isPermanent():
    env = grass.gisenv()
    if env['MAPSET'] == "PERMANENT":
        return True
    return False

def grassEpsg():
    proj=Module('g.proj',
               flags='p',
               quiet=True,
               stdout_=PIPE)
    proj=proj.outputs.stdout
    lines=proj.splitlines()
    for e,line in enumerate(lines):
        if 'EPSG' in line:
            epsg=lines[e+1].split(':')[1].replace(' ','')
            print('epsg=%s' % epsg)
            if flags['s']:
                if isPermanent():
                    writeEPSGtoPEMANENT(epsg)
                else:
                    grass.warning("Cannot acces PERMANENT mapset")
            return
    try:
        proj=Module('g.proj',
               flags='wf',
               quiet=True,
               stdout_=PIPE)
        proj=proj.outputs.stdout
        wkt2standards(proj)
    except:
        grass.error('WKT input error')

def wkt2standards(prj_txt):
    srs = osr.SpatialReference()
    srs.ImportFromESRI([prj_txt])
    if flags['w']:
        print('wkt=%s' % srs.ExportToWkt())
    if flags['p']:
        print('proj4=%s' % srs.ExportToProj4())
    srs.AutoIdentifyEPSG()
    try :
        int(srs.GetAuthorityCode(None))
        epsg=srs.GetAuthorityCode(None)
        print('epsg=%s' % epsg)
        if flags['s']:
            if isPermanent():
                writeEPSGtoPEMANENT(epsg)
            else:
                grass.warning("Cannot acces PERMANENT mapset")
    except:
        grass.error('Epsg code cannot be identified')

def epsg2standards(epsg):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(epsg))
    if flags['w']:
        print('wkt=%s' % srs.ExportToWkt())
    if flags['p']:
        print('proj4=%s' % srs.ExportToProj4())

def main():
    epsg=options['epsg']
    pathwkt=options['wkt']
    if epsg and pathwkt:
        grass.error('Only one type of conversions can be processed concurrently')

    if epsg:
        epsg2standards(epsg)
    else:
        if pathwkt:
            try:
                io= open(pathwkt,'r')
                wkt=io.read().rstrip()
                wkt2standards(wkt)
            except IOError as e:
                grass.error('Cannot open file %s, %s'%(e.errno, e.strerror))
        else:
            grassEpsg()

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
