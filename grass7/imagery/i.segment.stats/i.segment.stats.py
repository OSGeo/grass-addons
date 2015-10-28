#!/usr/bin/env python
############################################################################
#
# MODULE:       i.segment.stats
# AUTHOR:       Moritz Lennert
# PURPOSE:      Calculates statistics describing raster areas
#               (notably for segments resulting from i.segment)
#
# COPYRIGHT:    (c) 2015 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Calculates statistics describing raster areas
#% keyword: imagery
#% keyword: segmentation
#% keyword: statistics
#%end
#%option G_OPT_R_MAP
#% label: Raster map with areas (all pixels of an area have same id)
#% description: Raster map with areas, such as the output of i.segment
#% required: yes
#%end
#%option G_OPT_R_INPUTS
#% key: rasters
#% description: Name of input raster maps for statistics
#% multiple: yes
#% required: no
#% guisection: raster_statistics
#%end
#%option
#% key: raster_statistics
#% type: string
#% label: Statistics to calulate for each input raster map
#% required: no
#% multiple: yes
#% options: min,max,range,mean,mean_of_abs,stddev,variance,coeff_var,sum,sum_abs,first_quart,median,third_quart,perc_90
#% answer: mean,stddev,sum
#% guisection: raster_statistics
#%end
#%rules
#% requires: raster_statistics,rasters
#%end
#%option
#% key: area_measures
#% type: string
#% label: Area measurements to include in the output
#% required: no
#% multiple: yes
#% options: area,perimeter,compact,fd
#% answer: area,perimeter,compact,fd
#% guisection: shape_statistics
#%end
#%option G_OPT_F_OUTPUT
#% key: csvfile
#% label: CSV output file containing statistics
#% required: no
#% guisection: output
#%end
#% option G_OPT_V_OUTPUT
#% key: vectormap
#% label: Optional vector output map with statistics as attributes
#% required: no
#% guisection: output
#%end
#%rules
#% required: csvfile,vectormap
#%end

import os
import atexit
import collections
import math
import grass.script as grass
    

def cleanup():

    if grass.find_file(temporary_vect, element='vector')['name']:
            grass.run_command('g.remove', flags='f', type_='vector',
                    name=temporary_vect, quiet=True)
    if grass.find_file(temporary_clumped_rast, element='vector')['name']:
            grass.run_command('g.remove', flags='f', type_='vector',
                    name=temporary_clumped_rast, quiet=True)
    if insert_sql:
        os.remove(insert_sql)


def main():

    grass.use_temp_region()

    segment_map = options['map']
    csvfile = options['csvfile'] if options['csvfile'] else []
    vectormap = options['vectormap'] if options['vectormap'] else []
    rasters = options['rasters'].split(',') if options['rasters'] else []
    area_measures = options['area_measures'].split(',') if options['area_measures'] else []
    raster_statistics = options['raster_statistics'].split(',') if options['raster_statistics'] else []

    output_header = ['cat']
    output_dict = collections.defaultdict(list)

    global insert_sql
    insert_sql = None

    global temporary_vect
    global temporary_clumped_rast
    temporary_clumped_rast = 'segmstat_tmp_clumpedrast_%d' % os.getpid()
    temporary_vect = 'segmstat_tmp_vect_%d' % os.getpid()

    raster_stat_dict = {'zone': 0, 'min': 4, 'third_quart': 16, 'max': 5, 'sum':
            12, 'null_cells': 3, 'median': 15, 'label': 1, 'first_quart': 14,
            'range': 6, 'mean_of_abs': 8, 'stddev': 9, 'non_null_cells': 2,
            'coeff_var': 11, 'variance': 10, 'sum_abs': 13, 'perc_90': 17,
            'mean': 7}
    
    grass.run_command('g.region', raster=segment_map)
    grass.run_command('r.clump',
                      input_=segment_map,
                      output=temporary_clumped_rast,
                      quiet=True)
    grass.run_command('r.to.vect',
                      input_=temporary_clumped_rast,
                      output=temporary_vect,
                      type_='area',
                      flags='vt')

    for area_measure in area_measures:
        output_header.append(area_measure)
        res=grass.read_command('v.to.db', map_=temporary_vect,
                option=area_measure, column=area_measure,
                flags='p').splitlines()[1:]
        for element in res:
            values = element.split('|')
            output_dict[values[0]].append(values[1])

    for raster in rasters:
        if not grass.find_file(raster, element='raster')['name']:
            grass.message(_("Cannot find raster %s" % raster))
            continue
        rastername=raster.split('@')[0]
        output_header += [rastername + "_" + x for x in raster_statistics]
        stat_indices = [raster_stat_dict[x] for x in raster_statistics]
        res=grass.read_command('r.univar',
                               map_=raster,
                               zones=temporary_clumped_rast,
                               flags='et').splitlines()[1:]
        for element in res:
            values = element.split('|')
            output_dict[values[0]] = output_dict[values[0]]+ [values[x] for x in stat_indices]

    if csvfile:
        with open(csvfile, 'wb') as f:
            f.write(",".join(output_header)+"\n")
            for key in output_dict:
                f.write(key+","+",".join(output_dict[key])+"\n")
        f.close()

    if vectormap:
        insert_sql = grass.tempfile()
        fsql = open(insert_sql, 'w')
        fsql.write('BEGIN TRANSACTION;\n')
        create_statement = 'CREATE TABLE ' + vectormap + ' (cat int, '
        for header in output_header[1:-1]:
            create_statement += header +  ' double precision, '
        create_statement += output_header[-1] + ' double precision);\n'
        fsql.write(create_statement)
        for key in output_dict:
                sql = "INSERT INTO " + vectormap + " VALUES (" + key+","+",".join(output_dict[key])+");\n"
                sql = sql.replace('inf', 'NULL')
                fsql.write(sql)
        fsql.write('END TRANSACTION;')
        fsql.close()
        grass.run_command('g.copy', vector=temporary_vect+','+vectormap)
        grass.run_command('db.execute', input=insert_sql)
        grass.run_command('v.db.connect', map_=vectormap, table=vectormap)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
