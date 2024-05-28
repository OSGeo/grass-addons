#!/usr/bin/env python3

############################################################################
#
# MODULE:      i.eodag
#
# AUTHOR(S):   Hamed Elgizery
# MENTOR(S):   Luca Delucchi, Veronica Andreo, Stefan Blumentrath
#
# PURPOSE:     Downloads imagery datasets e.g. Landsat, Sentinel, and MODIS
#              using EODAG API.
# COPYRIGHT:   (C) 2024-2025 by Hamed Elgizery, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################


# %Module
# % description: Eodag interface to install imagery datasets from various providers.
# % keyword: imagery
# % keyword: eodag
# % keyword: sentinel
# % keyword: landsat
# % keyword: modis
# % keyword: datasets
# % keyword: download
# %end

# %option
# % key: dataset
# % type: string
# % description: Imagery dataset to search for
# % required: yes
# % answer: S1_SAR_GRD
# % guisection: Filter
# %end

# %option G_OPT_M_DIR
# % key: output
# % description: Name for output directory where to store downloaded data OR search results
# % required: no
# % guisection: Output
# %end

# %option
# % key: id
# % type: string
# % multiple: yes
# % description: List of scenes IDs to download
# % guisection: Filter
# %end

# %option
# % key: provider
# % type: string
# % description: Provider to use for searching/downloading, if none is provided the searching will be done according to the config file priority
# % required: no
# % guisection: Filter
# %end

# %option
# % key: start
# % type: string
# % description: Start date (in any ISO 8601 format), by default it is 60 days ago
# % guisection: Filter
# %end

# %option
# % key: end
# % type: string
# % description: End date (in any ISO 8601 format)
# % guisection: Filter
# %end

# %option
# % key: relation
# % type: string
# % description: Relation with area of interest
# % options: intersects, contains, within
# % answer: intersects
# % guisection: Optional
# %end

# %option
# % key: clouds
# % type: integer
# % description: Maximum cloud cover percentage for Landsat scene
# % required: no
# % guisection: Filter
# %end

# %option
# % key: timeout
# % type: integer
# % description: Download timeout in seconds
# % answer: 300
# % guisection: Optional
# %end


# %flag
# % key: l
# % description: List the search result without downloading
# %end

# %flag
# % key: e
# % description: Extract the downloaded the datasets
# %end

# %flag
# % key: d
# % description: Delete the product archieve after downloading
# %end


import sys
import os
import getpass
from datetime import *
import grass.script as gs
from grass.exceptions import ParameterError


def create_dir(dir):
    if not os.path.isdir(dir):
        try:
            os.makedirs(dir)
            return 0
        except Exception as e:
            gs.warning(_("Could not create directory {}").format(dir))
            return 1
    gs.verbose(_("Directory {} already exists").format(dir))
    return 0


def get_bb(vector=None):
    args = {}
    if vector:
        args["vector"] = vector
    # are we in LatLong location?
    kv = gs.parse_command("g.proj", flags="j")
    if "+proj" not in kv:
        gs.fatal("Unable to get bounding box: unprojected location not supported")
    if kv["+proj"] != "longlat":
        info = gs.parse_command("g.region", flags="uplg", **args)
        return {
            "lonmin": info["nw_long"],
            "latmin": info["sw_lat"],
            "lonmax": info["ne_long"],
            "latmax": info["nw_lat"],
        }
    info = gs.parse_command("g.region", flags="upg", **args)
    return {
        "lonmin": info["w"],
        "latmin": info["s"],
        "lonmax": info["e"],
        "latmax": info["n"],
    }


def download_products(products_list):
    dag.download_all(products_list)


def download_by_id(query_id: str):
    gs.verbose(
        _(f"Searching for product ending with: {query_id[-min(len(query_id), 8):]}")
    )
    product, count = dag.search(id=query_id)
    if count != 1:
        raise ParameterError("Product couldn't be uniquely identified")
    if not product[0].properties["id"].startswith(query_id):
        raise ParameterError("Product wasn't found")
    gs.verbose(_(f"Poduct ending with: {query_id[-min(len(query_id), 8):]} is found."))
    gs.verbose(_("Downloading..."))
    dag.download(product[0])


def download_by_ids(ids: list):
    for id in ids:
        try:
            download_by_id(id)
        except ParameterError:
            gs.error(
                _(f"Product ending with: {id[-min(len(id), 8):]}, failed to download")
            )


def setup_environment_variables():
    os.environ[f"EODAG__{options['provider']}__DOWNLOAD__EXTRACT"] = str(flags["e"])
    os.environ[f"EODAG__{options['provider']}__DOWNLOAD__DELETE_ARCHIV"] = str(
        flags["d"]
    )

    if options["output"]:
        os.environ[f"EODAG__{options['provider']}__DOWNLOAD__OUTPUTS_PREFIX"] = options[
            "output"
        ]


def main():
    # products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    # TODO: Add option for setting a differnt config file path
    global options, flags
    options, flags = gs.parser()
    # setting the envirionmnets variables has to come before the dag initialization
    setup_environment_variables()

    global dag
    dag = EODataAccessGateway()

    if options["provider"]:
        dag.set_preferred_provider(options["provider"])

    # Download by ids... if ids are provided only these ids will be downloaded
    if options["id"]:
        ids = options["id"].split(",")
        download_by_ids(ids)
    else:

        items_per_page = 20
        # TODO: Check that the product exists, could be handled by catching exceptions when searching...
        product_type = options["dataset"]

        # TODO: Allow user to specify a shape file path
        geom = (
            # use boudning box of current computational region
            # get_bb()
            {
                "lonmin": 1.9,
                "latmin": 43.9,
                "lonmax": 2,
                "latmax": 44,
            }  # hardcoded for testing
        )

        gs.verbose(geom)

        search_parameters = {
            "items_per_page": items_per_page,
            "productType": product_type,
            # TODO: Convert to a shapely object
            "geom": geom,
        }

        if options["clouds"]:
            search_parameters["cloudCover"] = options["clouds"]

        start_date = options["start"]
        if not options["start"]:
            delta_days = timedelta(60)
            start_date = str(datetime.now() - delta_days)
        start_date = datetime.fromisoformat(start_date)

        end_date = options["end"]
        if not options["end"]:
            end_date = str(datetime.now())
        end_date = datetime.fromisoformat(end_date)

        if end_date < start_date:
            gs.fatal(
                _(f"End Date ({end_date}) cannot come before Start Date ({start_date})")
            )

        # Requires further testing to make sure the isoformat works with all the providers
        # TODO: Normalize to UTC
        search_parameters["start"] = start_date.isoformat()[:-6]  # Remove the timezone
        search_parameters["end"] = end_date.isoformat()[:-6]

        search_results = dag.search_all(**search_parameters)
        num_results = len(search_results)
        gs.message(_(f"Found {num_results} matching scenes " f"of type {product_type}"))
        if flags["l"]:
            # TODO: Oragnize output format better
            idx = 0
            for product in search_results:
                print(
                    _(
                        f'Product #{idx} - ID:{product.properties["id"]},provider:{product.provider}'
                    )
                )
                idx += 1
        else:
            download_products(search_results)

            # TODO: Consider adding a quicklook flag
            """
            import matplotlib.pyplot as plt
            import matplotlib.image as mpimg

            fig = plt.figure(figsize=(10, 8))
            for i, product in enumerate(search_results, start=1):
                if i > 7 * 8:
                    break
                # This line takes care of downloading the quicklook
                quicklook_path = product.get_quicklook()

                # Plot the quicklook
                img = mpimg.imread(quicklook_path)
                ax = fig.add_subplot(7, 8, i)
                ax.set_title(i - 1)
                plt.imshow(img)
            plt.tight_layout()
            plt.show()
            """


if __name__ == "__main__":

    try:
        from eodag import EODataAccessGateway
        from eodag import setup_logging
        from eodag.api.product.metadata_mapping import DEFAULT_METADATA_MAPPING
        from eodag.utils import get_geometry_from_various

        # for debugging -> 3
        setup_logging(verbose=2)
    except:
        gs.fatal(_("Cannot import eodag. Please intall the library first."))

    sys.exit(main())
