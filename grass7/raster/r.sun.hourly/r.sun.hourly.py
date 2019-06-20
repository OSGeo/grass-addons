#!/usr/bin/env python

############################################################################
#
# MODULE:    r.sun.hourly for GRASS 6 and 7
# AUTHOR(S): Vaclav Petras, Anna Petrasova
# PURPOSE:
# COPYRIGHT: (C) 2013 - 2019 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

#%module
#% description: Runs r.sun in loop for given time range (mode 1)
#% keyword: raster
#% keyword: solar
#% keyword: sun energy
#% overwrite: yes
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: elevation
#% description: Name of the input elevation raster map [meters]
#% required : yes
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: aspect
#% description: Name of the input aspect map (terrain aspect or azimuth of the solar panel) [decimal degrees]
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: slope
#% description: Name of the input slope raster map (terrain slope or solar panel inclination) [decimal degrees]
#%end
#%option G_OPT_R_INPUT
#% key: linke
#% description: Name of the Linke atmospheric turbidity coefficient input raster map [-]
#% required : no
#%end
#%option
#% key: linke_value
#% type: double
#% description: A single value of the Linke atmospheric turbidity coefficient [-]
#% options: 0.0-7.0
#% answer: 3.0
#% required: no
#%end
#% rules
#%  exclusive: linke, linke_value
#% end
#%option G_OPT_R_INPUT
#% key: albedo
#% description: Name of the ground albedo coefficient input raster map [-]
#% required: no
#%end
#%option
#% key: albedo_value
#% type: double
#% description: A single value of the ground albedo coefficient [-]
#% options: 0.0-1.0
#% answer: 0.2
#% required: no
#%end
#% rules
#%  exclusive: albedo, albedo_value
#% end
#%option
#% key: start_time
#% type: double
#% label: Start time of interval
#% description: Use up to 2 decimal places
#% options: 0-24
#% required : yes
#%end
#%option
#% key: end_time
#% type: double
#% label: End time of interval
#% description: Use up to 2 decimal places
#% options: 0-24
#% required : yes
#%end
#%option
#% key: time_step
#% type: double
#% label: Time step for running r.sun [decimal hours]
#% description: Use up to 2 decimal places
#% options: 0-24
#% answer: 1
#%end
#%option
#% key: day
#% type: integer
#% description: No. of day of the year
#% options: 1-365
#% required : yes
#%end
#%option
#% key: year
#% type: integer
#% label: Year used for map registration into temporal dataset or r.timestamp
#% description: This value is not used in r.sun calcluations
#% options: 1900-9999
#% required: yes
#% answer: 1900
#%end
#%option
#% key: civil_time
#% type: double
#% description: Civil time zone value, if none, the time will be local solar time
#%end
#%option
#% key: beam_rad_basename
#% type: string
#% label: Base name for output beam irradiance raster maps [Wh.m-2]
#% description: Underscore and day number are added to the base name for each map
#%end
#%option
#% key: diff_rad_basename
#% type: string
#% label: Base name for output diffuse irradiance raster maps [Wh.m-2]
#% description: Underscore and day number are added to the base name for each map
#%end
#%option
#% key: refl_rad_basename
#% type: string
#% label: Base name for output ground reflected irradiance raster maps [Wh.m-2]
#% description: Underscore and day number are added to the base name for each map
#%end
#%option
#% key: glob_rad_basename
#% type: string
#% label: Base name for output global (total) irradiance raster maps [Wh.m-2]
#% description: Underscore and day number are added to the base name for each map
#%end
#%option
#% key: incidout_basename
#% type: string
#% label: Base name for output incidence angle raster maps
#% description: Underscore and day number are added to the base name for each map
#%end
#%option
#% key: nprocs
#% type: integer
#% description: Number of r.sun processes to run in parallel
#% options: 1-
#% answer: 1
#%end
#%flag
#% key: t
#% description: Dataset name is the same as the base name for the output series of maps
#% label: Register created series of output maps into temporal dataset
#%end
#%flag
#% key: b
#% description: Create binary rasters instead of irradiation rasters
#%end
#%flag
#% key: p
#% description: Do not incorporate the shadowing effect of terrain
#%end
#%flag
#% key: m
#% description: Use the low-memory version of the program
#%end


import os
import datetime
import atexit
from multiprocessing import Process

import grass.script as grass
import grass.script.core as core

TMP = []


def cleanup():
    if len(TMP):
        core.info(_("Cleaning %d temporary maps...") % len(TMP))
    for rast in TMP:
        grass.run_command('g.remove', type='raster', name=rast, flags='f',
                          quiet=True)


def is_grass_7():
    if core.version()['version'].split('.')[0] == '7':
        return True
    return False


def create_tmp_map_name(name):
    return '{mod}{pid}_{map_}_tmp'.format(mod='r_sun_crop',
                                          pid=os.getpid(),
                                          map_=name)


# add latitude map
def run_r_sun(elevation, aspect, slope, day, time,
              linke, linke_value, albedo, albedo_value,
              beam_rad, diff_rad, refl_rad, glob_rad,
              incidout, suffix, binary, binaryTmpName, flags):
    params = {}
    if linke:
        params.update({'linke': linke})
    if linke_value:
        params.update({'linke_value': linke_value})
    if albedo:
        params.update({'albedo': albedo})
    if albedo_value:
        params.update({'albedo_value': albedo_value})
    if beam_rad:
        params.update({'beam_rad': beam_rad + suffix})
    if diff_rad:
        params.update({'diff_rad': diff_rad + suffix})
    if refl_rad:
        params.update({'refl_rad': refl_rad + suffix})
    if glob_rad:
        params.update({'glob_rad': glob_rad + suffix})
    if incidout:
        params.update({'incidout': incidout + suffix})
    if flags:
        params.update({'flags': flags})

    if is_grass_7():
        grass.run_command('r.sun', elevation=elevation, aspect=aspect,
                          slope=slope, day=day, time=time,
                          overwrite=core.overwrite(), quiet=True,
                          **params)
    else:
        grass.run_command('r.sun', elevin=elevation, aspin=aspect,
                          slopein=slope, day=day, time=time,
                          overwrite=core.overwrite(), quiet=True,
                          **params)
    if binary:
        for output in (beam_rad, diff_rad, refl_rad, glob_rad):
            if not output:
                continue
            exp='{out} = if({inp} > 0, 1, 0)'.format(out=output + suffix + binaryTmpName,
                                                     inp=output + suffix)
            grass.mapcalc(exp=exp, overwrite=core.overwrite())
            grass.run_command('g.rename', raster = [output + suffix + binaryTmpName,
                                                output + suffix],
                              overwrite=True)


def set_color_table(rasters, binary=False):
    table = 'gyr'
    if binary:
        table = 'grey'
    if is_grass_7():
        grass.run_command('r.colors', map=rasters, col=table, quiet=True)
    else:
        for rast in rasters:
            grass.run_command('r.colors', map=rast, col=table, quiet=True)


def set_time_stamp(raster, time):
    grass.run_command('r.timestamp', map=raster, date=time, quiet=True)


def format_time(time):
    return '%05.2f' % time


def check_time_map_names(basename, mapset, start_time, end_time, time_step,
                         binary, binaryTmpName):
    if not basename:
        return
    for time in frange(start_time, end_time, time_step):
        maps = []
        maps.append('{name}{delim}{time}'.format(name=basename,
                                                 delim='_',
                                                 time=format_time(time)))
        if binary:
            maps.append('{name}{delim}{time}{binary}'.format(name=basename,
                                                             delim='_',
                                                             time=format_time(time),
                                                             binary=binaryTmpName))
        for map_ in maps:
            if grass.find_file(map_, element='cell', mapset=mapset)['file']:
                grass.fatal(_("Raster map <%s> already exists. Change the base"
                              " name or allow overwrite.") % map_)


def frange(x, y, step):
    while x <= y:
        yield x
        x += step


def format_grass_time(dt):
    """!Format datetime object to grass timestamps.
    Copied from temporal framework to use thsi script also in GRASS 6.
    """
    # GRASS datetime month names
    month_names = ["", "jan", "feb", "mar", "apr", "may", "jun",
                   "jul", "aug", "sep", "oct", "nov", "dec"]
    return "%.2i %s %.4i %.2i:%.2i:%.2i" % (dt.day, month_names[dt.month],
                                            dt.year, dt.hour, dt.minute,
                                            dt.second)


def main():
    options, flags = grass.parser()

    elevation_input = options['elevation']
    aspect_input = options['aspect']
    slope_input = options['slope']
    linke = options['linke']
    linke_value = options['linke_value']
    albedo = options['albedo']
    albedo_value = options['albedo_value']

    beam_rad_basename = options['beam_rad_basename']
    diff_rad_basename = options['diff_rad_basename']
    refl_rad_basename = options['refl_rad_basename']
    glob_rad_basename = options['glob_rad_basename']
    incidout_basename = options['incidout_basename']

    if not any([beam_rad_basename, diff_rad_basename,
                refl_rad_basename, glob_rad_basename,
                incidout_basename]):
        grass.fatal(_("No output specified."))

    start_time = float(options['start_time'])
    end_time = float(options['end_time'])
    time_step = float(options['time_step'])
    nprocs = int(options['nprocs'])
    day = int(options['day'])
    temporal = flags['t']
    binary = flags['b']
    binaryTmpName = 'binary'
    year = int(options['year'])
    rsun_flags = ''
    if flags['m']:
        rsun_flags += 'm'
    if flags['p']:
        rsun_flags += 'p'

    if not is_grass_7() and temporal:
        grass.warning(_("Flag t has effect only in GRASS 7"))

    # check: start < end
    if start_time > end_time:
        grass.fatal(_("Start time is after end time."))
    if time_step >= end_time - start_time:
        grass.fatal(_("Time step is too big."))

    # here we check all the days
    if not grass.overwrite():
        check_time_map_names(beam_rad_basename, grass.gisenv()['MAPSET'],
                             start_time, end_time, time_step, binary,
                             binaryTmpName)
        check_time_map_names(diff_rad_basename, grass.gisenv()['MAPSET'],
                             start_time, end_time, time_step, binary,
                             binaryTmpName)
        check_time_map_names(refl_rad_basename, grass.gisenv()['MAPSET'],
                             start_time, end_time, time_step, binary,
                             binaryTmpName)
        check_time_map_names(glob_rad_basename, grass.gisenv()['MAPSET'],
                             start_time, end_time, time_step, binary,
                             binaryTmpName)

    # check for slope/aspect
    if not aspect_input or not slope_input:
        params = {}
        if not aspect_input:
            aspect_input = create_tmp_map_name('aspect')
            params.update({'aspect': aspect_input})
            TMP.append(aspect_input)
        if not slope_input:
            slope_input = create_tmp_map_name('slope')
            params.update({'slope': slope_input})
            TMP.append(slope_input)

        grass.info(_("Running r.slope.aspect..."))
        grass.run_command('r.slope.aspect', elevation=elevation_input,
                          quiet=True, **params)

    grass.info(_("Running r.sun in a loop..."))
    count = 0
    # Parallel processing
    proc_list = []
    proc_count = 0
    suffixes = []
    suffixes_all = []
    times = list(frange(start_time, end_time, time_step))
    num_times = len(times)
    core.percent(0, num_times, 1)
    for time in times:
        count += 1
        core.percent(count, num_times, 10)

        suffix = '_' + format_time(time)
        proc_list.append(Process(target=run_r_sun,
                                 args=(elevation_input, aspect_input,
                                       slope_input, day, time,
                                       linke, linke_value,
                                       albedo, albedo_value,
                                       beam_rad_basename,
                                       diff_rad_basename,
                                       refl_rad_basename,
                                       glob_rad_basename,
                                       incidout_basename,
                                       suffix,
                                       binary, binaryTmpName,
                                       rsun_flags)))

        proc_list[proc_count].start()
        proc_count += 1
        suffixes.append(suffix)
        suffixes_all.append(suffix)

        if proc_count == nprocs or proc_count == num_times or count == num_times:
            proc_count = 0
            exitcodes = 0
            for proc in proc_list:
                proc.join()
                exitcodes += proc.exitcode

            if exitcodes != 0:
                core.fatal(_("Error while r.sun computation"))

            # Empty process list
            proc_list = []
            suffixes = []
    # FIXME: how percent really works?
    # core.percent(1, 1, 1)

    # add timestamps either via temporal framework in 7 or r.timestamp in 6.x
    if is_grass_7() and temporal:
        core.info(_("Registering created maps into temporal dataset..."))
        import grass.temporal as tgis

        def registerToTemporal(basename, suffixes, mapset, start_time,
                               time_step, title, desc):
            maps = ','.join([basename + suf + '@' + mapset for suf in suffixes])
            tgis.open_new_stds(basename, type='strds',
                               temporaltype='absolute',
                               title=title, descr=desc,
                               semantic='mean', dbif=None,
                               overwrite=grass.overwrite())
            tgis.register_maps_in_space_time_dataset(
                type='raster', name=basename, maps=maps, start=start_time,
                end=None, increment=time_step, dbif=None, interval=False)
        # Make sure the temporal database exists
        tgis.init()

        mapset = grass.gisenv()['MAPSET']
        absolute_time = datetime.datetime(year, 1, 1) + \
                        datetime.timedelta(days=day - 1) + \
                        datetime.timedelta(hours=start_time)
        start = absolute_time.strftime("%Y-%m-%d %H:%M:%S")
        step = datetime.timedelta(hours=time_step)
        step = "%d seconds" % step.seconds

        if beam_rad_basename:
            registerToTemporal(beam_rad_basename, suffixes_all, mapset, start,
                               step, title="Beam irradiance",
                               desc="Output beam irradiance raster maps [Wh.m-2]")
        if diff_rad_basename:
            registerToTemporal(diff_rad_basename, suffixes_all, mapset, start,
                               step, title="Diffuse irradiance",
                               desc="Output diffuse irradiance raster maps [Wh.m-2]")
        if refl_rad_basename:
            registerToTemporal(refl_rad_basename, suffixes_all, mapset, start,
                               step, title="Reflected irradiance",
                               desc="Output reflected irradiance raster maps [Wh.m-2]")
        if glob_rad_basename:
            registerToTemporal(glob_rad_basename, suffixes_all, mapset, start,
                               step, title="Total irradiance",
                               desc="Output total irradiance raster maps [Wh.m-2]")
        if incidout_basename:
            registerToTemporal(incidout_basename, suffixes_all, mapset, start,
                               step, title="Incidence angle",
                               desc="Output incidence angle raster maps")

    else:
        absolute_time = datetime.datetime(year, 1, 1) + \
                        datetime.timedelta(days=day - 1)
        for i, time in enumerate(times):
            grass_time = format_grass_time(absolute_time + datetime.timedelta(hours=time))
            if beam_rad_basename:
                set_time_stamp(beam_rad_basename + suffixes_all[i],
                               time=grass_time)
            if diff_rad_basename:
                set_time_stamp(diff_rad_basename + suffixes_all[i],
                               time=grass_time)
            if refl_rad_basename:
                set_time_stamp(refl_rad_basename + suffixes_all[i],
                               time=grass_time)
            if glob_rad_basename:
                set_time_stamp(glob_rad_basename + suffixes_all[i],
                               time=grass_time)
            if incidout_basename:
                set_time_stamp(incidout_basename + suffixes_all[i],
                               time=grass_time)

    if beam_rad_basename:
        maps = [beam_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if diff_rad_basename:
        maps = [diff_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if refl_rad_basename:
        maps = [refl_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if glob_rad_basename:
        maps = [glob_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if incidout_basename:
        maps = [incidout_basename + suf for suf in suffixes_all]
        set_color_table(maps)



if __name__ == "__main__":
    atexit.register(cleanup)
    main()
