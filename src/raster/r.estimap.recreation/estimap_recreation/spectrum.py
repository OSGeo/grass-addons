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

from .constants import EQUATION


def recreation_spectrum_expression(potential, opportunity):
    """
    Build and return a valid mapcalc expression for deriving
    the Recreation Opportunity Spectrum

    |-------------------------+-----+----------+------|
    | Potential / Opportunity | Far | Midrange | Near |
    |-------------------------+-----+----------+------|
    | Low                     | 1   | 2        | 3    |
    |-------------------------+-----+----------+------|
    | Moderate                | 4   | 5        | 6    |
    |-------------------------+-----+----------+------|
    | High                    | 7   | 8        | 9    |
    |-------------------------+-----+----------+------|

    Questions:

    - Why not use `r.cross`?
    - Use DUMMY strings for potential and opportunity raster map names?

    Parameters
    ----------
    potential :
        Map depicting potential for recreation

    opportunity :
        Map depicting opportunity for recreation

    Returns
    -------
    expression :
        A valid r.mapcalc expression

    Examples
    --------
    ...
    """
    expression = (
        " \\ \n if( {potential} == 1 && {opportunity} == 1, 1,"
        " \\ \n if( {potential} == 1 && {opportunity} == 2, 2,"
        " \\ \n if( {potential} == 1 && {opportunity} == 3, 3,"
        " \\ \n if( {potential} == 2 && {opportunity} == 1, 4,"
        " \\ \n if( {potential} == 2 && {opportunity} == 2, 5,"
        " \\ \n if( {potential} == 2 && {opportunity} == 3, 6,"
        " \\ \n if( {potential} == 3 && {opportunity} == 1, 7,"
        " \\ \n if( {potential} == 3 && {opportunity} == 2, 8,"
        " \\ \n if( {potential} == 3 && {opportunity} == 3, 9)))))))))"
    )

    expression = expression.format(potential=potential, opportunity=opportunity)

    msg = "*** Recreation Spectrum expression: \n"
    msg += expression
    grass.debug(msg)

    return expression


def compute_recreation_spectrum(potential, opportunity, spectrum):
    """
    Computes spectrum for recreation based on maps of potential and opportunity
    for recreation

    Parameters
    ----------
    potential :
        Name for input potential for recreation map

    opportunity :
        Name for input opportunity for recreation map

    Returns
    -------
    spectrum :
        Name for output spectrum of recreation map

    Examples
    --------
    ...
    """
    spectrum_expression = recreation_spectrum_expression(
        potential=potential, opportunity=opportunity
    )

    spectrum_equation = EQUATION.format(result=spectrum, expression=spectrum_expression)

    msg = "\n"
    msg += ">>> Recreation Spectrum equation: \n"
    msg += spectrum_equation
    grass.verbose(msg)

    grass.mapcalc(spectrum_equation, overwrite=True)

    return spectrum
