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
# % key: lambda
# % label: Lambda model file
# % description: Lambda model file created by Maxent or the r.maxent.train addon.
# % guisection: input
# %end

# %option G_OPT_R_INPUTS
# % key: raster
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
# % description: Names of the environmental parameter(s) as used in the model. These need to be given in the same order as the corresponding raster layers. If left out, the names are assumed to be the same as the  name of the raster layers.
# % required : no
# % guisection: input
# %end

# %option G_OPT_F_BIN_INPUT
# % key: alias_file
# % label: csv file with variable and layer names
# % description: A csv file with in the first column the names of the explanatory variables used in the model, and in the second column the names of corresponding raster layers. Make both are provided in the same order.
# % guisection: input
# % required: no
# %end

# %rules
# % excludes: alias_file,variables,raster
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

# %option G_OPT_MEMORYMB
# % Description: Maximum memory to be used by Maxent (in MB)
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


temp_directory = gs.tempdir()


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


def cleanup():
    """Remove temporary maps specified in the global list"""
    try:
        shutil.rmtree(temp_directory)
    except:
        pass


def check_layers_exist(layers):
    """
    Check if all layers in a list exist in accessible mapsets.

    param str layers: names of layers

    return list: list with names of missing layers
    """
    missing_layers = []
    for layer in layers:
        # Check if the layer exists in the current mapset
        if not gs.find_file(name=layer)["fullname"]:
            missing_layers.append(layer)
    return missing_layers


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


# Main
# ------------------------------------------------------------------
def main(options, flags):

    # Set verbosity level
    # ------------------------------------------------------------------
    if gs.verbosity() > 2:
        function_verbosity = False
    else:
        function_verbosity = True

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

    # Get names of variables and corresponding layer names
    # ------------------------------------------------------------------
    gs.info(_("Check if the variable and layer names correspond\n"))

    if bool(options["alias_file"]):
        with open(options["alias_file"]) as csv_file:
            row_data = list(csv.reader(csv_file, delimiter=","))
        col_data = list(zip(*row_data))
        chlay = check_layers_exist(col_data[1])
        if len(chlay) > 0:
            gs.message(
                _(
                    "The layer(s) {} do not exist in the accessible mapsets".format(
                        ", ".join(chlay)
                    )
                )
            )
        else:
            file_names = col_data[0]
            layer_names = col_data[1]
    else:
        layer_names = options["raster"].split(",")
        if bool(options["variables"]):
            file_names = options["variables"].split(",")
        else:
            file_names = [strip_mapset(x) for x in layer_names]

    # Export raster layers to temporary directory
    # ------------------------------------------------------------------
    gs.info(_("Export the raster layers as asci layers for use by Maxent\n"))

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
        "java",
        f"-mx{options['memory']}m",
        "-cp",
        maxent_file,
        "density.Project",
        options["lambda"],
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

    # -----------------------------------------------------------------
    # Import the resulting layer in GRASS GIS
    # -----------------------------------------------------------------
    gs.info(_("Importing the predicted suitability layer in grass gis\n"))
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
