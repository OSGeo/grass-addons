#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:        r.modis.import
# AUTHOR(S):     Luca Delucchi
# PURPOSE:       r.modis.import is an interface to pyModis for import into GRASS
#                GIS level 3 MODIS produts
#
# COPYRIGHT:        (C) 2011 by Luca Delucchi
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  MRT tools
#
#############################################################################

#%module
#% description: Download several tiles of MODIS products using pyModis
#% keywords: raster
#% keywords: MODIS
#%end
#%flag
#% key: m
#% description: Create a mosaic for each day
#%end
#%flag
#% key: t
#% description: Preserve temporary files (TIF and HDF mosaic)
#%end
#%flag
#% key: q
#% description: Create and import also the QA layer
#%end
#%option
#% key: mrtpath
#% type: string
#% key_desc: path
#% description: The full path to MRT directory
#% required: yes
#%end
#%option
#% key: dns
#% type: string
#% key_desc: path
#% description: Path to single HDF file
#% required: no
#%end
#%option
#% key: files
#% type: string
#% key_desc: file
#% description: Path to a file with a list of HDF files 
#% required: no
#%end
#%option
#% key: resampl
#% type: string
#% key_desc: resampling
#% description: Code of resampling type
#% options: NN, BI, CC, NONE
#% answer: NN
#% required: no
#%end
#%option
#% key: spectral
#% type: string
#% key_desc: spectral subset
#% description: A string to choose the subset of HDF file to use
#% required: no
#%end
#%option
#% key: folder
#% type: string
#% description: Folder where saves the data, full path
#% answer: $HOME/.grass7/r.modis/import
#% required: no
#%end

import os, sys, string, glob, shutil
import grass.script as grass
# add the folder containing libraries to python path
libmodis = os.path.join(os.getenv('GISBASE'), 'etc', 'r.modis')
sys.path.append(libmodis)
# try to import pymodis (modis) and some class for r.modis.download
try:
    from rmodislib import resampling, product, get_proj, projection
    from modis  import parseModis, convertModis, createMosaic
except ImportError:
    pass

def list_files(opt, mosaik=False):
    """Return a list of hdf files from the filelist on function single 
    Return a dictionary with a list o hdf file for each day on function mosaic
    """
    # read the file with the list of HDF
    if opt['files'] != '':
        listoffile = open(opt['files'],'r')
        basedir = os.path.split(listoffile.name)[0]
        # if mosaic create a dictionary
        if mosaik:
            filelist = {}
        # if not mosaic create a list
        else:
            filelist = []
        # append hdf files
        for line in listoffile:
            if string.find(line,'xml') == -1 and mosaik == False:
                filelist.append(line.strip())
            # for mosaic create a list of hdf files for each day
            elif string.find(line,'xml') == -1 and mosaik == True:
                day = line.split('/')[-1].split('.')[1]
                if filelist.has_key(day):
                    filelist[day].append(line)
                else:
                    filelist[day] = [line]
    # create a list for each file
    elif options['dns'] != '':
        filelist = [options['dns']]
        basedir = os.path.split(filelist[0])[0]
    return filelist, basedir

def spectral(opts,code,q):
    """Return spectral string"""
    # return the spectral set by the user
    if opts['spectral'] != '':
        spectr = opts['spectral']
    # return the spectral by default
    else:
        prod = product().fromcode(code)
        if q:
            spectr = prod['spec_qa']
        else:
            spectr = prod['spec']
    return spectr

def confile(hdf,opts,q,mosaik=False):
    """Create the configuration file for MRT software"""
    # create parseModis class and the parameter file
    pm = parseModis(hdf)
    # return projection and datum 
    projObj = projection()
    proj = projObj.returned()
    dat = projObj.datum()
    if proj == 'UTM':
        zone = projObj.utmzone()
    else:
        zone = None
    cod = os.path.split(hdf)[1].split('.')[0]
    if mosaik:
        # if mosaic import all because the layers are choosen during mosaic
        spectr = "( 1 1 1 1 1 1 1 1 1 1 1 1 )"
    else:
        spectr = spectral(opts, cod,q)
    # resampling
    resampl = resampling(opts['resampl']).returned()
    # projpar
    projpar = projObj.return_params()
    return pm.confResample(spectr, None, None, dat, resampl, proj, zone, projpar)

def import_tif(hdf,basedir,rem,target=False):
    """Import TIF files"""
    # prefix of HDF file
    prefix = os.path.split(hdf)[1].rstrip('.hdf')
    # list of tif files
    tifiles = glob.glob1(basedir, prefix + "*.tif")
    if not tifiles:
        grass.fatal(_('Error during the conversion'))
    # check if is in latlong location to set flag l
    if projection().val == 'll':
        f = "l"
    else:
        f = None
    # for each file import it
    for t in tifiles:
        basename = os.path.splitext(t)[0]
        name = os.path.join(basedir,t)
        try:
            grass.run_command('r.in.gdal', input = name, 
            output = basename, flags = f, overwrite = True, quiet = True)
            if rem:
                os.remove(name)
            if target:
                shutil.move(name,target)
        except:
            grass.fatal(_('Error during import'))
    return 0

def single(options,remove,qa):
    """Convert the hdf file to tif and import it
    """
    listfile, basedir = list_files(options)
    # for each file
    for i in listfile:
        # the full path to hdf file
        hdf = os.path.join(basedir,i)
        # create conf file fro mrt tools
        confname = confile(hdf,options,qa)
        # create convertModis class and convert it in tif file
        execmodis = convertModis(hdf,confname,options['mrtpath'])
        execmodis.run()
        # import tif files
        import_tif(i,basedir,remove)
        os.remove(confname)

    return grass.message(_('All files imported correctly'))

#def createXMLmosaic(listfiles):
    #modis.

def mosaic(options,remove,qa):
    """Create a daily mosaic of hdf files convert to tif and import it
    """
    dictfile, targetdir = list_files(options,True)
    # for each day
    for dat, listfiles in dictfile.iteritems():
        # create the file with the list of name
        tempfile = open(grass.tempfile(),'w')
        tempfile.writelines(listfiles)
        tempfile.close()
        # basedir of tempfile, where hdf files are write
        basedir = os.path.split(tempfile.name)[0]
        outname = "%s.%s.mosaic" % (listfiles[0].split('/')[-1].split('.')[0],
                                    listfiles[0].split('/')[-1].split('.')[1])
        # return the spectral subset in according mrtmosaic tool format
        spectr = spectral(options,listfiles[0].split('/')[-1].split('.')[0],qa)
        spectr = spectr.lstrip('( ').rstrip(' )')
        # create mosaic
        cm = createMosaic(tempfile.name,outname,options['mrtpath'],spectr)
        cm.run()
        # list of hdf files
        hdfdir = os.path.split(tempfile.name)[0]
        hdfiles = glob.glob1(hdfdir, outname + "*.hdf")
        for i in hdfiles:
            # the full path to hdf file
            hdf = os.path.join(hdfdir,i)
            # create conf file fro mrt tools
            confname = confile(hdf,options,qa,True)
            # create convertModis class and convert it in tif file
            execmodis = convertModis(hdf,confname,options['mrtpath'])
            execmodis.run()
            # remove hdf 
            if remove:
                # import tif files
                import_tif(i,basedir,remove)
                os.remove(hdf)
                os.remove(hdf + '.xml')
            # or move the hdf and hdf.xml to the dir where are the original files
            else:
                # import tif files
                import_tif(i,basedir,remove,targetdir)
                try: 
                    shutil.move(hdf,targetdir)
                    shutil.move(hdf + '.xml',targetdir)
                except:
                    pass
            # remove the conf file
            os.remove(confname)
        grass.try_remove(tempfile.name)
    return grass.message(_('All files imported correctly'))

def main():
    # check if you are in GRASS
    gisbase = os.getenv('GISBASE')
    if not gisbase:
        grass.fatal(_('$GISBASE not defined'))
        return 0
    # return an error if q and spectral are set
    if flags['q'] and options['spectral'] != '':
        grass.fatal(_('It is not possible set flag "q" and "spectral" option'))
        return 0
    # return an error if both dns and files option are set or not
    if options['dns'] == '' and options['files'] == '':
        grass.fatal(_('You have to choose one of "dns" or "files" options'))
        return 0
    elif options['dns'] != '' and options['files'] != '':
        grass.fatal(_('It is not possible set "dns" and "files" options together'))
        return 0
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version['version'].find('7.') == -1:
        grass.fatal(_('You are not in GRASS GIS version 7'))
        return 0
    # check if also qa layer are converted
    if flags['q']:
        qa_layer = True
    else:
        qa_layer = False
    # check if remove the files or not
    if flags['t']:
        remove = False
    else:
        remove = True
    # check if import simple file or mosaic
    if flags['m'] and options['dns'] != '':
        grass.fatal(_('It is not possible to create a mosaic with a single HDF file'))
        return 0
    elif flags['m']:
        mosaic(options,remove,qa_layer)
    else:
        single(options,remove,qa_layer)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
