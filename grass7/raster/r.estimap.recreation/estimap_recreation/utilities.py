"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import csv


def merge_two_dictionaries(first, second):
    """Merge two dictionaries in via shallow copy.
    Source: https://stackoverflow.com/a/26853961/1172302"""
    merged_dictionary = first.copy()
    merged_dictionary.update(second)
    return merged_dictionary


def dictionary_to_csv(filename, dictionary):
    """Write a Python dictionary as CSV named 'filename'

    Parameters
    ----------
    filename :
        Name for output file

    dictionary :
        Name of input Python dictionary to write to 'filename'

    Returns
    -------
        This function does not return anything

    Examples
    --------
    """

    # write a header
    rows = [",".join(["category", "label", "value"])]

    # terminology: from 'base' and 'cover' maps
    for base_key, value in dictionary.items():
        if not value:
            continue
        base_category = base_key[0]
        base_label = base_key[1]  # .decode('utf-8')
        row = ",".join([base_category, base_label, str(value)])
        rows.append(row)

    with open(filename, "w") as fh:
        fh.write("\n".join(rows))


def nested_dictionary_to_csv(filename, dictionary):
    """Write out a nested Python dictionary as CSV named 'filename'

    Parameters
    ----------
    filename :
        Name for output file

    dictionary :
        Name of the input Python dictionary
    """

    # write a header
    rows = [",".join(["base", "base_label", "cover", "cover_label", "area", "count", "percents"])]

    # terminology: from 'base' and 'cover' maps
    for base_key, inner_dictionary in dictionary.items():
        base_category = base_key[0]
        base_label = base_key[1]  # .decode('utf-8')

        for cover_category, inner_value in inner_dictionary.items():
            if not inner_value:
                continue
            cover_label = inner_value[0]
            area = inner_value[1]
            pixel_count = inner_value[2]
            pixel_percentage = inner_value[3]
            row = ",".join([
                base_category,
                base_label,
                cover_category,
                cover_label,
                area,
                pixel_count,
                pixel_percentage,
            ])
            rows.append(row)

        with open(filename, "w") as fh:
            fh.write("\n".join(rows))


# This function should be better off this module  # FIXME
def get_coefficients(coefficients_string):
    """Returns coefficients from an input coefficients_string

    Parameters
    ----------
    coefficients_string:
        One string which lists a metric and coefficients separated by comma
        without spaces

    Returns
    -------
    metric:
        Metric to use an input option to the `r.grow.distance` module

    constant:
        A constant value for the 'attractiveness' function

    kappa:
        A Kappa coefficients for the 'attractiveness' function

    alpha:
        An alpha coefficient for the 'attractiveness' function

    score
        A score value to multiply by the generic 'attractiveness' function

    Examples
    --------
    ...
    """
    coefficients = coefficients_string.split(",")
    msg = "Distance function coefficients: "
    metric = coefficients[0]
    msg += "Metric='{metric}', ".format(metric=metric)
    constant = coefficients[1]
    msg += "Constant='{constant}', ".format(constant=constant)
    kappa = coefficients[2]
    msg += "Kappa='{Kappa}', ".format(Kappa=kappa)
    alpha = coefficients[3]
    msg += "Alpha='{alpha}', ".format(alpha=alpha)
    try:
        if coefficients[4]:
            score = coefficients[4]
            msg += "Score='{score}'".format(score=score)
            grass.verbose(_(msg))  # FIXME REMOVEME ?
            return metric, constant, kappa, alpha, score
    except IndexError:
        grass.verbose(_("Score not provided"))  # FIXME REMOVEME ?

    grass.verbose(_(msg))  # FIXME REMOVEME ?
    return metric, constant, kappa, alpha
