#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.in.ssurgo
# AUTHOR:       Corey T. White, GeoForAll Lab, NCSU
# PURPOSE:      Get SSURGO ZIP files from Web Soil Survey
# COPYRIGHT:    (C) 2025-2026 Corey White and the GRASS Development Team
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Download and import SSURGO data from the USDA for a specified soil survey area.
# % keyword: raster
# % keyword: import
# % keyword: soils
# % keyword: SSURGO
# %end

# %option G_OPT_F_INPUT
# % key: ssurgo_path
# % description: Path to the SSURGO ZIP file downloaded from Web Soil Survey
# % guisection: Inputs
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: hydgrp
# % description: Hydrologic soil group
# % guisection: Outputs
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: ksat_h
# % description: Saturated Hydraulic Conductivity of Soil Ksat (high) [mm/hr]
# % guisection: Outputs
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: ksat_r
# % description: Saturated Hydraulic Conductivity of Soil Ksat (regular) [mm/hr]
# % guisection: Outputs
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: ksat_l
# % description: Saturated Hydraulic Conductivity of Soil Ksat (low) [mm/hr]
# % guisection: Outputs
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: mukey
# % description: Map unit key
# % guisection: Outputs
# % required: no
# %end

# %option G_OPT_V_OUTPUT
# % key: ssurgo_areas
# % description: Name for output soil grid
# % guisection: Outputs
# % required: no
# %end

# %option
# % key: desgnmaster
# % guisection: Options
# % type: string
# % required: no
# % multiple: no
# % options: A
# % answer: A
# % description: Designation of master horizon
# %end

# %option
# % key: hzdept_r
# % guisection: Options
# % type: integer
# % required: no
# % multiple: no
# % answer: 0
# % description: Horizon depth top (cm)
# %end

# %option
# % key: hzdepb_r
# % guisection: Options
# % type: integer
# % required: no
# % description: Horizon depth bottom (cm)
# %end

# %option G_OPT_M_NPROCS
# %end

# %flag
# % key: d
# % description: Use Soil Data Access (SDA) to query and download data for the specified map unit key (mukey) instead of using a local SSURGO ZIP file.
# %end

from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile
from requests import options
import grass.script as gs
from grass.exceptions import CalledModuleError
from grass.tools import Tools
from io import StringIO
import gettext
import json
import re
from enum import Enum
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import textwrap

# Set up translation function
_ = gettext.gettext

# Active GRASS session tools
tools = Tools()
SESSION = tools.g_gisenv(get="GISDBASE,LOCATION_NAME,MAPSET", sep="/").text
# --- Unit conversion constant ---
MICROMETERS_PER_SECOND_TO_MM_PER_HOUR = 3.6

gs.message(f"Active GRASS session: {SESSION}")


def _import_duckdb(error):
    """Import duckdb module"""
    try:
        import duckdb

        return duckdb
    except ImportError as err:
        if error:
            raise err
        return None


def region_to_crs_bbox(target_crs: str) -> list[float]:
    """Convert GRASS region bounds to a bounding box in another CRS using m.proj."""
    region = gs.region()
    # Extract corner coordinates
    west, south, east, north = region["w"], region["s"], region["e"], region["n"]
    nsres = region["nsres"]
    ewres = region["ewres"]

    # Format input coordinates for m.proj (as string input to stdin)
    coords = f"{west}|{south}\n{east}|{north}\n"

    proj_in = gs.parse_command("g.proj", format="proj4", flags="pf")
    gs.debug(_("region_to_crs_bbox: proj_in: %s") % proj_in)
    proj_out = gs.parse_command("g.proj", format="proj4", srid=target_crs, flags="pf")
    gs.debug(_("region_to_crs_bbox: proj_out: %s") % proj_out)

    # We currently dont have an easy way to get arround needing a tempfile when
    # we want to both pass an argument to stdin and we want the results added to the stdout
    with tempfile.NamedTemporaryFile(
        mode="w+t", prefix="r_soildb", suffix=".txt"
    ) as fp:
        try:
            gs.write_command(
                "m.proj",
                input="-",
                proj_in=f"+proj={proj_in['+proj']}",
                proj_out=f"+proj={proj_out['+proj']}",
                stdin=coords,
                output=fp.name,
                verbose=True,
                quiet=False,
                overwrite=True,
            )
        except CalledModuleError as e:
            gs.fatal(f"Projection failed: {e}")

        # Parse the tempfile output
        lines = fp.readlines()
        gs.message(_("Reproject Bounds for WCS query: %s") % lines)
        clean_lines = [line.strip() for line in lines]
        ll_x, ll_y, ll_z = map(float, clean_lines[0].split("|"))  # Lower-left
        ur_x, ur_y, ur_z = map(float, clean_lines[1].split("|"))  # Upper-right

        return [ll_x, ll_y, ur_x, ur_y, ewres, nsres]


def region_to_crs_wkt(target_crs: str = "EPSG:5070") -> str:
    """Convert GRASS region bounds to a WKT polygon in another CRS using m.proj."""
    west, south, east, north = region_to_crs_bbox(target_crs)[:4]
    wkt = f"POLYGON(({west} {south}, {east} {south}, {east} {north}, {west} {north}, {west} {south}))"
    gs.debug(_("region_to_crs_wkt: wkt: %s") % wkt)
    return wkt


def region_to_wgs84_decimal_degrees_bbox():
    """convert region bbox to wgs84 decimal degrees bbox"""
    region = gs.parse_command("g.region", quiet=True, flags="ubg")
    bbox = [
        float(c)
        for c in [region["ll_w"], region["ll_s"], region["ll_e"], region["ll_n"]]
    ]
    return bbox


def region_to_wkt_wgs84():
    """Convert GRASS region bounds to a WKT polygon in WGS84."""
    west, south, east, north = region_to_wgs84_decimal_degrees_bbox()
    wkt = f"POLYGON(({west} {south}, {east} {south}, {east} {north}, {west} {north}, {west} {south}))"
    return wkt


def check_if_zipfile(file_path: Path) -> Path:
    """Check if the provided file path is a ZIP file."""
    # if not file_path.is_file():
    #     raise FileNotFoundError(f"File not found: {file_path}")
    # if file_path.suffix.lower() == ".zip":
    return Path("/vsizip") / file_path.relative_to(file_path.anchor)
    # return file_path


def connect_duckdb(threads=None):
    """Connect to a DuckDB database."""
    duckdb = _import_duckdb(error=True)
    duckdb_config = {}

    # By default, duckdb uses all available threads.
    if threads > 0:
        duckdb_config = {"threads": threads}

    con = duckdb.connect(read_only=False, config=duckdb_config)
    con.install_extension("spatial")
    con.load_extension("spatial")
    return con


def hydrologic_group_categories(hydgrp_code):
    """Lookup table for hydrologic group codes to descriptions."""
    lookup = {
        "A": "Low runoff potential",
        "B": "Moderate runoff potential",
        "C": "High runoff potential",
        "D": "Very high runoff potential",
        "A/B": "Between A and B",
        "A/C": "Between A and C",
        "A/D": "Between A and D",
        "B/C": "Between B and C",
        "B/D": "Between B and D",
        "C/D": "Between C and D",
    }
    return lookup.get(hydgrp_code, "Unknown")


def hydrologic_soil_group_categories(map_name: str) -> None:
    """Assign descriptive category labels to the hydrologic soil group raster.

    Maps integer HSG codes to human-readable labels using *r.category*.

    :param str map_name: Name of the hydrologic soil group raster map.
    """
    category_rules = [
        ("1", "A: Low runoff potential"),
        ("2", "B: Moderate runoff potential"),
        ("3", "C: High runoff potential"),
        ("4", "D: Very high runoff potential"),
        ("11", "A/D: Between A and D"),
        ("12", "B/D: Between B and D"),
        ("13", "C/D: Between C and D"),
        ("14", "D/D: Very high runoff potential (drained/undrained)"),
    ]
    rules_str = "\n".join(f"{code}|{label}" for code, label in category_rules) + "\n"
    tools.r_category(
        map=map_name,
        rules=StringIO(rules_str),
        separator="pipe",
    )


def hydrologic_soil_group_color_scheme(map_name: str) -> None:
    """Apply brown color scheme to elevation map."""
    print("Applying brown elevation color scheme...")
    hydgrp_color_palette = [
        ("1", "#E7F5FF"),  # A Low runoff potential
        ("2", "#A6D9FF"),  # B Moderate runoff potential
        ("3", "#FFD27A"),  # C High runoff potential
        ("4", "#7A2E1B"),  # D Very high runoff potential
        ("11", "#C6A8A1"),  # A/D Between A and D
        ("12", "#B1846B"),  # B/D Between B and D
        ("13", "#C06A44"),  # C/D Between C and D
        ("14", "#4A1A10"),  # D/D Very high runoff potential (drained/undrained)
    ]
    # Convert palette list to rules string for r_colors
    hydgrp_color_scheme = (
        "\n".join(f"{pos} {color}" for pos, color in hydgrp_color_palette) + "\n"
    )
    tools.r_colors(map=map_name, rules=StringIO(hydgrp_color_scheme), flags="")


def ksat_color_scheme(map_name: str) -> None:
    """Apply brown color scheme to elevation map."""
    print("Applying brown elevation color scheme...")
    ksat_color_palette = [
        # Very low Ksat (clays, compacted soils)
        ("0%", "#3B1F0E"),  # very slow infiltration
        ("10%", "#5A2D1A"),
        ("20%", "#7A3F1D"),
        # Low–moderate Ksat
        ("30%", "#9C5A2A"),
        ("40%", "#B97C3F"),
        # Transitional (loams)
        ("50%", "#D6A95C"),
        # Moderate–high Ksat
        ("60%", "#BFD38A"),
        ("70%", "#8FCB9B"),
        # High Ksat (sands)
        ("80%", "#5FB7B2"),
        ("90%", "#3A8FB7"),
        # Very high Ksat (gravel / macroporous)
        ("100%", "#1E5E8C"),
    ]
    # Convert palette list to rules string for r_colors
    ksat_color_scheme = (
        "\n".join(f"{pos} {color}" for pos, color in ksat_color_palette) + "\n"
    )
    tools.r_colors(map=map_name, rules=StringIO(ksat_color_scheme), flags="")


def update_hydrologic_group(tools, vector_map, source_col="hydgrp", target_col="hsg"):
    """
    Ensure an integer Hydrologic Soil Group (HSG) column exists on the vector and populate it from source_col.
    Mapping:
      A->1, B->2, C->3, D->4
      A/D->11, B/D->12, C/D->13, D/D->14 (dual drained/undrained codes)
    Skips unknown/ambiguous codes.
    """
    # Ensure target column exists
    cols = tools.v_info(map=vector_map, format="json", flags="c").json

    # Handles previous json repsonse structure from GRASS 8.4.1
    if type(cols) is dict:
        cols = cols.get("columns", [])

    col_names = [c["name"] for c in cols]
    if target_col not in col_names:
        tools.v_db_addcolumn(map=vector_map, columns=f"{target_col} INTEGER")

    # Mapping from hydgrp text to numeric HSG
    mapping = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "A/D": 11,  # A/D
        "B/D": 12,  # B/D
        "C/D": 13,  # C/D
        "D/D": 14,  # D/D
        # keep ambiguous combos out (AB, AC, BC, etc.) unless you have a rule
    }

    # Update rows for each mapping entry (handle uppercase/lowercase)
    for code, num in mapping.items():
        where = f"{source_col} = '{code}' OR {source_col} = '{code.lower()}'"
        tools.v_db_update(
            map=vector_map, column=target_col, value=str(num), where=where
        )

    # Optionally set unmatched values to NULL (skip here) or 0:
    tools.v_db_update(
        map=vector_map, column=target_col, value="NULL", where=f"{target_col} IS NULL"
    )

    return target_col


def local_ssurgo_query(
    con,
    wkt_bbox,
    ssurgo_path,
    desgnmaster,
    hzdept_r,
    hzdepb_r,
    hydgrp_out,
    ksat_h_out,
    ksat_r_out,
    ksat_l_out,
    mukey_out,
    ssurgo_areas_out,
):
    """
    Import SSURGO data from a local ZIP file.

    This function processes a local SSURGO ZIP file, extracts the relevant soil data based on the specified parameters,
    and outputs the desired raster and vector layers.

    Args:
        con (duckdb.Connection): An active connection to a DuckDB database with the spatial extension loaded.
        wkt_bbox (str): WKT polygon representing the bounding box.
        ssurgo_path (str): Path to the local SSURGO file.
        desgnmaster (str): Designation of master horizon.
        hzdept_r (int): Horizon depth top (cm).
        hzdepb_r (int): Horizon depth bottom (cm).
        hydgrp_out (str): Name for output hydrologic soil group raster.
        ksat_h_out (str): Name for output Ksat high raster.
        ksat_r_out (str): Name for output Ksat regular raster.
        ksat_l_out (str): Name for output Ksat low raster.
        mukey_out (str): Name for output map unit key raster.
        ssurgo_areas_out (str): Name for output soil grid vector layer.

    Returns:
        None: This function does not return any value. It creates raster and vector layers in the GRASS environment.
    """
    MICROMETERS_PER_SECOND_TO_MM_PER_HOUR = 3.6  # Conversion factor
    top = hzdept_r
    bottom = hzdepb_r
    # Table mu polygon fields used:
    # mukey: Map unit key
    # shape: Geometry field

    # Table component fields used:
    # mukey: Map unit key
    # cokey: Component key
    # comppct_r: Component percentage of map unit
    # compname: Component name
    # runoff: Runoff curve number
    # hydgrp: Hydrologic soil group
    # hydricon: Hydric condition
    # hydricrating: Hydric rating
    # drainagecl: Drainage class

    # Table chorizon fields used:
    # hzdept_r: Horizon depth top (cm)
    # hzdepb_r: Horizon depth bottom (cm)
    # ksat_r: (representative) (micrometers per second)
    #    The amount of water that would move vertically
    #    through a unit area of saturated soil in unit
    #    time under unit hydraulic gradient.
    # ksat_h: (high) (micrometers per second)
    # ksat_l: (low) (micrometers per second)
    # desgnmaster: Designation of master horizon

    # TODO: Additional fields to consider for future outputs:
    # hydgrpdcd: Hydrologic Group - Dominant Conditions
    # sandtotal_r: Sand content of the horizon (percent)
    # claytotal_r: Clay content of the horizon (percent)
    # wtdepannmin_r: Minimum annual water table depth (cm)

    # ---- Materialise each SSURGO layer into temporary tables so that ----
    # ---- DuckDB can build indexes and avoid repeated full-file scans. ---
    gs.message(_("Loading SSURGO layers into memory..."))

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE mu AS
        SELECT mukey, shape AS geom
        FROM ST_Read(
            '{ssurgo_path}',
            layer = 'MUPOLYGON',
            spatial_filter_box = ST_EXTENT(
                ST_AsWKB(ST_GeomFromText(?))
            )
        )
        """,
        [wkt_bbox],
    )
    mu_count = con.execute("SELECT count(*) FROM mu").fetchone()[0]
    gs.message(_("Loaded %d map unit polygons.") % mu_count)

    if mu_count == 0:
        gs.warning(_("No records found in your region."))
        return None

    # Load component and chorizon once; join-filter by mukey list
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE comp AS
        SELECT c.*
        FROM ST_Read('{ssurgo_path}', layer = 'component') AS c
        WHERE c.mukey IN (SELECT mukey FROM mu)
          AND c.comppct_r IS NOT NULL
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE horiz AS
        SELECT h.*
        FROM ST_Read('{ssurgo_path}', layer = 'chorizon') AS h
        WHERE h.cokey IN (SELECT cokey FROM comp)
          AND h.ksat_r IS NOT NULL
          AND h.hzdept_r = 0
          AND h.hzdepb_r > 0
          AND h.desgnmaster = '{desgnmaster}'
        """
    )

    gs.message(_("SSURGO layers loaded. Running analysis query..."))

    query = f"""
    WITH dom_comp AS (
        SELECT mu.geom,
               c.mukey,
               c.cokey,
               c.comppct_r,
               c.compname,
               c.runoff,
               c.hydgrp,
               c.hydricon,
               c.hydricrating,
               c.drainagecl,
               ROW_NUMBER() OVER (
                   PARTITION BY c.mukey
                   ORDER BY c.comppct_r DESC, c.cokey
               ) AS rn
        FROM comp c
        INNER JOIN mu ON mu.mukey = c.mukey
    ),
    dom AS (
        SELECT mukey, cokey, comppct_r, compname, runoff,
               hydgrp, hydricon, hydricrating, drainagecl, geom
        FROM dom_comp
        WHERE rn = 1
    ),
    hz AS (
        SELECT mukey,
            CASE WHEN SUM(thk) = 0 THEN NULL
                 ELSE SUM(thk * ksat_l) / SUM(thk) END AS ksat_l,
            CASE WHEN SUM(thk) = 0 THEN NULL
                 ELSE SUM(thk * ksat_r) / SUM(thk) END AS ksat_r,
            CASE WHEN SUM(thk) = 0 THEN NULL
                 ELSE SUM(thk * ksat_h) / SUM(thk) END AS ksat_h
        FROM (
            SELECT
                d.mukey,
                h.ksat_l * {MICROMETERS_PER_SECOND_TO_MM_PER_HOUR} AS ksat_l,
                h.ksat_r * {MICROMETERS_PER_SECOND_TO_MM_PER_HOUR} AS ksat_r,
                h.ksat_h * {MICROMETERS_PER_SECOND_TO_MM_PER_HOUR} AS ksat_h,
                CASE
                    WHEN h.hzdept_r IS NULL OR h.hzdepb_r IS NULL THEN 0
                    ELSE
                        CASE
                            WHEN (CASE WHEN h.hzdepb_r < {bottom} THEN h.hzdepb_r ELSE {bottom} END)
                                 - (CASE WHEN h.hzdept_r > {top} THEN h.hzdept_r ELSE {top} END) > 0
                            THEN (CASE WHEN h.hzdepb_r < {bottom} THEN h.hzdepb_r ELSE {bottom} END)
                                 - (CASE WHEN h.hzdept_r > {top} THEN h.hzdept_r ELSE {top} END)
                            ELSE 0
                        END
                END AS thk
            FROM dom d
            INNER JOIN horiz h ON h.cokey = d.cokey
        ) x
        GROUP BY mukey
    )
    SELECT
        d.geom,
        d.mukey,
        CAST(d.mukey AS INTEGER) AS mukey_int,
        d.cokey,
        d.compname,
        d.comppct_r,
        d.runoff,
        d.hydgrp,
        d.hydricon,
        d.hydricrating,
        d.drainagecl,
        hz.ksat_l,
        hz.ksat_r,
        hz.ksat_h
    FROM dom d
    LEFT JOIN hz ON hz.mukey = d.mukey
    """
    ksat_data = con.execute(query).fetchdf()
    if ksat_data.size == 0:
        gs.warning(_("No records found in your region."))
        return None

    try:
        output_layer = ssurgo_areas_out
        fd, tmp_filepath = tempfile.mkstemp(suffix=".fgb")

        # GRASS GDAL driver isn't supported by duckdb
        gs.message(f"Tempfile Path: {tmp_filepath}")

        export_sql = f"""
        COPY (
            {query.strip()}
        ) TO '{tmp_filepath}'
        (FORMAT GDAL, DRIVER 'FlatGeobuf', SRS 'EPSG:5070');
        """

        con.execute(export_sql)

        # Export to GRASS using GDAL/OGR_GRASS driver
        tempdir = tempfile.TemporaryDirectory()

        gs.create_project(path=tempdir.name, epsg=5070, overwrite=True)
        with gs.setup.init(Path(tempdir.name)) as temp_session:
            # Create a new GRASS session for the temp dataset
            with Tools(session=temp_session) as t:
                gs.message("#" * 50)
                gs.message("Starting temp GRASS session for SSURGO import...")
                session_env = t.g_gisenv(
                    get="GISDBASE,LOCATION_NAME,MAPSET", sep="/"
                ).text
                gs.debug(f"Temp Session info: {session_env}")
                t.v_in_ogr(
                    input=tmp_filepath,
                    output=output_layer,
                    type="boundary",
                    snap=1e-7,
                    flags="",
                )

                new_vect = t.g_list(type="vector", format="json").json
                gs.debug(f"Temp Session Vectors: {new_vect}")

            gs.debug("#" * 50)
            tmp_project_name = Path(tempdir.name).name
            gs.debug(f"Project Name: {tmp_project_name}")
            tmp_dbpath = Path(tempdir.name).parent
            gs.debug(f"Temp DB Path: {tmp_dbpath}")

        with gs.setup.init(Path(SESSION)) as session:
            gs.debug(f"Original Session info: {session}")
            with Tools(session=session) as tools:
                gs.message("Reprojecting ssurgo data...")

                tools.v_proj(
                    project=tmp_project_name,
                    input=output_layer,
                    dbase=tmp_dbpath,
                    mapset="PERMANENT",
                    output=output_layer,
                    verbose=False,
                )

    except CalledModuleError as e:
        gs.fatal(f"Import failed: {e}")

    except Exception as e:
        gs.fatal(f"An error occurred: {e}")

    finally:
        gs.debug("cleaning up temp project")
        tempdir.cleanup()
        gs.debug(f"Tempfile Name: {tmp_filepath=}")
        os.close(fd)
        os.remove(tmp_filepath)
        gs.debug("cleaned up temp FlatGeoBuff")

    return output_layer


def _rasterize_and_style(ssurgo_areas, hydgrp, ksat_h, ksat_r, ksat_l, mukey):
    """Convert imported SSURGO vector attributes to raster maps and apply color schemes.

    :param str ssurgo_areas: Name of the imported SSURGO vector map.
    :param str hydgrp: Output name for hydrologic soil group raster (or empty to skip).
    :param str ksat_h: Output name for Ksat high raster (or empty to skip).
    :param str ksat_r: Output name for Ksat regular raster (or empty to skip).
    :param str ksat_l: Output name for Ksat low raster (or empty to skip).
    :param str mukey: Output name for map unit key raster (or empty to skip).
    """
    with gs.setup.init(Path(SESSION)) as session:
        with Tools(session=session) as stools:
            update_hydrologic_group(stools, ssurgo_areas)
            _output_maps = [
                ("hsg", hydgrp, "hydgrp"),
                ("ksat_h", ksat_h, None),
                ("ksat_r", ksat_r, None),
                ("ksat_l", ksat_l, None),
                ("mukey_int", mukey, None),
            ]
            for col, map_name, label_column in _output_maps:
                if not map_name:
                    continue

                stools.v_to_rast(
                    input=ssurgo_areas,
                    type="area",
                    use="attr",
                    attribute_column=col,
                    output=map_name,
                    label_column=label_column if label_column else "",
                )

                if col in ("ksat_l", "ksat_r", "ksat_h"):
                    ksat_color_scheme(map_name)

                if col == "mukey_int":
                    stools.r_colors(map=map_name, color="random")

                if col == "hsg":
                    hydrologic_soil_group_categories(map_name)
                    hydrologic_soil_group_color_scheme(map_name)


def _parse_wkt_coordinates(coord_string):
    """Parse a WKT coordinate string into a list of coordinate pairs.

    :param str coord_string: Comma-separated coordinate pairs, e.g. ``"x1 y1, x2 y2"``.
    :return: List of ``[x, y]`` pairs.
    :rtype: list[list[float]]
    """
    coords = []
    for pair in coord_string.strip().split(","):
        parts = pair.strip().split()
        if len(parts) >= 2:
            coords.append([float(parts[0]), float(parts[1])])
    return coords


def _wkt_to_geojson_geometry(wkt_str):
    """Convert a WKT POLYGON or MULTIPOLYGON string to a GeoJSON geometry dict.

    :param str wkt_str: Well-Known Text geometry string (WGS 84).
    :return: GeoJSON geometry dict or None if unsupported type.
    :rtype: dict or None
    """
    wkt_str = wkt_str.strip()
    upper = wkt_str.upper()

    # Regex matching the innermost parenthesised coordinate groups
    ring_re = re.compile(r"\(\s*([^()]+?)\s*\)")

    if upper.startswith("MULTIPOLYGON"):
        body = wkt_str[len("MULTIPOLYGON") :].strip()
        # Remove outermost parens
        body = body[1:-1].strip()

        # Split polygon groups at depth-0 commas
        polygon_strings = []
        depth = 0
        start = 0
        for i, ch in enumerate(body):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                polygon_strings.append(body[start:i].strip())
                start = i + 1
        polygon_strings.append(body[start:].strip())

        mp_coords = []
        for pstr in polygon_strings:
            rings = [_parse_wkt_coordinates(m.group(1)) for m in ring_re.finditer(pstr)]
            if rings:
                mp_coords.append(rings)

        return {"type": "MultiPolygon", "coordinates": mp_coords}

    if upper.startswith("POLYGON"):
        body = wkt_str[len("POLYGON") :].strip()
        rings = [_parse_wkt_coordinates(m.group(1)) for m in ring_re.finditer(body)]
        return {"type": "Polygon", "coordinates": rings}

    gs.warning(_("Unsupported WKT geometry type, skipping."))
    return None


def sda_ssurgo_query(
    aoi_wkt,
    desgnmaster,
    hzdept_r,
    hzdepb_r,
    ssurgo_areas_out,
):
    """Import SSURGO data from the Soil Data Access (SDA) web service.

    Fetches soil polygon geometry and attribute data for the area of interest
    defined by *aoi_wkt* (WGS 84), writes the result to a temporary GeoJSON
    file, imports it into a temporary GRASS project, and reprojects into the
    current project.

    :param str aoi_wkt: WKT polygon of the area of interest in WGS 84.
    :param str desgnmaster: Designation of master horizon.
    :param int hzdept_r: Horizon depth top (cm).
    :param int hzdepb_r: Horizon depth bottom (cm).
    :param str ssurgo_areas_out: Name for the output vector map.
    :return: Name of the imported vector map or None on failure.
    :rtype: str or None
    """
    client = SDAClient()
    results = client.fetch_sda(
        aoi_wkt=aoi_wkt,
        top_cm=hzdept_r,
        bottom_cm=hzdepb_r,
        desgnmaster=desgnmaster,
        agg=SoilAggMethod.DOMINANT_COMPONENT,
    )

    if not results or "Table" not in results:
        gs.fatal(_("No records returned from Soil Data Access (SDA)."))
        return None

    rows = results["Table"]
    if not rows:
        gs.fatal(_("SDA query returned empty results for the current region."))
        return None

    gs.message(_("Received {} records from SDA.").format(len(rows)))

    # Build GeoJSON FeatureCollection from SDA response
    features = []
    for row in rows:
        wkt = row.get("wkt")
        if not wkt:
            continue
        geom = _wkt_to_geojson_geometry(wkt)
        if geom is None:
            continue
        properties = {}
        for key, val in row.items():
            if key == "wkt":
                continue
            # Convert numeric strings to appropriate Python types
            if val is None or val == "":
                properties[key] = None
            else:
                try:
                    if "." in str(val):
                        properties[key] = float(val)
                    else:
                        properties[key] = int(val)
                except (ValueError, TypeError):
                    properties[key] = val
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": properties,
            }
        )

    if not features:
        gs.fatal(_("No valid geometries found in SDA response."))
        return None

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Write GeoJSON to temporary file and import into GRASS
    fd, geojson_path = tempfile.mkstemp(suffix=".geojson")
    tempdir = tempfile.TemporaryDirectory()
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(geojson, f)

        # Import into temporary GRASS project in WGS 84 (EPSG:4326)
        gs.create_project(path=tempdir.name, epsg=4326, overwrite=True)
        with gs.setup.init(Path(tempdir.name)) as temp_session:
            with Tools(session=temp_session) as t:
                gs.message(_("Importing SDA data into temporary project..."))
                t.v_in_ogr(
                    input=geojson_path,
                    output=ssurgo_areas_out,
                    type="boundary",
                    snap=1e-6,
                )

        # Reproject from temporary WGS 84 project to the current project
        tmp_project_name = Path(tempdir.name).name
        tmp_dbpath = Path(tempdir.name).parent

        with gs.setup.init(Path(SESSION)) as session:
            with Tools(session=session) as stools:
                gs.message(_("Reprojecting SDA data to current project..."))
                stools.v_proj(
                    project=tmp_project_name,
                    input=ssurgo_areas_out,
                    dbase=tmp_dbpath,
                    mapset="PERMANENT",
                    output=ssurgo_areas_out,
                )

    except CalledModuleError as e:
        gs.fatal(_("SDA import failed: {}").format(e))

    finally:
        tempdir.cleanup()
        if os.path.exists(geojson_path):
            os.remove(geojson_path)

    return ssurgo_areas_out


class SoilAggMethod(Enum):
    DOMINANT_COMPONENT = "dominant_component"
    WEIGHTED_COMPONENT = "weighted_component"


class SDAClient:
    """
    Client for interacting with the Soil Data Access (SDA) database.

    This class provides methods to execute SQL queries against the SDA database
    and retrieve soil data based on specified parameters.
    """

    REST_URL = "https://sdmdataaccess.sc.egov.usda.gov/tabular/post.rest"

    def _build_sda_sql(
        self,
        aoi_wkt,
        top_cm: int,
        bottom_cm: int,
        desgnmaster: str = "A",
        agg: SoilAggMethod = SoilAggMethod.DOMINANT_COMPONENT,
    ):
        """
        Build a T-SQL batch that:

        1. Finds intersecting mukeys from an AOI WKT (WGS 84).
        2. Picks the dominant component per mukey.
        3. Aggregates depth-weighted Ksat (low, representative, high) in mm/hr.
        4. Returns mupolygon WKT, mukey, component attributes, and Ksat values.

        :param str aoi_wkt: WKT polygon (WGS 84) of the area of interest.
        :param int top_cm: Horizon depth top (cm).
        :param int bottom_cm: Horizon depth bottom (cm).
        :param str desgnmaster: Master horizon designation filter (default ``'A'``).
        :param SoilAggMethod agg: Aggregation method.
        :return: T-SQL query string.
        :rtype: str
        """
        top = float(top_cm)
        bottom = float(bottom_cm)
        conv = MICROMETERS_PER_SECOND_TO_MM_PER_HOUR

        if agg == SoilAggMethod.DOMINANT_COMPONENT:
            sql = f"""
            WITH mu AS (
              SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{aoi_wkt}')
            ),
            dom_comp AS (
              SELECT c.mukey, c.cokey, c.comppct_r, c.compname,
                     c.hydgrp, c.drainagecl,
                     ROW_NUMBER() OVER (
                       PARTITION BY c.mukey
                       ORDER BY c.comppct_r DESC, c.cokey
                     ) AS rn
              FROM component c
              INNER JOIN mu ON mu.mukey = c.mukey
              WHERE c.comppct_r IS NOT NULL
            ),
            dom AS (
              SELECT mukey, cokey, comppct_r, compname, hydgrp, drainagecl
              FROM dom_comp WHERE rn = 1
            ),
            hz AS (
              SELECT x.mukey,
                CASE WHEN SUM(x.thk) = 0 THEN NULL
                     ELSE SUM(x.thk * x.ksat_l) / SUM(x.thk) END AS ksat_l,
                CASE WHEN SUM(x.thk) = 0 THEN NULL
                     ELSE SUM(x.thk * x.ksat_r) / SUM(x.thk) END AS ksat_r,
                CASE WHEN SUM(x.thk) = 0 THEN NULL
                     ELSE SUM(x.thk * x.ksat_h) / SUM(x.thk) END AS ksat_h
              FROM (
                SELECT d.mukey,
                  h.ksat_l * {conv} AS ksat_l,
                  h.ksat_r * {conv} AS ksat_r,
                  h.ksat_h * {conv} AS ksat_h,
                  CASE
                    WHEN h.hzdept_r IS NULL OR h.hzdepb_r IS NULL THEN 0
                    ELSE
                      CASE
                        WHEN (CASE WHEN h.hzdepb_r < {bottom} THEN h.hzdepb_r
                                   ELSE {bottom} END)
                           - (CASE WHEN h.hzdept_r > {top} THEN h.hzdept_r
                                   ELSE {top} END) > 0
                        THEN (CASE WHEN h.hzdepb_r < {bottom} THEN h.hzdepb_r
                                   ELSE {bottom} END)
                           - (CASE WHEN h.hzdept_r > {top} THEN h.hzdept_r
                                   ELSE {top} END)
                        ELSE 0
                      END
                  END AS thk
                FROM dom d
                INNER JOIN chorizon h ON h.cokey = d.cokey
                WHERE h.ksat_r IS NOT NULL
                  AND h.hzdept_r = 0
                  AND h.hzdepb_r > 0
                  AND h.desgnmaster = '{desgnmaster}'
              ) x
              GROUP BY x.mukey
            ),
            poly AS (
              SELECT t.mukey, p.MupolygonWktWgs84 AS wkt
              FROM (SELECT mukey FROM mu) t
              CROSS APPLY SDA_Get_MupolygonWktWgs84_from_Mukey(t.mukey) p
            )
            SELECT poly.mukey,
                   CAST(poly.mukey AS INT) AS mukey_int,
                   dom.compname,
                   dom.comppct_r,
                   dom.hydgrp,
                   dom.drainagecl,
                   hz.ksat_l,
                   hz.ksat_r,
                   hz.ksat_h,
                   poly.wkt
            FROM poly
            LEFT JOIN dom ON dom.mukey = poly.mukey
            LEFT JOIN hz ON hz.mukey = poly.mukey
            """
        else:
            # weighted_component
            sql = f"""
            WITH mu AS (
              SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{aoi_wkt}')
            ),
            comp AS (
              SELECT c.mukey, c.cokey, c.comppct_r
              FROM component c
              INNER JOIN mu ON mu.mukey = c.mukey
              WHERE c.comppct_r IS NOT NULL
            ),
            -- pick dominant component for categorical attributes (hydgrp, etc.)
            dom_comp AS (
              SELECT c.mukey, c.compname, c.hydgrp, c.drainagecl,
                     ROW_NUMBER() OVER (
                       PARTITION BY c.mukey
                       ORDER BY c.comppct_r DESC, c.cokey
                     ) AS rn
              FROM component c
              INNER JOIN mu ON mu.mukey = c.mukey
              WHERE c.comppct_r IS NOT NULL
            ),
            dom AS (
              SELECT mukey, compname, hydgrp, drainagecl
              FROM dom_comp WHERE rn = 1
            ),
            comp_hz AS (
              SELECT z.mukey, z.cokey, z.comppct_r,
                CASE WHEN SUM(z.thk) = 0 THEN NULL
                     ELSE SUM(z.thk * z.ksat_l) / SUM(z.thk) END AS ksat_l_comp,
                CASE WHEN SUM(z.thk) = 0 THEN NULL
                     ELSE SUM(z.thk * z.ksat_r) / SUM(z.thk) END AS ksat_r_comp,
                CASE WHEN SUM(z.thk) = 0 THEN NULL
                     ELSE SUM(z.thk * z.ksat_h) / SUM(z.thk) END AS ksat_h_comp
              FROM (
                SELECT c.mukey, c.cokey, c.comppct_r,
                  h.ksat_l * {conv} AS ksat_l,
                  h.ksat_r * {conv} AS ksat_r,
                  h.ksat_h * {conv} AS ksat_h,
                  CASE
                    WHEN h.hzdept_r IS NULL OR h.hzdepb_r IS NULL THEN 0
                    ELSE
                      CASE
                        WHEN (CASE WHEN h.hzdepb_r < {bottom} THEN h.hzdepb_r
                                   ELSE {bottom} END)
                           - (CASE WHEN h.hzdept_r > {top} THEN h.hzdept_r
                                   ELSE {top} END) > 0
                        THEN (CASE WHEN h.hzdepb_r < {bottom} THEN h.hzdepb_r
                                   ELSE {bottom} END)
                           - (CASE WHEN h.hzdept_r > {top} THEN h.hzdept_r
                                   ELSE {top} END)
                        ELSE 0
                      END
                  END AS thk
                FROM comp c
                INNER JOIN chorizon h ON h.cokey = c.cokey
                WHERE h.ksat_r IS NOT NULL
                  AND h.hzdept_r = 0
                  AND h.hzdepb_r > 0
                  AND h.desgnmaster = '{desgnmaster}'
              ) z
              GROUP BY z.mukey, z.cokey, z.comppct_r
            ),
            hz AS (
              SELECT mukey,
                CASE WHEN SUM(comppct_r) = 0 THEN NULL
                     ELSE SUM(comppct_r * ksat_l_comp) / SUM(comppct_r) END AS ksat_l,
                CASE WHEN SUM(comppct_r) = 0 THEN NULL
                     ELSE SUM(comppct_r * ksat_r_comp) / SUM(comppct_r) END AS ksat_r,
                CASE WHEN SUM(comppct_r) = 0 THEN NULL
                     ELSE SUM(comppct_r * ksat_h_comp) / SUM(comppct_r) END AS ksat_h
              FROM comp_hz
              WHERE ksat_r_comp IS NOT NULL
              GROUP BY mukey
            ),
            poly AS (
              SELECT t.mukey, p.MupolygonWktWgs84 AS wkt
              FROM (SELECT mukey FROM mu) t
              CROSS APPLY SDA_Get_MupolygonWktWgs84_from_Mukey(t.mukey) p
            )
            SELECT poly.mukey,
                   CAST(poly.mukey AS INT) AS mukey_int,
                   dom.compname,
                   dom.hydgrp,
                   dom.drainagecl,
                   hz.ksat_l,
                   hz.ksat_r,
                   hz.ksat_h,
                   poly.wkt
            FROM poly
            LEFT JOIN dom ON dom.mukey = poly.mukey
            LEFT JOIN hz ON hz.mukey = poly.mukey
            """

        return textwrap.dedent(sql).strip()

    def _sda_post_sql(self, sql, sda_url=None, timeout=120):
        """
        POST SQL to SDA post.rest endpoint and return parsed JSON.

        The response is converted so that ``result["Table"]`` is a list of
        dicts keyed by column name, which matches the format expected by
        the rest of the pipeline.

        :param str sql: T-SQL query string.
        :param str sda_url: SDA REST URL (defaults to *REST_URL*).
        :param int timeout: HTTP request timeout in seconds.
        :return: Parsed JSON response dict with ``{"Table": [row_dict, ...]}``.
        :rtype: dict
        """
        if sda_url is None:
            sda_url = self.REST_URL
        form_data = urlencode({"QUERY": sql, "FORMAT": "JSON+COLUMNNAME"})
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        req = Request(
            sda_url, data=form_data.encode("utf-8"), headers=headers, method="POST"
        )
        gs.debug(_("SDA request URL: {}").format(sda_url))
        try:
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                result = json.loads(raw)
        except HTTPError as e:
            gs.fatal(
                _("SDA HTTP error {code}: {reason}").format(
                    code=e.code, reason=e.reason
                )
            )
            return None
        except URLError as e:
            gs.fatal(_("SDA connection error: {}").format(e.reason))
            return None
        except json.JSONDecodeError:
            gs.fatal(
                _(
                    "SDA did not return valid JSON. "
                    "Check the service status or query syntax."
                )
            )
            return None

        # Convert JSON+COLUMNNAME array format to list of dicts.
        # First row = column names, remaining rows = data.
        table = result.get("Table")
        if not table or len(table) < 2:
            return result
        columns = table[0]
        result["Table"] = [dict(zip(columns, row)) for row in table[1:]]
        return result

    def fetch_sda(
        self,
        aoi_wkt,
        top_cm: int,
        bottom_cm: int,
        desgnmaster: str = "A",
        agg: SoilAggMethod = SoilAggMethod.DOMINANT_COMPONENT,
    ):
        """Fetch SSURGO data from SDA for the given area of interest.

        :param str aoi_wkt: WKT polygon of the AOI in WGS 84.
        :param int top_cm: Horizon depth top (cm).
        :param int bottom_cm: Horizon depth bottom (cm).
        :param str desgnmaster: Master horizon designation filter.
        :param SoilAggMethod agg: Aggregation method.
        :return: Parsed JSON response from SDA containing a ``Table`` key.
        :rtype: dict or None
        """
        gs.debug(_("SDAClient.fetch_sda: building SQL query..."))
        sql = self._build_sda_sql(aoi_wkt, top_cm, bottom_cm, desgnmaster, agg)
        gs.debug(_("SDAClient.fetch_sda: SQL built, querying SDA..."))
        result = self._sda_post_sql(sql)
        gs.debug(_("SDAClient.fetch_sda: received response from SDA."))
        return result


def main():
    # Inputs
    ssurgo_path = options["ssurgo_path"]

    # TODO: Add ability to specify different Horizons
    desgnmaster = options["desgnmaster"]
    hzdept_r = int(options["hzdept_r"])
    hzdepb_r = int(options["hzdepb_r"]) if options["hzdepb_r"] else 25
    flag_d = flags["d"]

    # Outputs
    ###################################################
    # Raster outputs
    hydgrp = options["hydgrp"]
    ksat_h = options["ksat_h"]
    ksat_r = options["ksat_r"]
    ksat_l = options["ksat_l"]
    mukey = options["mukey"]

    # Vector outputs
    ssurgo_areas = options["ssurgo_areas"]

    # TODO: Add raster3d output option for depth-varying Ksat

    # Processing options
    nprocs = int(options["nprocs"])  # optional

    # Error if no duckdb and flag d is not set.
    if not flag_d:
        _import_duckdb(error=True)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tif_path = tmp.name

        try:
            if flag_d:
                gs.message(
                    _(
                        "Using Soil Data Access (SDA) to query and download "
                        "data for the current computational region."
                    )
                )
                aoi_wkt = region_to_wkt_wgs84()
                ssurgo_areas = sda_ssurgo_query(
                    aoi_wkt=aoi_wkt,
                    desgnmaster=desgnmaster,
                    hzdept_r=hzdept_r,
                    hzdepb_r=hzdepb_r,
                    ssurgo_areas_out=ssurgo_areas,
                )
                if ssurgo_areas:
                    _rasterize_and_style(
                        ssurgo_areas, hydgrp, ksat_h, ksat_r, ksat_l, mukey
                    )
            else:
                gs.message(_("Importing SSURGO data from local file."))
                _ssurgo_path = check_if_zipfile(Path(ssurgo_path))
                wkt_bbox = region_to_crs_wkt(target_crs="EPSG:5070")
                con = connect_duckdb(threads=nprocs)
                ssurgo_areas = local_ssurgo_query(
                    con=con,
                    wkt_bbox=wkt_bbox,
                    ssurgo_path=_ssurgo_path,
                    desgnmaster=desgnmaster,
                    hzdept_r=hzdept_r,
                    hzdepb_r=hzdepb_r,
                    hydgrp_out=hydgrp,
                    ksat_h_out=ksat_h,
                    ksat_r_out=ksat_r,
                    ksat_l_out=ksat_l,
                    mukey_out=mukey,
                    ssurgo_areas_out=ssurgo_areas,
                )
                if ssurgo_areas:
                    _rasterize_and_style(
                        ssurgo_areas, hydgrp, ksat_h, ksat_r, ksat_l, mukey
                    )
        finally:
            if os.path.exists(tif_path):
                os.remove(tif_path)


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
