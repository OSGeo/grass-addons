## DESCRIPTION

***t.rast.null*** manages NULL-values of the input space time raster
dataset.

The **setnull** parameter is used to specify values in the ranges to be
set to NULL. A range is either a single value (e.g., 5.3), or a pair of
values (e.g., 4.76-34.56). Existing NULL-values are left NULL, unless
the null argument is requested.

The **null** parameter eliminates the NULL value and replaces it with
the given value. This argument is applied only to existing NULL values,
and not to the NULLs created by the **setnull** argument.

## EXAMPLES

Set specific values (0,-1 and -2) of a space time raster dataset to
NULL:

```sh
    t.rast.null input=MY_INPUT_DATASET setnull=0,-1,-2
```

## SEE ALSO

*[r.null](https://grass.osgeo.org/grass-stable/manuals/r.null.html)*

## AUTHOR

Luca Delucchi, Fondazione Edmund Mach
