#!/usr/bin/env python

############################################################################
#
# MODULE:    r.sun.daily; based on rsun_crop.sh from GRASS book
# AUTHOR(S): Vaclav Petras, Anna Petrasova
#            Nikos Alexandris (updates for linke, albedo, latitude, horizon)
#
# PURPOSE:
# COPYRIGHT: (C) 2013 - 2019 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Runs r.sun for multiple days in loop (mode 2)
# % keyword: raster
# % keyword: solar
# % keyword: sun energy
# %end

# %option G_OPT_R_ELEV
# % key: elevation
# % type: string
# % description: Name of the input elevation raster map [meters]
# % gisprompt: old,cell,raster
# % required : yes
# %end

# %option
# % key: aspect
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of the input aspect map (terrain aspect or azimuth of the solar panel) [decimal degrees]
# %end

# %option
# % key: slope
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of the input slope raster map (terrain slope or solar panel inclination) [decimal degrees]
# %end

# %option G_OPT_R_INPUT
# % key: linke
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of the Linke atmospheric turbidity coefficient input raster map [-]
# % required : no
# %end

# %option
# % key: linke_value
# % key_desc: float
# % type: double
# % description: A single value of the Linke atmospheric turbidity coefficient [-]
# % options: 0.0-7.0
# % answer: 3.0
# % required : no
# %end

# % rules
# %  exclusive: linke, linke_value
# % end

# %option G_OPT_R_INPUT
# % key: albedo
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of the ground albedo coefficient input raster map [-]
# % required : no
# %end

# %option
# % key: albedo_value
# % key_desc: float
# % type: double
# % description: A single value of the ground albedo coefficient [-]
# % options: 0.0-1.0
# % answer: 0.2
# % required : no
# %end

# % rules
# %  exclusive: albedo, albedo_value
# % end

# %option G_OPT_R_INPUT
# % key: lat
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of input raster map containing latitudes (if projection undefined) [decimal degrees]
# % required : no
# %end

# %option G_OPT_R_INPUT
# % key: long
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of input raster map containing longitudes (if projection undefined) [decimal degrees]
# % required : no
# %end

# %option G_OPT_R_BASENAME_INPUT
# % key: horizon_basename
# % key_desc: basename
# % type: string
# % gisprompt: old,cell,raster
# % description: The horizon information input map basename
# % required : no
# %end

# %option
# % key: horizon_step
# % key_desc: stepsize
# % type: string
# % gisprompt: old,cell,raster
# % description: Angle step size for multidirectional horizon [degrees]
# % required : no
# %end

# % rules
# %  requires_all: horizon_basename, horizon_step
# % end

# %option
# % key: start_day
# % type: integer
# % description: Start day (of year) of interval
# % options: 1-365
# % required : yes
# %end

# %option
# % key: end_day
# % type: integer
# % description: End day (of year) of interval
# % options: 1-365
# % required : yes
# %end

# %option
# % key: day_step
# % type: integer
# % description: Run r.sun for every n-th day [days]
# % options: 1-365
# % answer: 1
# %end

# %option
# % key: step
# % type: double
# % description: Time step when computing all-day radiation sums [decimal hours]
# % answer: 0.5
# %end

# %option
# % key: civil_time
# % type: double
# % description: Civil time zone value, if none, the time will be local solar time
# %end

# %option
# % key: beam_rad
# % type: string
# % gisprompt: new,cell,raster
# % description: Output beam irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
# % required: no
# %end

# %option
# % key: diff_rad
# % type: string
# % gisprompt: new,cell,raster
# % description: Output diffuse irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
# % required: no
# %end

# %option
# % key: refl_rad
# % type: string
# % gisprompt: new,cell,raster
# % description: Output ground reflected irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
# % required: no
# %end

# %option
# % key: glob_rad
# % type: string
# % gisprompt: new,cell,raster
# % description: Output global (total) irradiance/irradiation raster map cumulated for the whole period of time [Wh.m-2.day-1]
# % required: no
# %end

# %option
# % key: insol_time
# % type: string
# % gisprompt: new,cell,raster
# % description: Output insolation time raster map cumulated for the whole period of time [h]
# % required: no
# %end

# %option
# % key: beam_rad_basename
# % type: string
# % label: Base name for output beam irradiation raster maps [Wh.m-2.day-1]
# % description: Underscore and day number are added to the base name for daily maps
# %end

# %option
# % key: diff_rad_basename
# % type: string
# % label: Base name for output diffuse irradiation raster maps [Wh.m-2.day-1]
# % description: Underscore and day number are added to the base name for daily maps
# %end

# %option
# % key: refl_rad_basename
# % type: string
# % label: Base name for output ground reflected irradiation raster maps [Wh.m-2.day-1]
# % description: Underscore and day number are added to the base name for daily maps
# %end

# %option
# % key: glob_rad_basename
# % type: string
# % label: Base name for output global (total) irradiance/irradiation raster maps [Wh.m-2.day-1]
# % description: Underscore and day number are added to the base name for daily maps
# %end

# %option
# % key: insol_time_basename
# % type: string
# % label: Base name for output insolation time raster map cumulated for the whole period of time [h]
# % description: Underscore and day number are added to the base name for daily maps
# %end

# %option
# % key: solar_constant
# % type: double
# % required: no
# % multiple: no
# % label: Solar constant [W/m^2]
# % description: If not specified, r.sun default will be used.
# %end

# %option
# % key: nprocs
# % type: integer
# % description: Number of r.sun processes to run in parallel
# % options: 1-
# % answer: 1
# %end

# %flag
# % key: t
# % description: Dataset name is the same as the base name for the output series of maps
# % label: Register created series of output maps into temporal dataset
# %end

# %flag
# % key: p
# % description: Do not incorporate the shadowing effect of terrain
# %end

# %flag
# % key: m
# % description: Use the low-memory version of the program
# %end

import os
import atexit
from multiprocessing import Process

import grass.script as grass
import grass.script.core as core


REMOVE = []
MREMOVE = []


def cleanup():
    """
    Clean up temporary maps
    """
    if REMOVE or MREMOVE:
        core.info(_("Cleaning temporary maps..."))
    for rast in REMOVE:
        grass.run_command("g.remove", type="raster", name=rast, flags="f", quiet=True)
    for pattern in MREMOVE:
        grass.run_command(
            "g.remove",
            type="raster",
            pattern="{pattern}*".format(pattern=pattern),
            flags="f",
            quiet=True,
        )


def module_has_parameter(module, parameter):
    from grass.script import task as gtask

    task = gtask.command_info(module)
    return parameter in [each["name"] for each in task["params"]]


def create_tmp_map_name(name):
    """
    Create temporary map names
    """
    return "{mod}{pid}_{map_}_tmp".format(mod="r_sun_crop", pid=os.getpid(), map_=name)


def run_r_sun(
    elevation,
    aspect,
    slope,
    latitude,
    longitude,
    linke,
    linke_value,
    albedo,
    albedo_value,
    horizon_basename,
    horizon_step,
    solar_constant,
    day,
    step,
    beam_rad,
    diff_rad,
    refl_rad,
    glob_rad,
    insol_time,
    suffix,
    flags,
):
    """
    Execute r.sun using the provided input options. Except for the required
    parameters, the function updates the list of optional/selected parameters
    to instruct for user requested inputs and outputs.
    Optional inputs:

    - latitude
    - longitude
    - linke  OR  single linke value
    - albedo  OR  single albedo value
    - horizon maps
    """
    params = {}
    if beam_rad:
        params.update({"beam_rad": beam_rad + suffix})
    if diff_rad:
        params.update({"diff_rad": diff_rad + suffix})
    if refl_rad:
        params.update({"refl_rad": refl_rad + suffix})
    if glob_rad:
        params.update({"glob_rad": glob_rad + suffix})
    if insol_time:
        params.update({"insol_time": insol_time + suffix})
    if linke:
        params.update({"linke": linke})
    if linke_value:
        params.update({"linke_value": linke_value})
    if albedo:
        params.update({"albedo": albedo})
    if albedo_value:
        params.update({"albedo_value": albedo_value})
    if horizon_basename and horizon_step:
        params.update({"horizon_basename": horizon_basename})
        params.update({"horizon_step": horizon_step})
    if solar_constant is not None:
        params.update({"solar_constant": solar_constant})

    if flags:
        params.update({"flags": flags})

    grass.run_command(
        "r.sun",
        elevation=elevation,
        aspect=aspect,
        slope=slope,
        day=day,
        step=step,
        overwrite=core.overwrite(),
        quiet=True,
        **params
    )


def set_color_table(rasters):
    """
    Set 'gyr' color tables for raster maps
    """
    grass.run_command("r.colors", map=rasters, col="gyr", quiet=True)


def set_time_stamp(raster, day):
    """
    Timestamp script's daily output map
    """
    grass.run_command("r.timestamp", map=raster, date="%d days" % day, quiet=True)


def format_order(number, zeros=3):
    """
    Add leading zeros to string
    """
    return str(number).zfill(zeros)


def check_daily_map_names(basename, mapset, start_day, end_day, day_step):
    """
    Check if maps exist with name(s) identical to the scripts intented outputs
    """
    if not basename:
        return
    for day in range(start_day, end_day + 1, day_step):
        map_ = "{base}_{day}".format(base=basename, day=format_order(day))
        if grass.find_file(map_, element="cell", mapset=mapset)["file"]:
            grass.fatal(
                _(
                    "Raster map <{name}> already exists. "
                    "Change the base name or allow overwrite."
                    "".format(name=map_)
                )
            )


def sum_maps(sum_, basename, suffixes):
    """
    Sum up multiple raster maps
    """
    maps = "+".join([basename + suf for suf in suffixes])
    grass.mapcalc(
        "{sum_} = {new}".format(sum_=sum_, new=maps), overwrite=True, quiet=True
    )


def main():
    options, flags = grass.parser()

    # required
    elevation_input = options["elevation"]
    aspect_input = options["aspect"]
    slope_input = options["slope"]

    # optional
    latitude = options["lat"]
    longitude = options["long"]
    linke_input = options["linke"]
    linke_value = options["linke_value"]
    albedo_input = options["albedo"]
    albedo_value = options["albedo_value"]
    horizon_basename = options["horizon_basename"]
    horizon_step = options["horizon_step"]

    # outputs
    beam_rad = options["beam_rad"]
    diff_rad = options["diff_rad"]
    refl_rad = options["refl_rad"]
    glob_rad = options["glob_rad"]
    insol_time = options["insol_time"]
    beam_rad_basename = beam_rad_basename_user = options["beam_rad_basename"]
    diff_rad_basename = diff_rad_basename_user = options["diff_rad_basename"]
    refl_rad_basename = refl_rad_basename_user = options["refl_rad_basename"]
    glob_rad_basename = glob_rad_basename_user = options["glob_rad_basename"]
    insol_time_basename = insol_time_basename_user = options["insol_time_basename"]

    # missing output?
    if not any(
        [
            beam_rad,
            diff_rad,
            refl_rad,
            glob_rad,
            insol_time,
            beam_rad_basename,
            diff_rad_basename,
            refl_rad_basename,
            glob_rad_basename,
            insol_time_basename,
        ]
    ):
        grass.fatal(_("No output specified."))

    start_day = int(options["start_day"])
    end_day = int(options["end_day"])
    day_step = int(options["day_step"])

    if day_step > 1 and (beam_rad or diff_rad or refl_rad or glob_rad or insol_time):
        grass.fatal(
            _("Day step higher then 1 would produce" " meaningless cumulative maps.")
        )

    # check: start < end
    if start_day > end_day:
        grass.fatal(_("Start day is after end day."))
    if day_step >= end_day - start_day:
        grass.fatal(_("Day step is too big."))

    step = float(options["step"])

    nprocs = int(options["nprocs"])

    solar_constant = (
        float(options["solar_constant"]) if options["solar_constant"] else None
    )
    if solar_constant:
        # check it's newer version of r.sun
        if not module_has_parameter("r.sun", "solar_constant"):
            grass.warning(
                _(
                    "This version of r.sun lacks solar_constant option, "
                    "it will be ignored. Use newer version of r.sun."
                )
            )
            solar_constant = None

    if beam_rad and not beam_rad_basename:
        beam_rad_basename = create_tmp_map_name("beam_rad")
        MREMOVE.append(beam_rad_basename)
    if diff_rad and not diff_rad_basename:
        diff_rad_basename = create_tmp_map_name("diff_rad")
        MREMOVE.append(diff_rad_basename)
    if refl_rad and not refl_rad_basename:
        refl_rad_basename = create_tmp_map_name("refl_rad")
        MREMOVE.append(refl_rad_basename)
    if glob_rad and not glob_rad_basename:
        glob_rad_basename = create_tmp_map_name("glob_rad")
        MREMOVE.append(glob_rad_basename)
    if insol_time and not insol_time_basename:
        insol_time_basename = create_tmp_map_name("insol_time")
        MREMOVE.append(insol_time_basename)

    # check for existing identical map names
    if not grass.overwrite():
        check_daily_map_names(
            beam_rad_basename, grass.gisenv()["MAPSET"], start_day, end_day, day_step
        )
        check_daily_map_names(
            diff_rad_basename, grass.gisenv()["MAPSET"], start_day, end_day, day_step
        )
        check_daily_map_names(
            refl_rad_basename, grass.gisenv()["MAPSET"], start_day, end_day, day_step
        )
        check_daily_map_names(
            glob_rad_basename, grass.gisenv()["MAPSET"], start_day, end_day, day_step
        )
        check_daily_map_names(
            insol_time_basename, grass.gisenv()["MAPSET"], start_day, end_day, day_step
        )

    # check for slope/aspect
    if not aspect_input or not slope_input:
        params = {}
        if not aspect_input:
            aspect_input = create_tmp_map_name("aspect")
            params.update({"aspect": aspect_input})
            REMOVE.append(aspect_input)
        if not slope_input:
            slope_input = create_tmp_map_name("slope")
            params.update({"slope": slope_input})
            REMOVE.append(slope_input)

        grass.info(_("Running r.slope.aspect..."))
        grass.run_command(
            "r.slope.aspect", elevation=elevation_input, quiet=True, **params
        )

    if beam_rad:
        grass.mapcalc("{beam} = 0".format(beam=beam_rad), quiet=True)
    if diff_rad:
        grass.mapcalc("{diff} = 0".format(diff=diff_rad), quiet=True)
    if refl_rad:
        grass.mapcalc("{refl} = 0".format(refl=refl_rad), quiet=True)
    if glob_rad:
        grass.mapcalc("{glob} = 0".format(glob=glob_rad), quiet=True)
    if insol_time:
        grass.mapcalc("{insol} = 0".format(insol=insol_time), quiet=True)

    rsun_flags = ""
    if flags["m"]:
        rsun_flags += "m"
    if flags["p"]:
        rsun_flags += "p"

    grass.info(_("Running r.sun in a loop..."))
    count = 0
    # Parallel processing
    proc_list = []
    proc_count = 0
    suffixes_all = []
    days = range(start_day, end_day + 1, day_step)
    num_days = len(days)
    core.percent(0, num_days, 1)
    for day in days:
        count += 1
        core.percent(count, num_days, 10)

        suffix = "_" + format_order(day)
        proc_list.append(
            Process(
                target=run_r_sun,
                args=(
                    elevation_input,
                    aspect_input,
                    slope_input,
                    latitude,
                    longitude,
                    linke_input,
                    linke_value,
                    albedo_input,
                    albedo_value,
                    horizon_basename,
                    horizon_step,
                    solar_constant,
                    day,
                    step,
                    beam_rad_basename,
                    diff_rad_basename,
                    refl_rad_basename,
                    glob_rad_basename,
                    insol_time_basename,
                    suffix,
                    rsun_flags,
                ),
            )
        )

        proc_list[proc_count].start()
        proc_count += 1
        suffixes_all.append(suffix)

        if proc_count == nprocs or proc_count == num_days or count == num_days:
            proc_count = 0
            exitcodes = 0
            for proc in proc_list:
                proc.join()
                exitcodes += proc.exitcode

            if exitcodes != 0:
                core.fatal(_("Error while r.sun computation"))

            # Empty process list
            proc_list = []

    if beam_rad:
        sum_maps(beam_rad, beam_rad_basename, suffixes_all)
    if diff_rad:
        sum_maps(diff_rad, diff_rad_basename, suffixes_all)
    if refl_rad:
        sum_maps(refl_rad, refl_rad_basename, suffixes_all)
    if glob_rad:
        sum_maps(glob_rad, glob_rad_basename, suffixes_all)
    if insol_time:
        sum_maps(insol_time, insol_time_basename, suffixes_all)

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
    if insol_time:
        set_color_table([insol_time])

    if not any(
        [
            beam_rad_basename_user,
            diff_rad_basename_user,
            refl_rad_basename_user,
            glob_rad_basename_user,
            insol_time_basename_user,
        ]
    ):
        return 0

    # add timestamps and register to spatio-temporal raster data set
    temporal = flags["t"]
    if temporal:
        core.info(_("Registering created maps into temporal dataset..."))
        import grass.temporal as tgis

        def registerToTemporal(
            basename, suffixes, mapset, start_day, day_step, title, desc
        ):
            """
            Register daily output maps in spatio-temporal raster data set
            """
            maps = ",".join([basename + suf + "@" + mapset for suf in suffixes])
            tgis.open_new_stds(
                basename,
                type="strds",
                temporaltype="relative",
                title=title,
                descr=desc,
                semantic="sum",
                dbif=None,
                overwrite=grass.overwrite(),
            )

            tgis.register_maps_in_space_time_dataset(
                type="rast",
                name=basename,
                maps=maps,
                start=start_day,
                end=None,
                unit="days",
                increment=day_step,
                dbif=None,
                interval=False,
            )

        # Make sure the temporal database exists
        tgis.init()

        mapset = grass.gisenv()["MAPSET"]
        if beam_rad_basename_user:
            registerToTemporal(
                beam_rad_basename,
                suffixes_all,
                mapset,
                start_day,
                day_step,
                title="Beam irradiation",
                desc="Output beam irradiation raster maps [Wh.m-2.day-1]",
            )
        if diff_rad_basename_user:
            registerToTemporal(
                diff_rad_basename,
                suffixes_all,
                mapset,
                start_day,
                day_step,
                title="Diffuse irradiation",
                desc="Output diffuse irradiation raster maps [Wh.m-2.day-1]",
            )
        if refl_rad_basename_user:
            registerToTemporal(
                refl_rad_basename,
                suffixes_all,
                mapset,
                start_day,
                day_step,
                title="Reflected irradiation",
                desc="Output reflected irradiation raster maps [Wh.m-2.day-1]",
            )
        if glob_rad_basename_user:
            registerToTemporal(
                glob_rad_basename,
                suffixes_all,
                mapset,
                start_day,
                day_step,
                title="Total irradiation",
                desc="Output total irradiation raster maps [Wh.m-2.day-1]",
            )
        if insol_time_basename_user:
            registerToTemporal(
                insol_time_basename,
                suffixes_all,
                mapset,
                start_day,
                day_step,
                title="Total insolation",
                desc="Output total insolation raster maps [h]",
            )

    # just add timestamps, don't register
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
            if insol_time_basename_user:
                set_time_stamp(insol_time_basename + suffixes_all[i], day=day)

    # set color table for daily maps
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
    if insol_time_basename_user:
        maps = [insol_time_basename + suf for suf in suffixes_all]
        set_color_table(maps)


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
