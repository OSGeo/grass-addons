"""
@author Nikos Alexandris
"""

from .grassy_utilities import (
    grass,
    r,
    remove_map_at_exit,
    temporary_filename,
)
from .constants import (
    EQUATION,
    THRESHHOLD_ZERO,
)
from .messages import (
    MESSAGE_NORMALISING,
    ADDING_MAP_TO_COMPONENT,
    ZEROFY_NULL_CELLS,
)
from .names import (
    LAND_COMPONENT,
    LAND_COMPONENT_MAP_NAME,
    RECREATION_POTENTIAL_COMPONENT,
)
from .components import smooth_component
from .normalisation import zerofy_and_normalise_component


def zerofy_null_cells(raster_map):
    """
    This function sets NULL cells of a raster map to 0.

    Notes
    -----
    `r.null` operates always (currently?) on the complete input raster map.
    To ensure that it's output will be restricted within the current extent of
    the computational region, it is required to isubset it manually!
    Else, and in case the input raster map is larger than the computational
    region, the output of `r.null` will be larger too.
    """
    temporary_raster_map = temporary_filename(filename=raster_map)
    subset_raster_map = EQUATION.format(
        result=temporary_raster_map,
        expression=raster_map,
    )
    r.mapcalc(subset_raster_map)
    grass.debug(_(ZEROFY_NULL_CELLS))
    r.null(map=temporary_raster_map, null=0)
    return temporary_raster_map


def zerofy_component_null_cells(component):
    """
    Give a 'better' name to this helper function!
    """
    for dummy_index in component:
        land_map = component.pop(0)  # remove 'map' from 'land_component'
        suitability_map = zerofy_null_cells(land_map)  # process it
        msg = ADDING_MAP_TO_COMPONENT.format(
            raster=suitability_map,
            component=RECREATION_POTENTIAL_COMPONENT,
        )
        grass.verbose(_(msg))
        component.append(suitability_map)  # add back to 'land_component'
    return component


def normalise_land_component(land_component):
    """This function normalises the land component.

    Parameters
    ----------

    land_component :
        The land component

    Returns
    -------
        This function does not return anything

    Examples
    --------
        >>> normalise_land_component(land_component, recreation_potential_component)
    """
    remove_map_at_exit(land_component)
    zerofy_component_null_cells(land_component)
    if len(land_component) > 1:
        grass.verbose(_(MESSAGE_NORMALISING.format(component=LAND_COMPONENT)))
        land_component_map_name = temporary_filename(filename=LAND_COMPONENT_MAP_NAME)
        zerofy_and_normalise_component(
            land_component,
            THRESHHOLD_ZERO,
            land_component_map_name,
        )
    return land_component
