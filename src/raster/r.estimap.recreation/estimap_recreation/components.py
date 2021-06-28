"""
@author Nikos Alexandris
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import grass.script as grass
from grass.pygrass.modules.shortcuts import raster as r
from .grassy_utilities import smooth_map


def append_map_to_component(raster, component_name, component_list):
    """Appends raster map to given list of components

    Parameters
    ----------
    raster :
        Input raster map name

    component_name :
        Name of the component to add the raster map to

    component_list :
        List of raster maps to add the input 'raster' map

    Returns
    -------

    Examples
    --------
    ...
    """
    component_list.append(raster)
    msg = "Map {name} included in the '{component}' component"
    msg = msg.format(name=raster, component=component_name)
    grass.verbose(_(msg))


def smooth_component(component, method, size):
    """
    component:

    method:

    size:
    """
    try:
        msg = "Smoothing component '{c}'"
        grass.verbose(_(msg.format(c=component)))
        if len(component) > 1:
            for item in component:
                smooth_map(item, method=method, size=size)
        else:
            smooth_map(component[0], method=method, size=size)

    except IndexError:
        grass.verbose(_("Index Error"))  # FIXME: some useful message... ?


def classify_recreation_component(component, rules, output_name):
    """
    Recode an input recreation component based on given rules

    To Do:

    - Potentially, test range of input recreation component, i.e. ranging in
      [0,1]

    Parameters
    ----------
    component :
        Name of input raster map

    rules :
        Rules for r.recode

    output_name :
        Name for output raster map

    Returns
    -------
        Does not return any value

    Examples
    --------
    ...

    """
    r.recode(input=component, rules="-", stdin=rules, output=output_name)
