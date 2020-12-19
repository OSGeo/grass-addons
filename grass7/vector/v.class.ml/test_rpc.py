# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 01:47:42 2013

@author: pietro
"""
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point
from grass.pygrass.function import get_mapset_vector


def add_points(vname, vmapset='', *points):
    """
    >>> add_points('new', (1, 2), (2, 3), (3, 4))
    """
    mapset = get_mapset_vector(vname, vmapset)
    mode = 'rw' if mapset else 'w'
    with VectorTopo(vname, mapset, mode=mode) as vct:
        for x, y in points:
            vct.write(Point(x, y))


ciface = RPCServer()
check = ciface.call(function=add_points, args=('new', (1, 2), (2, 3), (3, 4)))
