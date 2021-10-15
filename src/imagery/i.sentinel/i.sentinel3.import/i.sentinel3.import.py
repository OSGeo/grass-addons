#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      i.sentinel3.import
# AUTHOR(S):   Stefan Blumentrath
# PURPOSE:     Imports Sentinel-3 data downloaded from Copernicus Open Access Hub
#              using i.sentinel.download.
# COPYRIGHT:   (C) 2021 by Stefan Blumentrath, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%Module
#% description: Imports Sentinel-3 satellite data downloaded from Copernicus Open Access Hub using i.sentinel.download.
#% keyword: imagery
#% keyword: satellite
#% keyword: Sentinel
#% keyword: import
#%end

#%option G_OPT_M_DIR
#% key: input
#% description: Name of input directory with downloaded Sentinel-3 data
#% required: yes
#%end

#%option
#% key: product
#% description: Product bands to import (e.g. LST)
#%end

#%option
#% key: ancillary_bands
#% options: LST_uncertainty,biome,fraction,NDVI,elevation_in
#% answer: LST_uncertainty,biome,fraction,NDVI,elevation_in
#% required: no
#% description: Ancillary data bands to import (e.g. LST_uncertainty)
#%end

#%option
#% key: quality_bands
#% options: bayes_in,cloud_in,confidence_in,probability_cloud_dual_in,probability_cloud_single_in
#% answer: bayes_in,cloud_in,confidence_in,probability_cloud_dual_in,probability_cloud_single_in
#% required: no
#% description: Quality flag bands to import (e.g. bayes_in)
#%end

#%option
#% key: basename
#% description: Basename used as prefix for map names
#% required: yes
#%end

#%option
#% key: pattern
#% description: File name pattern to import
#% guisection: Filter
#%end

#%option
#% key: modified_after
#% description: Import only files modified after this date ("YYYY-MM-DD")
#% guisection: Filter
#%end

#%option
#% key: modified_before
#% description: Import only files modified before this date ("YYYY-MM-DD")
#% guisection: Filter
#%end

#%option G_OPT_F_OUTPUT
#% key: register_output
#% description: Name for output file to use with t.register
#% required: no
#%end

#%option G_OPT_M_DIR
#% key: metadata
#% description: Name of directory into which Sentinel metadata json dumps are saved
#% required: no
#%end

#%option
#% key: nprocs
#% description: Number of parallel processes to use during import (default=1)
#% type: integer
#% answer: 1
#% required: no
#%end

#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end

#%flag
#% key: a
#% description: Apply cloud mask before import (can significantly speed up import)
#% guisection: Settings
#%end

#%flag
#% key: c
#% description: Import LST in degree celsius (default is kelvin)
#% guisection: Settings
#%end

#%flag
#% key: p
#% description: Print raster data to be imported and exit
#% guisection: Print
#%end

#%flag
#% key: j
#% description: Write metadata json for each band to LOCATION/MAPSET/cell_misc/BAND/description.json
#% guisection: Print
#%end

#%rules
#% excludes: -p,register_output
#%end

import atexit
from datetime import datetime
from itertools import chain
import os
import sys
from pathlib import Path
import json
from zipfile import ZipFile
from multiprocessing import Pool

import grass.script as gscript
from grass.pygrass.modules import Module, MultiModule
from grass.temporal.datetime_math import (
    datetime_to_grass_datetime_string as grass_timestamp,
)


TMPFILE = None


def cleanup():
    # remove temporary maps
    if TMPFILE is not None:
        gscript.try_remove(TMPFILE)


def np_as_scalar(var):
    if type(var).__module__ == np.__name__:
        if var.size > 1:
            return str(var)
        return var.item()
    else:
        return var


def filter(input_dir, pattern, modified_after, modified_before):
    # Filter files according to pattern (with L2 LST)
    if not pattern:
        pattern = "S3*SL_2_LST*.zip"

    s3_files = []
    s3_files = list(input_dir.glob(pattern))

    if len(s3_files) > 0 and (
        modified_after is not None or modified_before is not None
    ):
        modified_after = modified_after if modified_after is not None else datetime.min
        modified_before = (
            modified_before if modified_before is not None else datetime.now()
        )
        s3_files = [
            s3_file
            for s3_file in s3_files
            if modified_after
            < datetime.fromtimestamp(s3_file.stat().st_mtime)
            < modified_before
        ]

    if len(s3_files) < 1:
        gscript.fatal(
            _("Nothing found to import. Please check input and pattern options.")
        )

    return s3_files


def write_metadata(json_dict, metadatajson):
    gscript.verbose(_("Writing metadata to maps..."))
    with open(metadatajson, "w") as outfile:
        json.dump(json_dict, outfile)


def write_register_file(filename, register_input):
    gscript.verbose(_("Writing register file <{}>...").format(filename))
    with open(filename, "w") as fd:
        fd.write("\n".join(chain(*register_input)))


def convert_units(np_column, from_u, to_u):
    """Converts a numpy column from one unit to
    another, convertibility needs to be checked beforehand"""

    try:
        from cf_units import Unit
    except ImportError:
        gscript.fatal(
            _(
                "Could not import cf_units. Please install it with:\n"
                "'pip install cf_units'!"
            )
        )

    try:
        converted_col = Unit(from_u).convert(np_column, Unit(to_u))
    except ValueError:
        gscript.fatal(
            _(
                "Warning: Could not convert units from {from_u} to {to_u}.".format(
                    from_u=from_u, to_u=to_u
                )
            )
        )
        converted_col = np_column

    return converted_col


def transform_coordinates(coordinates):
    """Tranforms a numy array with coordinates to
    projection of the current location"""

    # Create source coordinate reference
    s_srs = osr.SpatialReference()
    s_srs.ImportFromEPSG(4326)

    # Create target coordinate reference
    t_srs = osr.SpatialReference()
    t_srs.ImportFromWkt(gscript.read_command("g.proj", flags="fw"))

    # Initialize osr transformation
    transform = osr.CoordinateTransformation(s_srs, t_srs)

    return (
        coordinates[:, [1, 0]]
        if s_srs.IsSame(t_srs)
        else np.array(transform.TransformPoints(coordinates))[:, [0, 1]]
    )


def adjust_region_env(reg, coords):
    """Get region bounding box of intersecting area with
    coordinates aligned to the current region"""
    coords_min = np.min(coords, axis=0)
    coords_max = np.max(coords, axis=0)

    diff = coords_max[0:2] / np.array([float(reg["ewres"]), float(reg["nsres"])])
    coords_max_aligned = diff.astype(np.int) * np.array(
        [float(reg["ewres"]), float(reg["nsres"])]
    )

    diff = coords_min[0:2] / np.array([float(reg["ewres"]), float(reg["nsres"])])
    coords_min_aligned = diff.astype(np.int) * np.array(
        [float(reg["ewres"]), float(reg["nsres"])]
    )

    new_bounds = {}
    new_bounds["e"], new_bounds["n"] = tuple(
        np.min(
            np.vstack(
                (coords_max_aligned, np.array([reg["e"], reg["n"]]).astype(np.float))
            ),
            axis=0,
        ).astype(np.str)
    )
    new_bounds["w"], new_bounds["s"] = tuple(
        np.max(
            np.vstack(
                (coords_min_aligned, np.array([reg["w"], reg["s"]]).astype(np.float))
            ),
            axis=0,
        ).astype(np.str)
    )

    if float(new_bounds["s"]) >= float(new_bounds["n"]) or float(
        new_bounds["w"]
    ) >= float(new_bounds["e"]):
        return None

    compute_env = os.environ.copy()
    compute_env["GRASS_region"] = gscript.region_env(**new_bounds)

    return compute_env


def import_s3(s3_file, kwargs):
    """Import Sentinel-3 netCDF4 data"""

    # Unpack dictionary variables
    rmap = kwargs["basename"]
    TMPFILE = kwargs["tmpfile"]
    reg_bounds = kwargs["reg_bounds"]
    current_reg = kwargs["current_reg"]
    mod_flags = kwargs["mod_flags"]
    bands = kwargs["bands"]
    product_type = kwargs["product_type"]
    has_bandref = kwargs["has_bandref"]
    json_standard_folder = kwargs["json_standard_folder"]
    overwrite = kwargs["overwrite"]

    # Define Sentinel 3 SL_2_LST__ format structure
    s3_sl_2_lst_structure = {
        "S3SL2LST": {
            "LST_in.nc": {"LST", "LST_uncertainty"},
            "flags_in.nc": {
                "bayes_in",
                "cloud_in",
                "confidence_in",
                "probability_cloud_dual_in",
                "probability_cloud_single_in",
            },
            "geodetic_in.nc": {"latitude_in", "longitude_in", "elevation_in"},
            "LST_ancillary_ds.nc": {"biome", "fraction", "NDVI"},
        }
    }

    # GRASS map precision
    grass_rmap_type = {
        "float32": "FCELL",
        "uint16": "CELL",
        "uint8": "CELL",
        "float64": "DCELL",
    }

    # Add required band to requested bands
    bands = bands.union({"latitude_in", "longitude_in", "LST"})

    tmp_ascii = TMPFILE.joinpath(s3_file.stem + ".txt")

    # Setup container dictionary
    nc_bands = {}

    # Setup module container
    module_queue = {}

    register_output = []

    # Open S3 file
    with ZipFile(s3_file) as zf:
        members = zf.namelist()
        root = Path(members[0])
        val_col = 0
        fmt = "%.5f,%.5f"
        # Print only product structure
        if mod_flags["p"]:
            zf.extractall(path=TMPFILE)
            product_info = []
            for nc_file in members:
                if nc_file.endswith(".nc"):
                    nc_file_path = TMPFILE.joinpath(nc_file)
                    nc_ds = Dataset(nc_file_path)
                    file_info = [
                        root,
                        nc_file_path.name,
                        nc_ds.title,
                        nc_ds.start_time,
                        nc_ds.creation_time,
                    ]
                    for band in nc_ds.variables.keys():
                        band_attrs = nc_ds[band].ncattrs()
                        var_info = [
                            band,
                            nc_ds[band].shape,
                            nc_ds[band]["title"] if "title" in band_attrs else band,
                            nc_ds[band].standard_name
                            if "standard_name" in band_attrs
                            else band,
                            nc_ds[band].long_name
                            if "long_name" in band_attrs
                            else band,
                        ]
                    product_info.append("|".join(map(str, file_info + var_info)))
            return product_info

        for nc_file, available_bands in s3_sl_2_lst_structure[product_type].items():
            # Collect input data in container dict
            requested_bands = available_bands.intersection(bands)
            if requested_bands:
                member = str(root.joinpath(nc_file))
                if member not in members:
                    gscript.fatal(
                        _(
                            "{s3_file} does not contain a container {container} with band {band}".format(
                                s3_file=s3_file,
                                container=nc_file,
                                band=", ".join(requested_bands),
                            )
                        )
                    )
                nc_file_path = zf.extract(member, path=TMPFILE)
                nc_file_open = Dataset(nc_file_path)
                file_attrs = nc_file_open.ncattrs()
                start_time = parse_timestr(nc_file_open.start_time)
                end_time = parse_timestr(nc_file_open.stop_time)
                file_description = ""
                for attr in [
                    "absolute_orbit_number",
                    "track_offset",
                    "start_offset",
                    "institution",
                    "references",
                    "source",
                    "contact",
                    "comment",
                ]:
                    file_description += "{attr}: {val}\n".format(
                        attr=attr, val=nc_file_open.getncattr(attr)
                    )
                file_description += "resolution: {}".format(
                    "x".join(nc_file_open.resolution.split(" ")[1:3])
                )

                for band in requested_bands:
                    if "itude_in" not in band:
                        val_col += 1
                    if member not in members:
                        gscript.fatal(
                            _(
                                "{s3_file} does not contain a container {container} with band {band}".format(
                                    s3_file=s3_file,
                                    container=nc_file,
                                    band=", ".join(requested_bands),
                                )
                            )
                        )

                    # metadata[band] = MultiModule(module_list=[])
                    nc_bands[band] = nc_file_open[band]
                    band_attrs = nc_bands[band].ncattrs()
                    # Define variable name
                    varname_short = (
                        nc_bands[band].standard_name
                        if "standard_name" in band_attrs
                        else band.rstrip("_in")
                    )
                    datatype = str(nc_bands[band][:].dtype)
                    # Define map name
                    mapname = "{rmap}_{var}_{time}".format(
                        rmap=rmap,
                        var=varname_short,
                        time=start_time.strftime("%Y%m%dT%H%M%S"),
                    )
                    # Define unit
                    unit = nc_bands[band].units if "units" in band_attrs else None
                    unit = (
                        "degree_celsius"
                        if band.startswith("LST") and mod_flags["c"]
                        else unit
                    )
                    # Define datatype and import method
                    if datatype in ["uint8", "uint16"]:
                        method = "max"  # Unfortunately there is no "mode" in r.in.xyz
                        fmt += ",%i" if "itude_in" not in band else ""
                    else:
                        method = "mean"
                        fmt += ",%.5f" if "itude_in" not in band else ""
                    # Compile description
                    description = file_description
                    if "valid_max" in band_attrs:
                        if "add_offset" in band_attrs:
                            min_val = (
                                nc_bands[band].valid_min * nc_bands[band].scale_factor
                                + nc_bands[band].add_offset
                            )
                            max_val = (
                                nc_bands[band].valid_max * nc_bands[band].scale_factor
                                + nc_bands[band].add_offset
                            )
                        description += (
                            "\n\nvalid_min: {min_val}\nvalid_max: {max_val}".format(
                                min_val=min_val, max_val=max_val
                            )
                        )
                    # Define valid input range
                    if "_FillValue" in band_attrs:
                        fill_val = (
                            nc_bands[band]._FillValue
                            if "_FillValue" in band_attrs
                            else None
                        )
                        if fill_val > 0:
                            zrange = [fill_val - 1, np.min(nc_bands[band])]
                        else:
                            zrange = [fill_val + 1, np.max(nc_bands[band])]
                    elif "flag_values" in band_attrs:
                        zrange = [
                            min(nc_bands["biome"].flag_values),
                            max(nc_bands["biome"].flag_values),
                        ]
                    else:
                        zrange = None

                    support_kwargs = {
                        "map": mapname,
                        "title": "{band_title} from {file_title}".format(
                            band_title=nc_bands[band].long_name
                            if "long_name" in band_attrs
                            else band.rstrip("_in"),
                            file_title=nc_file_open.title,
                        ),
                        "history": nc_file_open.history,
                        "units": unit,
                        "source1": nc_file_open.product_name,
                        "source2": None,
                        "description": description,
                    }
                    if has_bandref:
                        support_kwargs["bandref"] = "S3_{}".format(varname_short)

                    # Write metadata json if requested
                    if json_standard_folder:
                        write_metadata(
                            {
                                **{
                                    a: np_as_scalar(nc_file_open.getncattr(a))
                                    for a in nc_file_open.ncattrs()
                                },
                                **{"variable": band},
                                **{
                                    a: np_as_scalar(nc_file_open[band].getncattr(a))
                                    for a in nc_file_open[band].ncattrs()
                                },
                            },
                            json_standard_folder.joinpath(mapname + ".json"),
                        )

                    # Setup import modules
                    modules = [
                        Module(
                            "r.in.xyz",
                            input=str(tmp_ascii),
                            output=mapname,
                            method=method,
                            separator=",",
                            x=1,
                            y=2,
                            # Arry contains a column z at position 3 (with all 0)
                            # after coordinate transformation
                            z=2 + val_col,
                            flags="i",
                            type=grass_rmap_type[datatype],
                            zrange=zrange,
                            percent=100,
                            run_=False,
                            overwrite=overwrite,
                        ),
                        Module(
                            "r.support",
                            **support_kwargs,
                            run_=False,
                        ),
                        Module(
                            "r.timestamp",
                            map=mapname,
                            date=grass_timestamp(start_time),
                            run_=False,
                        ),
                    ]
                    # Define categories for flag datasets
                    if "flag_masks" in band_attrs:
                        rules = "\n".join(
                            [
                                ":".join([str(nc_bands[band].flag_masks[idx]), label])
                                for idx, label in enumerate(
                                    nc_bands[band].flag_meanings.split(" ")
                                )
                            ]
                        )
                        modules.append(
                            Module(
                                "r.category",
                                map=mapname,
                                rules="-",
                                stdin_=rules,
                                separator=":",
                                run_=False,
                            )
                        )
                    module_queue[band] = modules
                    # Compile output for t.register
                    if "itude_in" not in band:
                        register_list = [
                            mapname,
                            start_time.isoformat(),
                            end_time.isoformat(),
                        ]
                        if has_bandref:
                            register_list.append(f"S3_{varname_short}")
                        register_output.append("|".join(register_list))

        # geo_tx = Dataset("./geodetic_tx.nc")
        # geom_tn = Dataset("./geometry_tn.nc")
        # cart_in = Dataset("./cartesian_in.nc")
        # cart_tx = Dataset("./cartesian_tx.nc")
        # indices_in = Dataset("./indices_in.nc")
        # met_tx = Dataset("./met_tx.nc")
        # time_in = Dataset("./time_in.nc")

    # Create initial mask
    mask = nc_bands["LST"][:].mask

    # Mask to region
    mask = np.ma.mask_or(
        mask,
        np.ma.masked_outside(
            nc_bands["longitude_in"],
            float(reg_bounds["ll_w"]),
            float(reg_bounds["ll_e"]),
        ).mask,
    )
    mask = np.ma.mask_or(
        mask,
        np.ma.masked_outside(
            nc_bands["latitude_in"],
            float(reg_bounds["ll_s"]),
            float(reg_bounds["ll_n"]),
        ).mask,
    )

    # Mask clouds if requested
    if mod_flags["a"]:
        mask = np.ma.mask_or(mask, np.ma.masked_equal(nc_bands["bayes_in"], 2).mask)
        mask = np.ma.mask_or(mask, np.ma.masked_greater(nc_bands["cloud_in"], 0).mask)

    # Extract grid coordinates
    lon = np.ma.masked_where(mask, nc_bands["longitude_in"][:]).compressed()
    lat = np.ma.masked_where(mask, nc_bands["latitude_in"][:]).compressed()

    # Project coordinates
    coords = transform_coordinates(np.dstack((lat, lon)).reshape(lat.shape[0], 2))

    env = adjust_region_env(current_reg, coords)
    if not env:
        gscript.warning(
            _(
                "No data to import within current computational region for {}".format(
                    s3_file
                )
            )
        )
        return

    # Fetch, mask and stack requested bands
    np_output = coords
    for band in nc_bands:
        if "itude_in" in band:
            continue
        add_array = nc_bands[band][:]
        if np.ma.is_masked(add_array):
            add_array = add_array.filled()
        if (band == "LST" or band == "LST_uncertainty") and mod_flags["c"]:
            add_array = convert_units(add_array, "K", "degree_celsius")

        np_output = np.hstack(
            (np_output, np.ma.masked_where(mask, add_array).compressed()[:, None])
        )

    # Write to temporary file
    np.savetxt(tmp_ascii, np_output, delimiter=",", fmt=fmt)

    # Run import routine
    for band in nc_bands:
        if "itude_in" in band:
            continue
        module_queue[band][0].env_ = env
        MultiModule(module_queue[band]).run()

    return register_output


def main():

    # check if input dir exists
    input_dir = Path(options["input"])
    if not input_dir.exists():
        gscript.fatal(_("Input directory <{}> does not exist").format(input_dir))

    if options["modified_after"]:
        try:
            modified_after = parse_timestr(options["modified_after"])
        except ValueError:
            gscript.fatal(_("Cannot parse input in modified_after option"))
    else:
        modified_after = None

    if options["modified_before"]:
        try:
            modified_before = parse_timestr(options["modified_before"])
        except ValueError:
            gscript.fatal(_("Cannot parse input in modified_before option"))
    else:
        modified_before = None

    # Filter files to import
    s3_files = filter(input_dir, options["pattern"], modified_after, modified_before)

    overwrite = gscript.overwrite()

    nprocs = int(options["nprocs"])

    basename = options["basename"]

    import_bands = set(options["ancillary_bands"].split(",")).union(
        set(options["quality_bands"].split(","))
    )

    # Create tempdir
    global TMPFILE
    TMPFILE = Path(gscript.tempfile(create=False))
    if not TMPFILE.exists():
        TMPFILE.mkdir()

    # Get region bounds
    reg_bounds = gscript.parse_command("g.region", flags="gb", quiet=True)
    current_reg = gscript.parse_command("g.region", flags="g")
    has_band_ref = float(gscript.version()["version"][0:3]) >= 7.9

    # Collect variables for import
    import_dict = {
        "basename": basename,
        "tmpfile": TMPFILE,
        "reg_bounds": dict(reg_bounds),
        "current_reg": dict(current_reg),
        "mod_flags": flags,
        "bands": import_bands,
        "has_bandref": has_band_ref,
        "product_type": "S3SL2LST",
        "overwrite": overwrite,
    }
    if flags["j"]:
        env = gscript.gisenv()
        json_standard_folder = Path(env["GISDBASE"]).joinpath(
            env["LOCATION_NAME"], env["MAPSET"], "cell_misc"
        )
        if not json_standard_folder.exists():
            json_standard_folder.mkdirs()
        import_dict["json_standard_folder"] = json_standard_folder
    else:
        import_dict["json_standard_folder"] = None

    if nprocs == 1:
        import_result = [
            import_s3(
                f,
                import_dict,
            )
            for f in s3_files
        ]
    else:
        pool = Pool(nprocs)
        import_result = pool.starmap(
            import_s3,
            [
                (
                    f,
                    import_dict,
                )
                for f in s3_files
            ],
        )
        pool.close()
        pool.join()

    if flags["p"]:
        print(
            "|".join(
                [
                    "product_file_name",
                    "nc_file_name",
                    "nc_file_title",
                    "nc_file_start_time",
                    "nc_file_creation_time",
                    "band",
                    "band_shape",
                    "band_title",
                    "band_standard_name",
                    "band_long_name",
                ]
            )
        )
        print("\n".join(chain(*import_result)))
        return 0

    if options["register_output"]:
        # Write t.register file if requested
        write_register_file(options["register_output"], import_result)

    return 0


if __name__ == "__main__":
    options, flags = gscript.parser()
    # Lazy imports
    try:
        from dateutil.parser import isoparse as parse_timestr
    except ImportError:
        print(
            "Could not import dateutil. Please install it with:\n"
            "'pip install dateutil'!"
        )
    try:
        from osgeo import osr
    except ImportError:
        print("Could not import gdal. Please install it with:\n" "'pip install GDAL'!")

    try:
        from netCDF4 import Dataset
    except ImportError:
        print(
            "Could not import netCDF4. Please install it with:\n"
            "'pip install netcdf4'!"
        )

    try:
        import numpy as np
    except ImportError:
        print(
            "Could not import numpy. Please install it with:\n" "'pip install numpy'!"
        )

    atexit.register(cleanup)
    sys.exit(main())
