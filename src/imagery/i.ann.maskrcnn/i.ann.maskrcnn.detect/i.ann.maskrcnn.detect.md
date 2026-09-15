## DESCRIPTION

*i.ann.maskrcnn.detect* allows the user to use a Mask R-CNN model to
detect features in GRASS GIS raster maps or georeferenced files and
extract them either as areas or points. The module creates a separate
map for each class.

## NOTES

The detection may be used for raster maps imported in GRASS GIS or for
external files (or using both). To use raster maps in GRASS GIS, you
need to pass them in three bands following the order used during the
training, e.g. if the training has been made on RGB images, use
*band1=\*.red*, *band1=\*.green* and *band3=\*.blue*. To pass multiple
images, put more maps into *band\** parameters, divided by ",".

The detection may be used also for multiple external files. However, all
files for the detection must be in one directory specified in the
*images\_directory* parameter. Even when using only one image, the
module finds it through this parameter.

When detecting, you can use new names of classes. Classes in the model
are not referenced by their name, but by their order. It means that if
the model was trained with classes *corn,rice* and you use
*i.ann.maskrcnn.detect* with classes *zea,oryza*, zea areas will present
areas detected as corn and oryza areas will present areas detected as
rice.

If the external file is georeferenced externally (by a worldfile or an
*.aux.xml* file), please use *-e* flag.

## EXAMPLES

### Detect buildings and lakes and import them as areas

One map imported in GRASS GIS:

```sh
i.ann.maskrcnn.detect band1=map1.red band2=map1.green band3=map1.blue classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5
```

Two maps (map1, map2) imported in GRASS GIS:

```sh
i.ann.maskrcnn.detect band1=map1.red,map2.red band2=map1.green,map2.green band3=map1.blue,map2.blue classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5
```

External files, the georeferencing is internal (GeoTIFF):

```sh
i.ann.maskrcnn.detect images_directory=/home/user/Documents/georeferenced_images classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5 images_format=tif
```

External files, the georeferencing is external:

```sh
i.ann.maskrcnn.detect images_directory=/home/user/Documents/georeferenced_images classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5 images_format=png -e
```

### Detect cottages and plattenbaus and import them as points

```sh
i.ann.maskrcnn.detect band1=map1.red band2=map1.green band3=map1.blue classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5 output_type=point
```

## SEE ALSO

*[Mask R-CNN in GRASS GIS](i.ann.maskrcnn.md),
[i.ann.maskrcnn.train](i.ann.maskrcnn.train.md)*

## AUTHOR

Ondrej Pesek
