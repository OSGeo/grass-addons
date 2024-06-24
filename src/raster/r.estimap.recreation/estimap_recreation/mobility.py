"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import grass.script as grass
from .distance import build_distance_function


def mobility_function(
    distance,
    constant,
    coefficients,
    population,
    score,
    suitability=None,
    real_numbers=False,
):
    """
    The following 'mobility' function, is identical to the one used in
    `compute_attractiveness()`, excluding, however, the 'score' term:

        if(L10<>0,(1+$D$3)/($D$3+exp(-$E$3*L10))*52,0)

    Source: Excel file provided by the MAES Team, Land Resources, D3

    ------------------------------------------------------------------
    if L<>0; then
      # (1 + D) / (D + exp(-E * L)) * 52)

      #  D: Kappa
      # -E: Alpha -- Note the '-' sign in front of E
      #  L: Population (within boundary, within distance buffer)
    ------------------------------------------------------------------

    Parameters
    ----------

    distance :
        Map of distance categories

    constant :
        Constant for the mobility function

    coefficients :
        A dictionary with a set for coefficients for each distance category, as
        (the example) presented in the following table:

        |----------+---------+---------|
        | Distance | Kappa   | Alpha   |
        |----------+---------+---------|
        | 0 to 1   | 0.02350 | 0.00102 |
        |----------+---------+---------|
        | 1 to 2   | 0.02651 | 0.00109 |
        |----------+---------+---------|
        | 2 to 3   | 0.05120 | 0.00098 |
        |----------+---------+---------|
        | 3 to 4   | 0.10700 | 0.00067 |
        |----------+---------+---------|
        | >4       | 0.06930 | 0.00057 |
        |----------+---------+---------|

        Note, the last distance category is not considered in deriving the
        final "map of visits".

        Note, the Alpha coefficient, is signed with a '-' in the mobility
        function.

    population :
        A map with the distribution of the demand per distance category and
        predefined geometric boundaries (see `r.stats.zonal` deriving the
        'demand' map ).

    score :
        A score value for the mobility function

    suitability :
        [ NOTE: this argument is yet unused!  It is meant to be used only after
        successful integration of land suitability scores in
        build_distance_function(). ]
        If 'suitability' is given, it is used as a multiplication
        factor to the base equation.

    real_numbers :
        If real_numbers is False (which is the default), the mapcalc expression
        used to build the mobility function, will derive integer values.

    Returns
    -------

    mobility_expression :
        A valid mapcalc expression to compute the flow based on the
        predefined function `build_distance_function`.

    Examples
    --------
    ...
    """
    expressions = {}  # create a dictionary of expressions

    for distance_category, parameters in coefficients.items():
        kappa, alpha = parameters

        # Note, alpha gets a minus, that is: -alpha
        expressions[distance_category] = build_distance_function(
            constant=constant,
            kappa=kappa,
            alpha=-alpha,
            variable=population,
            score=score,
        )
        # suitability=suitability)  # Not used.
        # Maybe it can, though, after successfully testing its
        # integration to build_distance_function().

        grass.debug(_("For distance '{d}':".format(d=distance)))
        grass.debug(_(expressions[distance_category]))

    msg = "Expressions per distance category: {e}".format(e=expressions)
    grass.debug(_(msg))

    # build expressions -- explicit: use the'score' kwarg!
    expression = (
        "eval( mobility_0 = {expression_0},"
        " \\ \n mobility_1 = {expression_1},"
        " \\ \n mobility_2 = {expression_2},"
        " \\ \n mobility_3 = {expression_3},"
        " \\ \n distance_0 = {distance} == {distance_category_0},"
        " \\ \n distance_1 = {distance} == {distance_category_1},"
        " \\ \n distance_2 = {distance} == {distance_category_2},"
        " \\ \n distance_3 = {distance} == {distance_category_3},"
        " \\ \n if( distance_0, mobility_0,"
        " \\ \n if( distance_1, mobility_1,"
        " \\ \n if( distance_2, mobility_2,"
        " \\ \n if( distance_3, mobility_3,"
        " \\ \n null() )))))"
    )
    if not real_numbers:
        expression = "round(" + expression + ")"
    grass.debug(_("Mapcalc expression: {e}".format(e=expression)))

    # replace keywords appropriately
    # 'distance' is a map
    # 'distance_category' is a value
    # hence: 'distance' != 'distance_category'
    mobility_expression = expression.format(
        expression_0=expressions[0],
        expression_1=expressions[1],
        expression_2=expressions[2],
        expression_3=expressions[3],
        distance_category_0=0,
        distance_category_1=1,
        distance_category_2=2,
        distance_category_3=3,
        distance=distance,
    )
    # FIXME Make the above more elegant?

    msg = "Big expression (after formatting): {e}".format(e=expression)
    grass.debug(_(msg))

    return mobility_expression
