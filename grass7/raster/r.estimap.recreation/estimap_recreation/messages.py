INFRASTRUCTURE_NOT_REQUIRED = (
    "Infrastructure is not required "
    "to derive the 'potential' recreation map."
)
COMPUTING_INTERMEDIATE_POTENTIAL_MAP = "\n>>> Computing intermediate potential map"
COMPUTING_INTERMEDIATE_OPPORTUNITY_MAP = "*** Computing intermediate opportunity map '{opportunity}'"
CLASSIFYING_POTENTIAL_MAP = "\n>>> Classifying '{potential}' map"
CLASSIFYING_OPPORTUNITY_MAP = "* Classifying '{opportunity}' map"
WRITING_SPECTRUM_MAP = "* Writing '{spectrum}' map"
MOBILITY_FUNCTION = "*** Mobility function: {f}"
MESSAGE_PROCESSING = "\n>>> Processing..."
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
MESSAGE_NORMALISING = "\n>>> Normalising '{component}' component\n"
ZEROFY_NULL_CELLS = "*** Setting NULL cells to 0"
ADDING_MAP_TO_COMPONENT = "* Adding '{raster}' map to '{component}' component\n"
WATER_COMPONENT_INCLUDES = '*** Water component includes currently: {component}'
SCORING_PROTECTED_AREAS = "Scoring protected areas '{protected}' based on '{rules}'"
POPULATION_STATISTICS = "iii Population statistics: {s}"
FATAL_MESSAGE_LAND_USE_DATATYPE = (
    "\n"
    "!!! The '{landuse}' input map "
    "should be a categorical one "
    "and of type 'CELL'. "
    "\nPerhaps you meant to use the 'land' input option instead?"
)
FATAL_MESSAGE_MISSING_COASTLINE = (
    "The coastline map is required in order to "
    "compute attractiveness based on the "
    "coast geomorphology raster map"
)
FATAL_MESSAGE_MISSING_COAST_PROXIMITY = "No coast proximity"
FILE_NOT_FOUND = ">>> File '{f}' not found! "
