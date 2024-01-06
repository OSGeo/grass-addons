#!/usr/bin/env python

"""
 MODULE:       i.histo.match
 AUTHOR(S):    Stefan Blumentrath (Norway) parallel / Numpy re-implementation
               of the original module written by:
               Luca Delucchi, Fondazione E. Mach (Italy)
               original PERL code was developed by:
               Laura Zampa (2004) student of Dipartimento di Informatica e
               Telecomunicazioni, Facoltà di Ingegneria,
               University of Trento  and ITC-irst, Trento (Italy)

 PURPOSE:      Calculate histogram matching of several images
 COPYRIGHT:    (C) 2011-2024 by the GRASS Development Team

               This program is free software under the GNU General
               Public License (>=v2). Read the file COPYING that
               comes with GRASS for details.
"""

# %module
# % description: Calculate histogram matching of several images.
# % keyword: imagery
# % keyword: histogram matching
# %end

# %option G_OPT_R_INPUTS
# % description: Name of raster maps to be analyzed
# % required: yes
# %end

# %option
# % key: suffix
# % type: string
# % gisprompt: Suffix for output maps
# % description: Suffix for output maps
# % required: no
# % answer: match
# %end

# %option G_OPT_R_OUTPUT
# % description: Name for mosaic output map
# % required: no
# %end

# %option G_OPT_DB_DATABASE
# % description: DEPRECATED, do not use
# % required : no
# %end

# %option
# % key: max
# % type: integer
# % gisprompt: Number of the maximum value for raster maps
# % description: Number of the maximum value for raster maps
# % required: no
# % answer: 255
# %end

# %option G_OPT_M_NPROCS
# %end


import sys
import os

from functools import partial
from multiprocessing import Pool

import numpy as np

import grass.script as gs


def create_image_histogram_array(max_value):
    """Create empty numpy array for image histograms"""
    # Create numpy array
    histogram_array = np.zeros(
        max_value,
        dtype={
            "names": ("grey_value", "pixel_frequency", "cumulative_histogram", "cdf"),
            "formats": (int, int, int, float),
        },
    )
    histogram_array["grey_value"] = range(0, max_value)

    return histogram_array


def get_cumulative_image_histogram(image, max_value=255):
    """Get cumulative image histogram"""
    # Create numpy array
    image_histogram = create_image_histogram_array(max_value)

    # Set the region on the raster in region env
    g_env = os.environ.copy()
    g_env["GRASS_REGION"] = gs.region_env(raster=image, align=image)

    # calculate statistics
    stats_out = np.genfromtxt(
        gs.decode(
            gs.read_command(
                "r.stats",
                flags="cin",
                input=image,
                separator=",",
                env=g_env,
                quiet=True,
            )
        )
        .strip()
        .split("\n"),
        delimiter=",",
        dtype=None,
    )
    for idx, frequency in stats_out:
        image_histogram["pixel_frequency"][idx] = frequency

    image_histogram["cumulative_histogram"] = np.cumsum(
        image_histogram["pixel_frequency"]
    )
    number_of_pixels = np.sum(image_histogram["pixel_frequency"])
    image_histogram["cdf"] = np.round(
        image_histogram["cumulative_histogram"].astype(float) / float(number_of_pixels),
        6,
    )

    return (image, number_of_pixels, image_histogram)


def get_average_cumulative_image_histogram(image_histograms, max_value):
    """Get average of cumulative image histograms"""

    # Create average numpy array
    average_image_histogram = create_image_histogram_array(max_value)
    average_image_histogram["pixel_frequency"] = (
        sum((hist[2]["pixel_frequency"] for hist in image_histograms))
        / len(image_histograms)
    ).astype(int)
    average_image_histogram["cumulative_histogram"] = np.cumsum(
        average_image_histogram["pixel_frequency"]
    )

    # Get total number of pixels divided by number of images
    number_of_pixels = np.sum(average_image_histogram["pixel_frequency"])
    average_image_histogram["cdf"] = np.round(
        average_image_histogram["cumulative_histogram"].astype(float)
        / float(number_of_pixels),
        6,
    )

    return average_image_histogram


def reclassify_image(image_histogram_result, suffix=None, average_image_histogram=None):
    """Reclassify image usiing corresponding grey values for closest
    average CDF values"""
    image = image_histogram_result[0]
    image_histogram = image_histogram_result[2]
    outname = f"{image.split('@')[0]}.{suffix}"

    # check if the output map already exists
    result = gs.core.find_file(outname, element="cell")
    if result["fullname"] and gs.overwrite():
        gs.run_command("g.remove", flags="f", type="raster", name=outname, quiet=True)
    elif result["fullname"] and not gs.overwrite():
        gs.warning(
            _("Raster map {} already exists and will not be overwritten").format(
                outname
            )
        )
        return outname

    # Create average reclassification rules
    reclass_rules = []
    for grey_value in image_histogram["grey_value"]:
        # Select new grey value based on closesd average CDF value
        new_grey = (
            np.abs(image_histogram["cdf"][grey_value] - average_image_histogram["cdf"])
        ).argmin()
        reclass_rules.append(f"{grey_value} = {new_grey}")

    gs.write_command(
        "r.reclass",
        quiet=True,
        input=image,
        out=outname,
        rules="-",
        stdin="\n".join(reclass_rules) + "\n",
    )

    # Write CMD history:
    gs.raster_history(outname)
    return outname


def main():
    """Main function"""
    # Split input images
    images = options["input"].split(",")

    # Database path is deprecated
    if options["database"]:
        gs.warning(_("database option is deprecated and no longer used."))

    # Output suffix
    suffix = options["suffix"]

    # Output mosaic map
    mosaic = options["output"]

    # Increment the maximum value by 1 for correct usage of range function
    max_value = int(options["max"]) + 1

    # Setup parallel processing
    nprocs = min(len(images), int(options["nprocs"]))
    get_cumulative_histogram = partial(
        get_cumulative_image_histogram, max_value=max_value
    )

    gs.verbose(_("Calculating Cumulative Distribution Functions ..."))
    # Get cumulative image histograms
    if nprocs > 1:
        with Pool(nprocs) as pool:
            image_histograms = pool.map(get_cumulative_histogram, images)
    else:
        image_histograms = [get_cumulative_histogram(image) for image in images]

    # Compute average cumulative image histogram
    average_histogram = get_average_cumulative_image_histogram(
        image_histograms, max_value
    )

    gs.verbose(_("Reclassifying bands based on average histogram..."))
    reclassify_image_grey_value = partial(
        reclassify_image, suffix=suffix, average_image_histogram=average_histogram
    )
    # Reclassify images
    if nprocs > 1:
        with Pool(nprocs) as pool:
            output_names = pool.map(reclassify_image_grey_value, image_histograms)
    else:
        output_names = [
            reclassify_image_grey_value(image_histogram_result)
            for image_histogram_result in image_histograms
        ]

    if mosaic:
        gs.verbose(_("Processing mosaic <{}>...").format(mosaic))
        # Set the region on the raster in region env
        g_env = os.environ.copy()
        g_env["GRASS_REGION"] = gs.region_env(raster=options["input"], align=images[0])

        gs.run_command(
            "r.patch",
            input=output_names,
            output=mosaic,
            nprocs=options["nprocs"],
            env=g_env,
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
