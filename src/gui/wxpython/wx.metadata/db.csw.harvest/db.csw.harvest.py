#!/usr/bin/env python

"""
@module  db.csw.harvest
@brief   Module for creating metadata based on ISO for vector maps

(C) 2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@modified for GRASS GIS by Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
@originaly created by  "# Copyright (c) 2010 Tom Kralidis"



# simple process to harvest CSW catalogues via Harvest operations


"""

# %module
# % description: CSW database manager
# % keyword: csw
# % keyword: metadata
# % keyword: harvesting
# %end

# %option
# % key: source
# % label: uri source
# % description: uri to csw source
# % required : yes
# %end

# %option
# % key: destination
# % label: uri destination
# % description: uri to csw destination
# % required : yes
# %end

# %option
# % key: max
# % label: max records
# % description: uri to csw destination
# % type: integer
# %end

import sys
import os

from grass.script import core as grass
from grass.script.utils import set_path

set_path(modulename="wx.metadata", dirname="mdlib", path="..")

from mdlib import globalvar

# from __future__ import absolute_import
# from __future__ import print_function


def harvest(source, dst):
    maxrecords = options["max"]
    if options["max"] == 0 or None:
        maxrecords = 10
    stop = 0
    flag = 0

    src = CatalogueServiceWeb(source)
    dest = CatalogueServiceWeb(dst)

    while stop == 0:
        if flag == 0:  # first run, start from 0
            startposition = 0
        else:  # subsequent run, startposition is now paged
            startposition = src.results["nextrecord"]

        src.getrecords(esn="brief", startposition=startposition, maxrecords=maxrecords)

        print(src.results)

        if (
            src.results["nextrecord"] == 0
            or src.results["returned"] == 0
            or src.results["nextrecord"] > src.results["matches"]
        ):  # end the loop, exhausted all records
            stop = 1
            break

        # harvest each record to destination CSW
        for i in list(src.records):
            source = "%s?service=CSW&version=2.0.2&request=GetRecordById&id=%s" % (
                sys.argv[1],
                i,
            )
            dest.harvest(source=source, resourcetype="http://www.isotc211.org/2005/gmd")
            # print dest.request
            # print dest.response

        flag = 1


def _get_csw(catalog_url, timeout=10):
    """function to init owslib.csw.CatalogueServiceWeb"""
    # connect to the server
    try:
        catalog = CatalogueServiceWeb(catalog_url, timeout=timeout)
        return catalog
    except ExceptionReport as err:
        msg = "Error connecting to service: %s" % err
    except ValueError as err:
        msg = "Value Error: %s" % err
    except Exception as err:
        msg = "Unknown Error: %s" % err
    grass.error("CSW Connection error: %s" % msg)

    return False


def main():
    try:
        global CatalogueServiceWeb, ExceptionReport

        from owslib.csw import CatalogueServiceWeb
        from owslib.ows import ExceptionReport
    except ModuleNotFoundError as e:
        msg = e.msg
        grass.fatal(
            globalvar.MODULE_NOT_FOUND.format(
                lib=msg.split("'")[-2], url=globalvar.MODULE_URL
            )
        )

    if not _get_csw(options["source"]):
        return

    harvest(options["source"], options["destination"])


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
