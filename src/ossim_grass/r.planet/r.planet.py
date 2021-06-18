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
#% keywords: raster
#%end
#%option
#% key: map
#% type: string
#% gisprompt: old,raster,raster
#% key_desc: name
#% description: Name of raster map 
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
#%option
#% key: tile
#% type: double
#% key_desc: tile
#% description: tile
#% required : no
#%end
#%flag
#% key: a
#% description: Add raster
#%END
#%flag
#% key: r
#% description: Remove raster
#%END
#%flag
#% key: d
#% description: Orthoigen 
#%END


import sys
import os
import socket
import grass.script as grass
import osgeo.gdal as gdal

def main():
    add = flags['a']
    remove = flags['r']
    orthoigen = flags['d']
    host = options['host']
    dport = options['dport']
    pport = options['pport']
    tile = options['tile']
    grassenv = grass.gisenv()
    mappa = options['map'].replace("@"," ")
    mappa = mappa.split()

    nflags = len(filter(None, [add, remove, orthoigen]))
    if nflags > 1:
        grass.run_command('g.message' , message = 'Cannot add & remove a map or use orthoigen at the same time.')
    if nflags < 1:
        grass.run_command('g.message' , message = 'No action requested , please choose one from "-a : add" or "-r : remove" flags.')
    try :
        rasterpath = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], mappa[1], 'cellhd') 
        mapfile = os.path.join(rasterpath, mappa[0])
        vrtdir = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], mappa[1], 'vrt/raster/')
        #print vrtdir
    except :
        rasterpath = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], grassenv['MAPSET'], 'cellhd')
        mapfile = os.path.join(rasterpath, mappa[0])   
        vrtdir = os.path.join(grassenv['GISDBASE'], grassenv['LOCATION_NAME'], grassenv['MAPSET'], 'vrt/raster/')
        #print vrtdir
    d = os.path.dirname(vrtdir)
    if not os.path.exists(d):
        os.makedirs(d)
    #os.makedirs(d)
    vrtfilename =  mappa[0] + '.vrt'
    output = os.path.join(vrtdir, vrtfilename) 
    if not os.path.exists(output):
        gdal.GetDriverByName('VRT').CreateCopy(output,gdal.Open(mapfile))
        #grass.run_command('r.out.gdal', format = 'VRT', type = 'Float64', input = mappa[0] , output = '%s' % (output))
    proj_info = projinfo()
    unit = proj_info['units']
    if unit.lower() == 'meters':
        zoom_position = setCPRJ(options['map'])
    if unit.lower() == 'metres':
        zoom_position = setCPRJ(options['map'])
    if unit.lower() == 'degrees':
        zoom_position = setCLL(options['map'])
    lat = zoom_position[0]
    lon = zoom_position[1]
    distance = zoom_position[2]
    if nflags == 1:
        if add :
            try :
                addzoom(output,lon,lat,distance,host,dport,pport)
                print 'Added raster file :', mappa[0]
                print 'Camera positioned to : '
                print 'Longitude = ',lon
                print 'Latitude = ', lat
                print 'Altitude = ' , distance
            except :
                print "conecction error"
        if remove :
            removefile(output,host,dport)
            print 'Removed raster file :', mappa[0]
        if orthoigen :
            if tile != '':
                path = os.path.dirname(output)
                elevdir = os.path.join(path,'elevation',mappa[0]+'/')
                print elevdir
                if not os.path.exists(elevdir):
                    os.makedirs(elevdir)
                    elev = mappa[0]+'.tiff'
                    exportiff(output,elev)
                    instr = make3d(tile, elev, elevdir)
                    print instr
                    os.system(instr)
                if tile == '':
                    print 'please set the tile dimension'

def exportiff(infile,outfile):
    gdal.GetDriverByName('GTiff').CreateCopy(outfile,gdal.Open(infile))



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
    info_region = grass.read_command('g.region', flags = 'cael', rast = '%s' % (map)) 
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
    info_region = grass.read_command('g.region', flags = 'ael', rast = '%s' % (map)) 
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


def makedir(path):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d)

def make3d(tile, elev, outdir):
    makedir(outdir)
    kwl = 'elev.kwl'
    template = 'igen.slave_tile_buffers: 5 \n'
    template += 'igen.tiling.type: ossimTiling \n'
    template += 'igen.tiling.tiling_distance: 1 1 \n'
    template += 'igen.tiling.tiling_distance_type: degrees \n'
    template += 'igen.tiling.delta: %s %s \n' % (tile,tile)
    template += 'igen.tiling.delta_type: total_pixels \n'
    template += 'igen.tiling.padding_size_in_pixels: 0 0 \n'
    template += 'object1.description: \n'
    template += 'object1.enabled:  1 \n'
    template += 'object1.id:  1 \n'
    template += 'object1.object1.description: \n'  
    template += 'object1.object1.enabled:  1 \n'
    template += 'object1.object1.id:  2 \n'
    template += 'object1.object1.resampler.magnify_type:  bilinear \n'
    template += 'object1.object1.resampler.minify_type:  bilinear \n'
    template += 'object1.object1.type:  ossimImageRenderer \n'
    template += 'object1.object2.type:  ossimCastTileSourceFilter \n'
    template += 'object1.object2.scalar_type: ossim_sint16 \n'
    template += 'object1.type:  ossimImageChain \n'
    template += 'object2.type: ossimGeneralRasterWriter \n'
    template += 'object2.byte_order: big_endian \n'
    template += 'object2.create_overview: false \n'
    template += 'object2.create_histogram: false \n'
    template += 'object2.create_external_geometry: false \n'
    template += 'product.projection.type: ossimEquDistCylProjection \n'
    open(kwl,'w').write(template)
    #instr = 'export DYLD_FRAMEWORK_PATH=/Users/sasha/OssimBuilds/Release/ ; '
    instr = '/usr/local/bin/ossim-orthoigen'
    instr += ' --tiling-template '
    instr += kwl
    instr +=' --view-template '
    instr += kwl
    instr +=' --writer-template '
    instr += kwl
    instr +=' --chain-template '
    instr += kwl
    instr += ' %s ' % elev 
    instr += '%s' % outdir
    instr +='/%SRTM%'
    return instr


def makeoverview(input):
    os.system("ossim-img2rr %s" % input)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())


