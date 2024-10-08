#!/usr/bin/env python3

############################################################################
#
# MODULE:	i.sar.speckle
#
# AUTHOR:   Margherita Di Leo, Santiago Seppi
#
# PURPOSE:	Speckle noise removal for synthetic aperture radar (SAR) images
#
# COPYRIGHT: (C) 2002-2023 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
# REFERENCES:
#
# Lee, J. S. (1986). Speckle suppression and analysis for synthetic aperture
# radar images. Optical engineering, 25(5), 255636.
#
#############################################################################

# %Module
# % description: Remove speckle from SAR image
# % keyword: imagery
# % keyword: speckle
# % keyword: sar
# % keyword: radar
# % overwrite: yes
# %End
# %option G_OPT_R_INPUT
# % key: input
# % description: Name of input image
# % required: yes
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Name of output image
# % required: yes
# %end
# %option
# % key: method
# % description: Method for speckle removal
# % options: lee,mean,gauss
# % answer: lee
# % required: yes
# %end
# %option
# % key: size
# % type: integer
# % description: Size of neighborhood
# % answer: 11
# % required: yes
# %end
# %option
# % key: std
# % type: double
# % description: Standard deviation value in case gaussian filter is selected
# % answer: 1
# % required: no
# %end


#import os
import grass.script as gs
import atexit
#from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

def remove(name):
    gs.run_command("g.remove", type="raster", name=name, flags="f", quiet=True, errors="ignore")

def lee_filter(img, size, img_out):
    #pid = str(os.getpid())
    # ~ img_mean = "tmp%s_img_mean" % pid
    # ~ img_sqr = "tmp%s_img_sqr" % pid
    # ~ img_sqr_mean = "tmp%s_img_sqr_mean" % pid
    # ~ img_variance = "tmp%s_img_variance" % pid
    # ~ img_weights = "tmp%s_img_weights" % pid
    
    img_mean = gs.append_node_pid("img_mean")
    img_sqr = gs.append_node_pid("img_sqr")
    img_sqr_mean = gs.append_node_pid("img_sqr_mean")
    img_variance = gs.append_node_pid("img_variance")
    img_weights = gs.append_node_pid("img_weights")
    atexit.register(remove, img_mean)
    atexit.register(remove, img_sqr)
    atexit.register(remove, img_sqr_mean)
    atexit.register(remove, img_variance)
    atexit.register(remove, img_weights)


    # Local mean
    r.neighbors(input=img, size=size, method="average", output=img_mean)
    # Local square mean
    r.mapcalc("%s = %s^2" % (img_sqr, img))
    r.neighbors(input=img_sqr, size=size, method="average", output=img_sqr_mean)
    # Local variance
    r.mapcalc("%s = %s - (%s^2)" % (img_variance, img_sqr_mean, img_mean))
    # Overall variance
    univar_stats = gs.parse_command("r.univar", map=img, flags="ge")
    overall_variance = univar_stats["variance"]
    # Weights
    r.mapcalc(
        "%s = %s / (%s + %s)"
        % (img_weights, img_variance, img_variance, overall_variance)
    )
    # Output
    r.mapcalc(
        "%s = %s + %s * (%s - %s)" % (img_out, img_mean, img_weights, img, img_mean)
    )

    # ~ # Cleanup
    # ~ gs.message(_("Cleaning up intermediate files..."))
    # ~ try:
        # ~ gs.run_command(
            # ~ "g.remove", flags="f", quiet=False, type="raster", pattern="tmp*"
        # ~ )
    # ~ except:
        # ~ """ """

    return img_out


def mean_filter(img, size, img_out):
    # Local mean
    r.neighbors(input=img, size=size, method="average", output=img_out)

    return img_out


def gauss_filter(img, size, std, img_out):
    # Gauss function
    r.neighbors(
        input=img,
        size=size,
        weighting_function="gaussian",
        weighting_factor=std,
        output=img_out,
    )

    return img_out


def main():
    method = options["method"]  # algorithm for speckle removal
    img = options["input"]  # name of input image
    img_out = options["output"]  # name of output image
    size = options["size"]  # size of neighborhood

    out = gs.core.find_file(img_out)

    if (out["name"] != "") and not gs.overwrite():
        gs.warning(
            _("Output map name already exists. " "Delete it or use overwrite flag")
        )

    if method == "lee":
        #g.message(_("Applying Lee Filter"))
        img_out = lee_filter(img, size, img_out)
        #g.message(_("Done."))

    elif method == "mean":
        #g.message(_("Applying Mean Filter"))
        img_out = mean_filter(img, size, img_out)
        #g.message(_("Done."))

    elif method == "gauss":
        std = options["std"]
        #g.message(_("Applying Gauss Filter"))
        img_out = gauss_filter(img, size, std, img_out)
        #g.message(_("Done."))

    else:
        gs.fatal(_("The requested speckle filter is not yet implemented."))


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
