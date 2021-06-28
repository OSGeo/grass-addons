# -*- coding: utf-8 -*-
"""
Created on Thu Oct 23 01:06:18 2014

@author: meskal
"""

#
# import pygrass modules
#
import math

# from grass.pygrass.vector import VectorTopo
# import road_base as Base

# from grass.pygrass.vector.geometry import Point
# from grass.pygrass.vector.geometry import Line


class Marks(object):
    """Return"""

    def __init__(self, polygon, tabla, plant, vert):
        """Return"""
        self.polygon = polygon
        #        self.tabla_iter = tabla_iter
        self.plant = plant
        self.vert = vert

        self.tabla = tabla

    #        self.init_marks()

    def __str__(self):
        """Return"""
        return "TransLine(" + str(self.tabla) + ")"

    #    def init_marks(self):
    #        """ Return
    #        """
    #        for dats in self.tabla_iter:
    #
    #            if dats[5] is not None:
    #                self.list_dats.append(dict(zip(['pk', 'dist', 'elev', 'azi',
    #                                                'name', 'cod'], dats[1:7])))

    def num_marks(self):
        """Return"""

    def get_pnts(self):
        """Return"""
        list_pnts = []
        list_attrs = []
        for i, dats in enumerate(self.tabla):

            r_pnt = self.plant.get_roadpoint(dats["pk"])

            self.vert.set_elev(r_pnt)

            if "," in dats["dist"]:
                distances = dats["dist"].split(",")
                elevations = dats["elev"].split(",")
            else:
                distances = dats["dist"]
                elevations = dats["elev"]

            if dats["azi"] != "":
                azi = dats["azi"].split(",")
            else:
                azi = ["1"] * len(distances)

            for i, dist in enumerate(distances):
                m_pnt = r_pnt.parallel(float(dist), math.pi / 2)
                m_pnt.z = r_pnt.z + float(elevations[i])
                m_pnt.dist_displ = dist
                if azi[i] == "-1":
                    m_pnt.azi = m_pnt.azi + math.pi
                list_pnts.append(m_pnt)
                list_attrs.append(
                    [
                        m_pnt.npk,
                        round(90 - m_pnt.azi * 180 / math.pi + 360 + 90, 4),
                        dats["name"],
                        dats["cod"],
                        m_pnt.dist_displ,
                        m_pnt.z,
                    ]
                )
        return list_pnts, list_attrs
