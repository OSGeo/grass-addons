## DESCRIPTION

*r.confusionmatrix* calculates the confusion matrix, overall, user and
producer accuracies, the omission and commission errors and the Kappa
coefficient of classification result using *r.kappa*.

## NOTES

The reference can be a raster map **raster\_reference** or a vector map
**vector\_reference** with a **column** containing the class labels as
integer numbers.

In case of vector reference, this map is rasterized according to the
extent and resolution of the **classification** raster map.

## EXAMPLE

Compute the confusion matrix as a CSV file including description of the
accuracies:

```sh
r.confusionmatrix classification=classified raster_reference=trainingmap csvfile=test.csv -d
```

## SEE ALSO

*[r.kappa](https://grass.osgeo.org/grass-stable/manuals/r.kappa.html)*

## AUTHOR

Anika Weinmann, [mundialis GmbH & Co. KG](https://www.mundialis.de/)
