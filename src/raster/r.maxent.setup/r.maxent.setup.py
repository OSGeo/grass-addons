#!/usr/bin/env python

############################################################################
#
# MODULE:       r.maxent.setup
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Helper function. Let the user copy the Maxent software
#               (https://biodiversityinformatics.amnh.org/open_source/maxent/),
#               to the addon folder, and offer the option to users to
#               set the path to the java executable.
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
# % description: Helper module to install Maxent to the addon directory
# % keyword: modeling
# % keyword: Maxent
# %end

# %option G_OPT_F_BIN_INPUT
# % key: maxent
# % label: Location Maxent jar file
# % description: Give the path to the Maxent executable file (maxent.jar)
# % required: no
# % guisection: Input
# %end

# %option G_OPT_F_BIN_INPUT
# % key: java
# % label: Location Jave executable
# % description: Give the path to the Java executable file.
# % required: no
# % guisection: Input
# %end

# %flag
# % key: j
# % label: Check if Java can be found on the system
# % description: Check if Java can be found from the GRASS GIS command line.
# %end

# %flag
# % key: u
# % label: Overwrites maxent.jar in addon directory
# % description: If the Maxent executable already exists in the addon directory, it will be overwritten.
# %end

# %rules
# % excludes: -j, maxent, java, -u
# %end

# %rules
# % required: -j, maxent, java
# %end

# import libraries
# ------------------------------------------------------------------
import subprocess
import os
import shutil
import sys
import grass.script as gs


# Functions
# -------------------------------------------------------------------
def install_maxent(maxent, overwrite):
    """Copy Maxent.jar to the addon directory. First there will be a check
    if the provided path is correct. Next, there will be a check if the file
    exists in the destination directory.

    :param str maxent: path to the maxent.jar file, including the file name
    :flag str overwrite: Set option to overwrite an existing Maxent.jar file

    :return str: status or error message.
    """

    # Check if provided path+file exists
    if not os.path.isfile(maxent):
        msg = "The maxent.jar file was not found on the location you provided"
        gs.fatal(_(msg))

    # Check if the file has the right name (maxent.jar)
    file_name = os.path.basename(os.path.basename(maxent))
    maxent_path = os.environ.get("GRASS_ADDON_BASE")
    maxent_copy = os.path.join(maxent_path, "scripts", "maxent.jar")
    if file_name != "maxent.jar":
        gs.fatal(
            _(
                "The name of the maxent program should be 'maxent.jar',"
                " not '{}'".format(file_name)
            )
        )

    # Check file exists in addon directory
    maxent_file = os.environ.get("GRASS_ADDON_BASE")
    maxent_file = os.path.join(maxent_file, "scripts", "maxent.jar")
    maxent_copy = os.path.isfile(maxent_file)

    # If overwrite is set, copy maxent overwriting the existing file
    if maxent_copy and bool(overwrite):
        shutil.copyfile(maxent, maxent_file)
        msg = (
            "Replaced the maxent.jar file in the grass gis addon script directory.\n"
            f"path: {maxent_file}.\n"
        )
        gs.info(_(msg))
    elif not os.path.isfile(maxent_file):
        shutil.copyfile(maxent, maxent_file)
        msg = (
            "Copied the maxent.jar file to the grass gis addon script directory.\n"
            f"path: {maxent_file}.\n"
        )
        gs.info(_(msg))
    else:
        msg = (
            "There is already a maxent.jar file in the scripts \n"
            "directory. Use the -u flag if you want to update \n"
            f"the file {maxent_file}."
        )
        gs.fatal(_(msg))


def set_path_to_java(java, overwrite):
    """Create a text file with path to java executables in the addon
    directory

    :param str java: path to the java executable file, including the file name
    :flag str overwrite: Set option to overwrite an existing the text file

    :return str: status or error message and path to text file
    """

    # Check if provided path+file exists
    if not os.path.isfile(java):
        msg = "The java executable was not found on the location you provided"
        gs.fatal(_(msg))

    # Check text file exists in addon directory
    addon_directory = os.environ.get("GRASS_ADDON_BASE")
    txt_java_path = os.path.join(
        addon_directory, "scripts", "r_maxent_path_to_java.txt"
    )
    java_txt_copy = os.path.isfile(txt_java_path)

    # If overwrite is set, copy maxent overwriting the existing file
    if java_txt_copy and bool(overwrite):
        with open(txt_java_path, "w") as file:
            file.write(java)
        msg = (
            "Text file created:\n"
            "{}\n"
            "with path to java executable:\n"
            "{}".format(txt_java_path, java)
        )
        gs.info(_(msg))
    elif not os.path.isfile(java_txt_copy):
        with open(txt_java_path, "w") as file:
            file.write(java)
        msg = (
            "Text file created:\n"
            "{}\n"
            "with path to java executable:\n"
            "{}".format(txt_java_path, java)
        )
        gs.info(_(msg))
    else:
        msg = (
            "The text file with the path to the java executable \n"
            "already exists in the adadon directory. Use the -u \n"
            "flag if you want to update the file"
        )
        gs.fatal(_(msg))


def java_findable():
    """
    Check if Java can be found by running the 'java -version' command.

    Returns:
        bool: True if Java is findable, False otherwise.
    """
    try:
        # Run 'java -version' and suppress its output
        subprocess.run(
            ["java", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# Main
# ------------------------------------------------------------------
def main(options, flags):

    # Check if Java can be found
    if flags["j"]:
        if not java_findable():
            gs.warning(
                _(
                    "Java cannot be found from GRASS GIS. Please ensure Java "
                    "is installed and/or properly configured. If you are sure "
                    "Java is installed, you can use this module to define the "
                    "path to the java executable. See the help file for details."
                )
            )
        else:
            gs.message(_("Java is accessible from GRASS GIS."))

    # Set path to java executable
    if bool(options["java"]):
        set_path_to_java(java=os.path.normpath(options["java"]), overwrite=flags["u"])
    else:
        if not java_findable():
            gs.message(
                _(
                    "Java is not installed or not accessible via the system PATH. "
                    "Please ensure Java is installed and/or properly configured."
                    "If you are sure Java is installed, you can use this module"
                    "to define the path to the java executable. See the help file"
                    "for details."
                )
            )

    # Install maxent
    if bool(options["maxent"]):
        install_maxent(maxent=os.path.normpath(options["maxent"]), overwrite=flags["u"])


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
