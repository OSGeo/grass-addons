#!/usr/bin/env python


"""
MODULE:         i.nightlights.intercalibration

AUTHOR:         Nikos Alexandris <nik@nikosalexandris.net> Trikala, March 2015

PURPOSE:        Performing inter-satellite calibration on DMSP-OLS Nighttime
                Lights Time Series (cleaned up average visible band) based on
                regression models proposed by Elvidge (2009/2014), Liu (2012)
                and Wu (2013).

                - Elvidge (2009)

                  Empirical second order polynomial regression model:


                  where:

                  - DN adj.:    Adjusted Digital Numbers
                  - DN          Raw Digital Number
                  - C0:         First polynomial constant
                  - C1:         Second polynomial constant
                  - C2:         Third polynomial constant


                - Elvidge (2014)

                  Same model as in 2009, improved coefficients


                - Liu (2012)

                  Empirical second order polynomial regression model & optimal
                  threshold method:  DNc = a × DN^2 + b × DN + c

                  where:

                  - DNc:        Calibrated Digital Number
                  - DN:         Raw Digital Number
                  - a:          First polynomial constant
                  - b:          Second polynomial constant
                  - c:          Third polynomial constant


                - Wu (2013)

                  Power calibration model:  DNc + 1 = a × (DN + 1)^b

                  where:

                  - DNc:        Calibrated Digital Number
                  - DN:         Raw Digital Number
                  - a:          Constant
                  - b:          Power

               Overview

   +----------------------------------------------------------------------+
   |                                                                      |
   |          +-----------------+                                         |
   | DN  +--> |Calibration Model| +-->  Calibrated DN                     |
   |          +---^-------------+            ^                            |
   |              |                          |                            |
   |              |             +--Evaluation+Methods-------------------+ |
   |              |             |                                       | |
   |              |             | ? Not Implemented                     | |
   |              |             |                                       | |
   |              |             +---------------------------------------+ |
   |              |                                                       |
   | +--Regression+Models-----------------------------------------------+ |
   | |                                                                  | |
   | |  Elvidge, 2009/2014:  DNc = C0 + C1×DN + C2×DNv2                 | |
   | |                                                                  | |
   | |  Liu, 2012:  based on Elvidge's model + optimal threshold method | |
   | |                                                                  | |
   | |  Wu, 2014:            DNc + 1 = a×(DN + 1)^b                     | |
   | |                                                                  | |
   | |  Others?                                                         | |
   | |                                                                  | |
   | +------------------------------------------------------------------+ |
   |                                               http://asciiflow.com   |
   +----------------------------------------------------------------------+


               Sources

               - <http://ngdc.noaa.gov/eog/dmsp.html>

               - <http://ngdc.noaa.gov/eog/dmsp/downloadV4composites.html>

               - Metadata on DMSP-OLS:
               <https://catalog.data.gov/harvest/object/e84ef28f-7935-4ca2-b9c7-7a77cb156c4c/html>

               - From <http://ngdc.noaa.gov/eog/gcv4_readme.txt> on the data
               this module is meant to process:

                 F1?YYYY_v4b_stable_lights.avg_vis.tif: The cleaned up avg_vis
                 contains the lights from cities, towns, and other sites with
                 persistent lighting, including gas flares. Ephemeral events,
                 such as fires have been discarded. Then the background noise
                 was identified and replaced with values of zero. Data values
                 range from 1-63. Areas with zero cloud-free observations are
                 represented by the value 255.


 COPYRIGHT:    (C) 2014 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

# %Module
# %  description: Performs inter-satellite calibration on DMSP-OLS Nighttime Lights Time Series
# %  keywords: imagery
# %  keywords: inter-satellite
# %  keywords: calibration
# %  keywords: nighttime lights
# %  keywords: time series
# %  keywords: DMSP-OLS
# %End

# %flag
# %  key: c
# %  description: Print out citation for selected calibration model
# %end

# %flag
# %  key: i
# %  description: Print out calibration equations
# %end

# % flag
# %  key: e
# %  description: Evaluation based on the Normalised Difference Index
# % end

# % flag
# %  key: g
# %  description: Print in shell script style (currently only NDI via -e)
# % end

# %flag
# %  key: x
# %  description: Match computational region to extent of input image
# %end

# %flag
# % key: z
# %  description: Exclude zero values from the analysis (retain zero cells in output)
# %end

# %flag
# % key: n
# %  description: Exclude zero values from the analysis (set zero cells to NULL in output)
# %end

# %flag
# % key: t
# %  description: Do not try to transfer timestamps (for input without timestamp)
# %end

# % rules
# %  exclusive: -z,-n
# % end

# %option G_OPT_R_INPUTS
# % key: image
# % key_desc: name
# % description: Clean average DMSP-OLS visible band digital number image(s)
# % required : yes
# % multiple : yes
# %end

# %option G_OPT_R_BASENAME_OUTPUT
# % key: suffix
# % key_desc: suffix
# % type: string
# % label: output file(s) suffix
# % description: Suffix for calibrated average digital number output image(s)
# % required: yes
# % answer: c
# %end

# %option
# % key: model
# % key_desc: author
# % type: string
# % label: Calibration model
# % description: Inter-satellite calibration model for average DMSP-OLS nighttime lights time series
# % descriptions: Elvidge (2009 or 2014), Liu 2012, Wu 2013
# % options: elvidge2009,elvidge2014,liu2012,wu2013
# % required: yes
# % answer: elvidge2014
# % guisection: Calibration Model
# % multiple : no
# %end


# required librairies -------------------------------------------------------
import os
import sys

sys.path.insert(
    1,
    os.path.join(os.path.dirname(sys.path[0]), "etc", "i.nightlights.intercalibration"),
)

import atexit
import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g

# from grass.pygrass.modules.shortcuts import raster as r
# from grass.pygrass.raster.abstract import Info

from intercalibration_models import Elvidge, Liu2012, Wu2013


# any constants? -------------------------------------------------------------
MODELS = {"elvidge": Elvidge, "liu2012": Liu2012, "wu2013": Wu2013}

# helper functions ----------------------------------------------------------
def cleanup():
    """
    Clean up temporary maps
    """
    if len(temporary_maps) > 0:
        for temporary_map in temporary_maps:
            grass.message(_("Removing temporary files..."))
            grass.run_command(
                "g.remove", flags="f", type="rast", name=temporary_map, quiet=True
            )


def run(cmd, **kwargs):
    """
    Pass required arguments to grass commands (?)
    """
    grass.run_command(cmd, quiet=True, **kwargs)


def retrieve_model_parameters(model_class, *args, **kwargs):
    """
    Run the user-requested calibration model and return model class objects
    from which the calibration coefficients, the associated RMSE, and the
    mapcalc formula of interest will be retrieved.
    """
    model = model_class(*args, **kwargs)
    citation_string = model.citation
    coefficients = model.coefficients
    coefficients_r2 = model.report_r2()
    mapcalc_formula = model.mapcalc
    return citation_string, coefficients, coefficients_r2, mapcalc_formula


def total_light_index(ntl_image):
    """
    Evaluation index (TLI) which represents the sum of grey values in an area.
    """
    univar = grass.parse_command(
        "r.univar", map=ntl_image, flags="g", parse=(grass.parse_key_val, {"sep": "="})
    )
    return float(univar["sum"])


def normalised_difference_index(tli_one, tli_two):
    """
    Normalised Difference Index based on the total light indices of two
    satellite images in a certain year.
    """
    return abs(tli_one - tli_two) / (tli_one + tli_two)


def main():
    """
    Main program: get names for input, output suffix, options and flags
    """
    input_list = options["image"].split(",")
    outputsuffix = options["suffix"]

    # Select model based on author
    author_year = options["model"]
    if "elvidge" in author_year:
        version = author_year[7:]
        author_year = "elvidge"
    else:
        version = None
    Model = MODELS[author_year]
    # ----------------------------

    # flags
    citation = flags["c"]
    info = flags["i"]
    extend_region = flags["x"]
    timestamps = not (flags["t"])
    zero = flags["z"]
    null = flags["n"]  # either zero or null, not both --- FixMe! ###
    evaluation = flags["e"]
    shell = flags["g"]

    global temporary_maps
    temporary_maps = []

    msg = "|i Inter-satellite calibration of DMSP-OLS Nighttime Stable " "Lights"
    g.message(msg)
    del msg

    """Temporary Region and Files"""

    if extend_region:
        grass.use_temp_region()  # to safely modify the region

    tmpfile = grass.basename(grass.tempfile())
    tmp = "tmp." + tmpfile

    """Loop over list of input images"""

    for image in input_list:

        satellite = image[0:3]
        year = image[3:7]

        """If requested, match region to input image"""

        if extend_region:
            run("g.region", rast=image)  # ## FixMe?
            msg = "\n|! Matching region extent to map {name}"
            msg = msg.format(name=image)
            g.message(msg)
            del msg

        elif not extend_region:
            grass.warning(_("Operating on current region"))

        """Retrieve coefficients"""

        msg = "\n|> Calibrating average visible Digital Number values "
        g.message(msg)
        del msg

        # if "version" == True use Elvidge, else use Liu2012 or Wu2013
        args = (satellite, year, version) if version else (satellite, year)
        model_parameters = retrieve_model_parameters(Model, *args)

        #        # print model's generic equation?
        #        if info:
        #            print this
        #            print that

        # split parameters in usable variables
        citation_string, coefficients, r2, mapcalc_formula = model_parameters
        msg = "|>>> Regression coefficients: " + str(coefficients)
        msg += "\n" + "|>>> " + r2
        g.message(msg)
        del msg

        # Temporary Map
        tmp_cdn = "{prefix}.Calibrated".format(prefix=tmp)
        temporary_maps.append(tmp_cdn)

        """Formula for mapcalc"""

        equation = "{out} = {inputs}"
        calibration_formula = equation.format(out=tmp_cdn, inputs=mapcalc_formula)

        # alternatives
        if zero:
            zcf = "{out} = if(Input == 0, 0, {formula})"
            calibration_formula = zcf.format(out=tmp_cdn, formula=mapcalc_formula)
            msg = "\n|i Excluding zero cells from the analysis"
            g.message(msg)
            del msg

        elif null:
            ncf = "{out} = if(Input == 0, null(), {formula})"
            calibration_formula = ncf.format(out=tmp_cdn, formula=mapcalc_formula)
            msg = "\n|i Setting zero cells to NULL"
            g.message(msg)
            del msg

        # Compress even more? -----------------------------------------------
        #        if zero or null:
        #            zero = 0 if zero else ('null()')
        #            equation = "{out} = if(Input == 0, {zn}, {formula})"
        #            calibration_formula = equation.format(out=tmp_cdn, zero, formula=mapcalc_formula)
        # ----------------------------------------------- Compress even more?

        # replace the "dummy" string...
        calibration_formula = calibration_formula.replace("Input", image)

        """Calibrate"""

        if info:
            msg = "\n|i Mapcalc formula: {formula}"
            g.message(msg.format(formula=mapcalc_formula))
            del msg

        grass.mapcalc(calibration_formula, overwrite=True)

        """Transfer timestamps, if any"""

        if timestamps:

            try:
                datetime = grass.read_command("r.timestamp", map=image)
                run("r.timestamp", map=tmp_cdn, date=datetime)

                msg = "\n|i Timestamping: {stamp}".format(stamp=datetime)
                g.message(msg)

            except CalledModuleError:
                grass.fatal(
                    _(
                        "\n|* Timestamp is missing! "
                        "Please add one to the input map if further times series "
                        "analysis is important. "
                        "If you don't need it, you may use the -t flag."
                    )
                )

        else:
            grass.warning(_("As requested, timestamp transferring not attempted."))

        # -------------------------------------------------------------------------
        # add timestamps and register to spatio-temporal raster data set
        # -------------------------------------------------------------------------

        # ToDo -- borrowed from r.sun.daily
        # - change flag for "don't timestamp", see above
        # - use '-t' for temporal, makes more sense
        # - adapt following

        # temporal = flags['t']
        # if temporal:
        #     core.info(_("Registering created maps into temporal dataset..."))
        #     import grass.temporal as tgis

        #     def registerToTemporal(basename, suffixes, mapset, start_day, day_step,
        #                            title, desc):
        #         """
        #         Register daily output maps in spatio-temporal raster data set
        #         """
        #         maps = ','.join([basename + suf + '@' + mapset for suf in suffixes])
        #         tgis.open_new_stds(basename, type='strds', temporaltype='relative',
        #                            title=title, descr=desc, semantic='sum',
        #                            dbif=None, overwrite=grass.overwrite())

        #         tgis.register_maps_in_space_time_dataset(type='rast',
        #                                                  name=basename, maps=maps,
        #                                                  start=start_day, end=None,
        #                                                  unit='days',
        #                                                  increment=day_step,
        #                                                  dbif=None, interval=False)

        """Normalised Difference Index (NDI), if requested"""

        ndi = float()
        if evaluation:

            # total light indices for input, tmp_cdn images
            tli_image = total_light_index(image)
            tli_tmp_cdn = total_light_index(tmp_cdn)

            # build
            ndi = normalised_difference_index(tli_image, tli_tmp_cdn)

            # report if -g
            if shell:
                msg = "ndi={index}".format(index=round(ndi, 3))
                g.message(msg)
                del msg

            # else, report
            else:
                msg = "\n|i Normalised Difference Index for {dn}: {index}"
                msg = msg.format(dn=image, index=round(ndi, 3))
                g.message(msg)
                del msg

        """Strings for metadata"""

        history_calibration = "Regression model: "
        history_calibration += mapcalc_formula
        history_calibration += "\n\n"
        if ndi:
            history_calibration += "NDI: {ndi}".format(ndi=round(ndi, 10))
        title_calibration = "Calibrated DMSP-OLS Stable Lights"
        description_calibration = (
            "Inter-satellite calibrated average " "Digital Number values"
        )
        units_calibration = "Digital Numbers (Calibrated)"

        source1_calibration = citation_string
        source2_calibration = ""

        # history entry
        run(
            "r.support",
            map=tmp_cdn,
            title=title_calibration,
            units=units_calibration,
            description=description_calibration,
            source1=source1_calibration,
            source2=source2_calibration,
            history=history_calibration,
        )

        """Add suffix to basename & rename end product"""

        name = "{prefix}.{suffix}"
        name = name.format(prefix=image.split("@")[0], suffix=outputsuffix)
        calibrated_name = name
        run("g.rename", rast=(tmp_cdn, calibrated_name))
        temporary_maps.remove(tmp_cdn)

        """Restore previous computational region"""

        if extend_region:
            grass.del_temp_region()
            g.message("\n|! Original Region restored")

        """Things left to do..."""

        if citation:
            msg = "\n|i Citation: {string}".format(string=citation_string)
            g.message(msg)
            del msg


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
