## DESCRIPTION

*r.forestfrag* Computes the forest fragmentation following the
methodology proposed by Riitters et al. (2000). See [this
article](https://www.ecologyandsociety.org/vol4/iss2/art3/) for a
detailed explanation.

It follows a "sliding window" algorithm with overlapping windows. The
amount of forest and its occurrence as adjacent forest pixels within
fixed-area "moving-windows" surrounding each forest pixel is measured.
The window size is user-defined. The result is stored at the location of
the center pixel. Thus, a pixel value in the derived map refers to
"between-pixel" fragmentation around the corresponding forest location.

As input it requires a binary map with (1) forest and (0) non-forest.
Obviously, one can replace forest any other land cover type. If one
wants to exclude the influence of a specific land cover type, e.g.,
water bodies, it should be classified as no-data (NA) in the input map.
See e.g., [blog
post](https://pvanb.wordpress.com/2016/03/25/update-of-r-forestfrag-addon/).

Let *Pf* be the proportion of pixels in the window that are forested.
Define *Pff* (strictly) as the proportion of all adjacent (cardinal
directions only) pixel pairs that include at least one forest pixel, for
which both pixels are forested. *Pff* thus (roughly) estimates the
conditional probability that, given a pixel of forest, its neighbor is
also forest. The classification model then identifies six fragmentation
categories as:

```sh
interior:       Pf = 1.0
patch:          Pf < 0.4
transitional:   0.4 ≤ Pf < 0.6
edge:           Pf ≥ 0.6 and Pf - Pff < 0
perforated:     Pf ≥ 0.6 and Pf - Pff > 0
undetermined:   Pf ≥ 0.6 and Pf = Pff
```

## NOTES

- The moving window size is user-defined (default=3) and must be an
    odd number. If an even number is given, the function will stop with
    an error message.
- No-data cells are ignored. This means that statistics at the raster
    edges are based on fewer cells (smaller) moving windows. If this is
    a problem, the user can choose to have the output raster trimmed
    with a number of raster cells equal to 1/2 \* the size of the moving
    window.
- The function respects the region. However, the user has the option
    to set the region to match the input layer.

## EXAMPLE

In the North Carolina sample Location, set the computational region to
match the land classification raster map:

```sh
g.region raster=landclass96
```

Then mark all cells which are forest as 1 and everything else as zero:

```sh
r.mapcalc "forest = if(landclass96 == 5, 1, 0)"
```

Use the new forest presence raster map to compute the forest
fragmentation index with window size 7:

```sh
r.forestfrag input=forest output=fragmentation window=7
```

![image-alt](r_forestfrag_window_7.png)
![image-alt](r_forestfrag_window_11.png)

*Two forest fragmentation indices with window size 7 (left) and 11
(right) show how increasing window size increases the amount of edges.*

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.li](https://grass.osgeo.org/grass-stable/manuals/r.li.html)*

The addon is based on the
[r.forestfrag.sh](https://grasswiki.osgeo.org/wiki/AddOns/GRASS_6#r.forestfrag)
script, with as extra options user-defined moving window size, option to
trim the region (by default it respects the region) and a better
handling of no-data cells.

## REFERENCES

Riitters, K., J. Wickham, R. O'Neill, B. Jones, and E. Smith. 2000.
Global-scale patterns of forest fragmentation. Conservation Ecology
4(2): 3. \[online\] URL: <https://www.consecol.org/vol4/iss2/art3/>

## AUTHORS

Emmanuel Sambale (original shell version)  
Stefan Sylla (original shell version)  
Paulo van Breugel (Python version, user-defined moving window size)  
Vaclav Petras (major code clean up)
