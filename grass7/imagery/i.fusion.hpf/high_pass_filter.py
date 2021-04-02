#!/usr/bin/env python


"""
@author: Nikos Alexandris | Created on 13:02:59, Nov 3 2014
"""

import os
from constants import MATRIX_PROPERTIES, CENTER_CELL, MODULATOR, MODULATOR_2, FILTER_TEMPLATE


def get_kernel_size(ratio):
    """
    High Pass Filter Additive image fusion compatible kernel size.
    Based on a float ratio, ranging in (1.0, 10.0).
    Returns a single integer
    """
    kernel_size = [k for ((lo, hi), k) in MATRIX_PROPERTIES if lo <= ratio < hi][0]
    return kernel_size


def get_center_cell(level, kernel_size):
    """
    High Pass Filter Additive image fusion compatible kernel center
    cell value.
    """
    level = level.capitalize()
    kernel_size_idx = [k for ((lo, hi), k) in MATRIX_PROPERTIES].index(kernel_size)
    center = [cc for cc in CENTER_CELL[level]][kernel_size_idx]
    return center


def get_modulator_factor(modulation, ratio):
    """
    Return the modulation factor for the first pass of the
    High-Pass Filter Addition Technique for Image Fusion.

    The modulation factor determines the image's Cripsness.

    Parameters
    ----------
    modulation: str
        Possible values are: `"min", "mid", max"`.
    ratio: int
        The resolution ratio between the high resolution pancrhomatic data
        and the lower resolution spectral data.

    Returns
    -------
    modulation_factor: float

    """
    kernel_size = get_kernel_size(ratio)
    kernel_size_idx = [k for ((lo, hi), k) in MATRIX_PROPERTIES].index(kernel_size)
    modulation = modulation.capitalize()
    modulation_factor = [mf for mf in MODULATOR[modulation]][kernel_size_idx]
    return modulation_factor


def get_modulator_factor2(modulation):
    """
    Return the modulation factor for the second pass of the
    High-Pass Filter Addition Technique for Image Fusion.

    The modulation factor determines the image's Cripsness.

    Parameters
    ----------
    modulation: str
        Possible values are: `"min", "mid", max"`.

    Returns
    -------
    modulation_factor: float

    """
    modulation = modulation.capitalize()
    modulation_factor = MODULATOR_2[modulation]
    return modulation_factor


def get_row(size):
    """ Return a matrix row consisting of -1. """
    row = [-1] * size
    return row


def get_mid_row(size, center):
    """
    Return a matrix row consisting of -1 except of the center value which equals `center`.
    """
    row = get_row(size)
    row[size // 2] = center
    return row


def get_kernel(size, level):
    """
    Return a compatible Kernel (`size` x `size`) for the
    High-Pass Filter Addition Technique for Image Fusion.

    Parameters
    ----------
    size: int
        An odd integer specifying the size of the kernel (i.e. number or rows and columns).
    level: str

    Raises
    ------
    ValueError: If `size` is not an odd integer.

    """

    if size % 2 != 1:
        raise ValueError("Size must be an odd integer, not <%r>" % size)
    center = get_center_cell(level, size)
    kernel = [get_row(size)] * size
    kernel[size // 2] = get_mid_row(size, center)
    return kernel


def matrix_to_string(matrix):
    lines = [" ".join(str(item) for item in row) for row in matrix]
    string = os.linesep.join(lines)
    return string


def get_high_pass_filter(ratio, level='Low', divisor=1, type='P'):
    """
    Return a filter suitable for applying the High-Pass Filter Addition
    Technique for Image Fusion using GRASS-GIS' `r.mfilter` module.

    Returns a *NIX ASCII multi-line string whose contents is
    a matrix defining the way in which raster data will be filtered
    by r.mfilter. The format of this file is described in r.mfilter's
    manual.

    """
    size = get_kernel_size(ratio)
    kernel = get_kernel(size, level)
    filter = FILTER_TEMPLATE.format(
        kernel=matrix_to_string(kernel),
        divisor=divisor,
        type=type,
        size=size,
    )
    return filter
