#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.maxent.predict
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Create a predicted suitability distribution layer using a
#               Maxent model (lambda file) and set of environmental raster
#               layers as input. The lambda model file can be created by
#               the Maxent software directly, or using the r.maxent.train
#               addon, which provides a convenient wrapper to the Maxent
#               (https://biodiversityinformatics.amnh.org/open_source/maxent/).
#
# COPYRIGHT:   (C) 2024 Paulo van Breugel and the GRASS Development Team
#              https://ecodiv.earth
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

# %Module
# % description: Use a Maxent model to create a suitability distribution layer
# % keyword: modeling
# % keyword: Maxent
# %end

# %option G_OPT_F_BIN_INPUT
# % key: lambdafile
# % label: Lambda model file
# % description: Lambda model file created by Maxent or the r.maxent.train addon.
# % guisection: input
# % required: yes
# %end

# %option
# % key: evp_maps
# % type: string
# % description: Names of the raster layers representing the environmental variables used in the Maxent model.
# % required : yes
# % multiple : yes
# % gisprompt: old,cell,raster
# % guisection: input
# %end

# %option
# % key: alias_names
# % type: string
# % label: alias names
# % description: Names of the environmental parameter(s) as used in the model. These need to be given in the same order as the corresponding raster layers.
# % required : no
# % guisection: input
# %end

# %option G_OPT_F_BIN_INPUT
# % key: alias_file
# % label: Alias file
# % description: A csv file with in the first column the names of the explanatory variable names as used in the model, and in the second column the names of the names of the corresponding raster layers.
# % guisection: input
# % required: no
# %end

# %rules
# % excludes: alias_file,alias_names,evp_maps
# %end

# %flag
# % key: c
# % label: Do not apply clamping
# % description: Do not apply clamping when projecting.
# % guisection: parameters
# %end

# %flag
# % key: f
# % label: Fade effect clamping
# % description: Reduce prediction at each point in projections by the difference between clamped and non-clamped output at that point.
# % guisection: parameters
# %end

# %rules
# % excludes: -c, -f
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
# % key: i
# % label: Copy maxent.jar to addon directory
# % description: Copy the maxent.jar (path provided with the 'maxent' parameter) to the addon scripts directory.
# %end

# %flag
# % key: u
# % label: Overwrites maxent.jar in addon directory
# % description: Copy the maxent.jar (path provided with the 'maxent' parameter) to the addon scripts directory. If the file already exist in the addon directory, it is overwritten.
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

    options = {
        "lambdaFile": "Bradypus_tridactylus.lambdas",
        "evp_maps": "bio02,bio04",
        "alias_names": "bio02,bio04",
        "alias_file": "/home/paulo/data/aliasfile.csv",
        "maxent": "maxent.jar",
        "threads": 8,
        "memory": 30000,
    }
    flags = {"c": False, "f": False, "v": False, "i": False, "u": False}

    # Names of variables and corresponding layer names
    # ------------------------------------------------------------------
    if bool(options["alias_file"]):
        import csv

        with open(options["alias_file"]) as csv_file:
            row_data = list(csv.reader(csv_file, delimiter=","))
        col_data = list(zip(*row_data))

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
        gs.info(_("Created the layer {} in GRASS GIS".format(newname)))

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

    # Import the raster files in GRASS
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
