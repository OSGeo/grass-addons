#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:        r.in.modis.download
# AUTHOR(S):     Luca Delucchi
# PURPOSE:       r.in.modis.download is an internafe to pyModis to download 
#                several tiles of MODIS produts from NASA ftp
#
# COPYRIGHT:        (C) 2011 by Luca Delucchi
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

#%module
#% description: Download several tiles of MODIS products using pyModis
#% keywords: raster
#%end
#%flag
#% key: d
#% description: For debug mode, it will write more info in the log file
#%end
#%flag
#% key: g
#% description: Return the name of file containing the list of HDF tiles downloaded in shell script style
#%end
#%option
#% key: setting
#% type: string
#% gisprompt: old,file,input
#% label: Full path to setting file.
#% description: "-" to pass the parameter from stdin
#% required: yes
#% guisection: Define
#%end
#%option
#% key: product
#% type: string
#% description: Name of MODIS product
#% required: no
#% options: lst_aqua_daily, lst_terra_daily, snow_terra_eight, ndvi_terra_sixte
#% answer: lst_terra_daily
#%end
#%option
#% key: tiles
#% type: string
#% description: The names of tile/s to download
#% required: no
#%end
#%option
#% key: startday
#% type: string
#% description: The day from start download. If not set the download starts from today
#% required: no
#%end
#%option
#% key: endday
#% type: string
#% description: The day to stop download. If not set the download stops 10 day before the start day
#% required: no
#%end
#%option
#% key: folder
#% type: string
#% description: The folder where store the data downloaded. If not set it take the path of setting file
#% required: no
#%end

# import library
import os, sys
from datetime import *
import grass.script as grass

# add the folder containing libraries to python path
libmodis = os.path.join(os.getenv('GISBASE'), 'etc', 'r.modis')
sys.path.append(libmodis)
# try to import pymodis (modis) and some class for r.modis.download
try:
    from rmodislib import product
    from modis import downModis
except ImportError:
    pass

def check(home):
    """ Check if a folder it is writable by the user that launch the process
    """
    if os.access(home,os.W_OK):
        return 1
    else:
        grass.fatal(_("Folder to write downloaded files doesn't" \
        + " exist or is not writeable"))
        return 0

def checkdate(options):
    """ Function to check the data and return the correct value to download the
        the tiles
    """
    def check2day(second,first=None):
        """Function to check two date"""
        if not first:
            valueDay = None
            firstDay = date.today()
        else:
            valueDay = first
            firstSplit = first.split('-')
            firstDay = date(int(firstSplit[0]),int(firstSplit[1]),int(firstSplit[2]))
        lastSplit = second.split('-')
        lastDay = date(int(lastSplit[0]),int(lastSplit[1]),int(lastSplit[2]))
        delta = firstDay-lastDay
        valueDelta = int(delta.days)
        return valueDay, second, valueDelta

    # no set start and end day
    if options['startday'] == '' and options['endday'] == '':
        return None, None, 10
    # set only end day
    elif options['startday'] == '' and options['endday'] != '':
        today = date.today().strftime("%Y-%m-%d")
        if today <= options['endday']:
            grass.fatal(_('The last day cannot before >= of the first day'))
            return 0
        valueDay, valueEnd, valueDelta = check2day(options['endday'])
    # set only start day
    elif options['startday'] != '' and options['endday'] == '':
        valueDay = options['startday']
        valueEnd = None
        valueDelta = 10
    # set start and end day
    elif options['startday'] != '' and options['endday'] != '':
        valueDay, valueEnd, valueDelta = check2day(options['endday'],options['startday'])
    return valueDay, valueEnd, valueDelta 

# main function
def main():
    # check if you are in GRASS
    gisbase = os.getenv('GISBASE')
    if not gisbase:
        grass.fatal(_('$GISBASE not defined'))
        return 0
    # set username, password and folder if settings are insert by stdin
    if options['setting'] == '-':
        if options['folder']:
            if check(options['folder']):
                fold = options['folder']
            user = raw_input(_('Insert username (usually anonymous): '))
            passwd = raw_input(_('Insert password (your mail): '))
        else:
            grass.fatal(_("Please set folder option if you want pass username " \
            + "and password by stdin"))
            return 0
    # set username, password and folder by file
    else:
        # open the file and read the the user and password:
        # first line is username
        # second line is password
        filesett = open(options['setting'],'r')
        fileread = filesett.readlines()
        user = fileread[0].strip()
        passwd = fileread[1].strip()
        filesett.close()
        # set the folder by option folder
        if options['folder']:
            if check(options['folder']):
                fold = options['folder']
        # set the folder from path where setting file is stored 
        else:
            path = os.path.split(options['setting'])[0]
            if check(path):
                fold = path
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version['version'].find('7.') == -1:
        grass.fatal(_('You are not in GRASS GIS version 7'))
        return 0
    # first date and delta
    firstday, finalday, delta = checkdate(options)
    # the product
    prod = product(options['product']).returned()
    # set tiles
    if options['tiles'] == '':
        tiles = None
    else:
        tiles = options['tiles']
    # set the debug
    if flags['d']:
      debug_opt = True
    else:
      debug_opt = False
    #start modis class
    modisOgg = downModis(url = prod['url'], user = user,password = passwd, 
            destinationFolder = fold, tiles = tiles, path = prod['folder'], 
            today = firstday, enddate = finalday, delta = delta, debug = debug_opt)
    # connect to ftp
    modisOgg.connectFTP()
    # download tha tiles
    modisOgg.downloadsAllDay()
    if flags['g']:
      grass.message(modisOgg.filelist.name)
    else:
      grass.message(_("Downloading MODIS product..."))
      grass.message(_("All data are downloaded, now you can use r.in.modis.import "\
      + "or r.in.modis.process with option 'conf=" + modisOgg.filelist.name + '\''))

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
