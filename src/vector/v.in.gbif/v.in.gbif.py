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
import grass.script as gs

import csv


def process_csv(
    gbifraw, new_gbif_csv, primary_encoding=None, fallback_encoding="utf-8"
):
    """
    Process a CSV file using a primary encoding and fallback to another if the first fails.
    Substitutes problematic characters during the second fallback.

    :param gbifraw: Path to the input CSV file.
    :param new_gbif_csv: Path to the output CSV file.
    :param primary_encoding: Primary encoding to try first. If None, uses system default.
    :param fallback_encoding: Fallback encoding to use if the primary fails.
    """

    def process_file(input_encoding, handle_errors=False):
        """
        Process the file with the specified encoding.
        If `handle_errors` is True, substitutes problematic characters.
        """
        error_mode = "replace" if handle_errors else "strict"
        gs.message(
            _(
                "Trying to process file using encoding: {} (errors={})".format(
                    input_encoding, error_mode
                )
            )
        )
        with open(
            gbifraw, "r", encoding=input_encoding, errors=error_mode
        ) as csvinfile:
            gbifreader = csv.reader(csvinfile, delimiter="\t")
            with open(new_gbif_csv, "w", newline="", encoding="utf-8") as csvoutfile:
                gbifwriter = csv.writer(
                    csvoutfile, quotechar='"', quoting=csv.QUOTE_ALL
                )
                for row in gbifreader:
                    gbifwriter.writerow(row)
        gs.message(
            _("File processed successfully using encoding: {}".format(input_encoding))
        )

    try:
        process_file(primary_encoding)
    except UnicodeDecodeError as e:
        gs.warning(
            _("Warming: Unable to decode the file with system default encoding.")
        )
        gs.warning(_("Details: {}".format(e)))
        gs.warning(_("Falling back to encoding: {}".format(fallback_encoding)))

        try:
            process_file(fallback_encoding, handle_errors=True)
        except UnicodeDecodeError as e:
            gs.warning(
                _(
                    "Error: Unable to decode the file even with fallback encoding {}".format(
                        fallback_encoding
                    )
                )
            )
            gs.fatal(_("Details: {}".format(e)))
        except Exception as e:
            gs.fatal(
                _(
                    "An unexpected error occurred during fallback processing: {}".format(
                        e
                    )
                )
            )
    except FileNotFoundError as e:
        gs.fatal(_("Error: File not found - {}".format(e.filename)))
    except Exception as e:
        gs.fatal(_("An unexpected error occurred: {}".format(e)))


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
    in_proj = gs.parse_command("g.proj", flags="g")

    if in_proj["name"].lower() == "xy_location_unprojected":
        gs.fatal(_("xy-locations are not supported"))

    # import GBIF data
    gs.message("Starting importing GBIF data ...")
    gs.message("preparing data for vrt ...")

    # new quoted GBIF csv file
    gbiftempdir = tempfile.gettempdir()
    new_gbif_csv = os.path.join(gbiftempdir, gbifcsv)

    # quote raw data
    process_csv(gbifraw, new_gbif_csv, primary_encoding=None, fallback_encoding="utf-8")

    # write vrt
    gs.message("writing vrt ...")
    new_gbif_vrt = os.path.join(gbiftempdir, gbifvrt)

    f = open(f"{new_gbif_vrt}", "wt")
    f.write(
        """<OGRVRTDataSource>
    <OGRVRTLayer name="%s">
        <SrcDataSource relativeToVRT="1">%s</SrcDataSource>
        <GeometryType>wkbPoint</GeometryType>
        <LayerSRS>WGS84</LayerSRS>
                <Field name="g_gbifid" src="gbifid" type="Integer64" />
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

    gs.message("----")
    # Give information where output file are saved
    gs.message("GBIF vrt files:")
    gs.message(gbifvrt)
    gs.message("-")
    gs.message(gbifcsv)
    gs.message("----")

    # import GBIF vrt
    gs.message("importing GBIF vrt ...")

    # reprojection-on-the-fly if flag r

    if reproject_gbif:

        gs.message("reprojecting data on-the-fly ...")
        gs.run_command("v.import", input=new_gbif_vrt, output=gbifimported, quiet=True)

        # no reprojection-on-the-fly

    else:

        gs.run_command(
            "v.in.ogr",
            input=new_gbif_vrt,
            layer=gbif_vrt_layer,
            output=gbifimported,
            quiet=True,
        )

    gs.message("...")
    # v.in.gbif done!
    gs.message("importing GBIF data done!")
    # move vrt and csv to user defined directory

    if move_vrt_gbif_to_dir:

        gs.message("----")
        gs.message("Create GBIF vrt data files ...")
        shutil.move(new_gbif_vrt, directory)
        shutil.move(new_gbif_csv, directory)
        gs.message("in following user defined directory:")
        gs.message(directory)
        gs.message("----")

    else:

        gs.message("----")
        gs.message("Some clean up ...")
        os.remove("%s" % new_gbif_vrt)
        os.remove("%s" % new_gbif_csv)
        gs.message("Clean up done.")
        gs.message("----")


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
