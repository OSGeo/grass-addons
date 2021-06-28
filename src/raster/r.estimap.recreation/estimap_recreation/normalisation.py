"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v

from .constants import *
from .grassy_utilities import *


def zerofy_small_values(raster, threshhold, output_name):
    """
    Set the input raster map cell values to 0 if they are smaller than the
    given threshhold

    Parameters
    ----------
    raster :
        Name of input raster map

    threshhold :
        Reference for which to flatten smaller raster pixel values to zero

    output_name :
        Name of output raster map

    Returns
    -------
        Does not return any value

    Examples
    --------
    ...
    """
    rounding = "if({raster} < {threshhold}, 0, {raster})"
    rounding = rounding.format(raster=raster, threshhold=threshhold)
    rounding_equation = EQUATION.format(result=output_name, expression=rounding)
    grass.mapcalc(rounding_equation, overwrite=True)


def normalize_map(raster, output_name):
    """
    Normalize all raster map cells by subtracting the raster map's minimum and
    dividing by the range.

    Parameters
    ----------
    raster :
        Name of input raster map

    output_name :
        Name of output raster map

    Returns
    -------

    Examples
    --------
    ...
    """
    # grass.debug(_("Input to normalize: {name}".format(name=raster)))
    # grass.debug(_("Ouput: {name}".format(name=output_name)))

    finding = grass.find_file(name=raster, element="cell")

    if not finding["file"]:
        grass.fatal("Raster map {name} not found".format(name=raster))
    # else:
    #     grass.debug("Raster map {name} found".format(name=raster))

    # univar_string = grass.read_command('r.univar', flags='g', map=raster)
    # univar_string = univar_string.replace('\n', '| ').replace('\r', '| ')
    # msg = "Univariate statistics: {us}".format(us=univar_string)

    minimum = grass.raster_info(raster)["min"]
    grass.debug(_("Minimum: {m}".format(m=minimum)))

    maximum = grass.raster_info(raster)["max"]
    grass.debug(_("Maximum: {m}".format(m=maximum)))

    if minimum is None or maximum is None:
        msg = "Minimum and maximum values of the <{raster}> map are 'None'.\n"
        msg += "=========================================== \n"
        msg += "Possible sources for this erroneous case are: "
        msg += "\n  - the <{raster}> map is empty "
        msg += "\n  - the MASK opacifies all non-NULL cells "
        msg += "\n  - the region is not correctly set\n"
        msg += "=========================================== "
        grass.fatal(_(msg.format(raster=raster)))

    normalisation = "float(({raster} - {minimum}) / ({maximum} - {minimum}))"
    normalisation = normalisation.format(
        raster=raster, minimum=minimum, maximum=maximum
    )

    # Maybe this can go in the parent function? 'raster' names are too long!
    # msg = "Normalization expression: "
    # msg += normalisation
    # grass.verbose(_(msg))

    normalisation_equation = EQUATION.format(
        result=output_name, expression=normalisation
    )
    grass.mapcalc(normalisation_equation, overwrite=True)
    get_univariate_statistics(output_name)


def zerofy_and_normalise_component(components, threshhold, output_name):
    """
    Sums up all maps listed in the given "components" object and derives a
    normalised output.

    To Do:

    * Improve `threshold` handling. What if threshholding is not desired? How
    to skip performing it?

    Parameters
    ----------
    components :
        Input list of raster maps (components)

    threshhold :
        Reference value for which to flatten all smaller raster pixel values to
        zero

    output_name :
        Name of output raster map

    Returns
    -------
    ...

    Examples
    --------
    ...
    """
    msg = " * Normalising sum of: "
    msg += ",".join(components)
    grass.debug(_(msg))
    grass.verbose(_(msg))

    if len(components) > 1:

        # prepare string for mapcalc expression
        components = [name.split("@")[0] for name in components]
        components_string = SPACY_PLUS.join(components)
        components_string = components_string.replace(" ", "")
        components_string = components_string.replace("+", "_")

        # temporary map names
        tmp_intermediate = temporary_filename(filename=components_string)
        tmp_output = temporary_filename(filename=components_string)

        # build mapcalc expression
        component_expression = SPACY_PLUS.join(components)
        component_equation = EQUATION.format(
            result=tmp_intermediate, expression=component_expression
        )

        grass.mapcalc(component_equation, overwrite=True)

    elif len(components) == 1:
        # temporary map names, if components contains one element
        tmp_intermediate = components[0]
        tmp_output = temporary_filename(filename=tmp_intermediate)

    if threshhold > THRESHHOLD_ZERO:
        msg = " * Setting values < {threshhold} in '{raster}' to zero"
        grass.verbose(msg.format(threshhold=threshhold, raster=tmp_intermediate))
        zerofy_small_values(tmp_intermediate, threshhold, tmp_output)

    else:
        tmp_output = tmp_intermediate

    # grass.verbose(_("Temporary map name: {name}".format(name=tmp_output)))
    grass.debug(_("Output map name: {name}".format(name=output_name)))
    # r.info(map=tmp_output, flags='gre')

    ### FIXME

    normalize_map(tmp_output, output_name)

    ### FIXME
