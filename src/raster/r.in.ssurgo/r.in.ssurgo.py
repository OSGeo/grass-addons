#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.in.ssurgo
# AUTHOR:       Corey T. White, GeoForAll Lab, NCSU
# PURPOSE:      Download and import SSURGO data
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

# %option G_OPT_V_OUTPUT
# % key: soils
# % description: Name for output soil vecotor layer containing the source SSURGO map unit polygons and attributes.
# % guisection: Outputs
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: hydgrp
# % description: Hydrologic soil group (HSG) raster map output
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
# % key: s
# % description: Force the SQLite/OGR backend for local SSURGO import (skip DuckDB)
# %end

from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile
import grass.script as gs
from grass.exceptions import CalledModuleError
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


# Unit conversion constant
MICROMETERS_PER_SECOND_TO_MM_PER_HOUR = 3.6


class SoilAggMethod(Enum):
    DOMINANT_COMPONENT = "dominant_component"
    WEIGHTED_COMPONENT = "weighted_component"


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
    """Check if the provided file path is a ZIP file and construct /vsizip/ path."""
    # Check if the path exists
    absolute_path = file_path.resolve(strict=False)
    if not absolute_path.exists():
        raise FileNotFoundError(
            _("File not found: <{}> Parent: <{}>").format(
                absolute_path, file_path.parent
            )
        )
    # If it is a ZIP file, return the path prefixed with /vsizip/ for GDAL virtual file system access
    if absolute_path.suffix.lower() == ".zip":
        # Use zipfile to validate and handle the archive
        import zipfile

        # Verify it's a valid ZIP file
        if not zipfile.is_zipfile(absolute_path):
            raise ValueError(
                _(
                    "File <{}> appears to be corrupted or not a valid ZIP archive"
                ).format(file_path)
            )

        # Extract the base name without extension and append .gdb
        # gSSURGO_CONUS.zip -> /vsizip//path/to/gSSURGO_CONUS.zip/gSSURGO_CONUS.gdb
        # This allows users to point to the zip file directly and we can handle the internal pathing.
        base_name = absolute_path.stem
        gdb_name = f"{base_name}.gdb/"

        # Construct the /vsizip/ path - note: use str() to avoid Path issues with /vsizip/
        vsizip_path = f"/vsizip/{absolute_path}/{gdb_name}"
        gs.message(_("Expected gdb path within ZIP: %s") % vsizip_path)

        # Verify the .gdb directory exists within the ZIP archive
        with zipfile.ZipFile(absolute_path, "r") as zip_ref:
            zip_contents = zip_ref.namelist()
            # Check if any file starts with gdb_name/ (indicating a directory)
            gdb_found = any(
                name.startswith(f"{gdb_name}") or name == f"{gdb_name}"
                for name in zip_contents
            )
            if gdb_found:
                return vsizip_path
            else:
                raise ValueError(
                    _(
                        "Expected geodatabase directory <{}> not found in ZIP archive <{}>"
                    ).format(gdb_name, absolute_path)
                )

    return absolute_path


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
    gs.write_command(
        "r.category",
        map=map_name,
        rules="-",
        separator="pipe",
        stdin=rules_str,
    )


def hydrologic_soil_group_color_scheme(map_name: str) -> None:
    """Apply hydrologic soil group color scheme to elevation map."""
    gs.verbose(_("Applying hydrologic soil group color scheme..."))
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
    # Convert palette list to rules string for r.colors
    hydgrp_color_scheme = (
        "\n".join(f"{pos} {color}" for pos, color in hydgrp_color_palette) + "\n"
    )
    gs.write_command(
        "r.colors",
        map=map_name,
        rules="-",
        stdin=hydgrp_color_scheme,
    )


def ksat_color_scheme(map_name: str) -> None:
    """Apply ksat color scheme to elevation map."""
    gs.verbose(_("Applying ksat color scheme..."))
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
    # Convert palette list to rules string for r.colors
    ksat_color_scheme = (
        "\n".join(f"{pos} {color}" for pos, color in ksat_color_palette) + "\n"
    )
    gs.write_command(
        "r.colors",
        map=map_name,
        rules="-",
        stdin=ksat_color_scheme,
    )


def update_hydrologic_group(vector_map, source_col="hydgrp", target_col="hsg"):
    """
    Ensure an integer Hydrologic Soil Group (HSG) column exists on the vector and populate it from source_col.
    Mapping:
      A->1, B->2, C->3, D->4
      A/D->11, B/D->12, C/D->13, D/D->14 (dual drained/undrained codes)
    Skips unknown/ambiguous codes.
    """
    # Ensure target column exists. parse_command already parses JSON output
    # when format="json" is requested, so use the returned list directly.
    cols = gs.parse_command("v.info", map=vector_map, format="json", flags="c")
    col_names = [c["name"] for c in cols]
    if target_col not in col_names:
        gs.run_command(
            "v.db.addcolumn", map=vector_map, columns=f"{target_col} INTEGER"
        )

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
        gs.run_command(
            "v.db.update",
            map=vector_map,
            column=target_col,
            value=str(num),
            where=where,
        )

    # Optionally set unmatched values to NULL (skip here) or 0:
    gs.run_command(
        "v.db.update",
        map=vector_map,
        column=target_col,
        value="NULL",
        where=f"{target_col} IS NULL",
    )

    return target_col


def local_ssurgo_query(
    con,
    tmp_filepath,
    wkt_bbox,
    ssurgo_path,
    desgnmaster,
    hzdept_r,
    hzdepb_r,
    agg: SoilAggMethod = SoilAggMethod.DOMINANT_COMPONENT,
):
    """
    Import SSURGO data from a local ZIP file.

    This function processes a local SSURGO ZIP file, extracts the relevant soil data based on the specified parameters,
    and outputs the desired raster and vector layers.

    Args:
        con (duckdb.Connection): An active connection to a DuckDB database with the spatial extension loaded.
        tmp_filepath (str): Path to a temporary file for intermediate data storage.
        wkt_bbox (str): WKT polygon representing the bounding box.
        ssurgo_path (str): Path to the local SSURGO file.
        desgnmaster (str): Designation of master horizon.
        hzdept_r (int): Horizon depth top (cm).
        hzdepb_r (int): Horizon depth bottom (cm).
        agg (SoilAggMethod): Aggregation method.
    Returns:
        None: This function does not return any value. It creates raster and vector layers in the GRASS environment.
    """
    conv = MICROMETERS_PER_SECOND_TO_MM_PER_HOUR
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
    # texture: Texture class based on particle size distribution

    # Materialise each SSURGO layer into temporary tables so that
    # DuckDB can build indexes and avoid repeated full-file scans.
    gs.message(_("Loading SSURGO layers into memory..."))

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE mu AS
        SELECT mukey, shape AS geom
        FROM ST_Read(
            $ssurgo_path,
            layer = 'MUPOLYGON',
            spatial_filter =
                ST_AsWKB(ST_GeomFromText($wkt_bbox))
        )
        """,
        {"ssurgo_path": ssurgo_path, "wkt_bbox": wkt_bbox},
    )
    mu_count = con.execute("SELECT count(*) FROM mu").fetchone()[0]
    gs.message(_("Loaded %d map unit polygons.") % mu_count)

    con.execute("CREATE INDEX mu_idx ON mu USING RTREE (geom);")
    gs.message(_("Created spatial index on map unit polygons."))

    # Load component and chorizon once; join-filter by mukey list
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE comp AS
        SELECT c.*
        FROM ST_Read($1, layer = 'component') AS c
        WHERE c.mukey IN (SELECT mukey FROM mu)
        AND c.comppct_r IS NOT NULL
        """,
        [ssurgo_path],
    )

    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE horiz AS
        SELECT h.*
        FROM ST_Read($1, layer = 'chorizon') AS h
        WHERE h.cokey IN (SELECT cokey FROM comp)
        """,
        [ssurgo_path],
    )
    gs.message(_("SSURGO layers loaded. Running analysis query..."))
    if mu_count == 0:
        gs.warning(_("No records found in your region."))
        return None

    if agg == SoilAggMethod.DOMINANT_COMPONENT:
        gs.message(_("Using dominant component aggregation method."))
        # Dominant component aggregation method:
        query = f"""
        WITH dom_comp AS (
            SELECT
                c.mukey,
                c.cokey,
                c.comppct_r,
                c.hydgrp,
                ROW_NUMBER() OVER (
                    PARTITION BY c.mukey
                    ORDER BY c.comppct_r DESC, c.cokey
                ) AS rn
            FROM comp c
            INNER JOIN mu ON mu.mukey = c.mukey
            WHERE c.comppct_r IS NOT NULL
        ),
        dom AS (
            SELECT mukey, cokey, comppct_r, hydgrp
            FROM dom_comp
            WHERE rn = 1
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
                        WHEN h.hzdept_r IS NULL OR h.hzdepb_r IS NULL
                            THEN 0
                        ELSE
                            CASE
                                WHEN (
                                    CASE
                                        WHEN h.hzdepb_r < {bottom}
                                            THEN h.hzdepb_r
                                        ELSE {bottom}
                                    END
                                )
                                - (
                                    CASE
                                        WHEN h.hzdept_r > {top}
                                            THEN h.hzdept_r
                                        ELSE {top}
                                    END
                                ) > 0
                                THEN (
                                    CASE
                                        WHEN h.hzdepb_r < {bottom}
                                            THEN h.hzdepb_r
                                        ELSE {bottom}
                                    END
                                    )
                                    - (
                                        CASE
                                            WHEN h.hzdept_r > {top}
                                                THEN h.hzdept_r
                                            ELSE {top}
                                        END
                                    )
                                ELSE 0
                            END
                    END AS thk
                FROM dom d
                INNER JOIN horiz h ON h.cokey = d.cokey
                WHERE h.ksat_r IS NOT NULL
                  AND h.hzdept_r = 0
                  AND h.hzdepb_r > 0
                  AND h.desgnmaster = '{desgnmaster}'
            ) x
            GROUP BY x.mukey
        )
        SELECT mu.mukey,
            CAST(mu.mukey AS INTEGER) AS mukey_int,
            d.cokey,
            d.comppct_r,
            d.hydgrp,
            hz.ksat_l,
            hz.ksat_r,
            hz.ksat_h,
            mu.geom
        FROM mu
        LEFT JOIN dom d ON d.mukey = mu.mukey
        LEFT JOIN hz ON hz.mukey  = mu.mukey
        """

    else:
        # weighted_component
        gs.message(_("Using dominant component aggregation method."))
        gs.warning(_("Weighted component aggregation method not yet implemented."))
        pass

    ssurgo_data = con.execute(query).fetchdf()
    if ssurgo_data.size == 0:
        gs.warning(_("No records found in your region."))
        return None

    try:
        export_sql = f"""
        COPY (
            {query.strip()}
        ) TO '{tmp_filepath}'
        (FORMAT GDAL, DRIVER 'FlatGeobuf', SRS 'EPSG:5070');
        """

        con.execute(export_sql)

    except Exception as e:
        gs.fatal(_("An error occurred: %s") % str(e))

    return tmp_filepath


def local_ssurgo_sqlite_query(
    tmp_filepath,
    ssurgo_path,
    desgnmaster,
    hzdept_r,
    hzdepb_r,
    agg: SoilAggMethod = SoilAggMethod.DOMINANT_COMPONENT,
):
    """Import SSURGO data from a local GDB using OGR and SQLite.

    This is a DuckDB-free alternative to :func:`local_ssurgo_query`.  It uses
    GDAL/OGR (already required by GRASS) to read layers from the GDB, Python's
    built-in :mod:`sqlite3` for the depth-weighted aggregation query, and OGR
    again to write the result as a FlatGeobuf file ready for
    :func:`write_ssurgo_to_grass`.

    Spatial filtering uses OGR's :meth:`SetSpatialFilterRect` on the
    ``MUPOLYGON`` layer.  Component and horizon records are fetched with
    batched ``ExecuteSQL`` calls on the GDB data source so that only the rows
    relevant to the current region are loaded into memory.

    Args:
        tmp_filepath (str): Path for the output FlatGeobuf file.
        ssurgo_path (str): Path to the SSURGO GDB or ``/vsizip/`` path.
        desgnmaster (str): Master horizon designation filter (e.g. ``'A'``).
        hzdept_r (int): Horizon depth top (cm).
        hzdepb_r (int): Horizon depth bottom (cm).
        agg (SoilAggMethod): Aggregation method.

    Returns:
        str or None: Path to the written FlatGeobuf file, or ``None`` on
        failure.
    """

    conv = MICROMETERS_PER_SECOND_TO_MM_PER_HOUR
    top = hzdept_r
    bottom = hzdepb_r

    # Parse bbox from WKT
    # west, south, east, north = region_to_crs_bbox("EPSG:5070")[:4]

    try:
        gs.run_command(
            "v.import",
            input=ssurgo_path,
            output="soils_polygons",
            layer="MUPOLYGON",
            extent="region",
            snap=1e-8,
            overwrite=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to import MUPOLYGON layer: %s") % str(e))

    try:
        gs.message(_("Creating tables for component and horizon data..."))
        ddl_create = """
        CREATE TABLE comp (
            cokey      TEXT PRIMARY KEY,
            mukey      TEXT,
            comppct_r  REAL,
            hydgrp     TEXT
        );
        CREATE TABLE horiz (
            chkey        TEXT,
            cokey        TEXT,
            hzdept_r     REAL,
            hzdepb_r     REAL,
            ksat_l       REAL,
            ksat_r       REAL,
            ksat_h       REAL,
            desgnmaster  TEXT
        );
        """
        gs.run_command("db.execute", sql=ddl_create, overwrite=True)
    except CalledModuleError as e:
        gs.fatal(_("Failed to create tables: %s") % str(e))

    # Import component table from GDB into a temporary GRASS table, then
    # insert only the rows whose mukey appears in the soils_polygons layer.
    gs.message(_("Loading component data from SSURGO GDB..."))
    try:
        gs.run_command(
            "db.in.ogr",
            input=ssurgo_path,
            db_table="component",
            output="_comp_tmp",
            key="cokey",
            overwrite=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to import component table: %s") % str(e))

    try:
        gs.run_command(
            "db.execute",
            sql=(
                "INSERT INTO comp (cokey, mukey, comppct_r, hydgrp) "
                "SELECT cokey, mukey, comppct_r, hydgrp "
                "FROM _comp_tmp "
                "WHERE mukey IN (SELECT mukey FROM soils_polygons) "
                "AND comppct_r IS NOT NULL"
            ),
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to populate comp table: %s") % str(e))
    finally:
        gs.run_command("db.execute", sql="DROP TABLE IF EXISTS _comp_tmp")

    comp_count = int(
        gs.read_command("db.select", sql="SELECT count(*) FROM comp", flags="c").strip()
    )
    gs.message(_("Loaded %d component records.") % comp_count)

    # Import chorizon table from GDB into a temporary table, then insert
    # only rows whose cokey appears in the comp table.
    gs.message(_("Loading horizon data from SSURGO GDB..."))
    try:
        gs.run_command(
            "db.in.ogr",
            input=ssurgo_path,
            db_table="chorizon",
            output="_horiz_tmp",
            overwrite=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to import chorizon table: %s") % str(e))

    try:
        gs.run_command(
            "db.execute",
            sql=(
                "INSERT INTO horiz "
                "(chkey, cokey, hzdept_r, hzdepb_r, ksat_l, ksat_r, ksat_h, desgnmaster) "
                "SELECT chkey, cokey, hzdept_r, hzdepb_r, ksat_l, ksat_r, ksat_h, desgnmaster "
                "FROM _horiz_tmp "
                "WHERE cokey IN (SELECT cokey FROM comp)"
            ),
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to populate horiz table: %s") % str(e))
    finally:
        gs.run_command("db.execute", sql="DROP TABLE IF EXISTS _horiz_tmp")

    horiz_count = int(
        gs.read_command(
            "db.select", sql="SELECT count(*) FROM horiz", flags="c"
        ).strip()
    )
    gs.message(_("Loaded %d horizon records.") % horiz_count)

    if agg != SoilAggMethod.DOMINANT_COMPONENT:
        gs.warning(
            _("Weighted component aggregation not yet implemented for SQLite query.")
        )
        return None

    gs.message(_("Running dominant component aggregation..."))

    # Add result columns to the soils_polygons attribute table
    try:
        gs.run_command(
            "v.db.addcolumn",
            map="soils_polygons",
            columns=(
                "mukey_int INTEGER,"
                "cokey TEXT,"
                "comppct_r REAL,"
                "hydgrp TEXT,"
                "ksat_l REAL,"
                "ksat_r REAL,"
                "ksat_h REAL"
            ),
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to add columns to soils_polygons: %s") % str(e))

    # Build per-mukey aggregation table using window functions (SQLite >= 3.25)
    gs.run_command("db.execute", sql="DROP TABLE IF EXISTS _agg_tmp")
    agg_sql = f"""
    CREATE TABLE _agg_tmp AS
    WITH dom_comp AS (
        SELECT c.mukey, c.cokey, c.comppct_r, c.hydgrp,
               ROW_NUMBER() OVER (
                   PARTITION BY c.mukey
                   ORDER BY c.comppct_r DESC, c.cokey
               ) AS rn
        FROM comp c
        WHERE c.comppct_r IS NOT NULL
    ),
    dom AS (
        SELECT mukey, cokey, comppct_r, hydgrp
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
                    ELSE MAX(0,
                        MIN(COALESCE(h.hzdepb_r, 0), {bottom}) -
                        MAX(COALESCE(h.hzdept_r, 0), {top})
                    )
                END AS thk
            FROM dom d
            INNER JOIN horiz h ON h.cokey = d.cokey
            WHERE h.ksat_r IS NOT NULL
              AND h.hzdept_r = 0
              AND h.hzdepb_r > 0
              AND h.desgnmaster = '{desgnmaster}'
        ) x
        GROUP BY x.mukey
    )
    SELECT dom.mukey,
        CAST(dom.mukey AS INTEGER) AS mukey_int,
        dom.cokey,
        dom.comppct_r,
        dom.hydgrp,
        hz.ksat_l,
        hz.ksat_r,
        hz.ksat_h
    FROM dom
    LEFT JOIN hz ON hz.mukey = dom.mukey
    """
    try:
        gs.run_command("db.execute", sql=agg_sql)
    except CalledModuleError as e:
        gs.fatal(_("Failed to create aggregation table: %s") % str(e))

    # Write aggregated values back into the soils_polygons attribute table
    try:
        gs.run_command(
            "db.execute",
            sql=(
                "UPDATE soils_polygons SET "
                "mukey_int = (SELECT mukey_int FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey), "
                "cokey     = (SELECT cokey     FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey), "
                "comppct_r = (SELECT comppct_r FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey), "
                "hydgrp    = (SELECT hydgrp    FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey), "
                "ksat_l    = (SELECT ksat_l    FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey), "
                "ksat_r    = (SELECT ksat_r    FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey), "
                "ksat_h    = (SELECT ksat_h    FROM _agg_tmp WHERE _agg_tmp.mukey = soils_polygons.mukey)"
            ),
        )
    except CalledModuleError as e:
        gs.fatal(
            _("Failed to update soils_polygons with aggregation results: %s") % str(e)
        )
    finally:
        gs.run_command("db.execute", sql="DROP TABLE IF EXISTS _agg_tmp")

    agg_count = int(
        gs.read_command(
            "db.select",
            sql="SELECT count(*) FROM soils_polygons WHERE ksat_r IS NOT NULL",
            flags="c",
        ).strip()
    )
    gs.message(_("Aggregation complete. %d features with ksat values.") % agg_count)

    # Export enriched soils_polygons to FlatGeobuf for write_ssurgo_to_grass
    gs.message(_("Writing results to FlatGeobuf..."))
    try:
        gs.run_command(
            "v.out.ogr",
            input="soils_polygons",
            output=tmp_filepath,
            format="FlatGeobuf",
            overwrite=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Failed to export soils_polygons to FlatGeobuf: %s") % str(e))
    return tmp_filepath


def _rasterize_and_style(ssurgo_areas, hydgrp, ksat_h, ksat_r, ksat_l, mukey):
    """Convert imported SSURGO vector attributes to raster maps and apply color schemes.

    :param str ssurgo_areas: Name of the imported SSURGO vector map.
    :param str hydgrp: Output name for hydrologic soil group raster (or empty to skip).
    :param str ksat_h: Output name for Ksat high raster (or empty to skip).
    :param str ksat_r: Output name for Ksat regular raster (or empty to skip).
    :param str ksat_l: Output name for Ksat low raster (or empty to skip).
    :param str mukey: Output name for map unit key raster (or empty to skip).
    """
    update_hydrologic_group(ssurgo_areas)
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

        gs.run_command(
            "v.to.rast",
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
            gs.run_command("r.colors", map=map_name, color="random")

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


def sda_ssurgo_query(aoi_wkt, tmp_fd, desgnmaster, hzdept_r, hzdepb_r):
    """Import SSURGO data from the Soil Data Access (SDA) web service.

    Fetches soil polygon geometry and attribute data for the area of interest
    defined by *aoi_wkt* (WGS 84), writes the result to a temporary GeoJSON
    file, imports it into a temporary GRASS project, and reprojects into the
    current project.

    :param str aoi_wkt: WKT polygon of the area of interest in WGS 84.
    :param int tmp_fd: File descriptor for a temporary file to write the GeoJSON output.
    :param str desgnmaster: Designation of master horizon.
    :param int hzdept_r: Horizon depth top (cm).
    :param int hzdepb_r: Horizon depth bottom (cm).
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
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(geojson, f)
    except Exception as e:
        gs.fatal(_("Failed to write GeoJSON to temporary file: %s") % e)
        return None


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
              SELECT DISTINCT mukey
              FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{aoi_wkt}')
            ),
            dom_comp AS (
              SELECT c.mukey,
                    c.cokey,
                    c.comppct_r,
                    c.hydgrp,
                    ROW_NUMBER() OVER (
                       PARTITION BY c.mukey
                       ORDER BY c.comppct_r DESC, c.cokey
                     ) AS rn
              FROM component c
              INNER JOIN mu ON mu.mukey = c.mukey
              WHERE c.comppct_r IS NOT NULL
            ),
            dom AS (
              SELECT mukey, cokey, comppct_r, hydgrp
              FROM dom_comp
              WHERE rn = 1
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
                    WHEN h.hzdept_r IS NULL OR h.hzdepb_r IS NULL
                        THEN 0
                    ELSE
                        CASE
                            WHEN (
                                CASE
                                    WHEN h.hzdepb_r < {bottom}
                                        THEN h.hzdepb_r
                                    ELSE {bottom}
                                END
                            )
                            - (
                                CASE
                                    WHEN h.hzdept_r > {top}
                                        THEN h.hzdept_r
                                    ELSE {top}
                                END
                            ) > 0
                            THEN (
                                CASE
                                    WHEN h.hzdepb_r < {bottom}
                                        THEN h.hzdepb_r
                                    ELSE {bottom}
                                END
                            )
                            - (
                                CASE
                                    WHEN h.hzdept_r > {top}
                                        THEN h.hzdept_r
                                    ELSE {top}
                                END
                            )
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
                   d.cokey,
                   d.comppct_r,
                   d.hydgrp,
                   hz.ksat_l,
                   hz.ksat_r,
                   hz.ksat_h,
                   poly.wkt
            FROM poly
            LEFT JOIN dom d ON d.mukey = poly.mukey
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


def write_ssurgo_to_grass(tmp_filepath, ssurgo_areas_out, src_srs: int):
    """Write SSURGO data to a GRASS vector layer.

    :param data: List of dicts containing SSURGO attributes and WKT geometry.
    :param ssurgo_areas_out: Name of the output GRASS vector map.
    :param src_srs: EPSG code of the input
           5070 for the FlatGeobuf file 4326 for the GeoJSON file.
    :return: Name of the created GRASS vector map.
    """

    try:
        # Create temporary GRASS project for the source data
        tempdir = tempfile.TemporaryDirectory()
        tmp_project_name = Path(tempdir.name).name
        tmp_dbpath = Path(tempdir.name).parent

        # Import data into temporary GRASS project. Pass an isolated env so
        # that the temp session's GISRC/GIS_LOCK are confined to a copy and
        # the caller's global GRASS session remains intact when the context
        # exits (gs.setup.init's finish() deletes GISRC from the env it was
        # given — which would otherwise be os.environ).
        gs.create_project(path=tempdir.name, epsg=src_srs, overwrite=True)
        with gs.setup.init(Path(tempdir.name), env=os.environ.copy()) as temp_session:
            gs.message(_("Importing data into temporary project..."))
            gs.run_command(
                "v.in.ogr",
                input=tmp_filepath,
                output=ssurgo_areas_out,
                type="boundary",
                snap=1e-8,
                env=temp_session.env,
            )

        # Reproject from temporary project to the current (already active) project.
        # Do NOT wrap in `gs.setup.init(SESSION)` — exiting that context tears
        # down GISRC for the calling session.
        gs.message(_("Reprojecting data to current project..."))
        gs.run_command(
            "v.proj",
            project=tmp_project_name,
            input=ssurgo_areas_out,
            dbase=str(tmp_dbpath),
            mapset="PERMANENT",
            output=ssurgo_areas_out,
        )

        # Clip reprojected polygons to the current computational region.
        # -r: clip by region (no clip map needed)
        gs.message(_("Clipping output to current computational region..."))
        clipped_name = f"{ssurgo_areas_out}_clipped"
        gs.run_command(
            "v.clip",
            input=ssurgo_areas_out,
            output=clipped_name,
            flags="r",
            overwrite=True,
        )
        gs.run_command(
            "g.remove",
            type="vector",
            name=ssurgo_areas_out,
            flags="f",
        )
        gs.run_command(
            "g.rename",
            vector=f"{clipped_name},{ssurgo_areas_out}",
        )

    except CalledModuleError as e:
        gs.fatal(_("GRASS module error during data import: %s") % e)

    finally:
        gs.debug("cleaning up temp project")
        tempdir.cleanup()
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
            gs.debug(f"Removed temp file: {tmp_filepath}")

    return ssurgo_areas_out


def main():
    # Inputs
    ssurgo_path = options["ssurgo_path"]

    # TODO: Add ability to specify different Horizons
    desgnmaster = options["desgnmaster"]
    hzdept_r = int(options["hzdept_r"])
    hzdepb_r = int(options["hzdepb_r"]) if options["hzdepb_r"] else 25

    # Outputs
    ###################################################
    # Raster outputs
    hydgrp = options["hydgrp"]
    ksat_h = options["ksat_h"]
    ksat_r = options["ksat_r"]
    ksat_l = options["ksat_l"]
    mukey = options["mukey"]

    # Vector outputs
    ssurgo_areas = options["soils"]

    # TODO: Add raster3d output option for depth-varying Ksat

    # Processing options
    nprocs = int(options["nprocs"])  # optional

    if not ssurgo_path:
        gs.message(
            _(
                "Using Soil Data Access (SDA) to query and download "
                "data for the current computational region."
            )
        )
        aoi_wkt = region_to_wkt_wgs84()
        try:
            fd, tmp_filepath = tempfile.mkstemp(suffix=".geojson")
            sda_ssurgo_query(
                aoi_wkt=aoi_wkt,
                tmp_fd=fd,
                desgnmaster=desgnmaster,
                hzdept_r=hzdept_r,
                hzdepb_r=hzdepb_r,
            )
            write_ssurgo_to_grass(tmp_filepath, ssurgo_areas, src_srs=4326)
        except Exception as e:
            gs.fatal(f"An error occurred during SDA processing: {e}")
        finally:
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)
                gs.debug(f"Removed temp file: {tmp_filepath}")

    else:
        gs.message(_("Importing SSURGO data from local file."))
        _ssurgo_path = check_if_zipfile(Path(ssurgo_path))
        wkt_bbox = region_to_crs_wkt(target_crs="EPSG:5070")

        # The -s flag forces the SQLite/OGR backend even when duckdb is
        # importable. This lets users (and CI) exercise the SQLite path
        # without uninstalling duckdb.
        force_sqlite = bool(flags.get("s"))
        duckdb = None if force_sqlite else _import_duckdb(error=False)
        if duckdb:
            gs.message(_("Using DuckDB for local SSURGO query."))
            con = connect_duckdb(threads=nprocs)
            try:
                fd, tmp_filepath = tempfile.mkstemp(suffix=".fgb")

                # GRASS GDAL driver isn't supported by duckdb
                gs.message(f"Tempfile Path: {tmp_filepath}")
                local_ssurgo_query(
                    con=con,
                    tmp_filepath=tmp_filepath,
                    wkt_bbox=wkt_bbox,
                    ssurgo_path=_ssurgo_path,
                    desgnmaster=desgnmaster,
                    hzdept_r=hzdept_r,
                    hzdepb_r=hzdepb_r,
                )
                write_ssurgo_to_grass(tmp_filepath, ssurgo_areas, src_srs=5070)
            except Exception as e:
                gs.fatal(f"An error occurred during local SSURGO processing: {e}")
            finally:
                if con:
                    con.close()
                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)
                    gs.debug(f"Removed temp file: {tmp_filepath}")
        else:
            gs.message(_("Importing with SQLite/OGR local SSURGO query."))
            try:
                fd, tmp_filepath = tempfile.mkstemp(suffix=".fgb")
                gs.message(f"Tempfile Path: {tmp_filepath}")
                local_ssurgo_sqlite_query(
                    tmp_filepath=tmp_filepath,
                    # wkt_bbox=wkt_bbox,
                    ssurgo_path=str(_ssurgo_path),
                    desgnmaster=desgnmaster,
                    hzdept_r=hzdept_r,
                    hzdepb_r=hzdepb_r,
                )
                write_ssurgo_to_grass(tmp_filepath, ssurgo_areas, src_srs=5070)
            except Exception as e:
                gs.fatal(f"An error occurred during SQLite SSURGO processing: {e}")
            finally:
                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)
                    gs.debug(f"Removed temp file: {tmp_filepath}")

    if ssurgo_areas:
        _rasterize_and_style(ssurgo_areas, hydgrp, ksat_h, ksat_r, ksat_l, mukey)


if __name__ == "__main__":
    options, flags = gs.parser()
    # Active GRASS session path: GISDBASE/LOCATION/MAPSET
    gisenv = gs.gisenv()
    SESSION = f"{gisenv['GISDBASE']}/{gisenv['LOCATION_NAME']}/{gisenv['MAPSET']}"
    gs.message(f"Active GRASS session: {SESSION}")
    main()
