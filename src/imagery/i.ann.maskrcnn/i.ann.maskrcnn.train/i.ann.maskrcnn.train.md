## DESCRIPTION

*i.ann.maskrcnn.train* allows the user to train a Mask R-CNN model on
his own dataset. The dataset has to be prepared in a predefined
structure.

### DATASET STRUCTURE

Training dataset should be in the following structure:

dataset-directory

- imagenumber
  - imagenumber.jpg (training image)
  - imagenumber-class1-number.png (mask for one instance of class1)
  - imagenumber-class1-number.png (mask for another instance of
        class1)
  - ...
- imagenumber2
  - imagenumber2.jpg
  - imagenumber2-class1-number.png (mask for one instance of class1)
  - imagenumber2-class2-number.png (mask for another class instance)
  - ...

The described structure of directories is required. Pictures must be
\*.jpg files with 3 channels (for example RGB), masks must be \*.png
files consisting of numbers between 1 and 255 (object instance) and 0s
(elsewhere). A mask file for each instance of an object should be
provided separately distinguished by the suffix number.

## NOTES

If you are using initial weights (the *model* parameter), epochs are
divided into three segments. Firstly training layers 5+, then
fine-tuning layers 4+ and the last segment is fine-tuning the whole
architecture. Ending number of epochs is shown for your segment, not for
the whole training.

The usage of the *-b* flag will result in an activation of batch
normalization layers training. By default, this option is set to False,
as it is not recommended to train them when using just small batches
(batch is defined by the *images\_per\_gpu* parameter).

If the dataset consists of images of the same size, the user may use the
*-n* flag to avoid resizing or padding of images. When the flag is not
used, images are resized to have their longer side equal to the value of
the *images\_max\_dim* parameter and the shorter side longer or equal to
the value of the *images\_min\_dim* parameter and zero-padded to be of
shape

images\_max\_dim x images\_max\_dim

. It results in the fact that even images of different sizes may be
used.

After each epoch, the current model is saved. It allows the user to stop
the training when he feels satisfied with loss functions. It also allows
the user to test models even during the training (and, again, stop it
even before the last epoch).

## EXAMPLES

Dataset for examples:

crops

- 000000
  - 000000.jpg
  - 000000-corn-0.png
  - 000000-corn-1.png
  - ...
- 000001
  - 000001.jpg
  - 000001-corn-0.png
  - 000001-rice-0.png
  - ...

### Training from scratch

```sh
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops
```

After default number of epochs, we will get a model where the first
class is trained to detect corn fields and the second one to detect rice
fields.

If we use the command with reversed classes order, we will get a model
where the first class is trained to detect rice fields and the second
one to detect corn fields.

```sh
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=rice,corn logs=/home/user/Documents/logs name=crops
```

The name of the model does not have to be the same as the dataset folder
but should be referring to the task of the dataset. A good name for this
one (referring also to the order of classes) could be also this one:

```sh
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=rice,corn logs=/home/user/Documents/logs name=rice_corn
```

### Training from a pretrained model

We can use a pretrained model to make our training faster. It is
necessary for the model to be trained on the same channels and similar
features, but it does not have to be the same ones (e.g. model trained
on swimming pools in maps can be used for a training on buildings in
maps).

A model trained on different classes (use *-e* flag to exclude head
weights).

```sh
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops model=/home/user/Documents/models/buildings.h5 -e
```

A model trained on the same classes.

```sh
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops model=/home/user/Documents/models/corn_rice.h5
```

### Fine-tuning a model

It is also possible to stop your training and then continue. To continue
in the training, just use the last saved epoch as a pretrained model.

```sh
i.ann.maskrcnn.train training_dataset=/home/user/Documents/crops classes=corn,rice logs=/home/user/Documents/logs name=crops model=/home/user/Documents/models/mask_rcnn_crops_0005.h5
```

## SEE ALSO

*[Mask R-CNN in GRASS GIS](i.ann.maskrcnn.md),
[i.ann.maskrcnn.detect](i.ann.maskrcnn.detect.md)*

## AUTHOR

Ondrej Pesek
