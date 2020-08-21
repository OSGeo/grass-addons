#!/usr/bin/env python3

############################################################################
#
# MODULE:       i.sentinel.coverage
#
# AUTHOR(S):    Anika Bettge <bettge at mundialis.de>
#
# PURPOSE:      Checks the area coverage of the by filters selected Sentinel
#               scenes
#
# COPYRIGHT:	(C) 2020 by mundialis and the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#% description: checks the area coverage of the by filters selected Sentinel scenes.
#% keyword: imagery
#% keyword: Sentinel
#% keyword: geometry
#% keyword: spatial query
#% keyword: area
#%end

#%option G_OPT_F_INPUT
#% key: settings
#% label: Full path to settings file (user, password)
#%end

#%option G_OPT_V_INPUT
#% key: area
#% description: Area input vector maps
#%end

#%option
#% key: start
#% type: string
#% description: Start date ('YYYY-MM-DD')
#% guisection: Filter
#%end

#%option
#% key: end
#% type: string
#% description: End date ('YYYY-MM-DD')
#% guisection: Filter
#%end

#%option
#% key: type
#% type: string
#% description: Sentinel-1 or -2
#% guisection: Filter
#% required: no
#% multiple: no
#% options: s1,s2
#% answer: s2
#%end

#%option
#% key: clouds
#% type: integer
#% required: no
#% multiple: no
#% description: Maximum cloud cover percentage for Sentinel scene
#% guisection: Filter
#%end

#%option
#% key: minpercent
#% type: integer
#% required: no
#% multiple: no
#% description: Minimal percentage of coverage; otherwise an error is thrown
#% guisection: Filter
#%end

#%option
#% key: names
#% type: string
#% description: Sentinel-1 or -2 names
#% guisection: Filter
#% required: no
#% multiple: yes
#%end

#%option G_OPT_F_OUTPUT
#% key: output
#% label: Output file with a list of Sentinel scene names
#% required: no
#%end

import atexit
import os
from datetime import datetime, timedelta

import grass.script as grass

# initialize global vars
rm_regions = []
rm_vectors = []
rm_rasters = []


def cleanup():
    nuldev = open(os.devnull, 'w')
    kwargs = {
        'flags': 'f',
        'quiet': True,
        'stderr': nuldev
    }
    for rmr in rm_regions:
        if rmr in [x for x in grass.parse_command('g.list', type='region')]:
            grass.run_command(
                'g.remove', type='region', name=rmr, **kwargs)
    for rmv in rm_vectors:
        if grass.find_file(name=rmv, element='vector')['file']:
            grass.run_command(
                'g.remove', type='vector', name=rmv, **kwargs)
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element='raster')['file']:
            grass.run_command(
                'g.remove', type='raster', name=rmrast, **kwargs)


def scenename_split(scenename):
    '''
    When using the query option in i.sentinel.filename and defining
    specific filenames, the parameters Producttype, Start-Date, and End-Date
    have to be definied as well.This function extracts these parameters from a
    Sentinel-2 filename and returns the proper string to be passed to the query
    option.
    Args:
        scenename(string): Name of the scene in the format
                           S2A_MSIL1C_20180822T155901_N0206_R097_T17SPV_20180822T212023
    Returns:
        producttype(string): Sentinel-2 producttype in the required parameter
                             format for i.sentinel.download, e.g. S2MSI2A
        start_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date -1 day
        end_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date +1 day

    '''
    try:
        ### get producttype
        name_split = scenename.split('_')
        type_string = name_split[1]
        level_string = type_string.split('L')[1]
        producttype = 'S2MSI' + level_string
        ### get dates
        date_string = name_split[2].split('T')[0]
        dt_obj = datetime.strptime(date_string,"%Y%m%d")
        start_day_dt = dt_obj - timedelta(days=1)
        end_day_dt = dt_obj + timedelta(days=1)
        start_day = start_day_dt.strftime('%Y-%m-%d')
        end_day = end_day_dt.strftime('%Y-%m-%d')
    except:
        grass.fatal("The name of the scene must have a format of e.g. S2A_MSIL1C_YYYYMMDDT155901_N0206_R097_T17SPV_20180822T212023")
    return producttype, start_day, end_day


def get_size(vector):
    tmpvector = 'tmp_getsize_%s' % str(os.getpid())
    rm_vectors.append(tmpvector)
    grass.run_command(
        'g.copy', vector="%s,%s" % (vector, tmpvector), quiet=True)
    if len(grass.vector_db(tmpvector)) == 0:
        grass.run_command('v.db.addtable', map=tmpvector, quiet=True)
    grass.run_command(
        'v.db.addcolumn', map=tmpvector,
        columns="tmparea DOUBLE PRECISION", quiet=True)
    grass.run_command(
        'v.to.db', map=tmpvector, columns='tmparea', option='area',
        units='meters', quiet=True, overwrite=True)
    sizeselected = grass.parse_command('v.db.select', map=tmpvector, flags="v")
    sizesstr = [x.split('|')[1:] for x in sizeselected if x.startswith('tmparea|')][0]
    sizes = [float(x) for x in sizesstr]
    return sum(sizes)


def main():

    global rm_regions, rm_rasters, rm_vectors

    ### check if we have the i.sentinel.download + i.sentinel.import addons
    if not grass.find_program('i.sentinel.download', '--help'):
        grass.fatal(_("The 'i.sentinel.download' module was not found, install it first:") +
                    "\n" +
                    "g.extension i.sentinel")
    if not grass.find_program('i.sentinel.import', '--help'):
        grass.fatal(_("The 'i.sentinel.import' module was not found, install it first:") +
                    "\n" +
                    "g.extension i.sentinel")

    # parameters
    settings = options['settings']
    output = options['output']
    area = options['area']
    if options['type'] == 's1':
        producttype = 'GRD'
    else:
        producttype = 'S2MSI2A'

    grass.message(_("Retrieving Sentinel footprints from ESA hub ..."))
    fps = 'tmp_fps_%s' % str(os.getpid())
    rm_vectors.append(fps)
    if not options['names']:
        s_list = grass.parse_command(
            'i.sentinel.download',
            settings=settings,
            map=area,
            clouds=options['clouds'],
            producttype=producttype,
            start=options['start'],
            end=options['end'],
            footprints=fps,
            flags='lb',
            quiet=True)
        if len(s_list) == 0:
            grass.fatal('No products found')
        name_list = [x.split(' ')[1] for x in s_list]
    else:
        name_list = []
        fp_list = []
        for name in options['names'].split(','):
            real_producttype, start_day, end_day = scenename_split(name)
            if real_producttype != producttype:
                grass.fatal("Producttype of ")
            fpi = 'tmp_fps_%s_%s' % (name, str(os.getpid()))
            try:
                grass.run_command(
                    'i.sentinel.download',
                    settings=settings,
                    map=area,
                    producttype=producttype,
                    footprints=fpi,
                    start=start_day,
                    end=end_day,
                    flags='bl',
                    quiet=True)
                name_list.append(name)
                fp_list.append(fpi)
                rm_vectors.append(fpi)
            except:
                grass.warning('%s was not found in %s' % (name, area))
        grass.run_command(
            'v.patch', input=','.join(fp_list), output=fps, quiet=True)

    grass.message(_("Getting size of %s ...") % area)
    areasize = get_size(area)

    grass.message(_("Getting size of footprints in %s ...") % area)
    fps_in_area = 'tmp_fps_in_area_%s' % str(os.getpid())
    rm_vectors.append(fps_in_area)
    grass.run_command(
        'v.overlay', ainput=fps, atype='area', binput=area, operator='and',
         output=fps_in_area, quiet=True)
    grass.run_command(
        'v.db.addcolumn', map=fps_in_area, columns="tmp INTEGER", quiet=True)
    grass.run_command(
        'v.db.update', map=fps_in_area, column='tmp', value=1, quiet=True)
    fps_in_area_dis = 'tmp_fps_in_area_dis_%s' % str(os.getpid())
    rm_vectors.append(fps_in_area_dis)
    grass.run_command(
        'v.dissolve', input=fps_in_area, output=fps_in_area_dis,
        column='tmp', quiet=True)
    grass.run_command(
        'v.db.addtable', map=fps_in_area_dis, quiet=True)
    fpsize = get_size(fps_in_area_dis)

    percent = fpsize / areasize * 100.0
    grass.message(_("%.2f percent of the %s is covered") % (percent, area))

    if options['minpercent']:
        if percent < int(options['minpercent']):
            grass.fatal("The percentage of coverage is to low")

    # save list of Sentinel names
    if output:
        with open(output, 'w') as f:
            f.write(','.join(name_list))
        grass.message(_(
            "Name of Sentinel scenes are written to <%s>") % (output))

    # TODO Sentinel-1 select only "one" scene (no overlap)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
