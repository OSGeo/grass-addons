#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
@author: Nikos Alexandris | October 2014
"""

"""
Constants for the HPFA Image Fusion Technique:
Kernel Size, Center Value, Modulation Factor (all depend on Resolution Ratio).

Sources:

- "Optimizing the High-Pass Filter Addition Technique for Image Fusion",
Ute G. Gangkofner, Pushkar S. Pradhan, and Derrold W. Holcomb (2008).

- “ERDAS IMAGINE.” Accessed March 19, 2015.
http://doc.hexagongeospatial.com/ERDAS%20IMAGINE/ERDAS_IMAGINE_Help/#ii_hpfmerge_mergedialog.htm.

"""

RATIO_RANGES = (
    (1, 2.5),
    (2.5, 3.5),
    (3.5, 5.5),
    (5.5, 7.5),
    (7.5, 9.5),
    (9.5, float('inf')))

KERNEL_SIZES = (5, 7, 9, 11, 13, 15)

MATRIX_PROPERTIES = list(zip(RATIO_RANGES, KERNEL_SIZES))


# Replicating ERDAS' Imagine parameters -------------------------------------
CENTER_CELL = {
    'Low': [24, 48, 80, 120, 168, 336],
    'Mid': [28, 56, 93, 150, 210, 392],
    'High': [32, 64, 106, 180, 252, 448]}

# Can't find a unique sequence pattern, so... python fun below: =============
#ks = (5, 7, 9, 11, 13, 15)
#lo = list([(s**2-1) for s in ks[0:-1]])
#lo.append(int((ks[-1]**2-1)*1.5))
#inc = list([v/6 for v in lo[0:3]])
#inc.extend([v/4 for v in lo[3:5]])
#inc.append(lo[-1]/6)
#mi = list([a + b for a, b in zip(lo, inc)])
#hi = list([a + b for a, b in zip(mi, inc)])
#CENTER_CELL = {'High': hi, 'Low': lo, 'Mid': mi}
# ===========================================================================


MODULATOR = {
    'Min': [0.20, 0.35, 0.35, 0.50, 0.65, 1.00],
    'Mid': [0.25, 0.50, 0.50, 0.65, 1.00, 1.35],
    'Max': [0.30, 0.65, 0.65, 1.00, 1.40, 2.00]}

MODULATOR_2 = {'Min': 0.25, 'Mid': 0.35, 'Max': 0.50}

FILTER_TEMPLATE = """\
MATRIX    {size}
{kernel}
DIVISOR   {divisor}
TYPE      {type}
"""
