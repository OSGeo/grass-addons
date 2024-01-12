#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.maxent.train
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Maxent modeling using the Maxent software
#               (https://biodiversityinformatics.amnh.org/open_source/maxent/),
#               exposing most options/parameters.
#
# COPYRIGHT:   (C) 2024 Paulo van Breugel and the GRASS Development Team
#              http://ecodiv.earth
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

# %module
# % description: Create/train a Maxent model
# % keyword: modeling
# % keyword: Maxent
# %end

# %option G_OPT_F_BIN_INPUT
# % key: samplesfile
# % label: Sample file presence locations
# % description: Please enter the name of a file containing presence locations for one or more species.
# % guisection: Basic
# % required: yes
# %end

# %option G_OPT_F_BIN_INPUT
# % key: environmentallayersfile
# % label: Sample file with background locations
# % description:  Please enter the file name of the SWD file with environmental variables (can be created with v.maxent.swd or r.out.maxent_swd).
# % guisection: Basic
# % required: yes
# %end

# %option
# % key: togglelayertype
# % type: string
# % label: Prefix that identifies categorical data
# % description: Toggle continuous/categorical for environmental variables whose names begin with this prefix (default: all continuous)
# % guisection: Basic
# %end

# %option G_OPT_M_DIR
# % key: projectionlayers
# % label: Location of an alternate set of environmental variables.
# % description: Location of an alternate set of environmental variables. Maxent models will be projected onto these variables.
# % guisection: Basic
# % required: no
# %end

# %option G_OPT_M_DIR
# % key: outputdirectory
# % label: Directory where outputs will be written.
# % description: Directory where outputs will be written. This should be different from the environmental layers directory.
# % guisection: Basic
# % required: yes
# %end

# %option
# % key: suffix
# % type: string
# % label: Suffix for name(s) of prediction layer(s)
# % description: Add a suffix to the name(s) of imported prediction layer(s)
# % guisection: Basic
# %end

# %option
# % key: nodata
# % type: integer
# % description: Value to be interpreted as nodata values in SWD sample data
# % answer : -9999
# % required: no
# % guisection: Basic
# %end

# %option
# % key: importsamplepredictions
# % type: string
# % label: Create a vector point layer from the sample predictions
# % description: Import the the file(s) with sample predictions as point feature layer.
# % options: yes,no
# % answer: no
# % guisection: Output
# %end

# %option
# % key: writebackgroundpredictions
# % type: string
# % label: Create a vector point layer with predictions at background points
# % description: Create a vector point layer with predictions at background points
# % options: yes,no
# % answer: no
# % guisection: Output
# %end

# %option
# % key: responsecurves
# % type: string
# % label: Create response curves.
# % description: Create graphs showing how predicted relative probability of occurrence depends on the value of each environmental variable.
# % options: yes,no
# % answer: no
# % guisection: Output
# %end

# %option
# % key: writeplotdata
# % type: string
# % label: Write response curve data to file
# % description: Write output files containing the data used to make response curves, for import into external plotting software.
# % options: yes,no
# % answer: no
# % guisection: Output
# %end

# %option
# % key: outputformat
# % type: string
# % label: Representation probability
# % description: Representation of probabilities used in writing output grids. See Help for details.
# % options: cloglog,logistic,cumulative,raw
# % answer: cloglog
# % guisection: Parameters
# %end

# %option
# % key: extrapolate
# % type: string
# % label: Allow model to extrapolate
# % description: Predict to regions of environmental space outside the limits encountered during training.
# % options: yes,no
# % answer: yes
# % guisection: Parameters
# %end

# %option
# % key: removeduplicates
# % type: string
# % label: Remove duplicate presence records.
# % description: Remove duplicate presence records. If environmental data are in grids, duplicates are records in the same grid cell. Otherwise, duplicates are records with identical coordinates.
# % options: yes,no
# % answer: yes
# % guisection: Parameters
# %end

# %option
# % key: doclamp
# % type: string
# % label: Apply clamping
# % description: Apply clamping when projecting.
# % options: yes,no
# % answer: yes
# % guisection: Parameters
# %end

# %option
# % key: fadebyclamping
# % type: string
# % label: Fade effect clamping
# % description: Reduce prediction at each point in projections by the difference between clamped and non-clamped output at that point.
# % options: yes,no
# % answer: no
# % guisection: Parameters
# %end

# %option
# % key: linear
# % type: string
# % label: Allow linear features to be used
# % answer: yes
# % options: yes,no
# % guisection: Parameters
# %end

# %option
# % key: quadratic
# % type: string
# % label: Allow quadratic features to be used
# % answer: yes
# % options: yes,no
# % guisection: Parameters
# %end

# %option
# % key: product
# % type: string
# % label: Allow product features to be used
# % answer: yes
# % options: yes,no
# % guisection: Parameters
# %end

# %option
# % key: threshold
# % type: string
# % label: Allow product features to be used
# % answer: no
# % options: yes,no
# % guisection: Parameters
# %end

# %option
# % key: hinge
# % type: string
# % label: Allow hinge features to be used
# % answer: yes
# % options: yes,no
# % guisection: Parameters
# %end

# %option
# % key: autofeature
# % type: string
# % label: Automatically select feature classes
# % description: Automatically select which feature classes to use, based on number of training samples.
# % answer: yes
# % options: yes,no
# % guisection: Parameters
# %end

# %option
# % key: jackknife
# % type: string
# % label: jacknife validation
# % description: Measure importance of each environmental variable by training with each environmental variable first omitted, then used in isolation.
# % options: yes,no
# % answer: no
# % guisection: Validation
# %end

# %option
# % key: randomtestpoints
# % type: integer
# % label: Percentage of random test points
# % description: Percentage of presence localities to be randomly set aside as test points, used to compute AUC, omission etc.
# % answer: 0
# % guisection: Validation
# %end

# %option G_OPT_V_INPUT
# % key: testsamplesfile
# % type: string
# % label: Test presence locations
# % description: Use the presence localities in this csv file to compute statistics (AUC, omission etc.).
# % guisection: Validation
# % required: no
# %end

# %option
# % key: replicatetype
# % type: string
# % label: Number of replicates in cross-validation
# % description: If replicates > 1, do multiple runs using crossvalidate,bootstrap or subsample. See the Maxent help file for the difference.
# % guisection: Validation
# % options: crossvalidate,bootstrap,subsample
# % answer: crossvalidate
# %end

# %option
# % key: replicates
# % type: integer
# % label: Number of replicates in cross-validation
# % description: If replicates > 1, do multiple runs of this type: Crossvalidate: samples divided into replicates folds; each fold in turn used for test data. Bootstrap: replicate sample sets chosen by sampling with replacement. Subsample: replicate sample sets chosen by removing random test percentage without replacement to be used for evaluation.
# % guisection: Validation
# % answer: 1
# % options:1-20
# %end

# %option
# % key: betamultiplier
# % type: double
# % label: Multiply all automatic regularization parameters by this number.
# % description: Multiply all automatic regularization parameters by this number. A higher number gives a more spread-out distribution.
# % answer: 1.0
# % guisection: Advanced
# %end

# %option
# % key: addsamplestobackground
# % type: string
# % label: Add sample points to background if conditions differ
# % description: Add to the background any sample for which has a combination of environmental values that isn't already present in the background
# % answer: yes
# % options: yes,no
# % guisection: Advanced
# %end

# %option
# % key: addallsamplestobackground
# % type: string
# % label: Add all samples to the background
# % description: Add all samples to the background, even if they have combinations of environmental values that are already present in the background
# % answer: no
# % options: yes,no
# % guisection: Advanced
# %end

# %option
# % key: maximumiterations
# % type: integer
# % label: Maximum iterations optimization
# % description: Stop training after this many iterations of the optimization algorithm.
# % answer: 500
# % guisection: Advanced
# %end

# %option
# % key: convergencethreshold
# % type: double
# % label: Convergence threshold
# % description: Stop training when the drop in log loss per iteration drops below this number.
# % answer: 0.00005
# % guisection: Advanced
# %end

# %option
# % key: convergencethreshold
# % type: double
# % label: Convergence threshold
# % description: Stop training when the drop in log loss per iteration drops below this number.
# % answer: 0.00005
# % guisection: Advanced
# %end

# %option
# % key: lq2lqptthreshold
# % type: integer
# % label: Theshold for product and threshold features
# % description: Number of samples at which product and threshold features start being used.
# % answer: 80
# % guisection: Advanced
# %end

# %option
# % key: l2lqthreshold
# % type: integer
# % label: Theshold for quadratic feature
# % description: Number of samples at which quadratic features start being used.
# % answer: 10
# % guisection: Advanced
# %end

# %option
# % key: hingethreshold
# % type: integer
# % label: Theshold for hinge feature
# % description: Number of samples at which hinge features start being used.
# % answer: 15
# % guisection: Advanced
# %end

# %option
# % key: beta_threshold
# % type: double
# % label: Regularization parameter for treshold features
# % description: Regularization parameter to be applied to all threshold features; negative value enables automatic setting.
# % answer: -1.0
# % guisection: Advanced
# %end

# %option
# % key: beta_categorical
# % type: double
# % label: Regularization parameter for categorical features
# % description: Regularization parameter to be applied to all categorical features; negative value enables automatic setting.
# % answer: -1.0
# % guisection: Advanced
# %end

# %option
# % key: beta_lqp
# % type: double
# % label: Regularization parameter for lin, quad en prod features
# % description: Regularization parameter to be applied to all linear, quadratic and product features; negative value enables automatic setting.
# % answer: -1.0
# % guisection: Advanced
# %end

# %option
# % key: beta_hinge
# % type: double
# % label: Regularization parameter for hinge features
# % description: Regularization parameter to be applied to all linear, quadratic and product features; negative value enables automatic setting.
# % answer: -1.0
# % guisection: Advanced
# %end

# %option
# % key: defaultprevalence
# % type: double
# % label: Default prevalence of the species
# % description: Default prevalence of the species: probability of presence at ordinary occurrence points. See Elith et al., Diversity and Distributions, 2011 for details.
# % answer: 0.5
# % options: 0-1
# % guisection: Advanced
# %end

# %option
# % key: randomseed
# % type: string
# % label: Use a random seed
# % description: If selected, a different random seed will be used for each run, so a different random test/train partition will be made and a different random subset of the background will be used, if applicable.
# % answer: no
# % options: no,yes
# % guisection: Advanced
# %end

# %option G_OPT_F_BIN_INPUT
# % key: maxent
# % label: Location Maxent jar file
# % description: Give the path to the Maxent executable file (maxent.jar)
# % required: no
# %end

# %option G_OPT_M_NPROCS
# % key: threads
# % label: Number of processor threads to use.
# %end

# %option G_OPT_MEMORYMB
# % Description: Maximum memory to be used by Maxent (in MB)
# %end

# %flag
# % key: v
# % label: Make the Maxent user interface visible
# % description: Show the Maxent interface and do not start automatically. Use for debugging.
# %end

# %flag
# % key: w
# % label: Do not autorun Maxent
# % description: When you select this option, Maxent will not start before you hit the start option. Requires the -v flag to be set as well
# %end

# %flag
# % key: s
# % label: randomseed
# % description: If selected, a different random seed will be used for each run, so a different random test/train partition will be made and a different random subset of the background will be used, if applicable.
# %end

# %flag
# % key: i
# % label: Copy maxent.jar to addon directory
# % description: copy the maxent.jar (path provided with the 'maxent' parameter) to the addon scripts directory.
# %end

# %flag
# % key: u
# % label: Overwrites maxent.jar in addon directory
# % description: copy the maxent.jar (path provided with the 'maxent' parameter) to the addon scripts directory. If the file already exist in the addon directory, it is overwritten.
# %end

# %flag
# % key:
# % label: Overwrite
# % description: Overwrite files and grass gis layers
# %end

# %rules
# % exclusive: replicates,randomtestpoints
# %end

# %rules
# % requires: -w, -v
# %end

# %rules
# % exclusive: -i, -u
# %end


# %rules
# % requires_all: fadebyclamping, doclamp
# %end

# import libraries
import csv
import os
import sys
import subprocess
import shutil
import grass.script as gs
import numpy as np


def find_index_case_insensitive(lst, target):
    """
    Find index for string match, matching case insensitive
    """
    for i, item in enumerate(lst):
        if item.lower() == target.lower():
            return i
    return -1  # Return -1 if the element is not found


def Check_if_layer_exist(layer):
    """
    Checks if layer exist in current mapset
    """
    mapset = gs.gisenv()["MAPSET"]
    filename = gs.find_file(layer, element="vector", mapset=mapset)["name"]
    return len(filename) > 0


def main(options, flags):
    # Set verbosity level
    if gs.verbosity() > 2:
        function_verbosity = False
    else:
        function_verbosity = True

    # Checking availability of maxent.jar
    # ------------------------------------------------------------------
    if bool(options["maxent"]):
        maxent_file = options["maxent"]
        if not os.path.isfile(maxent_file):
            gs.fatal(
                _("The maxent.jar file was not found on the location you provided")
            )
        file_name = os.path.basename(os.path.basename(maxent_file))
        maxent_path = os.environ.get("GRASS_ADDON_BASE")
        maxent_copy = os.path.join(maxent_path, "scripts", "maxent.jar")
        if file_name != "maxent.jar":
            gs.fatal(
                _(
                    "The name of the maxent program should be 'maxent.jar',"
                    " not '{}'".format(file_name)
                )
            )
        if bool(flags["i"]):
            if os.path.isfile(maxent_copy):
                gs.fatal(
                    _(
                        "There is already a maxent.jar file in the scripts \n"
                        "directory. Remove the -i flag. If you want to update \n"
                        " the maxent.jar file, use the -u flag instead."
                    )
                )
            else:
                shutil.copyfile(maxent_file, maxent_copy)
                gs.message(
                    _(
                        "Copied the maxent.jar file to the grass gis addon script directory .\n\n"
                    ),
                    flags="i",
                )
        if bool(flags["u"]):
            shutil.copyfile(maxent_file, maxent_copy)
            gs.message(
                _(
                    "Copied the maxent.jar file to the grass gis addon script directory .\n\n"
                ),
                flags="i",
            )

    else:
        maxent_file = os.environ.get("GRASS_ADDON_BASE")
        maxent_file = os.path.join(maxent_file, "scripts", "maxent.jar")
        if not os.path.isfile(maxent_file):
            gs.fatal(
                _(
                    "You did not provide the path to the maxent.jar file,\n"
                    "nor was it found in the addon script directory.\n"
                    "See the manual page for instructions."
                )
            )

    # Input parameters - building command line string
    # ------------------------------------------------------------------

    # names options
    comment_line_string = (
        f"java -mx{options['memory']}m -jar {maxent_file}"
        f" environmentallayers={options['environmentallayersfile']}"
        f" samplesfile={options['samplesfile']}"
        f" outputdirectory={options['outputdirectory']}"
        f" testsamplesfile={options['testsamplesfile']}"
        f" replicatetype={options['replicatetype']}"
        f" writemess=false warnings=true tooltips=true"
    )

    # Named input variable
    if bool(options["projectionlayers"]):
        comment_line_string = (
            f"{comment_line_string} projectionlayers={options['projectionlayers']}"
        )
    if options["nodata"] != "-9999":
        comment_line_string = f"{comment_line_string} nodata={options['nodata']}"
    if options["outputformat"] != "cloglog":
        comment_line_string = (
            f"{comment_line_string} outputformat={options['outputformat']}"
        )

    # True/false
    bool_options = {"togglelayertype": "prefixes=true"}
    option_list = [val for key, val in bool_options.items() if bool(options.get(key))]
    comment_line_string += " ".join(option_list)

    # Building the command line string - option = no
    bool_false = {
        "askoverwrite": "askoverwrite=false",
        "extrapolate": "extrapolate=false",
        "removeduplicates": "removeduplicates=false",
        "doclamp": "doclamp=false",
        "linear": "linear=false",
        "quadratic": "quadratic=false",
        "product": "product=false",
        "hinge": "hinge=false",
        "autofeature": "autofeature=false",
        "logscale": "logscale=false",
        "addsamplestobackground": "addsamplestobackground=false",
    }
    option_false = [val for key, val in bool_false.items() if options.get(key) == "no"]
    comment_line_string += " ".join(option_false)

    # Building the command line string - option = yes
    bool_true = {
        "writebackgroundpredictions": "writebackgroundpredictions=true",
        "writeplotdata": "writeplotdata=true",
        "fadebyclamping": "fadebyclamping=true",
        "threshold": "threshold=true",
        "jackknife": "jackknife=true",
        "responsecurves": "responsecurves=true",
        "addallsamplestobackground": "addallsamplestobackground=true",
    }
    option_true = [val for key, val in bool_true.items() if options.get(key) == "yes"]
    comment_line_string += " ".join(option_true)

    # Building the command line string - conditional on input value
    if int(options["randomtestpoints"]) > 0:
        comment_line_string = (
            f"{comment_line_string} randomtestpoints={int(options['randomtestpoints'])}"
        )
    if int(options["replicates"]) > 1:
        comment_line_string = (
            f"{comment_line_string} replicates={int(options['replicates'])}"
        )
    if bool(options["projectionlayers"]) and options["replicates"] == "1":
        comment_line_string = f"{comment_line_string} outputgrids=true"
    else:
        comment_line_string = f"{comment_line_string} outputgrids=false"
    bool_val = {
        "betamultiplier": "1.0",
        "maximumiterations": "500",
        "convergencethreshold": "0.00005",
        "lq2lqptthreshold": "80",
        "l2lqthreshold": "10",
        "hingethreshold": "15",
        "beta_threshold": "-1.0",
        "beta_categorical": "-1.0",
        "beta_lqp": "-1.0",
        "beta_hinge": "-1.0",
        "defaultprevalence": "0.5",
        "threads": "1",
    }
    option_val = [
        f"{key}={options.get(key)}"
        for key, val in bool_val.items()
        if options.get(key) != val
    ]
    comment_line_string += " ".join(option_val)

    # Flags
    bool_flags = {
        "s": "randomseed=true",
        "w": "autorun=false",
        "v": "visible=true",
    }
    options_flags = [val for key, val in bool_flags.items() if bool(flags.get(key))]
    comment_line_string += " ".join(options_flags)

    # -----------------------------------------------------------------
    # Run Maxent, train and create the model
    # -----------------------------------------------------------------
    gs.message(_("Maxent runtime messages"), flags="i")
    gs.message(_("-----------------------"), flags="i")
    popen = subprocess.Popen(
        comment_line_string, stdout=subprocess.PIPE, shell=True, universal_newlines=True
    )
    for stdout_line in iter(popen.stdout.readline, ""):
        print(stdout_line),
    gs.message(_("-----------------------\n"), flags="i")
    gs.message(
        _(
            "Done, you can find the model outputs in:\n {}\n".format(
                options["outputdirectory"]
            )
        ),
        flags="i",
    )
    gs.message(_("-----------------------\n"))

    # -----------------------------------------------------------------
    # Get relevant statistics to present
    # -----------------------------------------------------------------
    reps = int(options["replicates"])
    if reps > 1:
        if options["replicatetype"] == "crossvalidate":
            valtype = "crossvalidation"
        elif options["replicatetype"] == "bootstrap":
            valtype = "bootstrapping"
        else:
            valtype = "subsampling"
        msg = (
            "A {0} with {1} replications was carried out.\n"
            "The average and standard deviaton of the AUC of the"
            "\n {1} submodels are presented below.\n\n".format(
                valtype, options["replicates"]
            )
        )
        gs.message(_(msg), flags="i")
    else:
        gs.message(_("The AUC of the model is printed below:\n"), flags="i")

    statistics_file = os.path.join(options["outputdirectory"], "maxentResults.csv")
    with open(statistics_file, "r") as file:
        stats = csv.reader(file)
        variables = []
        variables = next(stats)
        rows = []
        for row in stats:
            rows.append(row)

    statistics = rows[len(rows) - 1]
    i = variables.index("#Training samples")
    gs.message(_(f"Number of training samples: {statistics[i]}"), flags="i")
    i = variables.index("#Background points")
    gs.message(_(f"Number of background points: {statistics[i]}"), flags="i")
    i = variables.index("Training AUC")
    gs.message(_(f"Training AUC: {statistics[i]}"), flags="i")
    try:
        i = variables.index("Test AUC")
        msg = f"Test AUC: {statistics[i]}"
        i = variables.index("AUC Standard Deviation")
        gs.message(_("{} (+/- {})".format(msg, statistics[i])), flags="i")
    except ValueError:
        gs.message(_("Test AUC: no test data was provided"), flags="i")

    gs.message(_("-----------------------\n"), flags="i")

    # -----------------------------------------------------------------
    # Transpose the maxentResults.csv file and save
    # -----------------------------------------------------------------
    rows2 = list(map(list, zip(variables, *rows)))
    statistics_fileout = statistics_file.replace(".csv", "_trans.csv")
    with open(statistics_fileout, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(rows2)

    # -----------------------------------------------------------------
    # Get list with all files in the folder
    # -----------------------------------------------------------------
    all_files = all_files = os.listdir(options["outputdirectory"])
    # Check if v.db.pyupdate is installed
    plugins_installed = gs.read_command(
        "g.extension", flags="a", quiet=function_verbosity
    ).split("\n")

    # -----------------------------------------------------------------
    # Import sampleprediction files(s) grass gis
    # -----------------------------------------------------------------
    outputformat = options["outputformat"]
    if options["importsamplepredictions"] == "yes":
        gs.message(
            _("Importing the point layers with predictions in grass gis\n"), flags="i"
        )

        # Get names of samplePrediction files
        if int(options["replicates"]) > 1:
            prediction_csv = list()
            for i in range(0, int(options["replicates"])):
                prediction_csv += [
                    file
                    for file in all_files
                    if file.endswith(f"_{i}_samplePredictions.csv")
                ]
        else:
            prediction_csv = [
                file for file in all_files if file.endswith("_samplePredictions.csv")
            ]
        prediction_layers = [
            x.replace(".csv", f"{options['suffix']}") for x in prediction_csv
        ]
        coldef = (
            "X double precision, "
            "Y double precision, "
            "Test_vs_train varchar(10), "
            "Raw double precision, "
            "Cumulative double precision,"
            "Cloglog double precision"
        )

        nm = outputformat.capitalize()
        for index, file in enumerate(prediction_csv):
            msg = "Importing samplePrediction layer {} of {}".format(
                index + 1, len(prediction_csv)
            )
            gs.message(_(msg), flags="i")
            inputfile = os.path.join(options["outputdirectory"], file)
            if Check_if_layer_exist(prediction_layers[index]):
                gs.fatal(
                    _(
                        "The layer {} already exists (1)".format(
                            prediction_layers[index]
                        )
                    )
                )
            gs.run_command(
                "v.in.ascii",
                input=inputfile,
                output=prediction_layers[index],
                separator="comma",
                skip=1,
                columns=coldef,
                quiet=function_verbosity,
            )
            # Remove unused columns
            for col in ["Raw", "Cumulative", "Cloglog"]:
                if nm != col:
                    gs.run_command(
                        "v.db.dropcolumn",
                        map=prediction_layers[index],
                        columns=col,
                        quiet=function_verbosity,
                    )
            # Rename colomn for first layer
            if len(prediction_csv) > 1 and index == 0:
                col_rename = f"{nm},{nm}_1"
                gs.run_command(
                    "v.db.renamecolumn",
                    map=prediction_layers[0],
                    column=col_rename,
                    quiet=function_verbosity,
                )
            # Spatial join of layer to first layer
            if int(options["replicates"]) > 1 and index > 0:
                msg = "Combining samplePrediction layer and computing summary stats".format(
                    index + 1, len(prediction_csv)
                )
                colname = f"{nm}_{index+1}"
                gs.run_command(
                    "v.db.addcolumn",
                    map=prediction_layers[0],
                    columns=f"{colname} double precision",
                    quiet=True,
                )
                gs.run_command(
                    "v.what.vect",
                    map=prediction_layers[0],
                    column=colname,
                    query_map=prediction_layers[index],
                    query_column=nm,
                    quiet=True,
                )
                gs.run_command(
                    "g.remove",
                    flags="f",
                    type="vector",
                    name=prediction_layers[index],
                    quiet=function_verbosity,
                )

        # Calculate columns with summary stats
        if int(options["replicates"]) > 1:
            if "v.db.pyupdate" in plugins_installed:
                vars = [f"{nm}_{num}" for num in range(1, reps + 1)]
                vars_min = f"min({','.join(vars)})"
                vars_max = f"max({','.join(vars)})"
                vars_mean = f"({'+'.join(vars)})/{reps}"
                vars_range = "tmp999 - tmp888"
                gs.run_command(
                    "v.db.addcolumn",
                    map=prediction_layers[0],
                    columns="tmp888 double precision",
                    quiet=True,
                )
                gs.run_command(
                    "v.db.pyupdate",
                    map=prediction_layers[0],
                    column="tmp888",
                    expression=vars_min,
                    quiet=True,
                )
                gs.run_command(
                    "v.db.addcolumn",
                    map=prediction_layers[0],
                    columns="tmp999 double precision",
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.db.pyupdate",
                    map=prediction_layers[0],
                    column="tmp999",
                    expression=vars_max,
                    quiet=True,
                )
                gs.run_command(
                    "v.db.addcolumn",
                    map=prediction_layers[0],
                    columns=f"{nm}_mean double precision",
                    quiet=True,
                )
                gs.run_command(
                    "v.db.pyupdate",
                    map=prediction_layers[0],
                    column=f"{nm}_mean",
                    expression=vars_mean,
                    quiet=True,
                )
                gs.run_command(
                    "v.db.addcolumn",
                    map=prediction_layers[0],
                    columns=f"{nm}_range double precision",
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.db.pyupdate",
                    map=prediction_layers[0],
                    column=f"{nm}_range",
                    expression=vars_range,
                    quiet=True,
                )
                gs.run_command(
                    "v.db.dropcolumn",
                    map=prediction_layers[0],
                    columns="tmp888",
                    quiet=True,
                )
                gs.run_command(
                    "v.db.dropcolumn",
                    map=prediction_layers[0],
                    columns="tmp999",
                    quiet=function_verbosity,
                )
                for d in vars:
                    gs.run_command(
                        "v.db.dropcolumn",
                        map=prediction_layers[0],
                        columns=d,
                        quiet=function_verbosity,
                    )
            else:
                gs.message(
                    "Install v.db.pyupdate if you want summary stats\ninstead of stats for each submodel"
                )
            newname = prediction_layers[0].replace("_0_", "_")
            if Check_if_layer_exist(newname):
                gs.fatal(_("The layer {} already exists (2)".format(newname)))
            gs.run_command(
                "g.rename",
                vector=f"{prediction_layers[0]},{newname}",
                quiet=function_verbosity,
            )
            gs.message(
                _(
                    "Created the layer {} with the {} sample predictions".format(
                        outputformat, newname
                    )
                ),
                flags="i",
            )
        else:
            gs.message(
                _("Created the layer {} in grass gis".format(prediction_layers[0])),
                flags="i",
            )

        # Defined color column
        if len(prediction_csv) == 1:
            color_column = nm
            inputmap = prediction_layers[0]
        else:
            color_column = f"{nm}_mean"
            inputmap = newname
            # Drop columns test_vs_training if combined layer
            gs.run_command(
                "v.db.dropcolumn",
                map=inputmap,
                columns="Test_vs_train",
                quiet=function_verbosity,
            )
        gs.run_command(
            "v.colors",
            map=inputmap,
            use="attr",
            column=color_column,
            color="bcyr",
            quiet=function_verbosity,
        )

    # -----------------------------------------------------------------
    # Import the background file with predicted values in grass
    # -----------------------------------------------------------------
    if options["writebackgroundpredictions"] == "yes":
        gs.message(_("-----------------------\n"), flags="i")
        gs.message(
            _("Creating point layers with predictions at background locations\n"),
            flags="i",
        )

        # Import background predictions in case of replicates = 1
        if int(options["replicates"]) == 1:
            prediction_bgr = [
                file for file in all_files if file.endswith("backgroundPredictions.csv")
            ]
            if len(prediction_bgr) > 1:
                gs.fatal(
                    "Your output folder contains more than one backgroundPrediction file,"
                    "even though you did not ran any probably contains outputs from earlier models\n"
                    "Please make sure there is only one backgroundPrediction file."
                )
            prediction_bgrlay = prediction_bgr.replace(".csv", f"{options['suffix']}")
            # column names
            coldef = (
                "X double precision, "
                "Y double precision, "
                "Raw double precision, "
                "Cumulative double precision,"
                "Cloglog double precision"
            )
            gs.message(_("Importing backgroundPrediction layer"), flags="i")
            inputfile = os.path.join(options["outputdirectory"], prediction_bgr)
            if Check_if_layer_exist(prediction_bgrlay):
                gs.fatal(_("The layer {} already exists (3)".format(prediction_bgrlay)))
            gs.run_command(
                "v.in.ascii",
                input=inputfile,
                output=prediction_bgrlay,
                separator="comma",
                skip=1,
                columns=coldef,
                overwrite=flags["o"],
                quiet=function_verbosity,
            )
            colnames = list(
                gs.parse_command("db.columns", table=prediction_bgrlay).keys()
            )
            nm = colnames[find_index_case_insensitive(colnames, outputformat)]
            gs.run_command(
                "v.colors",
                map=prediction_bgrlay,
                use="attr",
                column=nm,
                color="bcyr",
                quiet=function_verbosity,
            )

        # Import background prediction points in case of replicates > 1
        else:
            prediction_bgr = [
                file
                for file in all_files
                if file.endswith("_avg.csv")
                or file.endswith("_stddev.csv")
                or file.endswith("_median.csv")
            ]
            prediction_bgrlay = [
                x.replace(".csv", f"{options['suffix']}") for x in prediction_bgr
            ]
            for index, file in enumerate(prediction_bgr):
                msg = "Importing backgroundPrediction layer {} {} of {}".format(
                    prediction_bgrlay[index], index + 1, len(prediction_bgr)
                )
                gs.message(_(msg), flags="i")
                inputfile = os.path.join(options["outputdirectory"], file)
                with open(inputfile) as f:
                    header_line = f.readline().strip("\n").split(",")
                coldef = [
                    f"{x.replace(' ', '_')} double precision" for x in header_line
                ]
                if Check_if_layer_exist(prediction_bgrlay[index]):
                    gs.fatal(
                        _(
                            "The layer {} already exists (4)".format(
                                prediction_bgrlay[index]
                            )
                        )
                    )
                gs.run_command(
                    "v.in.ascii",
                    input=inputfile,
                    output=prediction_bgrlay[index],
                    separator="comma",
                    skip=1,
                    columns=coldef,
                    overwrite=flags["o"],
                    quiet=function_verbosity,
                )

                # Create color table
                gs.run_command(
                    "v.colors",
                    map=prediction_bgrlay[index],
                    use="attr",
                    column=coldef[2].replace(" double precision", ""),
                    color="bcyr",
                    quiet=function_verbosity,
                )

    # -----------------------------------------------------------------
    # Import the raster filesin grass
    # -----------------------------------------------------------------
    if bool(options["projectionlayers"]):
        gs.message(_("-----------------------\n"), flags="i")
        gs.message(_("Importing the projection layers"), flags="i")
        asciilayers = [asc for asc in all_files if asc.endswith(".asc")]
        grasslayers = [gr.replace(".asc", f"{options['suffix']}") for gr in asciilayers]
        for idx, asci in enumerate(asciilayers):
            gs.message(
                _("Importing layer {} of {}".format(idx + 1, len(grasslayers))),
                flags="i",
            )
            asciifile = os.path.join(options["outputdirectory"], asci)
            if Check_if_layer_exist(asciifile):
                gs.fatal(_("The layer {} already exists (5)".format(grasslayers[idx])))
            gs.run_command(
                "r.in.gdal",
                flags="o",
                input=asciifile,
                output=grasslayers[idx],
                memory=int(options["memory"]),
                quiet=function_verbosity,
                overwrite=flags["o"],
            )
            gs.message(_("Imported {}".format(grasslayers[idx])), flags="i")
    gs.message(_("---------Done----------\n"), flags="i")


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
