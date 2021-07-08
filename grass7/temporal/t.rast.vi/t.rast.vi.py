#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.rast.vi
#
# AUTHOR(S):    Luca Delucchi <luca.delucchi fmach.it>
#
# PURPOSE:      Calculate vegetation indices for temporal datasets.
#
# COPYRIGHT:	(C) 2021 by luca delucchi and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################

#%Module
#% description: Calculate vegetation indices for temporal datasets
#% keyword: temporal
#% keyword: vegetation
#% keyword: raster
#% keyword: time
#%end

#%option
#% key: red
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time raster dataset with red band
#% gisprompt: old,strds,strds
#%end

#%option
#% key: green
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time raster dataset with green band
#% gisprompt: old,strds,strds
#%end

#%option
#% key: blue
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time raster dataset with blue band
#% gisprompt: old,strds,strds
#%end

#%option
#% key: nir
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time raster dataset with nir band
#% gisprompt: old,strds,strds
#%end

#%option
#% key: band5
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time raster dataset with 5th channel surface reflectance band
#% gisprompt: old,strds,strds
#%end

#%option
#% key: band7
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time raster dataset with 7th channel surface reflectance band
#% gisprompt: old,strds,strds
#%end

#%option
#% key: output
#% type: string
#% required: yes
#% multiple: no
#% key_desc: name
#% description: Name of the output space time raster dataset
#% gisprompt: new,strds,strds
#%end

#%option
#% key: prefix
#% type: string
#% required: no
#% multiple: no
#% key_desc: name
#% description: Prefix of the output raster names within the space time raster dataset
#% gisprompt: new,strds,strds
#%end

#%option
#% key: clouds
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time dataset with clouds
#% gisprompt: old,strds,strds
#%end

#%option
#% key: shadows
#% type: string
#% required: no
#% multiple: no
#% description: Name of the input space time dataset with shadow
#% gisprompt: old,strds,strds
#%end

#%option
#% key: viname
#% type: string
#% required: no
#% multiple: no
#% description: Type of vegetation index
#% options: arvi, dvi, evi, evi2, gvi, gari, gemi, ipvi, msavi, msavi2, ndvi, ndwi, pvi, savi, sr, vari, wdvi
#% answer: ndvi
#%end

#%option G_OPT_T_WHERE
#%end

#%option
#% key: soil_line_slope
#% type: double
#% required: no
#% multiple: no
#% description: Value of the slope of the soil line (MSAVI only)
#% guisection: MSAVI settings
#%end

#%option
#% key: soil_line_intercept
#% type: double
#% required: no
#% multiple: no
#% description: Value of the intercept of the soil line (MSAVI only)
#% guisection: MSAVI settings
#%end

#%option
#% key: soil_noise_reduction
#% type: double
#% required: no
#% multiple: no
#% description: Value of the factor of reduction of soil noise (MSAVI only)
#% guisection: MSAVI settings
#%end


#%option
#% key: nprocs
#% type: integer
#% required: no
#% multiple: no
#% label: Number of parallel processes to run
#% answer: 1
#%end

#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% label: Maximum memory to be used if vector to raster operation is needed (in MB)
#% answer: 300
#%end

import sys
import copy
import grass.script as gscript
import grass.temporal as tgis
import grass.pygrass.modules as pymod


def check_temporal_exist(name, stdtype="strds"):
    if not name:
        return None
    try:
        sp = tgis.open_old_stds(name, stdtype, dbif)
    except:
        sp = None
    return sp


def check_map_numbers(where, **kwargs):
    numrast = None
    for kw in kwargs:
        sp = kwargs[kw]
        maps = sp.get_registered_maps_as_objects(where, "start_time", None)
        if maps is None:
            gscript.fatal(
                _(
                    "Space time raster dataset {st} seems to be "
                    "empty".format(st=sp.get_name())
                )
            )
        else:
            if numrast is None:
                numrast = len(maps)
                name = sp.get_name()
            else:
                if numrast != len(maps):
                    grass.warning(
                        _(
                            "The number of raster maps in {} strds and {} strds differs.".format(
                                name, sp.get_name()
                            )
                        )
                    )
    return 0


def main():
    global dbif

    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    red = check_temporal_exist(options["red"])
    green = check_temporal_exist(options["green"])
    blue = check_temporal_exist(options["blue"])
    nir = check_temporal_exist(options["nir"])
    band5 = check_temporal_exist(options["band5"])
    band7 = check_temporal_exist(options["band7"])
    clouds = check_temporal_exist(options["clouds"])
    viname = options["viname"]
    if not clouds:
        clouds = check_temporal_exist(options["clouds"], "stvds")
    shadows = check_temporal_exist(options["shadows"])
    if not shadows:
        shadows = check_temporal_exist(options["shadows"], "stvds")
    strdsout = check_temporal_exist(options["output"])

    nprocs = int(options["nprocs"])
    where = options["where"]
    sl_slope = options["soil_line_slope"]
    sl_int = options["soil_line_intercept"]
    sl_red = options["soil_noise_reduction"]
    memory = int(options["memory"])
    overwrite = gscript.overwrite()

    list_strds = {}
    if viname == "sr" and (not red or not nir):
        gscript.fatal(_("sr index requires red and nir strds"))
    elif viname == "sr":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "ndvi" and (not red or not nir):
        gscript.fatal(_("ndvi index requires red and nir maps"))
    elif viname == "ndvi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "ndwi" and (not green or not nir):
        gscript.fatal(_("ndwi index requires green and nir maps"))
    elif viname == "ndwi":
        check_map_numbers(where, green=green, nir=nir)
        list_strds["green"] = green
        list_strds["nir"] = nir

    if viname == "ipvi" and (not red or not nir):
        gscript.fatal(_("ipvi index requires red and nir maps"))
    elif viname == "ipvi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "dvi" and (not red or not nir):
        gscript.fatal(_("dvi index requires red and nir maps"))
    elif viname == "dvi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "pvi" and (not red or not nir):
        gscript.fatal(_("pvi index requires red and nir maps"))
    elif viname == "pvi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "wdvi" and (not red or not nir):
        gscript.fatal(_("wdvi index requires red and nir maps"))
    elif viname == "wdvi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "savi" and (not red or not nir):
        gscript.fatal(_("savi index requires red and nir maps"))
    elif viname == "savi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "msavi" and (
        not red or not nir or not sl_slope or not sl_int or not sl_red
    ):
        gscript.fatal(
            _(
                "msavi index requires red and nir maps, and 3 parameters related to soil line"
            )
        )
    elif viname == "msavi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "msavi2" and (not red or not nir):
        gscript.fatal(_("msavi2 index requires red and nir maps"))
    elif viname == "msavi2":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "gemi" and (not red or not nir):
        gscript.fatal(_("gemi index requires red and nir maps"))
    elif viname == "gemi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "arvi" and (not red or not nir or not blue):
        gscript.fatal(_("arvi index requires blue, red and nir maps"))
    elif viname == "arvi":
        check_map_numbers(where, red=red, nir=nir, blue=blue)
        list_strds["red"] = red
        list_strds["nir"] = nir
        list_strds["blue"] = blue

    if viname == "evi" and (not red or not nir or not blue):
        gscript.fatal(_("evi index requires blue, red and nir maps"))
    elif viname == "evi":
        check_map_numbers(where, red=red, nir=nir, blue=blue)
        list_strds["red"] = red
        list_strds["nir"] = nir
        list_strds["blue"] = blue

    if viname == "evi2" and (not red or not nir):
        gscript.fatal(_("evi2 index requires red and nir maps"))
    elif viname == "evi2":
        check_map_numbers(where, red=red, nir=nir)
        list_strds["red"] = red
        list_strds["nir"] = nir

    if viname == "vari" and (not red or not green or not blue):
        gscript.fatal(_("vari index requires blue, green and red maps"))
    elif viname == "vari":
        check_map_numbers(where, red=red, green=green, blue=blue)
        list_strds["red"] = red
        list_strds["green"] = green
        list_strds["blue"] = blue

    if viname == "gari" and (not red or not nir or not blue or not green):
        gscript.fatal(_("gari index requires blue, green, red and nir maps"))
    elif viname == "gari":
        check_map_numbers(where, red=red, nir=nir, green=green, blue=blue)
        list_strds.extend([red, green, blue, nir])
        list_strds["red"] = red
        list_strds["nir"] = nir
        list_strds["blue"] = blue
        list_strds["green"] = green

    if viname == "gvi" and (
        not red or not nir or not blue or not green or not band5 or not band7
    ):
        gscript.fatal(
            _("gvi index requires blue, green, red, nir, chan5 and chan7 maps")
        )
    elif viname == "gvi":
        check_map_numbers(where, red=red, nir=nir)
        list_strds.extend([red, green, blue, nir, band5, band7])
        list_strds["red"] = red
        list_strds["nir"] = nir
        list_strds["blue"] = blue
        list_strds["green"] = green
        list_strds["band5"] = band5
        list_strds["band7"] = band7

    if viname == "ndwi":
        from_std = green
    else:
        from_std = red
    maps = from_std.get_registered_maps_as_objects(where, "start_time", None)

    if not strdsout:
        strdsout = tgis.check_new_stds(
            options["output"], "strds", dbif=dbif, overwrite=False
        )
        ttype, stype, title, descr = from_std.get_initial_values()
        title = "{vi} from {se}".format(vi=viname, se=from_std.get_name())
        descr = "{vi} from {se}".format(vi=viname, se=from_std.get_name())
        if where:
            descr += " for {wh}".format(wh=where.replace("'", ""))
        print(title, descr)
        strdsout = tgis.open_new_stds(
            options["output"], "strds", ttype, title, descr, stype, dbif, overwrite
        )

    times = []
    for ma in maps:
        if ma.get_temporal_type() == "absolute":
            times.append(ma.get_absolute_time())
        else:
            times.append(ma.get_relative_time())

    process_queue = pymod.ParallelModuleQueue(int(nprocs))
    vtorast = pymod.Module("v.to.rast", memory=memory, quiet=True, run_=False)
    vtorast.inputs.use = "val"
    ivi = pymod.Module("i.vi", quiet=True, run_=False)
    ivi.inputs.viname = viname
    outlist = []

    for ti in times:
        if ti[1]:
            mywhere = "start_time >= '{}' AND start_time <= '{}'".format(ti[0], ti[1])
        else:
            mywhere = "start_time = '{}'".format(ti[0])
        rasters = {}
        rasters_cloud = {}
        rasters_shadow = {}
        for k, strds in list_strds.items():
            rast = strds.get_registered_maps_as_objects(mywhere, "start_time", None)
            rasters[k] = rast
        cmd_list = []
        # control if cloud and/or shadow exists as raster or vector
        cloud_exists = False
        shadow_exists = False
        extent = rast[0].get_temporal_extent()
        clean = []
        if clouds:
            maps = clouds.get_registered_maps_as_objects(mywhere, "start_time", None)
            if len(maps) == 0:
                gscript.warning(_("No clouds map for {}").format(ti[0]))
            else:
                cloud_exists = True
                if len(maps) > 1:
                    gscript.warning(_("To many clouds maps, only first will be used"))
                if clouds.get_type() == "stvds":
                    cloud_map = "cloud_{}".format(ti[0].strftime("%Y_%m_%d_%H_%M"))

                    vtocloud = copy.deepcopy(vtorast)
                    vtocloud.inputs.input = maps[0].get_id()
                    vtocloud.outputs.output = cloud_map
                    cmd_list.append(vtocloud)
                    clean.append(cloud_map)
                elif clouds.get_type() == "strds":
                    cloud_map = maps[0].get_id()
                for k, rast in rasters.items():
                    out = "{}_cloud".format(rast[0].get_name())
                    rasters_cloud[k] = out
                    expression = "{} = if( isnull({}), {}, null() )".format(
                        out, cloud_map, rast[0].get_name()
                    )
                    cloudmapcalc = pymod.Module(
                        "r.mapcalc", expression=expression, run_=False, quiet=True
                    )
                    cmd_list.append(cloudmapcalc)
                    clean.append(out)
        if shadows:
            maps = shadows.get_registered_maps_as_objects(mywhere, "start_time", None)
            if len(maps) == 0:
                gscript.warning(_("No shadow map for {}").format(ti[0]))
            else:
                shadow_exists = True
                if len(maps) > 1:
                    gscript.warning(_("To many shadows maps, only first will be used"))
                if shadows.get_type() == "stvds":
                    shadow_map = "cloud_{}".format(ti[0].strftime("%Y_%m_%d_%H_%M"))
                    vtoshadow = copy.deepcopy(vtorast)
                    vtoshadow.inputs.input = maps[0].get_name()
                    vtoshadow.outputs.output = shadow_map
                    cmd_list.append(vtoshadow)
                    clean.append(shadow_map)
                elif shadows.get_type() == "strds":
                    shadow_map = maps[0].get_id()
                if cloud_exists:
                    inrasters = rasters_cloud
                else:
                    inrasters = rasters
                for k, rast in inrasters.items():
                    out = "{}_cloud".format(rast[0].get_name())
                    rasters_shadow["k"] = out
                    expression = "{} = if( isnull({}), {}, null() )".format(
                        out, shadow_map, rast[0].get_name()
                    )
                    shadowmapcalc = pymod.Module(
                        "r.mapcalc", expression=expression, run_=False
                    )
                    cmd_list.append(shadowmapcalc)
                    clean.append(out)
        if not cloud_exists and not shadow_exists:
            inputs = rasters
        elif cloud_exists and not shadow_exists:
            inputs = rasters_cloud
        elif cloud_exists and shadow_exists:
            inputs = rasters_shadow
        thisivi = copy.deepcopy(ivi)
        for k, rast in inputs.items():
            if type(rast) == str:
                thisivi.inputs[k].value = rast
            else:
                if len(rast) > 1:
                    gscript.warning(_("To many map as input, only first will be used"))
                thisivi.inputs[k].value = rast[0].get_name()
        if options["prefix"]:
            out = "{pre}_{ti}_{vi}".format(
                pre=options["prefix"], ti=ti[0].strftime("%Y_%m_%d_%H_%M"), vi=viname
            )
        else:
            out = "{ti}_{vi}".format(ti=ti[0].strftime("%Y_%m_%d_%H_%M"), vi=viname)
        thisivi.outputs.output = out
        cmd_list.append(thisivi)
        new_map = tgis.open_new_map_dataset(
            out,
            None,
            type="raster",
            temporal_extent=extent,
            overwrite=overwrite,
            dbif=dbif,
        )
        outlist.append(new_map)
        if len(clean) > 0:
            gremove = pymod.Module("g.remove", run_=False)
            gremove(type="raster", name=",".join(clean), quiet=True, flags="f")
            cmd_list.append(gremove)
        timemodule = pymod.MultiModule(cmd_list)
        timemodule.run()
    #     process_queue.put(timemodule)
    # process_queue.wait()
    # proc_list = process_queue.get_finished_modules()

    # # Check return status of all finished modules
    # error = 0
    # for proc in proc_list:
    #     if proc.returncode != 0:
    #         gscript.error(
    #             _("Error running module: %\n    stderr: %s")
    #             % (proc.get_bash(), proc.outputs.stderr)
    #         )
    #         error += 1

    # if error > 0:
    #     gscript.fatal(_("Error running modules."))
    num_maps = len(outlist)
    # collect empty maps to remove them
    empty_maps = []

    # Register the maps in the database
    count = 0
    for mapp in outlist:
        count += 1

        if count % 10 == 0:
            gscript.percent(count, num_maps, 1)

        # Do not register empty maps
        mapp.load()
        if mapp.metadata.get_min() is None and mapp.metadata.get_max() is None:
            empty_maps.append(mapp)
            continue

        # Insert map in temporal database
        mapp.insert(dbif)
        strdsout.register_map(mapp, dbif)

    # Update the spatio-temporal extent and the metadata table entries
    strdsout.update_from_registered_maps(dbif)
    gscript.percent(1, 1, 1)
    dbif.close()


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
