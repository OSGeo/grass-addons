#!/usr/bin/env python3

##############################################################################
# MODULE:    r.anim.morph
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Generate animation frames that morph a before raster into an
#            after raster using per-cell animation plans after Lobo, Appert
#            and Pietriga (2019).
#
# COPYRIGHT: (C) 2026 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Morphs a before raster into an after raster as a spatially aware sequence of animation frames
# % keyword: raster
# % keyword: animation
# % keyword: morph
# % keyword: temporal
# % keyword: imagery
# % keyword: change detection
# %end

# %option G_OPT_R_INPUTS
# % key: before
# % label: Before raster map(s)
# % description: One raster, or one raster per band in the same order as after
# %end

# %option G_OPT_R_INPUTS
# % key: after
# % label: After raster map(s)
# % description: One raster, or one raster per band in the same order as before
# %end

# %option G_OPT_R_BASENAME_OUTPUT
# % key: output
# % label: Basename for the output frames
# % description: Frames are named <output>_001, <output>_002, ... (or <output>_b<band>_001, ... for multiple bands)
# %end

# %option
# % key: frames
# % type: integer
# % label: Number of frames
# % answer: 30
# % options: 2-1000
# %end

# %option
# % key: primitive
# % type: string
# % label: Animation primitive
# % description: Spatial ordering of the transition inside the region of interest
# % options: blend,appearance,disappearance,contraction,expansion,deformation,radial,directional,dem,plan
# % descriptions: blend;Uniform blend, every cell transitions at the same time;appearance;Region grows from its edge inward (requires mask_after);disappearance;Region fades from its edge inward (requires mask_before);contraction;Shape shrinks from mask_before to mask_after;expansion;Shape grows from mask_before to mask_after;deformation;Shape contracts and expands at the same time;radial;Transition spreads from a center point outward;directional;Transition sweeps in a compass direction;dem;Transition ordered by elevation;plan;Use precomputed plan_start and plan_end rasters
# % answer: blend
# %end

# %option G_OPT_R_INPUT
# % key: mask_before
# % label: Region of interest in the before image
# % description: Cells greater than zero belong to the region of interest
# % required: no
# % guisection: Region of interest
# %end

# %option G_OPT_R_INPUT
# % key: mask_after
# % label: Region of interest in the after image
# % description: Cells greater than zero belong to the region of interest
# % required: no
# % guisection: Region of interest
# %end

# %option G_OPT_R_INPUT
# % key: dem
# % label: Elevation raster for the dem primitive
# % description: Higher cells transition first unless the -i flag is set
# % required: no
# % guisection: Primitive
# %end

# %option
# % key: direction
# % type: string
# % label: Compass direction of the directional primitive
# % description: N means the transition moves from south to north
# % options: N,S,E,W,NE,NW,SE,SW
# % answer: N
# % required: no
# % guisection: Primitive
# %end

# %option G_OPT_M_COORDS
# % key: coordinates
# % label: Center of the radial primitive
# % description: Defaults to the center of the computational region
# % guisection: Primitive
# %end

# %option G_OPT_R_INPUT
# % key: plan_start
# % label: Precomputed start times for the plan primitive
# % description: Raster of normalized start times in the range 0 to 1
# % required: no
# % guisection: Primitive
# %end

# %option G_OPT_R_INPUT
# % key: plan_end
# % label: Precomputed end times for the plan primitive
# % description: Raster of normalized end times in the range 0 to 1
# % required: no
# % guisection: Primitive
# %end

# %option
# % key: roi_start
# % type: double
# % label: Start of the region of interest transition
# % description: Normalized time in the range 0 to 1
# % answer: 0.0
# % options: 0-1
# % guisection: Timing
# %end

# %option
# % key: roi_end
# % type: double
# % label: End of the region of interest transition
# % description: Normalized time in the range 0 to 1
# % answer: 1.0
# % options: 0-1
# % guisection: Timing
# %end

# %option
# % key: bg_start
# % type: double
# % label: Start of the background transition
# % description: Normalized time in the range 0 to 1
# % answer: 0.0
# % options: 0-1
# % guisection: Timing
# %end

# %option
# % key: bg_end
# % type: double
# % label: End of the background transition
# % description: Normalized time in the range 0 to 1
# % answer: 1.0
# % options: 0-1
# % guisection: Timing
# %end

# %option
# % key: blend_duration
# % type: double
# % label: Duration of the blend of a single cell
# % description: Normalized duration in the range 0 to 1, zero for an instant swap
# % answer: 0.3
# % options: 0-1
# % guisection: Timing
# %end

# %option G_OPT_F_INPUT
# % key: stages
# % label: JSON file with a sequence of animation stages
# % description: Each stage is an object with the same keys as the tool options; stages are combined into one plan
# % required: no
# %end

# %option G_OPT_R_BASENAME_OUTPUT
# % key: output_plan
# % label: Basename for the animation plan rasters
# % description: Saves the start and end times as <output_plan>_S and <output_plan>_E
# % required: no
# %end

# %option G_OPT_M_NPROCS
# %end

# %flag
# % key: i
# % description: Invert the transition order of the radial, directional, and dem primitives
# %end

# %flag
# % key: c
# % description: Match the mean and standard deviation of each before band to its after band
# %end

# %flag
# % key: p
# % description: Compute and report the animation plan without writing frames
# %end

# %rules
# % collective: plan_start,plan_end
# %end

import atexit
import json
import os

import grass.script as gs
from grass.tools import Tools

TMP_RASTERS = []
TMP_FILES = []
PRIMITIVES = (
    "blend",
    "appearance",
    "disappearance",
    "contraction",
    "expansion",
    "deformation",
    "radial",
    "directional",
    "dem",
    "plan",
)


def cleanup():
    if TMP_RASTERS:
        gs.run_command(
            "g.remove", type="raster", name=",".join(TMP_RASTERS), flags="f", quiet=True
        )
    for path in TMP_FILES:
        if os.path.exists(path):
            os.remove(path)


def tmp_raster(base):
    name = gs.append_node_pid(f"tmp_r_anim_morph_{base}_{len(TMP_RASTERS)}")
    TMP_RASTERS.append(name)
    return name


def mapcalc(tools, name, expression):
    tools.r_mapcalc(expression=f"{name} = {expression}")
    return name


def raster_range(tools, name):
    """Return (min, max) of a raster, or (None, None) when it has no data."""
    info = tools.r_info(map=name, flags="r", format="json").json
    if info["min"] is None or info["max"] is None:
        return None, None
    return float(info["min"]), float(info["max"])


def binary_mask(tools, raster):
    """Return a temporary 0/1 raster (no nulls) with 1 where raster > 0."""
    return mapcalc(
        tools,
        tmp_raster("mask"),
        f"if(isnull({raster}), 0, if({raster} > 0, 1, 0))",
    )


def mask_is_empty(tools, mask):
    return raster_range(tools, mask)[1] == 0


def no_cells(tools, condition):
    """True when no cell of the current region satisfies condition."""
    flag = mapcalc(tools, tmp_raster("any"), f"if({condition}, 1, 0)")
    return raster_range(tools, flag)[1] == 0


def distance_to(tools, condition):
    """Map-unit distance from every cell to the nearest cell where condition holds."""
    target = mapcalc(tools, tmp_raster("target"), f"if({condition}, 1, null())")
    distance = tmp_raster("dist")
    metric = "geodesic" if gs.locn_is_latlong() else "euclidean"
    tools.r_grow_distance(input=target, distance=distance, metric=metric)
    return distance


def normalized(tools, raster, zone):
    """Scale raster to 0..1 over the cells where zone is true; 0 elsewhere."""
    inside = mapcalc(tools, tmp_raster("inside"), f"if({zone}, {raster}, null())")
    low, high = raster_range(tools, inside)
    if low is None or high == low:
        return "0.0"
    return f"if({zone}, ({raster} - {low}) / ({high} - {low}), 0.0)"


def edge_order(tools, mask):
    """Normalized distance from the edge of mask inward (0 at the edge)."""
    distance = distance_to(tools, f"{mask} == 0")
    return normalized(tools, distance, f"{mask} == 1")


def plan_zones(tools, primitive, cfg):
    """Build the zone raster and the ordering expression of one primitive.

    Zones: 0 background, 1 ordered transition, 2 uniform region-of-interest
    transition. The ordering expression evaluates to 0 (first) .. 1 (last)
    inside zone 1.
    """
    mb = binary_mask(tools, cfg["mask_before"]) if cfg.get("mask_before") else None
    ma = binary_mask(tools, cfg["mask_after"]) if cfg.get("mask_after") else None
    if mb is not None and mask_is_empty(tools, mb):
        gs.warning(_("mask_before has no cells greater than zero"))
        mb = None
    if ma is not None and mask_is_empty(tools, ma):
        gs.warning(_("mask_after has no cells greater than zero"))
        ma = None

    if primitive == "blend":
        return "2", "0.0"

    if primitive == "appearance":
        if ma is None:
            gs.fatal(_("Primitive 'appearance' requires mask_after"))
        return ma, edge_order(tools, ma)

    if primitive == "disappearance":
        if mb is None:
            gs.fatal(_("Primitive 'disappearance' requires mask_before"))
        return mb, f"1.0 - ({edge_order(tools, mb)})"

    if primitive == "contraction":
        if mb is None:
            gs.fatal(_("Primitive 'contraction' requires mask_before"))
        if ma is None:
            return mb, f"1.0 - ({edge_order(tools, mb)})"
        leaving = f"({mb} == 1 && {ma} == 0)"
        zone = mapcalc(
            tools,
            tmp_raster("zone"),
            f"if({mb} == 1 && {ma} == 1, 2, if({leaving}, 1, 0))",
        )
        if no_cells(tools, leaving):
            gs.warning(
                _("mask_before has no cells outside mask_after; nothing contracts")
            )
            return zone, "0.0"
        order = normalized(tools, distance_to(tools, f"{ma} == 1"), leaving)
        return zone, f"1.0 - ({order})"

    if primitive == "expansion":
        if ma is None:
            gs.fatal(_("Primitive 'expansion' requires mask_after"))
        if mb is None:
            return ma, edge_order(tools, ma)
        entering = f"({ma} == 1 && {mb} == 0)"
        zone = mapcalc(
            tools,
            tmp_raster("zone"),
            f"if({mb} == 1 && {ma} == 1, 2, if({entering}, 1, 0))",
        )
        if no_cells(tools, entering):
            gs.warning(
                _("mask_after has no cells outside mask_before; nothing expands")
            )
            return zone, "0.0"
        return zone, normalized(tools, distance_to(tools, f"{mb} == 1"), entering)

    if primitive == "deformation":
        if mb is None or ma is None:
            gs.fatal(_("Primitive 'deformation' requires mask_before and mask_after"))
        leaving = f"({mb} == 1 && {ma} == 0)"
        entering = f"({ma} == 1 && {mb} == 0)"
        zone = mapcalc(
            tools,
            tmp_raster("zone"),
            f"if({mb} == 1 && {ma} == 1, 2, if({leaving} || {entering}, 1, 0))",
        )
        leave_order = normalized(tools, distance_to(tools, f"{ma} == 1"), leaving)
        enter_order = normalized(tools, distance_to(tools, f"{mb} == 1"), entering)
        return zone, f"if({leaving}, 1.0 - ({leave_order}), {enter_order})"

    roi = mb if mb is not None else ma
    zone = roi if roi is not None else "1"

    if primitive == "radial":
        if cfg.get("coordinates"):
            cx, cy = (float(v) for v in cfg["coordinates"])
        else:
            region = gs.region()
            cx = (region["w"] + region["e"]) / 2.0
            cy = (region["s"] + region["n"]) / 2.0
        radius = mapcalc(
            tools, tmp_raster("radius"), f"sqrt((x() - {cx})^2 + (y() - {cy})^2)"
        )
        order = normalized(tools, radius, f"{zone} == 1")
    elif primitive == "directional":
        axis = {
            "N": "y()",
            "S": "-y()",
            "E": "x()",
            "W": "-x()",
            "NE": "x() + y()",
            "NW": "y() - x()",
            "SE": "x() - y()",
            "SW": "-x() - y()",
        }[cfg.get("direction", "N").upper()]
        sweep = mapcalc(tools, tmp_raster("sweep"), axis)
        order = normalized(tools, sweep, f"{zone} == 1")
    elif primitive == "dem":
        if not cfg.get("dem"):
            gs.fatal(_("Primitive 'dem' requires dem"))
        dem = cfg["dem"]
        order = normalized(tools, dem, f"{zone} == 1 && !isnull({dem})")
        if not cfg.get("invert"):
            order = f"1.0 - ({order})"
        return zone, order
    else:
        gs.fatal(_("Unknown primitive '{}'").format(primitive))

    if cfg.get("invert"):
        order = f"1.0 - ({order})"
    return zone, order


def build_plan(tools, cfg, start_name, end_name):
    """Write the start and end time rasters of one stage."""
    primitive = cfg.get("primitive", "blend").lower()
    if primitive not in PRIMITIVES:
        gs.fatal(_("Unknown primitive '{}'").format(primitive))
    if primitive == "plan":
        if not cfg.get("plan_start") or not cfg.get("plan_end"):
            gs.fatal(_("Primitive 'plan' requires plan_start and plan_end"))
        mapcalc(tools, start_name, f"max(0.0, min(1.0, {cfg['plan_start']}))")
        mapcalc(tools, end_name, f"max(0.0, min(1.0, {cfg['plan_end']}))")
        return

    roi_start = float(cfg.get("roi_start", 0.0))
    roi_end = float(cfg.get("roi_end", 1.0))
    bg_start = float(cfg.get("bg_start", 0.0))
    bg_end = float(cfg.get("bg_end", 1.0))
    blend = float(cfg.get("blend_duration", 0.3))
    for label, start, end in (("roi", roi_start, roi_end), ("bg", bg_start, bg_end)):
        if not 0.0 <= start <= end <= 1.0:
            gs.fatal(
                _("{0}_start and {0}_end must satisfy 0 <= start <= end <= 1").format(
                    label
                )
            )
    if blend > roi_end - roi_start:
        gs.fatal(_("blend_duration must not exceed roi_end - roi_start"))

    zone, order = plan_zones(tools, primitive, cfg)
    ordered_start = f"{roi_start} + ({order}) * {roi_end - roi_start - blend}"
    mapcalc(
        tools,
        start_name,
        f"if({zone} == 2, {roi_start}, if({zone} == 1, {ordered_start}, {bg_start}))",
    )
    mapcalc(
        tools,
        end_name,
        f"if({zone} == 2, {roi_end}, "
        f"if({zone} == 1, min(1.0, {start_name} + {blend}), {bg_end}))",
    )


def match_statistics(tools, before, after):
    """Return a temporary raster with before rescaled to the mean and
    standard deviation of after."""
    stats_before = tools.r_univar(map=before, format="json").json
    stats_after = tools.r_univar(map=after, format="json").json
    if not stats_before.get("n") or not stats_after.get("n"):
        return before
    if stats_before["stddev"] < 1e-10:
        return before
    scale = stats_after["stddev"] / stats_before["stddev"]
    return mapcalc(
        tools,
        tmp_raster("matched"),
        f"({before} - {stats_before['mean']}) * {scale} + {stats_after['mean']}",
    )


def frame_names(output, n_frames, n_bands):
    pad = len(str(n_frames))
    names = []
    for band in range(1, n_bands + 1):
        band_names = []
        for frame in range(1, n_frames + 1):
            label = str(frame).zfill(pad)
            if n_bands == 1:
                band_names.append(f"{output}_{label}")
            else:
                band_names.append(f"{output}_b{band}_{label}")
        names.append(band_names)
    return names


def check_outputs(names):
    if gs.overwrite():
        return
    for name in names:
        if gs.find_file(name, element="cell")["fullname"]:
            gs.fatal(
                _(
                    "Raster map <{}> already exists. "
                    "Use --overwrite to replace existing frames"
                ).format(name)
            )


def report_plan(tools, start_name, end_name):
    for label, name in (("S", start_name), ("E", end_name)):
        stats = tools.r_univar(map=name, format="json").json
        gs.message(
            _("{0}: min={1:.3f} max={2:.3f} mean={3:.3f}").format(
                label, stats["min"], stats["max"], stats["mean"]
            )
        )


def main():
    options, flags = gs.parser()
    atexit.register(cleanup)
    tools = Tools()

    before = options["before"].split(",")
    after = options["after"].split(",")
    if len(before) != len(after):
        gs.fatal(_("The number of before and after maps must match"))
    n_bands = len(before)
    n_frames = int(options["frames"])
    output = options["output"]
    nprocs = int(options["nprocs"])

    names = frame_names(output, n_frames, n_bands)
    if not flags["p"]:
        check_outputs([name for band in names for name in band])

    if options["output_plan"]:
        start_name = options["output_plan"] + "_S"
        end_name = options["output_plan"] + "_E"
        check_outputs([start_name, end_name])
    else:
        start_name = tmp_raster("start")
        end_name = tmp_raster("end")

    cfg = {
        "primitive": options["primitive"],
        "mask_before": options["mask_before"],
        "mask_after": options["mask_after"],
        "dem": options["dem"],
        "direction": options["direction"],
        "coordinates": options["coordinates"].split(",")
        if options["coordinates"]
        else None,
        "plan_start": options["plan_start"],
        "plan_end": options["plan_end"],
        "roi_start": options["roi_start"],
        "roi_end": options["roi_end"],
        "bg_start": options["bg_start"],
        "bg_end": options["bg_end"],
        "blend_duration": options["blend_duration"],
        "invert": flags["i"],
    }

    if options["stages"]:
        gs.message(_("Building the animation plan from stages..."))
        with open(options["stages"]) as stage_file:
            stages = json.load(stage_file)
        if not isinstance(stages, list) or not stages:
            gs.fatal(_("The stages file must contain a non-empty list of stages"))
        stage_starts = []
        stage_ends = []
        for index, stage in enumerate(stages, start=1):
            stage_cfg = dict(cfg)
            stage_cfg.update(stage)
            stage_start = tmp_raster(f"stage{index}_start")
            stage_end = tmp_raster(f"stage{index}_end")
            build_plan(tools, stage_cfg, stage_start, stage_end)
            stage_starts.append(stage_start)
            stage_ends.append(stage_end)
        mapcalc(tools, start_name, f"min({', '.join(stage_starts)})")
        mapcalc(tools, end_name, f"max({', '.join(stage_ends)})")
    else:
        gs.message(
            _("Building the animation plan with primitive '{}'...").format(
                cfg["primitive"]
            )
        )
        build_plan(tools, cfg, start_name, end_name)

    report_plan(tools, start_name, end_name)
    if options["output_plan"]:
        tools.r_support(map=start_name, title="Animation plan: start times")
        tools.r_support(map=end_name, title="Animation plan: end times")
    if flags["p"]:
        return

    if flags["c"]:
        gs.message(_("Matching before statistics to after..."))
        before = [match_statistics(tools, b, a) for b, a in zip(before, after)]

    gs.message(_("Rendering {} frames...").format(n_frames))
    times = [index / (n_frames - 1) for index in range(n_frames)]
    for band, (band_before, band_after) in enumerate(zip(before, after)):
        expressions = []
        for name, time in zip(names[band], times):
            # r.mapcalc has no scientific notation, so spell the literals out.
            alpha = (
                f"max(0.0, min(1.0, ({time:.12f} - {start_name}) "
                f"/ max({end_name} - {start_name}, 0.0000000001)))"
            )
            expressions.append(
                f"{name} = (1.0 - {alpha}) * {band_before} + {alpha} * {band_after}"
            )
        path = gs.tempfile()
        TMP_FILES.append(path)
        with open(path, "w") as expression_file:
            expression_file.write("\n".join(expressions) + "\n")
        tools.r_mapcalc(file=path, nprocs=nprocs)
        tools.r_colors(map=",".join(names[band]), raster=band_after)
        for index, name in enumerate(names[band], start=1):
            tools.r_support(
                map=name,
                title=f"Frame {index} of {n_frames}",
                description=f"r.anim.morph {cfg['primitive']} band {band + 1}",
            )
        gs.percent(band + 1, n_bands, 1)

    gs.message(_("Frames written with basename <{}>").format(output))


if __name__ == "__main__":
    main()
