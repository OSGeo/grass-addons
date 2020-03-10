"""
@author Nikos Alexandris
"""

from .constants import (
    SUITABILITY_SCORES,
    URBAN_ATLAS_TO_MAES_NOMENCLATURE,
)
from .colors import (
    SCORE_COLORS,
)
from .messages import (
    FATAL_MESSAGE_LAND_USE_DATATYPE,
    USING_SUITABILITY_SCORES_FROM_FILE,
    USING_SUITABILITY_SCORES_FROM_INTERNAL_RULES,
    USING_SUITABILITY_SCORES_FROM_STRING,
    ATTEMPT_TO_USE_LAND_USE_FOR_AREAL_STATISTICS,
    USING_LAND_COVER_RECLASSIFICATION_RULES_FROM_FILE,
    USING_INTERNAL_LAND_COVER_RECLASSIFICATION_RULES,
    USING_LAND_COVER_RECLASSIFICATION_RULES_FROM_STRING,
    DERIVING_LAND_SUITABILITY,
)
from .names import (
    LAND_COMPONENT_NAME,
)
from .grassy_utilities import (
    grass,
    recode_map,
    remove_files_at_exit,
    temporary_filename,
    string_to_file,
)
from .components import (
    append_map_to_component,
)

def build_land_component(
        landuse,
        suitability_scores,
        landcover,
        landcover_reclassification_rules,
        maes_ecosystem_types,
        land,
    ):
    """

    Parameters
    ----------

    landuse :
        Land use map

    suitability_scores :
        Scores for each land use class (category, in GRASS GIS' terminology)

    landcover :
        Land cover map

    landcover_reclassification_rules :
        Reclassification rules for land cover map

    maes_ecosystem_types :
        MAES ecosystem types (classes)

    land :
        The user-fed 'land' input map(s) option

    Returns
    -------

    land_component :
        The 'land' component

    """
    land_component = []  # a list, use .extend() wherever required

    if landuse:
        # Check datatype: a land use map should be categorical, i.e. of type CELL
        landuse_datatype = grass.raster.raster_info(landuse)["datatype"]
        if landuse_datatype != "CELL":
            grass.fatal(_(FATAL_MESSAGE_LAND_USE_DATATYPE.format(landuse=landuse)))

    if (
        landuse
        and suitability_scores
        and ":" not in suitability_scores
    ):

        msg = USING_SUITABILITY_SCORES_FROM_FILE.format(scores=suitability_scores)
        grass.verbose(_(msg))

    suitability_map_name = temporary_filename(filename="suitability")

    if (
        landuse
        and not suitability_scores
    ):
        msg = USING_SUITABILITY_SCORES_FROM_INTERNAL_RULES.format(map=landuse)
        grass.warning(_(msg))

        temporary_suitability_map_name = temporary_filename(filename=suitability_map_name)
        suitability_scores = string_to_file(
            SUITABILITY_SCORES, filename=temporary_suitability_map_name
        )
        remove_files_at_exit(suitability_scores)

    if (
        landuse
        and suitability_scores
        and ":" in suitability_scores
    ):
        msg = USING_SUITABILITY_SCORES_FROM_STRING.format(map=landuse)
        grass.verbose(_(msg))
        temporary_suitability_map_name = temporary_filename(filename=suitability_map_name)
        suitability_scores = string_to_file(
            suitability_scores, filename=temporary_suitability_map_name
        )
        remove_files_at_exit(suitability_scores)

    # FIXME -----------------------------------------------------------------

    # Use one landcover input if supply is requested
    # Use one set of land cover reclassification rules

    if not landcover and landuse:

        landcover = landuse
        msg = ATTEMPT_TO_USE_LAND_USE_FOR_AREAL_STATISTICS.format(landuse=landuse)
        grass.warning(_(msg))

    # if 'land_classes' is a file
    if (
        landcover
        and landcover_reclassification_rules
        and ":" not in landcover_reclassification_rules
    ):
        msg = USING_LAND_COVER_RECLASSIFICATION_RULES_FROM_FILE
        msg = msg.format(rules=landcover_reclassification_rules)
        grass.verbose(_(msg))

    # if 'land_classes' not given
    if landcover and not landcover_reclassification_rules:

        # if 'landcover' is not the MAES land cover,
        # then use internal reclassification rules
        # how to test:
        # 1. landcover is not a "MAES" land cover
        # 2. landcover is an Urban Atlas one?

        msg = USING_INTERNAL_LAND_COVER_RECLASSIFICATION_RULES.format(map=landcover)
        grass.verbose(_(msg))

        temporary_maes_ecosystem_types = temporary_filename(filename=maes_ecosystem_types)
        landcover_reclassification_rules = string_to_file(
            URBAN_ATLAS_TO_MAES_NOMENCLATURE, filename=maes_ecosystem_types
        )
        remove_files_at_exit(landcover_reclassification_rules)

        # if landcover is a "MAES" land cover, no need to reclassify!

    if (
        landuse
        and landcover_reclassification_rules
        and ":" in landcover_reclassification_rules
    ):
        msg = USING_LAND_COVER_RECLASSIFICATION_RULES_FROM_STRING.format(map=landcover)
        grass.verbose(_(msg))
        temporary_maes_land_classes = temporary_filename(filename=maes_land_classes)
        landcover_reclassification_rules = string_to_file(
            landcover_reclassification_rules, filename=maes_land_classes
        )
        remove_files_at_exit(landcover_reclassification_rules)

    # FIXME -----------------------------------------------------------------

    if land:

        land_component = land.split(",")

    if landuse and suitability_scores:

        msg = DERIVING_LAND_SUITABILITY
        grass.verbose(msg.format(landuse=landuse, rules=suitability_scores))

        # suitability is the 'suitability_map_name'
        recode_map(
            raster=landuse,
            rules=suitability_scores,
            colors=SCORE_COLORS,
            output=suitability_map_name,
        )

        append_map_to_component(
            raster=suitability_map_name,
            component_name=LAND_COMPONENT_NAME,
            component_list=land_component,
        )

    return land_component
