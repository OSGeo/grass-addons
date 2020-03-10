#!/usr/bin/env python

"""
MODULE:    v.rast.bufferstats

AUTHOR(S): Stefan Blumentrath < stefan.blumentrath AT nina.no>
           With lots of inspiration from v.what.rast.buffer by
           Hamish Bowman, Dunedin, New Zealand

PURPOSE:   Calculates statistics of raster map(s) for buffers around vector geometries.

COPYRIGHT: (C) 2018 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.


To Dos:
- consider adding distance weights
- add neighborhood stats ???
- silence r.category
- add where clause

/#%option G_OPT_DB_WHERE
/#% required: no
/#%end

    where = options['where']

"""

#%Module
#% label: Calculates statistics of raster map(s) for buffers around vector geometries.
#% keyword: vector
#% keyword: raster
#% keyword: buffer
#% keyword: statistics
#%End

#%option G_OPT_V_INPUT
#% description: Vector map containing geometries to compute buffer statistics for
#%end

#%option G_OPT_R_INPUTS
#% key: raster
#% description: Raster map(s) to calculate statistics from
#% multiple: yes
#% required : yes
#%end

#%option
#% key: buffers
#% type: integer
#% description: Buffer distance(s) in map units
#% multiple: yes
#% required : yes
#%end

#%option
#% key: type
#% type:string
#% description: Vector type to work on
#% options: points,lines,areas
#% answer: points,lines,areas
#% multiple: yes
#% required: yes
#%end

## ,centroid not supported in pygrass

#%option G_OPT_V_FIELD
#% required: no
#%end

#%option
#% key: column_prefix
#% type: string
#% description: Column prefix for new attribute columns
#% required : yes
#% multiple: yes
#%end

#%option
#% key: methods
#% type: string
#% description: The methods to use
#% required: no
#% multiple: yes
#% options: number,number_null,minimum,maximum,range,sum,average,average_abs,stddev,variance,coeff_var,first_quartile,median,third_quartile
#% answer: number,number_null,minimum,maximum,range,sum,average,average_abs,stddev,variance,coeff_var,first_quartile,median,third_quartile
#%end

#%option
#% key: percentile
#% type: integer
#% description: Percentile to calculate
#% options: 0-100
#% required : no
#%end

#%flag
#% key: t
#% description: Tabulate area within buffers for categories in raster map(s)
#%end

#%flag
#% key: p
#% description: Used with -t flag will return percentage of area for categories
#%end

#%flag
#% key: u
#% description: Update columns if they already exist
#%end

#%flag
#% key: r
#% description: Remove columns without data
#%end

#%option G_OPT_F_OUTPUT
#% description: Name for output file (if "-" output to stdout)
#% required: no
#%end

#%option G_OPT_F_SEP
#% description: Field separator in output file
#% answer: |
#% required: no
#%end

import sys
import os
import atexit
import math
from subprocess import PIPE
import grass.script as grass
from grass.pygrass.vector import VectorTopo
from grass.pygrass.raster.abstract import RasterAbstractBase
from grass.pygrass.gis import Mapset
from grass.pygrass.vector.geometry import Boundary
from grass.pygrass.vector.geometry import Centroid
from grass.pygrass.gis.region import Region
#from grass.pygrass.vector.table import *
from grass.pygrass.modules.interface.module import Module
from itertools import chain

if not "GISBASE" in os.environ.keys():
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

TMP_MAPS = []

def cleanup():
    """Remove temporary data
    """
    #remove temporary region file
    try:
        grass.run_command('g.remove', flags='f', name=TMP_MAPS,
                          quiet=True, type=['vector', 'raster'],
                          stderr=os.devnull, stdout_=os.devnull)
    except:
        pass

    try:
        grass.run_command('g.remove', flags='f', name='MASK',
                          quiet=True, type='raster',
                          stderr=os.devnull, stdout_=os.devnull)
    except:
        pass

def align_current(region, bbox):
    """Align current region to bounding box

    :param region: PyGRASS Region object
    :param bbox: PyGRASS Bbox object
    :returns: adjusted PyGRASS Region object
    :type region: PyGRASS Region object
    :type bbox: PyGRASS Bbox object
    :rtype: dict

    :Example:

    >>> align_current(region, bbox)
    region
    """
    north = region.north
    east = region.east
    west = region.west
    south = region.south
    nsres = region.nsres
    ewres = region.ewres

    region.north = north - (math.floor((north - bbox.north) / nsres)
                            * nsres)
    region.south = south - (math.ceil((south - bbox.south) / nsres)
                            * nsres)
    region.east = east - (math.floor((east - bbox.east) / ewres)
                          * ewres)
    region.west = west - (math.ceil((west - bbox.west) / ewres)
                          * ewres)

    return region

def random_name(length):
    """Generate a random name of length "length" starting with a letter

    :param length: length of the random name to generate
    :returns: String with a random name of length "length" starting with a letter
    :type length: int
    :rtype: string

    :Example:

    >>> random_name(12)
    'MxMa1kAS13s9'
    """

    import string
    import random
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    randomname = '1'
    while randomname[0].isdigit():
        randomname = ''.join(random.choice(chars) for _ in range(length))

    return randomname

def raster_type(raster):
    """Check raster map type (int or double) and return categories for int maps

    :param raster: name of the raster map to check
    :returns: string with raster map type and list of categories with lables
    :type raster: string
    :rtype: string
    :rtype: list

    :Example:

    >>> raster_type('elevation')
    'double precision', []
    """
    rcats = []
    try:
        rcats = grass.read_command('r.category', map=raster,
                                   quiet=True).rstrip('\n').split('\n')
        rmap_type = 'int'
    except:
        pass

    if len(rcats) == 0:
        rmap_type = 'double precision'

    return rmap_type, rcats

def main():
    in_vector = options['input'].split('@')[0]
    if len(options['input'].split('@')) > 1:
        in_mapset = options['input'].split('@')[1]
    else:
        in_mapset = None
    raster_maps = options['raster'].split(',')   # raster file(s) to extract from
    output = options['output']
    methods = tuple(options['methods'].split(','))
    percentile = None if options['percentile'] == '' else map(float, options['percentile'].split(','))
    column_prefix = tuple(options['column_prefix'].split(','))
    buffers = options['buffers'].split(',')
    types = options['type'].split(',')
    layer = options['layer']
    sep = options['separator']
    update = flags['u']
    tabulate = flags['t']
    percent = flags['p']
    remove = flags['r']

    mymapset = Mapset().name
    # Do checks using pygrass
    for rmap in raster_maps:
        r_map = RasterAbstractBase(rmap)
        if not r_map.exist():
            grass.fatal('Could not find raster map {}.'.format(rmap))
    m_map = RasterAbstractBase('MASK@{}'.format(mymapset))
    if m_map.exist():
        grass.fatal("Please remove MASK first")

    invect = VectorTopo(in_vector)
    if not invect.exist():
        grass.fatal("Vector file {} does not exist".format(in_vector))

    if output:
        if output == '-':
            out = None
        else:
            out = open(output, 'w')

    # Check if input map is in current mapset (and thus editable)
    if in_mapset and unicode(in_mapset) != unicode(Mapset()):
        grass.fatal("Input vector map is not in current mapset and cannot be modified. \
                    Please consider copying it to current mapset.".format(output))

    buffers = []
    for buf in options['buffers'].split(','):
        try:
            b = float(buf)
            if b.is_integer():
                buffers.append(int(b))
            else:
                buffers.append(b)
        except:
            grass.fatal('')
        if b < 0:
            grass.fatal("Negative buffer distance not supported!")

    ### Define column types depenting on statistic, map type and
    ### DB backend (SQLite supports only double and not real)
    # int: statistic produces allways integer precision
    # double: statistic produces allways floating point precision
    # map_type: precision f statistic depends on map type
    int_dict = {'number': (0, 'int', 'n'),
                'number_null': (1, 'int', 'null_cells'),
                'minimum': (3, 'map_type', 'min'),
                'maximum': (4, 'map_type', 'max'),
                'range': (5, 'map_type', 'range'),
                'average': (6, 'double', 'mean'),
                'average_abs': (7, 'double', 'mean_of_abs'),
                'stddev': (8, 'double', 'stddev'),
                'variance': (9, 'double', 'variance'),
                'coeff_var': (10, 'double', 'coeff_var'),
                'sum': (11, 'map_type', 'sum'),
                'first_quartile': (12, 'map_type', 'first_quartile'),
                'median': (13, 'map_type', 'median'),
                'third_quartile': (14, 'map_type', 'third_quartile'),
                'percentile': (15, 'map_type', 'percentile')}

    if len(raster_maps) != len(column_prefix):
        grass.fatal('Number of maps and number of column prefixes has to be equal!')

    # Generate list of required column names and types
    col_names = []
    col_types = []
    for p in column_prefix:
        rmaptype, rcats = raster_type(raster_maps[column_prefix.index(p)])
        for b in buffers:
            b_str = str(b).replace('.', '_')
            if tabulate:
                if rmaptype == 'double precision':
                    grass.fatal('{} has floating point precision. Can only tabulate integer maps'.format(raster_maps[column_prefix.index(p)]))
                col_names.append('{}_{}_b{}'.format(p, 'ncats', b_str))
                col_types.append('int')
                col_names.append('{}_{}_b{}'.format(p, 'mode', b_str))
                col_types.append('int')
                col_names.append('{}_{}_b{}'.format(p, 'null', b_str))
                col_types.append('double precision')
                col_names.append('{}_{}_b{}'.format(p, 'area_tot', b_str))
                col_types.append('double precision')
                for rcat in rcats:
                    col_names.append('{}_{}_b{}'.format(p, rcat.split('\t')[0], b_str))
                    col_types.append('double precision')
            else:
                for m in methods:
                    col_names.append('{}_{}_b{}'.format(p, int_dict[m][2], b_str))
                    col_types.append(rmaptype if int_dict[m][1] == 'map_type' else int_dict[m][1])
                if percentile:
                    for perc in percentile:
                        col_names.append('{}_percentile_{}_b{}'.format(p,
                                                                       int(perc) if (perc).is_integer() else perc,
                                                                       b_str))
                        col_types.append(rmaptype if int_dict[m][1] == 'map_type' else int_dict[m][1])

    # Open input vector map
    in_vect = VectorTopo(in_vector, layer=layer)
    in_vect.open(mode='r')

    # Get name for temporary map
    tmp_map = random_name(21)
    TMP_MAPS.append(tmp_map)

    # Setup stats collectors
    if tabulate:
        # Collector for raster category statistics
        stats = Module('r.stats', run_=False, stdout_=PIPE)
        stats.inputs.sort = 'desc'
        stats.inputs.null_value = 'null'
        stats.flags.quiet = True
        if percent:
            stats.flags.p = True
            stats.flags.n = True
        else:
            stats.flags.a = True
    else:
        # Collector for univariat statistics
        univar = Module('r.univar', run_=False, stdout_=PIPE)
        univar.inputs.separator = sep
        univar.flags.g = True
        univar.flags.quiet = True

        # Add extended statistics if requested
        if set(methods).intersection(set(['first_quartile',
                                          'median', 'third_quartile'])):
            univar.flags.e = True

        if percentile is not None:
            univar.flags.e = True
            univar.inputs.percentile = percentile

    # Check if attribute table exists
    if not output:
        if not in_vect.table:
            grass.fatal('No attribute table found for vector map {}'.format(in_vect))

        # Modify table as needed
        tab = in_vect.table
        tab_name = tab.name
        tab_cols = tab.columns

        # Add required columns
        existing_cols = list(set(tab_cols.names()).intersection(col_names))
        if len(existing_cols) > 0:
            if not update:
                grass.fatal('Column(s) {} already exist! Please use the u-flag \
                            if you want to update values in those columns'.format(','.join(existing_cols)))
            else:
                grass.warning('Column(s) {} already exist!'.format(','.join(existing_cols)))
        for e in existing_cols:
            idx = col_names.index(e)
            del col_names[idx]
            del col_types[idx]
        tab_cols.add(col_names, col_types)

        conn = tab.conn
        cur = conn.cursor()

        sql_str_start = 'UPDATE {} SET '.format(tab_name)


    # Get computational region
    grass.use_temp_region()
    #r = Region()
    #r.read()
    # Adjust region extent to buffer around geometry
    #reg = deepcopy(r)

    # Create iterator for geometries of all selected types
    geoms = chain()
    geoms_n = 0
    n_geom = 1
    for geom_type in types:
        geoms_n += in_vect.number_of(geom_type)
        if in_vect.number_of(geom_type) > 0:
            geoms = chain(in_vect.viter(geom_type))

    # Loop over geometries
    for geom in geoms:
        # Get cat
        cat = geom.cat
        # Give progress information
        grass.percent(n_geom, geoms_n, 1)
        n_geom = n_geom + 1

        # Add where clause to UPDATE statement
        sql_str_end = ' WHERE cat = {};'.format(cat)

        # Loop over ser provided buffer distances
        for buf in buffers:
            b_str = str(buf).replace('.', '_')
            # Buffer geometry
            if buf <= 0:
                buffer_geom = geom
            else:
                buffer_geom = geom.buffer(buf)
            # Create temporary vector map with buffered geometry
            tmp_vect = VectorTopo(tmp_map, quiet=True)
            tmp_vect.open(mode='w')
            #print(int(cat))
            tmp_vect.write(Boundary(points=buffer_geom[0].to_list()))
            # , c_cats=int(cat), set_cats=True
            tmp_vect.write(Centroid(x=buffer_geom[1].x,
                                    y=buffer_geom[1].y), cat=int(cat))

            #################################################
            # How to silence VectorTopo???
            #################################################

            # Save current stdout
            #original = sys.stdout

            #f = open(os.devnull, 'w')
            #with open('output.txt', 'w') as f:
            #sys.stdout = io.BytesIO()
            #sys.stdout.fileno() = os.devnull
            #sys.stderr = f
            #os.environ.update(dict(GRASS_VERBOSE='0'))
            tmp_vect.close(build=False)
            grass.run_command('v.build', map=tmp_map, quiet=True)
            #os.environ.update(dict(GRASS_VERBOSE='1'))

            #reg = Region()
            #reg.read()
            #r.from_vect(tmp_map)
            #r = align_current(r, buffer_geom[0].bbox())
            #r.set_current()

            # Check if the following is needed
            # needed specially with r.stats -p
            grass.run_command('g.region', vector=tmp_map, flags='a')

            # Create a MASK from buffered geometry
            grass.run_command('v.to.rast', input=tmp_map,
                              output='MASK', use='val',
                              value=int(cat), quiet=True)


            #reg.write()

            updates = []
            # Compute statistics for every raster map
            for rm in range(len(raster_maps)):
                rmap = raster_maps[rm]
                prefix = column_prefix[rm]

                if tabulate:
                    # Get statistics on occurrence of raster categories within buffer
                    stats.inputs.input = rmap
                    stats.run()
                    t_stats = stats.outputs['stdout'].value.rstrip(os.linesep).replace(' ', '_b{} = '.format(b_str)).split(os.linesep)
                    if t_stats[0].split('_b{} = '.format(b_str))[0].split('_')[-1] != 'null':
                        mode = t_stats[0].split('_b{} = '.format(b_str))[0].split('_')[-1]
                    elif len(t_stats) == 1:
                        mode = 'NULL'
                    else:
                        mode = t_stats[1].split('_b{} = '.format(b_str))[0].split('_')[-1]

                    if not output:
                        updates.append('\t{}_{}_b{} = {}'.format(prefix, 'ncats', b_str, len(t_stats)))
                        updates.append('\t{}_{}_b{} = {}'.format(prefix, 'mode', b_str, mode))

                        area_tot = 0
                        for l in t_stats:
                            updates.append('\t{}_{}'.format(prefix, l.rstrip('%')))
                            if l.split('_b{} ='.format(b_str))[0].split('_')[-1] != 'null':
                                area_tot = area_tot + float(l.rstrip('%').split('= ')[1])
                        if not percent:
                            updates.append('\t{}_{}_b{} = {}'.format(prefix, 'area_tot', b_str, area_tot))

                    else:
                        out_str = '{1}{0}{2}{0}{3}{0}{4}{0}{5}{6}'.format(sep, cat, prefix, buf, 'ncats', len(t_stats), os.linesep)
                        out_str += '{1}{0}{2}{0}{3}{0}{4}{0}{5}{6}'.format(sep, cat, prefix, buf, 'mode', mode, os.linesep)
                        area_tot = 0
                        for l in t_stats:
                            rcat = l.split('_b{} ='.format(b_str))[0].split('_')[-1]
                            area = l.split('= ')[1]
                            out_str += '{1}{0}{2}{0}{3}{0}{4}{0}{5}{6}'.format(sep, cat, prefix, buf, 'area {}'.format(rcat), area, os.linesep)
                            if rcat != 'null':
                                area_tot = area_tot + float(l.split('= ')[1])
                        out_str += '{1}{0}{2}{0}{3}{0}{4}{0}{5}{6}'.format(sep, cat, prefix, buf, 'area_tot', area_tot, os.linesep)

                        if output == '-':
                            print(out_str.rstrip(os.linesep))
                        else:
                            out.write(out_str)

                else:
                    # Get univariate statistics within buffer
                    univar.inputs.map = rmap
                    univar.run()
                    u_stats = univar.outputs['stdout'].value.rstrip(os.linesep).replace('=', '_b{} = '.format(b_str)).split(os.linesep)

                    # Test i u_stats is empty and give warning
                    if (percentile and len(u_stats) <= 14) or (univar.flags.e and len(u_stats) <= 13) or len(u_stats) <= 12:
                        grass.warning('No data within buffer {} around geometry {}'.format(buf, cat))
                        break

                    # Extract statistics for selected methods
                    for m in methods:
                        if not output:
                            # Add to list of UPDATE statements
                            updates.append('\t{}_{}'.format(prefix,
                                                                     u_stats[int_dict[m][0]]))
                        else:
                            out_str = '{1}{0}{2}{0}{3}{0}{4}{0}{5}'.format(sep, cat, prefix, buf, m, u_stats[int_dict[m][0]].split('= ')[1])
                            if output == '-':
                                print(out_str)
                            else:
                                out.write(out_str)

                    if percentile:
                        perc_count = 0
                        for perc in percentile:
                            if not output:
                                updates.append('{}_percentile_{}_b{} = {}'.format(p,
                                                                                  int(perc) if (perc).is_integer() else perc,
                                                                                  b_str, u_stats[15+perc_count].split('= ')[1]))
                            else:
                                out_str = '{1}{0}{2}{0}{3}{0}{4}{0}{5}'.format(sep, cat, prefix, buf, 'percentile_{}'.format(int(perc) if (perc).is_integer() else perc), u_stats[15+perc_count].split('= ')[1])
                                if output == '-':
                                    print(out_str)
                                else:
                                    out.write(out_str)
                            perc_count = perc_count + 1

            if not output and len(updates) > 0:
                cur.execute('{}{}{}'.format(sql_str_start,
                                            ',\n'.join(updates),
                                            sql_str_end))

            # Remove temporary maps
            #, stderr=os.devnull, stdout_=os.devnull)
            grass.run_command('g.remove', flags='f', type='raster',
                              name='MASK', quiet=True)
            grass.run_command('g.remove', flags='f', type='vector',
                              name=tmp_map, quiet=True)

        if not output:
            conn.commit()

    grass.use_temp_region()
    # Close cursor and DB connection
    if not output and not output == "-":
        cur.close()
        conn.close()
        # Update history
        grass.vector.vector_history(in_vector)
    elif output != "-":
        # write results to file
        out.close()

    if remove:
        dropcols = []
        selectnum = 'select count({}) from {}'
        for i in col_names:
            thisrow = grass.read_command('db.select', flags='c',
                                         sql=selectnum.format(i, in_vector))
            if int(thisrow) == 0:
                dropcols.append(i)
        grass.debug("Columns to delete: {}".format(', '.join(dropcols)),
                    debug=2)
        grass.run_command('v.db.dropcolumn', map=in_vector, columns=dropcols)

    # Clean up
    cleanup()

# Run the module
if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
