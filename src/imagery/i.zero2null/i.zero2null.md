## DESCRIPTION

*i.zero2null* replaces zero cells with NULL cells at the edges of
imagery, e.g. Sentinel-2 scenes.

Sentinel-2 scenes can also have small patches of zero cells, typically
in water bodies. These patches are removed and filled with neighboring
cells.

## EXAMPLE

The Sentinel-2 scene
`S2B_MSIL2A_20190724T103029_N0213_R108_T32ULA_20190724T130550,
uuid: 0a7cb5ee-80d4-4d15-be19-0b3fdf40791f` shows unexpected no-data
pixels in lakes.

```sh
# download S2 scene affected by no.data pixels within the scene
i.sentinel.download settings=credentials.txt \
  uuid=0a7cb5ee-80d4-4d15-be19-0b3fdf40791f output=test_s2_scene

# show lst of granules in scene
i.sentinel.import -p input=test_s2_scene

# import selected bands of scene
i.sentinel.import input=test_s2_scene pattern='B0(2|3|4|8)_10m'
g.list raster
g.region raster=T32ULA_20190724T103029_B04_10m -p
```

[![image-alt](i_zero2null_s2_uncorr.png)](i_zero2null_s2_uncorr.png)  
*Figure: Sentinel-2 red band with undesired 0-value pixels*

```sh
# zoom to scene subset with undesired 0-value pixels
g.region n=5516940 s=5516840 w=334410 e=334550 res=10
# visualize pixel values, e.g. in red band
d.rast T32ULA_20190724T103029_B04_10m
d.rast.num T32ULA_20190724T103029_B04_10m text_color=blue

# fix 0-value pixels
i.zero2null map=T32ULA_20190724T103029_B02_10m,T32ULA_20190724T103029_B03_10m,T32ULA_20190724T103029_B04_10m,T32ULA_20190724T103029_B08_10m
# visualize updated pixel values (0 values now replaced), e.g. in red band
d.rast T32ULA_20190724T103029_B04_10m
d.rast.num T32ULA_20190724T103029_B04_10m text_color=blue
```

[![image-alt](i_zero2null_s2_corr.png)](i_zero2null_s2_corr.png)  
*Figure: Sentinel-2 red band after correction with *i.zero2null**

## SEE ALSO

*[i.sentinel](i.sentinel.md) module set*

## AUTHOR

Markus Metz, mundialis
