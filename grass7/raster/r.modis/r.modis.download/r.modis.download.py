#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:        r.in.modis.download
# AUTHOR(S):     Luca Delucchi
# PURPOSE:       r.in.modis.download is an interface to pyModis for download
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
#% keyword: raster
#% keyword: import
#%end
#%flag
#% key: d
#% description: For debug mode, it will write more info in the log file
#%end
#%flag
#% key: g
#% description: Return the name of file containing the list of HDF tiles downloaded in shell script style
#%end
#%flag
#% key: c
#% description: Does not perform GDAL check on downloaded images
#%end
#%option G_OPT_F_INPUT
#% key: settings
#% label: Full path to settings file
#% required: yes
#% guisection: Define
#%end
#%option
#% key: product
#% type: string
#% label: Name of MODIS product(s)
#% multiple: yes
#% required: no
#% options: lst_terra_daily_1000, lst_aqua_daily_1000, lst_terra_eight_1000, lst_aqua_eight_1000, lst_terra_daily_6000, lst_aqua_daily_6000, ndvi_terra_sixteen_250, ndvi_aqua_sixteen_250, ndvi_terra_sixteen_500, ndvi_aqua_sixteen_500, ndvi_terra_sixteen_1000, ndvi_aqua_sixteen_1000, snow_terra_daily_500, snow_aqua_daily_500, snow_terra_eight_500, snow_aqua_eight_500
#% answer: lst_terra_daily_1000
#%end
#%option
#% key: tiles
#% type: string
#% label: The name(s) of tile(s) to download (comma separated)
#% description: e.g.: h18v04
#% required: no
#%end
#%option
#% key: startday
#% type: string
#% label: First date to download
#% description: Format: YYYY-MM-DD. If not set the download starts from today and go back 10 days. If not endday the download stops 10 days after the endday
#% required: no
#%end
#%option
#% key: endday
#% type: string
#% label: Last date to download
#% description: Format: YYYY-MM-DD. To use only together with startday
#% required: no
#%end
#%option
#% key: folder
#% type: string
#% label: Folder to store the downloaded data
#% description: If not set, path of settings file is used
#% required: no
#%end


# import library
import os
import sys
from datetime import *
import grass.script as grass
from grass.pygrass.utils import get_lib_path


path = get_lib_path(modname='r.modis', libname='libmodis')
if path is None:
    grass.fatal("Not able to find the modis library directory.")
sys.path.append(path)

from rmodislib import product
from downmodis import downModis


def check(home):
    """ Check if a folder it is writable by the user that launch the process
    """
    if os.access(home, os.W_OK):
        return True
    else:
        grass.fatal(_("Folder to write downloaded files does not "
                      "exist or is not writeable"))


def checkdate(options):
    """ Function to check the data and return the correct value to download the
        the tiles
    """
    def check2day(second, first=None):
        """Function to check two date"""
        if not first:
            valueDay = None
            firstDay = date.today()
        else:
            valueDay = first
            firstSplit = first.split('-')
            firstDay = date(int(firstSplit[0]), int(firstSplit[1]),
                            int(firstSplit[2]))
        lastSplit = second.split('-')
        lastDay = date(int(lastSplit[0]), int(lastSplit[1]), int(lastSplit[2]))
        if firstDay < lastDay:
            grass.fatal(_("End day has to be bigger then start day"))
        delta = firstDay - lastDay
        valueDelta = int(delta.days)
        return valueDay, second, valueDelta
    # no set start and end day
    if options['startday'] == '' and options['endday'] == '':
        return None, None, 10
    # set only end day
    elif options['startday'] != '' and options['endday'] == '':
        valueDelta = 10
        valueEnd = options['startday']
        firstSplit = valueEnd.split('-')
        firstDay = date(int(firstSplit[0]), int(firstSplit[1]),
                        int(firstSplit[2]))
        delta = timedelta(10)
        lastday = firstDay + delta
        valueDay = lastday.strftime("%Y-%m-%d")
    # set only start day
    elif options['startday'] == '' and options['endday'] != '':
        grass.fatal(_("It is not possible use <endday> option without "
                      "<startday> option"))
    # set start and end day
    elif options['startday'] != '' and options['endday'] != '':
        valueDay, valueEnd, valueDelta = check2day(options['startday'],
                                                   options['endday'])
    return valueDay, valueEnd, valueDelta


# main function
def main():
    # check if you are in GRASS
    gisbase = os.getenv('GISBASE')
    if not gisbase:
        grass.fatal(_('$GISBASE not defined'))
        return 0
    # set username, password and folder if settings are insert by stdin
    if options['settings'] == '-':
        if options['folder'] != '':
            if check(options['folder']):
                fold = options['folder']
            user = 'anonymous'
            passwd = raw_input(_('Insert password (your e-mail): '))
        else:
            grass.fatal(_("Set folder parameter when using stdin for passing "
                          "the username and password"))
            return 0
    # set username, password and folder by file
    else:
        # open the file and read the the user and password:
        # first line is username
        # second line is password
        if check(options['settings']):
            filesett = open(options['settings'], 'r')
            fileread = filesett.readlines()
            user = fileread[0].strip()
            passwd = fileread[1].strip()
            filesett.close()
        else:
            grass.fatal(_("File <%s> not found") % options['settings'])
        # set the folder by option folder
        if options['folder'] != '':
            if check(options['folder']):
                fold = options['folder']
        # set the folder from path where settings file is stored
        else:
            path = os.path.split(options['settings'])[0]
            if check(path):
                fold = path
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version['version'].find('7.') == -1:
        grass.fatal(_('GRASS GIS version 7 required'))
        return 0
    # the product
    products = options['product'].split(',')
    # first date and delta
    firstday, finalday, delta = checkdate(options)
    # set tiles
    if options['tiles'] == '':
        tiles = None
        grass.warning(_("Option 'tiles' not set. Downloading all available tiles"))
    else:
        tiles = options['tiles']
    # set the debug
    if flags['d']:
        debug_opt = True
    else:
        debug_opt = False
    if flags['c']:
        checkgdal = False
    else:
        checkgdal = True
    for produ in products:
        prod = product(produ).returned()
        #start modis class
        modisOgg = downModis(url=prod['url'], user=user, password=passwd,
                             destinationFolder=fold, tiles=tiles, delta=delta,
                             path=prod['folder'], product=prod['prod'],
                             today=firstday, enddate=finalday, debug=debug_opt,
                             checkgdal=checkgdal)
        # connect to ftp
        modisOgg.connect()
        if modisOgg.nconnection <= 20:
            # download tha tiles
            grass.message(_("Downloading MODIS product <%s>..." % produ))
            modisOgg.downloadsAllDay()
            filesize = int(os.path.getsize(modisOgg.filelist.name))
            if flags['g'] and filesize != 0:
                grass.message("filename=%s" % modisOgg.filelist.name)
            elif flags['g'] and filesize == 0:
                grass.message("filename=")
            elif not flags['g'] and filesize == 0:
                grass.message(_("All data have been previously downloaded"))
            elif filesize != 0:
                grass.message(_("All data have been downloaded, continue "
                                "with r.modis.import with the option "
                                "'files=%s'" % modisOgg.filelist.name))
        else:
            grass.fatal(_("Error during connection"))

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
