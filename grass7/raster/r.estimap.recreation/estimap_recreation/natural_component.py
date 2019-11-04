"""
@author Nikos Alexandris
"""

from .names import NATURAL_COMPONENT_NAME
from .messages import SCORING_PROTECTED_AREAS
from .grassy_utilities import (
    grass,
    recode_map,
)
from .colors import SCORE_COLORS
from .components import append_map_to_component


def build_natural_component(
        natural,
        protected,
        protected_scores,
        output_scored_protected_areas,
    ):
    """
    Build the natural component based on user defined maps for the 'natural'
    option, as well as the 'protected' option along with a predefined set of
    scores

    Parameters
    ----------

    natural :

    protected :

    protected_scores :

    Returns
    -------

    output_scored_protected_areas :

    """
    natural_component = []

    if natural:

        natural_component = natural.split(",")

    natural_components = []

    if protected:

        msg = SCORING_PROTECTED_AREAS
        grass.verbose(_(msg.format(protected=protected, rules=protected_scores)))

        recode_map(
            raster=protected,
            rules=protected_scores,
            colors=SCORE_COLORS,
            output=output_scored_protected_areas,
        )

        append_map_to_component(
            raster=output_scored_protected_areas,
            component_name=NATURAL_COMPONENT_NAME,
            component_list=natural_components,
        )

    # merge natural resources component related maps in one list
    natural_component += natural_components
    return natural_component
