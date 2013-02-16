#!/usr/bin/env python

############################################################################
#
# MODULE:       r.in.srtm.region
#
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Create a DEM from 3 arcsec SRTM v2.1 tiles
#
# COPYRIGHT:    (C) 2011 GRASS development team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Creates a DEM from 3 arcsec SRTM v2.1 tiles.
#% keywords: raster
#% keywords: import
#%end
#%option G_OPT_R_OUTPUT
#% description: Name for output raster map
#% required: yes
#%end
#%option
#% key: url
#% description: base url to fetch SRTM v2.1 tiles
#% answer: http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/
#% required: no
#%end
#%option G_OPT_M_DIR
#% key: local
#% label: local folder with SRTM v2.1 tiles
#% description: use local folder instead of url to retrieve SRTM tiles
#% required: no
#%end
#%option
#% key: region
#% type: double
#% label: Import subregion only (default is current region)
#% description: Format: xmin,ymin,xmax,ymax - usually W,S,E,N
#% key_desc: xmin,ymin,xmax,ymax
#% multiple: yes
#% required: no
#%end
#%option
#% key: memory
#% type: integer
#% description: Memory in MB for interpolation
#% answer: 300
#% required: no
#%end
#%flag
#%  key: n
#%  description: Fill null cells
#%end


proj = ''.join([
    'GEOGCS[',
    '"wgs84",',
    'DATUM["WGS_1984",SPHEROID["wgs84",6378137,298.257223563],TOWGS84[0.000000,0.000000,0.000000]],',
    'PRIMEM["Greenwich",0],',
    'UNIT["degree",0.0174532925199433]',
    ']'])

import sys
import os
import shutil
import atexit
import urllib
import urllib2
import time

import grass.script as grass

def import_local_tile(tile, local, pid):
    output = tile + '.r.in.srtm2.tmp.' + str(pid)
    local_tile = str(tile) + '.hgt.zip'
    
    path = os.path.join(local, local_tile)
    if os.path.exists(path):
	path = os.path.join(local, tile)
	grass.run_command('r.in.srtm', input = path, output = output, quiet = True)
	return 1

    # SRTM subdirs: Africa, Australia, Eurasia, Islands, North_America, South_America
    for srtmdir in ('Africa', 'Australia', 'Eurasia', 'Islands', 'North_America', 'South_America'):
	path = os.path.join(local, srtmdir, local_tile)

	if os.path.exists(path):
	    path = os.path.join(local, srtmdir, tile)
	    grass.run_command('r.in.srtm', input = path, output = output, quiet = True)
	    return 1

    return 0

def download_tile(tile, url, pid):
    output = tile + '.r.in.srtm2.tmp.' + str(pid)
    local_tile = str(tile) + '.hgt.zip'

    urllib.urlcleanup()

    # SRTM subdirs: Africa, Australia, Eurasia, Islands, North_America, South_America
    for srtmdir in ('Africa', 'Australia', 'Eurasia', 'Islands', 'North_America', 'South_America'):
	remote_tile = str(url) + str(srtmdir) + '/' + local_tile
	goturl = 1
    
	try:
	    f = urllib2.urlopen(remote_tile)
	    fo = open(local_tile, 'w+b')
	    fo.write(f.read())
	    fo.close
	    time.sleep(0.5)
	    # does not work:
	    #urllib.urlretrieve(remote_tile, local_tile, data = None)
	except:
	    goturl = 0
	    pass
	
	if goturl == 1:
	    return 1

    return 0
    
    
def cleanup():
    if not in_temp:
	return
    os.chdir(currdir)
    grass.run_command('g.region', region = tmpregionname)
    grass.run_command('g.remove', region = tmpregionname, quiet = True)
    #grass.try_rmdir(tmpdir)

def main():
    global tile, tmpdir, in_temp, currdir, tmpregionname

    in_temp = False

    url = options['url']
    local = options['local']
    output = options['output']
    memory = options['memory']
    fillnulls = flags['n']
    
    if len(url) == 0 and len(local) == 0:
	grass.fatal(_("Either 'url' or 'local' is needed"))
	
    if len(local) == 0:
	local = None

    # are we in LatLong location?
    s = grass.read_command("g.proj", flags='j')
    kv = grass.parse_key_val(s)
    if kv['+proj'] != 'longlat':
	grass.fatal(_("This module only operates in LatLong locations"))

    if fillnulls == 1 and memory <= 0:
	grass.warning(_("Amount of memory to use for interpolation must be positive, setting to 300 MB"))
	memory = '300'

    # make a temporary directory
    tmpdir = grass.tempfile()
    grass.try_remove(tmpdir)
    os.mkdir(tmpdir)
    currdir = os.getcwd()
    pid = os.getpid()

    # change to temporary directory
    os.chdir(tmpdir)
    in_temp = True
    if local is None:
	local = tmpdir

    # get extents
    reg = grass.region()
    tmpregionname = 'r_in_srtm2_tmp_region'
    grass.run_command('g.region', save = tmpregionname)
    if options['region'] is None or options['region'] == '':
	north = reg['n']
	south = reg['s']
	east = reg['e']
	west = reg['w']
    else:
	west, south, east, north = options['region'].split(',')
	west = float(west)
	south = float(south)
	east = float(east)
	north = float(north)

    # adjust extents to cover SRTM tiles: 1 degree bounds
    tmpint = int(north)
    if tmpint < north:
	north = tmpint + 1
    else:
	north = tmpint
	
    tmpint = int(south)
    if tmpint > south:
	south = tmpint - 1
    else:
	south = tmpint

    tmpint = int(east)
    if tmpint < east:
	east = tmpint + 1
    else:
	east = tmpint

    tmpint = int(west)
    if tmpint > west:
	west = tmpint - 1
    else:
	west = tmpint
	
    if north == south:
	north += 1
    if east == west:
	east += 1

    rows = abs(north - south)
    cols = abs(east - west)
    ntiles = rows * cols
    grass.message(_("Importing %d SRTM tiles...") % ntiles, flag = 'i')
    counter = 1

    srtmtiles = ''
    valid_tiles = 0
    for ndeg in range(south, north):
	for edeg in range(west, east):
	    grass.percent(counter, ntiles, 1)
	    counter += 1
	    if ndeg < 0:
		tile = 'S'
	    else:
		tile = 'N'
	    tile = tile + '%02d' % abs(ndeg)
	    if edeg < 0:
		tile = tile + 'W'
	    else:
		tile = tile + 'E'
	    tile = tile + '%03d' % abs(edeg)
	    grass.debug("Tile: %s" % tile, debug = 1)
	    
	    if local != tmpdir:
		gotit = import_local_tile(tile, local, pid)
	    else:
		gotit = download_tile(tile, url, pid)
		if gotit == 1:
		    gotit = import_local_tile(tile, tmpdir, pid)
	    if gotit == 1:
		grass.verbose(_("Tile %s successfully imported") % tile)
		valid_tiles += 1
	    else:
		# create tile with zeros
		# north
		if ndeg < 0:
		    tmpn = '%02d:59:58.5S' % (abs(ndeg) - 2)
		else:
		    tmpn = '%02d:00:01.5N' % (ndeg + 1)
		# south
		if ndeg <= 0:
		    tmps = '%02d:00:01.5S' % abs(ndeg)
		else:
		    tmps = '%02d:59:58.5N' % (ndeg - 1)
		# east
		if edeg < 0:
		    tmpe = '%03d:59:58.5W' % (abs(edeg) - 2)
		else:
		    tmpe = '%03d:00:01.5E' % (edeg + 1)
		# west
		if edeg <= 0:
		    tmpw = '%03d:00:01.5W' % abs(edeg)
		else:
		    tmpw = '%03d:59:58.5E' % (edeg - 1)

		grass.run_command('g.region', n = tmpn, s = tmps, e = tmpe, w = tmpw, res = '00:00:03')
		grass.run_command('r.mapcalc', expression = "%s = 0" % (tile + '.r.in.srtm2.tmp.' + str(pid)), quiet = True)
		grass.run_command('g.region', region = tmpregionname)


    # g.mlist with sep = comma does not work ???
    pattern = '*.r.in.srtm2.tmp.%d' % pid
    srtmtiles = grass.read_command('g.mlist',
                                   type = 'rast',
				   pattern = pattern,
				   sep = 'newline',
				   quiet = True)

    srtmtiles = srtmtiles.splitlines()
    srtmtiles = ','.join(srtmtiles)

    if valid_tiles == 0:
	grass.run_command('g.remove', rast = str(srtmtiles), quiet = True)
	grass.warning(_("No tiles imported"))
	if local != tmpdir:
	    grass.fatal(_("Please check if local folder <%s> is correct.") % local)
	else:
	    grass.fatal(_("Please check internet connection and if url <%s> is correct.") % url)

    grass.run_command('g.region', rast = str(srtmtiles));
    
    if fillnulls == 0:
	grass.run_command('r.patch', input = srtmtiles, output = output)
    else:
	ncells = grass.region()['cells'] 
	if long(ncells) > 1000000000:
	    grass.message(_("%s cells to interpolate, this will take some time") % str(ncells), flag = 'i')
	grass.run_command('r.patch', input = srtmtiles, output = output + '.holes')
	mapstats = grass.parse_command('r.univar', map = output + '.holes', flags = 'g', quiet = True)
	if mapstats['null_cells'] == '0':
	    grass.run_command('g.rename', rast = '%s,%s' % (output + '.holes', output), quiet = True)
	else:
	    grass.run_command('r.resamp.bspline',
			      input = output + '.holes',
			      output = output + '.interp',
			      se = '0.0025', sn = '0.0025',
			      method = 'bilinear',
			      memory = memory,
			      flags = 'n')
	    grass.run_command('r.patch',
	                      input = '%s,%s' % (output + '.holes',
			      output + '.interp'),
			      output = output + '.float',
			      flags = 'z')
	    grass.run_command('r.mapcalc', expression = '%s = round(%s)' % (output, output + '.float'))
	    grass.run_command('g.remove',
			      rast = '%s,%s,%s' % (output + '.holes', output + '.interp', output + '.float'),
			      quiet = True)

    grass.run_command('g.mremove', rast = pattern, flags = 'f', quiet = True)

    # nice color table
    grass.run_command('r.colors', map = output, color = 'srtm', quiet = True)

    # write metadata:
    tmphist = grass.tempfile()
    f = open(tmphist, 'w+')
    f.write(os.environ['CMDLINE'])
    f.close()
    grass.run_command('r.support', map = output,
		      loadhistory = tmphist,
		      description = 'generated by r.in.srtm.region',
		      source1 = 'SRTM V2.1',
		      source2 = (local if local != tmpdir else url))
    grass.try_remove(tmphist)

    grass.message(_("Done: generated map <%s>") % output)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
