#!/usr/bin/env python

############################################################################
#
# MODULE:    r.sun.daily for GRASS 6 and 7; based on rsun_crop.sh from GRASS book
# AUTHOR(S): Vaclav Petras, Anna Petrasova
#
# PURPOSE:
# COPYRIGHT: (C) 2013 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

#%module
#% description: Runs r.sun for multiple days in loop (mode 2)
#% keywords: raster
#% keywords: sun
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: elev_in
#% description: Name of the input elevation raster map [meters]
#% required : yes
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: asp_in
#% description: Name of the input aspect map (terrain aspect or azimuth of the solar panel) [decimal degrees]
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: slope_in
#% description: Name of the input slope raster map (terrain slope or solar panel inclination) [decimal degrees]
#%end
#%option
#% key: start_day
#% type: integer
#% description: Start day (of year) of interval
#% options: 1-365
#% required : yes
#%end
#%option
#% key: end_day
#% type: integer
#% description: End day (of year) of interval
#% options: 1-365
#% required : yes
#%end
#%option
#% key: day_step
#% type: integer
#% description: Run r.sun for every n-th day [days]
#% options: 1-365
#% answer: 1
#%end
#%option
#% key: step
#% type: double
#% description: Time step when computing all-day radiation sums [decimal hours]
#% answer: 0.5
#%end
#%option
#% key: civil_time
#% type: double
#% description: Civil time zone value, if none, the time will be local solar time
#%end
#%option
#% type: string
#% gisprompt: new,cell,raster
#% key: beam_rad
#% description: Output beam irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
#% required: no
#%end
#%option
#% type: string
#% gisprompt: new,cell,raster
#% key: diff_rad
#% description: Output diffuse irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
#% required: no
#%end
#%option
#% type: string
#% gisprompt: new,cell,raster
#% key: refl_rad
#% description: Output ground reflected irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
#% required: no
#%end
#%option
#% type: string
#% gisprompt: new,cell,raster
#% key: glob_rad
#% description: Output global (total) irradiance/irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
#% required: no
#%end
#%option
#% key: beam_rad_basename
#% type: string
#% label: Base name for output beam irradiation raster maps [Wh.m-2.day-1]
#% description: Underscore and day number are added to the base name for daily maps
#%end
#%option
#% key: diff_rad_basename
#% type: string
#% label: Base name for output diffuse irradiation raster maps [Wh.m-2.day-1]
#% description: Underscore and day number are added to the base name for daily maps
#%end
#%option
#% key: refl_rad_basename
#% type: string
#% label: Base name for output ground reflected irradiation raster maps [Wh.m-2.day-1]
#% description: Underscore and day number are added to the base name for daily maps
#%end
#%option
#% key: glob_rad_basename
#% type: string
#% label: Base name for output global (total) irradiance/irradiation raster maps [Wh.m-2.day-1]
#% description: Underscore and day number are added to the base name for daily maps
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


import os
import atexit
from multiprocessing import Process

import grass.script as grass
import grass.script.core as core


REMOVE = []
MREMOVE = []


def cleanup():
    if REMOVE or MREMOVE:
        core.info(_("Cleaning temporary maps..."))
    for rast in REMOVE:
        grass.run_command('g.remove', type='rast', pattern=rast, flags='f',
                          quiet=True)
    for pattern in MREMOVE:
        grass.run_command('g.remove', type='rast', pattern='%s*' % pattern,
                          flags='f', quiet=True)


def is_grass_7():
    if core.version()['version'].split('.')[0] == '7':
        return True
    return False


def create_tmp_map_name(name):
    return '{mod}{pid}_{map_}_tmp'.format(mod='r_sun_crop',
                                          pid=os.getpid(),
                                          map_=name)


# add latitude map
def run_r_sun(elevation, aspect, slope, day, step,
              beam_rad, diff_rad, refl_rad, glob_rad, suffix):
    params = {}
    if beam_rad:
        params.update({'beam_rad': beam_rad + suffix})
    if diff_rad:
        params.update({'diff_rad': diff_rad + suffix})
    if refl_rad:
        params.update({'refl_rad': refl_rad + suffix})
    if glob_rad:
        params.update({'glob_rad': glob_rad + suffix})

    if is_grass_7():
        grass.run_command('r.sun', elevation=elevation, aspect=aspect,
                          slope=slope, day=day, step=step,
                          overwrite=core.overwrite(), quiet=True,
                          **params)
    else:
        grass.run_command('r.sun', elevin=elevation, aspin=aspect,
                          slopein=slope,
                          day=day, step=step,
                          overwrite=core.overwrite(), quiet=True,
                          **params)


def set_color_table(rasters):
    if is_grass_7():
        grass.run_command('r.colors', map=rasters, col='gyr', quiet=True)
    else:
        for rast in rasters:
            grass.run_command('r.colors', map=rast, col='gyr', quiet=True)


def set_time_stamp(raster, day):
    grass.run_command('r.timestamp', map=raster, date='%d days' % day,
                      quiet=True)


def format_order(number, zeros=3):
    return str(number).zfill(zeros)


def check_daily_map_names(basename, mapset, start_day, end_day, day_step):
    if not basename:
        return
    for day in range(start_day, end_day + 1, day_step):
        map_ = '%s%s%s' % (basename, '_', format_order(day))
        if grass.find_file(map_, element='cell', mapset=mapset)['file']:
            grass.fatal(_("Raster map <%s> already exists. Change the base "
                          "name or allow overwrite.") % map_)


def sum_maps(sum_, basename, suffixes):
    maps = '+'.join([basename + suf for suf in suffixes])
    grass.mapcalc('{sum_}={sum_} + {new}'.format(sum_=sum_, new=maps),
                  overwrite=True, quiet=True)


def main():
    options, flags = grass.parser()

    elevation_input = options['elev_in']
    aspect_input = options['asp_in']
    slope_input = options['slope_in']

    beam_rad = options['beam_rad']
    diff_rad = options['diff_rad']
    refl_rad = options['refl_rad']
    glob_rad = options['glob_rad']

    beam_rad_basename = beam_rad_basename_user = options['beam_rad_basename']
    diff_rad_basename = diff_rad_basename_user = options['diff_rad_basename']
    refl_rad_basename = refl_rad_basename_user = options['refl_rad_basename']
    glob_rad_basename = glob_rad_basename_user = options['glob_rad_basename']

    if not any([beam_rad, diff_rad, refl_rad, glob_rad,
                beam_rad_basename, diff_rad_basename,
                refl_rad_basename, glob_rad_basename]):
        grass.fatal(_("No output specified."))

    start_day = int(options['start_day'])
    end_day = int(options['end_day'])
    day_step = int(options['day_step'])

    if day_step > 1 and (beam_rad or diff_rad or refl_rad or glob_rad):
        grass.fatal(_("Day step higher then 1 would produce"
                      " meaningless cumulative maps."))

    # check: start < end
    if start_day > end_day:
        grass.fatal(_("Start day is after end day."))
    if day_step >= end_day - start_day:
        grass.fatal(_("Day step is too big."))

    step = float(options['step'])

    nprocs = int(options['nprocs'])

    temporal = flags['t']
    if not is_grass_7() and temporal:
        grass.warning(_("Flag t has effect only in GRASS 7"))

    if beam_rad and not beam_rad_basename:
        beam_rad_basename = create_tmp_map_name('beam_rad')
        MREMOVE.append(beam_rad_basename)
    if diff_rad and not diff_rad_basename:
        diff_rad_basename = create_tmp_map_name('diff_rad')
        MREMOVE.append(diff_rad_basename)
    if refl_rad and not refl_rad_basename:
        refl_rad_basename = create_tmp_map_name('refl_rad')
        MREMOVE.append(refl_rad_basename)
    if glob_rad and not glob_rad_basename:
        glob_rad_basename = create_tmp_map_name('glob_rad')
        MREMOVE.append(glob_rad_basename)

    # here we check all the days
    if not grass.overwrite():
        check_daily_map_names(beam_rad_basename, grass.gisenv()['MAPSET'],
                              start_day, end_day, day_step)
        check_daily_map_names(diff_rad_basename, grass.gisenv()['MAPSET'],
                              start_day, end_day, day_step)
        check_daily_map_names(refl_rad_basename, grass.gisenv()['MAPSET'],
                              start_day, end_day, day_step)
        check_daily_map_names(glob_rad_basename, grass.gisenv()['MAPSET'],
                              start_day, end_day, day_step)

    # check for slope/aspect
    if not aspect_input or not slope_input:
        params = {}
        if not aspect_input:
            aspect_input = create_tmp_map_name('aspect')
            params.update({'aspect': aspect_input})
            REMOVE.append(aspect_input)
        if not slope_input:
            slope_input = create_tmp_map_name('slope')
            params.update({'slope': slope_input})
            REMOVE.append(slope_input)

        grass.info(_("Running r.slope.aspect..."))
        grass.run_command('r.slope.aspect', elevation=elevation_input,
                          quiet=True, **params)

    if beam_rad:
        grass.mapcalc('%s=0' % beam_rad, quiet=True)
    if diff_rad:
        grass.mapcalc('%s=0' % diff_rad, quiet=True)
    if refl_rad:
        grass.mapcalc('%s=0' % refl_rad, quiet=True)
    if glob_rad:
        grass.mapcalc('%s=0' % glob_rad, quiet=True)

    grass.info(_("Running r.sun in a loop..."))
    count = 0
    # Parallel processing
    proc_list = []
    proc_count = 0
    suffixes = []
    suffixes_all = []
    days = range(start_day, end_day + 1, day_step)
    num_days = len(days)
    core.percent(0, num_days, 1)
    for day in days:
        count += 1
        core.percent(count, num_days, 10)

        suffix = '_' + format_order(day)
        proc_list.append(Process(target=run_r_sun,
                                 args=(elevation_input, aspect_input,
                                       slope_input, day, step,
                                       beam_rad_basename,
                                       diff_rad_basename,
                                       refl_rad_basename,
                                       glob_rad_basename,
                                       suffix)))

        proc_list[proc_count].start()
        proc_count += 1
        suffixes.append(suffix)
        suffixes_all.append(suffix)

        if proc_count == nprocs or proc_count == num_days or count == num_days:
            proc_count = 0
            exitcodes = 0
            for proc in proc_list:
                proc.join()
                exitcodes += proc.exitcode

            if exitcodes != 0:
                core.fatal(_("Error while r.sun computation"))

            if beam_rad:
                sum_maps(beam_rad, beam_rad_basename, suffixes)
            if diff_rad:
                sum_maps(diff_rad, diff_rad_basename, suffixes)
            if refl_rad:
                sum_maps(refl_rad, refl_rad_basename, suffixes)
            if glob_rad:
                sum_maps(glob_rad, glob_rad_basename, suffixes)

            # Empty process list
            proc_list = []
            suffixes = []
    # FIXME: how percent really works?
    # core.percent(1, 1, 1)

    # set color table
    if beam_rad:
        set_color_table([beam_rad])
    if diff_rad:
        set_color_table([diff_rad])
    if refl_rad:
        set_color_table([refl_rad])
    if glob_rad:
        set_color_table([glob_rad])

    if not any([beam_rad_basename_user, diff_rad_basename_user,
                refl_rad_basename_user, glob_rad_basename_user]):
        return 0

    # add timestamps either via temporal framework in 7 or r.timestamp in 6.x
    if is_grass_7() and temporal:
        core.info(_("Registering created maps into temporal dataset..."))
        import grass.temporal as tgis

        def registerToTemporal(basename, suffixes, mapset, start_day, day_step,
                               title, desc):
            maps = ','.join([basename + suf + '@' + mapset for suf in suffixes])
            tgis.open_new_space_time_dataset(basename, type='strds',
                                             temporaltype='relative',
                                             title=title, descr=desc,
                                             semantic='sum', dbif=None,
                                             overwrite=grass.overwrite())
            tgis.register_maps_in_space_time_dataset(
                type='rast', name=basename, maps=maps, start=start_day, end=None,
                unit='days', increment=day_step, dbif=None, interval=False)
        # Make sure the temporal database exists
        tgis.init()

        mapset = grass.gisenv()['MAPSET']
        if beam_rad_basename_user:
            registerToTemporal(beam_rad_basename, suffixes_all, mapset,
                               start_day, day_step, title="Beam irradiation",
                               desc="Output beam irradiation raster maps [Wh.m-2.day-1]")
        if diff_rad_basename_user:
            registerToTemporal(diff_rad_basename, suffixes_all, mapset,
                               start_day, day_step,
                               title="Diffuse irradiation",
                               desc="Output diffuse irradiation raster maps [Wh.m-2.day-1]")
        if refl_rad_basename_user:
            registerToTemporal(refl_rad_basename, suffixes_all, mapset,
                               start_day, day_step,
                               title="Reflected irradiation",
                               desc="Output reflected irradiation raster maps [Wh.m-2.day-1]")
        if glob_rad_basename_user:
            registerToTemporal(glob_rad_basename, suffixes_all, mapset,
                               start_day, day_step, title="Total irradiation",
                               desc="Output total irradiation raster maps [Wh.m-2.day-1]")

    else:
        for i, day in enumerate(days):
            if beam_rad_basename_user:
                set_time_stamp(beam_rad_basename + suffixes_all[i], day=day)
            if diff_rad_basename_user:
                set_time_stamp(diff_rad_basename + suffixes_all[i], day=day)
            if refl_rad_basename_user:
                set_time_stamp(refl_rad_basename + suffixes_all[i], day=day)
            if glob_rad_basename_user:
                set_time_stamp(glob_rad_basename + suffixes_all[i], day=day)

    if beam_rad_basename_user:
        maps = [beam_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps)
    if diff_rad_basename_user:
        maps = [diff_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps)
    if refl_rad_basename_user:
        maps = [refl_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps)
    if glob_rad_basename_user:
        maps = [glob_rad_basename + suf for suf in suffixes_all]
        set_color_table(maps)


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
