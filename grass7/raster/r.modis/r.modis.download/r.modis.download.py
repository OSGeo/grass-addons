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
#%option
#% key: product
#% type: string
#% description: Name of MODIS product
#% required: yes
#% options: lst_aqua_daily, lst_terra_daily, snow_terra_eight, ndvi_terra_sixte
#% answer: lst_terra_daily
#%end
#%option
#% key: username
#% type: string
#% key_desc: username
#% description: Name of user to NASA ftp access, it's better use SETTING.py
#% required: no
#%end
#%option
#% key: password
#% type: string
#% key_desc: password
#% description: Password of user to NASA ftp access, it's better use SETTING.py
#% required: no
#%end
#%option
#% key: folder
#% type: string
#% description: Folder where saves the data, full path
#% answer: $HOME/.grass7/r.modis/download
#% required: no
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
#%flag
#% key: d
#% description: For debug mode, it will write more info in the log file
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


def check(home,suffix):
    """ Function to check the path necessary to work this module
    """

    # check if ~/.grass7/r.modis/download exist or create it
    if not os.path.exists(home):
        os.mkdir(home)
        os.mkdir(os.path.join(home,suffix))
    elif not os.path.exists(os.path.join(home,suffix)):
        os.mkdir(os.path.join(home,suffix))
    return 1

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
        import pdb; pdb.set_trace()
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

    # set the home path
    home = os.path.expanduser('~')
     
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version['version'].find('7.') != -1:
        session_path = '.grass7'
        grass_fold = os.path.join(home,session_path)
        if not os.path.exists(grass_fold):
          os.mkdir(grass_fold)
    else: 
        grass.fatal(_('You are not in GRASS GIS version 7'))
        return 0
    # path to ~/grass7/r.modis
    path = os.path.join(grass_fold,'r.modis')
    # first date and delta
    firstday, finalday, delta = checkdate(options)
    #username and password are optional because the command lines history 
    #will store the password in this these options; so you are the possibility
    #to use a file
    if options['username'] == '' and options['password'] == '':
        sett_file = os.path.join(path,'SETTING.py')
        grass.message("For setting will use %s" % sett_file)
        try:
            sys.path.append(path)
            import SETTING
        except ImportError:
            grass.fatal("%s not exist or is not well formatted. Create "\
            "the file with inside:\n\n#!/usr/bin/env python\n\nusername="\
            "your_user\npassword=xxxxx" % sett_file)
            return 0
        user = SETTING.username
        passwd = SETTING.username
    else:
        grass.message("For setting will use username and password options")
        user = options['username']
        passwd = options['password']        
    
    prod = product(options['product']).returned()
    # set folder
    if options['folder'].find('HOME/.grass7/r.modis/download') == 1:
        fold = os.path.join(path,'download')
        # some check
        check(path,'download')
    else:
        fold = options['folder']
    # set tiles
    if options['tiles'] == '':
        tiles = None
    else:
        tiles = options['tiles']
        
    # start modis class
    modisOgg = downModis(url = prod['url'], user = user,password = passwd, 
            destinationFolder = fold, tiles = tiles, path = prod['folder'], 
            today = firstday, enddate = finalday, delta = delta)
    # connect to ftp
    modisOgg.connectFTP()
    # download tha tiles
    modisOgg.downloadsAllDay()
    grass.message("All data are downloaded, now you can use r.in.modis.import "\
    "or r.in.modis.process with option 'conf=" + modisOgg.filelist.name)
    
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
