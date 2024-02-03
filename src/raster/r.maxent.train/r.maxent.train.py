#!/usr/bin/env python

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

# %Module
# % description: Create and train a Maxent model
# % keyword: modeling
# % keyword: Maxent
# %End

# %option G_OPT_F_BIN_INPUT
# % key: samplesfile
# % label: Sample file presence locations
# % description: Please enter the name of a file containing presence locations for one or more species.
# % guisection: Input
# % required: yes
# %end

# %option G_OPT_F_BIN_INPUT
# % key: environmentallayersfile
# % label: Sample file with background locations
# % description:  Please enter the file name of the SWD file with environmental variables (can be created with v.maxent.swd or r.out.maxent_swd).
# % guisection: Input
# % required: yes
# %end

# %option
# % key: togglelayertype
# % type: string
# % label: Prefix that identifies categorical data
# % description: Toggle continuous/categorical for environmental variables whose names begin with this prefix (default: all continuous)
# % guisection: Input
# %end

# %option G_OPT_M_DIR
# % key: projectionlayers
# % label: Location of an alternate set of environmental variables.
# % description: Location of an alternate set of environmental variables. Maxent models will be projected onto these variables. The result will be imported in grass gis.
# % guisection: Input
# % required: no
# %end

# %option
# % key: suffix
# % type: string
# % label: Suffix for name(s) of prediction layer(s)
# % description: Add a suffix to the name(s) of imported prediction layer(s)
# % guisection: Input
# %end

# %option
# % key: nodata
# % type: integer
# % label: Nodata values
# % description: Value to be interpreted as nodata values in SWD sample data
# % answer : -9999
# % required: no
# % guisection: Input
# %end

# %option G_OPT_M_DIR
# % key: outputdirectory
# % label: Directory where outputs will be written.
# % description: Directory where outputs will be written. This should be different from the environmental layers directory.
# % guisection: Output
# % required: yes
# %end

# %flag
# % key: y
# % label: Create a vector point layer from the sample predictions
# % description: Import the the file(s) with sample predictions as point feature layer.
# % guisection: Output
# %end

# %option G_OPT_V_OUTPUT
# % key: samplepredictions
# % label: Name of sample prediction layer
# % description: Give the name of sample prediction layer. If you leave this empty, the default name given by Maxent will be used.
# % guisection: Output
# % required: no
# %end

# %rules
# % requires: samplepredictions, -y
# %end

# %flag
# % key: b
# % label: Create a vector point layer with predictions at background points
# % description: Create a vector point layer with predictions at background points
# % guisection: Output
# %end

# %option G_OPT_V_OUTPUT
# % key: backgroundpredictions
# % label: Name of background prediction layer
# % description: Give the name of background prediction layer. If you leave this empty, the default name given by Maxent will be used.
# % guisection: Output
# % required: no
# %end

# %rules
# % requires: backgroundpredictions, -b
# %end

# %option G_OPT_R_OUTPUT
# % key: predictionlayer
# % label: Name of raster prediction layer
# % description: Give the name of raster prediction layer. If you leave this empty, the default name given by Maxent will be used.
# % guisection: Output
# % required: no
# %end

# %rules
# % requires: predictionlayer, projectionlayers
# %end

# %flag
# % key: g
# % label: Create response curves.
# % description: Create graphs showing how predicted relative probability of occurrence depends on the value of each environmental variable.
# % guisection: Output
# %end

# %flag
# % key: w
# % label: Write response curve data to file
# % description: Write output files containing the data used to make response curves, for import into external plotting software.
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
# % key: betamultiplier
# % type: double
# % label: Multiply all automatic regularization parameters by this number.
# % description: Multiply all automatic regularization parameters by this number. A higher number gives a more spread-out distribution.
# % answer: 1.0
# % guisection: Parameters
# %end

# %flag
# % key: e
# % label: Extrapolate
# % description: Predict to regions of environmental space outside the limits encountered during training.
# % guisection: Parameters
# %end

# %flag
# % key: c
# % label: Do not apply clamping
# % description: Do not apply clamping when projecting.
# % guisection: Parameters
# %end

# %flag
# % key: f
# % label: Fade effect clamping
# % description: Reduce prediction at each point in projections by the difference between clamped and non-clamped output at that point.
# % guisection: Parameters
# %end

# %rules
# % excludes: -c, -f
# %end

# %flag
# % key: l
# % label: Disable linear features
# % description: Do not use linear features for the model (they are used by default).
# % guisection: Parameters
# %end

# %flag
# % key: q
# % label: Disable quadratic features
# % description: Do not use quadratic features for the model (they are used by default).
# % guisection: Parameters
# %end

# %flag
# % key: p
# % label: Disable product features
# % description: Do not use product features for the model (they are used by default).
# % guisection: Parameters
# %end

# %flag
# % key: t
# % label: Use product features
# % description: By default, threshold features are not used. Use this flag to enable them.
# % guisection: Parameters
# %end

# %flag
# % key: h
# % label: Disable hinge features
# % description: Do not use hinge features for the model (they are used by default).
# % guisection: Parameters
# %end

# %flag
# % key: a
# % label: Do not use automatic selection of feature classes
# % description: By default, Maxent automatically select which feature classes to use, based on number of training samples. Use this flag to disable autoselection of features.
# % guisection: Parameters
# %end

# %flag
# % key: n
# % label: Don't add sample points to background if conditions differ
# % description: By default, samples that have a combination of environmental values that isn't already present in the background are added to the background samples. Use this flag to avoid that.
# % guisection: Parameters
# %end

# %flag
# % key: j
# % label: Use jacknife validation
# % description: Measure importance of each environmental variable by training with each environmental variable first omitted, then used in isolation.
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

# %flag
# % key: d
# % label: Keep duplicate presence records.
# % description: Keep duplicate presence records. If environmental data are in grids, duplicates are records in the same grid cell. Otherwise, duplicates are records with identical coordinates.
# % guisection: Advanced
# %end

# %flag
# % key: s
# % label: Use a random seed
# % description: If selected, a different random seed will be used for each run, so a different random test/train partition will be made and a different random subset of the background will be used, if applicable.
# % guisection: Advanced
# %end

# %flag
# % key: x
# % label: Add all samples to the background
# % description: Add all samples to the background, even if they have combinations of environmental values that are already present in the background
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
# % key: m
# % label: Do not autorun Maxent
# % description: When you select this option, Maxent will not start before you hit the start option. This will set the -v flag to true (overriding user choice).
# %end

# %flag
# % key: i
# % label: Copy maxent.jar to addon directory
# % description: Copy the maxent.jar (path provided with the 'maxent' parameter) to the addon scripts directory.
# %end

# %flag
# % key: u
# % label: Overwrites maxent.jar in addon directory
# % description: Copy the maxent.jar (path provided with the 'maxent' parameter) to the addon scripts directory. If the file already exist in the addon directory, it is overwritten.
# %end

# %rules
# % exclusive: replicates,randomtestpoints
# % exclusive: -i, -u
# %end

# import libraries
# ------------------------------------------------------------------
import atexit
import csv
import re
import os
import shutil
import subprocess
import sys
import uuid
import numpy as np
import grass.script as gs


CLEAN_LAY = []


# Funtions
# ------------------------------------------------------------------
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


def create_temporary_name(prefix):
    tmpf = f"{prefix}{str(uuid.uuid4().hex)}"
    CLEAN_LAY.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    maps = reversed(CLEAN_LAY)
    mapset = gs.gisenv()["MAPSET"]
    for map_name in maps:
        for element in ("raster", "vector"):
            found = gs.find_file(
                name=map_name,
                element=element,
                mapset=mapset,
            )
            if found["file"]:
                gs.run_command(
                    "g.remove",
                    flags="f",
                    type=element,
                    name=map_name,
                    quiet=True,
                )


def repl_char(keep, strlist, replwith):
    """Replace all characters except those in newstr"""
    nwlist = list()
    for i in keep:
        for j in strlist:
            i = i.replace(j, replwith)
        nwlist += [i]
    return nwlist


# Main
# ------------------------------------------------------------------
def main(options, flags):
    # Set verbosity level
    # ------------------------------------------------------------------
    if gs.verbosity() > 2:
        function_verbosity = False
    else:
        function_verbosity = True

    # Checking availability of maxent.jar
    # ------------------------------------------------------------------
    path_to_maxent = options["maxent"]
    if bool(path_to_maxent):
        maxent_file = options["maxent"]
        if not os.path.isfile(maxent_file):
            msg = "The maxent.jar file was not found on the location you provided"
            gs.fatal(_(msg))
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
                msg = (
                    "There is already a maxent.jar file in the scripts \n"
                    "directory. Remove the -i flag. If you want to update \n"
                    " the maxent.jar file, use the -u flag instead."
                )
                gs.fatal(_(msg))
            else:
                shutil.copyfile(maxent_file, maxent_copy)
                msg = "Copied the maxent.jar file to the grass gis addon script directory .\n\n"
                gs.info(_(msg))
        if bool(flags["u"]):
            shutil.copyfile(maxent_file, maxent_copy)
            msg = "Copied the maxent.jar file to the grass gis addon script directory .\n\n"
            gs.info(_(msg))
    else:
        maxent_file = os.environ.get("GRASS_ADDON_BASE")
        maxent_file = os.path.join(maxent_file, "scripts", "maxent.jar")
        if not os.path.isfile(maxent_file):
            msg = (
                "You did not provide the path to the maxent.jar file,\n"
                "nor was it found in the addon script directory.\n"
                "See the manual page for instructions."
            )
            gs.fatal(_(msg))

    # Check variable names in swd files and environmental layers
    # ------------------------------------------------------------------
    envir_layers = options["environmentallayersfile"]
    sample_layers = options["samplesfile"]
    with open(envir_layers) as f:
        header_environ = f.readline().strip("\n").split(",")
    with open(sample_layers) as f:
        header_samples = f.readline().strip("\n").split(",")
    if header_samples != header_environ:
        envp = os.path.basename(envir_layers)
        samp = os.path.basename(sample_layers)
        msg = "The columnnames in the {} and {} files are not the same".format(
            envp, samp
        )
        gs.fatal(_(msg))
    envir_layers = options["projectionlayers"]
    if bool(envir_layers):
        envir_files = os.listdir(options["projectionlayers"])
        envir_names = [asc for asc in envir_files if asc.endswith(".asc")]
        envir_names = [n.replace(".asc", "") for n in envir_names]
        if not set(header_samples[3:]).issubset(envir_names):
            msg = "Not all variables are available as ascii files in:\n {}".format(
                envir_layers
            )
            gs.fatal(_(msg))

    # Input parameters - building command line string
    # ------------------------------------------------------------------
    # Conditional
    if flags["m"]:
        flags["v"] = True

    # names options
    maxent_command = [
        "java",
        f"-mx{options['memory']}m",
        "-jar",
        maxent_file,
        f"environmentallayers={options['environmentallayersfile']}",
        f"samplesfile={options['samplesfile']}",
        f"outputdirectory={options['outputdirectory']}",
        "writemess=false",
    ]

    # If not default value
    bool_val = {
        "replicatetype": "crossvalidate",
        "randomtestpoints": "0",
        "replicates": "1",
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
        "nodata": "-9999",
        "outputformat": "cloglog",
        "togglelayertype": "",
        "projectionlayers": "",
        "testsamplesfile": "",
    }
    maxent_command += [
        f"{key}={options.get(key)}"
        for key, val in bool_val.items()
        if options.get(key) != val
    ]

    # Flags (true/false)
    bool_flags = {
        "g": "responsecurves=true",
        "w": "writeplotdata=true",
        "b": "writebackgroundpredictions=true",
        "e": "extrapolate=true",
        "c": "doclamp=false",
        "f": "fadebyclamping=true",
        "l": "linear=false",
        "q": "quadratic=false",
        "p": "product=false",
        "h": "hinge=false",
        "t": "threshold=true",
        "a": "autofeature=false",
        "n": "addsamplestobackground=false",
        "j": "jackknife=true",
        "d": "removeduplicates=false",
        "s": "randomseed=true",
        "x": "addallsamplestobackground=true",
    }
    maxent_command += [val for key, val in bool_flags.items() if flags.get(key)]
    bool_flags = {
        "v": "visible=false",
        "m": "autorun=true",
    }
    maxent_command += [val for key, val in bool_flags.items() if not flags.get(key)]

    # Building the command line string - conditional on multiple input value
    if bool(options["projectionlayers"]):
        if options["replicates"] == "1":
            maxent_command += ["outputgrids=true"]
        else:
            maxent_command += ["outputgrids=false"]

    # Run Maxent, train and create the model
    # -----------------------------------------------------------------
    gs.info(_("Maxent runtime messages"))
    gs.info(_("-----------------------"))

    with subprocess.Popen(
        maxent_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ) as process:
        # Capture and print stdout
        for stdout_line in process.stdout:
            gs.info(stdout_line)
        # Capture and print stderr
        for stderr_line in process.stderr:
            gs.info(stderr_line)
        # Check the return code
        process.wait()
        if process.returncode != 0:
            gs.fatal(_("Maxent terminated with an error"))
    msg = "Done, you can find the model outputs in:\n {}\n".format(
        options["outputdirectory"]
    )
    gs.info(_(msg))
    gs.info(_("-----------------------\n"))

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
        gs.info(_(msg))
    else:
        gs.info(_("Basic stats about the model are printed below:\n"))

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
    gs.info(_(f"Number of training samples: {statistics[i]}"))
    i = variables.index("#Background points")
    gs.info(_(f"Number of background points: {statistics[i]}"))
    i = variables.index("Training AUC")
    print(_(f"Training AUC: {statistics[i]}"))
    try:
        i = variables.index("Test AUC")
        msg = f"Test AUC: {statistics[i]}"
        i = variables.index("AUC Standard Deviation")
        gs.message(_("{} (+/- {})".format(msg, statistics[i])))
    except ValueError:
        gs.info(_("Test AUC: no test data was provided"))

    # Transpose the maxentResults.csv file and save
    # -----------------------------------------------------------------
    rows2 = list(map(list, zip(variables, *rows)))
    statistics_fileout = statistics_file.replace(".csv", "_trans.csv")
    with open(statistics_fileout, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(rows2)

    # -----------------------------------------------------------------
    # Get list with all files in the output folder
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
    reps = int(options["replicates"])
    if bool(flags["y"]):
        gs.info(_("-----------------------\n"))
        gs.info(_("Importing the point layers with predictions in grass gis\n"))

        # Get names of samplePrediction files
        if reps > 1:
            prediction_csv = list()
            for i in range(0, reps):
                prediction_csv += [
                    file
                    for file in all_files
                    if file.endswith(f"_{i}_samplePredictions.csv")
                ]
        else:
            prediction_csv = [
                file for file in all_files if file.endswith("_samplePredictions.csv")
            ]
        prediction_layers = [create_temporary_name("x") for x in prediction_csv]

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
            gs.info(_(msg))
            inputfile = os.path.join(options["outputdirectory"], file)
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
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.what.vect",
                    map=prediction_layers[0],
                    column=colname,
                    query_map=prediction_layers[index],
                    query_column=nm,
                    quiet=function_verbosity,
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
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.db.pyupdate",
                    map=prediction_layers[0],
                    column="tmp888",
                    expression=vars_min,
                    quiet=function_verbosity,
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
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.db.addcolumn",
                    map=prediction_layers[0],
                    columns=f"{nm}_mean double precision",
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.db.pyupdate",
                    map=prediction_layers[0],
                    column=f"{nm}_mean",
                    expression=vars_mean,
                    quiet=function_verbosity,
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
                    quiet=function_verbosity,
                )
                gs.run_command(
                    "v.db.dropcolumn",
                    map=prediction_layers[0],
                    columns="tmp888",
                    quiet=function_verbosity,
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
                gs.warning(
                    "Install v.db.pyupdate if you want summary stats\n"
                    "instead of stats for each submodel"
                )
        if bool(options["samplepredictions"]):
            newname = f"{options['samplepredictions']}{options['suffix']}"
        else:
            newname = (
                prediction_csv[0].replace(".csv", options["suffix"]).replace("_0_", "_")
            )
        gs.run_command(
            "g.rename",
            vector=f"{prediction_layers[0]},{newname}",
            quiet=function_verbosity,
        )
        gs.info(_("Created the layer {} in grass gis".format(newname)))

        # Defined color column
        if "v.db.pyupdate" in plugins_installed:
            if len(prediction_csv) == 1:
                color_column = nm
            else:
                color_column = f"{nm}_mean"
                gs.run_command(
                    "v.db.dropcolumn",
                    map=newname,
                    columns="Test_vs_train",
                    quiet=function_verbosity,
                )
            gs.run_command(
                "v.colors",
                map=newname,
                use="attr",
                column=color_column,
                color="bcyr",
                quiet=function_verbosity,
            )

    # Import the background file with predicted values in grass
    # -----------------------------------------------------------------
    if flags["b"]:
        bkgrpoints = options["backgroundpredictions"]
        gs.info(_("-----------------------\n"))

        # Import background predictions in case of replicates = 1
        if reps == 1:
            prediction_bgr = [
                file for file in all_files if file.endswith("backgroundPredictions.csv")
            ]
            if len(prediction_bgr) > 1:
                gs.fatal(
                    "Your output folder contains more than one backgroundPrediction file,"
                    "These might be output files from earlier models? Please make sure\n"
                    "there is only one backgroundPrediction file and run the model again."
                )
            prediction_bgrlay = [create_temporary_name("x")]
            if bool(bkgrpoints):
                prediction_bgrlay = f"{bkgrpoints}{options['suffix']}"
            else:
                prediction_bgrlay = prediction_bgr[0].replace(".csv", options["suffix"])

            # column names
            coldef = (
                "X double precision, "
                "Y double precision, "
                "Raw double precision, "
                "Cumulative double precision,"
                "Cloglog double precision"
            )
            msg = "Importing background Prediction point layer {}".format(
                prediction_bgrlay
            )
            gs.info(_(msg))
            inputfile = os.path.join(options["outputdirectory"], prediction_bgr[0])
            gs.run_command(
                "v.in.ascii",
                input=inputfile,
                output=prediction_bgrlay,
                separator="comma",
                skip=1,
                columns=coldef,
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
            gs.info(
                _("Creating point layers with predictions at background locations\n")
            )
            prediction_bgr = [
                file
                for file in all_files
                if file.endswith("_avg.csv")
                or file.endswith("_stddev.csv")
                or file.endswith("_median.csv")
            ]
            prediction_bgrlay = [
                x.replace(".csv", options["suffix"]) for x in prediction_bgr
            ]
            pattern = re.compile(r"_([^_]+\.csv)$")
            result = re.sub(pattern, "", prediction_bgr[0])
            if bool(bkgrpoints):
                prediction_bgrlay = [
                    x.replace(result, bkgrpoints) for x in prediction_bgrlay
                ]
            for index, file in enumerate(prediction_bgr):
                msg = "Importing {}: {} of {}".format(
                    prediction_bgrlay[index], index + 1, len(prediction_bgr)
                )
                gs.info(_(msg))
                inputfile = os.path.join(options["outputdirectory"], file)
                with open(inputfile) as f:
                    header_line = f.readline().strip("\n").split(",")
                r = f"{result}_"
                coldef = [
                    f"{x.replace(' ', '_')} double precision" for x in header_line
                ]
                coldef = [x.replace(r, "") for x in coldef]
                gs.run_command(
                    "v.in.ascii",
                    input=inputfile,
                    output=prediction_bgrlay[index],
                    separator="comma",
                    skip=1,
                    columns=coldef,
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

    # Import the raster files in grass
    # -----------------------------------------------------------------
    if options["projectionlayers"]:
        gs.info(_("-----------------------\n"))
        gs.info(_("Importing the raster projection layers"))

        predlays = options["predictionlayer"]
        asciilayers = [asc for asc in all_files if asc.endswith(".asc")]
        grasslayers = [gr.replace(".asc", f"{options['suffix']}") for gr in asciilayers]
        pattern = re.compile(r"_([^_]+\.asc)$")
        result = re.sub(pattern, "", asciilayers[0])
        if bool(predlays):
            grasslayers = [x.replace(result, predlays) for x in grasslayers]
        for idx, asci in enumerate(asciilayers):
            gs.info(_("Importing layer {} of {}".format(idx + 1, len(grasslayers))))
            asciifile = os.path.join(options["outputdirectory"], asci)
            gs.run_command(
                "r.in.gdal",
                flags="o",
                input=asciifile,
                output=grasslayers[idx],
                memory=int(options["memory"]),
                quiet=function_verbosity,
            )
            gs.info(_("Imported {}".format(grasslayers[idx])))
    gs.info(_("---------Done----------\n"))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
