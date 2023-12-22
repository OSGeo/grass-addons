#!/usr/bin/env python3

"""
 MODULE:       t.rast.import.netcdf
 AUTHOR(S):    Stefan Blumentrath
 PURPOSE:      Import netCDF files that adhere to the CF convention as a
               Space Time Raster Dataset (STRDS)
 COPYRIGHT:    (C) 2023 by stefan.blumentrath, and the GRASS Development Team

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

"""

# %module
# % description: Import netCDF files that adhere to the CF convention as STRDS.
# % keyword: temporal
# % keyword: import
# % keyword: raster
# % keyword: time
# % keyword: netcdf
# %end

# %flag
# % key: a
# % description: Append to STRDS
# % guisection: Settings
# %end

# %flag
# % key: r
# % description: Import only within current region
# % guisection: Filter
# %end

# %flag
# % key: l
# % description: Link the raster files using r.external
# % guisection: Settings
# %end

# %flag
# % key: f
# % description: Link the raster files in a fast way, without reading metadata using r.external
# % guisection: Settings
# %end

# %flag
# % key: e
# % description: Extend location extents based on new dataset
# % guisection: Settings
# %end

# %flag
# % key: o
# % label: Override projection check (use current location's projection)
# % description: Assume that the dataset has same projection as the current location
# % guisection: Settings
# %end

# %option G_OPT_F_INPUT
# % key: input
# % type: string
# % required: yes
# % multiple: no
# % key_desc: Input file(s) ("-" = stdin)
# % description: URL or name of input netcdf-file ("-" = stdin)
# %end

# %option G_OPT_F_INPUT
# % key: semantic_labels
# % type: string
# % required: no
# % multiple: no
# % key_desc: Input file with configuration for semantic labels ("-" = stdin)
# % description: File with mapping of variables or subdatasets to semantic labels
# % guisection: Settings
# %end

# %option G_OPT_STRDS_OUTPUT
# % required: no
# % multiple: no
# % description: Name of the output space time raster dataset
# %end

# %option
# % key: end_time
# % label: Latest timestamp of temporal extent to include in the output
# % description: Timestamp of format "YYYY-MM-DD HH:MM:SS"
# % type: string
# % required: no
# % multiple: no
# % guisection: Filter
# %end

# %option
# % key: start_time
# % label: Earliest timestamp of temporal extent to include in the output
# % description: Timestamp of format "YYYY-MM-DD HH:MM:SS"
# % type: string
# % required: no
# % multiple: no
# % guisection: Filter
# %end

# %option
# % key: temporal_relations
# % label: Allowed temporal relation for temporal filtering
# % description: Allowed temporal relation between time dimension in the netCDF file and temporal window defined by start_time and end_time
# % type: string
# % required: no
# % multiple: yes
# % options: equal,during,contains,overlaps,overlapped,starts,started,finishes,finished
# % answer: equal,during,contains,overlaps,overlapped,starts,started,finishes,finished
# % guisection: Filter
# %end

# %option
# % key: resample
# % type: string
# % required: no
# % multiple: no
# % label: Resampling method when data is reprojected
# % options: nearest,bilinear,bicubic,cubicspline,lanczos,average,mode,max,min,med,Q1,Q3
# % answer: nearest
# % guisection: Settings
# %end

# %option
# % key: print
# % type: string
# % required: no
# % multiple: no
# % label: Print metadata and exit
# % options: extended, grass
# % guisection: Print
# %end

# %option G_OPT_M_COLR
# % description: Color table to assign to imported datasets
# % answer: viridis
# % guisection: Settings
# %end

# %option
# % key: memory
# % type: integer
# % required: no
# % multiple: no
# % key_desc: memory in MB
# % label: Maximum memory to be used (in MB)
# % description: Cache size for raster rows
# % answer: 300
# % guisection: Settings
# %end

# %option
# % key: nprocs
# % type: integer
# % required: no
# % multiple: no
# % key_desc: Number of cores
# % label: Number of cores to use during import
# % answer: 1
# % guisection: Settings
# %end

# %option G_OPT_F_SEP
# % guisection: Settings
# %end

# %rules
# % excludes: -l,-r
# % excludes: print,output
# % required: print,output
# %end

# %option
# % key: nodata
# % type: string
# % required: no
# % multiple: yes
# % key_desc: Source nodata
# % description: Comma separated list of values representing nodata in the input dataset
# %end

# Todo:
# Allow filtering based on metadata
# Support more VRT options (gdal_datatype)
# Implement e-flag
# Allow to print subdataset information as semantic label json (useful defining custom semantic labels)
# - Make use of more metadata (units, scaling)

from copy import deepcopy
from datetime import datetime
from functools import partial
from io import StringIO
from itertools import chain
from math import ceil, floor
from multiprocessing import Pool
import os
from pathlib import Path
import re
import sys

import numpy as np

# import dateutil.parser as parser

import grass.script as gscript
import grass.temporal as tgis
from grass.pygrass.modules import Module, MultiModule
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region

# from grass.temporal. import update_from_registered_maps
from grass.temporal.register import register_maps_in_space_time_dataset
from grass.temporal.temporal_extent import TemporalExtent
from grass.temporal.datetime_math import datetime_to_grass_datetime_string

# Datasets may or may not contain subdatasets
# Datasets may contain several layers
# r.external registers all bands by default

RESAMPLE_DICT = {
    "nearest": "near",
    "bilinear": "bilinear",
    "bicubic": "cubic",
    "cubicspline": "cubicspline",
    "lanczos": "lanczos",
    "average": "average",
    "mode": "mode",
    "max": "max",
    "min": "min",
    "med": "med",
    "Q1": "Q1",
    "Q3": "Q3",
}

GRASS_VERSION = list(map(int, gscript.version()["version"].split(".")[0:2]))
TGIS_VERSION = 2
ALIGN_REGION = None


def align_windows(window, region=None):
    """Align two regions
    Python version of:
    https://github.com/OSGeo/grass/blob/main/lib/raster/align_window.c

    Modifies the input ``window`` to align to ``ref`` region. The
    resolutions in ``window`` are set to match those in ``ref``
    and the ``window`` edges (north, south, east, west) are modified
    to align with the grid of the ``ref`` region.

    The ``window`` may be enlarged if necessary to achieve the
    alignment. The north is rounded northward, the south southward,
    the east eastward and the west westward. Lon-lon constraints are
    taken into consideration to make sure that the north doesn't go
    above 90 degrees (for lat/lon) or that the east does "wrap" past
    the west, etc.

    :param window: dict of window to align, with keys north, south, east,
                   west, ns_res, ew_res, is_latlong
    :type window: dict
    :param ref: dict of window to align to, with keys north, south, east,
                west, ns_res, ew_res, is_latlong
    :type ref: dict
    :return: a modified version of ``window`` that is aligend to ``ref``
    :rtype: dict

    """
    aligned_window = {
        "ns_res": region.nsres,
        "ew_res": region.ewres,
        "is_latlong": region.proj == "ll",
        "north": (
            region.north
            - floor((region.north - window[3]) / region.nsres) * region.nsres
        ),
        "south": (
            region.south
            - ceil((region.south - window[1]) / region.nsres) * region.nsres
        ),
        "west": (
            region.west + floor((window[0] - region.west) / region.ewres) * region.ewres
        ),
        "east": (
            region.east + ceil((window[2] - region.east) / region.ewres) * region.ewres
        ),
    }
    if aligned_window["is_latlong"]:
        while aligned_window["north"] > 90.0 + aligned_window["ns_res"] / 2.0:
            aligned_window["north"] -= aligned_window["ns_res"]
        while aligned_window["south"] < -90.0 - aligned_window["ns_res"] / 2.0:
            aligned_window["south"] += aligned_window["ns_res"]
    return aligned_window


def legalize_name_string(string):
    """Replace conflicting characters with _"""
    legal_string = re.sub(r"[^\w\d-]+|[^\x00-\x7F]+|[ -/\\]+", "_", string)
    return legal_string


def get_time_dimensions(meta):
    """Extracts netcdf-cf compliant time dimensions from metadata using UDUNITS2"""
    if "NETCDF_DIM_time_VALUES" not in meta:
        return None
    time_values = np.fromstring(
        meta["NETCDF_DIM_time_VALUES"].strip("{").strip("}"), sep=",", dtype=np.float64
    )
    time_dates = cf_units.num2date(
        time_values, meta["time#units"], meta["time#calendar"]
    )
    return time_dates


def check_semantic_label_support(module_options):
    """Check if the current version of GRASS GIS and TGIS support the
    semantic label concept"""
    if GRASS_VERSION[0] < 8:
        if module_options["semantic_labels"]:
            gscript.warning(
                _(
                    "The semantic labels concept requires GRASS GIS version 8.0 or later.\n"
                    "Ignoring the semantic label configuration file <{conf_file}>"
                ).format(conf_file=module_options["semantic_labels"])
            )
        return False

    if TGIS_VERSION < 3:
        if module_options["semantic_labels"]:
            gscript.warning(
                _(
                    "The semantic labels concept requires TGIS version 3 or later.\n"
                    "Ignoring the semantic label configuration file <{conf_file}>"
                ).format(conf_file=module_options["semantic_labels"])
            )
        return False

    return True


def parse_semantic_label_conf(conf_file):
    """Read user provided mapping of subdatasets / variables to semantic labels
    Return a dict with mapping, bands that are not mapped in this file are skipped
    from import"""
    if conf_file is None or conf_file == "" or SEMANTIC_LABEL_SUPPORT is False:
        return None

    semantic_label = {}
    if not os.access(options["semantic_labels"], os.R_OK):
        gscript.fatal(
            _(
                "Cannot read configuration file <{conf_file}>".format(
                    conf_file=conf_file
                )
            )
        )
    with open(conf_file, "r") as c_file:
        configuration = c_file.read()
        for idx, line in enumerate(configuration.split("\n")):
            if line.startswith("#") or "=" not in line:
                continue
            if len(line.split("=")) == 2:
                line = line.split("=")
                # Check if assigned semantic label has legal a name
                if Rast_legal_semantic_label(line[1]) == 1:
                    semantic_label[line[0]] = line[1]
                else:
                    gscript.fatal(
                        _(
                            "Line {line_nr} in configuration file <{conf_file}> "
                            "contains an illegal band name".format(
                                line_nr=idx + 1, conf_file=conf_file
                            )
                        )
                    )
    if not semantic_label:
        gscript.fatal(
            _(
                "Invalid formated or empty semantic label configuration in file <{}>".format(
                    conf_file
                )
            )
        )

    return semantic_label


def get_metadata(netcdf_metadata, subdataset="", semantic_label=None):
    """Transform NetCDF metadata to GRASS metadata"""
    # title , history , institution , source , comment and references

    meta = {}
    # title is required metadata for netCDF-CF
    title = (
        netcdf_metadata["NC_GLOBAL#title"]
        if "NC_GLOBAL#title" in netcdf_metadata
        else ""
    )
    title += (
        ", {subdataset}: {long_name}, {method}".format(
            subdataset=subdataset,
            long_name=netcdf_metadata.get("{}#long_name".format(subdataset)),
            method=netcdf_metadata.get("{}#cell_methods".format(subdataset)),
        )
        if subdataset != ""
        else ""
    )
    title += (
        ", version: {}".format(netcdf_metadata["NC_GLOBAL#version"])
        if "NC_GLOBAL#version" in netcdf_metadata
        else ""
    )
    title += (
        ", type: {}".format(netcdf_metadata["NC_GLOBAL#type"])
        if "NC_GLOBAL#type" in netcdf_metadata
        else ""
    )
    meta["title"] = title
    # history is required metadata for netCDF-CF
    meta["history"] = netcdf_metadata.get(
        "NC_GLOBAL#history"
    )  # phrase Text to append to the next line of the map's metadata file
    meta["units"] = netcdf_metadata.get(
        "{}#units".format(subdataset)
    )  # string Text to use for map data units

    meta["vdatum"] = None  # string Text to use for map vertical datum
    meta["source1"] = netcdf_metadata.get("NC_GLOBAL#source")
    meta["source2"] = netcdf_metadata.get("NC_GLOBAL#institution")

    meta["description"] = "\n".join(
        map(
            str,
            filter(
                None,
                [
                    netcdf_metadata.get("NC_GLOBAL#summary"),
                    netcdf_metadata.get("NC_GLOBAL#comment"),
                    netcdf_metadata.get("NC_GLOBAL#references"),
                ],
            ),
        )
    )
    if semantic_label is not None:
        meta["semantic_label"] = semantic_label[subdataset]
    elif SEMANTIC_LABEL_SUPPORT and Rast_legal_semantic_label(subdataset):
        meta["semantic_label"] = subdataset

    return meta


def transform_bounding_box(bbox, transform, edge_densification=15):
    """Transform the datasets bounding box into the projection of the location
    with desified edges
    bbox is a tuple of (xmin, ymin, xmax, ymax)
    Adapted from:
    https://gis.stackexchange.com/questions/165020/how-to-calculate-the-bounding-box-in-projected-coordinates
    """
    u_l = np.array((bbox[0], bbox[3]))
    l_l = np.array((bbox[0], bbox[1]))
    l_r = np.array((bbox[2], bbox[1]))
    u_r = np.array((bbox[2], bbox[3]))

    def _transform_vertex(vertex):
        x_transformed, y_transformed, _ = transform.TransformPoint(*vertex)
        return (x_transformed, y_transformed)

    # This list comprehension iterates over each edge of the bounding box,
    # divides it into `edge_densification` number of points, then reduces
    # that list to an appropriate `bounding_fn` given the edge.
    # For example the left edge needs to be the minimum x coordinate so
    # we generate `edge_samples` number of points between the upper left and
    # lower left point, transform them all to the new coordinate system
    # then get the minimum x coordinate "min(p[0] ...)" of the batch.
    transformed_bounding_box = [
        bounding_fn(
            [
                _transform_vertex(p_a * v + p_b * (1 - v))
                for v in np.linspace(0, 1, edge_densification)
            ]
        )
        for p_a, p_b, bounding_fn in [
            (u_l, l_l, lambda point_list: min([p[0] for p in point_list])),
            (l_l, l_r, lambda point_list: min([p[1] for p in point_list])),
            (l_r, u_r, lambda point_list: max([p[0] for p in point_list])),
            (u_r, u_l, lambda point_list: max([p[1] for p in point_list])),
        ]
    ]
    return transformed_bounding_box


def check_projection_match(reference_crs, subdataset):
    """Check if projections match with projection of the location
    using gdal/osr
    """
    subdataset_crs = subdataset.GetSpatialRef()
    location_crs = osr.SpatialReference()
    location_crs.ImportFromWkt(reference_crs)
    return subdataset_crs.IsSame(location_crs)


def get_import_type(projection_match, resample, flags_dict):
    """Define import type ("r.in.gdal", "r.external")"""
    # Define resample algorithm
    if not projection_match and not flags_dict["o"]:
        resample = resample or "nearest"
        if resample not in RESAMPLE_DICT:
            gscript.fatal(
                _(
                    "For re-projection with gdalwarp only the following "
                    "resample methods are allowed: {}".format(
                        ", ".join(list(RESAMPLE_DICT.keys()))
                    )
                )
            )
        resample = RESAMPLE_DICT[resample]
    else:
        resample = None
    # Define import module
    if flags_dict["l"] or flags_dict["f"]:
        import_type = "r.external"
    else:
        import_type = "r.in.gdal"

    return import_type, resample, projection_match


def setup_temporal_filter(options_dict):
    """Gernerate temporal filter from input"""
    time_formats = {
        10: "%Y-%m-%d",
        19: "%Y-%m-%d %H:%M:%S",
    }
    kwargs = {}
    relations = options_dict["temporal_relations"].split(",")
    for time_ref in ["start_time", "end_time"]:
        if options_dict[time_ref]:
            if len(options_dict[time_ref]) not in time_formats:
                gscript.fatal(_("Unsupported datetime format in {}.".format(time_ref)))
            try:
                kwargs[time_ref] = datetime.strptime(
                    options_dict[time_ref], time_formats[len(options_dict[time_ref])]
                )
            except ValueError:
                gscript.fatal(_("Can not parse input in {}.".format(time_ref)))
        else:
            kwargs[time_ref] = None
    return TemporalExtent(**kwargs), relations


def apply_temporal_filter(ref_window, relations, start, end):
    """Apply temporal filter to time dimension"""
    if ref_window.start_time is None and ref_window.end_time is None:
        return True
    return (
        ref_window.temporal_relation(TemporalExtent(start_time=start, end_time=end))
        in relations
    )


def get_end_time(start_time_dimensions):
    """Compute end time from start time"""
    end_time_dimensions = None
    if len(start_time_dimensions) > 1:
        time_deltas = np.diff(start_time_dimensions)
        time_deltas = np.append(time_deltas, np.mean(time_deltas))
        end_time_dimensions = start_time_dimensions + time_deltas
    else:
        end_time_dimensions = start_time_dimensions
    return end_time_dimensions


# import or link data
def read_data(
    sds_dict,
    flags_dict,
    modules,
    gisenv,
):
    """Import or link data and metadata"""

    input_url = sds_dict["url"]
    metadata = sds_dict["grass_metadata"]
    import_type = sds_dict["import_options"][0]
    start_time_dimensions = sds_dict["start_time_dimensions"]
    maps = sds_dict["maps"]
    bands = sds_dict["bands"]
    strds_name = sds_dict["strds_name"]

    queue = []

    # Merge major functions?

    # Requires GRASS GIS >= 8.0
    # r.external [-feahvtr]
    # r.in.gdal [-eflakcrp]
    # is_subdataset = input_url.startswith("NETCDF")

    # Setup import module
    import_mod = modules[import_type]
    import_mod.inputs.input = input_url

    # Setup metadata module
    meta_mod = modules["r.support"]
    meta_mod(**metadata)

    # Setup timestamp module
    time_mod = modules["r.timestamp"]
    if not flags_dict["f"]:
        # Setup color module
        color_mod = modules["r.colors"]
    # Parallel module
    # mapname_list = []
    # infile = Path(input_url).name.split(":")
    # mapname_list.append(legalize_name_string(infile[0]))
    # if is_subdataset:
    # mapname_list.append(legalize_name_string(infile[1]))

    for i, raster_map in enumerate(maps):
        band = bands[i]
        mapname = raster_map.split("@")[0]
        new_meta = deepcopy(meta_mod)
        new_meta(map=mapname)
        new_time = deepcopy(time_mod)
        new_time(
            map=mapname,
            date=datetime_to_grass_datetime_string(
                start_time_dimensions[i]
            ),  # use predefined string
        )
        mm = []
        if not RasterRow(mapname, gisenv["MAPSET"]).exist() or gscript.overwrite():
            new_import = deepcopy(import_mod)
            new_import(band=band, output=mapname)
            mm.append(new_import)
        if not flags_dict["f"]:
            new_color = deepcopy(color_mod)
            new_color(map=mapname)
            mm.append(new_color)
        mm.extend([new_meta, new_time])

        queue.append(mm)

    return strds_name, maps, queue


def create_vrt(
    subdataset, gisenv, resample, nodata, equal_proj, transform, recreate=False
):
    """Create a GDAL VRT for import"""
    vrt_dir = Path(gisenv["GISDBASE"]).joinpath(
        gisenv["LOCATION_NAME"], gisenv["MAPSET"], "gdal"
    )
    vrt = vrt_dir.joinpath(
        "netcdf_{}.vrt".format(
            legalize_name_string(Path(subdataset.GetDescription()).name)
        )
    )
    vrt_name = str(vrt)
    if vrt.exists() and not recreate:
        return vrt_name
    kwargs = {"format": "VRT"}
    if equal_proj:
        if nodata is not None:
            kwargs["noData"] = nodata
        vrt = gdal.Translate(
            vrt_name,
            subdataset,  # Use already opened dataset here
            options=gdal.TranslateOptions(
                **kwargs
                # stats=True,
                # outputType=gdal.GDT_Int16,
                # outputBounds=
            ),
        )
    else:
        gt = subdataset.GetGeoTransform()
        transformed_bbox = transform_bounding_box(
            (
                gt[0],
                gt[3] + gt[5] * subdataset.RasterYSize,
                gt[0] + gt[1] * subdataset.RasterXSize,
                gt[3],
            ),
            transform,
            edge_densification=15,
        )
        # Cropping to computational region should only be done with r-flag
        aligned_bbox = ALIGN_REGION(transformed_bbox)
        kwargs["dstSRS"] = gisenv["LOCATION_PROJECTION"]
        kwargs["resampleAlg"] = resample
        # Resolution should be probably taken from region rather than from source dataset
        kwargs["xRes"] = gt[1]
        kwargs["yRes"] = -gt[5]
        kwargs["outputBounds"] = (
            aligned_bbox["west"],
            aligned_bbox["south"],
            aligned_bbox["east"],
            aligned_bbox["north"],
        )

        if nodata is not None:
            kwargs["srcNodata"] = nodata
        vrt = gdal.Warp(
            vrt_name,
            subdataset,
            options=gdal.WarpOptions(
                **kwargs
                # outputType=gdal.GDT_Int16,
            ),
        )
    vrt = None
    vrt = vrt_name

    return vrt


def parse_netcdf(
    in_url,
    semantic_label,
    reference_crs,
    valid_window,
    valid_relations,
    options,
    flags,
    gisenv,
):
    """Parse and check netcdf file to extract relevant metadata"""

    inputs_dict = {}

    # Check if file exists and readable
    gscript.verbose(_("Processing {}".format(in_url)))
    try:
        ncdf = gdal.Open(in_url)
    except FileNotFoundError:
        gscript.warning(_("Could not open <{}>.\nSkipping...".format(in_url)))
        return None

    # Get global metadata
    ncdf_metadata = ncdf.GetMetadata()

    # Get CF version
    cf_version = ncdf_metadata.get("NC_GLOBAL#Conventions")

    if cf_version is None or not cf_version.upper().startswith("CF"):
        gscript.warning(
            _(
                "Input netCDF file does not adhere to CF-standard. Import may fail or be incorrect."
            )
        )

    # Sub datasets containing variables have 3 dimensions (x,y,z)
    sds = [
        # SDS_ID, SDS_url, SDS_dimension
        [sds[0].split(":")[-1], sds[0], len(sds[1].split(" ")[0].split("x"))]
        for sds in ncdf.GetSubDatasets()
        if len(sds[1].split(" ")[0].split("x")) == 3
    ]

    # Filter based on semantic_label if provided
    if semantic_label is not None:
        sds = [s for s in sds if s[0] in semantic_label.keys()]

    # Open subdatasets to get metadata
    if sds:  # and ncdf.RasterCount == 0:
        sds = [[gdal.Open(s[1])] + s for s in sds]
    elif not sds and ncdf.RasterCount == 0:
        gscript.warning(_("No data to import from file {}").format(in_url))
        return None
    else:
        # Check raster layers
        sds = [ncdf, "", "", 0]

    # Extract metadata
    # Collect relevant inputs in a dictionary
    inputs_dict[in_url] = {}
    inputs_dict[in_url]["sds"] = []

    for s_d in sds:
        sds_metadata = s_d[0].GetMetadata()
        sds_url = s_d[0].GetDescription()
        raster_count = s_d[0].RasterCount
        if "NETCDF_DIM_time_VALUES" in sds_metadata:
            # Apply temporal filter
            sd_time_dimensions = get_time_dimensions(sds_metadata)
            end_times = get_end_time(sd_time_dimensions)
            requested_time_dimensions = np.array(
                [
                    apply_temporal_filter(
                        valid_window, valid_relations, start, end_times[idx]
                    )
                    for idx, start in enumerate(sd_time_dimensions)
                ]
            )
            if not requested_time_dimensions.any():
                gscript.warning(
                    _(
                        "Nothing to import from subdataset {s} in {f}".format(
                            s=s_d[1], f=sds_url
                        )
                    )
                )
                continue

            end_time_dimensions = end_times[requested_time_dimensions]
            # s_d["requested_time_dimensions"] = np.where(requested_time_dimensions)[0]
            start_time_dimensions = sd_time_dimensions[requested_time_dimensions]
            requested_time_dimensions = np.where(requested_time_dimensions)[0]

            # Get metadata
            grass_metadata = get_metadata(sds_metadata, s_d[1], semantic_label)
            # Compile mapname
            infile = Path(in_url).stem.split(":")
            map_name = legalize_name_string(infile[0])
            location_crs = osr.SpatialReference()
            location_crs.ImportFromWkt(reference_crs)
            subdataset_crs = s_d[0].GetSpatialRef()
            projections_match = subdataset_crs.IsSame(location_crs)
            import_type, resample, projections_match = get_import_type(
                flags["o"] or projections_match,
                options["resample"],
                flags,
            )

            transform = None
            if not projections_match:
                transform = osr.CoordinateTransformation(subdataset_crs, location_crs)

            # Loop over bands / time dimension
            maps = []
            bands = []
            for i, band in enumerate(requested_time_dimensions):
                if raster_count > 1:
                    map_name = f"{map_name}_{start_time_dimensions[i].strftime('%Y%m%dT%H%M%S')}"
                map_name = f"{map_name}.{grass_metadata.get('semantic_label') or i + 1}"
                bands.append(i + 1)
                maps.append(
                    "{map}@{mapset}|{start_time}|{end_time}|{semantic_label}".format(
                        map=map_name,
                        mapset=gisenv["MAPSET"],
                        start_time=start_time_dimensions[i].strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        end_time=end_time_dimensions[i].strftime("%Y-%m-%d %H:%M:%S"),
                        semantic_label=grass_metadata.get("semantic_label") or "",
                    )
                )
            # Store metadata in dictionary
            inputs_dict[in_url]["sds"].append(
                {
                    "strds_name": (
                        "{}_{}".format(options["output"], s_d[1])
                        if s_d[1] and not semantic_label
                        else options["output"]
                    ),
                    "id": s_d[1],
                    "url": sds_url
                    if options["print"] or import_type == "r.in.gdal"
                    else create_vrt(
                        s_d[0],
                        gisenv,
                        resample,
                        options["nodata"],
                        projections_match,
                        transform,
                        recreate=gscript.overwrite(),
                    ),  # create VRT here???
                    "grass_metadata": grass_metadata,
                    "extended_metadata": sds_metadata,
                    "time_dimensions": sd_time_dimensions,
                    "start_time_dimensions": start_time_dimensions,
                    "end_time_dimensions": end_time_dimensions,
                    "requested_time_dimensions": requested_time_dimensions,
                    "rastercount": s_d[0].RasterCount,
                    "bands": bands,
                    "maps": maps,
                    "import_options": [import_type, resample, projections_match],
                }
            )
        # Close open GDAL datasets
        s_d = None
    # Close open GDAL datasets
    sds = None

    return inputs_dict


def run_modules(mod_list):
    """Run MultiModules"""
    for mm in mod_list:
        MultiModule(
            module_list=mm,
            sync=True,
            set_temp_region=False,
        ).run()


def main():
    """run the main workflow"""

    global cf_units
    try:
        import cf_units
    except ImportError:
        gscript.fatal(
            _(
                "Cannot import Python library 'cf-units'\n"
                "Please install it with (pip install cf-units)"
            )
        )

    # Check if NetCDF driver is available
    if not gdal.GetDriverByName("netCDF"):
        gscript.fatal(
            _("netCDF driver missing in GDAL. Please install netcdf binaries.")
        )

    # Unregister potentially conflicting driver
    for driver in ["HDF5", "HDF5Image"]:
        if gdal.GetDriverByName(driver):
            gdal.GetDriverByName(driver).Deregister()

    inputs = options["input"].split(",")
    sep = gscript.utils.separator(options["separator"])

    valid_window, valid_relations = setup_temporal_filter(options)

    if options["nodata"]:
        try:
            nodata = " ".join(map(str, map(int, options["nodata"].split(","))))
        except Exception:
            gscript.fatal(_("Invalid input for nodata"))
    else:
        nodata = None

    if len(inputs) == 1:
        if inputs[0] == "-":
            inputs = sys.stdin.read().strip().split()
        elif not inputs[0].endswith(".nc"):
            try:
                with open(inputs[0], "r") as in_file:
                    inputs = in_file.read().strip().split()
            except IOError:
                gscript.fatal(_("Unable to read text from <{}>.".format(inputs[0])))

    inputs = [
        "/vsicurl/" + in_url if in_url.startswith("http") else in_url
        for in_url in inputs
    ]

    for in_url in inputs:
        # Maybe other suffixes are valid too?
        if not in_url.endswith(".nc"):
            gscript.fatal(_("<{}> does not seem to be a NetCDF file".format(in_url)))

    # Initialize TGIS
    tgis.init()
    global TGIS_VERSION
    TGIS_VERSION = tgis.get_tgis_db_version_from_metadata()

    global SEMANTIC_LABEL_SUPPORT
    SEMANTIC_LABEL_SUPPORT = check_semantic_label_support(options)
    semantic_label = parse_semantic_label_conf(options["semantic_labels"])

    # Get GRASS GIS environment info
    grass_env = dict(gscript.gisenv())

    # Create directory for vrt files if needed
    if flags["l"] or flags["f"]:
        vrt_dir = Path(grass_env["GISDBASE"]).joinpath(
            grass_env["LOCATION_NAME"], grass_env["MAPSET"], "gdal"
        )
        if not vrt_dir.is_dir():
            vrt_dir.mkdir()

    # Get projection of the current location
    grass_env["LOCATION_PROJECTION"] = gscript.read_command(
        "g.proj", flags="wf"
    ).strip()

    # Current region
    global ALIGN_REGION
    ALIGN_REGION = partial(align_windows, region=Region())

    # Get existing STRDS
    dataset_list = tgis.list_stds.get_dataset_list(
        type="strds", temporal_type="absolute", columns="name"
    )
    existing_strds = (
        [row["name"] for row in dataset_list[grass_env["MAPSET"]]]
        if grass_env["MAPSET"] in dataset_list
        else []
    )

    # Setup module objects
    imp_flags = "o" if flags["o"] else ""
    modules = {
        "r.external": Module(
            "r.external",
            quiet=True,
            overwrite=gscript.overwrite(),
            run_=False,
            finish_=False,
            flags=imp_flags + "ra" if flags["f"] else imp_flags + "ma",
        ),
        "r.in.gdal": Module(
            "r.in.gdal",
            quiet=True,
            overwrite=gscript.overwrite(),
            run_=False,
            finish_=False,
            flags=imp_flags + "ra" if flags["r"] else imp_flags + "a",
            memory=options["memory"],
        ),
        "r.timestamp": Module("r.timestamp", quiet=True, run_=False, finish_=False),
        "r.colors": Module(
            "r.colors",
            quiet=True,
            color=options["color"],
            run_=False,
            finish_=False,
        ),
        "r.support": Module("r.support", quiet=True, run_=False, finish_=False),
    }

    # Check inputs
    # URL or file readable
    # STRDS exists / appcreation_dateend to
    # get basename from existing STRDS

    modified_strds = {}
    queued_modules = []

    if int(options["nprocs"]) <= 1 or len(inputs) <= 1:
        inputs_dict = [
            parse_netcdf(
                in_url,
                semantic_label,
                grass_env["LOCATION_PROJECTION"],
                valid_window,
                valid_relations,
                options,
                flags,
                grass_env,
            )
            for in_url in inputs
        ]
    else:
        with Pool(processes=min([int(options["nprocs"]), len(inputs)])) as p:
            inputs_dict = p.starmap(
                parse_netcdf,
                [
                    (
                        in_url,
                        semantic_label,
                        grass_env["LOCATION_PROJECTION"],
                        valid_window,
                        valid_relations,
                        options,
                        flags,
                        grass_env,
                    )
                    for in_url in inputs
                ],
            )
    inputs_dict = {k: v for elem in inputs_dict if elem for k, v in elem.items()}

    if options["print"] in ["grass", "extended"]:
        print_type = "{}_metadata".format(options["print"])
        print(
            sep.join(
                ["id", "url", "rastercount", "time_dimensions"]
                + list(next(iter(inputs_dict.values()))["sds"][0][print_type].keys())
            )
        )
        print(
            "\n".join(
                [
                    sep.join(
                        [
                            s_d["id"],
                            s_d["url"],
                            str(s_d["rastercount"]),
                            str(len(s_d["time_dimensions"])),
                        ]
                        + list(map(str, s_d[print_type].values()))
                    )
                    for s_d in chain.from_iterable(
                        [i["sds"] for i in inputs_dict.values()]
                    )
                ]
            )
        )
        sys.exit(0)

    # Create STRDS if necessary
    relevant_strds = {
        (
            dval["strds_name"],
            dval["grass_metadata"]["title"],
            dval["grass_metadata"]["description"],
        )
        for sds_dict in inputs_dict.values()
        for dval in sds_dict["sds"]
    }

    relevant_strds_dict = {}

    for strds in relevant_strds:
        if strds[0] not in relevant_strds_dict:
            relevant_strds_dict[strds[0]] = {"title": strds[1], "description": strds[2]}
        else:
            if strds[1] not in relevant_strds_dict[strds[0]]["title"]:
                relevant_strds_dict[strds[0]]["title"] += f", {strds[1]}"
            if strds[2] not in relevant_strds_dict[strds[0]]["description"]:
                relevant_strds_dict[strds[0]]["description"] += f", {strds[2]}"

    # Get unique list of STRDS to be created or modified
    for strds in relevant_strds_dict:
        # Append if exists and overwrite allowed (do not update metadata)
        if (
            strds not in existing_strds or (gscript.overwrite and not flags["a"])
        ) and strds not in modified_strds:
            tgis.open_new_stds(
                strds,
                "strds",  # type
                "absolute",  # temporaltype
                relevant_strds_dict[strds]["title"],
                relevant_strds_dict[strds]["description"],
                "mean",  # semanticstype
                None,  # dbif
                gscript.overwrite,
            )
            modified_strds[strds] = []
        elif not flags["a"]:
            gscript.fatal(_("STRDS exisits."))

        else:
            modified_strds[strds] = []

        if strds not in existing_strds:
            existing_strds.append(strds)

    # This is a time consuming part due to building of VRT files
    with Pool(processes=int(options["nprocs"])) as pool:
        queueing_results = pool.starmap(
            read_data,
            [
                (
                    sds_dict,
                    # options,
                    flags,
                    modules,
                    grass_env,
                    # nodata,
                )
                for url_dict in inputs_dict.values()
                for sds_dict in url_dict["sds"]
            ],
        )

    for qres in queueing_results:
        modified_strds[qres[0]].extend(qres[1])
        queued_modules.extend(qres[2])

    # Run modules in parallel
    use_cores = min(len(queued_modules), int(options["nprocs"]))
    with Pool(processes=use_cores) as pool:
        pool.map(run_modules, np.array_split(queued_modules, use_cores))

    for strds_name, r_maps in modified_strds.items():
        # Register raster maps in strds using tgis
        tgis_strds = tgis.SpaceTimeRasterDataset(strds_name + "@" + grass_env["MAPSET"])
        if GRASS_VERSION >= [8, 0] and TGIS_VERSION >= 3:
            map_file = StringIO("\n".join(r_maps))
        else:
            map_file = gscript.tempfile()
            with open(map_file, "w") as m_f:
                m_f.write("\n".join(r_maps))
        register_maps_in_space_time_dataset(
            "raster",
            strds_name + "@" + grass_env["MAPSET"],
            file=map_file,
            update_cmd_list=False,
        )

        tgis_strds.update_from_registered_maps(dbif=None)

    return 0


if __name__ == "__main__":
    options, flags = gscript.parser()

    # lazy imports
    global gdal
    try:
        from osgeo import gdal, osr
    except ImportError:
        gscript.fatal(
            _(
                "Unable to load GDAL Python bindings (requires "
                "package 'python-gdal' or Python library GDAL "
                "to be installed)."
            )
        )

    try:
        from grass.lib.raster import Rast_legal_semantic_label

        SEMANTIC_LABEL_SUPPORT = True
    except Exception:
        SEMANTIC_LABEL_SUPPORT = False

    sys.exit(main())
