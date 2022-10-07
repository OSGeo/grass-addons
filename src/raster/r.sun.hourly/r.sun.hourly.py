#!/usr/bin/env python

############################################################################
#
# MODULE:    r.sun.hourly for GRASS 8
# AUTHOR(S): Vaclav Petras, Anna Petrasova
# PURPOSE:
# COPYRIGHT: (C) 2013 - 2022 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Runs r.sun in loop for given time range within one day (mode 1 or 2)
# % keyword: raster
# % keyword: solar
# % keyword: sun energy
# % keyword: parallel
# % overwrite: yes
# %end
# %option
# % type: string
# % gisprompt: old,cell,raster
# % key: elevation
# % description: Name of the input elevation raster map [meters]
# % required : yes
# %end
# %option
# % type: string
# % gisprompt: old,cell,raster
# % key: aspect
# % description: Name of the input aspect map (terrain aspect or azimuth of the solar panel) [decimal degrees]
# %end
# %option
# % type: string
# % gisprompt: old,cell,raster
# % key: slope
# % description: Name of the input slope raster map (terrain slope or solar panel inclination) [decimal degrees]
# %end
# %option G_OPT_R_INPUT
# % key: linke
# % description: Name of the Linke atmospheric turbidity coefficient input raster map [-]
# % required : no
# %end
# %option
# % key: linke_value
# % type: double
# % description: A single value of the Linke atmospheric turbidity coefficient [-]
# % options: 0.0-7.0
# % answer: 3.0
# % required: no
# %end
# % rules
# %  exclusive: linke, linke_value
# % end
# %option G_OPT_R_INPUT
# % key: albedo
# % description: Name of the ground albedo coefficient input raster map [-]
# % required: no
# %end
# %option
# % key: albedo_value
# % type: double
# % description: A single value of the ground albedo coefficient [-]
# % options: 0.0-1.0
# % answer: 0.2
# % required: no
# %end
# % rules
# %  exclusive: albedo, albedo_value
# % end
# %option G_OPT_R_INPUT
# % key: coeff_bh
# % required: no
# % description: Name of real-sky beam radiation coefficient (thick cloud) input raster map [0-1]
# %end
# %option G_OPT_STRDS_INPUT
# % key: coeff_bh_strds
# % required: no
# % description: Name of real-sky beam radiation coefficient (thick cloud) input space-time raster dataset
# %end
# % rules
# %  exclusive: coeff_bh, coeff_bh_strds
# % end
# %option G_OPT_R_INPUT
# % key: coeff_dh
# % required: no
# % description: Name of real-sky diffuse radiation coefficient (haze) input raster map [0-1]
# %end
# %option G_OPT_STRDS_INPUT
# % key: coeff_dh_strds
# % required: no
# % description: Name of real-sky diffuse radiation coefficient (haze) input space-time raster dataset
# %end
# % rules
# %  exclusive: coeff_dh, coeff_dh_strds
# % end
# %option G_OPT_R_INPUT
# % key: lat
# % required: no
# % description: Name of input raster map containing latitudes [decimal degrees]
# %end
# %option G_OPT_R_INPUT
# % key: long
# % required: no
# % description: Name of input raster map containing longitudes [decimal degrees]
# %end
# %option
# % key: mode
# % required: yes
# % options: mode1,mode2
# % answer: mode1
# % descriptions: mode1;r.sun mode 1 computes irradiance [W.m-2];mode2;r.sun mode 2 computes irradiation [Wh.m-2]
# % description: Select r.sun mode to choose between irradiance (mode 1) and irradiation (mode 2)
# %end
# %option
# % key: start_time
# % type: double
# % label: Start time of interval
# % description: Use up to 2 decimal places
# % options: 0-24
# % required : yes
# %end
# %option
# % key: end_time
# % type: double
# % label: End time of interval
# % description: Use up to 2 decimal places
# % options: 0-24
# % required : yes
# %end
# %option
# % key: time_step
# % type: double
# % label: Time step for running r.sun [decimal hours]
# % description: Use up to 2 decimal places
# % options: 0-24
# % answer: 1
# %end
# %option
# % key: day
# % type: integer
# % description: No. of day of the year
# % options: 1-365
# % required : yes
# %end
# %option
# % key: year
# % type: integer
# % label: Year used for map registration into temporal dataset or r.timestamp
# % description: This value is not used in r.sun calculations
# % options: 1900-9999
# % required: yes
# % answer: 1900
# %end
# %option
# % key: civil_time
# % type: double
# % description: Civil time zone value, if none, the time will be local solar time
# %end
# %option
# % key: distance_step
# % type: double
# % required: no
# % description: Sampling distance step coefficient (0.5-1.5)
# % answer: 1.0
# %end
# %option
# % key: beam_rad_basename
# % type: string
# % label: Base name for output beam irradiance [W.m-2] (mode 1) or irradiation raster map [Wh.m-2] (mode 2)
# % description: Underscore and time are added to the base name for each map
# %end
# %option
# % key: diff_rad_basename
# % type: string
# % label: Base name for output diffuse irradiance [W.m-2] (mode 1) or irradiation raster map [Wh.m-2] (mode 2)
# % description: Underscore and time are added to the base name for each map
# %end
# %option
# % key: refl_rad_basename
# % type: string
# % label: Base name for output ground reflected irradiance [W.m-2] (mode 1) or irradiation raster map [Wh.m-2] (mode 2)
# % description: Underscore and time are added to the base name for each map
# %end
# %option
# % key: glob_rad_basename
# % type: string
# % label: Base name for output global (total) irradiance [W.m-2] (mode 1) or irradiation raster map [Wh.m-2] (mode 2)
# % description: Underscore and time are added to the base name for each map
# %end
# %option
# % key: incidout_basename
# % type: string
# % label: Base name for output incidence angle raster maps (mode 1 only)
# % description: Underscore and time are added to the base name for each map
# %end
# %option
# % key: beam_rad
# % type: string
# % description: Output beam irradiation raster map [Wh.m-2] (mode 2) integrated over specified time period
# %end
# %option
# % key: diff_rad
# % type: string
# % description: Output diffuse irradiation raster map [Wh.m-2] (mode 2) integrated over specified time period
# %end
# %option
# % key: refl_rad
# % type: string
# % description: Output ground reflected irradiation raster map [Wh.m-2] (mode 2) integrated over specified time period
# %end
# %option
# % key: glob_rad
# % type: string
# % description: Output global (total) irradiation raster map [Wh.m-2] (mode 2) integrated over specified time period
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
# % key: c
# % description: Compute cumulative raster maps of irradiation (only with mode 2)
# %end
# %flag
# % key: t
# % description: Dataset name is the same as the base name for the output series of maps
# % label: Register created series of output maps into temporal dataset
# %end
# %flag
# % key: b
# % description: Create binary rasters instead of irradiance rasters
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
import datetime
import atexit
from multiprocessing import Process

import grass.script as grass
import grass.script.core as core
from grass.exceptions import CalledModuleError

REMOVE = []
MREMOVE = []


def cleanup():
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


def create_tmp_map_name(name):
    return "{mod}{pid}_{map_}_tmp".format(mod="r_sun_crop", pid=os.getpid(), map_=name)


# add latitude map
def run_r_sun(
    elevation,
    aspect,
    slope,
    day,
    time,
    civil_time,
    linke,
    linke_value,
    albedo,
    albedo_value,
    coeff_bh,
    coeff_dh,
    lat,
    long_,
    beam_rad,
    diff_rad,
    refl_rad,
    glob_rad,
    incidout,
    suffix,
    binary,
    tmpName,
    time_step,
    distance_step,
    solar_constant,
    flags,
):
    params = {}
    if linke:
        params.update({"linke": linke})
    if linke_value:
        params.update({"linke_value": linke_value})
    if albedo:
        params.update({"albedo": albedo})
    if albedo_value:
        params.update({"albedo_value": albedo_value})
    if coeff_bh:
        params.update({"coeff_bh": coeff_bh})
    if coeff_dh:
        params.update({"coeff_dh": coeff_dh})
    if lat:
        params.update({"lat": lat})
    if long_:
        params.update({"long": long_})
    if beam_rad:
        params.update({"beam_rad": beam_rad + suffix})
    if diff_rad:
        params.update({"diff_rad": diff_rad + suffix})
    if refl_rad:
        params.update({"refl_rad": refl_rad + suffix})
    if glob_rad:
        params.update({"glob_rad": glob_rad + suffix})
    if incidout:
        params.update({"incidout": incidout + suffix})
    if flags:
        params.update({"flags": flags})
    if civil_time is not None:
        params.update({"civil_time": civil_time})
    if distance_step is not None:
        params.update({"distance_step": distance_step})
    if solar_constant is not None:
        params.update({"solar_constant": solar_constant})

    grass.run_command(
        "r.sun",
        elevation=elevation,
        aspect=aspect,
        slope=slope,
        day=day,
        time=time,
        overwrite=core.overwrite(),
        quiet=True,
        **params,
    )
    if binary:
        for output in (beam_rad, diff_rad, refl_rad, glob_rad):
            if not output:
                continue
            exp = "{out} = if({inp} > 0, 1, 0)".format(
                out=output + suffix + tmpName, inp=output + suffix
            )
            grass.mapcalc(exp=exp, overwrite=core.overwrite())
            grass.run_command(
                "g.rename",
                raster=[output + suffix + tmpName, output + suffix],
                quiet=True,
                overwrite=True,
            )
    if time_step:
        for output in (beam_rad, diff_rad, refl_rad, glob_rad):
            if not output:
                continue
            exp = "{out} = {inp} * {ts}".format(
                inp=output + suffix, ts=time_step, out=output + suffix + tmpName
            )
            grass.mapcalc(exp=exp, overwrite=core.overwrite())
            grass.run_command(
                "g.rename",
                raster=[output + suffix + tmpName, output + suffix],
                overwrite=True,
                quiet=True,
            )


def set_color_table(rasters, binary=False):
    table = "gyr"
    if binary:
        table = "grey"
    grass.run_command("r.colors", map=rasters, col=table, quiet=True)


def set_time_stamp(raster, time):
    grass.run_command("r.timestamp", map=raster, date=time, quiet=True)


def format_time(time):
    return "%05.2f" % time


def check_time_map_names(
    basename, mapset, start_time, end_time, time_step, binary, tmpName, mode1
):
    if not basename:
        return
    if mode1:
        f = frange1
    else:
        f = frange2
    for time in f(start_time, end_time, time_step):
        maps = []
        maps.append(
            "{name}{delim}{time}".format(
                name=basename, delim="_", time=format_time(time)
            )
        )
        if binary:
            maps.append(
                "{name}{delim}{time}{binary}".format(
                    name=basename, delim="_", time=format_time(time), binary=tmpName
                )
            )
        for map_ in maps:
            if grass.find_file(map_, element="cell", mapset=mapset)["file"]:
                grass.fatal(
                    _(
                        "Raster map <%s> already exists. Change the base"
                        " name or allow overwrite."
                    )
                    % map_
                )


def frange1(x, y, step):
    """Returns [x, y]"""
    while x <= y:
        yield x
        x += step


def frange2(x, y, step):
    """Returns [x, y)"""
    i = 0
    while x + i * step < y:
        yield x + i * step + 0.5 * step
        i += 1


def format_grass_time(dt):
    """!Format datetime object to grass timestamps.
    Copied from temporal framework to use thsi script also in GRASS 6.
    """
    # GRASS datetime month names
    month_names = [
        "",
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    return "%.2i %s %.4i %.2i:%.2i:%.2i" % (
        dt.day,
        month_names[dt.month],
        dt.year,
        dt.hour,
        dt.minute,
        dt.second,
    )


def sum_maps(sum_, basename, suffixes):
    """
    Sum up multiple raster maps
    """
    maps = "+".join([basename + suf for suf in suffixes])
    grass.mapcalc(
        "{sum_} = {new}".format(sum_=sum_, new=maps), overwrite=True, quiet=True
    )


def get_raster_from_strds(year, day, time, strds):
    """Return a raster map for certain date and time from a strds"""
    dt = datetime.datetime(year, 1, 1)
    dt += datetime.timedelta(days=day - 1) + datetime.timedelta(hours=time)
    where = "start_time <= '{t}' AND end_time >= '{t}'".format(
        t=dt.strftime("%Y-%m-%d %H:%M")
    )
    try:
        raster = grass.read_command(
            "t.rast.list",
            flags="u",
            input=strds,
            order="start_time",
            where=where,
            method="comma",
            quiet=True,
        ).strip()
        return raster
    except CalledModuleError:
        grass.warning(
            "No raster found for {t} in dataset {s}".format(
                t=dt.strftime("%Y-%m-%d %H:%M"), s=strds
            )
        )
        return None


def main():
    options, flags = grass.parser()

    elevation_input = options["elevation"]
    aspect_input = options["aspect"]
    slope_input = options["slope"]
    linke = options["linke"]
    linke_value = options["linke_value"]
    albedo = options["albedo"]
    albedo_value = options["albedo_value"]
    coeff_bh = options["coeff_bh"]
    coeff_bh_strds = options["coeff_bh_strds"]
    coeff_dh = options["coeff_dh"]
    coeff_dh_strds = options["coeff_dh_strds"]
    lat = options["lat"]
    long_ = options["long"]

    beam_rad_basename = beam_rad_basename_user = options["beam_rad_basename"]
    diff_rad_basename = diff_rad_basename_user = options["diff_rad_basename"]
    refl_rad_basename = refl_rad_basename_user = options["refl_rad_basename"]
    glob_rad_basename = glob_rad_basename_user = options["glob_rad_basename"]
    incidout_basename = options["incidout_basename"]

    beam_rad = options["beam_rad"]
    diff_rad = options["diff_rad"]
    refl_rad = options["refl_rad"]
    glob_rad = options["glob_rad"]

    has_output = any(
        [
            beam_rad_basename,
            diff_rad_basename,
            refl_rad_basename,
            glob_rad_basename,
            incidout_basename,
            beam_rad,
            diff_rad,
            refl_rad,
            glob_rad,
        ]
    )

    if not has_output:
        grass.fatal(_("No output specified."))

    start_time = float(options["start_time"])
    end_time = float(options["end_time"])
    time_step = float(options["time_step"])
    nprocs = int(options["nprocs"])
    day = int(options["day"])
    civil_time = float(options["civil_time"]) if options["civil_time"] else None
    distance_step = (
        float(options["distance_step"]) if options["distance_step"] else None
    )
    solar_constant = (
        float(options["solar_constant"]) if options["solar_constant"] else None
    )
    temporal = flags["t"]
    binary = flags["b"]
    mode1 = True if options["mode"] == "mode1" else False
    mode2 = not mode1
    tmpName = "tmp"
    year = int(options["year"])
    rsun_flags = ""
    if flags["m"]:
        rsun_flags += "m"
    if flags["p"]:
        rsun_flags += "p"

    # check: start < end
    if start_time > end_time:
        grass.fatal(_("Start time is after end time."))
    if time_step >= end_time - start_time:
        grass.fatal(_("Time step is too big."))

    if mode2 and incidout_basename:
        grass.fatal(_("Can't compute incidence angle in mode 2"))
    if flags["c"] and mode1:
        grass.fatal(_("Can't compute cumulative irradiation rasters in mode 1"))
    if mode2 and flags["b"]:
        grass.fatal(_("Can't compute binary rasters in mode 2"))
    if any((beam_rad, diff_rad, refl_rad, glob_rad)) and mode1:
        grass.fatal(_("Can't compute irradiation raster maps in mode 1"))

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

    # here we check all the days
    if not grass.overwrite():
        check_time_map_names(
            beam_rad_basename,
            grass.gisenv()["MAPSET"],
            start_time,
            end_time,
            time_step,
            binary,
            tmpName,
            mode1,
        )
        check_time_map_names(
            diff_rad_basename,
            grass.gisenv()["MAPSET"],
            start_time,
            end_time,
            time_step,
            binary,
            tmpName,
            mode1,
        )
        check_time_map_names(
            refl_rad_basename,
            grass.gisenv()["MAPSET"],
            start_time,
            end_time,
            time_step,
            binary,
            tmpName,
            mode1,
        )
        check_time_map_names(
            glob_rad_basename,
            grass.gisenv()["MAPSET"],
            start_time,
            end_time,
            time_step,
            binary,
            tmpName,
            mode1,
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

    grass.info(_("Running r.sun in a loop..."))
    count = 0
    # Parallel processing
    proc_list = []
    proc_count = 0
    suffixes = []
    suffixes_all = []
    if mode1:
        times = list(frange1(start_time, end_time, time_step))
    else:
        times = list(frange2(start_time, end_time, time_step))
    num_times = len(times)
    core.percent(0, num_times, 1)
    for time in times:
        count += 1
        core.percent(count, num_times, 10)

        coeff_bh_raster = coeff_bh
        if coeff_bh_strds:
            coeff_bh_raster = get_raster_from_strds(
                year, day, time, strds=coeff_bh_strds
            )
        coeff_dh_raster = coeff_dh
        if coeff_dh_strds:
            coeff_dh_raster = get_raster_from_strds(
                year, day, time, strds=coeff_dh_strds
            )

        suffix = "_" + format_time(time)
        proc_list.append(
            Process(
                target=run_r_sun,
                args=(
                    elevation_input,
                    aspect_input,
                    slope_input,
                    day,
                    time,
                    civil_time,
                    linke,
                    linke_value,
                    albedo,
                    albedo_value,
                    coeff_bh_raster,
                    coeff_dh_raster,
                    lat,
                    long_,
                    beam_rad_basename,
                    diff_rad_basename,
                    refl_rad_basename,
                    glob_rad_basename,
                    incidout_basename,
                    suffix,
                    binary,
                    tmpName,
                    None if mode1 else time_step,
                    distance_step,
                    solar_constant,
                    rsun_flags,
                ),
            )
        )

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

    if beam_rad:
        sum_maps(beam_rad, beam_rad_basename, suffixes_all)
        set_color_table([beam_rad])
    if diff_rad:
        sum_maps(diff_rad, diff_rad_basename, suffixes_all)
        set_color_table([diff_rad])
    if refl_rad:
        sum_maps(refl_rad, refl_rad_basename, suffixes_all)
        set_color_table([refl_rad])
    if glob_rad:
        sum_maps(glob_rad, glob_rad_basename, suffixes_all)
        set_color_table([glob_rad])

    if not any(
        [
            beam_rad_basename_user,
            diff_rad_basename_user,
            refl_rad_basename_user,
            glob_rad_basename_user,
        ]
    ):
        return 0

    # cumulative sum
    if flags["c"]:
        copy_tmp = create_tmp_map_name("copy")
        REMOVE.append(copy_tmp)
        for each in (
            beam_rad_basename_user,
            diff_rad_basename_user,
            refl_rad_basename_user,
            glob_rad_basename_user,
        ):
            if each:
                previous = each + suffixes_all[0]
                for suffix in suffixes_all[1:]:
                    new = each + suffix
                    grass.run_command("g.copy", raster=[new, copy_tmp], quiet=True)
                    grass.mapcalc(
                        "{new} = {previous} + {current}".format(
                            new=new, previous=previous, current=copy_tmp
                        ),
                        overwrite=True,
                    )
                    previous = new

    # add to temporal framework
    if temporal:
        core.info(_("Registering created maps into temporal dataset..."))
        import grass.temporal as tgis

        def registerToTemporal(
            basename, suffixes, mapset, start_time, time_step, title, desc
        ):
            maps = ",".join([basename + suf + "@" + mapset for suf in suffixes])
            tgis.open_new_stds(
                basename,
                type="strds",
                temporaltype="absolute",
                title=title,
                descr=desc,
                semantic="mean",
                dbif=None,
                overwrite=grass.overwrite(),
            )
            tgis.register_maps_in_space_time_dataset(
                type="raster",
                name=basename,
                maps=maps,
                start=start_time,
                end=None,
                increment=time_step,
                dbif=None,
                interval=False,
            )

        # Make sure the temporal database exists
        tgis.init()

        mapset = grass.gisenv()["MAPSET"]
        if mode2:
            start_time += 0.5 * time_step
        absolute_time = (
            datetime.datetime(year, 1, 1)
            + datetime.timedelta(days=day - 1)
            + datetime.timedelta(hours=start_time)
        )
        start = absolute_time.strftime("%Y-%m-%d %H:%M:%S")
        step = datetime.timedelta(hours=time_step)
        step = "%d seconds" % step.seconds

        if beam_rad_basename_user:
            registerToTemporal(
                beam_rad_basename_user,
                suffixes_all,
                mapset,
                start,
                step,
                title="Beam irradiance" if mode1 else "Beam irradiation",
                desc="Output beam irradiance raster maps [W.m-2]"
                if mode1
                else "Output beam irradiation raster maps [Wh.m-2]",
            )
        if diff_rad_basename_user:
            registerToTemporal(
                diff_rad_basename_user,
                suffixes_all,
                mapset,
                start,
                step,
                title="Diffuse irradiance" if mode1 else "Diffuse irradiation",
                desc="Output diffuse irradiance raster maps [W.m-2]"
                if mode1
                else "Output diffuse irradiation raster maps [Wh.m-2]",
            )
        if refl_rad_basename_user:
            registerToTemporal(
                refl_rad_basename_user,
                suffixes_all,
                mapset,
                start,
                step,
                title="Reflected irradiance" if mode1 else "Reflected irradiation",
                desc="Output reflected irradiance raster maps [W.m-2]"
                if mode1
                else "Output reflected irradiation raster maps [Wh.m-2]",
            )
        if glob_rad_basename_user:
            registerToTemporal(
                glob_rad_basename_user,
                suffixes_all,
                mapset,
                start,
                step,
                title="Total irradiance" if mode1 else "Total irradiation",
                desc="Output total irradiance raster maps [W.m-2]"
                if mode1
                else "Output total irradiation raster maps [Wh.m-2]",
            )
        if incidout_basename:
            registerToTemporal(
                incidout_basename,
                suffixes_all,
                mapset,
                start,
                step,
                title="Incidence angle",
                desc="Output incidence angle raster maps",
            )

    else:
        absolute_time = datetime.datetime(year, 1, 1) + datetime.timedelta(days=day - 1)
        for i, time in enumerate(times):
            grass_time = format_grass_time(
                absolute_time + datetime.timedelta(hours=time)
            )
            if beam_rad_basename_user:
                set_time_stamp(
                    beam_rad_basename_user + suffixes_all[i], time=grass_time
                )
            if diff_rad_basename_user:
                set_time_stamp(
                    diff_rad_basename_user + suffixes_all[i], time=grass_time
                )
            if refl_rad_basename_user:
                set_time_stamp(
                    refl_rad_basename_user + suffixes_all[i], time=grass_time
                )
            if glob_rad_basename_user:
                set_time_stamp(
                    glob_rad_basename_user + suffixes_all[i], time=grass_time
                )
            if incidout_basename:
                set_time_stamp(incidout_basename + suffixes_all[i], time=grass_time)

    if beam_rad_basename_user:
        maps = [beam_rad_basename_user + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if diff_rad_basename_user:
        maps = [diff_rad_basename_user + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if refl_rad_basename_user:
        maps = [refl_rad_basename_user + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if glob_rad_basename_user:
        maps = [glob_rad_basename_user + suf for suf in suffixes_all]
        set_color_table(maps, binary)
    if incidout_basename:
        maps = [incidout_basename + suf for suf in suffixes_all]
        set_color_table(maps)


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
