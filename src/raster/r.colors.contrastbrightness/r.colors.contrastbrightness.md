## DESCRIPTION

The *r.colors.contrastbrightness* module generates a contrasted version
of the input raster map. The contrast is the gain of the affine
transform, use values of 1.0-3.0 in case of an 8 bit image. The
brightness is the bias of the affine transform, use values of 0.0-100.0
in case of an 8 bit image.

## EXAMPLES

Contrast enhancement of an 8-bit raster band This does nothing to the
image:

```sh
r.colors.contrastbrightness min=0.0 max=255.0 contrast=1.0 brightness=0.0 input=myinraster output=myoutraster
```

This does change the contrast of the image:

```sh
r.colors.contrastbrightness min=0.0 max=255.0 contrast=3.0 brightness=0.0 input=myinraster output=myoutraster
```

This does change the brightness of the image:

```sh
r.colors.contrastbrightness min=0.0 max=255.0 contrast=1.0 brightness=100.0 input=myinraster output=myoutraster
```

## SEE ALSO

*[r.colors](https://grass.osgeo.org/grass-stable/manuals/r.colors.html),
[v.colors](https://grass.osgeo.org/grass-stable/manuals/v.colors.html),
[r3.colors](https://grass.osgeo.org/grass-stable/manuals/r3.colors.html),
[r.cpt2grass](r.cpt2grass.md),
[r.colors.matplotlib](r.colors.matplotlib.md)*

## AUTHOR

Yann Chemin, [JRC, Ispra, Italy](http://jrc.it/)
