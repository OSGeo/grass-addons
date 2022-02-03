#!/usr/bin/env python3

############################################################################
# MODULE:        r.learn.predict
# AUTHOR:        Steven Pawley
# PURPOSE:       Supervised classification and regression of GRASS rasters
#                using the python scikit-learn package
#
# COPYRIGHT: (c) 2017-2020 Steven Pawley, and the GRASS Development Team
#                This program is free software under the GNU General Public
#                for details.
#
#############################################################################

# %module
# % description: Apply a fitted scikit-learn estimator to rasters in a GRASS GIS imagery group.
# % keyword: raster
# % keyword: classification
# % keyword: regression
# % keyword: machine learning
# % keyword: scikit-learn
# % keyword: prediction
# %end

# %option G_OPT_I_GROUP
# % key: group
# % label: Group of raster layers used for prediction
# % description: GRASS imagery group of raster maps representing feature variables to be used in the machine learning model
# % required: yes
# % multiple: no
# %end

# %option G_OPT_F_INPUT
# % key: load_model
# % label: Load model from file
# % description: File representing pickled scikit-learn estimator model
# % required: yes
# % guisection: Required
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Output Map
# % description: Raster layer name to store result from classification or regression model. The name will also used as a perfix if class probabilities or intermediate of cross-validation results are ordered as maps.
# % guisection: Required
# % required: yes
# %end

# %flag
# % key: p
# % label: Output class membership probabilities
# % description: A raster layer is created for each class. For the case of a binary classification, only the positive (maximum) class is output
# % guisection: Optional
# %end

# %flag
# % key: z
# % label: Only predict class probabilities
# % guisection: Optional
# %end

# %option
# % key: chunksize
# % type: integer
# % label: Number of pixels to pass to the prediction method
# % description: Number of pixels to pass to the prediction method. GRASS GIS reads raster by-row so chunksize is rounded down based on the number of columns
# % answer: 100000
# % guisection: Optional
# %end


import grass.script as gs
import numpy as np
import math
from grass.pygrass.gis.region import Region
from grass.pygrass.modules.shortcuts import raster as r

gs.utils.set_path(modulename="r.learn.ml2", dirname="rlearnlib", path="..")

from rlearnlib.raster import RasterStack


def string_to_rules(string):
    """Converts a string to a file for input as a GRASS Rules File"""
    tmp = gs.tempfile()
    f = open("%s" % (tmp), "wt")
    f.write(string)
    f.close()
    return tmp


def main():
    try:
        import sklearn
        import joblib

        if sklearn.__version__ < "0.20":
            gs.fatal("Package python3-scikit-learn 0.20 or newer is not installed")

    except ImportError:
        gs.fatal("Package python3-scikit-learn 0.20 or newer is not installed")

    # parser options
    group = options["group"]
    output = options["output"]
    model_load = options["load_model"]
    probability = flags["p"]
    prob_only = flags["z"]
    chunksize = int(options["chunksize"])

    # remove @ from output in case overwriting result
    if "@" in output:
        output = output.split("@")[0]

    # check probabilities=True if prob_only=True
    if prob_only is True and probability is False:
        gs.fatal("Need to set probabilities=True if prob_only=True")

    # reload fitted model and training data
    estimator, y, class_labels = joblib.load(model_load)

    # define RasterStack
    stack = RasterStack(group=group)

    # perform raster prediction
    region = Region()
    row_incr = math.ceil(chunksize / region.cols)

    # do not read by increments if increment > n_rows
    if row_incr >= region.rows:
        row_incr = None

    # prediction
    if prob_only is False:
        gs.message("Predicting classification/regression raster...")
        stack.predict(
            estimator=estimator,
            output=output,
            height=row_incr,
            overwrite=gs.overwrite(),
        )

    if probability is True:
        gs.message("Predicting class probabilities...")
        stack.predict_proba(
            estimator=estimator,
            output=output,
            class_labels=np.unique(y),
            overwrite=gs.overwrite(),
            height=row_incr,
        )

    # assign categories for classification map
    if class_labels and prob_only is False:
        rules = []

        for val, lab in class_labels.items():
            rules.append(",".join([str(val), str(lab)]))

        rules = "\n".join(rules)
        rules_file = string_to_rules(rules)
        r.category(map=output, rules=rules_file, separator="comma")


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
