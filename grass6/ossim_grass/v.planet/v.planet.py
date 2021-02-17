#!/usr/bin/env python
################################################################################
#
# MODULE:       r.planet.py
#
# AUTHOR(S):    Massimo Di Stefano 2010-02-7
#               
#
# PURPOSE:      
#
# COPYRIGHT:    (c) 2010 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# REQUIRES:     Ossimplanet
#                 
#               
#
################################################################################

#%module
#% description: 
#% keywords: vector
#%end
#%option
#% key: map
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of vector map 
#% required: yes
#%end
#%option
#% key: host
#% type: string
#% key_desc: host
#% answer: 127.0.0.1
#% description: Host
#% required : no
#%end
#%option
#% key: dport
#% type: integer
#% key_desc: dport
#% answer: 8000
#% description: Data Port 
#% required : no
#%end
#%option
#% key: pport
#% type: integer
#% key_desc: port
#% answer: 7000
#% description: Position Port 
#% required : no
#%end
#%flag
#% key: a
#% description: Add vector
#%END
#%flag
#% key: r
#% description: Remove vector
#%END
#%option
#% key: brush
#% type: string
#% key_desc: brush
#% description: brush color  
#% required : no
#%end
#%option
#% key: pen
#% type: string
#% key_desc: pen
#% description: pen color  
#% required : no
#%end
#%option
#% key: size
#% type: string
#% key_desc: size
#% description: size 
#% required : no
#%end
#%option
#% key: fill
#% type: string
#% key_desc: fill
#% description: fill 
#% required : no
#%end
#%option
#% key: thickness
#% type: string
#% key_desc: thickness
#% description: thickness 
#% required : no
#% answer: 1
#%end

import sys
import os
import socket
import grass.script as grass
import string

try:
    from osgeo import osr, ogr, gdal
except ImportError:
    import osr, ogr, gdal

from ogrTovrt import ogrvrt #, makestile


def main():
    add = flags['a']
    remove = flags['r']
    host = options['host']
    dport = options['dport']
    pport = options['pport']
    grassenv = grass.gisenv()
    mappa = options['map'].replace("@"," ")
    mappa = mappa.split()
    nflags = len(filter(None, [add, remove]))
    if nflags > 1:
        grass.run_command('g.message' , message = 'Cannot add & remove a map at same time.')
    if nflags < 1:
        grass.run_command('g.message' , message = 'No action requested , please choose one from "-a : add" or "-r : remove" flags.')
    try :
        vectorpath = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], mappa[1], 'vector' , mappa[0] ) 
        mapfile = os.path.join(vectorpath, 'head')
        vrtdir = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], mappa[1], 'vrt', 'vector/')
    except :
        vectorpath = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], grassenv['MAPSET'], mappa[0] )
        mapfile = os.path.join(vectorpath, 'head' )   
        vrtdir = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], grassenv['MAPSET'], 'vrt', 'vector/')
    d = os.path.dirname(vrtdir)
    if not os.path.exists(d):
        os.makedirs(d)
    vrtfilename =  mappa[0] + '.vrt'
    output = os.path.join(vrtdir, vrtfilename)
    if not os.path.exists(output):
        ogrvrt(mapfile,output)
        print 'try to make omd'
        makestile(output, options['brush'], options['pen'], options['size'], options['fill'], options['thickness'])
        proj_info = projinfo()
        unit = proj_info['units']
        if unit.lower() == 'meters':
            zoom_position = setCPRJ(options['map'])
        if unit.lower() == 'metres':
            zoom_position = setCPRJ(options['map'])
        if unit == 'Degrees':
            zoom_position = setCLL(options['map'])
        lat = zoom_position[0]
        lon = zoom_position[1]
        distance = zoom_position[2]
    if add :
        try:
            addzoom(output,lon,lat,distance,host,dport,pport)
            print 'Added vector file :', mappa[0]
            print 'Camera positioned to : '
            print 'Longitude = ',lon
            print 'Latitude = ', lat
            print 'Altitude = ' , distance
        except :
            print "conecction error"
    if remove :
        removefile(output,host,dport)
        print 'Removed vector file :', mappa[0]


def addfile(output,host,dport):
    overview = output.replace('.vrt','.ovr')
    if not os.path.isfile(overview):
        makeoverview(output)
    ossim_data_xml = "<Add target=':idolbridge'><Image groupType='groundTexture'><filename>%s</filename> <id>%s</id><name>%s</name></Image></Add>" % (output,output,output)
    ossimdata = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ossimdata.connect((host, int(dport)))
    ossimdata.send(ossim_data_xml)
    ossimdata.close()


def zoomto(lon,lat,distance,host,pport):
    ossim_zoom_xml = '<Set target=":navigator" vref="wgs84"><Camera><longitude>%s</longitude><latitude>%s</latitude><altitude>%s</altitude><heading>0</heading><pitch>0</pitch><roll>0</roll><altitudeMode>absolute</altitudeMode><range>%s</range></Camera></Set>' % (lon, lat, distance, distance)
    ossimposition = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ossimposition.connect((host, int(pport)))  
    ossimposition.send(ossim_zoom_xml)
    ossimposition.close()


def removefile(output,host,dport):
    ossimdata = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ossimdata.connect((host, int(dport)))
    ossim_data_xml = "<Remove target=':idolbridge' id='%s' />" % (output)
    ossimdata.send(ossim_data_xml)
    ossimdata.close()


def addzoom(output,lon,lat,distance,host,dport,pport):
    addfile(output,host,dport)
    zoomto(lon,lat,distance,host,pport)


def projinfo():
    units = grass.read_command("g.proj", flags='p')
    units = units.replace('-','')
    units = grass.parse_key_val(units, ':')
    units_key = units.keys()
    for i in units_key :
        key_value = str(units[i]).strip()
        units[i] = key_value
    return units



def setCLL(map):
    center = []
    info_region = grass.read_command('g.region', flags = 'cael', vect = '%s' % (map)) 
    dict_region = grass.parse_key_val(info_region, ':')
    lon = dict_region['east-west center']	
    lat = dict_region['north-south center']
    lon = str(lon)
    lat = str(lat)
    lon = lon.replace(':', " ")
    lat = lat.replace(':', " ")
    if lat[-1] == 'N':
        signlat = 1
    if lat[-1] == 'S':
        signlat = -1
    if lon[-1] == 'E':
        signlon = 1
    if lon[-1] == 'W':
        signlon = -1
    lat = lat[:-1] 
    lon = lon[:-1]
    lat = [float(i) for i in lat.split()]
    lon = [float(i) for i in lon.split()]
    lat = (lat[0] + (lat[1] / 60) + lat[2] / 3600) * float(signlat)
    lon = (lon[0] + (lon[1] / 60) + lon[2] / 3600) * float(signlon)
    ns = float(dict_region['north-south extent'])
    we = float(dict_region['east-west extent'])
    distance = (ns + we) / 2
    center.append(lat)
    center.append(lon)
    center.append(distance)
    return center


def setCPRJ(map):
    center = []
    info_region = grass.read_command('g.region', flags = 'ael', vect = '%s' % (map)) 
    dict_region = grass.parse_key_val(info_region, ':')
    lon = dict_region['center longitude']	
    lat = dict_region['center latitude']
    lon = str(lon)
    lat = str(lat)
    lon = lon.replace(':', " ")
    lat = lat.replace(':', " ")
    if lat[-1] == 'N':
        signlat = 1
    if lat[-1] == 'S':
        signlat = -1
    if lon[-1] == 'E':
        signlon = 1
    if lon[-1] == 'W':
        signlon = -1
    lat = lat[:-1] 
    lon = lon[:-1]
    lat = [float(i) for i in lat.split()]
    lon = [float(i) for i in lon.split()]
    lat = (lat[0] + (lat[1] / 60) + lat[2] / 3600) * float(signlat)
    lon = (lon[0] + (lon[1] / 60) + lon[2] / 3600) * float(signlon)
    ns = float(dict_region['north-south extent'])
    we = float(dict_region['east-west extent'])
    distance = (ns + we) / 2
    center.append(lat)
    center.append(lon)
    center.append(distance)
    return center

def makeoverview(input):
    print 'vector object should alredy have internal preview, make overview skipped'
    #os.system("ossim-img2rr %s" % input)


def makestile(outfile, brush, pen, size, fill, thickness):
    brush = brush.split(',')
    pen = pen.split(',')
    size = size.split(',')
    print brush, pen, size
    outfile = outfile.replace('.vrt','')
    outfile = outfile+'.omd'
    omd = '// vector file rendering options\n'
    omd += 'brush_color: %s %s %s \n' % (brush[0], brush[1], brush[2])
    omd += 'pen_color: %s %s %s \n' % (pen[0], pen[1], pen[2])
    omd += 'point_width_height: %s %s \n' % (size[0], size[1])
    omd += 'fill_flag: %s \n' % (fill)
    omd += 'thickness: %s \n' % (thickness)
    open(outfile,'w').write(omd)
    print omd



if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())


