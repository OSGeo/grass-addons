"""
@author Nikos Alexandris
"""

MESSAGE_PROCESSING = "\n>>> Processing..."
FATAL_MESSAGE_LAND_USE_DATATYPE = (
    "\n"
    "!!! The '{landuse}' input map "
    "should be a categorical one "
    "and of type 'CELL'. "
    "\nPerhaps you meant to use the 'land' input option instead?"
)
USING_SUITABILITY_SCORES_FROM_FILE = (
    " * Using suitability scores from file: {scores}."
)
USING_SUITABILITY_SCORES_FROM_INTERNAL_RULES = (
    " * Using internal rules to score land use classes in '{map}'"
)
USING_SUITABILITY_SCORES_FROM_STRING = (
    " * Using provided string of rules to score land use classes in {map}"
)
ATTEMPT_TO_USE_LAND_USE_FOR_AREAL_STATISTICS = (
    "\n!!! Land cover map 'landcover' not given. "
    "Attempt to use the '{landuse}' map to derive areal statistics"
)
USING_LAND_COVER_RECLASSIFICATION_RULES_FROM_FILE = (
    "* Using land cover reclassification rules from file: {rules}."
)
USING_INTERNAL_LAND_COVER_RECLASSIFICATION_RULES = (
    "* Using internal rules to reclassify the '{map}' map"
)
USING_LAND_COVER_RECLASSIFICATION_RULES_FROM_STRING = (
    "* Using provided string of rules to reclassify the '{map}' map"
)
MATCHING_COMPUTATIONAL_RESOLUTION = (
    "\n!!! Matching computational resolution to {raster}"
)
DERIVING_LAND_SUITABILITY = (
    "Deriving land suitability from '{landuse}' "
    "based on rules described in file '{rules}'"
)
FATAL_MESSAGE_MISSING_COASTLINE = (
    "The coastline map is required in order to "
    "compute attractiveness based on the "
    "coast geomorphology raster map"
)
FATAL_MESSAGE_MISSING_COAST_PROXIMITY = "No coast proximity"
MESSAGE_NORMALIZING = "\n>>> Normalizing '{component}' component\n"
WATER_COMPONENT_INCLUDES = '*** Water component includes currently: {component}'
SCORING_PROTECTED_AREAS = "Scoring protected areas '{protected}' based on '{rules}'"
POPULATION_STATISTICS = "iii Population statistics: {s}"
