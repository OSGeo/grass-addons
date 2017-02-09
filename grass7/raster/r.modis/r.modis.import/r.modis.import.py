#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:        r.modis.import
# AUTHOR(S):     Luca Delucchi
# PURPOSE:       r.modis.import is an interface to pyModis for import into
#                GRASS GIS level 3 MODIS produts
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
#   -  MRT tools, https://lpdaac.usgs.gov/lpdaac/tools/modis_reprojection_tool
#
#############################################################################

#%module
#% description: Import single or multiple tiles of MODIS products using pyModis
#% keyword: raster
#% keyword: MODIS
#%end
#%flag
#% key: m
#% description: Create a mosaic for each date
#%end
#%flag
#% key: t
#% description: Preserve temporary files (TIF and HDF mosaic)
#%end
#%flag
#% key: q
#% description: Ignore the QA map layer
#%end
#%flag
#% key: w
#% description: Create a text file to use into t.register
#%end

#%option
#% key: input
#% type: string
#% key_desc: path
#% description: Full path to single HDF file
#% gisprompt: old,file,input
#% required: no
#%end
#%option G_OPT_F_INPUT
#% key: files
#% description: Full path to file with list of HDF files
#% required: no
#%end
#%option
#% key: method
#% type: string
#% key_desc: resampling
#% description: Name of spatial resampling method
#% options: nearest, bilinear, cubic
#% answer: nearest
#% required: no
#%end
#%option
#% key: mrtpath
#% type: string
#% key_desc: path
#% description: Full path to MRT directory
#% gisprompt: old,dir,input
#% required: no
#%end
#%option
#% key: spectral
#% type: string
#% key_desc: spectral subset
#% description: String of the form "( 1 0 1 0 )" to choose a subset of HDF layers to import
#% required: no
#%end

import os
import sys
import string
import glob
import shutil
import grass.script as grass
from datetime import datetime
from datetime import timedelta
from grass.pygrass.utils import get_lib_path
import tempfile
path = get_lib_path(modname='r.modis', libname='libmodis')
if path is None:
    grass.fatal("Not able to find the modis library directory.")
sys.path.append(path)


class grassParseModis:
    """Class to reproduce parseModis class when VRT is used for mosaic

       :param str filename: the name of MODIS hdf file
    """

    def __init__(self, filename, date):
        self.hdfname = filename
        self.date = date

    def retRangeTime(self):
        return {'RangeBeginningDate': self.date}


def list_files(opt, mosaik=False):
    """If used in function single(): Return a list of HDF files from the file
    list. If used in function mosaic(): Return a dictionary with a list of HDF
    files for each day
    """
    # read the file with the list of HDF
    if opt['files'] != '':
        listoffile = open(opt['files'], 'r')
        basedir = os.path.split(listoffile.name)[0]
        # if mosaic create a dictionary
        if mosaik:
            filelist = {}
        # if not mosaic create a list
        else:
            filelist = []
        # append hdf files
        for line in listoffile:
            if string.find(line, 'xml') == -1 and mosaik is False:
                filelist.append(line.strip())
            # for mosaic create a list of hdf files for each day
            elif string.find(line, 'xml') == -1 and mosaik is True:
                day = line.split('/')[-1].split('.')[1]
                if day in filelist:
                    filelist[day].append(line.strip())
                else:
                    filelist[day] = [line.strip()]
    # create a list for each file
    elif options['input'] != '':
        filelist = [options['input']]
        basedir = os.path.split(filelist[0])[0]
    return filelist, basedir


def spectral(opts, prod, q, m=False):
    """Return spectral string"""
    # return the spectral set selected by the user
    if opts['spectral'] != '':
        spectr = opts['spectral']
    # return the spectral by default
    else:
        if q:
            if prod['spec_qa']:
                spectr = prod['spec_qa']
            else:
                spectr = prod['spec']
        else:
            spectr = prod['spec']
        if m:
            spectr = spectr.replace(' 0', '')
    return spectr


def confile(pm, opts, q, mosaik=False):
    """Create the configuration file for MRT software"""
    # return projection and datum
    projObj = projection()
    proj = projObj.returned()
    dat = projObj.datum()
    if proj == 'UTM':
        zone = projObj.utmzone()
    else:
        zone = None
    cod = os.path.split(pm.hdfname)[1].split('.')[0]
    prod = product().fromcode(cod)
    if mosaik:
        # if mosaic it remove all the 0 from the subset string to convert all
        # the right layer
        spectr = spectral(opts, prod, q, True)
    else:
        spectr = spectral(opts, prod, q)
    # out prefix
    pref = prefix(opts)
    # resampling
    resampl = resampling(opts['method']).returned()
    # projpar
    projpar = projObj.return_params()
    if projpar != "( 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 )":
        dat = "NODATUM"
    # resolution
    if proj != 'GEO':
        res = int(prod['res']) * int(projObj.proj['meters'])
    else:
        res = None
    try:
        conf = pm.confResample(spectr, res, pref, dat, resampl,
                               proj, zone, projpar)
        return conf
    except IOError, e:
        grass.fatal(e)


def metadata(pars, mapp):
    """ Set metadata to the imported files """
    # metadata
    grass.run_command('r.support', quiet=True, map=mapp, source1="MODIS NASA",
                      hist="Imported with r.modis.import")
    # timestamp
    rangetime = pars.retRangeTime()
    data = rangetime['RangeBeginningDate'].split('-')
    dataobj = datetime(int(data[0]), int(data[1]), int(data[2]))
    grass.run_command('r.timestamp', map=mapp, quiet=True,
                      date=dataobj.strftime("%d %b %Y"))
    return dataobj
    # color
#    if string.find(mapp, 'QC') != -1 or string.find(mapp, 'Quality') != -1 or \
#    string.find(mapp, 'QA') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll)
#    elif string.find(mapp, 'NDVI') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[0])
#    elif string.find(mapp, 'EVI') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[1])
#    elif string.find(mapp, 'LST') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[0])
#    elif string.find(mapp, 'Snow') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[0])


def modis_prefix(inp, mosaic=False):
    """return the modis prefix"""
    modlist = os.path.split(inp)[1].split('.')
    if mosaic:
        return '.'.join(modlist[:2])
    else:
        return '.'.join(modlist[:3])


def import_tif(basedir, rem, write, pm, prod, target=None, listfile=None):
    """Import TIF files"""
    # list of tif files
    pref = modis_prefix(pm.hdfname)
    tifiles = glob.glob1(basedir, "{pr}*.tif".format(pr=pref))
    if not tifiles:
        tifiles = glob.glob1(os.getcwd(), "{pr}*.tif".format(pr=pref))
    if not tifiles:
        grass.fatal(_('Error during the conversion'))
    # check if user is in latlong location to set flag l
    if projection().val == 'll':
        f = "l"
    else:
        f = None
    outfile = []
    # for each file import it
    for t in tifiles:
        basename = os.path.splitext(t)[0]
        basename = basename.replace(' ', '_')
        name = os.path.join(basedir, t)
        if not os.path.exists(name):
            name = os.path.join(os.getcwd(), t)
        if not os.path.exists(name):
            grass.warning(_("File %s doesn't find" % name))
            continue
        filesize = int(os.path.getsize(name))
        if filesize < 1000:
            grass.warning(_('Probably some error occur during the conversion'
                            'for file <%s>. Escape import' % name))
            continue
        try:
            grass.run_command('r.in.gdal', input=name, output=basename,
                              overwrite=write, quiet=True)
            outfile.append(basename)
        except:
            grass.warning(_('Error during import of %s' % basename))
            continue
        data = metadata(pm, basename)
        if rem:
            os.remove(name)
        if target:
            if target != basedir:
                shutil.move(name, target)
        if listfile:
            fdata = data + timedelta(prod['days'])
            listfile.write("{name}|{sd}|{fd}\n".format(name=basename,
                                                       sd=data.strftime("%Y-%m-%d"),
                                                       fd=fdata.strftime("%Y-%m-%d")))
    return outfile


def findfile(pref, suff):
    """ Check if a file exists on mapset """
    if grass.find_file(pref + suff)['file']:
        return grass.find_file(pref + suff)
    else:
        grass.warning(_("Raster map <%s> not found") % (pref + suff))


def doy2date(modis):
    """From he MODIS code to YYYY-MM-DD string date"""
    year = modis[:4]
    doy = modis[-3:]
    dat = datetime.strptime('{ye} {doy}'.format(ye=year,  doy=doy), '%Y %j')
    return dat.strftime('%Y-%m-%d')

def single(options, remove, an, ow, fil):
    """Convert the HDF file to TIF and import it
    """
    listfile, basedir = list_files(options)
    # for each file
    for i in listfile:
        if os.path.exists(i):
            hdf = i
        else:
            # the full path to hdf file
            hdf = os.path.join(basedir, i)
            if not os.path.exists(hdf):
                grass.warning(_("%s not found" % i))
                continue
        pm = parseModis(hdf)
        if options['mrtpath']:
            # create conf file fro mrt tools
            confname = confile(pm, options, an)
            # create convertModis class and convert it in tif file
            execmodis = convertModis(hdf, confname, options['mrtpath'])
        else:
            projwkt = get_proj('w')
            projObj = projection()
            pref = i.split('/')[-1]
            prod = product().fromcode(pref.split('.')[0])
            spectr = spectral(options, prod, an)
            if projObj.returned() != 'GEO':
                res = int(prod['res']) * int(projObj.proj['meters'])
            else:
                res = None
            outname = "%s.%s.%s.single" % (pref.split('.')[0],
                                           pref.split('.')[1],
                                           pref.split('.')[2])
            outname = outname.replace(' ', '_')
            execmodis = convertModisGDAL(hdf, outname, spectr, res,
                                         wkt=projwkt)
        execmodis.run()
        import_tif(basedir=basedir, rem=remove, write=ow, pm=pm,
                   listfile=fil, prod=prod)
        if options['mrtpath']:
            os.remove(confname)


def mosaic(options, remove, an, ow, fil):
    """Create a daily mosaic of HDF files convert to TIF and import it
    """
    dictfile, targetdir = list_files(options, True)
    pid = str(os.getpid())
    # for each day
    for dat, listfiles in dictfile.iteritems():
        pref = listfiles[0].split('/')[-1]
        prod = product().fromcode(pref.split('.')[0])
        spectr = spectral(options, prod, an)
        spectr = spectr.lstrip('( ').rstrip(' )')
        outname = "%s.%s_mosaic" % (pref.split('.')[0], pref.split('.')[1])
        outname = outname.replace(' ', '_')
        # create mosaic
        if options['mrtpath']:
            # create the file with the list of name
            tempfile = open(os.path.join(targetdir, pid), 'w')
            tempfile.writelines(listfiles)
            tempfile.close()
            # basedir of tempfile, where hdf files are write
            basedir = os.path.split(tempfile.name)[0]
            # return the spectral subset in according mrtmosaic tool format
            cm = createMosaic(tempfile.name, outname, options['mrtpath'],
                              spectr)
            cm.run()
            hdfiles = glob.glob1(basedir, outname + "*.hdf")
        else:
            basedir = targetdir
            listfiles = [os.path.join(basedir, i) for i in listfiles]
            cm = createMosaicGDAL(listfiles, spectr)
            cm.write_vrt(outname)
            hdfiles = glob.glob1(basedir, outname + "*.vrt")
        for i in hdfiles:
            # the full path to hdf file
            hdf = os.path.join(basedir, i)
            try:
                pm = parseModis(hdf)
            except:
                out = i.replace('.vrt', '')
                data = doy2date(dat[1:])
                pm = grassParseModis(out, data)
            # create convertModis class and convert it in tif file
            if options['mrtpath']:
                # create conf file fro mrt tools
                confname = confile(pm, options, an, True)
                execmodis = convertModis(hdf, confname, options['mrtpath'])
            else:
                confname = None
                projwkt = get_proj('w')
                projObj = projection()
                if projObj.returned() != 'GEO':
                    res = int(prod['res']) * int(projObj.proj['meters'])
                else:
                    res = None
                execmodis = convertModisGDAL(hdf, out, spectr, res, wkt=projwkt,
                                             vrt=True)
            execmodis.run()
            # remove hdf
            if remove:
                # import tif files
                import_tif(basedir=basedir, rem=remove, write=ow,
                           pm=pm, listfile=fil, prod=prod)
                try:
                    os.remove(hdf)
                    os.remove(hdf + '.xml')
                except OSError:
                    pass
            # move the hdf and hdf.xml to the dir where are the original files
            else:
                # import tif files
                import_tif(basedir=basedir, rem=remove, write=ow,
                           pm=pm, target=targetdir, listfile=fil, prod=prod)
                try:
                    shutil.move(hdf, targetdir)
                    shutil.move(hdf + '.xml', targetdir)
                except OSError:
                    pass
            # remove the conf file
            try:
                os.remove(confname)
            except (OSError, TypeError) as e:
                pass
        if options['mrtpath']:
            grass.try_remove(tempfile.name)
        grass.try_remove(os.path.join(targetdir, 'mosaic', pid))


def main():

    try:
        # try to import pymodis (modis) and some classes for r.modis.download
        from rmodislib import resampling, product, projection, get_proj
        from convertmodis import convertModis, createMosaic
        from convertmodis_gdal import createMosaicGDAL, convertModisGDAL
        from parsemodis import parseModis
    except:
        grass.fatal("r.modis library is not installed")
    # check if you are in GRASS
    gisbase = os.getenv('GISBASE')
    if not gisbase:
        grass.fatal(_('$GISBASE not defined'))
        return 0
    # return an error if q and spectral are set
    if not flags['q'] and options['spectral'] != '':
        grass.warning(_('If no QA layer chosen in the "spectral" option'
                        ' the command will report an error'))
    # return an error if both input and files option are set or not
    if options['input'] == '' and options['files'] == '':
        grass.fatal(_('Choose one of "input" or "files" options'))
        return 0
    elif options['input'] != '' and options['files'] != '':
        grass.fatal(_('It is not possible set "input" and "files"'
                      ' options together'))
        return 0
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version['version'].find('7.') == -1:
        grass.fatal(_('GRASS GIS version 7 required'))
        return 0
    # check if remove the files or not
    if flags['t']:
        remove = False
    else:
        remove = True
    if grass.overwrite():
        over = True
    else:
        over = False
    # check if do check quality, rescaling and setting of colors
    if flags['q']:
        analyze = False
    else:
        analyze = True
    if options['spectral']:
        count = options['spectral'].strip('(').strip(')').split().count('1')
    else:
        count = 0
    outfile = None
    if flags['w'] and count == 1:
        outfile = tempfile.NamedTemporaryFile(delete=False)
    elif flags['w'] and count != 1:
        grass.warning(_("To use correctly the file in t.rast.import you have "
                        "to select only a subset in the 'spectral' option. "
                        "Out file will be not created"))
    # check if import simple file or mosaic
    if flags['m'] and options['input'] != '':
        grass.fatal(_('It is not possible to create a mosaic with a single'
                      ' HDF file'))
        return 0
    elif flags['m']:
        mosaic(options, remove, analyze, over, outfile)
    else:
        single(options, remove, analyze, over, outfile)
    if outfile:
        outfile.close()
        grass.message(_("You can continue with temporal framework, registering"
                        " the maps using t.register "
                        "'file={name}'".format(name=outfile.name)))

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
