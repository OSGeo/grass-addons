#!/usr/bin/env python3
#
############################################################################
#
# MODULE:	    i.ann.maskrcnn.train
# AUTHOR(S):	Ondrej Pesek <pesej.ondrek@gmail.com>
# PURPOSE:	    Train your Mask R-CNN network
# COPYRIGHT:	(C) 2017 Ondrej Pesek and the GRASS Development Team
#
# 		This program is free software under the GNU General
# 		Public License (>=v2). Read the file COPYING that
# 		comes with GRASS for details.
#
#############################################################################

# %module
# % description: Train your Mask R-CNN network
# % keyword: ann
# % keyword: vector
# % keyword: raster
# %end
# %flag
# %  key: e
# %  description: Pretrained weights were trained on another classes / resolution / sizes
# %end
# %flag
# %  key: s
# %  description: Do not use 10 % of images and save their list to logs dir
# %end
# %flag
# %  key: b
# %  description: Train also batch normalization layers (not recommended for small batches)
# %end
# %flag
# %  key: n
# %  description: No resizing or padding of images (images must be of the same size)
# %end
# %option G_OPT_M_DIR
# % key: training_dataset
# % label: Path to the dataset with images and masks
# % required: yes
# %end
# %option G_OPT_F_INPUT
# % key: model
# % type: string
# % label: Path to the .h5 file to use as initial values
# % description: Keep empty to train from a scratch
# % required: no
# % multiple: no
# %end
# %option
# % key: classes
# % type: string
# % label: Names of classes separated with ","
# % required: yes
# % multiple: yes
# %end
# %option G_OPT_M_DIR
# % key: logs
# % label: Path to the directory in which will be models saved
# % required: yes
# %end
# %option
# % key: name
# % type: string
# % label: Name for output models
# % required: yes
# %end
# %option
# % key: epochs
# % type: integer
# % label: Number of epochs
# % required: no
# % multiple: no
# % answer: 200
# % guisection: Training parameters
# %end
# %option
# % key: steps_per_epoch
# % type: integer
# % label: Steps per each epoch
# % required: no
# % multiple: no
# % answer: 3000
# % guisection: Training parameters
# %end
# %option
# % key: rois_per_image
# % type: integer
# % label: How many ROIs train per image
# % required: no
# % multiple: no
# % answer: 64
# % guisection: Training parameters
# %end
# %option
# % key: images_per_gpu
# % type: integer
# % label: Number of images per GPU
# % description: Bigger number means faster training but needs a bigger GPU
# % required: no
# % multiple: no
# % answer: 1
# % guisection: Training parameters
# %end
# %option
# % key: gpu_count
# % type: integer
# % label: Number of GPUs to be used
# % required: no
# % multiple: no
# % answer: 1
# % guisection: Training parameters
# %end
# %option
# % key: mini_mask_size
# % type: integer
# % label: Size of mini mask separated with ","
# % description: To use full sized masks, keep empty. Mini mask saves memory at the expense of precision
# % required: no
# % multiple: yes
# % guisection: Training parameters
# %end
# %option
# % key: validation_steps
# % type: integer
# % label: Number of validation steps
# % description: Bigger number means more accurate estimation of the model precision
# % required: no
# % multiple: no
# % answer: 100
# % guisection: Training parameters
# %end
# %option
# % key: images_min_dim
# % type: integer
# % label: Minimum length of images sides
# % description: Images will be resized to have their shortest side at least of this value (has to be a multiple of 64)
# % required: no
# % multiple: no
# % answer: 256
# % guisection: Training parameters
# %end
# %option
# % key: images_max_dim
# % type: integer
# % label: Maximum length of images sides
# % description: Images will be resized to have their longest side of this value (has to be a multiple of 64)
# % required: no
# % multiple: no
# % answer: 1280
# % guisection: Training parameters
# %end
# %option
# % key: backbone
# % type: string
# % label: Backbone architecture
# % required: no
# % multiple: no
# % answer: resnet101
# % options: resnet50,resnet101
# % guisection: Training parameters
# %end


import grass.script as gscript
from grass.script.utils import get_lib_path
import os
import sys
from random import shuffle

path = get_lib_path(modname="maskrcnn", libname="model")
if path is None:
    grass.script.fatal("Not able to find the maskrcnn library directory.")
sys.path.append(path)


def main(options, flags):

    from config import ModelConfig
    import utils
    import model as modellib

    try:
        dataset = options["training_dataset"]
        initialWeights = options["model"]
        classes = options["classes"]
        name = options["name"]
        logs = options["logs"]
        epochs = int(options["epochs"])
        stepsPerEpoch = int(options["steps_per_epoch"])
        ROIsPerImage = int(options["rois_per_image"])
        imagesPerGPU = int(options["images_per_gpu"])
        GPUcount = int(options["gpu_count"])
        miniMaskSize = options["mini_mask_size"]
        validationSteps = int(options["validation_steps"])
        imMaxDim = int(options["images_max_dim"])
        imMinDim = int(options["images_min_dim"])
        backbone = options["backbone"]
    except KeyError:
        # GRASS parses keys and values as bytes instead of strings
        dataset = options[b"training_dataset"].decode("utf-8")
        initialWeights = options[b"model"].decode("utf-8")
        classes = options[b"classes"].decode("utf-8").split(",")
        name = options[b"name"].decode("utf-8")
        logs = options[b"logs"].decode("utf-8")
        epochs = int(options[b"epochs"])
        stepsPerEpoch = int(options[b"steps_per_epoch"])
        ROIsPerImage = int(options[b"rois_per_image"])
        imagesPerGPU = int(options[b"images_per_gpu"])
        GPUcount = int(options[b"gpu_count"])
        miniMaskSize = options[b"mini_mask_size"].decode("utf-8")
        validationSteps = int(options[b"validation_steps"])
        imMaxDim = int(options[b"images_max_dim"])
        imMinDim = int(options[b"images_min_dim"])
        backbone = options[b"backbone"].decode("utf-8")

        newFlags = dict()
        for flag, value in flags.items():
            newFlags.update({flag.decode("utf-8"): value})
        flags = newFlags

    if not flags["b"]:
        trainBatchNorm = False
    else:
        # None means train in normal mode but do not force it when inferencing
        trainBatchNorm = None

    if not flags["n"]:
        # Resize and pad with zeros to get a square image of
        # size [max_dim, max_dim].
        resizeMode = "square"
    else:
        resizeMode = "none"

    # Configurations
    config = ModelConfig(
        name=name,
        imagesPerGPU=imagesPerGPU,
        GPUcount=GPUcount,
        numClasses=len(classes) + 1,
        trainROIsPerImage=ROIsPerImage,
        stepsPerEpoch=stepsPerEpoch,
        miniMaskShape=miniMaskSize,
        validationSteps=validationSteps,
        imageMaxDim=imMaxDim,
        imageMinDim=imMinDim,
        backbone=backbone,
        trainBatchNorm=trainBatchNorm,
        resizeMode=resizeMode,
    )
    config.display()

    # Create model
    model = modellib.MaskRCNN(mode="training", config=config, model_dir=logs)

    # Load weights
    if initialWeights:
        gscript.message("Loading weights {}".format(initialWeights))
    if initialWeights and flags["e"]:
        model.load_weights(
            initialWeights,
            by_name=True,
            exclude=["mrcnn_class_logits", "mrcnn_bbox_fc", "mrcnn_bbox", "mrcnn_mask"],
        )
    elif initialWeights:
        model.load_weights(initialWeights, by_name=True)

    gscript.message("Reading images from dataset {}".format(dataset))
    images = list()
    for root, subdirs, _ in os.walk(dataset):
        if not subdirs:
            # TODO: More structures
            images.append(root)

    shuffle(images)

    if flags["s"]:
        # Write list of unused images to logs
        testImagesThreshold = int(len(images) * 0.9)
        gscript.message(
            "List of unused images saved in the logs directory" 'as "unused.txt"'
        )
        with open(os.path.join(logs, "unused.txt"), "w") as unused:
            for filename in images[testImagesThreshold:]:
                unused.write("{}\n".format(filename))
    else:
        testImagesThreshold = len(images)

    evalImagesThreshold = int(testImagesThreshold * 0.75)

    # augmentation = imgaug/augmenters.Fliplr(0.5)

    # Training dataset
    trainImages = images[:evalImagesThreshold]
    dataset_train = utils.Dataset()
    dataset_train.import_contents(classes, trainImages, name)
    dataset_train.prepare()

    # Validation dataset
    evalImages = images[evalImagesThreshold:testImagesThreshold]
    dataset_val = utils.Dataset()
    dataset_val.import_contents(classes, evalImages, name)
    dataset_val.prepare()

    if initialWeights:
        # Training - Stage 1
        # Adjust epochs and layers as needed
        gscript.message("Training network heads")
        model.train(
            dataset_train,
            dataset_val,
            learning_rate=config.LEARNING_RATE,
            epochs=int(epochs / 7),
            layers="heads",
        )  # augmentation=augmentation

        # Training - Stage 2
        # Finetune layers from ResNet stage 4 and up
        gscript.message("Fine tune Resnet stage 4 and up")
        # divide the learning rate by 10 if ran out of memory or
        # if weights exploded
        model.train(
            dataset_train,
            dataset_val,
            learning_rate=config.LEARNING_RATE,
            epochs=int(epochs / 7) * 3,
            layers="4+",
        )  # augmentation=augmentation

        # Training - Stage 3
        # Fine tune all layers
        gscript.message("Fine tune all layers")
        # out of if statement
    else:
        gscript.message("Training all layers")
        # out of if statement

    # divide the learning rate by 100 if ran out of memory or
    # if weights exploded
    model.train(
        dataset_train,
        dataset_val,
        learning_rate=config.LEARNING_RATE / 10,
        epochs=epochs,
        layers="all",
    )  # augmentation=augmentation


if __name__ == "__main__":
    options, flags = gscript.parser()
    main(options, flags)
