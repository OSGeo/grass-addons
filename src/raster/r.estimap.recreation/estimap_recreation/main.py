"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import atexit
import os

from .constants import (
    CITATION_RECREATION_POTENTIAL,
    COLUMN_PREFIX_SPECTRUM,
    COLUMN_PREFIX_DEMAND,
    COLUMN_PREFIX_UNMET,
    COLUMN_PREFIX_FLOW,
    EQUATION,
    HIGHEST_RECREATION_CATEGORY,
    METHODS,
    MOBILITY_COEFFICIENTS,
    MOBILITY_CONSTANT,
    MOBILITY_SCORE,
    RECREATION_OPPORTUNITY_CATEGORIES,
    RECREATION_POTENTIAL_CATEGORIES,
    THRESHHOLD_0001,
    THRESHHOLD_ZERO,
)
from .messages import (
    CLASSIFYING_POTENTIAL_MAP,
    CLASSIFYING_OPPORTUNITY_MAP,
    COMPUTING_INTERMEDIATE_POTENTIAL_MAP,
    COMPUTING_INTERMEDIATE_OPPORTUNITY_MAP,
    WRITING_SPECTRUM_MAP,
    FILE_NOT_FOUND,
    INFRASTRUCTURE_NOT_REQUIRED,
    MESSAGE_PROCESSING,
    MATCHING_COMPUTATIONAL_RESOLUTION,
    MESSAGE_NORMALISING,
    MOBILITY_FUNCTION,
    POPULATION_STATISTICS,
)
from .names import (
    WATER_COMPONENT,
    NATURAL_COMPONENT,
    SCORED_PROTECTED_AREAS_MAP_NAME,
    RECREATION_POTENTIAL_TITLE,
    RECREATION_OPPORTUNITY_COMPONENT,
    RECREATION_OPPORTUNITY_TITLE,
    RECREATION_SPECTRUM_TITLE,
    MAES_ECOSYSTEM_TYPES_MAP_TITLE,
)
from .labels import (
    POTENTIAL_CATEGORY_LABELS,
    OPPORTUNITY_CATEGORY_LABELS,
    SPECTRUM_CATEGORY_LABELS,
    SPECTRUM_DISTANCE_CATEGORY_LABELS,
)
from .colors import (
    SCORE_COLORS,
    POTENTIAL_COLORS,
    OPPORTUNITY_COLORS,
    SPECTRUM_COLORS,
)
from .grassy_utilities import (
    grass,
    g,
    r,
    remove_map_at_exit,
    remove_files_at_exit,
    temporary_filename,
    remove_temporary_maps,
    string_to_file,
    get_univariate_statistics,
    recode_map,
    update_meta,
    export_map,
    update_vector,
)
from .distance import (
    compute_artificial_proximity,
)
from .normalisation import zerofy_and_normalise_component
from .normalise_land import normalise_land_component
from .accessibility import compute_artificial_accessibility
from .spectrum import compute_recreation_spectrum
from .components import (
    smooth_component,
    classify_recreation_component,
)
from .land_component import build_land_component
from .water_component import build_water_component
from .natural_component import build_natural_component
from .infrastructure_component import build_infrastructure_component
from .mobility import mobility_function
from .demand import (
    compute_demand,
    compute_unmet_demand,
)
from .supply_and_use import compute_supply


def main(options, flags):
    """
    Main program
    """

    # remove temporary maps unless -s is passed
    atexit.register(lambda: remove_temporary_maps(save_temporary_maps=flags["s"]))

    info = flags["i"]
    real_numbers = flags["r"]
    average_filter = flags["f"]
    landuse_extent = flags["e"]
    print_only = flags["p"]

    timestamp = options["timestamp"]

    metric = options["metric"]
    units = options["units"]
    if len(units) > 1:
        units = units.split(",")

    """names for input, output, output suffix, options"""

    if options["region"]:
        # QGIS sets the maximum bounding box covering all input raster maps,
        # and the coarsest resolution of all maps, as the computational region
        # in the Location/Mapset where processing takes place.
        #
        # We fix this by requiring the user (in the QGIS Plugin *only*) to set the
        # computational region from a raster map of his choice.
        # GRASS GIS users don't need to use this option.
        g.region(raster=options["region"], quiet=False)

    mask = options["mask"]

    """
    following some hard-coded names -- review and remove!
    """

    land = options["land"].split("@")[0]

    water = options["water"].split("@")[0]
    water_component_map_name = temporary_filename(filename="water_component")

    natural = options["natural"].split("@")[0]
    natural_component_map_name = temporary_filename(filename="natural_component")

    infrastructure = options["infrastructure"].split("@")[0]
    infrastructure_component_map_name = temporary_filename(
        filename="infrastructure_component"
    )

    """Processing"""

    grass.verbose(_(MESSAGE_PROCESSING))

    """Land components"""

    landuse = options["landuse"]
    suitability_scores = options["suitability_scores"]
    landcover = options["landcover"]
    landcover_reclassification_rules = options["land_classes"]

    # if the given 'rules' file(name) does not exist
    if landcover_reclassification_rules and not os.path.exists(
        landcover_reclassification_rules
    ):
        missing_absolute_filename = os.path.abspath(landcover_reclassification_rules)
        raise ValueError(FILE_NOT_FOUND.format(f=missing_absolute_filename))

    """Water components"""

    lakes = options["lakes"]
    lakes_coefficients = options["lakes_coefficients"]
    coastline = options["coastline"]
    coast_geomorphology = options["coast_geomorphology"]
    bathing_water = options["bathing_water"]
    bathing_water_coefficients = options["bathing_coefficients"]
    bathing_water_proximity_map_name = "bathing_water_proximity"

    """Natural components"""

    protected = options["protected"]
    protected_scores = options["protected_scores"]

    """Artificial areas"""

    artificial = options["artificial"]
    artificial_distance_categories = options["artificial_distances"]
    roads = options["roads"]
    roads_distance_categories = options["roads_distances"]

    """Aggregational boundaries"""

    base = options["base"]
    base_vector = options["base_vector"]
    aggregation = options["aggregation"]

    """Population"""

    population = options["population"]
    if population:
        population_ns_resolution = grass.raster_info(population)["nsres"]
        population_ew_resolution = grass.raster_info(population)["ewres"]

    """Outputs"""

    potential_title = RECREATION_POTENTIAL_TITLE
    recreation_potential = options["potential"]  # intermediate / output
    recreation_potential_map_name = temporary_filename(filename="recreation_potential")

    opportunity_title = RECREATION_OPPORTUNITY_TITLE
    recreation_opportunity = options["opportunity"]
    recreation_opportunity_map_name = temporary_filename(
        filename="recreation_opportunity"
    )

    spectrum_title = RECREATION_SPECTRUM_TITLE
    # if options['spectrum']:
    recreation_spectrum = options["spectrum"]  # output
    # else:
    #     recreation_spectrum = 'recreation_spectrum'
    # recreation_spectrum_component_map_name =
    #       temporary_filename(filename='recreation_spectrum_component_map')

    spectrum_distance_categories = options["spectrum_distances"]
    if ":" in spectrum_distance_categories:
        temporary_recreation_spectrum = temporary_filename(filename=recreation_spectrum)
        spectrum_distance_categories = string_to_file(
            spectrum_distance_categories, filename=temporary_recreation_spectrum
        )
        remove_files_at_exit(spectrum_distance_categories)

    highest_spectrum = "highest_recreation_spectrum"
    crossmap = "crossmap"  # REMOVEME

    demand = options["demand"]
    unmet_demand = options["unmet"]

    flow = options["flow"]
    # Name for the 'flow' map
    flow_map_name = temporary_filename(filename="flow")
    #     Required when the 'flow' input option is not defined by the user, yet
    #     some of the requested outputs require first the production of the
    #     'flow' map. An example is the request for a supply table without
    #     requesting the 'flow' map itself.

    supply = options["supply"]  # use as CSV filename prefix
    use = options["use"]  # use as CSV filename prefix

    """ First, care about the computational region"""

    if mask:
        msg = " * Masking NULL cells based on '{mask}'".format(mask=mask)
        grass.verbose(_(msg))
        r.mask(raster=mask, overwrite=True, quiet=True)

    if landuse_extent:
        g.message(_(MATCHING_COMPUTATIONAL_RESOLUTION.format(raster=landuse)))
        grass.use_temp_region()  # modify the region safely
        g.region(flags="p", raster=landuse)  # set region to 'landuse'

    """Land Component
            or Suitability of Land to Support Recreation Activities (SLSRA)"""
    maes_ecosystem_types = "maes_ecosystem_types"
    land_component = build_land_component(
        landuse=landuse,
        suitability_scores=suitability_scores,
        landcover=landcover,
        landcover_reclassification_rules=landcover_reclassification_rules,
        maes_ecosystem_types=maes_ecosystem_types,
        land=land,
    )

    """Water Component"""
    water_component = build_water_component(
        water=water,
        lakes=lakes,
        lakes_coefficients=lakes_coefficients,
        coastline=coastline,
        coast_geomorphology=coast_geomorphology,
        bathing_water=bathing_water,
        bathing_water_coefficients=bathing_water_coefficients,
    )

    """Natural Component"""
    natural_component = build_natural_component(
        natural=natural,
        protected=protected,
        protected_scores=protected_scores,
        output_scored_protected_areas=SCORED_PROTECTED_AREAS_MAP_NAME,
    )

    """ Normalize land, water, natural inputs
    and add them to the recreation potential component"""

    recreation_potential_component = []

    normalised_land_component = normalise_land_component(land_component=land_component)
    if normalise_land_component and average_filter:
        smooth_component(
            normalise_land_component,
            method="average",
            size=7,
        )
    recreation_potential_component.extend(normalised_land_component)

    """Water"""
    if len(water_component) > 1:
        grass.verbose(_(MESSAGE_NORMALISING.format(component=WATER_COMPONENT)))
        zerofy_and_normalise_component(
            water_component,
            THRESHHOLD_ZERO,
            water_component_map_name,
        )
        recreation_potential_component.append(water_component_map_name)
    else:
        recreation_potential_component.extend(water_component)

    remove_map_at_exit(water_component_map_name)

    """Natural"""
    if len(natural_component) > 1:
        grass.verbose(_(MESSAGE_NORMALISING.format(component=NATURAL_COMPONENT)))
        zerofy_and_normalise_component(
            components=natural_component,
            threshhold=THRESHHOLD_ZERO,
            output_name=natural_component_map_name,
        )
        recreation_potential_component.append(natural_component_map_name)
    else:
        recreation_potential_component.extend(natural_component)

    if natural_component and average_filter:
        smooth_component(natural_component, method="average", size=7)

    remove_map_at_exit(natural_component_map_name)

    """ Recreation Potential [Output] """
    tmp_recreation_potential = temporary_filename(
        filename=recreation_potential_map_name
    )

    msg = COMPUTING_INTERMEDIATE_POTENTIAL_MAP
    grass.verbose(_(msg.format(potential=tmp_recreation_potential)))
    grass.debug(_("*** Maps: {maps}".format(maps=recreation_potential_component)))

    zerofy_and_normalise_component(
        components=recreation_potential_component,
        threshhold=THRESHHOLD_ZERO,
        output_name=tmp_recreation_potential,
    )

    # recode recreation_potential
    tmp_recreation_potential_categories = temporary_filename(
        filename=recreation_potential
    )

    msg = CLASSIFYING_POTENTIAL_MAP.format(potential=tmp_recreation_potential)
    grass.verbose(_(msg))

    classify_recreation_component(
        component=tmp_recreation_potential,
        rules=RECREATION_POTENTIAL_CATEGORIES,
        output_name=tmp_recreation_potential_categories,
    )

    if recreation_potential:

        # export 'recreation_potential' map and
        # use 'output_name' for the temporary 'potential' map for spectrum
        tmp_recreation_potential_categories = export_map(
            input_name=tmp_recreation_potential_categories,
            title=potential_title,
            categories=POTENTIAL_CATEGORY_LABELS,
            colors=POTENTIAL_COLORS,
            output_name=recreation_potential,
            timestamp=timestamp,
        )

    # Infrastructure to access recreational facilities, amenities, services
    # Required for recreation opportunity and successively recreation spectrum

    if infrastructure and not any(
        [recreation_opportunity, recreation_spectrum, demand, flow, supply]
    ):
        grass.warning(_(INFRASTRUCTURE_NOT_REQUIRED))

    if any([recreation_opportunity, recreation_spectrum, demand, flow, supply]):

        infrastructure_component = build_infrastructure_component(
            infrastructure=infrastructure,
            artificial=artificial,
            roads=roads,
            roads_distance_categories=roads_distance_categories,
            roads_proximity_map_name="roads_proximity",
            artificial_distance_categories=artificial_distance_categories,
            artificial_proximity_map_name="artificial_proximity",
            artificial_accessibility_map_name="artificial_accessibility",
        )

    # # Recreational facilities, amenities, services

    # recreation_component = []
    # recreation_components = []

    # if recreation:
    #     recreation_component.append(recreation)

    # # merge recreation component related maps in one list
    # recreation_component += recreation_components

    """ Recreation Spectrum """

    if any([recreation_spectrum, demand, flow, supply]):

        recreation_opportunity_component = []

        # input
        zerofy_and_normalise_component(
            components=infrastructure_component,
            threshhold=THRESHHOLD_ZERO,
            output_name=infrastructure_component_map_name,
        )

        recreation_opportunity_component.append(infrastructure_component_map_name)

        # # input
        # zerofy_and_normalise_component(recreation_component,
        #         THRESHHOLD_0001, recreation_component_map_name)
        # recreation_opportunity_component.append(recreation_component_map_name)
        # remove_map_at_exit(recreation_component_map_name)

        # intermediate

        # REVIEW --------------------------------------------------------------
        tmp_recreation_opportunity = temporary_filename(
            filename=recreation_opportunity_map_name
        )
        msg = COMPUTING_INTERMEDIATE_OPPORTUNITY_MAP
        grass.debug(_(msg.format(opportunity=tmp_recreation_opportunity)))

        grass.verbose(
            _(MESSAGE_NORMALISING.format(component=RECREATION_OPPORTUNITY_COMPONENT))
        )
        grass.debug(_("*** Maps: {maps}".format(maps=recreation_opportunity_component)))

        zerofy_and_normalise_component(
            components=recreation_opportunity_component,
            threshhold=THRESHHOLD_0001,
            output_name=tmp_recreation_opportunity,
        )

        # Why threshhold 0.0003? How and why it differs from 0.0001?
        # -------------------------------------------------------------- REVIEW

        msg = CLASSIFYING_OPPORTUNITY_MAP
        grass.verbose(msg.format(opportunity=recreation_opportunity_map_name))

        # recode opportunity_component
        tmp_recreation_opportunity_categories = temporary_filename(
            filename=recreation_opportunity
        )
        classify_recreation_component(
            component=tmp_recreation_opportunity,
            rules=RECREATION_OPPORTUNITY_CATEGORIES,
            output_name=tmp_recreation_opportunity_categories,
        )

        """ Recreation Opportunity [Output]"""

        if recreation_opportunity:

            # export 'recreation_opportunity' map and
            # use 'output_name' for the temporary 'potential' map for spectrum
            tmp_recreation_opportunity_categories = export_map(
                input_name=tmp_recreation_opportunity_categories,
                title=opportunity_title,
                categories=OPPORTUNITY_CATEGORY_LABELS,
                colors=OPPORTUNITY_COLORS,
                output_name=recreation_opportunity,
                timestamp=timestamp,
            )

        # Recreation Spectrum: Potential + Opportunity [Output]

        if not recreation_spectrum and any([demand, flow, supply]):
            recreation_spectrum = temporary_filename(filename="recreation_spectrum")
            remove_map_at_exit(recreation_spectrum)

        recreation_spectrum = compute_recreation_spectrum(
            potential=tmp_recreation_potential_categories,
            opportunity=tmp_recreation_opportunity_categories,
            spectrum=recreation_spectrum,
        )

        msg = WRITING_SPECTRUM_MAP.format(spectrum=recreation_spectrum)
        grass.verbose(_(msg))
        get_univariate_statistics(recreation_spectrum)

        # get category labels
        temporary_spectrum_categories = temporary_filename(
            filename="categories_of_" + recreation_spectrum
        )
        spectrum_category_labels = string_to_file(
            SPECTRUM_CATEGORY_LABELS,
            filename=temporary_spectrum_categories,
        )
        remove_files_at_exit(spectrum_category_labels)

        # update category labels, meta and colors
        r.category(
            map=recreation_spectrum,
            rules=spectrum_category_labels,
            separator=":",
        )
        update_meta(recreation_spectrum, spectrum_title)
        r.colors(
            map=recreation_spectrum,
            rules="-",
            stdin=SPECTRUM_COLORS,
            quiet=True,
        )

        if base_vector:

            update_vector(
                vector=base_vector,
                raster=recreation_spectrum,
                methods=METHODS,
                column_prefix=COLUMN_PREFIX_SPECTRUM,
            )

    """Valuation Tables"""

    if any([demand, flow, supply, aggregation]):

        """Highest Recreation Spectrum == 9"""

        expression = (
            "if({spectrum} == {highest_recreation_category}, {spectrum}, null())"
        )
        highest_spectrum_expression = expression.format(
            spectrum=recreation_spectrum,
            highest_recreation_category=HIGHEST_RECREATION_CATEGORY,
        )
        highest_spectrum_equation = EQUATION.format(
            result=highest_spectrum, expression=highest_spectrum_expression
        )
        r.mapcalc(highest_spectrum_equation, overwrite=True)
        remove_map_at_exit(highest_spectrum)  # FIXME

        """Distance map"""

        distance_to_highest_spectrum = temporary_filename(filename=highest_spectrum)
        r.grow_distance(
            input=highest_spectrum,
            distance=distance_to_highest_spectrum,
            metric=metric,
            quiet=True,
            overwrite=True,
        )

        """Distance categories"""

        distance_categories_to_highest_spectrum = "categories_of_"
        distance_categories_to_highest_spectrum += distance_to_highest_spectrum
        remove_map_at_exit(distance_categories_to_highest_spectrum)  # FIXME

        recode_map(
            raster=distance_to_highest_spectrum,
            rules=spectrum_distance_categories,
            colors=SCORE_COLORS,
            output=distance_categories_to_highest_spectrum,
        )

        temporary_distance_categories_to_highest_spectrum = temporary_filename(
            filename=distance_categories_to_highest_spectrum
        )
        spectrum_distance_category_labels = string_to_file(
            SPECTRUM_DISTANCE_CATEGORY_LABELS,
            filename=temporary_distance_categories_to_highest_spectrum,
        )
        remove_files_at_exit(spectrum_distance_category_labels)

        r.category(
            map=distance_categories_to_highest_spectrum,
            rules=spectrum_distance_category_labels,
            separator=":",
        )

        """Combine Base map and Distance Categories"""

        tmp_crossmap = temporary_filename(filename=crossmap)
        r.cross(
            input=(distance_categories_to_highest_spectrum, base),
            flags="z",
            output=tmp_crossmap,
            quiet=True,
        )

        msg = MATCHING_COMPUTATIONAL_RESOLUTION.format(raster=population)
        grass.verbose(_(msg))
        grass.use_temp_region()  # to safely modify the region
        g.region(
            nsres=population_ns_resolution,
            ewres=population_ew_resolution,
            flags="a",
        )  # Resolution should match 'population'

        if info:
            population_statistics = get_univariate_statistics(population)
            population_total = population_statistics["sum"]
            msg = POPULATION_STATISTICS.format(s=population_total)
            grass.verbose(_(msg))

        """Demand Distribution"""

        if any([flow, supply, aggregation]) and not demand:
            demand = temporary_filename(filename="demand")

        compute_demand(
            base=tmp_crossmap,
            population=population,
            method="sum",
            output_demand=demand,
            vector_base_map=base_vector,
            vector_methods=METHODS,
            vector_column_prefix=COLUMN_PREFIX_DEMAND,
        )

        """Unmet Demand"""

        if unmet_demand:
            compute_unmet_demand(
                distance_categories_to_highest_spectrum=distance_categories_to_highest_spectrum,
                constant=MOBILITY_CONSTANT,
                coefficients=MOBILITY_COEFFICIENTS[4],
                population=demand,
                score=MOBILITY_SCORE,
                real_numbers=real_numbers,
                output_unmet_demand=unmet_demand,
                vector_base_map=base_vector,
                vector_methods=METHODS,
                vector_column_prefix=COLUMN_PREFIX_UNMET,
            )

        """Mobility function"""

        if not flow and any([supply, aggregation]):

            flow = flow_map_name
            remove_map_at_exit(flow)

        if flow or any([supply, aggregation]):

            mobility_expression = mobility_function(
                distance=distance_categories_to_highest_spectrum,
                constant=MOBILITY_CONSTANT,
                coefficients=MOBILITY_COEFFICIENTS,
                population=demand,
                score=MOBILITY_SCORE,
                real_numbers=real_numbers,
            )
            # suitability=suitability)  # Not used.
            # Maybe it can, though, after successfully testing its
            # integration to build_distance_function().

            grass.debug(_(MOBILITY_FUNCTION.format(f=mobility_expression)))

            """Flow map"""

            mobility_equation = EQUATION.format(
                result=flow, expression=mobility_expression
            )
            r.mapcalc(mobility_equation, overwrite=True)

            if base_vector:

                update_vector(
                    vector=base_vector,
                    raster=flow,
                    methods=METHODS,
                    column_prefix=COLUMN_PREFIX_FLOW,
                )

    """Supply Table"""

    if aggregation:

        supply_parameters = {}

        if supply:
            supply_parameters.update({"supply_filename": supply})

        if use:
            supply_parameters.update({"use_filename": use})

        if base_vector:
            supply_parameters.update({"vector": base_vector})

        compute_supply(
            base=landcover,
            recreation_spectrum=recreation_spectrum,
            highest_spectrum=highest_spectrum,
            base_reclassification_rules=landcover_reclassification_rules,
            reclassified_base=maes_ecosystem_types,
            reclassified_base_title=MAES_ECOSYSTEM_TYPES_MAP_TITLE,
            flow=flow,
            aggregation=aggregation,
            ns_resolution=population_ns_resolution,
            ew_resolution=population_ew_resolution,
            print_only=print_only,
            **supply_parameters,
        )

    # restore region
    if landuse_extent:
        grass.del_temp_region()  # restoring previous region settings
        grass.verbose("Original Region restored")

    # print citation
    citation = "Citation: " + CITATION_RECREATION_POTENTIAL
    grass.verbose(citation)
