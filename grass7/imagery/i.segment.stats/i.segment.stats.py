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
#% options: area,perimeter,compact_circle,compact_square,fd
#% answer: area,perimeter,compact_circle,fd
#% guisection: shape_statistics
#%end
#%option G_OPT_F_OUTPUT
#% key: csvfile
#% label: CSV output file containing statistics
#% required: no
#% guisection: output
#%end
#%option G_OPT_F_SEP
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
#% flag
#% key: r
#% description: Adjust region to input map
#%END


import os
import atexit
import collections
import math
import grass.script as gscript
    

def cleanup():

    if temporary_vect:
        if gscript.find_file(temporary_vect, element='vector')['name']:
            gscript.run_command('g.remove', flags='f', type_='vector',
                    name=temporary_vect, quiet=True)
    if insert_sql:
        os.remove(insert_sql)

    os.remove(stats_temp_file)


def main():


    segment_map = options['map']
    csvfile = options['csvfile'] if options['csvfile'] else []
    vectormap = options['vectormap'] if options['vectormap'] else []
    rasters = options['rasters'].split(',') if options['rasters'] else []
    area_measures = options['area_measures'].split(',') if options['area_measures'] else []
    r_object_geometry = True
    if area_measures:
	if not gscript.find_program('r.object.geometry', '--help'):
		message = _("You need to install the addon r.object.geometry to be able")
		message += _(" to calculate area measures. Ignoring these measures for now.")
		message += _(" You can install the addon with 'g.extension r.object.geometry'")
		gscript.warning(message)
		r_object_geometry = False

    raster_statistics = options['raster_statistics'].split(',') if options['raster_statistics'] else []
    separator = gscript.separator(options['separator'])

    output_header = ['cat']
    output_dict = collections.defaultdict(list)

    global insert_sql
    insert_sql = None
    global temporary_vect
    temporary_vect = None

    raster_stat_dict = {'zone': 0, 'min': 4, 'third_quart': 16, 'max': 5, 'sum':
            12, 'null_cells': 3, 'median': 15, 'label': 1, 'first_quart': 14,
            'range': 6, 'mean_of_abs': 8, 'stddev': 9, 'non_null_cells': 2,
            'coeff_var': 11, 'variance': 10, 'sum_abs': 13, 'perc_90': 17,
            'mean': 7}

    geometry_stat_dict = {'cat': 0, 'area': 1, 'perimeter': 2,
			'compact_square': 3, 'compact_circle': 4, 'fd' : 5}
    
    if flags['r']:
        gscript.use_temp_region()
        gscript.run_command('g.region', raster=segment_map)

    global stats_temp_file
    stats_temp_file = gscript.tempfile()
    if area_measures and r_object_geometry:
	gscript.message(_("Calculating geometry statistics"))
	output_header += area_measures
	stat_indices = [geometry_stat_dict[x] for x in area_measures]
        gscript.run_command('r.object.geometry',
     		      	    input_=segment_map,
		      	    output=stats_temp_file,
		      	    overwrite=True,
		      	    quiet=True)
    
	firstline = True
    	with open(stats_temp_file, 'r') as fin:
	    for line in fin:
		if firstline:
		    firstline = False
		    continue
		values = line.rstrip().split('|')
		output_dict[values[0]] = [values[x] for x in stat_indices]

    for raster in rasters:
	gscript.message(_("Calculating statistics for raster %s" % raster))
        if not gscript.find_file(raster, element='raster')['name']:
            gscript.message(_("Cannot find raster %s" % raster))
            continue
        rastername=raster.split('@')[0]
        output_header += [rastername + "_" + x for x in raster_statistics]
        stat_indices = [raster_stat_dict[x] for x in raster_statistics]
        gscript.run_command('r.univar',
                            map_=raster,
                            zones=segment_map,
			    output=stats_temp_file,
                            flags='et',
			    overwrite=True,
			    quiet=True)

	firstline = True
    	with open(stats_temp_file, 'r') as fin:
	    for line in fin:
		if firstline:
		    firstline = False
		    continue
		values = line.rstrip().split('|')
		values = line.rstrip().split('|')
	    	if area_measures:
            	    output_dict[values[0]] = output_dict[values[0]]+ [values[x] for x in stat_indices]
	    	else:
            	    output_dict[values[0]] = [values[x] for x in stat_indices]

    message = _("Some values could not be calculated for the objects below. ")
    message += _("These objects are thus not included in the results. ")
    message += _("HINT: Check some of the raster maps for null values ")
    message += _("and possibly fill these values with r.fillnulls.")
    error_objects = []

    if csvfile:
        with open(csvfile, 'wb') as f:
            f.write(separator.join(output_header)+"\n")
            for key in output_dict:
		if len(output_dict[key]) + 1 == len(output_header):
                    f.write(key+separator+separator.join(output_dict[key])+"\n")
		else:
		    error_objects.append(key)
        f.close()

    if vectormap:
	gscript.message(_("Creating vector map"))
        temporary_vect = 'segmstat_tmp_vect_%d' % os.getpid()
        gscript.run_command('r.to.vect',
                            input_=segment_map,
                            output=temporary_vect,
                            type_='area',
                            flags='vt',
			    overwrite=True,
			    quiet=True)

        insert_sql = gscript.tempfile()
        fsql = open(insert_sql, 'w')
        fsql.write('BEGIN TRANSACTION;\n')
        create_statement = 'CREATE TABLE ' + vectormap + ' (cat int, '
        for header in output_header[1:-1]:
            create_statement += header +  ' double precision, '
        create_statement += output_header[-1] + ' double precision);\n'
        fsql.write(create_statement)
        for key in output_dict:
		if len(output_dict[key]) + 1  == len(output_header):
                    sql = "INSERT INTO " + vectormap + " VALUES (" + key+","+",".join(output_dict[key])+");\n"
                    sql = sql.replace('inf', 'NULL')
                    fsql.write(sql)
		else:
		    if not csvfile:
		    	error_objects.append(key)
		
        fsql.write('END TRANSACTION;')
        fsql.close()

        gscript.run_command('g.copy', vector=temporary_vect+','+vectormap, quiet=True)
        gscript.run_command('db.execute', input=insert_sql, quiet=True)
        gscript.run_command('v.db.connect', map_=vectormap, table=vectormap, quiet=True)

    if error_objects:
	object_string = ', '.join(error_objects)
	message += _("\n\nObjects with errors: %s" % object_string)
	gscript.warning(message)
		

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
