## DESCRIPTION

*r.learn.ml2* represents a front-end to the scikit learn python package.
The module enables scikit-learn classification and regression models to
be applied to GRASS GIS rasters that are stored as part of an imagery
group *group* or specified as individual maps in the optional *raster*
parameter.

The training component of the machine learning workflow is performed
using the *[r.learn.train](r.learn.train.md)* module. This module uses
training data consisting of labelled pixels in a GRASS GIS raster map,
or a GRASS GIS vector containing points, and develops a machine learning
model on the rasters within a GRASS imagery group. This model needs to
be saved to a file and can be automatically compressed if the .gz file
extension is used.

After a model is training, the *[r.learn.predict](r.learn.predict.md)*
module needs to be called, which will retrieve the saved and pre-fitted
model and apply it to a GRASS GIS imagery group.

## NOTES

*r.learn.ml2* uses the "scikit-learn" machine learning python package
(version ≥ 0.20) along with the "pandas" package. These packages need to
be installed within your GRASS GIS Python environment. For Linux users,
these packages should be available through the linux package manager.
For MS-Windows users using a 64 bit GRASS, the easiest way of installing
the packages is by using the precompiled binaries from [Christoph
Gohlke](http://www.lfd.uci.edu/~gohlke/pythonlibs/) and by using the
[OSGeo4W](https://grass.osgeo.org/download/software/ms-windows/)
installation method of GRASS, where the python setuptools can also be
installed. You can then use 'easy\_install pip' to install the pip
package manager. Then, you can download the NumPy+MKL and scikit-learn
.whl files.

## EXAMPLE

Here we are going to use the GRASS GIS sample North Carolina data set as
a basis to perform a landsat classification. We are going to classify a
Landsat 7 scene from 2000, using training information from an older
(1996) land cover dataset.

Landsat 7 (2000) bands 7,4,2 color composite example:

![image-alt](lsat7_2000_b742.png)

Note that this example must be run in the "landsat" mapset of the North
Carolina sample data set location.

First, we are going to generate some training pixels from an older
(1996) land cover classification:

```sh
g.region raster=landclass96 -p
r.random input=landclass96 npoints=1000 raster=training_pixels
```

Then we can use these training pixels to perform a classification on the
more recently obtained landsat 7 image:

```sh
# train a random forest classification model using r.learn.train
r.learn.train group=lsat7_2000 training_map=training_pixels \
    model_name=RandomForestClassifier n_estimators=500 save_model=rf_model.gz

# perform prediction using r.learn.predict
r.learn.predict group=lsat7_2000 load_model=rf_model.gz output=rf_classification

# check raster categories - they are automatically applied to the classification output
r.category rf_classification

# copy color scheme from landclass training map to result
r.colors rf_classification raster=training_pixels
```

Random forest classification result:

![image-alt](rfclassification.png)

## SEE ALSO

[r.learn.train](r.learn.train.md), [r.learn.predict](r.learn.predict.md)

## REFERENCES

Scikit-learn: Machine Learning in Python, Pedregosa et al., JMLR 12, pp.
2825-2830, 2011.

## AUTHOR

Steven Pawley
