#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author Nikos Alexandris |
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
import atexit

# constants

from estimap_recreation.labels import POTENTIAL_CATEGORY_LABELS
from estimap_recreation.labels import OPPORTUNITY_CATEGORY_LABELS
from estimap_recreation.labels import SPECTRUM_CATEGORY_LABELS
from estimap_recreation.labels import SPECTRUM_DISTANCE_CATEGORY_LABELS
from estimap_recreation.colors import POTENTIAL_COLORS
from estimap_recreation.colors import OPPORTUNITY_COLORS
from estimap_recreation.colors import SPECTRUM_COLORS

# utilities

from estimap_recreation.grassy_utilities import *
from estimap_recreation.utilities import *

# algorithms

from estimap_recreation.distance import *
from estimap_recreation.normalisation import *
from estimap_recreation.accessibility import *
from estimap_recreation.spectrum import *
from estimap_recreation.components import *
from estimap_recreation.mobility import *
from estimap_recreation.supply_and_use import *

def main():
    """
    Main program
    """
    atexit.register(remove_temporary_maps)

    """Flags and Options"""
    options, flags = grass.parser()

    # Flags that are not being used
    info = flags["i"]
    save_temporary_maps = flags["s"]

    # Flags that are being used
    average_filter = flags["f"]
    landuse_extent = flags["e"]
    print_only = flags["p"]

    timestamp = options["timestamp"]

    metric = options["metric"]
    units = options["units"]
    if len(units) > 1:
        units = units.split(",")

    """names for input, output, output suffix, options"""

    mask = options["mask"]

    """
    following some hard-coded names -- review and remove!
    """

    land = options["land"]
    land_component_map_name = temporary_filename(filename="land_component")

    water = options["water"]
    water_component_map_name = temporary_filename(filename="water_component")

    natural = options["natural"]
    natural_component_map_name = temporary_filename(filename="natural_component")

    urban = options["urban"]
    urban_component_map = "urban_component"

    infrastructure = options["infrastructure"]
    infrastructure_component_map_name = temporary_filename(filename="infrastructure_component")

    recreation = options["recreation"]
    recreation_component_map_name = temporary_filename(filename="recreation_component")

    """Land components"""

    landuse = options["landuse"]
    if landuse:
        # Check datatype: a land use map should be categorical, i.e. of type CELL
        landuse_datatype = grass.raster.raster_info(landuse)["datatype"]
        if landuse_datatype != "CELL":
            msg = (
                "The '{landuse}' input map "
                "should be a categorical one "
                "and of type 'CELL'. "
                "Perhaps you meant to use the 'land' input option instead?"
            )
            grass.fatal(_(msg.format(landuse=landuse)))

    suitability_map_name = temporary_filename(filename="suitability")
    suitability_scores = options["suitability_scores"]

    if landuse and suitability_scores and ":" not in suitability_scores:
        msg = "Suitability scores from file: {scores}."
        msg = msg.format(scores=suitability_scores)
        grass.verbose(_(msg))

    if landuse and not suitability_scores:
        msg = "Using internal rules to score land use classes in '{map}'"
        msg = msg.format(map=landuse)
        grass.warning(_(msg))

        temporary_suitability_map_name = temporary_filename(filename=suitability_map_name)
        suitability_scores = string_to_file(
            SUITABILITY_SCORES, filename=temporary_suitability_map_name
        )
        remove_files_at_exit(suitability_scores)

    if landuse and suitability_scores and ":" in suitability_scores:
        msg = "Using provided string of rules to score land use classes in {map}"
        msg = msg.format(map=landuse)
        grass.verbose(_(msg))
        temporary_suitability_map_name = temporary_filename(filename=suitability_map_name)
        suitability_scores = string_to_file(
            suitability_scores, filename=temporary_suitability_map_name
        )
        remove_files_at_exit(suitability_scores)

    # FIXME -----------------------------------------------------------------

    # Use one landcover input if supply is requested
    # Use one set of land cover reclassification rules

    landcover = options["landcover"]

    if not landcover:
        landcover = landuse
        msg = "Land cover map 'landcover' not given. "
        msg += "Attempt to use the '{landuse}' map to derive areal statistics"
        msg = msg.format(landuse=landuse)
        grass.verbose(_(msg))

    maes_ecosystem_types = "maes_ecosystem_types"
    maes_ecosystem_types_scores = "maes_ecosystem_types_scores"
    landcover_reclassification_rules = options["land_classes"]

    # if 'land_classes' is a file
    if (
        landcover
        and landcover_reclassification_rules
        and ":" not in landcover_reclassification_rules
    ):
        msg = "Land cover reclassification rules from file: {rules}."
        msg = msg.format(rules=landcover_reclassification_rules)
        grass.verbose(_(msg))

    # if 'land_classes' not given
    if landcover and not landcover_reclassification_rules:

        # if 'landcover' is not the MAES land cover,
        # then use internal reclassification rules
        # how to test:
        # 1. landcover is not a "MAES" land cover
        # 2. landcover is an Urban Atlas one?

        msg = "Using internal rules to reclassify the '{map}' map"
        msg = msg.format(map=landcover)
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
        msg = "Using provided string of rules to reclassify the '{map}' map"
        msg = msg.format(map=landcover)
        grass.verbose(_(msg))
        temporary_maes_land_classes = temporary_filename(filename=maes_land_classes)
        landcover_reclassification_rules = string_to_file(
            landcover_reclassification_rules, filename=maes_land_classes
        )
        remove_files_at_exit(landcover_reclassification_rules)

    # FIXME -----------------------------------------------------------------

    """Water components"""

    lakes = options["lakes"]
    lakes_coefficients = options["lakes_coefficients"]
    lakes_proximity_map_name = "lakes_proximity"
    coastline = options["coastline"]
    coast_proximity_map_name = "coast_proximity"
    coast_geomorphology = options["coast_geomorphology"]
    # coast_geomorphology_coefficients = options['geomorphology_coefficients']
    coast_geomorphology_map_name = "coast_geomorphology"
    bathing_water = options["bathing_water"]
    bathing_water_coefficients = options["bathing_coefficients"]
    bathing_water_proximity_map_name = "bathing_water_proximity"

    """Natural components"""

    protected = options["protected"]
    protected_scores = options["protected_scores"]
    protected_areas_map_name = "protected_areas"

    """Artificial areas"""

    artificial = options["artificial"]
    artificial_proximity_map_name = "artificial_proximity"
    artificial_distance_categories = options["artificial_distances"]

    roads = options["roads"]
    roads_proximity_map_name = "roads_proximity"
    roads_distance_categories = options["roads_distances"]

    artificial_accessibility_map_name = "artificial_accessibility"

    """Devaluation"""

    devaluation = options["devaluation"]

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

    potential_title = "Recreation potential"
    recreation_potential = options["potential"]  # intermediate / output
    recreation_potential_map_name = temporary_filename(filename="recreation_potential")

    opportunity_title = "Recreation opportunity"
    recreation_opportunity = options["opportunity"]
    recreation_opportunity_map_name = "recreation_opportunity"

    spectrum_title = "Recreation spectrum"
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
            spectrum_distance_categories,
            filename=temporary_recreation_spectrum
        )
        remove_files_at_exit(spectrum_distance_categories)

    highest_spectrum = "highest_recreation_spectrum"
    crossmap = "crossmap"  # REMOVEME

    demand = options["demand"]
    unmet_demand = options["unmet"]

    flow = options["flow"]
    flow_map_name = "flow"

    supply = options["supply"]  # use as CSV filename prefix
    use = options["use"]  # use as CSV filename prefix

    """ First, care about the computational region"""

    if mask:
        msg = "Masking NULL cells based on '{mask}'".format(mask=mask)
        grass.verbose(_(msg))
        r.mask(raster=mask, overwrite=True, quiet=True)

    if landuse_extent:
        grass.use_temp_region()  # to safely modify the region
        g.region(flags="p", raster=landuse)  # Set region to 'mask'
        msg = "|! Computational resolution matched to {raster}"
        msg = msg.format(raster=landuse)
        g.message(_(msg))

    """Land Component
            or Suitability of Land to Support Recreation Activities (SLSRA)"""

    land_component = []  # a list, use .extend() wherever required

    if land:

        land_component = land.split(",")

    if landuse and suitability_scores:

        msg = "Deriving land suitability from '{landuse}' "
        msg += "based on rules described in file '{rules}'"
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
            component_name="land",
            component_list=land_component,
        )

    """Water Component"""

    water_component = []
    water_components = []

    if water:

        water_component = water.split(",")
        msg = "Water component includes currently: {component}"
        msg = msg.format(component=water_component)
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
            component_name="water",
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
            component_name="water",
            component_list=water_components,
        )

    if coast_geomorphology:

        try:

            if not coastline:
                msg = "The coastline map is required in order to "
                msg += "compute attractiveness based on the "
                msg += "coast geomorphology raster map"
                msg = msg.format(c=water_component)
                grass.fatal(_(msg))

        except NameError:
            grass.fatal(_("No coast proximity"))

        coast_attractiveness = neighborhood_function(
            raster=coast_geomorphology,
            method=NEIGHBORHOOD_METHOD,
            size=NEIGHBORHOOD_SIZE,
            distance_map=coast_proximity,
        )

        append_map_to_component(
            raster=coast_attractiveness,
            component_name="water",
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
            component_name="water",
            component_list=water_components,
        )

    # merge water component related maps in one list
    water_component += water_components

    """Natural Component"""

    natural_component = []
    natural_components = []

    if natural:

        natural_component = natural.split(",")

    if protected:
        msg = "Scoring protected areas '{protected}' based on '{rules}'"
        grass.verbose(_(msg.format(protected=protected, rules=protected_scores)))

        protected_areas = protected_areas_map_name

        recode_map(
            raster=protected,
            rules=protected_scores,
            colors=SCORE_COLORS,
            output=protected_areas,
        )

        append_map_to_component(
            raster=protected_areas,
            component_name="natural",
            component_list=natural_components,
        )

    # merge natural resources component related maps in one list
    natural_component += natural_components

    """ Normalize land, water, natural inputs
    and add them to the recreation potential component"""

    recreation_potential_component = []

    if land_component:

        for dummy_index in land_component:

            # remove 'land_map' from 'land_component'
            # process and add it back afterwards
            land_map = land_component.pop(0)

            """
            This section sets NULL cells to 0.
            Because `r.null` operates on the complete input raster map,
            manually subsetting the input map is required.
            """
            suitability_map = temporary_filename(filename=land_map)
            subset_land = EQUATION.format(result=suitability_map, expression=land_map)
            r.mapcalc(subset_land)

            grass.debug(_("Setting NULL cells to 0"))  # REMOVEME ?
            r.null(map=suitability_map, null=0)  # Set NULLs to 0

            msg = "\nAdding land suitability map '{suitability}' "
            msg += "to 'Recreation Potential' component\n"
            msg = msg.format(suitability=suitability_map)
            grass.verbose(_(msg))

            # add 'suitability_map' to 'land_component'
            land_component.append(suitability_map)

    if len(land_component) > 1:
        grass.verbose(_("\nNormalize 'Land' component\n"))
        zerofy_and_normalise_component(
            land_component, THRESHHOLD_ZERO, land_component_map_name
        )
        recreation_potential_component.extend(land_component)
    else:
        recreation_potential_component.extend(land_component)

    if land_component and average_filter:
        smooth_component(land_component, method="average", size=7)

    remove_map_at_exit(land_component)

    if len(water_component) > 1:
        grass.verbose(_("\nNormalize 'Water' component\n"))
        zerofy_and_normalise_component(
            water_component, THRESHHOLD_ZERO, water_component_map_name
        )
        recreation_potential_component.append(water_component_map_name)
    else:
        recreation_potential_component.extend(water_component)

    remove_map_at_exit(water_component_map_name)

    if len(natural_component) > 1:
        grass.verbose(_("\nNormalize 'Natural' component\n"))
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

    tmp_recreation_potential = temporary_filename(filename=recreation_potential_map_name)

    msg = "Computing intermediate 'Recreation Potential' map: '{potential}'"
    grass.verbose(_(msg.format(potential=tmp_recreation_potential)))
    grass.debug(_("Maps: {maps}".format(maps=recreation_potential_component)))

    zerofy_and_normalise_component(
        components=recreation_potential_component,
        threshhold=THRESHHOLD_ZERO,
        output_name=tmp_recreation_potential,
    )

    # recode recreation_potential
    tmp_recreation_potential_categories = temporary_filename(filename=recreation_potential)

    msg = "\nClassifying '{potential}' map"
    msg = msg.format(potential=tmp_recreation_potential)
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
        msg = (
            "Infrastructure is not required "
            "to derive the 'potential' recreation map."
        )
        grass.warning(_(msg))

    if any([recreation_opportunity, recreation_spectrum, demand, flow, supply]):

        infrastructure_component = []
        infrastructure_components = []

        if infrastructure:
            infrastructure_component.append(infrastructure)

        """Artificial surfaces (includung Roads)"""

        if artificial and roads:

            msg = "Roads distance categories: {c}"
            msg = msg.format(c=roads_distance_categories)
            grass.debug(_(msg))
            roads_proximity = compute_artificial_proximity(
                raster=roads,
                distance_categories=roads_distance_categories,
                output_name=roads_proximity_map_name,
            )

            msg = "Artificial distance categories: {c}"
            msg = msg.format(c=artificial_distance_categories)
            grass.debug(_(msg))
            artificial_proximity = compute_artificial_proximity(
                raster=artificial,
                distance_categories=artificial_distance_categories,
                output_name=artificial_proximity_map_name,
            )

            artificial_accessibility = compute_artificial_accessibility(
                artificial_proximity,
                roads_proximity,
                output_name=artificial_accessibility_map_name,
            )

            infrastructure_components.append(artificial_accessibility)

        # merge infrastructure component related maps in one list
        infrastructure_component += infrastructure_components

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
        tmp_recreation_opportunity = temporary_filename(filename=recreation_opportunity_map_name)
        msg = "Computing intermediate opportunity map '{opportunity}'"
        grass.debug(_(msg.format(opportunity=tmp_recreation_opportunity)))

        grass.verbose(_("\nNormalize 'Recreation Opportunity' component\n"))
        grass.debug(_("Maps: {maps}".format(maps=recreation_opportunity_component)))

        zerofy_and_normalise_component(
            components=recreation_opportunity_component,
            threshhold=THRESHHOLD_0001,
            output_name=tmp_recreation_opportunity,
        )

        # Why threshhold 0.0003? How and why it differs from 0.0001?
        # -------------------------------------------------------------- REVIEW

        msg = "Classifying '{opportunity}' map"
        grass.verbose(msg.format(opportunity=tmp_recreation_opportunity))

        # recode opportunity_component
        tmp_recreation_opportunity_categories = temporary_filename(filename=recreation_opportunity)
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

        msg = "Writing '{spectrum}' map"
        msg = msg.format(spectrum=recreation_spectrum)
        grass.verbose(_(msg))
        get_univariate_statistics(recreation_spectrum)

        # get category labels
        temporary_spectrum_categories = temporary_filename(filename="categories_of_" + recreation_spectrum)
        spectrum_category_labels = string_to_file(
            SPECTRUM_CATEGORY_LABELS, filename=temporary_spectrum_categories
        )

        # add to list for removal
        remove_files_at_exit(spectrum_category_labels)

        # update category labels, meta and colors
        spectrum_categories = "categories_of_"

        r.category(
            map=recreation_spectrum, rules=spectrum_category_labels, separator=":"
        )

        update_meta(recreation_spectrum, spectrum_title)

        r.colors(map=recreation_spectrum, rules="-", stdin=SPECTRUM_COLORS, quiet=True)

        if base_vector:
            update_vector(
                vector=base_vector,
                raster=recreation_spectrum,
                methods=METHODS,
                column_prefix="spectrum",
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

        temporary_distance_categories_to_highest_spectrum = temporary_filename(filename=distance_categories_to_highest_spectrum)
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

        grass.use_temp_region()  # to safely modify the region
        g.region(
            nsres=population_ns_resolution, ewres=population_ew_resolution, flags="a"
        )  # Resolution should match 'population' FIXME
        msg = "|! Computational extent & resolution matched to {raster}"
        msg = msg.format(raster=landuse)
        grass.verbose(_(msg))

        population_statistics = get_univariate_statistics(population)
        population_total = population_statistics['sum']
        msg = "|i Population statistics: {s}".format(s=population_total)
        grass.verbose(_(msg))

        """Demand Distribution"""

        if any([flow, supply, aggregation]) and not demand:
            demand = temporary_filename(filename="demand")

        r.stats_zonal(
            base=tmp_crossmap,
            flags="r",
            cover=population,
            method="sum",
            output=demand,
            overwrite=True,
            quiet=True,
        )

        # copy 'reclassed' as 'normal' map (r.mapcalc)
        # so as to enable removal of it and its 'base' map
        demand_copy = demand + "_copy"
        copy_expression = "{input_raster}"
        copy_expression = copy_expression.format(input_raster=demand)
        copy_equation = EQUATION.format(result=demand_copy, expression=copy_expression)
        r.mapcalc(copy_equation, overwrite=True)

        # remove the reclassed map 'demand'
        g.remove(flags="f", type="raster", name=demand, quiet=True)

        # rename back to 'demand'
        g.rename(raster=(demand_copy, demand), quiet=True)

        if demand and base_vector:
            update_vector(
                vector=base_vector,
                raster=demand,
                methods=METHODS,
                column_prefix="demand",
            )

        """Unmet Demand"""

        if unmet_demand:

            # compute unmet demand

            unmet_demand_expression = compute_unmet_demand(
                distance=distance_categories_to_highest_spectrum,
                constant=MOBILITY_CONSTANT,
                coefficients=MOBILITY_COEFFICIENTS[4],
                population=demand,
                score=MOBILITY_SCORE,
            )
            # suitability=suitability)  # Not used.
            # Maybe it can, though, after successfully testing its
            # integration to build_distance_function().

            grass.debug(
                _("Unmet demand function: {f}".format(f=unmet_demand_expression))
            )

            unmet_demand_equation = EQUATION.format(
                result=unmet_demand, expression=unmet_demand_expression
            )
            r.mapcalc(unmet_demand_equation, overwrite=True)

            if base_vector:
                update_vector(
                    vector=base_vector,
                    raster=unmet_demand,
                    methods=METHODS,
                    column_prefix="unmet",
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
            )
            # suitability=suitability)  # Not used.
            # Maybe it can, though, after successfully testing its
            # integration to build_distance_function().

            msg = "Mobility function: {f}"
            grass.debug(_(msg.format(f=mobility_expression)))

            """Flow map"""

            mobility_equation = EQUATION.format(
                result=flow, expression=mobility_expression
            )
            r.mapcalc(mobility_equation, overwrite=True)

            if base_vector:
                update_vector(
                    vector=base_vector,
                    raster=flow_map_name,
                    methods=METHODS,
                    column_prefix="flow",
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
            reclassified_base_title="MAES ecosystem types",
            flow=flow,
            flow_map_name=flow_map_name,
            aggregation=aggregation,
            ns_resolution=population_ns_resolution,
            ew_resolution=population_ew_resolution,
            print_only=print_only,
            **supply_parameters
        )

    # restore region
    if landuse_extent:
        grass.del_temp_region()  # restoring previous region settings
        grass.verbose("Original Region restored")

    # print citation
    citation = "Citation: " + CITATION_RECREATION_POTENTIAL
    grass.verbose(citation)
