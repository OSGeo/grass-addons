# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 20:36:10 2014

@author: meskal
"""

#
# import pygrass modules
#
import math

# from grass.pygrass.vector import VectorTopo
# import road_base as Base

# from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line


class Parabola(object):
    """ Return
    """

    def __init__(self, k_v=0, pnt_1=None, pnt_v=None, pnt_2=None, plant=None):
        """ Return
        """
        self.k_v = k_v
        self.pnt_1 = pnt_1
        self.pnt_v = pnt_v
        self.pnt_2 = pnt_2

        self.slope_in = self.pnt_1.slope2(self.pnt_v)
        self.slope_out = self.pnt_v.slope2(self.pnt_2)

        self.pnt_in = pnt_v
        self.pnt_out = pnt_v

        self._init_align(plant)
#        self.vtype = None
        self.vert_type()

    def _init_align(self, plant):
        """ Return
        """
        if self.k_v != 0:
            # B=Kv*phi**2/8

            self.pnt_in = plant.get_roadpoint(self.pnt_v.npk -
                                              (self.length() / 2))

            self.pnt_in.z = self.pnt_v.z - self.slope_in * (self.length() / 2)

            self.pnt_out = plant.get_roadpoint(self.pnt_v.npk +
                                               (self.length() / 2))
            self.pnt_out.z = self.pnt_v.z + self.slope_out * (self.length() /
                                                              2)

        self.pnt_in.v_param = self.slope_in
        self.pnt_in.v_type = 'in'
        self.pnt_v.v_param = self.k_v
        self.pnt_v.v_type = 'v'
        self.pnt_out.v_param = self.slope_out
        self.pnt_out.v_type = 'end'

    def length(self):
        """ Return
        """
        phi = (self.slope_in - self.slope_out)
        len_tan = self.k_v * phi / 2
        return 2 * len_tan

    def true_length(self):
        """ Return
        """
        return (self.pnt_2.npk - self.pnt_1.npk) / math.cos(self.slope_in)

    def vert_type(self):
        """ Return
        """
        if self.slope_in < 0 and self.slope_out > 0:
            return 'Concave'
        elif self.slope_in > 0 and self.slope_out < 0:
            return 'Convex'
        elif self.slope_in >= 0 and self.slope_out > 0:
            if self.slope_in < self.slope_out:
                return 'Concave'
            else:
                return 'Convex'
        elif self.slope_in < 0 and self.slope_out <= 0:
            if self.slope_in > self.slope_out:
                return 'Concave'
            else:
                return 'Convex'

    def grass_rgb(self):
        """ Return
        """
        if self.vert_type() == 'Concave':
            return '0:255:0'
        else:
            return '0:128:0'

    def is_in(self, r_pnt):
        """ Return
        """
        if self.pnt_in.npk <= r_pnt.npk <= self.pnt_out.npk:
            return True
        else:
            return False

    def get_elev(self, r_pnt):
        """ Return
        """
        r_pnt.z = self.pnt_in.z + self.slope_in * \
            (r_pnt.npk - self.pnt_in.npk) - \
            (1 / (2 * self.k_v)) * (r_pnt.npk - self.pnt_in.npk) ** 2
        r_pnt.v_type = self.vert_type()
        r_pnt.v_param = round(100 * (self.slope_in - (1 / self.k_v) *
                              (r_pnt.npk - self.pnt_in.npk)), 4)

    def get_charact(self):
        """ Return
        """
        return [self.pnt_in, self.pnt_v]

    def get_charact_attrs(self):
        """ Return
        """
        return [[self.pnt_in.get_pk(), self.pnt_in.v_type,
                 round(self.pnt_in.v_param, 4)],
                [self.pnt_v.get_pk(), self.pnt_v.v_type,
                 round(self.pnt_v.v_param, 4)]]


class VStraight(object):
    """ Return
    """

    def __init__(self, pnt_in=None, pnt_out=None):
        """ Return
        """
        self.pnt_in = pnt_in
        self.pnt_out = pnt_out

        self.slope_in = self.pnt_in.slope2(self.pnt_out)
        self.pnt_in.v_param = self.slope_in
        self.pnt_in.v_type = 'in'
        self.pnt_out.v_param = self.slope_in
        self.pnt_out.v_type = 'end'

    def length(self):
        """ Return
        """
        return self.pnt_out.npk - self.pnt_in.npk

    def true_length(self):
        """ Return
        """
        return (self.pnt_out.npk - self.pnt_in.npk) / math.cos(self.slope_in)

    def vert_type(self):
        """ Return
        """
        if self.slope_in > 0:
            return 'Up'
        else:
            return 'Down'

    def grass_rgb(self):
        """ Return
        """
        if self.slope_in > 0:
            return '0:0:255'
        else:
            return '255:0:0'

    def is_in(self, r_pnt):
        """ Return
        """
        if round(self.pnt_in.npk, 4) <= round(r_pnt.npk, 4) <= \
                round(self.pnt_out.npk, 4):
            return True
        else:
            return False

    def get_elev(self, r_pnt):
        """ Return
        """
        r_pnt.z = self.pnt_in.z + self.slope_in * (r_pnt.npk - self.pnt_in.npk)
        r_pnt.v_type = self.vert_type()
        r_pnt.v_param = round(100 * self.slope_in, 4)

    def get_charact(self):
        """ Return
        """
        return [self.pnt_in]

    def get_charact_attrs(self):
        """ Return
        """
        return [[self.pnt_in.get_pk(), self.pnt_in.v_type,
                 round(self.pnt_in.v_param, 4)]]


# =============================================
# Vert
# =============================================

class Vert(object):
    """ Return
    """

    def __init__(self, polygon, tabla_iter, plant):
        """ Return
        """
        self.polygon = polygon
        self.tabla_iter = tabla_iter
        self.plant = plant

        self.aligns = []
        self.leng_accum = [0]

        self._init_vert()

    def __str__(self):
        """ Return
        """
        string = "["
        for i in self.aligns:
            string += str(i)
        string += "]"
        return string

    def _init_vert(self):
        """ Return
        """
        dat_1 = []
        dat_2 = []
        leng_tot = 0
        for i, dat_3 in enumerate(self.tabla_iter):

            if i == 1:
                end_pnt = self.plant.get_roadpoint(dat_2['pk'])
                end_pnt.z = dat_2['elev']

                pnt_2 = self.plant.get_roadpoint(-1)
                pnt_2.z = dat_3['elev']

            if i >= 2:
                if i == 2:
                    end_pnt = self.plant.get_roadpoint(dat_1['pk'])
                    end_pnt.z = dat_1['elev']

                pnt_v = self.plant.get_roadpoint(dat_2['pk'])
                pnt_v.z = dat_2['elev']

                pnt_2 = self.plant.get_roadpoint(dat_3['pk'])

                pnt_2.z = dat_3['elev']

                parabola = Parabola(dat_2['kv'], end_pnt, pnt_v, pnt_2,
                                    self.plant)

                straight = VStraight(end_pnt, parabola.pnt_in)

                self.aligns.append(straight)
                leng_tot += straight.length()
                self.leng_accum.append(leng_tot)

                self.aligns.append(parabola)
                leng_tot += parabola.length()
                self.leng_accum.append(leng_tot)

                end_pnt = parabola.pnt_out

            dat_1 = dat_2
            dat_2 = dat_3

            if i == len(self.tabla_iter) - 1:

                straight = VStraight(end_pnt, pnt_2)
                self.aligns.append(straight)
                leng_tot += straight.length()
                self.leng_accum.append(leng_tot)

    def set_elev(self, r_pnt):
        """ Return
        """
        for ali in self.aligns:
            if ali.is_in(r_pnt):
                ali.get_elev(r_pnt)

    def set_pnts_elev(self, list_r_pnts):
        """ Return
        """
        for r_pnt in list_r_pnts:
            self.set_elev(r_pnt)

    def set_lines_elev(self, list_r_lines):
        """ Return
        """
        for list_r_lines in list_r_lines:
            self.set_pnts_elev(list_r_lines)

    def get_segments_pnts(self, list_r_pnts, line=False):
        """Return
        """
        r_lines = []
        list_attrs = []
        for ali in self.aligns:
            pnts_align = [ali.pnt_in]
            for r_pnt in list_r_pnts:
                if ali.is_in(r_pnt):
                    pnts_align.append(r_pnt)
            pnts_align.append(ali.pnt_out)
            list_attrs.append([ali.pnt_in.get_pk(), ali.vert_type(),
                               round(ali.length(), 4),
                               round(ali.slope_in, 4), ali.grass_rgb()])
            if line:
                r_lines.append(Line(pnts_align))
            else:
                r_lines.append(pnts_align)
        return r_lines, list_attrs

    def get_charact_pnts(self):
        """ Return
        """
        list_pnts = []
        list_attrs = []
        for ali in self.aligns:
            list_pnts.extend(ali.get_charact())
            list_attrs.extend(ali.get_charact_attrs())
        ali = self.aligns[-1]
        list_pnts.append(ali.pnt_out)
        list_attrs.append([ali.pnt_out.get_pk(), ali.pnt_out.v_type,
                           round(ali.pnt_out.v_param, 4)])
        return list_pnts, list_attrs

if __name__ == '__main__':
    import doctest
    doctest.testmod()
