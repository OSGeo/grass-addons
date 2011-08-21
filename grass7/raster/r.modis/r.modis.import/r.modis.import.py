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
#      -  MRT tools, https://lpdaac.usgs.gov/lpdaac/tools/modis_reprojection_tool
#
#############################################################################

#%module
#% description: Import single or more tiles of MODIS products using pyModis/MRT
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
#% description: Doesn't use the QA map, don't use with "r" flag
#%end
#%flag
#% key: r
#% description: Doesn't resampling the output map
#%end
#%option
#% key: mrtpath
#% type: string
#% key_desc: path
#% description: The full path to MRT directory
#% gisprompt: old,dir,input
#% required: yes
#%end
#%option
#% key: dns
#% type: string
#% key_desc: path
#% description: Path to single HDF file
#% gisprompt: old,file,input
#% required: no
#%end
#%option
#% key: files
#% type: string
#% key_desc: file
#% description: Path to a file with a list of HDF files 
#% gisprompt: old,file,input
#% required: no
#%end
#%option G_OPT_R_OUTPUT
#% required : no
#% guisection: Import
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

import os, sys, string, glob, shutil
import grass.script as grass
from datetime import date
# add the folder containing libraries to python path
libmodis = os.path.join(os.getenv('GISBASE'), 'etc', 'r.modis')
sys.path.append(libmodis)
# try to import pymodis (modis) and some class for r.modis.download
try:
    from rmodislib import resampling, product, get_proj, projection
    from modis  import parseModis, convertModis, createMosaic
except ImportError:
    pass

def list_files(opt, mosaik = False):
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

def spectral(opts, code, q, m = False):
    """Return spectral string"""
    # return the spectral set by the user
    if opts['spectral'] != '':
        spectr = opts['spectral']
    # return the spectral by default
    else:
        prod = product().fromcode(code)
        if m:
            spectr = prod['spec_all']
        elif q:
            if prod['spec_qa']:
                spectr = prod['spec_qa']
            else: 
                spectr = prod['spec']
        else:
            spectr = prod['spec']
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
    if mosaik:
        # if mosaic import all because the layers are choosen during mosaic
        spectr = spectral(opts, cod, q, True)
    else:
        spectr = spectral(opts, cod, q)
    # out prefix
    pref = prefix(opts)
    # resampling
    resampl = resampling(opts['resampl']).returned()
    # projpar
    projpar = projObj.return_params()
    return pm.confResample(spectr, None, pref, dat, resampl, proj, zone, projpar)

def prefix(options, name = False):
    """Return the prefix of output file if not set return None to use default
       value
    """
    if options['output']:
        return options['output']
    else:
        return None  

def import_tif(out, basedir, rem, write, target=None):
    """Import TIF files"""
    # list of tif files
    tifiles = glob.glob1(basedir, out + "*.tif")
    if not tifiles:
        grass.fatal(_('Error during the conversion'))
    # check if is in latlong location to set flag l
    if projection().val == 'll':
        f = "l"
    else:
        f = None
    outfile = []
    # for each file import it
    for t in tifiles:
        basename = os.path.splitext(t)[0]
        name = os.path.join(basedir,t)
        try:
            grass.run_command('r.in.gdal', input = name, output = basename,
                              flags = f, overwrite = write, quiet = True)
            outfile.append(basename)
        except:
            grass.fatal(_('Error during import'))
        if rem:
            os.remove(name)
        if target: 
            if target != basedir:
                shutil.move(name,target)
    return outfile

def findfile(pref, suff):
    """ Check if a file exists on mapset """
    if grass.find_file(pref + suff)['file']:
        return grass.find_file(pref + suff)
    else:
        grass.warning(_("Raster map <%s> not found") % (pref + suff))

def metadata(pars, mapp, coll):
    """ Set metadata to the imported files """
    # metadata
    meta = pars.metastring()
    grass.run_command('r.support', quiet = True, map=mapp, hist=meta)
    # timestamp
    rangetime = pars.retRangeTime()
    data = rangetime['RangeBeginningDate'].split('-')
    dataobj = date(int(data[0]),int(data[1]),int(data[2]))
    grass.run_command('r.timestamp', map=mapp, date=dataobj.strftime("%d %b %Y"),
                      quiet = True)
    # color
    if string.find(mapp, 'QA'):
        grass.run_command('r.colors', quiet = True, map=mapp, color = coll)
    elif string.find(mapp, 'NDVI'):
        grass.run_command('r.colors', quiet = True, map=mapp, color = coll[0])
    elif string.find(mapp, 'EVI'):
        grass.run_command('r.colors', quiet = True, map=mapp, color = coll[1])
    elif string.find(mapp, 'LST'):
        grass.run_command('r.colors', quiet = True, map=mapp, color = coll[0])
    elif string.find(mapp, 'Snow'):
        grass.run_command('r.colors', quiet = True, map=mapp, color = coll[0])

def analize(pref, an, cod, parse, write):
    """ Analiza the MODIS data using QA if present """
    prod = product().fromcode(cod)
    if not prod['spec_qa']:
        grass.warning(_("There is not QA file, analysis will be skipped"))
        an = 'noqa'
    pat = prod['pattern']
    suf = prod['suff']
    col = prod['color']
    val = []
    qa = []
    for v,q in suf.iteritems():
        val.append(findfile(pref,v))
        if q:
            qa.append(findfile(pref,q))
    grass.run_command('g.region', rast = val[0]['fullname'])

    for n in range(len(val)):
        valname = val[n]['name']
        valfull = val[n]['fullname']
        grass.run_command('r.null', map = valfull)
        if string.find(cod,'13Q1') or string.find(cod,'13A2'):
          mapc = "%s.2 = %s / 10000" % (valname, valfull)
          grass.mapcalc(mapc)
        elif string.find(cod,'11A1') or string.find(cod,'11A2') or string.find(cod,'11B1'):
          mapc = "%s.2 = (%s * 0.0200) - 273.15" % (valname, valfull)
          grass.mapcalc(mapc)
        if an == 'noqa':
            #grass.run_command('g.remove', quiet = True, rast = valfull)
            try:
                grass.run_command('g.rename', quiet = True, overwrite = write, 
                                  rast= (valname + '.2', valname + '.check'))
            except:
                pass
            #TODO check in modis.py to adjust the xml file of mosaic
            #metadata(parse, valname, col)
            #metadata(parse, valname + '.check', col)
            #metadata(parse, qafull, 'byr')
        if an == 'all':
            if len(qa) != len(val):
                grass.fatal(_("The number of QA and value maps is different, something wrong"))
            qaname = qa[n]['name']
            qafull = qa[n]['fullname']
            finalmap = "%s.3=if(" % valname
            for key,value in prod['pattern'].iteritems():
                for v in value:
                  outpat = "%s.%i.%i" % (qaname, key, v)
                  grass.run_command('r.bitpattern', quiet = True, input = qafull, 
                                    output = outpat, pattern = key, patval= v)
                  finalmap += "%s == 0 && " % outpat
            if string.find(cod,'13Q1') or string.find(cod,'13A2'):
                finalmap += "%s.2 <= 1.000" % valname
            else:
                finalmap.rstrip(' && ')
            finalmap += ",%s.2, null() )" % valname
            grass.mapcalc(finalmap)
            #grass.run_command('g.remove', quiet = True, rast=(valname, valname + '.2'))
            grass.run_command('g.remove', quiet = True, rast=(valname + '.2'))
            grass.run_command('g.mremove', flags="f", quiet = True,
			      rast = ("%s.*" % qaname))
            grass.run_command('g.rename', quiet = True, overwrite = write,
                              rast=(valname + '.3', valname + '.check'))
            #TODO check in modis.py to adjust the xml file of mosaic
            #metadata(parse, valname, col)
            #metadata(parse, valname + '.check', col)
            #metadata(parse, qafull, 'byr')
            
def single(options,remove,an,ow):
    """Convert the hdf file to tif and import it
    """
    listfile, basedir = list_files(options)
    # for each file
    for i in listfile:
        # the full path to hdf file
        hdf = os.path.join(basedir,i)
        # create conf file fro mrt tools
        pm = parseModis(hdf)
        confname = confile(pm,options,an)
        # create convertModis class and convert it in tif file
        execmodis = convertModis(hdf,confname,options['mrtpath'])
        execmodis.run()
        output = prefix(options)
        if not output:
            output = os.path.split(hdf)[1].rstrip('.hdf')
        # import tif files
        maps_import = import_tif(output,basedir,remove,ow)
        if an:
            cod = os.path.split(pm.hdfname)[1].split('.')[0]
            analize(output, an, cod, pm, ow)
        os.remove(confname)
    return grass.message(_('All files imported correctly'))

def mosaic(options,remove,an,ow):
    """Create a daily mosaic of hdf files convert to tif and import it
    """
    dictfile, targetdir = list_files(options,True)
    # for each day
    for dat, listfiles in dictfile.iteritems():
        # create the file with the list of name
        tempfile = open(os.path.join(targetdir,str(os.getpid())),'w')
        tempfile.writelines(listfiles)
        tempfile.close()
        # basedir of tempfile, where hdf files are write
        basedir = os.path.split(tempfile.name)[0]
        outname = "%s.%s.mosaic" % (listfiles[0].split('/')[-1].split('.')[0],
                                    listfiles[0].split('/')[-1].split('.')[1])
        # return the spectral subset in according mrtmosaic tool format
        spectr = spectral(options,listfiles[0].split('/')[-1].split('.')[0],an, True)
        spectr = spectr.lstrip('( ').rstrip(' )')
        # create mosaic
        cm = createMosaic(tempfile.name, outname, options['mrtpath'], spectr)
        cm.run()
        # list of hdf files
        hdfiles = glob.glob1(basedir, outname + "*.hdf")
        for i in hdfiles:
            # the full path to hdf file
            hdf = os.path.join(basedir,i)
            # create conf file fro mrt tools
            pm = parseModis(hdf)
            confname = confile(pm,options,an)
            # create convertModis class and convert it in tif file
            execmodis = convertModis(hdf, confname, options['mrtpath'])
            execmodis.run()
            # remove hdf 
            if remove:
                # import tif files
                import_tif(outname, basedir, remove, ow)
                if an:
                    cod = os.path.split(pm.hdfname)[1].split('.')[0]
                    analize(outname, an, cod, pm, ow)
                os.remove(hdf)
                os.remove(hdf + '.xml')
            # or move the hdf and hdf.xml to the dir where are the original files
            else:
                # import tif files
                import_tif(outname, basedir, remove, ow, targetdir)
                if an:
                    cod = os.path.split(pm.hdfname)[1].split('.')[0]
                    analize(outname, an, cod, pm, ow)
                try: 
                    shutil.move(hdf,targetdir)
                    shutil.move(hdf + '.xml',targetdir)
                except:
                    pass
            # remove the conf file
            os.remove(confname)
        grass.try_remove(tempfile.name)
        grass.try_remove(os.path.join(targetdir,'mosaic',str(os.getpid())))
    return grass.message(_('All files imported correctly'))

def main():
    # check if you are in GRASS
    gisbase = os.getenv('GISBASE')
    if not gisbase:
        grass.fatal(_('$GISBASE not defined'))
        return 0
    # return an error if q and spectral are set
    if not flags['q'] and options['spectral'] != '':
        grass.warning(_('If you have not choose QA layer in the "spectral" option'\
        + 'the command would be report an error'))
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
    # check if remove the files or not
    if flags['t']:
        remove = False
    else:
        remove = True
    if grass.overwrite():
        over = True
    else:
        over = False
    # check if do check quality, resampling and setting of color
    if flags['r']:
        analize = None
    elif flags['q']:
        analize = 'noqa'
    else:
        analize = 'all'
    # check if import simple file or mosaic
    if flags['m'] and options['dns'] != '':
        grass.fatal(_('It is not possible to create a mosaic with a single HDF file'))
        return 0
    elif flags['m']:
        mosaic(options,remove,analize,over)
    else:
        single(options,remove,analize,over)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
