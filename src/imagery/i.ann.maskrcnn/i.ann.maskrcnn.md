---
name: i.ann.maskrcnn
description: Mask R-CNN toolset
---

# Mask R-CNN toolset

## DESCRIPTION

Mask R-CNN tools allow the user to train his own model and use it for a
detection of objects, or to use a model provided by someone else. It can
be seen as a supervised classification using convolutional neural
networks.

The training is done using module *i.ann.maskrcnn.train*. The user feeds
the module with training data consisting of images and masks for each
instance of intended classes, and gets a model. For difficult tasks and
when not using a pretrained model, the training may take even weeks; in
case of a good pretrained model and powerful PC with GPU support, the
training could get good results after 1 day and even less.

When the user has a model, it can be used for the detection.
*i.ann.maskrcnn.detect* detects classes learned during the training and
extracts from given images vectors corresponding to detected objects.
Objects can be extracted either as areas or points.

## DEPENDENCIES

*i.ann.maskrcnn.\** modules contain a lot of external Python
dependencies. To run modules, it is necessary to have them installed.
Modules use Python3, so please install Python3 versions.

- NumPy
- Pillow
- SciPy
- Cython
- scikit-image
- OSGeo
- TensorFlow \< 2.0
- Keras
- h5py

After dependencies are fulfilled, modules can be installed in GRASS GIS
\>= 7.8 using the *g.extension* module:

```sh
g.extension extension=maskrcnn
```

## MODULES

*[i.ann.maskrcnn.train](i.ann.maskrcnn.train.md),
[i.ann.maskrcnn.detect](i.ann.maskrcnn.detect.md)*

## AUTHOR

Ondrej Pesek
