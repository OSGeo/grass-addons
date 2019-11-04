"""
@author Nikos Alexandris
"""

from .constants import (
    EUCLIDEAN,
    NEIGHBORHOOD_METHOD,
    NEIGHBORHOOD_SIZE,
    WATER_PROXIMITY_CONSTANT,
    WATER_PROXIMITY_ALPHA,
    WATER_PROXIMITY_KAPPA,
    WATER_PROXIMITY_SCORE,
)
from .names import WATER_COMPONENT_NAME
from .messages import (
    FATAL_MESSAGE_MISSING_COASTLINE,
    FATAL_MESSAGE_MISSING_COAST_PROXIMITY,
    WATER_COMPONENT_INCLUDES,
)
from .utilities import get_coefficients
from .grassy_utilities import grass
from .distance import (
    compute_attractiveness,
    neighborhood_function,
)
from .components import append_map_to_component

def build_water_component(
        water,
        lakes,
        lakes_coefficients,
        coastline,
        coast_geomorphology,
        bathing_water,
        bathing_water_coefficients,
    ):
    """
    Build and return the 'water' component
    """

    water_component = []
    water_components = []

    if water:

        water_component = water.split(",")
        msg = WATER_COMPONENT_INCLUDES.format(component=water_component)
        grass.debug(_(msg))
        # grass.verbose(_(msg))

    if lakes:

        if lakes_coefficients:
            metric, constant, kappa, alpha, score = get_coefficients(lakes_coefficients)

        lakes_proximity = compute_attractiveness(
            raster=lakes,
            metric=EUCLIDEAN,
            constant=constant,
            kappa=kappa,
            alpha=alpha,
            score=score,
            mask=lakes,
        )

        append_map_to_component(
            raster=lakes_proximity,
            component_name=WATER_COMPONENT_NAME,
            component_list=water_components,
        )

    if coastline:

        coast_proximity = compute_attractiveness(
            raster=coastline,
            metric=EUCLIDEAN,
            constant=WATER_PROXIMITY_CONSTANT,
            alpha=WATER_PROXIMITY_ALPHA,
            kappa=WATER_PROXIMITY_KAPPA,
            score=WATER_PROXIMITY_SCORE,
        )

        append_map_to_component(
            raster=coast_proximity,
            component_name=WATER_COMPONENT_NAME,
            component_list=water_components,
        )

    if coast_geomorphology:

        try:

            if not coastline:
                grass.fatal(_(FATAL_MESSAGE_MISSING_COASTLINE))

        except NameError:
            grass.fatal(_(FATAL_MESSAGE_MISSING_COAST_PROXIMITY))

        coast_attractiveness = neighborhood_function(
            raster=coast_geomorphology,
            method=NEIGHBORHOOD_METHOD,
            size=NEIGHBORHOOD_SIZE,
            distance_map=coast_proximity,
        )

        append_map_to_component(
            raster=coast_attractiveness,
            component_name=WATER_COMPONENT_NAME,
            component_list=water_components,
        )

    if bathing_water:

        if bathing_water_coefficients:
            metric, constant, kappa, alpha = get_coefficients(
                bathing_water_coefficients
            )

        bathing_water_proximity = compute_attractiveness(
            raster=bathing_water,
            metric=EUCLIDEAN,
            constant=constant,
            kappa=kappa,
            alpha=alpha,
        )

        append_map_to_component(
            raster=bathing_water_proximity,
            component_name=WATER_COMPONENT_NAME,
            component_list=water_components,
        )

    # merge water component related maps in one list
    water_component += water_components

    return water_component
