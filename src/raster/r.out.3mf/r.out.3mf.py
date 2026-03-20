#!/usr/bin/env python3

##############################################################################
# MODULE:    r.out.3mf
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Export a raster DEM to 3MF format for 3D printing.
#
# COPYRIGHT: (C) 2026 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

# %module
# % description: Exports a raster DEM to 3MF format for 3D printing.
# % keyword: raster
# % keyword: export
# % keyword: 3D printing
# % keyword: 3MF
# %end

# %option G_OPT_R_INPUT
# % key: input
# % description: Name of input raster DEM
# % required: yes
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % description: Name of output 3MF file
# % required: yes
# % answer: output.3mf
# %end

# %option
# % key: zscale
# % type: double
# % description: Vertical exaggeration factor (Z scale multiplier)
# % required: no
# % answer: 1.0
# % options: 0.01-100.0
# %end

# %option
# % key: base_height
# % type: double
# % description: Base/floor thickness in model units (mm equivalent after scaling)
# % required: no
# % answer: 2.0
# %end

# %option
# % key: resolution
# % type: integer
# % description: Resampling resolution (1 = native, 2 = half resolution, etc.)
# % required: no
# % answer: 1
# % options: 1-16
# %end

# %option
# % key: size
# % type: double
# % description: Maximum extent of the model in mm (longest axis will be scaled to this)
# % required: no
# % answer: 100.0
# %end

# %option
# % key: units
# % type: string
# % description: Units declaration embedded in the 3MF file
# % required: no
# % answer: millimeter
# % options: millimeter,centimeter,inch,foot,meter
# %end

# %flag
# % key: n
# % description: Normalize Z values to 0-1 before applying zscale (useful for non-metric DEMs)
# %end

# %flag
# % key: s
# % description: Smooth normals (calculate per-vertex normals for smoother appearance)
# %end

import os
import zipfile
from io import BytesIO

import grass.script as gs
import grass.script.array as garray
import numpy as np


# ---------------------------------------------------------------------------
# 3MF XML templates
# ---------------------------------------------------------------------------

CONTENT_TYPES_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""

RELS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model" Id="rel0"/>
</Relationships>
"""

MODEL_XML_HEADER = """\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="{units}" xml:lang="en-US"
       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
       xmlns:p="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">
  <metadata name="Application">GRASS GIS r.out.3mf</metadata>
  <metadata name="Description">DEM exported from GRASS GIS</metadata>
  <resources>
    <object id="1" type="model">
      <mesh>
"""

MODEL_XML_FOOTER = """\
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
  </build>
</model>
"""


# ---------------------------------------------------------------------------
# Mesh building helpers
# ---------------------------------------------------------------------------


def build_mesh(elev, zscale, base_height, size_mm, normalize=False):
    """
    Convert a 2-D elevation array into vertices and triangles for a
    watertight (printable) solid.

    The solid consists of:
      - Top surface  (the DEM terrain)
      - Bottom face  (flat floor)
      - Four side walls connecting top perimeter to bottom perimeter
    """
    rows, cols = elev.shape

    # --- Scale XY so the longer axis == size_mm ---
    xy_scale = size_mm / max(rows - 1, cols - 1)

    # --- Scale Z ---
    # By default, preserve DEM elevation differences and apply zscale directly.
    # With -n, normalize the DEM to 0..1 before applying zscale.
    if normalize:
        z_min = elev.min()
        z_max = elev.max()
        z_range = z_max - z_min if z_max != z_min else 1.0
        z_rel = (elev - z_min) / z_range
    else:
        z_rel = elev - elev.min()

    z_floor = 0.0
    z_top = base_height + z_rel * zscale

    # Build top-surface vertices  (rows x cols)
    vertices = []
    for r in range(rows):
        for c in range(cols):
            x = c * xy_scale
            y = (rows - 1 - r) * xy_scale  # flip Y so North is up
            z = z_top[r, c]
            vertices.append((x, y, z))

    # Bottom perimeter vertices (same XY, z = floor)
    # We need the 4 walls; add all perimeter points at z_floor
    # Top perimeter indices (in order: top row, right col, bottom row rev, left col rev)
    def top_idx(r, c):
        return r * cols + c

    # Collect perimeter in order
    perim_top = []
    for c in range(cols):
        perim_top.append(top_idx(0, c))  # top edge
    for r in range(1, rows):
        perim_top.append(top_idx(r, cols - 1))  # right edge
    for c in range(cols - 2, -1, -1):
        perim_top.append(top_idx(rows - 1, c))  # bottom edge
    for r in range(rows - 2, 0, -1):
        perim_top.append(top_idx(r, 0))  # left edge

    # Add bottom perimeter vertices at z_floor
    perim_bottom_start = len(vertices)
    for pi in perim_top:
        vx, vy, _ = vertices[pi]
        vertices.append((vx, vy, z_floor))

    # Add center bottom vertex for floor fan
    cx = (cols - 1) * xy_scale / 2
    cy = (rows - 1) * xy_scale / 2
    floor_center = len(vertices)
    vertices.append((cx, cy, z_floor))

    triangles = []

    # --- Top surface triangles (two triangles per quad) ---
    for r in range(rows - 1):
        for c in range(cols - 1):
            tl = top_idx(r, c)
            tr = top_idx(r, c + 1)
            bl = top_idx(r + 1, c)
            br = top_idx(r + 1, c + 1)
            triangles.append((tl, tr, br))
            triangles.append((tl, br, bl))

    # --- Side walls ---
    n_perim = len(perim_top)
    for i in range(n_perim):
        j = (i + 1) % n_perim
        t0 = perim_top[i]
        t1 = perim_top[j]
        b0 = perim_bottom_start + i
        b1 = perim_bottom_start + j
        # Winding: outward-facing (vertices go CW from outside = CCW for interior)
        triangles.append((t0, b0, b1))
        triangles.append((t0, b1, t1))

    # --- Floor triangles (fan from center) ---
    for i in range(n_perim):
        j = (i + 1) % n_perim
        b0 = perim_bottom_start + i
        b1 = perim_bottom_start + j
        # Floor faces down: winding reversed
        triangles.append((floor_center, b1, b0))

    return vertices, triangles


# ---------------------------------------------------------------------------
# 3MF serialisation
# ---------------------------------------------------------------------------


def vertices_xml(vertices):
    lines = ["        <vertices>"]
    for x, y, z in vertices:
        lines.append(f'          <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>')
    lines.append("        </vertices>")
    return "\n".join(lines)


def triangles_xml(triangles):
    lines = ["        <triangles>"]
    for v1, v2, v3 in triangles:
        lines.append(f'          <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>')
    lines.append("        </triangles>")
    return "\n".join(lines)


def write_3mf(output_path, vertices, triangles, units):
    model_xml = (
        MODEL_XML_HEADER.format(units=units)
        + vertices_xml(vertices)
        + "\n"
        + triangles_xml(triangles)
        + "\n"
        + MODEL_XML_FOOTER
    )

    buf = BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", RELS_XML)
        zf.writestr("3D/3dmodel.model", model_xml)

    with open(output_path, "wb") as f:
        f.write(buf.getvalue())


# ---------------------------------------------------------------------------
# GRASS raster reading
# ---------------------------------------------------------------------------


def read_raster(name, resolution):
    """Read a GRASS raster into a numpy array using grass.script.array.

    Uses the native GRASS array API instead of exporting to ASCII, which
    avoids the tempfile/flag/header-parsing bugs in the previous version.
    """
    # Optionally coarsen the region resolution before reading
    if resolution > 1:
        region = gs.region()
        new_res = region["ewres"] * resolution
        gs.run_command("g.region", res=new_res, flags="a", quiet=True)
        gs.message(_("Region resampled to {:.2f} m resolution.").format(new_res))

    # Read directly into a masked numpy array
    arr = garray.array(name)
    data = np.array(arr, dtype=np.float64)

    # Fill null cells (masked) using nearest-neighbour distance transform
    if hasattr(arr, "mask") and np.any(arr.mask):
        gs.message(_("Filling null cells with nearest-neighbor interpolation..."))
        from scipy.ndimage import distance_transform_edt

        mask = np.array(arr.mask)
        idx = distance_transform_edt(mask, return_distances=False, return_indices=True)
        data = data[tuple(idx)]
    elif np.any(np.isnan(data)):
        gs.message(_("Filling NaN cells with nearest-neighbor interpolation..."))
        from scipy.ndimage import distance_transform_edt

        mask = np.isnan(data)
        idx = distance_transform_edt(mask, return_distances=False, return_indices=True)
        data = data[tuple(idx)]

    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    options, flags = gs.parser()

    input_raster = options["input"]
    output_path = options["output"]
    zscale = float(options["zscale"])
    base_height = float(options["base_height"])
    resolution = int(options["resolution"])
    size_mm = float(options["size"])
    units = options["units"]
    normalize = flags["n"]

    if flags["s"]:
        gs.warning(_("Flag -s is currently not implemented and will be ignored."))

    if not output_path.lower().endswith(".3mf"):
        output_path += ".3mf"

    raster_info = gs.find_file(input_raster, element="raster")
    if not raster_info["file"]:
        gs.fatal(_("Raster map <{}> not found.").format(input_raster))

    if os.path.exists(output_path) and not gs.overwrite():
        gs.fatal(
            _("File '{}' already exists. Use --overwrite to overwrite it.").format(
                output_path
            )
        )

    # Verify input exists
    gs.message(_("Reading raster map <{}>...").format(input_raster))

    # Read elevation data
    try:
        with gs.RegionManager():
            gs.run_command("g.region", raster=input_raster, quiet=True)
            elev = read_raster(input_raster, resolution)
    except Exception as e:
        gs.fatal(_("Failed to read raster map <{}>: {}").format(input_raster, e))

    gs.message(
        _("Raster size: {} cols x {} rows (Z range: {:.2f} - {:.2f})").format(
            elev.shape[1], elev.shape[0], elev.min(), elev.max()
        )
    )

    if normalize:
        gs.message(_("Applying Z normalization (0-1) before zscale."))

    # Build mesh
    gs.message(_("Building 3D mesh..."))
    vertices, triangles = build_mesh(
        elev, zscale, base_height, size_mm, normalize=normalize
    )

    gs.message(
        _("Mesh: {:,} vertices, {:,} triangles").format(len(vertices), len(triangles))
    )

    # Write 3MF
    gs.message(_("Writing file '{}'...").format(output_path))
    try:
        write_3mf(output_path, vertices, triangles, units)
    except Exception as e:
        gs.fatal(_("Failed to write 3MF file '{}': {}").format(output_path, e))

    size_bytes = os.path.getsize(output_path)
    gs.message(
        _("Done. Output file '{}' ({:.1f} KB).").format(output_path, size_bytes / 1024)
    )


if __name__ == "__main__":
    main()
