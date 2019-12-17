# -*- coding: utf-8 -*-

"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import math
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from .colors import MOBILITY_COLORS
from .constants import (
    EQUATION,
    HIGHEST_RECREATION_CATEGORY,
    SUITABILITY_SCORES_LABELS,
    COMMA,
    CSV_EXTENSION,
    METHODS,
)
from .grassy_utilities import (
    temporary_filename,
    remove_map_at_exit,
    remove_files_at_exit,
    string_to_file,
    get_raster_statistics,
    update_vector,
    raster_to_vector,
)
from .utilities import (
    merge_two_dictionaries,
    nested_dictionary_to_csv,
    dictionary_to_csv,
)


def compile_use_table(supply):
    """Compile the 'use' table out of a 'supply' table

    Parameters
    ----------
    supply :
        A nested Python dictionary that is compiled when runnning the
        compute_supply() function

    Returns
    -------

    Examples
    --------
    """
    uses = {}
    for outer_key, outer_value in supply.items():
        dictionaries = outer_value
        use_values = []
        for key, value in dictionaries.items():
            use_value = value[0]
            use_values.append(use_value)

        use_in_key = sum(
            [float(x) if not math.isnan(float(x)) else 0 for x in use_values]
        )

        try:
            uses[outer_key] = use_in_key
        except KeyError:
            print("Something went wrong in building the use table")

    return uses


def compute_supply(
        base,
        recreation_spectrum,
        highest_spectrum,
        base_reclassification_rules,
        reclassified_base,
        reclassified_base_title,
        flow,
        aggregation,
        ns_resolution,
        ew_resolution,
        print_only=False,
        flow_column_name=None,
        vector=None,
        supply_filename=None,
        use_filename=None,
    ):
    """
     Algorithmic description of the "Contribution of Ecosysten Types"

     # FIXME
     '''
     1   B ← {0, .., m-1}     :  Set of aggregational boundaries
     2   T ← {0, .., n-1}     :  Set of land cover types
     3   WE ← 0               :  Set of weighted extents
     4   R ← 0                :  Set of fractions
     5   F ← 0
     6   MASK ← HQR           : High Quality Recreation
     7   foreach {b} ⊆ B do   : for each aggregational boundary 'b'
     8      RB ← 0
     9      foreach {t} ⊆ T do  : for each Land Type
     10         WEt ← Et * Wt   : Weighted Extent = Extent(t) * Weight(t)
     11         WE ← WE⋃{WEt}   : Add to set of Weighted Extents
     12     S ← ∑t∈WEt
     13     foreach t ← T do
     14        Rt ← WEt / ∑WE
     15        R ← R⋃{Rt}
     16     RB ← RB⋃{R}
     '''
     # FIXME

    Parameters
    ----------
    recreation_spectrum:
        Map scoring access to and quality of recreation

    highest_spectrum :
        Expected is a map of areas with highest recreational value (category 9
        as per the report ... )

    base :
        Base land types map for final zonal statistics. Specifically to
        ESTIMAP's recrceation mapping algorithm

    base_reclassification_rules :
        Reclassification rules for the input base map

    reclassified_base :
        Name for the reclassified base cover map

    reclassified_base_title :
        Title for the reclassified base map

    ecosystem_types :

    flow :
        Map of visits, derived from the mobility function, depicting the
        number of people living inside zones 0, 1, 2, 3. Used as a cover map
        for zonal statistics.

    aggregation :

    ns_resolution :

    ew_resolution :

    statistics_filename :

    supply_filename :
        Name for CSV output file of the supply table

    use_filename :
        Name for CSV output file of the use table

    flow_column_name :
        Name for column to populate with 'flow' values

    vector :
        If 'vector' is given, a vector map of the 'flow' along with appropriate
        attributes will be produced.

    ? :
        Land cover class percentages in ROS9 (this is: relative percentage)

    output :
        Supply table (distribution of flow for each land cover class)

    Returns
    -------
    This function produces a map to base the production of a supply table in
    form of CSV.

    Examples
    --------
    """
    # Inputs
    flow_in_base = flow + "_" + base
    base_scores = base + ".scores"

    # Define lists and dictionaries to hold intermediate data
    statistics_dictionary = {}
    weighted_extents = {}
    flows = []

    # MASK areas of high quality recreation
    r.mask(raster=highest_spectrum, overwrite=True, quiet=True)

    # Reclassify land cover map to MAES ecosystem types
    r.reclass(
        input=base,
        rules=base_reclassification_rules,
        output=reclassified_base,
        quiet=True,
    )
    # add 'reclassified_base' to "remove_at_exit" after the reclassified maps!

    # Discard areas out of MASK
    temporary_reclassified_base = reclassified_base + "_temporary"
    copy_equation = EQUATION.format(
        result=temporary_reclassified_base, expression=reclassified_base
    )
    r.mapcalc(copy_equation, overwrite=True)
    g.rename(
            raster=(temporary_reclassified_base, reclassified_base),
            overwrite=True,
            quiet=True,
    )

    # Count flow within each land cover category
    r.stats_zonal(
        base=base,
        flags="r",
        cover=flow,
        method="sum",
        output=flow_in_base,
        overwrite=True,
        quiet=True,
    )
    remove_map_at_exit(flow_in_base)

    # Set colors for "flow" map
    r.colors(map=flow_in_base, color=MOBILITY_COLORS, quiet=True)

    # Parse aggregation raster categories and labels
    categories = grass.parse_command("r.category", map=aggregation, delimiter="\t")

    for category in categories:

        msg = "\n>>> Processing category '{c}' of aggregation map '{a}'"
        grass.verbose(_(msg.format(c=category, a=aggregation)))

        # Intermediate names

        cells = highest_spectrum + ".cells" + "." + category
        remove_map_at_exit(cells)

        extent = highest_spectrum + ".extent" + "." + category
        remove_map_at_exit(extent)

        weighted = highest_spectrum + ".weighted" + "." + category
        remove_map_at_exit(weighted)

        fractions = base + ".fractions" + "." + category
        remove_map_at_exit(fractions)

        flow_category = "_flow_" + category
        flow = base + flow_category
        remove_map_at_exit(flow)

        flow_in_reclassified_base = reclassified_base + "_flow"
        flow_in_category = reclassified_base + flow_category
        flows.append(flow_in_category)  # add to list for patching
        remove_map_at_exit(flow_in_category)

        # Output names

        msg = "*** Processing aggregation raster category: {r}"
        msg = msg.format(r=category)
        grass.debug(_(msg))
        # g.message(_(msg))

        # First, set region to extent of the aggregation map
        # and resolution to the one of the population map
        # Note the `-a` flag to g.region: ?
        # To safely modify the region: grass.use_temp_region()  # FIXME
        g.region(
            raster=aggregation,
            nsres=ns_resolution,
            ewres=ew_resolution,
            flags="a",
            quiet=True,
        )

        msg = "!!! Computational resolution matched to {raster}"
        msg = msg.format(raster=aggregation)
        grass.debug(_(msg))

        # Build MASK for current category & high quality recreation areas
        msg = " * Setting category '{c}' as a MASK"
        grass.verbose(_(msg.format(c=category, a=aggregation)))

        masking = "if( {spectrum} == {highest_quality_category} && "
        masking += "{aggregation} == {category}, "
        masking += "1, null() )"
        masking = masking.format(
            spectrum=recreation_spectrum,
            highest_quality_category=HIGHEST_RECREATION_CATEGORY,
            aggregation=aggregation,
            category=category,
        )
        masking_equation = EQUATION.format(result="MASK", expression=masking)
        grass.mapcalc(masking_equation, overwrite=True)

        # zoom to MASK
        g.region(zoom="MASK", nsres=ns_resolution, ewres=ew_resolution, quiet=True)

        # Count number of cells within each land category
        r.stats_zonal(
            flags="r",
            base=base,
            cover=highest_spectrum,
            method="count",
            output=cells,
            overwrite=True,
            quiet=True,
        )
        cells_categories = grass.parse_command("r.category", map=cells, delimiter="\t")
        grass.debug(_("*** Cells: {c}".format(c=cells_categories)))

        # Build cell category and label rules for `r.category`
        cells_rules = "\n".join(
            ["{0}:{1}".format(key, value) for key, value in cells_categories.items()]
        )

        # Discard areas out of MASK
        temporary_cells = cells + "_temporary"
        copy_equation = EQUATION.format(result=temporary_cells, expression=cells)
        r.mapcalc(copy_equation, overwrite=True)
        g.rename(
                raster=(temporary_cells, cells),
                overwrite=True,
                quiet=True,
        )

        # Reassign cell category labels
        r.category(map=cells,
                rules="-",
                stdin=cells_rules,
                separator=":",
        )

        # Compute extent of each land category
        extent_expression = "@{cells} * area()"
        extent_expression = extent_expression.format(cells=cells)
        extent_equation = EQUATION.format(result=extent, expression=extent_expression)
        r.mapcalc(extent_equation, overwrite=True)

        # Write extent figures as labels
        extent_figures_as_labels = extent + "_labeled"
        r.stats_zonal(
            flags="r",
            base=base,
            cover=extent,
            method="average",
            output=extent_figures_as_labels,
            overwrite=True,
            verbose=False,
            quiet=True,
        )
        g.rename(
                raster=(extent_figures_as_labels, extent),
                overwrite=True,
                quiet=True,
        )

        # Write land suitability scores as an ASCII file
        temporary_reclassified_base_map = temporary_filename(filename=reclassified_base)
        suitability_scores_as_labels = string_to_file(
            SUITABILITY_SCORES_LABELS, filename=temporary_reclassified_base_map
        )
        remove_files_at_exit(suitability_scores_as_labels)

        # Write scores as raster category labels
        r.reclass(
            input=base,
            output=base_scores,
            rules=suitability_scores_as_labels,
            overwrite=True,
            quiet=True,
            verbose=False,
        )
        remove_map_at_exit(base_scores)

        # Compute weighted extents
        weighted_expression = "@{extent} * float(@{scores})"
        weighted_expression = weighted_expression.format(
            extent=extent, scores=base_scores
        )
        weighted_equation = EQUATION.format(
            result=weighted, expression=weighted_expression
        )
        r.mapcalc(weighted_equation, overwrite=True)

        # Write weighted extent figures as labels
        weighted_figures_as_labels = weighted + "_figures_as_labels"
        r.stats_zonal(
            flags="r",
            base=base,
            cover=weighted,
            method="average",
            output=weighted_figures_as_labels,
            overwrite=True,
            verbose=False,
            quiet=True,
        )
        g.rename(
                raster=(weighted_figures_as_labels, weighted),
                overwrite=True,
                quiet=True)


        # Get weighted extents in a dictionary
        weighted_extents = grass.parse_command(
            "r.category", map=weighted, delimiter="\t"
        )

        # Compute the sum of all weighted extents and add to dictionary
        category_sum = sum(
            [
                float(x) if not math.isnan(float(x)) else 0
                for x in weighted_extents.values()
            ]
        )
        weighted_extents["sum"] = category_sum

        # Create a map to hold fractions of each weighted extent to the sum
        # See also:
        # https://grasswiki.osgeo.org/wiki/LANDSAT#Hint:_Minimal_disk_space_copies
        r.reclass(
            input=base,
            output=fractions,
            rules="-",
            stdin="*=*",
            verbose=False,
            quiet=True,
        )

        # Compute weighted fractions of land types
        fraction_category_label = {
            key: float(value) / weighted_extents["sum"]
            for (key, value) in weighted_extents.items()
            if key is not "sum"
        }

        # Build fraction category and label rules for `r.category`
        fraction_rules = "\n".join(
            [
                "{0}:{1}".format(key, value)
                for key, value in fraction_category_label.items()
            ]
        )

        # Set rules
        r.category(map=fractions, rules="-", stdin=fraction_rules, separator=":")

        # Assert that sum of fractions is ~1
        fraction_categories = grass.parse_command(
            "r.category", map=fractions, delimiter="\t"
        )

        fractions_sum = sum(
            [
                float(x) if not math.isnan(float(x)) else 0
                for x in fraction_categories.values()
            ]
        )
        msg = "*** Fractions: {f}".format(f=fraction_categories)
        grass.debug(_(msg))

        # g.message(_("Sum: {:.17g}".format(fractions_sum)))
        assert abs(fractions_sum - 1) < 1.0e-6, "Sum of fractions is != 1"

        # Compute flow
        flow_expression = "@{fractions} * @{flow}"
        flow_expression = flow_expression.format(fractions=fractions, flow=flow_in_base)
        flow_equation = EQUATION.format(result=flow, expression=flow_expression)
        r.mapcalc(flow_equation, overwrite=True)

        # Write flow figures as raster category labels
        r.stats_zonal(
            base=reclassified_base,
            flags="r",
            cover=flow,
            method="sum",
            output=flow_in_category,
            overwrite=True,
            verbose=False,
            quiet=True,
        )

        # Parse flow categories and labels
        flow_categories = grass.parse_command(
            "r.category",
            map=flow_in_category,
            delimiter="\t",
            quiet=True,
        )
        grass.debug(_("*** Flow: {c}".format(c=flow_categories)))

        # Build flow category and label rules for `r.category`
        flow_rules = "\n".join(
            ["{0}:{1}".format(key, value) for key, value in flow_categories.items()]
        )

        # Discard areas out of MASK

        # Check here again!
        # Output patch of all flow maps?

        temporary_flow_in_category = flow_in_category + "_temporary"
        copy_equation = EQUATION.format(
            result=temporary_flow_in_category, expression=flow_in_category
        )
        r.mapcalc(copy_equation, overwrite=True)
        g.rename(
                raster=(temporary_flow_in_category, flow_in_category),
                overwrite=True,
                quiet=True,
        )

        # Reassign cell category labels
        r.category(
            map=flow_in_category,
            rules="-",
            stdin=flow_rules,
            separator=":",
            quiet=True,
        )

        # Update title
        reclassified_base_title += " " + category
        r.support(flow_in_category, title=reclassified_base_title)

        # debugging
        # r.report(
        #     flags='hn',
        #     map=(flow_in_category),
        #     units=('k','c','p'),
        # )

        if print_only:

            grass.verbose(" * Flow in category {c}:".format(c=category))
            r.stats(
                input=(flow_in_category),
                output="-",
                flags="nacpl",
                separator=COMMA,
                quiet=True,
            )

        if not print_only:

            if flow_column_name:
                flow_column_prefix = flow_column_name + '_' + category
            else:
                flow_column_name = "flow"
                flow_column_prefix = flow_column_name + '_' + category

            # Produce vector map(s)
            if vector:

                update_vector(
                    vector=vector,
                    raster=flow_in_category,
                    methods=METHODS,
                    column_prefix=flow_column_prefix,
                )

                # update columns of an user-fed vector map
                # from the columns of vectorised flow-in-category raster map
                raster_to_vector(
                    raster_category_flow=flow_in_category,
                    vector_category_flow=flow_in_category,
                    flow_column_name=flow_column_name,
                    category=category,
                    type="area",
                )

            # get statistics
            dictionary = get_raster_statistics(
                map_one=aggregation,  # reclassified_base
                map_two=flow_in_category,
                separator="|",
                flags="nlcap",
            )

            # merge 'dictionary' with global 'statistics_dictionary'
            statistics_dictionary = merge_two_dictionaries(
                statistics_dictionary, dictionary
            )

        # It is important to remove the MASK!
        r.mask(flags="r", quiet=True)

    # Add the "reclassified_base" map to "remove_at_exit" here,
    # so as to be after all reclassified maps that derive from it
    remove_map_at_exit(reclassified_base)

    if not print_only:
        g.region(
            raster=aggregation,
            nsres=ns_resolution,
            ewres=ew_resolution,
            flags="a",
            quiet=True,
        )
        r.patch(
            flags="",
            input=flows,
            output=flow_in_reclassified_base,
            quiet=True,
        )
        remove_map_at_exit(flow_in_reclassified_base)

        if vector:
            # Patch all flow vector maps in one
            v.patch(
                flags="e",
                input=flows,
                output=flow_in_reclassified_base,
                overwrite=True,
                quiet=True,
            )

        # export to csv
        if supply_filename:
            nested_dictionary_to_csv(supply_filename, statistics_dictionary)

        if use_filename:
            uses = compile_use_table(statistics_dictionary)
            dictionary_to_csv(use_filename, uses)

    # Maybe return list of flow maps?  Requires unique flow map names
    return flows
