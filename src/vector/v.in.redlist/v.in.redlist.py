#!/usr/bin/env python

"""
MODULE:    v.in.redlist

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Imports IUCN Red List Spatial Data

COPYRIGHT: (C) 2015 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: importing of IUCN Red List Spatial Data
# % keyword: vector
# % keyword: geometry
# %end

# %option G_OPT_F_BIN_INPUT
# % key: input
# % description: name of the IUCN Red List Spatial Data shapefile
# % required : yes
# % guisection: GIS data
# %end

# %option G_OPT_V_OUTPUT
# % key: output
# % description: name of the imported IUCN Red List Spatial Data
# % required : no
# % guisection: GIS data
# %end

# %option
# % key: species_name
# % description: name of species which should be imported
# % required : no
# % guisection: GIS data
# %end

# %flag
# % key: l
# % description: list species in IUCN Red List Spatial Data
# % guisection: listing
# %end

# %flag
# % key: s
# % description: save species list to a text file
# % guisection: listing
# %end

# %option G_OPT_M_DIR
# % key: dir
# % description: Directory where the species list will be found
# % required : no
# % guisection: listing
# %end

import sys
import os
import grass.script as grass


def main():
    try:
        from osgeo import ogr
    except ImportError:
        grass.fatal(
            _(
                "Unable to load GDAL Python bindings (requires "
                "package 'python-gdal' or Python library GDAL "
                "to be installed)."
            )
        )

    redlist_shapefile_long = options["input"]
    imported_species = options["species_name"]
    species_to_import = options["output"]
    imported_species_quoted = "'" + imported_species + "'"
    directory = options["dir"]
    list_species = flags["l"]
    save_species = flags["s"]
    redlist_shapefile_short = os.path.basename(redlist_shapefile_long)
    species_filename = redlist_shapefile_short.split(".")[0]
    species_file = species_filename + ".txt"
    global tmp

    # save species list to a user defined directory

    if save_species:

        grass.message("saving species list to a text file ...")
        output_species_file = os.path.join(directory, species_file)
        # define ogr driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # open data source
        dataSource = driver.Open(redlist_shapefile_long, 0)
        # get layer
        layer = dataSource.GetLayer()
        # open export file
        f = open("%s" % (output_species_file), "w")
        # write content of the attribute table column binomial
        for feature in layer:
            f.write("%s\n" % (feature.GetField("binomial")))
        f.close()
        grass.message("%s" % (output_species_file))

    # print species list of the shapefile

    elif list_species:

        grass.message("list species IUCN Red List Spatial Data ...")
        # define ogr driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # open data source
        dataSource = driver.Open(redlist_shapefile_long, 0)
        # get layer
        layer = dataSource.GetLayer()
        for feature in layer:
            grass.message("%s" % (feature.GetField("binomial")))

    # import spatial data for a user defined species in the Red List

    else:

        grass.message(" importing spatial data for %s ..." % (imported_species_quoted))
        grass.run_command(
            "v.in.ogr",
            input=redlist_shapefile_long,
            output=species_to_import,
            where="binomial = %s" % (imported_species_quoted),
            quiet=True,
        )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
