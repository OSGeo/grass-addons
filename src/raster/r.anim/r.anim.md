---
name: r.anim
description: Toolset for spatially-aware animated transitions between rasters
---

# Toolset for spatially-aware animated transitions between rasters

## DESCRIPTION

The *r.anim* toolset generates smooth, spatially-aware animated
transitions between raster maps. *In-betweening* is the
process of generating the intermediate frames that carry one image into
another. Each tool in the toolset turns a small number of input rasters
into a numbered sequence of output frames that can be played back with
*[g.gui.animation](g.gui.animation.md)* or exported to an animated GIF or
video with external tools such as `ffmpeg` or ImageMagick.

Unlike a uniform cross-dissolve, the toolset lets different pixels
transition at different times, so the motion in the animation reflects
*where* and *how* the change happens rather than simply fading the whole
scene at once.

## MODULES

*[r.anim.morph](r.anim.morph.md)* morphs a *before* raster into an
*after* raster using the Baia animation-plan framework
([Lobo, Appert and Pietriga 2019](https://doi.org/10.1109/TVCG.2018.2796557)),
with primitives for contraction, expansion, deformation, appearance,
disappearance, directional, radial, and elevation-ordered transitions.
The tutorial
[Animating the Falls Lake drawdown with r.anim.morph](https://learning.openplains.com/content/blog/animating_water_level_change_with_r_anim_morph.html)
walks through a complete example on Sentinel-2 imagery.

The following members are planned:

- *(WIP)* *r.anim.flow* - optical-flow (warp-based) morphing between two
  rasters.
- *(WIP)* *r.anim.series* - interpolation of a space-time raster dataset
  (STRDS) into video-rate frames.

## INSTALLATION

The toolset can be installed using the *g.extension* tool:

```sh
g.extension extension=r.anim
```

A single member can be installed on its own, for example:

```sh
g.extension extension=r.anim.morph
```

## SEE ALSO

*[g.gui.animation](g.gui.animation.md),
[r.series.interp](r.series.interp.md),
[r.anim.morph](r.anim.morph.md)*

## AUTHORS

Corey T. White, [OpenPlains Inc.](https://openplains.com/)
