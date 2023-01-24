# i.landsat8.swist

*i.landsat8.swlst* is a GRASS GIS add-on, implementing a practical Split-Window (SW)
algorithm, estimating land surface temperature (LST), from the Thermal Infra-Red
Sensor (TIRS) aboard Landsat 8 with an accuracy of better than 1.0 K.

## Quick examples

After installation (see section *Installation* below), from within a GRASS-GIS
session, retrieve usage details via `i.landsat8.swlst --help`

The shortest call for processing a complete Landsat8 scene normally is:

```bash
i.landsat8.swlst mtl=MTL prefix=B landcover=FROM_GLC
```

where:

- `mtl=` the name of the MTL metadata file (normally with a `.txt` extension)
- `prefix=` the prefix of the band names imported in GRASS GIS' data base
- `landcover=` the name of a FROM-GLC map product that covers the extent of the
  Landsat8 scene under processing. FORM-GLC products are available at
  <http://data.ess.tsinghua.edu.cn/>.

A faster call is to use existing maps for all in-between
processing steps: at-satellite temperatures, cloud and emissivity maps.

- At-satellite temperature maps (options `t10`, `t11`) may be derived via
  the `i.landsat.toar` module. Note that `i.landsat.toar` does not
  process single bands selectively.

- The `clouds` option can be any user-defined map. Essentialy, it applies
  the given map as an inverted mask.

- The emissivity maps, derived by the module itself, can be saved once
  via the `emissivity_out` and `delta_emissivity_out` options and used
  afterwards via the `emissivity` and `delta_emissivity` options. Expert
  users, however, may use emissivity maps from other sources directly.
  An example command may be:

```bash
  i.landsat8.swlst t10=T10 t11=T11 clouds=Cloud_Map \
      emissivity=Average_Emissivity_Map delta_emissivity=Delta_Emissivity_Map \
          landcover=FROM_GLC -k -c
```

For details and more examples, read the manual.

## Description

The algorithm removes the atmospheric effect through differential
atmospheric absorption in the two adjacent thermal infrared channels
centered at about 11 and 12 μm.

The components of the algorithm estimating LST values are at-satellite
brightness temperature (BT); land surface emissivities (LSEs); and the
coefficients of the main Split-Window equation (SWCs).

**LSEs** are derived from an established look-up table linking the FROM-GLC
classification scheme to average emissivities. The NDVI and the FVC are *not*
computed each time an LST estimation is requested. Read [0] for details.

The **SWCs** depend on each pixel's column water vapor (CWV). **CWV** values are
retrieved based on a modified Split-Window Covariance-Variance Matrix Ratio
method (MSWCVMR) [1, 2]. **Note**, the spatial discontinuity found in the
images of the retrieved CWV, is attributed to the data gap in the images caused
by stray light outside of the FOV of the TIRS instrument [2]. In addition, the
size of the spatial window querying for CWV values in adjacent pixels, is a key
parameter of the MSWCVMR method. It influences accuracy and performance. In [2]
it is stated:

> A small window size n (N = n * n, see equation (1a)) cannot ensure a high
> correlation between two bands' temperatures due to the instrument noise. In
> contrast, the size cannot be too large because the variations in the surface
> and atmospheric conditions become larger as the size increases.

The combination of the brightness temperatures to estimate the LST bases upon
the equation:

```text
LST = b0 +
    + ( b1 + b2 * ( 1 - ae ) / ae + b3 * de / ae^2 ) * ( t10 + t11 ) / 2 +
    + ( b4 + b5 * ( 1 - ae ) / ae + b6 * de / ae^2 ) * ( t10 - t11 ) / 2 +
    + b7 * ( t10 - t11 )^2
```

Note, however, **the last quadratic term** of the Split-Window equation **is
applied only over barren land**. [Reference Required!]

**BTs** are derived from Landsat 8's TIRS channels 10 and 11. Prior to any
processing, the raw digital numbers are filtered for clouds.

To produce an LST map, the algorithm requires at minimum:

- TIRS bands 10 and 11
- the acquisition's metadata file (MTL)
- a Finer Resolution Observation & Monitoring of Global Land Cover (FROM-GLC)
  product

## Installation

### Requirements

See [GRASS Addons SVN repository, README file, Installation - Code
Compilation](https://svn.osgeo.org/grass/grass-addons/README)

### Steps

Making the script `i.lansat8.swlst` available from within any GRASS-GIS ver.
7.x session, may be done via the following steps:

1. launch a GRASS-GIS’ ver. 7.x session

2. navigate into the script’s source directory

3. execute `make MODULE_TOPDIR=$GISBASE`

## Implementation notes

- Created on Wed Mar 18 10:00:53 2015
- First all-through execution: Tue May 12 21:50:42 EEST 2015

## To Do

[High Priority]

- ~~Fix retrieval of adjacent subranges (exclude 6, get it only if there is no
  match for subranges 1, 2, 3, 4, and 5)~~

- Evaluate BIG mapcalc expressions -- are they correct?  I guess so ;-)
  - ~~Expression for Column Water Vapor~~
  - ~~CWV output values range -- is it rational?~~ It was not. There is a
    typo in paper [0]. The correct order of the coefficients is in papers [1,
    2].
  - ~~Expression for Land Surface Temperature~~
  - ~~LST output values range -- is it rational?  At the moment, not!~~
    Fixed. The main Split-Window equation was wrong.

- ~~Why is the LST out of range when using a fixed land cover class?~~ Cloudy
  pixels are, mainly, the reason. Better cloud masking is the solution.
- ~~Why does the multi-step approach on deriving the CWV map differ from the
  single big mapcalc expression?~~ **Fixed**
- ~~Implement direct conversion of B10, B11 to brightness temperature values.~~
  **Done**
- ~~Get the FROM-GLC map,~~ **Found**
- ~~implement mechanism to read land cover classes from it
  and use'm to retrieve emissivities~~ **Done**
- ~~How to use the FVC?~~ Don't. Just **use the Look-up table** (see [\*] for
  details).
- ~~Save average emissivity and delta emissivity maps for caching (re-use in
  subsequent trials, huge time saver!)~~ **Implemented**

[Mid]

- ~~Redo the example screenshots for the manual after corrections for CWV, LST
  equations.~~
- Use existing i.emissivity?  Not exactly compatible -- read paper for details.
  Anyhow, options to input average and delta emissivity maps implemented.
- Raster Row I/O -- Maybe *not* an option: see discussion with Pietro Zambelli
- How to perform pixel value validity checks for in-between and end products?
  `r.mapcalc` can't do this. Best to implement a test checking the values
  on-the-fly while they are created. A C-function?

[Low]

- ~~Test for too small region?~~ Works for a region of 267 rows x 267 cols
  (71289 cells)
- Deduplicate code in `split_window_lst` class, in functions
`_build_average_emissivity_mapcalc()` and
`_build_delta_emissivity_mapcalc()`
- Implement a median window filter, as another option in addition to mean.
- Profiling
- Implement a complete cloud masking function using the BQA image. Support for
  user requested confidence or types of clouds (?). Eg: options=
  clouds,cirrus,high,low ?
- ~~Multi-Threading? Note, r.mapcalc is already.~~

[\*] Details: the authors followed the CBEM method. Based on the FROM-GLC map,
they derived the following look-up table (LUT):

```text
Emissivity Class|TIRS10|TIRS11
Cropland|0.971|0.968
Forest|0.995|0.996
Grasslands|0.97|0.971
Shrublands|0.969|0.97
Wetlands|0.992|0.998
Waterbodies|0.992|0.998
Tundra|0.98|0.984
Impervious|0.973|0.981
Barren Land|0.969|0.978
Snow and ice|0.992|0.998
```

## References

- [0] Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao,
  Shaohua. 2015. "A Practical Split-Window Algorithm for Estimating
  Land Surface Temperature from Landsat 8 Data." Remote Sens. 7, no.
  1: 647-665.
  <http://www.mdpi.com/2072-4292/7/1/647/htm\#sthash.ba1pt9hj.dpuf>
- [1] Huazhong Ren, Chen Du, Qiming Qin, Rongyuan Liu, Jinjie Meng,
  and Jing Li. "Atmospheric Water Vapor Retrieval from Landsat 8 and
  Its Validation." 3045--3048. IEEE, 2014.
- [2] Ren, H., Du, C., Liu, R., Qin, Q., Yan, G., Li, Z. L., & Meng, J.
  (2015). Atmospheric water vapor retrieval from Landsat 8 thermal infrared
  images. Journal of Geophysical Research: Atmospheres, 120(5), 1723-1738.
- [3] FROM-GLC products, <http://data.ess.tsinghua.edu.cn/>

## Ευχαριστώ

- Yann Chemin
- Pietro Zambelli
- StackExchange contributors
- Sajid Pareeth
- Georgios Alexandris, Anthoula Alexandri
- Special thanks to author Huazhong Ren for commenting on questions (personal
  communication)
- Stefan Blumentrath
