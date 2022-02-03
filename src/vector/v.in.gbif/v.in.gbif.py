#!/usr/bin/env python

"""
MODULE:    v.in.gbif

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Imports GBIF species distribution data by saving original data to
           a GDAL VRT and importing the VRT by v.in.ogr

COPYRIGHT: (C) 2015 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: importing of GBIF species distribution data
# % keyword: vector
# % keyword: geometry
# %end

# %option G_OPT_F_INPUT
# % key: input
# % required: yes
# %end

# %option G_OPT_V_OUTPUT
# % key: output
# % description: name of imported GBIF data set
# % required : yes
# %end

# %flag
# % key: c
# % description: Create GDAL VRT data set of GBIF data
# % guisection: vrt
# %end

# %option G_OPT_M_DIR
# % key: dir
# % description: Directory where the output will be found
# % required : no
# % guisection: vrt
# %end

# %flag
# % key: r
# % description: Reproject data on-the-fly if no latlon (WGS84) location
# %end

import sys
import os
import csv
import math
import shutil
import tempfile
import grass.script as grass


def main():

    gbifraw = options["input"]
    gbifimported = options["output"]
    directory = options["dir"]
    move_vrt_gbif_to_dir = flags["c"]
    gbifvrt = gbifimported + ".vrt"
    gbif_vrt_layer = gbifimported
    gbifcsv = gbifimported + ".csv"
    reproject_gbif = flags["r"]
    global tmp

    # check for unsupported locations or unsupported combination of option and projected location
    in_proj = grass.parse_command("g.proj", flags="g")

    if in_proj["name"].lower() == "xy_location_unprojected":
        grass.fatal(_("xy-locations are not supported"))

    # import GBIF data
    grass.message("Starting importing GBIF data ...")
    grass.message("preparing data for vrt ...")

    # new quoted GBIF csv file
    gbiftempdir = tempfile.gettempdir()
    new_gbif_csv = os.path.join(gbiftempdir, gbifcsv)

    # quote raw data
    with open("%s" % (gbifraw), "rb") as csvinfile:
        gbifreader = csv.reader(csvinfile, delimiter="\t")
        with open("%s" % (new_gbif_csv), "wb") as csvoutfile:
            gbifwriter = csv.writer(csvoutfile, quotechar='"', quoting=csv.QUOTE_ALL)
            for row in gbifreader:
                gbifwriter.writerow(row)
    grass.message("----")

    # write        vrt
    grass.message("writing vrt ...")
    new_gbif_vrt = os.path.join(gbiftempdir, gbifvrt)

    f = open("%s" % (new_gbif_vrt), "wt")
    f.write(
        """<OGRVRTDataSource>
    <OGRVRTLayer name="%s">
        <SrcDataSource relativeToVRT="1">%s</SrcDataSource>
        <GeometryType>wkbPoint</GeometryType>
        <LayerSRS>WGS84</LayerSRS>
                <Field name="g_gbifid" src="gbifid" type="Integer" />
                <Field name="g_datasetkey" src="datasetkey" type="String" width="255" />
                <Field name="g_occurrenceid" src="occurrenceid" type="String" width="255" />
                <Field name="g_kingdom" src="kingdom" type="String" width="50" />
                <Field name="g_phylum" src="phylum" type="String" width="50" />
                <Field name="g_class" src="class" type="String" width="50" />
                <Field name="g_order" src="order" type="String" width="50" />
                <Field name="g_family" src="family" type="String" width="100" />
                <Field name="g_genus" src="genus" type="String" width="255" />
                <Field name="g_species" src="species" type="String" width="255" />
                <Field name="g_infraspecificepithet" src="infraspecificepithet" type="String" width="100" />
                <Field name="g_taxonrank" src="taxonrank" type="String" width="50" />
                <Field name="g_scientificname" src="scientificname" type="String" width="255" />
                <Field name="g_countrycode" src="countrycode" type="String" width="25" />
                <Field name="g_locality" src="locality" type="String" width="255" />
                <Field name="g_publishingorgkey" src="publishingorgkey" type="String" width="255" />
                <Field name="g_decimallatitude" src="decimallatitude" type="Real" />
                <Field name="g_decimallongitude" src="decimallongitude" type="Real" />
                <Field name="g_elevation" src="elevation" type="Real" />
                <Field name="g_elevationaccuracy" src="elevationaccuracy" type="String" width="50" />
                <Field name="g_depth" src="depth" type="String" width="255" />
                <Field name="g_depthaccuracy" src="depthaccuracy" type="String" width="255" />
                <Field name="g_eventdate" src="eventdate" type="String" width="255" />
                <Field name="g_day" src="day" type="Integer" width="255" />
                <Field name="g_month" src="month" type="Integer" width="255" />
                <Field name="g_year" src="year" type="Integer" width="255" />
                <Field name="g_taxonkey" src="taxonkey" type="String" width="100" />
                <Field name="g_specieskey" src="specieskey" type="String" width="100" />
                <Field name="g_basisofrecord" src="basisofrecord" type="String" width="100" />
                <Field name="g_institutioncode" src="institutioncode" type="String" width="100" />
                <Field name="g_collectioncode" src="collectioncode" type="String" width="100" />
                <Field name="g_catalognumber" src="catalognumber" type="String" width="255" />
                <Field name="g_recordnumber" src="recordnumber" type="String" width="255" />
                <Field name="g_identifiedby" src="identifiedby" type="String" width="255" />
                <Field name="g_license" src="license" type="String" width="255" />
                <Field name="g_rightsholder" src="rightsholder" type="String" width="255" />
                <Field name="g_recordedby" src="recordedby" type="String" width="255" />
                <Field name="g_typestatus" src="typestatus" type="String" width="255" />
                <Field name="g_establishmentmeans" src="establishmentmeans" type="String" width="255" />
                <Field name="g_lastinterpreted" src="lastinterpreted" type="String" width="255" />
                <Field name="g_mediatype" src="mediatype" type="String" width="100" />
                <Field name="g_issue" src="issue" type="String" width="255" />
                <GeometryField encoding="PointFromColumns" x="decimallongitude" y="decimallatitude"/>
        </OGRVRTLayer>
        </OGRVRTDataSource>"""
        % (gbif_vrt_layer, gbifcsv)
    )

    f.close()

    grass.message("----")
    # Give information where output file are saved
    grass.message("GBIF vrt files:")
    grass.message(gbifvrt)
    grass.message("-")
    grass.message(gbifcsv)
    grass.message("----")

    # import GBIF vrt
    grass.message("importing GBIF vrt ...")

    # reprojection-on-the-fly if flag r

    if reproject_gbif:

        grass.message("reprojecting data on-the-fly ...")
        grass.run_command(
            "v.import", input=new_gbif_vrt, output=gbifimported, quiet=True
        )

        # no reprojection-on-the-fly

    else:

        grass.run_command(
            "v.in.ogr",
            input=new_gbif_vrt,
            layer=gbif_vrt_layer,
            output=gbifimported,
            quiet=True,
        )

    grass.message("...")
    # v.in.gbif done!
    grass.message("importing GBIF data done!")
    # move vrt and csv to user defined directory

    if move_vrt_gbif_to_dir:

        grass.message("----")
        grass.message("Create GBIF vrt data files ...")
        shutil.move(new_gbif_vrt, directory)
        shutil.move(new_gbif_csv, directory)
        grass.message("in following user defined directory:")
        grass.message(directory)
        grass.message("----")

    else:

        grass.message("----")
        grass.message("Some clean up ...")
        os.remove("%s" % new_gbif_vrt)
        os.remove("%s" % new_gbif_csv)
        grass.message("Clean up done.")
        grass.message("----")


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
