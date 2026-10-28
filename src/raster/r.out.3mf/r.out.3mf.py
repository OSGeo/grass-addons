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
#            SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Exports a raster DEM to 3MF or STL format for 3D printing, with optional hollow mold and multi-color output.
# % keyword: raster
# % keyword: export
# % keyword: 3D printing
# % keyword: 3MF
# % keyword: STL
# %end

# %option G_OPT_R_INPUT
# % key: input
# % description: Name of input raster DEM
# % required: yes
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % description: Name of output file (extension follows the format option)
# % required: yes
# % answer: output.3mf
# %end

# %option
# % key: zscale
# % type: double
# % description: Vertical exaggeration factor; with -n flag, interpreted as mm of relief
# % required: no
# % answer: 1.0
# % options: 0.01-100.0
# %end

# %option
# % key: base_height
# % type: double
# % description: Base thickness in mm (solid) or wall height below terrain (mold)
# % required: no
# % answer: 3.0
# %end

# %option
# % key: wall_thickness
# % type: double
# % description: Shell wall thickness in mm (mold mode only, -m flag)
# % required: no
# % answer: 3.0
# % options: 1.0-20.0
# %end

# %option
# % key: resolution
# % type: integer
# % description: Resampling factor (1 = native, 2 = half resolution, etc.)
# % required: no
# % answer: 1
# % options: 1-16
# %end

# %option
# % key: size
# % type: double
# % description: Longest model axis in mm
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

# %option
# % key: colors
# % type: string
# % description: Color scheme for multi-color 3MF (requires multi-material slicer)
# % required: no
# % answer: elevation
# % options: none,elevation
# %end

# %option
# % key: format
# % type: string
# % description: Output file format (3mf includes color metadata; stl is geometry-only but universally supported)
# % required: no
# % answer: 3mf
# % options: 3mf,stl
# %end

# %flag
# % key: n
# % description: Normalize Z to 0-1 before applying zscale (useful for non-metric DEMs)
# %end

# %flag
# % key: m
# % description: Hollow mold mode (open-bottom shell for kinetic sand or casting molds)
# %end

# %flag
# % key: r
# % description: Export the full input raster extent instead of the current region
# %end

import os
import math
import atexit
import zipfile
from io import BytesIO

import grass.script as gs
import grass.script.array as garray
import numpy as np


# Color palettes
# Classic hypsometric tint: 7 elevation bands
ELEVATION_COLORS = [
    "#1a6b1a",  # 0-14%   deep forest green
    "#52a447",  # 14-29%  mid green
    "#a8c45a",  # 29-43%  yellow-green
    "#d4a017",  # 43-57%  gold / lowland tan
    "#8b5e3c",  # 57-71%  earthy brown
    "#7a7a7a",  # 71-86%  gray rock
    "#e8e8e0",  # 86-100% near-snow
]
WALL_COLOR = "#4a4a4a"  # dark charcoal for walls, rim, and base
WALL_COLOR_IDX = len(ELEVATION_COLORS)  # index 7 in the full palette


def _make_palette():
    """Full color list: 7 elevation bands + 1 wall/base color."""
    return ELEVATION_COLORS + [WALL_COLOR]


def _elev_color_idx(avg_z, z_min, z_max):
    n = len(ELEVATION_COLORS)
    if z_max <= z_min:
        return 0
    t = max(0.0, min(1.0, (avg_z - z_min) / (z_max - z_min)))
    return min(int(t * n), n - 1)


# 3MF XML generation
_CONTENT_TYPES_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""

_RELS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model" Id="rel0"/>
</Relationships>
"""


def _colorgroup_xml(palette, group_id=2):
    lines = [f'    <p:colorgroup id="{group_id}">']
    for color in palette:
        # 3MF requires 8-char #AARRGGBB (alpha-first)
        if len(color) == 7:
            color = "#FF" + color[1:]
        lines.append(f'      <p:color color="{color}"/>')
    lines.append("    </p:colorgroup>")
    return "\n".join(lines)


def _vertices_xml(vertices):
    lines = ["        <vertices>"]
    for x, y, z in vertices:
        lines.append(f'          <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>')
    lines.append("        </vertices>")
    return "\n".join(lines)


def _triangles_xml(triangles, tri_colors=None, colorgroup_id=2):
    lines = ["        <triangles>"]
    for i, (v1, v2, v3) in enumerate(triangles):
        if tri_colors is not None:
            ci = tri_colors[i]
            lines.append(
                f'          <triangle v1="{v1}" v2="{v2}" v3="{v3}"'
                f' pid="{colorgroup_id}" p1="{ci}" p2="{ci}" p3="{ci}"/>'
            )
        else:
            lines.append(f'          <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>')
    lines.append("        </triangles>")
    return "\n".join(lines)


def _model_xml(vertices, triangles, tri_colors, color_palette, units):
    use_color = color_palette is not None and tri_colors is not None
    core_ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"'
    mat_ns = 'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/material/2015/02"'
    ns_block = f"{core_ns}\n       {mat_ns}" if use_color else core_ns

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<model unit="{units}" xml:lang="en-US"',
        f"       {ns_block}>",
        '  <metadata name="Application">GRASS r.out.3mf</metadata>',
        '  <metadata name="Description">DEM exported from GRASS</metadata>',
        "  <resources>",
    ]
    if use_color:
        lines.append(_colorgroup_xml(color_palette))
    lines += [
        '    <object id="1" type="model">',
        "      <mesh>",
        _vertices_xml(vertices),
        _triangles_xml(triangles, tri_colors if use_color else None),
        "      </mesh>",
        "    </object>",
        "  </resources>",
        "  <build>",
        '    <item objectid="1"/>',
        "  </build>",
        "</model>",
    ]
    return "\n".join(lines)


def write_3mf(output_path, vertices, triangles, tri_colors, color_palette, units):
    model_xml = _model_xml(vertices, triangles, tri_colors, color_palette, units)
    buf = BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", _RELS_XML)
        zf.writestr("3D/3dmodel.model", model_xml)
    with open(output_path, "wb") as fh:
        fh.write(buf.getvalue())


def write_stl(output_path, vertices, triangles):
    """
    Write a binary STL file.

    Format: 80-byte header + uint32 triangle count +
            (float32 normal[3] + float32 v0[3] + float32 v1[3] + float32 v2[3]
             + uint16 attribute) x n_triangles  =  50 bytes per triangle.

    Normals are computed from the cross product of the first two edge vectors
    and stored as unit vectors, which is what most slicers expect (though many
    ignore the normal field and recompute it from the winding order).
    """
    import struct

    title = b"GRASS r.out.3mf binary STL export"
    header = title + b"\x00" * (80 - len(title))
    n_tris = len(triangles)

    buf = BytesIO()
    buf.write(header)
    buf.write(struct.pack("<I", n_tris))

    for v1, v2, v3 in triangles:
        ax, ay, az = vertices[v1]
        bx, by, bz = vertices[v2]
        cx, cy, cz = vertices[v3]

        # Edge vectors
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az

        # Cross product (outward normal direction from CCW winding)
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx

        # Normalise
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag > 1e-12:
            nx, ny, nz = nx / mag, ny / mag, nz / mag

        buf.write(struct.pack("<fff", nx, ny, nz))
        buf.write(struct.pack("<fff", ax, ay, az))
        buf.write(struct.pack("<fff", bx, by, bz))
        buf.write(struct.pack("<fff", cx, cy, cz))
        buf.write(struct.pack("<H", 0))  # attribute byte count

    with open(output_path, "wb") as fh:
        fh.write(buf.getvalue())


# Mesh building


def _perim_indices(rows, cols):
    """
    Return top-surface vertex indices forming the perimeter, in consistent
    traversal order: N edge W->E, E edge N->S, S edge E->W, W edge S->N.
    """

    def idx(r, c):
        return r * cols + c

    perim = []
    for c in range(cols):
        perim.append(idx(0, c))
    for r in range(1, rows):
        perim.append(idx(r, cols - 1))
    for c in range(cols - 2, -1, -1):
        perim.append(idx(rows - 1, c))
    for r in range(rows - 2, 0, -1):
        perim.append(idx(r, 0))
    return perim


def _inset_xy(vx, vy, cx, cy, dist):
    """Translate (vx, vy) toward centroid (cx, cy) by dist mm."""
    dx, dy = cx - vx, cy - vy
    mag = math.hypot(dx, dy)
    if mag < 1e-9:
        return vx, vy
    return vx + dx / mag * dist, vy + dy / mag * dist


def build_mesh(
    elev,
    zscale,
    base_height,
    size_mm,
    hollow=False,
    wall_thickness=3.0,
    ewres=1.0,
    nsres=1.0,
    normalized=False,
):
    """
    Convert a 2-D elevation array into a printable 3-D mesh.

    Solid mode  : watertight block (terrain top, side walls, flat floor).
    Hollow/mold : open-bottom shell (terrain top, outer walls, inner walls,
                  top rim, bottom rim) for kinetic sand or casting use.

    XY scaling preserves the geographic aspect ratio: ewres and nsres are used
    to compute the real-world footprint, then the longest axis is scaled to
    size_mm with the other axis scaled proportionally.

    All triangle windings follow the right-hand rule with outward normals:
      - Terrain surface  -> +Z normal
      - Outer walls      -> outward normal (away from model center)
      - Inner walls      -> normal faces cavity interior
      - Top rim          -> +Z normal
      - Bottom rim       -> -Z normal
      - Floor (solid)    -> -Z normal

    Returns
    -------
    vertices       : list of (x, y, z)
    triangles      : list of (v1, v2, v3), terrain triangles come first
    n_terrain_tris : count of terrain-surface triangles
    z_surf_min     : model-space Z at lowest terrain point
    z_surf_max     : model-space Z at highest terrain point
    model_dims     : (x_mm, y_mm, z_mm) actual model bounding box in mm
    """
    rows, cols = elev.shape

    # Real-world footprint in map units (metres, degrees, etc.)
    real_ew = (cols - 1) * ewres
    real_ns = (rows - 1) * nsres

    # Scale so the longest geographic axis == size_mm; preserve aspect ratio
    base_scale = size_mm / max(real_ew, real_ns)
    x_scale = base_scale * ewres  # mm per grid column step
    y_scale = base_scale * nsres  # mm per grid row step

    z_elev_min = float(elev.min())
    z_elev_max = float(elev.max())
    z_range = z_elev_max - z_elev_min if z_elev_max != z_elev_min else 1.0
    elev_norm = (elev - z_elev_min) / z_range  # 0 .. 1

    # Terrain relief in mm.
    # Geographic-true mode: base_scale (mm / map_unit) is the same factor used
    # for XY, so zscale=1.0 gives geographically true vertical scale.
    # Normalized mode: elev was rescaled to 0-1 in main(), so map units are
    # gone, so zscale is interpreted directly as mm of relief.
    if normalized:
        terrain_height = zscale
    else:
        terrain_height = z_range * base_scale * zscale
    z_floor = 0.0
    z_surf = base_height + elev_norm * terrain_height

    z_surf_min = float(z_surf.min())
    z_surf_max = float(z_surf.max())

    x_extent = (cols - 1) * x_scale
    y_extent = (rows - 1) * y_scale
    cx_model = x_extent / 2.0
    cy_model = y_extent / 2.0

    # Terrain vertices (rows x cols)
    vertices = []
    for r in range(rows):
        for c in range(cols):
            vertices.append(
                (
                    c * x_scale,
                    (rows - 1 - r) * y_scale,  # flip so North is +Y
                    float(z_surf[r, c]),
                )
            )

    def top_idx(r, c):
        return r * cols + c

    # Terrain surface: CCW from above (+Z outward normal)
    triangles = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            tl = top_idx(r, c)
            tr = top_idx(r, c + 1)
            bl = top_idx(r + 1, c)
            br = top_idx(r + 1, c + 1)
            triangles.append((tl, bl, br))
            triangles.append((tl, br, tr))

    n_terrain_tris = len(triangles)

    perim_top = _perim_indices(rows, cols)
    n_perim = len(perim_top)

    if hollow:
        _add_hollow(
            vertices,
            triangles,
            perim_top,
            n_perim,
            cx_model,
            cy_model,
            wall_thickness,
            z_floor,
        )
    else:
        _add_solid(vertices, triangles, perim_top, n_perim, cx_model, cy_model, z_floor)

    model_dims = (x_extent, y_extent, z_surf_max - z_floor)
    return vertices, triangles, n_terrain_tris, z_surf_min, z_surf_max, model_dims


def _add_solid(vertices, triangles, perim_top, n_perim, cx, cy, z_floor):
    """Side walls and solid floor."""

    bot_start = len(vertices)
    for pi in perim_top:
        vx, vy, _ = vertices[pi]
        vertices.append((vx, vy, z_floor))

    floor_center = len(vertices)
    vertices.append((cx, cy, z_floor))

    for i in range(n_perim):
        j = (i + 1) % n_perim
        t0 = perim_top[i]
        t1 = perim_top[j]
        b0 = bot_start + i
        b1 = bot_start + j

        # Outer wall: outward normal (CCW from outside)
        triangles.append((t0, t1, b1))
        triangles.append((t0, b1, b0))

    # Floor fan: downward normal (CCW from below)
    for i in range(n_perim):
        j = (i + 1) % n_perim
        b0 = bot_start + i
        b1 = bot_start + j
        triangles.append((floor_center, b0, b1))


def _add_hollow(
    vertices, triangles, perim_top, n_perim, cx, cy, wall_thickness, z_floor
):
    """
    Hollow mold shell:

      Outer walls  : terrain perimeter down to outer bottom rim.
      Inner walls  : inner-top (wall_thickness inset) down to inner bottom.
      Top rim      : strip closing the gap between terrain edge and inner-top.
      Bottom rim   : flat ring closing the bottom of the shell.
      Open bottom  : no floor polygon (the mold opening for kinetic sand).

    All normals are outward. The open bottom produces n_perim boundary edges
    (manifold everywhere else).
    """

    # Outer bottom (same XY as terrain perimeter, z = floor)
    outer_bot_start = len(vertices)
    for pi in perim_top:
        vx, vy, _ = vertices[pi]
        vertices.append((vx, vy, z_floor))

    # Inner top (inset toward centroid, z = same as terrain perimeter)
    inner_top_start = len(vertices)
    for pi in perim_top:
        vx, vy, vz = vertices[pi]
        ix, iy = _inset_xy(vx, vy, cx, cy, wall_thickness)
        vertices.append((ix, iy, vz))

    # Inner bottom (same XY as inner top, z = floor)
    inner_bot_start = len(vertices)
    for i in range(n_perim):
        ix, iy, _ = vertices[inner_top_start + i]
        vertices.append((ix, iy, z_floor))

    for i in range(n_perim):
        j = (i + 1) % n_perim

        t0 = perim_top[i]
        t1 = perim_top[j]
        ob0 = outer_bot_start + i
        ob1 = outer_bot_start + j
        it0 = inner_top_start + i
        it1 = inner_top_start + j
        ib0 = inner_bot_start + i
        ib1 = inner_bot_start + j

        # Outer wall, outward normal: (t0, t1, ob1), (t0, ob1, ob0)
        # {t0,t1} edge is shared with the terrain surface: count = 2, manifold.
        triangles.append((t0, t1, ob1))
        triangles.append((t0, ob1, ob0))

        # Inner wall, normal toward cavity: (it0, ib0, ib1), (it0, ib1, it1)
        # {it0,it1} top edge has count = 1: the intentional open mold boundary.
        # No top rim polygon here: adding one would put {t0,t1} on 3 triangles.
        # When pressed face-down into kinetic sand the terrain surface goes in
        # first, so this inner-top gap faces into the sand and gets sealed by it.
        triangles.append((it0, ib0, ib1))
        triangles.append((it0, ib1, it1))

        # Bottom rim, downward normal: (ob0, ob1, ib1), (ob0, ib1, ib0)
        # Seals the annulus at z_floor; the central hole is the mold opening.
        triangles.append((ob0, ob1, ib1))
        triangles.append((ob0, ib1, ib0))


def assign_colors(triangles, vertices, n_terrain_tris, z_surf_min, z_surf_max):
    """
    Per-triangle color indices.

    Terrain triangles are colored by average vertex Z (elevation band).
    Wall, rim, and floor triangles get the wall color index.
    """
    colors = []
    for i, (v1, v2, v3) in enumerate(triangles):
        if i < n_terrain_tris:
            avg_z = (vertices[v1][2] + vertices[v2][2] + vertices[v3][2]) / 3.0
            colors.append(_elev_color_idx(avg_z, z_surf_min, z_surf_max))
        else:
            colors.append(WALL_COLOR_IDX)
    return colors


def read_raster(name, resolution):
    """
    Read a GRASS raster into a float64 numpy array via grass.script.array.

    Null cells are filled with the native *r.fillnulls* spline interpolation
    into a temporary raster (removed at exit) before the array is read, so a
    watertight mesh can be built without holes. This keeps null handling inside
    GRASS instead of relying on an optional NumPy/SciPy fill.
    """
    if resolution > 1:
        region = gs.region()
        new_res = region["ewres"] * resolution
        gs.run_command("g.region", res=new_res, flags="a", quiet=True)
        gs.message(_("Region resampled to {:.2f} resolution.").format(new_res))

    null_cells = int(
        gs.parse_command("r.univar", map=name, flags="g", quiet=True)["null_cells"]
    )
    if null_cells > 0:
        gs.message(_("Filling null cells with r.fillnulls..."))
        filled = gs.append_node_pid("tmp_r_out_3mf_filled")
        atexit.register(
            gs.run_command,
            "g.remove",
            type="raster",
            name=filled,
            flags="f",
            quiet=True,
            errors="ignore",
        )
        gs.run_command("r.fillnulls", input=name, output=filled, quiet=True)
        name = filled

    arr = garray.array(mapname=name)
    return np.array(arr, dtype=np.float64)


def main():
    options, flags = gs.parser()

    input_raster = options["input"]
    output_path = options["output"]
    zscale = float(options["zscale"])
    base_height = float(options["base_height"])
    wall_thickness = float(options["wall_thickness"])
    resolution = int(options["resolution"])
    size_mm = float(options["size"])
    units = options["units"]
    color_scheme = options["colors"]
    out_format = options["format"].lower()
    normalize = flags["n"]
    hollow = flags["m"]
    full_raster = flags["r"]

    # Enforce correct extension regardless of what the user typed
    for ext in (".3mf", ".stl"):
        if output_path.lower().endswith(ext):
            output_path = output_path[: -len(ext)]
            break
    output_path += f".{out_format}"

    # The parser checks --overwrite against the name the user typed, but the
    # extension may have just been rewritten, so re-check the real output file.
    if os.path.exists(output_path) and not gs.overwrite():
        gs.fatal(
            _("Output file '{}' already exists. Use --overwrite to replace it.").format(
                output_path
            )
        )

    # STL carries no color data, warn rather than silently discard
    if out_format == "stl" and color_scheme == "elevation":
        gs.warning(
            _(
                "Option colors=elevation is ignored for STL output. "
                "Use format=3mf to retain color metadata."
            )
        )

    # Work in a temporary region so the user's current region is restored
    # when the tool exits, even on error. By default the current region is
    # respected; -r expands to the full input raster extent.
    gs.use_temp_region()
    atexit.register(gs.del_temp_region)
    if full_raster:
        gs.run_command("g.region", raster=input_raster, quiet=True)
    gs.message(_("Reading raster map <{}>...").format(input_raster))

    try:
        elev = read_raster(input_raster, resolution)
    except Exception as e:
        gs.fatal(
            _("Failed to read raster map <{name}>: {error}").format(
                name=input_raster, error=e
            )
        )

    rows, cols = elev.shape
    if rows < 2 or cols < 2:
        gs.fatal(
            _(
                "Region too small to build a mesh: {rows} rows x {cols} cols. "
                "At least 2 rows and 2 columns are required; adjust the region "
                "or lower the resolution value."
            ).format(rows=rows, cols=cols)
        )

    # Read resolution after read_raster: it may have changed the region if
    # resolution > 1, and ewres/nsres drive the XY aspect ratio of the mesh.
    region = gs.region()
    ewres = region["ewres"]
    nsres = region["nsres"]

    gs.message(
        _(
            "Raster: {cols} cols x {rows} rows "
            "(Z range: {zmin:.2f} to {zmax:.2f}, res: {ewres:.2f} x {nsres:.2f})"
        ).format(
            cols=cols,
            rows=rows,
            zmin=elev.min(),
            zmax=elev.max(),
            ewres=ewres,
            nsres=nsres,
        )
    )

    if normalize:
        z_min = elev.min()
        z_max = elev.max()
        z_rng = z_max - z_min if z_max != z_min else 1.0
        elev = (elev - z_min) / z_rng
        gs.message(_("Z values normalized to 0-1 range."))

    if hollow:
        gs.message(_("Building hollow mold mesh..."))
    else:
        gs.message(_("Building solid mesh..."))

    vertices, triangles, n_terrain_tris, z_surf_min, z_surf_max, model_dims = (
        build_mesh(
            elev,
            zscale=zscale,
            base_height=base_height,
            size_mm=size_mm,
            hollow=hollow,
            wall_thickness=wall_thickness,
            ewres=ewres,
            nsres=nsres,
            normalized=normalize,
        )
    )

    gs.message(
        _(
            "Mesh: {nverts:,} vertices, {ntris:,} triangles "
            "({nterrain:,} terrain surface)"
        ).format(
            nverts=len(vertices),
            ntris=len(triangles),
            nterrain=n_terrain_tris,
        )
    )
    gs.message(
        _("Model dimensions: {x:.1f} x {y:.1f} x {z:.1f} mm").format(
            x=model_dims[0], y=model_dims[1], z=model_dims[2]
        )
    )

    tri_colors = None
    color_palette = None
    if color_scheme == "elevation":
        gs.message(_("Assigning elevation color bands..."))
        color_palette = _make_palette()
        tri_colors = assign_colors(
            triangles, vertices, n_terrain_tris, z_surf_min, z_surf_max
        )

    gs.message(_("Writing '{}'...").format(output_path))
    try:
        if out_format == "stl":
            write_stl(output_path, vertices, triangles)
        else:
            write_3mf(
                output_path, vertices, triangles, tri_colors, color_palette, units
            )
    except Exception as e:
        gs.fatal(_("Failed to write output file '{}': {}").format(output_path, e))

    size_kb = os.path.getsize(output_path) / 1024
    gs.message(
        _("Done. Wrote '{path}' ({size:.1f} KB).").format(
            path=output_path, size=size_kb
        )
    )


if __name__ == "__main__":
    main()
