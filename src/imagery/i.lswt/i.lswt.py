#!/usr/bin/env python

############################################################################
#
# MODULE:	i.lswt
# AUTHOR(S):	Sajid Pareeth
#
# PURPOSE:	Compute Lake Surface Water Temperature (inland waters) from TOA Brightness Temperatures(BT)
# COPYRIGHT:	(C) 1997-2014 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################
# References:
# The satellite specific split-window coefficients are taken from:
# Jimenez-Munoz, J.-C., Sobrino, J.A., 2008. Split-Window Coefficients for
# Land Surface Temperature Retrieval From Low-Resolution Thermal Infrared Sensors.
# IEEE Geoscience and Remote Sensing Letters 5, 806–809. doi:10.1109/LGRS.2008.2001636
#
# A new method to develop continuos time series of LSWT from historical AVHRR
# is explained below, uses the same split window technique implemented here:
# Pareeth, S., Delucchi, L., Metz, M., Rocchini, D., Devasthale, A., Raspaud,
# M., Adrian, R., Salmaso, N., Neteler, M., 2016.
# New Automated Method to Develop Geometrically Corrected Time Series of
# Brightness Temperatures from Historical AVHRR LAC Data. Remote Sensing 8, 169
# doi:10.3390/rs8030169
#
##############################################################################

# %Module
# % description: Computes Lake Surface Water Temperatures (inland water bodies) from TOA Brightness Temperatures.
# % keyword: imagery
# % keyword: LSWT
# % keyword: MODIS
# % keyword: AVHRR
# % keyword: AATSR
# % keyword: SEVIRI
# % keyword: IMG
# %end

# %option G_OPT_R_INPUT
# % key: ainput
# % description: Brightness Temperature (10.5 - 11.5 micro m)
# %end
# %option G_OPT_R_INPUT
# % key: binput
# % description: Brightness Temperature (11.5 - 12.5 micro m)
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % key: basename
# % description: Name for output basename raster map(s)
# %end
# %option
# % key: satellite
# % type: string
# % description: Satellite name
# % required: yes
# % multiple: no
# % options: NOAA07-AVHRR,NOAA09-AVHRR,NOAA11-AVHRR,NOAA12-AVHRR,NOAA14-AVHRR,NOAA15-AVHRR,NOAA16-AVHRR,NOAA17-AVHRR,NOAA18-AVHRR,NOAA19-AVHRR,METOPA-AVHRR,ERS1-ATSR1,ERS2-ATSR2,Envisat-AATSR,Terra-MODIS,Aqua-MODIS,GOES8-IMG,GOES9-IMG,GOES10-IMG,GOES11-IMG,GOES12-IMG,GOES13-IMG,MSG1-SEVIRI,MSG2-SEVIRI
# % descriptions: NOAA07-AVHRR;Use split-window coefficients for NOAA07-AVHRR;
# %end
# %flag
# % key: i
# % description: Display split-window coefficients and exit
# %end

import grass.script as grass

coeffs = {
    "NOAA07-AVHRR": {
        "c0": [-0.060],
        "c1": [1.752],
        "c2": [0.326],
        "c3": [45.2],
        "c4": [-0.88],
        "c5": [-152],
        "c6": [18.9],
    },
    "NOAA09-AVHRR": {
        "c0": [-0.003],
        "c1": [2.054],
        "c2": [0.333],
        "c3": [47.3],
        "c4": [-1.64],
        "c5": [-164],
        "c6": [20.6],
    },
    "NOAA11-AVHRR": {
        "c0": [-0.037],
        "c1": [1.897],
        "c2": [0.329],
        "c3": [46.3],
        "c4": [-1.30],
        "c5": [-158],
        "c6": [19.7],
    },
    "NOAA12-AVHRR": {
        "c0": [0.027],
        "c1": [1.602],
        "c2": [0.352],
        "c3": [42.5],
        "c4": [0.04],
        "c5": [-147],
        "c6": [18.1],
    },
    "NOAA14-AVHRR": {
        "c0": [0.025],
        "c1": [1.458],
        "c2": [0.273],
        "c3": [44.0],
        "c4": [-0.47],
        "c5": [-133],
        "c6": [16.4],
    },
    "NOAA15-AVHRR": {
        "c0": [-0.031],
        "c1": [1.826],
        "c2": [0.327],
        "c3": [44.7],
        "c4": [-0.71],
        "c5": [-155],
        "c6": [19.3],
    },
    "NOAA16-AVHRR": {
        "c0": [-0.110],
        "c1": [1.277],
        "c2": [0.321],
        "c3": [40.1],
        "c4": [0.86],
        "c5": [-134],
        "c6": [16.3],
    },
    "NOAA17-AVHRR": {
        "c0": [-0.032],
        "c1": [1.783],
        "c2": [0.311],
        "c3": [45.1],
        "c4": [-0.87],
        "c5": [-151],
        "c6": [18.9],
    },
    "NOAA18-AVHRR": {
        "c0": [-0.098],
        "c1": [1.281],
        "c2": [0.276],
        "c3": [42.0],
        "c4": [0.18],
        "c5": [-129],
        "c6": [15.7],
    },
    "NOAA19-AVHRR": {
        "c0": [-0.031],
        "c1": [1.212],
        "c2": [0.235],
        "c3": [41.03],
        "c4": [0.450],
        "c5": [-120.24],
        "c6": [14.77],
    },
    "METOPA-AVHRR": {
        "c0": [-0.045],
        "c1": [1.733],
        "c2": [0.307],
        "c3": [44.3],
        "c4": [-0.61],
        "c5": [-150],
        "c6": [18.7],
    },
    "ERS1-ATSR1": {
        "c0": [-0.131],
        "c1": [1.697],
        "c2": [0.427],
        "c3": [42.58],
        "c4": [0.026],
        "c5": [-159.88],
        "c6": [19.62],
    },
    "ERS2-ATSR2": {
        "c0": [-0.151],
        "c1": [1.064],
        "c2": [0.342],
        "c3": [37.1],
        "c4": [1.81],
        "c5": [-131],
        "c6": [15.7],
    },
    "Envisat-AATSR": {
        "c0": [-0.172],
        "c1": [1.016],
        "c2": [0.299],
        "c3": [39.7],
        "c4": [0.97],
        "c5": [-124],
        "c6": [14.8],
    },
    "Terra-MODIS": {
        "c0": [-0.004],
        "c1": [2.625],
        "c2": [0.424],
        "c3": [41.4],
        "c4": [0.04],
        "c5": [-201],
        "c6": [26.6],
    },
    "Aqua-MODIS": {
        "c0": [0.012],
        "c1": [2.601],
        "c2": [0.424],
        "c3": [41.3],
        "c4": [0.14],
        "c5": [-199],
        "c6": [26.3],
    },
    "GOES8-IMG": {
        "c0": [0.048],
        "c1": [1.447],
        "c2": [0.244],
        "c3": [45.4],
        "c4": [-0.97],
        "c5": [-129],
        "c6": [15.8],
    },
    "GOES9-IMG": {
        "c0": [-0.011],
        "c1": [1.335],
        "c2": [0.236],
        "c3": [44.2],
        "c4": [-0.53],
        "c5": [-124],
        "c6": [15.3],
    },
    "GOES10-IMG": {
        "c0": [-0.111],
        "c1": [1.083],
        "c2": [0.219],
        "c3": [43.0],
        "c4": [-0.21],
        "c5": [-114],
        "c6": [13.9],
    },
    "GOES11-IMG": {
        "c0": [-0.030],
        "c1": [1.275],
        "c2": [0.245],
        "c3": [43.0],
        "c4": [-0.15],
        "c5": [-123],
        "c6": [15.1],
    },
    "GOES12-IMG": {
        "c0": [1.815],
        "c1": [-0.311],
        "c2": [0.020],
        "c3": [-46.3],
        "c4": [27.26],
        "c5": [-50],
        "c6": [7.6],
    },
    "GOES13-IMG": {
        "c0": [1.833],
        "c1": [-0.331],
        "c2": [0.022],
        "c3": [-40.7],
        "c4": [25.64],
        "c5": [-51],
        "c6": [7.9],
    },
    "MSG1-SEVIRI": {
        "c0": [0.006],
        "c1": [1.736],
        "c2": [0.297],
        "c3": [45.3],
        "c4": [-0.97],
        "c5": [-147],
        "c6": [18.3],
    },
    "MSG2-SEVIRI": {
        "c0": [-0.021],
        "c1": [1.503],
        "c2": [0.273],
        "c3": [44.2],
        "c4": [-0.58],
        "c5": [-135],
        "c6": [16.7],
    },
}


def main():
    options, flags = grass.parser()
    bt1 = options["ainput"]
    bt2 = options["binput"]
    basename = options["basename"]
    output = basename + "_lswt"
    satellite = options["satellite"]
    c0 = coeffs.get(satellite).get("c0")[0]
    c1 = coeffs.get(satellite).get("c1")[0]
    c2 = coeffs.get(satellite).get("c2")[0]
    coeff = flags["i"]
    if coeff:
        grass.message(
            "Split window coefficients for {satellite} are "
            "c0={c0};c1={c1};c2={c2}".format(satellite=satellite, c0=c0, c1=c1, c2=c2)
        )
        return
    elif (bool(bt1) == 0) or (bool(bt2) == 0) or (bool(basename) == 0):
        # logging.error('error: ', message)
        grass.error("in1, in2 and basename are required for computing lswt")
    else:
        grass.message(
            "Computing water surface temperature - Remember to set"
            " water mask: Output file is {basename}_lswt".format(basename=basename)
        )
        # Split window equation for water surface
        grass.mapcalc(
            exp="{out} = {bt1} + {c1} * ({bt1} - {bt2}) + {c2} *"
            " ({bt1} - {bt2})^2 + {c0}".format(
                out=output, bt1=bt1, bt2=bt2, c0=c0, c1=c1, c2=c2
            )
        )


if __name__ == "__main__":
    main()
