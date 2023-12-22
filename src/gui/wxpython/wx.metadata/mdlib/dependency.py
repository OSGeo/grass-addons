#!/usr/bin/env python

############################################################################
#
# MODULE:       dependency
#
# AUTHOR(S):    Matej Krejci <matejkrejci gmail.com> (GSoC 2014),
#               Tomas Zigo <tomas.zigo slovanet.sk>
#
# PURPOSE:      Check wx.metadata py lib dependencies
#
# COPYRIGHT:    (C) 2020 by Matej Krejci, Tomas Zigo, and the
#               GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

import importlib
import subprocess
import sys


URL = "https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support"

MODULES = {
    "jinja2": {
        "check_version": False,
    },
    "lxml": {
        "check_version": False,
    },
    "owslib": {
        "check_version": True,
        "package": ["owslib.iso"],
        "method": [["MD_Metadata"]],
        "version": ">=0.9",
    },
    "pycsw": {
        "check_version": True,
        "package": ["pycsw.core"],
        "submodule": [["admin"]],
        "version": ">=2.0",
    },
    "pyexcel_ods3": {
        "check_version": False,
    },
    "pygments": {
        "check_version": False,
    },
    "reportlab": {
        "check_version": False,
    },
    "sqlalchemy": {
        "check_version": False,
    },
    "validators": {
        "check_version": False,
    },
}

INSTALLED_VERSION_MESSAGE = "Installed version of {} library is " "<{}>."
REQ_VERSION_MESSAGE = (
    "{name} {version} is required. " "check requirements on the manual page <{url}>."
)


def check_dependencies(module_name, check_version=False):
    """Check if py module is installed

    :param str module_name: py module name
    :param bool check_version: check py module version

    :return

    bool True: if py module is installed

    None: if py module is missing
    """

    module_cfg = MODULES[module_name]
    try:
        module = importlib.import_module(module_name)
        if module_cfg["check_version"]:
            message = "{inst_ver} {req_ver}".format(
                inst_ver=INSTALLED_VERSION_MESSAGE.format(
                    module_name,
                    module.__version__,
                ),
                req_ver=REQ_VERSION_MESSAGE.format(
                    name=module_name,
                    version=module_cfg["version"],
                    url=URL,
                ),
            )

            for index, package in enumerate(module_cfg["package"]):
                _package = importlib.import_module(package)

                if module_cfg.get("method"):
                    for method in module_cfg.get("method")[index]:
                        if not hasattr(_package, method):
                            sys.stderr.write(message)

                elif module_cfg.get("module"):
                    for module in module_cfg.get("module")[index]:
                        try:
                            importlib.import_module(module)
                        except ModuleNotFoundError:
                            sys.stderr.write(message)

        return True
    except ModuleNotFoundError:
        message = "{name} {text} <{url}>.\n".format(
            name=module_name,
            text="library is missing. Check requirements on the " "manual page",
            url=URL,
        )
        sys.stderr.write(message)


def check_osmsm_lib():
    """Check if osmsm JavaScript static map image OpenStreetMap generator
    is installed

    https://github.com/jperelli/osm-static-maps
    """
    lib = "osmsm"
    try:
        subprocess.call([lib], stdout=subprocess.PIPE)
    except OSError:
        message = "{name} JavaScript {text} <{url}>.\n".format(
            name=lib,
            text="library is missing. Check requirements on the manual page",
            url=URL,
        )
        sys.stderr.write(message)


def main():
    for module in MODULES:
        if check_dependencies(module_name=module):
            print("{name} is installed.".format(name=module))
    check_osmsm_lib()


if __name__ == "__main__":
    sys.exit(main())
