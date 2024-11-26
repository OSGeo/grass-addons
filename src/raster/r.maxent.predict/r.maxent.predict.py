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
# %end

# %option G_OPT_R_INPUTS
# % key: rasters
# % type: string
# % label: Names of the input raster layers
# % description: Names of the raster layers representing the environmental variables used in the Maxent model.
# % required : no
# % guisection: input
# %end

# %option
# % key: variables
# % type: string
# % label: variable names
# % description: Names of the environmental parameter(s) as used in the model. These need to be given in the same order as the corresponding raster layers. If left out, the names are assumed to be the same as the name of the raster layers.
# % required : no
# % guisection: input
# %end

# %option G_OPT_M_DIR
# % key: projectionlayers
# % label: Location of folder with set of environmental variables.
# % description: Directory with set of rasters representing the same environmental variables as used to create the Maxent model. The names of the raster layers, excluding the file extension, need to be the same as the variable names used to create the Maxent model.
# % guisection: input
# % required: no
# %end

# %rules
# % excludes: projectionlayers,rasters,variables
# %end

# %option G_OPT_F_BIN_INPUT
# % key: alias_file
# % label: csv file with variable and layer names
# % description: A csv file with in the first column the names of the explanatory variables used in the model, and in the second column the names of corresponding raster layers. Make sure both are provided in the same order.
# % guisection: input
# % required: no
# %end

# %rules
# % excludes: alias_file,variables,rasters
# %end

# %flag
# % key: e
# % label: Automatically adapt resolution
# % description: When the ns and ew resolution are not the same, nearest neighbor resampling will be used to ensure both are the same.
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Prediction raster layer
# % description: The name of the raster layer with the predicted suitability scores
# % guisection: output
# % required: yes
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

# %option G_OPT_F_BIN_INPUT
# % key: java
# % label: Location java executable
# % description: If Java is installed, but cannot be found, the user can provide the path to the java executable file. Note, an alternative is to use the r.maxent.setup addon.
# % required: no
# %end

# %option G_OPT_MEMORYMB
# % Description: Maximum memory to be used by Maxent (in MB)
# %end

# %flag
# % key: p
# % label: Print Maxent command
# % description: Print the Maxent command used to create the prediction layer. For debugging.
# %end

# import libraries
# ------------------------------------------------------------------
import atexit
import csv
import os
import shutil
import subprocess
import sys
import uuid
import grass.script as gs

# Functions
# ------------------------------------------------------------------


def find_index_case_insensitive(lst, target):
    """
    Find index for string match, matching case insensitive
    """
    for i, item in enumerate(lst):
        if item.lower() == target.lower():
            return i
    return -1  # Return -1 if the element is not found


def cleanup():
    """Remove temporary maps specified in the global list"""
    try:
        shutil.rmtree(temp_directory)
    except:
        pass


def check_layers(layers):
    missing_layers = []
    double_layers = []
    current_mapset = gs.gisenv()["MAPSET"]
    for layer in layers:
        if "@" in layer:
            layname, mpset = layer.split("@")
        else:
            layname = layer
            mpset = ""

        # List raster layers matching the pattern in the specified mapset
        chlay = gs.parse_command(
            "g.list", flags="m", type="raster", pattern=layname, mapset=mpset
        )

        # Check if the layer exists in the current mapset
        chlay_mapsets = {mapsetname.split("@")[1] for mapsetname in chlay.keys()}
        if not chlay:
            missing_layers.append(layer)
        elif len(chlay) > 1 and current_mapset not in chlay_mapsets:
            double_layers.append(layer)
    return {"missing": missing_layers, "double": double_layers}


def create_temp_name(prefix):
    tmpf = f"{prefix}{str(uuid.uuid4().hex)}.asc"
    return tmpf


def strip_mapset(name, join_char="@"):
    """Strip Mapset name and '@' from map name
    >>> strip_mapset('elevation@PERMANENT')
    elevation

    :param str name: map name
    :param str join_char: Character separating map and mapset name

    :return str: mapname without the mapset name
    """
    return name.split(join_char)[0] if join_char in name else name


def java_functional(java_path):
    """
    Check if Java can be found by running the 'java -version' command.

    Returns:
        bool: True if Java is findable, False otherwise.
    """
    try:
        # Run 'java -version' and suppress its output
        subprocess.run(
            [java_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_java_txtfile():
    """Check if there is a text file with path to java executables in the addon
    directory
    """
    addon_directory = os.environ.get("GRASS_ADDON_BASE")
    if not addon_directory:
        gs.warning(_("GRASS_ADDON_BASE environment variable is not set."))
        return None

    file_path = os.path.join(addon_directory, "scripts", "r_maxent_path_to_java.txt")
    if not os.path.isfile(file_path):
        return None

    try:
        with open(file_path, "r") as file:
            java_path = file.readline().strip()
    except Exception as e:
        gs.warning(_("File with path to java exists but cannot be read: {}".format(e)))
        return None

    if not java_path:
        gs.warning(_("The file 'r_maxent_path_to_java.txt' is empty"))
        return None

    if not os.path.exists(java_path) or not java_functional(java_path):
        gs.warning(
            _(
                "The path to the Java executable '{}', defined in the "
                "'r_maxent_path_to_java.txt' in the addon directory "
                "does not exist or is not functional.".format(java_path)
            )
        )
        return None

    return java_path


# Main
# ------------------------------------------------------------------
def main(options, flags):

    # Set verbosity level
    # ------------------------------------------------------------------
    if gs.verbosity() > 2:
        function_verbosity = False
    else:
        function_verbosity = True

    # Check if provided java executable exists
    # ------------------------------------------------------------------
    jav = check_java_txtfile()
    if options["java"]:
        java_path = os.path.normpath(options["java"])
        if not os.path.isfile(java_path):
            gs.fatal(_("Provided path to java executable cannot be found."))
        elif not java_functional(java_path):
            gs.fatal(_("Problem with provided java executable."))
        else:
            path_to_java = os.path.normpath(options["java"])
    elif jav:
        path_to_java = jav
    elif java_functional("java"):
        path_to_java = "java"
    else:
        gs.warning(
            _(
                "Java cannot be found. Please ensure Java is installed "
                "and/or properly configured to be accessible from GRASS. \n"
                "If you are sure Java is installed, you can provide the path "
                "to the java executable using the 'java' parameter. \n"
                "For a more permanent solution, see the r.maxent.setup addon."
            )
        )

    # Checking availability of maxent.jar
    # ------------------------------------------------------------------
    if bool(options["maxent"]):
        maxent_file = os.path.normpath(options["maxent"])
        if not os.path.isfile(maxent_file):
            msg = "The maxent.jar file was not found on the location you provided"
            gs.fatal(_(msg))
    else:
        maxent_file = os.environ.get("GRASS_ADDON_BASE")
        maxent_file = os.path.join(maxent_file, "scripts", "maxent.jar")
        if not os.path.isfile(maxent_file):
            msg = (
                "You did not provide the path to the maxent.jar file,\n"
                "nor was it found in the addon script directory.\n"
                "See the manual page of r.maxent.setup for instructions."
            )
            gs.fatal(_(msg))

    # Check if X and Y resolution is equal
    # ------------------------------------------------------------------
    regioninfo = gs.parse_command("g.region", flags="g")
    if regioninfo["nsres"] != regioninfo["ewres"]:
        if flags["e"]:
            new_resolution = min(float(regioninfo["nsres"]), float(regioninfo["ewres"]))
            gs.run_command("g.region", flags="a", res=new_resolution)
            gs.message(
                "The ns and ew resolution of the current computational region are"
                " not the same\n. Resampling to the smallest of the two ({})".format(
                    round(new_resolution, 12)
                )
            )
        else:
            gs.fatal(
                "The ns and ew resolution of the computational region do not match.\n"
                "Change the resolution yourself or set the -e flag. Using the\n"
                "-e flag will adjust the resolution so both the ns and ew resolution\n"
                "match the smallest of the two, using nearest neighbor resampling."
            )

    # Create (or get) folder with environmental layers
    # ------------------------------------------------------------------

    projectionlayers = options["projectionlayers"]
    if projectionlayers:
        # The name of an existing folder with layers is provided
        temp_directory = projectionlayers
    else:
        # Create temporary folder for the raster layers
        temp_directory = gs.tempdir()

        # Get Get names of variables and corresponding layer names
        if bool(options["alias_file"]):
            with open(options["alias_file"]) as csv_file:
                row_data = list(csv.reader(csv_file, delimiter=","))
            col_data = list(zip(*row_data))
            file_names = col_data[0]
            layer_names = col_data[1]
        else:
            layer_names = options["rasters"].split(",")
            if bool(options["variables"]):
                file_names = options["variables"].split(",")
            else:
                file_names = [strip_mapset(x) for x in layer_names]
        chlay = check_layers(layer_names)
        if len(chlay["missing"]) > 0:
            gs.fatal(
                _(
                    "The layer(s) {} do not exist in the accessible mapsets".format(
                        ", ".join(chlay["missing"])
                    )
                )
            )
        if len(chlay["double"]) > 0:
            gs.fatal(
                _(
                    "There are layers with the name {} in multiple accessible mapsets, "
                    "none of which are in the current mapset."
                    "Add the mapset name to specify which or these layers should be used.".format(
                        ", ".join(chlay["double"])
                    )
                )
            )

        # Export raster layers to temporary directory
        gs.info(_("Export the raster layers as asci layers for use by Maxent\n"))
        gs.info(_("This may take some time ... please be patient.\n"))

        for n, layer_name in enumerate(layer_names):
            dt = gs.parse_command("r.info", map=layer_name, flags="g")["datatype"]
            if dt == "CELL":
                datatype = "Int16"
                nodataval = -9999
            else:
                datatype = ""
                nodataval = -9999999
            file_name = os.path.join(temp_directory, f"{file_names[n]}.asc")
            gs.run_command(
                "r.out.gdal",
                input=layer_name,
                output=file_name,
                format="AAIGrid",
                flags="c",
                type=datatype,
                nodata=nodataval,
                quiet=True,
            )

    # Input parameters - building command line string
    # ------------------------------------------------------------------
    gs.info(_("Running Maxent to create the prediction layer\n"))

    temp_file = os.path.join(temp_directory, create_temp_name("mxt_"))
    maxent_command = [
        path_to_java,
        f"-mx{options['memory']}m",
        "-cp",
        maxent_file,
        "density.Project",
        options["lambdafile"],
        temp_directory,
        temp_file,
    ]
    bool_flags = {
        "c": "doclamp=false",
        "f": "fadebyclamping=true",
    }
    maxent_command += [val for key, val in bool_flags.items() if flags.get(key)]

    # Run Maxent density.Project
    # -----------------------------------------------------------------
    gs.info(_("This may take some time ..."))
    with subprocess.Popen(
        maxent_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        text=True,
    ) as process:
        # Capture and print stdout
        for stdout_line in process.stdout:
            gs.info(stdout_line)
        # Capture and print stderr
        for stderr_line in process.stderr:
            gs.info(f"Warning/Error: {stderr_line}")
            if "java.util.NoSuchElementException" in stderr_line:
                missing_variables = (
                    "Check variable names and path + names of input files"
                )
        # Check the return code
        process.wait()
        if process.returncode != 0:
            if missing_variables:
                gs.fatal(missing_variables)
            else:
                gs.fatal(_("Maxent terminated with an error"))
    # -----------------------------------------------------------------
    # Import the resulting layer in GRASS GIS
    # -----------------------------------------------------------------
    if not os.path.isfile(temp_file):
        gs.fatal(
            _(
                "Maxent did not create an output raster for import in GRASS.\n"
                "Check the error message(s) above."
            )
        )
    gs.info(_("Importing the predicted suitability layer in GRASS GIS\n"))
    gs.run_command(
        "r.in.gdal",
        flags="o",
        input=temp_file,
        output=options["output"],
        memory=int(options["memory"]),
        quiet=function_verbosity,
    )
    if bool(flags["p"]):
        msg = " ".join(maxent_command)
        gs.info(_("Run:\n {}".format(msg)))
    else:
        gs.info(_("Done"))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
