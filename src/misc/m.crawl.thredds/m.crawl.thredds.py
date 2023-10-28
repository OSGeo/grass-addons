#!/usr/bin/env python
"""
MODULE:       m.crawl.thredds
AUTHOR(S):    stefan.blumentrath
PURPOSE:      List dataset urls from a thredds server (TDS)
COPYRIGHT:    (C) 2021-2023 by Stefan Blumentrath, and the GRASS Development Team

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
"""

# %module
# % description: List dataset urls from a Thredds Data Server (TDS) catalog.
# % keyword: temporal
# % keyword: import
# % keyword: download
# % keyword: data
# % keyword: metadata
# % keyword: netcdf
# % keyword: thredds
# % keyword: opendap
# %end

# %option
# % key: input
# % description: URL of a catalog on a thredds server
# % type: string
# % required: yes
# % multiple: no
# %end

# %option
# % key: print
# % description: Additional information to print
# % options: service,dataset_size
# % type: string
# % required: no
# % multiple: yes
# %end

# %option
# % key: services
# % label: Services of thredds server to crawl
# % description: Comma separated list of services names (lower case) of thredds server to crawl, typical services are: httpserver, netcdfsubset, opendap, wms
# % type: string
# % required: yes
# % multiple: yes
# % answer: httpserver
# %end

# %option
# % key: filter
# % description: Regular expression for filtering dataset and catalog URLs
# % type: string
# % required: no
# % multiple: no
# % answer: .*
# %end

# %option
# % key: skip
# % description: Regular expression(s) for skipping sub-catalogs / URLs (e.g. ".*jpeg.*,.*metadata.*)"
# % type: string
# % required: no
# % multiple: yes
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# % multiple: no
# % description: Name of the output file (stdout if omitted)
# % answer: -
# %end

# %option G_OPT_F_SEP
# % required: no
# % multiple: no
# %end

# %option
# % key: modified_before
# % label: Latest modification timestamp of datasets to include in the output
# % description: ISO-formated date or timestamp (e.g. "2000-01-01T12:12:55.03456Z" or "2000-01-01")
# % type: string
# % required: no
# % multiple: no
# %end

# %option
# % key: modified_after
# % label: Earliest modification timestamp of datasets to include in the output
# % description: ISO-formated date or timestamp (e.g. "2000-01-01T12:12:55.03456Z" or "2000-01-01")
# % type: string
# % required: no
# % multiple: no
# %end

# %option G_OPT_F_INPUT
# % key: authentication
# % required: no
# % multiple: no
# % description: File with authentication information (username and password) for thredds server
# % label: Authentication for thredds server
# %end

# Simplify the following with: G_OPT_M_NPROCS
# %option
# % key: nprocs
# % type: integer
# % required: no
# % multiple: no
# % key_desc: Number of cores
# % label: Number of cores to use for crawling thredds server
# % answer: 1
# %end

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import grass.script as gscript


def get_authentication(authentication_input):
    """Get authentication from input or environment"""
    thredds_authentication = None
    # Try to get authentication from environment variables
    if (
        os.environ.get("THREDDS_USER") is not None
        and os.environ.get("THREDDS_PASSWORD") is not None
    ):
        thredds_authentication = (
            os.environ.get("THREDDS_USER"),
            os.environ.get("THREDDS_PASSWORD"),
        )

    if authentication_input is not None and authentication_input != "":
        if authentication_input == "-":
            # stdin
            import getpass

            user = input(_("Insert username: "))
            password = getpass.getpass(_("Insert password: "))
            thredds_authentication = (user, password)
        elif os.access(authentication_input, os.R_OK):
            with open(authentication_input, "r", encoding="UTF8") as auth_file:
                thredds_authentication = tuple(auth_file.read().split(os.linesep)[0:2])
        else:
            gscript.fatal(
                _("Unable to open file <{}> for reading.").format(authentication_input)
            )
    return thredds_authentication


def parse_isotime(options_dict, time_key):
    """Parse user provided timestamp string into datetime object"""
    timestamp = None
    if options_dict[time_key] is not None and options_dict[time_key] != "":
        time_string = options_dict[time_key].replace("Z", "+0000")
        time_format = "%Y-%m-%d"
        if "T" in time_string:
            time_format += "T%H:%M:%S"
        if "." in time_string:
            time_format += ".%f"
        if re.match(r".*(\+|\-)[0-9][0-9][0-9][0-9]$", time_string) is None:
            time_string += "+0000"
        time_format += "%z"
        try:
            timestamp = datetime.strptime(time_string, time_format)
        except ValueError:
            gscript.fatal(
                _("Unable to parse {option} timestamp <{time_str}>.").format(
                    option=time_key, time_str=options_dict[time_key]
                )
            )
    return timestamp


def main():
    """Do the main work"""

    # lazy import thredds_crawler
    try:
        from thredds_crawler.crawl import Crawl
    except ImportError:
        gscript.fatal(
            _(
                "Unable to import Python library: thredds_crawler.\n"
                "Please make sure it is installed (pip install thredds_crawler).",
            )
        )

    # Parse and check the input options and flags

    separator_dict = {
        "pipe": "|",
        "space": " ",
        "comma": ",",
        "tab": "\t",
        "newline": os.linesep,
    }

    options["separator"] = (
        separator_dict[options["separator"]]
        if options["separator"] in separator_dict
        else options["separator"]
    )

    # Convert before and after timestamps to datetime objects
    for timestamp in ["modified_after", "modified_before"]:
        options[timestamp] = parse_isotime(options, timestamp)

    # Check if before and after is set meaningfully
    if options["modified_before"] is not None and options["modified_after"] is not None:
        if options["modified_before"] < options["modified_after"]:
            gscript.fatal(
                _(
                    "Date for modified_after needs to be before date for modified_before."
                )
            )

    # Parse list of requested services
    options["services"] = set(options["services"].split(","))

    # Get authentication if provided
    authentication = get_authentication(options["authentication"])

    # Check if output file can be written
    if options["output"] and options["output"] != "-":
        output = Path(options["output"])
        if output.exists():
            if not output.is_file():
                gscript.fatal(
                    _("Cannot write to <{}>. It exists and is not a file.").format(
                        options["output"]
                    )
                )

            if not gscript.overwrite():
                gscript.fatal(
                    _("File <{}> already exists. Use --o to overwrite.").format(
                        options["output"]
                    )
                )
        else:
            try:
                output.write_text("", encoding="UTF8")
                output.unlink()
            except OSError:
                gscript.fatal(
                    _("Unable to write to file <{}>.").format(options["output"])
                )
    else:
        output = None

    # Parse list of regular expressions for skipping parts of the catalog
    if options["skip"]:
        options["skip"] = Crawl.SKIPS + options["skip"].split(",")

    # Get datasets from thredds server, traversing it recursively
    try:
        catalog = Crawl(
            options["input"],
            before=options["modified_before"],
            after=options["modified_after"],
            select=[options["filter"]],
            skip=options["skip"],
            workers=int(options["nprocs"]),
            auth=authentication,
        )
    except ValueError:
        gscript.fatal(
            _(
                "Unable to crawl <{url}> with the given input.\n"
                "Please check provided options."
            ).format(url=options["input"])
        )

    if len(catalog.datasets) == 0:
        gscript.warning(
            _(
                "No datasets returned from server <{url}> with the given input.\n"
                "Please check provided options."
            ).format(url=options["input"])
        )
        dataset_urls = [
            options["separator"]
            * ("service" in options["print"] + "data_size" in options["print"])
        ]
    else:
        # List services
        services = {
            service.get("service").lower()
            for dataset in catalog.datasets
            for service in dataset.services
        }

        # Check if ANY requested service is provided by the server
        if options["services"].isdisjoint(services):
            gscript.fatal(
                _(
                    "The thredds server does not offer the requested service(s) <{}>."
                ).format(",".join(options["services"]))
            )

        # Check if ALL requested services are provided by the server for at least one dataset
        for service in options["services"]:
            if service not in services:
                options["services"].remove(service)
                gscript.warning(
                    _(
                        "The thredds server does not offer the requested service <{}>."
                    ).format(service)
                )

        # Get dataset information as a list of strings
        dataset_urls = [
            "".join(
                [
                    service.get("service").lower() + options["separator"]
                    if "service" in options["print"]
                    else "",
                    service.get("url"),
                    options["separator"] + str(dataset.size)
                    if "data_size" in options["print"]
                    else "",
                ]
            )
            for dataset in catalog.datasets
            for service in dataset.services
            if service.get("service").lower() in options["services"]
        ]

    # Return resulting list of datasets
    if output:
        output.write_text("\n".join(dataset_urls) + "\n", encoding="UTF8")
    else:
        print("\n".join(dataset_urls) + "\n")


if __name__ == "__main__":
    # Parse options and flags
    options, flags = gscript.parser()
    sys.exit(main())
