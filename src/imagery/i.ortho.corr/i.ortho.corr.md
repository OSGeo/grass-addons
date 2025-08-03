## DESCRIPTION

*i.ortho.corr* allows to correct orthophotos using the camera angle map
create by *i.ortho.photo*.

It creates a new image by searching further images adjacent to the input
image. The output contains part of near images where the camera angle
value is optimal.

## NOTES

It requires a tile index to be created containing all the images to be
processed (e.g., GDAL's *gdaltindex* can create that):

```sh
gdaltindex tile.shp $GRASSDATA/$LOCATION/$MAPSET/cellhd/*imagery.ortho
```

The *field* option is used for the field's name which contains the path
to the file, the default is *location* that it is used by *gdaltindex*.
The *exclude* option serves to remove some tiles, for example when
having tiles from a different flight, they can be excluded by passing a
string or a regular expression.

## EXAMPLES

Create tile index:

```sh
gdaltindex tile.shp $GRASSDATA/$LOCATION/$MAPSET/cellhd/*imagery.ortho
```

Import tile index inside the mapset

```sh
v.in.ogr dns=tile.shp out=tile_images
```

Start *i.ortho.corr* with the default parameters, the output map's name
will be `image.ortho_corr`. You can use default parameters if you didn't
change the output prefix in i.ortho.photo:

```sh
i.ortho.corr input=image.ortho tiles=tile_images
```

Start *i.ortho.corr* with different parameters

```sh
i.ortho.corr input=image.photo tiles=tile_images osuffix=.photo csuffix=.camera
```

## SEE ALSO

*[i.ortho.photo](https://grass.osgeo.org/grass-stable/manuals/i.ortho.photo.html),
[i.ortho.rectify](i.ortho.rectify.md)*

## AUTHOR

Luca Delucchi, Fondazione E. Mach (Italy)
