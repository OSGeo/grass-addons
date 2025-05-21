[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# r.earthworks

An add-on module for computational terrain modeling in GRASS GIS.

## Installation

`g.extension  extension=r.earthworks url=https://github.com/baharmon/r.earthworks`

## Example

To grade a road crossing over a valley in the
[North Carolina](https://grass.osgeo.org/sampledata/north_carolina/nc_basic_spm_grass7.zip)
sample dataset, run:

```sh
g.region n=217700 s=216200 w=639200 e=640700 res=10
r.earthworks elevation=elevation earthworks=earthworks lines=roadsmajor z=95 rate=0.25 operation=fill flat=25
r.contour input=earthworks output=contours step=2
```

| Elevation | Earthworks |
| --------- | ---------- |
| ![Elevation](r_earthworks_07.png) | ![Earthworks](r_earthworks_08.png) |
