"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from .constants import EQUATION


def artificial_accessibility_expression(artificial_proximity, roads_proximity):
    r"""
        Build an r.mapcalc compatible expression to compute accessibility to
        artificial surfaces based on the following accessibility classification
        rules for artificial surfaces:

    |-------------------+-------+------------+-------------+--------------+---------|
    | Anthropic \ Roads | < 500 | 500 - 1000 | 1000 - 5000 | 5000 - 10000 | > 10000 |
    |-------------------+-------+------------+-------------+--------------+---------|
    | < 500             | 1     | 1          | 2           | 3            | 4       |
    |-------------------+-------+------------+-------------+--------------+---------|
    | 500 - 1000        | 1     | 1          | 2           | 3            | 4       |
    |-------------------+-------+------------+-------------+--------------+---------|
    | 1000 - 5000       | 2     | 2          | 2           | 4            | 5       |
    |-------------------+-------+------------+-------------+--------------+---------|
    | 5000 - 10000      | 3     | 3          | 4           | 5            | 5       |
    |-------------------+-------+------------+-------------+--------------+---------|
    | > 10000           | 3     | 4          | 4           | 5            | 5       |
    |-------------------+-------+------------+-------------+--------------+---------|

        Parameters
        ----------
        artificial :
            Proximity to artificial surfaces

        roads :
            Proximity to roads

        Returns
        -------
        expression
            Valid r.mapcalc expression


        Examples
        --------
        ...
    """
    expression = (
        "if( {artificial} <= 2 && {roads} <= 2, 1,"
        " \\ \n if( {artificial} == 1 && {roads} == 3, 2,"
        " \\ \n if( {artificial} == 2 && {roads} == 3, 2,"
        " \\ \n if( {artificial} == 3 && {roads} <= 3, 2,"
        " \\ \n if( {artificial} <= 2 && {roads} == 4, 3,"
        " \\ \n if( {artificial} == 4 && {roads} == 2, 3,"
        " \\ \n if( {artificial} >= 4 && {roads} == 1, 3,"
        " \\ \n if( {artificial} <= 2 && {roads} == 5, 4,"
        " \\ \n if( {artificial} == 3 && {roads} == 4, 4,"
        " \\ \n if( {artificial} >= 4 && {roads} == 3, 4,"
        " \\ \n if( {artificial} == 5 && {roads} == 2, 4,"
        " \\ \n if( {artificial} >= 3 && {roads} == 5, 5,"
        " \\ \n if( {artificial} >= 4 && {roads} == 4, 5)))))))))))))"
    )

    expression = expression.format(
        artificial=artificial_proximity, roads=roads_proximity
    )
    return expression


def compute_artificial_accessibility(
    artificial_proximity, roads_proximity, output_name=None
):
    """Compute artificial proximity

    Parameters
    ----------
    artificial_proximity :
        Artificial surfaces...

    roads_proximity :
        Road infrastructure

    output_name :
        Name to pass to temporary_filename() to create a temporary map name

    Returns
    -------
    output :
        ...

    Examples
    --------
    ...
    """
    artificial = grass.find_file(name=artificial_proximity, element="cell")
    if not artificial["file"]:
        grass.fatal("Raster map {name} not found".format(name=artificial_proximity))

    roads = grass.find_file(name=roads_proximity, element="cell")
    if not roads["file"]:
        grass.fatal("Raster map {name} not found".format(name=roads_proximity))

    accessibility_expression = artificial_accessibility_expression(
        artificial_proximity, roads_proximity
    )
    # temporary maps will be removed!
    if output_name:
        tmp_output = temporary_filename(filename=output_name)
    else:
        basename = "artificial_accessibility"
        tmp_output = temporary_filename(filename=basename)

    accessibility_equation = EQUATION.format(
        result=tmp_output, expression=accessibility_expression
    )

    msg = "* Equation for proximity to artificial areas: \n"
    msg += accessibility_equation
    grass.verbose(msg)

    grass.verbose(_("* Computing accessibility to artificial surfaces"))
    grass.mapcalc(accessibility_equation, overwrite=True)

    return tmp_output
