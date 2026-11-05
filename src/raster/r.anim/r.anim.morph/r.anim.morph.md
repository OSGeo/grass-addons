## DESCRIPTION

*r.anim.morph* morphs a *before* raster into an *after* raster by writing a
numbered sequence of raster frames. Instead of fading every cell at the same
time, each cell follows its own schedule given by an **animation plan**
(Lobo, Appert and Pietriga 2019): a start-time raster S and an end-time
raster E in normalized time, where 0 is the first frame and 1 is the last.
A frame at time t shows the before value where t is below S, the after value
where t is above E, and a linear blend in between. Ordering the cells in
space is what makes a lake look like it is shrinking rather than fading.

Both inputs are given as one raster, or as one raster per band in the same
order (for example red, green, and blue). Frames are named
`<output>_001`, `<output>_002`, and so on, with the number of digits
matching **frames**. With several bands the names become
`<output>_b1_001`, `<output>_b2_001`, and so on.

### Regions, windows, and blend duration

Cells are split into a region of interest (ROI) given by **mask_before**
and **mask_after** (cells greater than zero) and the background outside it.
Cells of the ROI transition between **roi_start** and **roi_end**;
background cells transition between **bg_start** and **bg_end**. Setting
`roi_end=0.7 bg_start=0.7` stages the animation so the background changes
only after the ROI has finished.

Inside the ROI a primitive orders the cells from first to last. Each cell
blends over **blend_duration**, so a cell that starts at S ends at
S + blend_duration, capped at 1. A blend duration of 0 swaps the cell in a
single frame. The blend duration must fit inside the ROI window.

### Primitives

| Primitive | Order inside the ROI | Needs |
| --- | --- | --- |
| blend | every cell transitions over the ROI window | nothing |
| appearance | from the edge of the shape inward | mask_after |
| disappearance | from the edge of the shape inward | mask_before |
| contraction | cells leaving the shape, far from the new contour first | mask_before, optional mask_after |
| expansion | cells entering the shape, close to the old contour first | mask_after, optional mask_before |
| deformation | contraction and expansion together | mask_before, mask_after |
| radial | outward from **coordinates** (default: region center) | optional mask |
| directional | sweep in the compass **direction** | optional mask |
| dem | high elevation first (low first with **-i**) | dem, optional mask |
| plan | start and end times read from rasters | plan_start, plan_end |

For contraction, expansion, and deformation, cells that belong to both
masks transition uniformly over the ROI window while the cells that leave or
enter the shape are ordered by their distance to the other contour.
Contraction without **mask_after** shrinks the shape to nothing, and
expansion without **mask_before** grows it from nothing. Distances are
computed with *r.grow.distance* in map units. Radial, directional, and dem
normalize their ordering over the ROI, so the farthest, last, or lowest
cell of the ROI finishes exactly at **roi_end**; the **-i** flag reverses
their order.

The **plan** primitive reads S and E from **plan_start** and
**plan_end**, for example rasters saved earlier with **output_plan** or
plans built with *r.mapcalc*. Values are clamped to the range 0 to 1.

### Stages

A JSON file given with **stages** describes a list of stages that are
combined into a single plan by taking, for each cell, the earliest start
and the latest end. Each stage is an object whose keys are the tool options
(`primitive`, `mask_before`, `mask_after`, `dem`, `direction`,
`coordinates` as a two-element list, `plan_start`, `plan_end`,
`roi_start`, `roi_end`, `bg_start`, `bg_end`, `blend_duration`, and
`invert`); missing keys fall back to the command line.

```json
[
  {
    "primitive": "contraction",
    "mask_before": "lake_before",
    "mask_after": "lake_after",
    "roi_start": 0.0,
    "roi_end": 0.6,
    "bg_start": 0.6,
    "bg_end": 0.6,
    "blend_duration": 0.2
  },
  {
    "primitive": "blend",
    "roi_start": 0.6,
    "roi_end": 1.0
  }
]
```

### Flags

The **-c** flag rescales each before band to the mean and standard
deviation of its after band before rendering, which reduces the brightness
jump between scenes acquired under different conditions. The **-p** flag
computes and reports the plan without writing frames; together with
**output_plan** it saves the plan for inspection or reuse.

## NOTES

All computations use the current computational region and resolution; input
rasters are resampled to it. Frames are written by a single *r.mapcalc* call
per band, so memory use does not depend on the raster size and **nprocs**
speeds up rendering.

Null cells of the before and after rasters stay null in every frame. Null
cells of a mask count as background. Null cells of the dem transition last.
Rasters given as masks are compared with zero, so any raster can serve as a
mask.

Every frame receives the color table of its after raster so the animation
does not flicker. Frames can be played with *g.gui.animation* or exported
with *r.out.png* and turned into a video with an external tool. Frames of a
multi-band animation can be combined with *r.composite* or displayed with
*d.rgb*.

With several bands, the number of output rasters is **frames** times the
number of bands. Existing frames are only replaced with **--overwrite**.

## EXAMPLES

All examples use the North Carolina sample dataset. A full walkthrough on
real imagery, from a *t.stac* import of Sentinel-2 scenes to an MP4 of a
receding reservoir, is in the tutorial
[Animating the Falls Lake drawdown with r.anim.morph](https://learning.openplains.com/content/blog/animating_water_level_change_with_r_anim_morph.html).

### Fade between two Landsat scenes

The 1987 scene is stored in the *landsat* mapset of the sample dataset.

```sh
g.region raster=lsat7_2002_30 -p
r.anim.morph before=lsat5_1987_30@landsat,lsat5_1987_20@landsat,lsat5_1987_10@landsat \
    after=lsat7_2002_30,lsat7_2002_20,lsat7_2002_10 \
    output=landsat frames=24 -c
r.composite red=landsat_b1_12 green=landsat_b2_12 blue=landsat_b3_12 \
    output=landsat_12
```

### Shrinking lake

Two thresholds of the elevation model stand in for water extents before and
after a drawdown. The area between them drains from the far shore toward
the new shoreline, then the background fades.

```sh
g.region raster=elevation -p
r.mapcalc "lake_before = if(elevation < 100, 1, 0)"
r.mapcalc "lake_after = if(elevation < 95, 1, 0)"
r.anim.morph before=lake_before after=lake_after output=lake \
    primitive=contraction mask_before=lake_before mask_after=lake_after \
    roi_end=0.85 bg_start=0.85 blend_duration=0.2 frames=48 \
    output_plan=lake_plan
g.gui.animation raster=$(g.list type=raster pattern="lake_[0-9]*" separator=comma)
```

### Snow line moving downhill

The after raster is a constant white surface that borrows the grey color
table of the shaded relief, so the frames inherit a full grey ramp.

```sh
g.region raster=elevation -p
r.mapcalc "snow = 255"
r.colors map=snow raster=elevation_shade
r.anim.morph before=elevation_shade after=snow output=snowline \
    primitive=dem dem=elevation blend_duration=0.1 frames=30
```

### Reuse a saved plan

Inspect and edit the plan from the shrinking lake example, then render it
again with the plan primitive.

```sh
r.mapcalc "lake_plan_S2 = lake_plan_S * 0.5"
r.anim.morph before=lake_before after=lake_after output=lake2 \
    primitive=plan plan_start=lake_plan_S2 plan_end=lake_plan_E frames=48
```

## REFERENCES

Lobo, M.-J., Appert, C., and Pietriga, E. (2019). Animation plans for
before-and-after satellite images. IEEE Transactions on Visualization and
Computer Graphics, 25(2), 1347-1360.
[doi:10.1109/TVCG.2018.2796557](https://doi.org/10.1109/TVCG.2018.2796557)

## SEE ALSO

*[g.gui.animation](g.gui.animation.md),
[r.anim](r.anim.md),
[r.blend](r.blend.md),
[r.composite](r.composite.md),
[r.grow.distance](r.grow.distance.md),
[r.series.interp](r.series.interp.md)*

## AUTHORS

Corey T. White, [OpenPlains Inc.](https://openplains.com/)
