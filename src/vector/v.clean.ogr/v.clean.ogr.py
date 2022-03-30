#!/usr/bin/env python
############################################################################
#
# MODULE:       v.clean.ogr
# AUTHOR(S):    Markus Metz
# PURPOSE:      Import, clean, and export an OGR layer
# COPYRIGHT:    (C) 2018 by the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % description: Imports vector data into a GRASS vector map, cleans the data topologically, and exports them again using OGR library.
# % keyword: vector
# % keyword: cleaning
# % keyword: OGR
# % keyword: topology
# % keyword: geometry
# % keyword: snapping
# %end

# input options

# %option
# % key: input
# % type: string
# % required: yes
# % multiple: no
# % label: Name of OGR datasource to be imported
# % description: Example: directory containing shapefiles
# % gisprompt: old,datasource,datasource
# % guisection: Input
# %end
# %option
# % key: layer
# % type: string
# % required: yes
# % multiple: no
# % label: OGR layer name.
# % description: Examples: shapefile name without .shp
# % gisprompt: old,datasource_layer,datasource_layer
# % guisection: Input
# %end
# %option
# % key: where
# % type: string
# % required: no
# % multiple: no
# % key_desc: sql_query
# % label: WHERE conditions of SQL statement without 'where' keyword
# % description: Example: income < 1000 and population >= 10000
# % gisprompt: old,sql_query,sql_query
# % guisection: Selection
# %end
# %option
# % key: encoding
# % type: string
# % required: no
# % multiple: no
# % label: Encoding value for attribute data
# % description: Overrides encoding interpretation, useful when importing ESRI Shapefile
# % guisection: Attributes
# %end
# %option
# % key: key
# % type: string
# % required: no
# % multiple: no
# % label: Name of column used for categories
# % description: If not given, categories are generated as unique values and stored in 'cat' column
# % guisection: Attributes
# %end
# %option
# % key: geometry
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % label: Name of geometry column
# % description: If not given, all geometry columns from the input are used
# % gisprompt: old,dbcolumn,dbcolumn
# % guisection: Selection
# %end
# %flag
# % key: l
# % suppress_required: yes
# % description: List available OGR layers in data source and exit
# % guisection: Input
# %end

# cleaning options

# %option
# % key: snap
# % type: double
# % required: no
# % multiple: no
# % label: Snapping threshold for boundaries (map units)
# % description: '-1' for no snap
# % answer: -1
# % guisection: Cleaning
# %end
# %option
# % key: min_area
# % type: double
# % required: no
# % multiple: no
# % label: Minimum size of areas to be retained in output (square meters)
# % description: Disabled with values <= 0
# % answer: 0
# % guisection: Cleaning
# %end

# output options

# %option
# % key: output
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % label: Name of output OGR datasource
# % description: Examples: filename for a GeoPackage, directory for shapefiles
# % gisprompt: new,file,file
# % guisection: Output
# %end
# %option
# % key: format
# % type: string
# % required: yes
# % multiple: no
# % description: Data format to write
# % answer: GPKG
# % guisection: Output
# %end
# %flag
# % key: u
# % description: Open an existing output OGR datasource for update
# % guisection: Output
# %end
# %flag
# % key: f
# % suppress_required: yes
# % description: List supported output formats and exit
# % guisection: Output
# %end

import sys
import os
import atexit

import grass.script as grass
from grass.exceptions import CalledModuleError

# initialize global vars
TMPLOC = None
SRCGISRC = None
GISDBASE = None


def cleanup():
    # remove temp location
    if TMPLOC:
        grass.try_rmdir(os.path.join(GISDBASE, TMPLOC))
    if SRCGISRC:
        grass.try_remove(SRCGISRC)


def main():
    indsn = options["input"]
    inlayer = options["layer"]
    inwhere = options["where"]
    inenc = options["encoding"]
    inkey = options["key"]
    ingeom = options["geometry"]
    listlayers = flags["l"]

    min_area = options["min_area"]

    outdsn = options["output"]
    outformat = options["format"]
    outclean = "%s_clean" % inlayer
    outoverlaps = "%s_overlaps" % inlayer

    overwrite = grass.overwrite()

    # list input layers
    if flags["l"]:
        try:
            grass.run_command("v.in.ogr", input=indsn, flags="l")
        except CalledModuleError:
            grass.fatal(_("Unable to list layers in OGR datasource <%s>") % indsn)
        return 0

    # list output formats
    if flags["f"]:
        grass.run_command("v.out.ogr", flags="l")
        return 0

    # import options
    vopts = {}
    if options["encoding"]:
        vopts["encoding"] = options["encoding"]
    if options["where"]:
        vopts["where"] = options["where"]
    if options["geometry"]:
        vopts["geometry"] = options["geometry"]
    if options["key"]:
        vopts["key"] = options["key"]
    if options["snap"]:
        vopts["snap"] = options["snap"]

    # create temp location from input without import
    grassenv = grass.gisenv()
    tgtloc = grassenv["LOCATION_NAME"]
    tgtmapset = grassenv["MAPSET"]
    GISDBASE = grassenv["GISDBASE"]
    tgtgisrc = os.environ["GISRC"]
    SRCGISRC = grass.tempfile()

    TMPLOC = "temp_import_location_" + str(os.getpid())

    f = open(SRCGISRC, "w")
    f.write("MAPSET: PERMANENT\n")
    f.write("GISDBASE: %s\n" % GISDBASE)
    f.write("LOCATION_NAME: %s\n" % TMPLOC)
    f.write("GUI: text\n")
    f.close()

    grass.verbose(_("Creating temporary location for <%s>...") % indsn)
    try:
        grass.run_command(
            "v.in.ogr",
            input=indsn,
            location=TMPLOC,
            flags="i",
            quiet=True,
            overwrite=overwrite,
            **vopts,
        )
    except CalledModuleError:
        grass.fatal(_("Unable to create location from OGR datasource <%s>") % indsn)

    # switch to temp location
    os.environ["GISRC"] = str(SRCGISRC)

    outvect = "vector_clean"
    outvect_tmp = "vector_clean"
    if float(min_area) > 0:
        outvect_tmp = "vector_clean_import"

    # import into temp location
    grass.message(_("Importing <%s>, layer <%s> ...") % (indsn, inlayer))
    try:
        grass.run_command(
            "v.in.ogr",
            input=indsn,
            layer=inlayer,
            output=outvect_tmp,
            overwrite=overwrite,
            **vopts,
        )
    except CalledModuleError:
        grass.fatal(_("Unable to import OGR datasource <%s>") % indsn)

    # remove small areas
    if float(min_area) > 0:
        grass.message(
            _("Removing small areas in data source <%s>, layer <%s> ...")
            % (indsn, inlayer)
        )
        try:
            grass.run_command(
                "v.clean",
                input=outvect_tmp,
                output=outvect,
                type="area",
                tool="rmarea",
                threshold=min_area,
                overwrite=overwrite,
            )
        except CalledModuleError:
            grass.fatal(
                _("Removing small areas in data source <%s>, layer <%s> failed")
                % (indsn, inlayer)
            )

    # export
    oflags = "sm"
    if flags["u"]:
        oflags = "smu"
        overwrite = True

    outlayer = "%s_clean" % inlayer
    grass.message = _("Exporting cleaned layer as <%s>") % outlayer
    try:
        grass.run_command(
            "v.out.ogr",
            input=outvect,
            layer="1",
            output=outdsn,
            output_layer=outlayer,
            format=outformat,
            flags=oflags,
            overwrite=overwrite,
        )
    except CalledModuleError:
        grass.fatal(_("Unable to export to OGR datasource <%s>") % outdsn)

    # export any overlaps
    outlayers = grass.read_command("v.category", input=outvect, option="layers")

    nlayers = len(outlayers.splitlines())
    # for layer in outlayers.splitlines():
    #    nlayers += 1

    if nlayers == 2:
        outlayer = "%s_overlaps" % inlayer
        oflags = "smu"
        grass.message = _("Exporting overlaps as <%s>") % outlayer
        try:
            grass.run_command(
                "v.out.ogr",
                input=outvect,
                layer="2",
                output=outdsn,
                output_layer=outlayer,
                format=outformat,
                flags=oflags,
                overwrite=True,
            )
        except CalledModuleError:
            grass.fatal(_("Unable to export to OGR datasource <%s>") % outdsn)

    # switch to target location
    os.environ["GISRC"] = str(tgtgisrc)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
