#!/usr/bin/env python
############################################################################
#
# MODULE:       v.isochrones
# AUTHOR:       Moritz Lennert
# PURPOSE:      Takes a map of roads and starting points and creates
#               isochrones around the starting points
#
# COPYRIGHT:    (c) 2014 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Creates isochrones from a road map and starting points
#% keyword: vector
#% keyword: isochrones
#%end
#%option G_OPT_V_MAP
#% label: Roads with speed attribute
#% required: yes
#%end
#%option G_OPT_V_FIELD
#% required: yes
#%end
#%option G_OPT_DB_COLUMN
#% key: speed_column
#% description: Name of speed attribute column (in km/h)
#% required: yes
#%end
#%option G_OPT_V_INPUT
#% key: start_points
#% label: Vector map with starting points for isochrones
#% required: yes
#%end
#%option G_OPT_V_OUTPUT
#% key: isochrones
#% label: Output vector map with isochrone polygons
#% required: yes
#%end
#%option G_OPT_R_OUTPUT
#% key: timemap
#% label: Optional output raster map with continuous time from starting points
#% required: no
#%end
#%option
#% key: time_steps
#% type: double
#% description: Time steps of isochrones (in units defined by unit parameter)
#% multiple: yes
#% required: yes
#%end
#%option
#% key: offroad_speed
#% type: integer
#% description: Speed for off-road areas (in km/h)
#% required: no
#% answer: 5
#%end
#%option
#% key: unit
#% description: Time unit to use (seconds, minutes, hours)
#% type: string
#% required: no
#% options: s,m,h
#% answer: m
#%end

import os
import atexit
import math
import grass.script as grass

tmp_cost_map = None
tmp_map = None
tmp_time_map = None
tmp_region_map = None


def cleanup():

    # remove temporary cost column from road map
    grass.run_command('v.db.dropcolumn',
                      map=roads,
                      column=cost_column,
                      quiet=True)

    if grass.find_file(tmp_cost_map, element='raster')['name']:
        grass.run_command('g.remove', flags='f', type='raster', name=tmp_cost_map, quiet=True)
    if grass.find_file(tmp_map, element='raster')['name']:
        grass.run_command('g.remove', flags='f', type='raster', name=tmp_map, quiet=True)
    if grass.find_file(tmp_time_map, element='raster')['name']:
        grass.run_command('g.remove', flags='f', type='raster', name=tmp_time_map, quiet=True)
    if grass.find_file(tmp_region_map, element='raster')['name']:
        grass.run_command('g.remove', flags='f', type='raster', name=tmp_region_map, quiet=True)


def main():

    # Input
    global roads
    roads = options['map']
    speed_column = options['speed_column']
    start_points = options['start_points']
    time_steps = options['time_steps'].split(',')
    offroad_speed = int(options['offroad_speed'])
    unit = options['unit']
    # Output
    isochrones = options['isochrones']
    if options['timemap']:
        timemap = options['timemap']
    else:
        timemap = None

    global tmp_cost_map
    global tmp_map
    global tmp_time_map
    global tmp_region_map
    global cost_column

    tmp_cost_map = 'cost_map_tmp_%d' % os.getpid()
    tmp_map = 'map_tmp_%d' % os.getpid()
    tmp_time_map = 'time_map_tmp_%d' % os.getpid()
    tmp_region_map = 'region_map_tmp_%d' % os.getpid()

    # get current resolution
    region = grass.region()
    resolution = math.sqrt(float(region['nsres']) * float(region['ewres']))

    # add cost column to road vector
    cost_column = 'temp%d' % os.getpid()
    def_cost_column = cost_column + ' DOUBLE PRECISION'
    grass.run_command('v.db.addcolumn',
                      map=roads,
                      column=def_cost_column,
                      quiet=True)

    # calculate cost (in seconds) depending on speed
    # (resolution/(speed (in km/h) * 1000 / 3600))
    query_value = "%s / (%s * 1000 / 3600)" % (resolution, speed_column)
    grass.run_command('v.db.update',
                      map=roads,
                      column=cost_column,
                      qcolumn=query_value)

    # transform to raster
    grass.run_command('v.to.rast',
                      input=roads,
                      out=tmp_cost_map,
                      use='attr',
                      attrcolumn=cost_column,
                      type='line')

    # replace null values with cost for off-road areas
    # (resolution/(off-road speed * 1000 / 3600))
    null_value = resolution / (float(offroad_speed) * 1000 / 3600)
    grass.run_command('r.null', map=tmp_cost_map, null=null_value)

    # calculate time distance from starting points
    grass.run_command('r.cost',
                      input=tmp_cost_map,
                      start_points=start_points,
                      output=tmp_map)

    #  if necessary, transform time to desired time units
    if unit == 'm':
        expression = tmp_time_map + ' = ' + tmp_map + ' / 60'
        grass.mapcalc(expression)
    elif unit == 'h':
        expression = tmp_time_map + ' = ' + tmp_map + ' / 3600'
        grass.mapcalc(expression)
    else:
        grass.run_command('g.rename', raster = (tmp_map, tmp_time_map))

    if timemap:
        grass.run_command('g.copy', raster=(tmp_time_map, timemap))
        grass.run_command('r.colors', map=timemap, color='grey', flags='ne')

    # recode time distance to time steps
    recode_rules = '0:%s:%s\n' % (time_steps[0], time_steps[0])
    for count in range(1, len(time_steps)):
        recode_rules += time_steps[count-1] + ':'
        recode_rules += time_steps[count] + ':'
        recode_rules += time_steps[count] + '\n'

    grass.write_command('r.recode',
                        input=tmp_time_map,
                        output=tmp_region_map,
                        rules='-',
                        stdin=recode_rules)

    # transform to vector areas
    grass.run_command('r.to.vect',
                      input=tmp_region_map,
                      output=isochrones,
                      type='area',
                      column='time')

    # give the polygons a default color table
    grass.run_command('v.colors',
                      map=isochrones,
                      use='attr',
                      column='time',
                      color='grey')

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
