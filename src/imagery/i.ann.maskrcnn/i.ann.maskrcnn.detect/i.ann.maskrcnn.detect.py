#!/usr/bin/env python3
#
############################################################################
#
# MODULE:	    i.ann.maskrcnn.detect
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
# % description: Detect features in images using a Mask R-CNN model
# % keyword: ann
# % keyword: vector
# % keyword: raster
# %end
# %flag
# %  key: e
# %  description: External georeferencing in the images folder (when using images_directory)
# %end
# %option
# % key: band1
# % type: string
# % label: Name of raster maps to use for detection as the first band (divided by ",")
# %end
# %option
# % key: band2
# % type: string
# % label: Name of raster maps to use for detection as the second band (divided by ",")
# %end
# %option
# % key: band3
# % type: string
# % label: Name of raster maps to use for detection as the third band (divided by ",")
# %end
# %option G_OPT_M_DIR
# % key: images_directory
# % label: Path to a directory with external images to detect
# % required: no
# %end
# %option
# % key: images_format
# % type: string
# % label: Format suffix of images
# % description: .jpg, .tiff, .png, etc.
# %end
# %option
# % key: model
# % type: string
# % label: Path to the .h5 file containing the model
# % required: yes
# % multiple: no
# %end
# %option
# % key: classes
# % type: string
# % label: Names of classes separated with ","
# % required: yes
# % multiple: yes
# %end
# %option
# % key: output_type
# % type: string
# % label: Type of output
# % options: area, point
# % answer: area
# % required: no
# %end
# %rules
# % requires_all: images_directory, images_format
# % requires_all: band1, band2, band3
# % required: images_directory, band1
# %end


import os
from shutil import copyfile
import sys
from io import BytesIO

import numpy as np

import grass.script as gscript
from grass.script.utils import get_lib_path
import grass.script.array as garray

path = get_lib_path(modname="maskrcnn", libname="model")
if path is None:
    gscript.fatal("Not able to find the maskrcnn library directory.")
sys.path.append(path)


def main(options, flags):

    # Lazy import GDAL python bindings
    try:
        from osgeo import gdal, osr
    except ImportError as e:
        gscript.fatal(_("Module requires GDAL python bindings: {}").format(e))

    import model as modellib
    from config import ModelConfig

    try:
        imagesDir = options["images_directory"]
        modelPath = options["model"]
        classes = options["classes"].split(",")
        if options["band1"]:
            band1 = options["band1"].split(",")
            band2 = options["band2"].split(",")
            band3 = options["band3"].split(",")
        else:
            band1 = list()
            band2 = list()
            band3 = list()
        outputType = options["output_type"]
        if options["images_format"]:
            extension = options["images_format"]
            if options["images_format"][0] != ".":
                extension = ".{}".format(extension)
        else:
            extension = ""

        # a directory where masks and georeferencing will be saved in case of
        # external images
        masksDir = gscript.core.tempfile().rsplit(os.sep, 1)[0]
    except KeyError:
        # GRASS parses keys and values as bytes instead of strings
        imagesDir = options[b"images_directory"].decode("utf-8")
        modelPath = options[b"model"].decode("utf-8")
        classes = options[b"classes"].decode("utf-8").split(",")
        if options[b"band1"].decode("utf-8"):
            band1 = options[b"band1"].decode("utf-8").split(",")
            band2 = options[b"band2"].decode("utf-8").split(",")
            band3 = options[b"band3"].decode("utf-8").split(",")
        else:
            band1 = list()
            band2 = list()
            band3 = list()
        outputType = options[b"output_type"].decode("utf-8")
        if options[b"images_format"].decode("utf-8"):
            extension = options[b"images_format"].decode("utf-8")
            if extension[0] != ".":
                extension = ".{}".format(extension)
        else:
            extension = ""

        newFlags = dict()
        for flag, value in flags.items():
            newFlags.update({flag.decode("utf-8"): value})
        flags = newFlags

        # a directory where masks and georeferencing will be saved in case of
        # external images
        masksDir = gscript.core.tempfile().decode("utf-8").rsplit(os.sep, 1)[0]

    if len(band1) != len(band2) or len(band2) != len(band3):
        gscript.fatal("Length of band1, band2 and band3 must be equal.")

    # TODO: (3 different brands in case of lot of classes?)
    if len(classes) > 255:
        gscript.fatal("Too many classes. Must be less than 256.")

    if len(set(classes)) != len(classes):
        gscript.fatal("Two or more classes have the same name.")

    # used colour corresponds to class_id
    classesColours = range(len(classes) + 1)

    # Create model object in inference mode.
    config = ModelConfig(numClasses=len(classes) + 1)
    model = modellib.MaskRCNN(mode="inference", model_dir=modelPath, config=config)

    model.load_weights(modelPath, by_name=True)

    masks = list()
    detectedClasses = list()

    # TODO: Use the whole list instead of iteration
    if len(band1) > 0:
        gscript.message("Detecting features in raster maps...")
        # using maps imported in GRASS
        mapsCount = len(band1)
        for i in range(mapsCount):
            gscript.percent(i + 1, mapsCount, 1)
            maskTitle = "{}_{}".format(band1[i].split(".")[0], i)
            # load map into 3-band np.array
            gscript.run_command("g.region", raster=band1[i], quiet=True)
            bands = np.stack(
                (
                    garray.array(band1[i]),
                    garray.array(band2[i]),
                    garray.array(band3[i]),
                ),
                2,
            )

            # Run detection
            results = model.detect([bands], verbosity=gscript.verbosity())

            # Save results
            for r in results:
                parse_instances(
                    bands,
                    r["rois"],
                    r["masks"],
                    r["class_ids"],
                    # ['BG'] + [i for i in classes],
                    # r['scores'],
                    outputDir=masksDir,
                    which=outputType,
                    title=maskTitle,
                    colours=classesColours,
                    mList=masks,
                    cList=detectedClasses,
                    grassMap=True,
                )

    if imagesDir:
        gscript.message("Detecting features in images from the directory...")
        for imageFile in [
            file
            for file in next(os.walk(imagesDir))[2]
            if os.path.splitext(file)[1] == extension
        ]:
            image = skimage.io.imread(os.path.join(imagesDir, imageFile))
            if image.shape[2] > 3:
                image = image[:, :, 0:3]
            source = gdal.Open(os.path.join(imagesDir, imageFile))

            sourceProj = source.GetProjection()
            sourceTrans = source.GetGeoTransform()

            # Run detection
            results = model.detect([image], verbosity=gscript.verbosity())

            # Save results
            for r in results:
                parse_instances(
                    image,
                    r["rois"],
                    r["masks"],
                    r["class_ids"],
                    # ['BG'] + [i for i in classes],
                    # r['scores'],
                    outputDir=masksDir,
                    which=outputType,
                    title=imageFile,
                    colours=classesColours,
                    proj=sourceProj,
                    trans=sourceTrans,
                    mList=masks,
                    cList=detectedClasses,
                    externalReferencing=flags["e"],
                )

    if flags["e"]:
        gscript.message("Masks detected. Georeferencing masks...")
        external_georeferencing(
            imagesDir, classes, masksDir, masks, detectedClasses, extension
        )

    gscript.message("Converting masks to vectors...")
    masksString = ",".join(masks)
    for parsedClass in detectedClasses:
        gscript.message("Processing {} map...".format(classes[parsedClass - 1]))
        i = 0
        for maskName in masks:
            gscript.percent(i, len(masks), 1)
            gscript.run_command("g.region", raster=maskName, quiet=True)
            gscript.run_command(
                "r.mask",
                raster=maskName,
                maskcats=classesColours[parsedClass],
                quiet=True,
            )
            gscript.run_command(
                "r.to.vect",
                "s",
                input=maskName,
                output=maskName,
                type=outputType,
                quiet=True,
            )
            gscript.run_command("r.mask", "r", quiet=True)
            i += 1

        gscript.run_command(
            "v.patch", input=masksString, output=classes[parsedClass - 1]
        )
        gscript.run_command(
            "g.remove", "f", name=masksString, type="vector", quiet=True
        )
    gscript.run_command("g.remove", "f", name=masksString, type="raster", quiet=True)


def external_georeferencing(imagesDir, classes, masksDir, mList, cList, extension):
    """
    Find the external georeferencing and copy it to the directory with
    the image.

    :param imagesDir: a directory of original images
    :param classes: a list of classes names
    :param masksDir: intermediate directory where masks are saved
    :param mList: list of names of imported rasters
    :param cList: list of classes with at least one instance
    :param extension: extension if images
    """
    for referencing in [
        file
        for file in next(os.walk(imagesDir))[2]
        if (os.path.splitext(file)[1] != extension and extension in file)
    ]:
        fileName, refExtension = referencing.split(extension)
        # TODO: Join with converting to one loop
        for i in range(1, len(classes) + 1):
            maskName = fileName + "_" + str(i)
            maskFileName = maskName + ".png"
            if os.path.isfile(os.path.join(masksDir, maskFileName)):
                if i not in cList:
                    cList.append(i)
                mList.append(maskName)
                copy_georeferencing(
                    imagesDir, masksDir, maskFileName, refExtension, referencing
                )

                gscript.run_command(
                    "r.in.gdal",
                    input=os.path.join(masksDir, maskFileName),
                    output=maskName,
                    band=1,  # TODO: 3 if 3 band masks
                    overwrite=gscript.overwrite(),
                    quiet=True,
                )


def copy_georeferencing(imagesDir, masksDir, maskFileName, refExtension, referencing):
    """
    Copy georeferencing file.

    :param imagesDir: a directory of original images
    :param masksDir: intermediate directory where masks are saved
    :param maskFileName: title given to mask during parse_instances
    :param refExtension: extension of referencing file
    :param referencing: path to the file containing georeferencing
    """

    r2 = os.path.join(masksDir, maskFileName + refExtension)
    copyfile(os.path.join(imagesDir, referencing), r2)


def apply_mask(image, mask, colour):
    """
    Apply the given mask to the image.

    :param image: [band1, band2, band3]
    :param mask: [height, width]
    :param colour: integer giving corresponding to the class ID

    :return image: A three band mask
    """
    for c in range(3):
        image[:, :, c] = np.where(
            mask == 1,
            np.zeros([image.shape[0], image.shape[1]]) + colour[c],
            image[:, :, c],
        )

    return image


def parse_instances(
    image,
    boxes,
    masks,
    class_ids,
    # class_names,
    # scores=None,
    title="",
    # figsize=(16, 16),
    # ax=None,
    outputDir="",
    which="area",
    colours=None,
    proj=None,
    trans=None,
    mList=None,
    cList=None,
    grassMap=False,
    externalReferencing=None,
):
    """
    Create a raster from results of detection and import it into GRASS GIS or
    save to a temporal directory to wait for external georeferencing.

    :param image: [band1, band2, band3]
    :param boxes: [num_instance, (y1, x1, y2, x2, class_id)] in image
        coordinates
    :param masks: [height, width, num_instances]
    :param class_ids: [num_instances]
    :param class_names: list of class names of the dataset
    :param scores: (optional) confidence scores for each box
    :param title: title used for importing as a raster map
    :param figsize: (optional) the size of the image.
    :param outputDir: intermediate directory where masks will be saved
    :param which: either 'area' or 'point', a representation of detections
    :param colours: list of colours i order of class_ids
    :param proj: projection of image
    :param trans: geotransform of image
    :param mList: list of names of imported rasters
    :param cList: list of classes with at least one instance
    :param grassMap: boolean. True=using maps in GRASS, False=using external
        images
    :param externalReferencing: boolean. True=images are georeferenced by
        an external file

    May be extended in the future (commented parameters)
    """
    import matplotlib  # required by windows

    matplotlib.use("wxAGG")  # required by windows
    import matplotlib.pyplot as plt

    dpi = 80
    height, width = image.shape[:2]
    figsize = width / float(dpi), height / float(dpi)

    N = boxes.shape[0]
    if not N:
        gscript.message("\n*** No instances to detect in image {}*** \n".format(title))
    else:
        assert boxes.shape[0] == masks.shape[-1] == class_ids.shape[0]

    # Show area outside image boundaries.
    height, width = image.shape[:2]

    if which == "area":
        from matplotlib.patches import Polygon

        for classId in set(class_ids):
            fig = plt.figure(figsize=figsize)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis("off")
            masked_image = np.zeros(image.shape)
            index = 0

            for i in range(N):
                if class_ids[i] != classId:
                    continue
                colour = (colours[class_ids[i]],) * 3

                # Bounding box
                if not np.any(boxes[i]):
                    # Skip this instance. Has no bbox.
                    # Likely lost in image cropping.
                    continue

                # Mask
                mask = masks[:, :, i]
                masked_image = apply_mask(masked_image, mask, colour)

                # Mask Polygon
                # Pad to ensure proper polygons for masks that touch image
                # edges.
                padded_mask = np.zeros(
                    (mask.shape[0] + 2, mask.shape[1] + 2), dtype=np.uint8
                )
                padded_mask[1:-1, 1:-1] = mask
                contours = find_contours(padded_mask, 0.5)
                for verts in contours:
                    # Subtract the padding and flip (y, x) to (x, y)
                    verts = np.fliplr(verts) - 1
                    p = Polygon(verts, facecolor="none", edgecolor="none")
                    ax.add_patch(p)

                index = i
                # TODO: write probabilities
                # score = scores[i] if scores is not None else None

            masked_image = masked_image.astype(np.uint8)
            ax.imshow(masked_image, interpolation="nearest")
            ax.set(xlim=[0, width], ylim=[height, 0], aspect=1)

            maskName = "{}_{}".format(os.path.splitext(title)[0], str(class_ids[index]))

            if not externalReferencing and not grassMap:
                targetPath = os.path.join(
                    outputDir, "{}{}".format(maskName, os.path.splitext(title)[1])
                )

                plt.savefig(targetPath, dpi=dpi)
                plt.close()

                target = gdal.Open(targetPath, gdal.GA_Update)
                target.SetGeoTransform(trans)
                target.SetProjection(proj)
                target.FlushCache()
                mList.append(maskName)
                if class_ids[index] not in cList:
                    cList.append(class_ids[index])

                gscript.run_command(
                    "r.in.gdal",
                    input=targetPath,
                    output=maskName,
                    band=1,  # TODO: 3 if 3 band masks
                    overwrite=gscript.overwrite(),
                    quiet=True,
                )

            elif grassMap:
                # using maps imported in GRASS
                plt.close()
                mList.append(maskName)
                if class_ids[index] not in cList:
                    cList.append(class_ids[index])

                mask2d = garray.array(dtype=np.uint8)
                np.copyto(mask2d, masked_image[:, :, 0])
                mask2d.write(mapname=maskName)
            else:
                plt.savefig(os.path.join(outputDir, maskName), dpi=dpi)
                # plt.show()
                plt.close()

    elif which == "point":
        for classId in set(class_ids):
            fig = plt.figure(figsize=figsize)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis("off")
            masked_image = np.zeros(image.shape)
            index = 0
            for i in range(N):
                if class_ids[i] != classId:
                    continue

                fig = plt.figure(figsize=figsize)
                ax = fig.add_axes([0, 0, 1, 1])
                ax.axis("off")

                # Bounding box
                if not np.any(boxes[i]):
                    # Skip this instance. Has no bbox.
                    # Likely lost in image cropping.
                    continue
                y1, x1, y2, x2 = boxes[i]
                masked_image[int((y1 + y2) / 2)][int((x1 + x2) / 2)] = colours[
                    class_ids[i]
                ]

                index = i

                # TODO: write probabilities
                # Label
                # class_id = class_ids[i]
                # score = scores[i] if scores is not None else None
                # label = class_names[class_id]

            ax.imshow(masked_image.astype(np.uint8), interpolation="nearest")
            ax.set(xlim=[0, width], ylim=[height, 0], aspect=1)

            maskName = "{}_{}".format(os.path.splitext(title)[0], str(class_ids[index]))

            if not externalReferencing and not grassMap:
                targetPath = os.path.join(
                    outputDir, "{}{}".format(maskName, os.path.splitext(title)[1])
                )

                plt.savefig(targetPath, dpi=dpi)
                plt.close()

                target = gdal.Open(targetPath, gdal.GA_Update)
                target.SetGeoTransform(trans)
                target.SetProjection(proj)
                target.FlushCache()
                mList.append(maskName)
                if class_ids[index] not in cList:
                    cList.append(class_ids[index])

                gscript.run_command(
                    "r.in.gdal",
                    input=targetPath,
                    output=maskName,
                    band=1,  # TODO: 3 if 3 band masks
                    overwrite=gscript.overwrite(),
                    quiet=True,
                )
            elif grassMap:
                # using maps imported in GRASS
                plt.close()
                mList.append(maskName)
                if class_ids[index] not in cList:
                    cList.append(class_ids[index])

                mask2d = garray.array(dtype=np.uint8)
                np.copyto(mask2d, masked_image[:, :, 0])
                mask2d.write(mapname=maskName)
            else:
                plt.savefig(os.path.join(outputDir, maskName), dpi=dpi)
                # plt.show()
                plt.close()


if __name__ == "__main__":
    options, flags = gscript.parser()

    # import only after the parser finished and the code actually runs

    # Lazy imports

    try:
        from skimage.measure import find_contours
        import skimage.io
    except ImportError:
        grass.fatal(
            "Cannot import skimage." " Please install the Python scikit-image package."
        )
    try:
        from PIL import Image
    except ImportError:
        grass.fatal("Cannot import PIL." " Please install the Python pillow package.")

    main(options, flags)
