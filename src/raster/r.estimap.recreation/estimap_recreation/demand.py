from .grassy_utilities import (
    grass,
    g,
    r,
)
from .constants import (
    COLUMN_PREFIX_UNMET,
    EQUATION,
    METHODS,
    MOBILITY_COEFFICIENTS,
    MOBILITY_CONSTANT,
    MOBILITY_SCORE,
)
from .distance import build_distance_function
from .grassy_utilities import update_vector


def build_unmet_demand_expression(
    distance,
    constant,
    population,
    coefficients=MOBILITY_COEFFICIENTS[4],
    score=MOBILITY_SCORE,
    suitability=None,
    real_numbers=False,
):
    """
    Parameters
    ----------

    distance :
        Map of distance categories

    constant :
        Constant for the mobility function

    coefficients :
        A tuple with coefficients for the last distance category, as
        (the example) presented in the following table:

        |----------+---------+---------|
        | Distance | Kappa   | Alpha   |
        |----------+---------+---------|
        | >4       | 0.06930 | 0.00057 |
        |----------+---------+---------|

        Note, this is the last distance category. See also the
        mobility_function().

        Note, the Alpha coefficient, is signed with a '-' in the mobility
        function.

    population :
        A map with the distribution of the demand per distance category and
        predefined geometric boundaries (see `r.stats.zonal` deriving the
        'unmet demand' map ).

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
    distance_category = 4  # Hardcoded! FIXME

    kappa, alpha = coefficients
    unmet_demand_expression = build_distance_function(
        constant=constant, kappa=kappa, alpha=-alpha, variable=population, score=score
    )
    # suitability=suitability)  # Not used. Maybe it can, though,
    # after successfull testing its integration to
    # build_distance_function().

    msg = "Expression for distance category '{d}': {e}"
    msg = msg.format(d=distance_category, e=unmet_demand_expression)
    grass.debug(_(msg))

    # build expressions -- explicit: use the 'score' kwarg!
    expression = (
        "eval( unmet_demand = {expression},"
        " \\ \n distance = {distance} == {distance_category},"
        " \\ \n if( distance, unmet_demand,"
        " \\ \n null() ))"
    )
    if not real_numbers:
        expression = "round(" + expression + ")"
    grass.debug(_("Mapcalc expression: {e}".format(e=expression)))

    # replace keywords appropriately
    unmet_demand_expression = expression.format(
        expression=unmet_demand_expression,
        distance=distance,
        distance_category=distance_category,
    )

    msg = "Big expression (after formatting): {e}".format(e=unmet_demand_expression)
    grass.debug(_(msg))

    return unmet_demand_expression


def compute_unmet_demand(
    distance_categories_to_highest_spectrum,
    constant,
    coefficients,
    population,
    score,
    real_numbers,
    output_unmet_demand,
    vector_base_map=False,
    vector_methods=None,
    vector_column_prefix=None,
):
    """
    Parameters
    ----------
    distance_categories_to_highest_spectrum:
        Map of distance categories to areas of highest recreation spectrum

    constant:
        Constant for the mobility distance function

    coefficients :
        Set of coefficients for distance > 4 category, as
        (the example) presented in the following table:

        |----------+---------+---------|
        | Distance | Kappa   | Alpha   |
        |----------+---------+---------|
        | >4       | 0.06930 | 0.00057 |
        |----------+---------+---------|

    population:
        A map with the distribution of the demand per distance category and
        predefined geometric boundaries (see `r.stats.zonal` deriving the
        'demand' map ).

    score :
        A score value for the mobility function

    real_numbers :
        If real_numbers is False (which is the default), the mapcalc expression
        used to build the mobility function, will derive integer values.

    vector_base_map:
        A 'base' vector map to update with columns for unmet demand statistics

    vector_methods:
        Descriptive statistics for the `v.rast.stats` call--see update_vector()
        function

    vector_column_prefix:
        Prefix for 'unmet demand' columns added in the 'base' vector map

    Returns
    -------
    This function does not return anything
    """
    unmet_demand_expression = build_unmet_demand_expression(
        distance=distance_categories_to_highest_spectrum,
        constant=constant,
        coefficients=coefficients,
        population=population,
        score=score,
        real_numbers=real_numbers,
    )
    # suitability=suitability)  # Not used.
    # Maybe it can, though, after successfully testing its
    # integration to build_distance_function().

    msg = "*** Unmet demand function: {f}"
    grass.debug(_(msg.format(f=unmet_demand_expression)))

    unmet_demand_equation = EQUATION.format(
        result=output_unmet_demand, expression=unmet_demand_expression
    )
    r.mapcalc(unmet_demand_equation, overwrite=True)

    if vector_base_map:
        update_vector(
            vector=vector_base_map,
            raster=output_unmet_demand,
            methods=METHODS,
            column_prefix=COLUMN_PREFIX_UNMET,
        )


def compute_demand(
    base,
    population,
    method,
    output_demand,
    vector_base_map=None,
    vector_methods=None,
    vector_column_prefix=None,
):
    """ """
    r.stats_zonal(
        base=base,
        flags="r",
        cover=population,
        method=method,
        output=output_demand,
        overwrite=True,
        quiet=True,
    )

    # copy 'reclassed' as 'normal' map (r.mapcalc)
    # so as to enable removal of it and its 'base' map
    demand_copy = output_demand + "_copy"
    copy_expression = "{input_raster}"
    copy_expression = copy_expression.format(input_raster=output_demand)
    copy_equation = EQUATION.format(result=demand_copy, expression=copy_expression)
    r.mapcalc(copy_equation, overwrite=True)

    # remove reclassed map 'output_demand'
    # and rename 'copy' back to 'output_demand'
    g.remove(flags="f", type="raster", name=output_demand, quiet=True)
    g.rename(raster=(demand_copy, output_demand), quiet=True)

    if output_demand and vector_base_map:

        update_vector(
            vector=vector_base_map,
            raster=output_demand,
            methods=vector_methods,
            column_prefix=vector_column_prefix,
        )
