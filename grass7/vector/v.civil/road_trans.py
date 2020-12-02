# -*- coding: utf-8 -*-
"""
Created on Sat Aug  2 14:20:17 2014

@author: meskal
"""

#
# import pygrass modules
#
import math

# from grass.pygrass.vector import VectorTopo
import road_base as Base

# from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line
# from grass.pygrass.vector.geometry import Point


class TransLine(object):
    """ Return
    """

    def __init__(self, r_pnt=None, dist_left=None, dist_right=None):
        """ Return
        """
        self.r_pnt = r_pnt
        self.dist_left = dist_left
        self.dist_right = dist_right

        self.displ_left = []
        self.displ_right = []

        self.talud_left = None
        self.talud_right = None

        self.terr_pnts = None

    def __str__(self):
        """ Return
        """
        return "TransLine(" + str(self.r_pnt.npk) + ")"

    def __repr__(self):
        """ Return
        """
        return "TransLine(" + str(self.r_pnt.npk) + ")"

    def length(self):
        """ Return
        """
        return self.dist_left + self.dist_right

    def _get_straight(self):
        """ Return
        """
        p_left = self.r_pnt.parallel(self.dist_left, -math.pi / 2)
        p_right = self.r_pnt.parallel(self.dist_right, math.pi / 2)
        return Base.Straight(p_left, p_right)

    def get_line(self):
        """ Return
        """
        p_left = self.r_pnt.parallel(self.dist_left, -math.pi / 2)
        p_right = self.r_pnt.parallel(self.dist_right, math.pi / 2)
        return Line([p_left, p_right])

    def set_displ(self, displaced):
        """ Return
        """
        self.displ_left, self.displ_right = displaced.find_cutoff(self.r_pnt)

    def set_talud(self, taludes, terr):
        """ Return
        """
        if self.displ_left != [] and self.displ_left[-1] is not None:

            terr.set_pnt_terr(self.displ_left[-1])
            self.talud_left = \
                taludes.talud_left.get_pnt_slope(self.r_pnt,
                                                 self.displ_left[-1])
#        if self.talud_left is None:
#            self.talud_left = Base.RoadPoint(Point(0,0,0))
#            self.talud_left.dist_displ = 0
#            self.talud_left.npk = -1

        if self.displ_right != [] and self.displ_right[-1] is not None:
            terr.set_pnt_terr(self.displ_right[-1])
            self.talud_right = \
                taludes.talud_right.get_pnt_slope(self.r_pnt,
                                                  self.displ_right[-1])
#        if self.talud_right is not None:
#            self.talud_right = Base.RoadPoint(Point(0,0,0))
#            self.talud_right.dist_displ = 0
#            self.talud_right.npk = -1

    def set_terr_pnts(self, terr):
        """ Return
        """
        max_left_width = self.max_left_width()
        straight_1 = self._get_straight()
        self.terr_pnts = straight_1.get_roadpnts(0, -1, 1)
        terr.set_pnts_terr(self.terr_pnts)

        if self.dist_left < max_left_width:
            rest = max_left_width - self.dist_left
            for i, r_pnt in enumerate(self.terr_pnts):
                self.terr_pnts[i].npk = rest + r_pnt.npk

    def get_ras_pnts(self):
        """ Return
        """
        max_left_width = self.max_left_width()
        line = []
        if self.talud_left is not None:

            self.talud_left.npk = max_left_width - self.talud_left.dist_displ
            line.append(self.talud_left)

        for r_pnt in self.displ_left[::-1]:
            if r_pnt is not None:
                r_pnt.npk = max_left_width - r_pnt.dist_displ
                line.append(r_pnt)

        r_pnt_c = Base.RoadPoint(self.r_pnt, max_left_width, self.r_pnt.azi)
        line.append(r_pnt_c)


        for r_pnt in self.displ_right:
            if r_pnt is not None:
                r_pnt.npk = max_left_width + r_pnt.dist_displ
                line.append(r_pnt)

        if self.talud_right is not None:
            self.talud_right.npk = max_left_width + self.talud_right.dist_displ
            line.append(self.talud_right)

        return line

    def max_left_width(self):
        """ Return
        """
        if self.talud_left is not None:
            return max(self.dist_left, self.talud_left.dist_displ)
        return self.dist_left

    def max_right_width(self):
        """ Return
        """

        if self.talud_right is not None:
            return max(self.dist_right, self.talud_right.dist_displ)
        return self.dist_right

    def _width_terr(self):
        """ Return
        """
        return self.talud_left.dist_displ + self.talud_right.dist_displ

    def _max_terr(self):
        """ Return
        """
        return max([r_pnt.terr for r_pnt in self.terr_pnts])

    def _min_terr(self):
        """ Return
        """
        return min([r_pnt.terr for r_pnt in self.terr_pnts])

    def _max_height_displ(self):
        """ Return
        """
        lista = self.displ_left + self.displ_right
        if self.talud_left is not None:
            lista += [self.talud_left]
        if self.talud_right is not None:
            lista += [self.talud_right]
        return max([r_pnt.z for r_pnt in lista if r_pnt is not None])

    def _min_height_displ(self):
        """ Return
        """
        lista = self.displ_left + self.displ_right
        if self.talud_left is not None:
            lista += [self.talud_left]
        if self.talud_right is not None:
            lista += [self.talud_right]
        return min([r_pnt.z for r_pnt in lista if r_pnt is not None])

    def max_height(self):
        """ Return
        """
        return math.ceil(max(self._max_terr(), self._max_height_displ()))

    def min_height(self):
        """ Return
        """
        return math.floor(min(self._min_terr(), self._min_height_displ()))

    def max_width(self):
        """ Return
        """
        return max(self._width_terr(), self.length())


class Trans(object):
    """ Return
    """

    def __init__(self, polygon, tabla_iter, plant, vert, terr):
        """ Return
        """
        self.polygon = polygon
        self.tabla_iter = tabla_iter
        self.plant = plant
        self.vert = vert
        self.terr = terr

        self.t_aligns = []
        self.leng_accum = [0]

        self._init_trans()

    def __getitem__(self, index):
        return self.t_aligns[index]

    def __setitem__(self, index, value):
        self.t_aligns[index] = value

    def __delitem__(self, index):
        del self.t_aligns[index]

    def __len__(self):
        return len(self.t_aligns)

    def __str__(self):
        """ Return
        """
        string = "[\n"
        for i in self.t_aligns:
            string += str(i)
        string += "]"
        return string

    def __repr__(self):
        """ Return
        """
        string = "[\n"
        for i in self.t_aligns:
            string += str(i)
        string += "]"
        return string

    def _init_trans(self):
        """ Return
        """
        dat_1 = []
        for i, dat_2 in enumerate(self.tabla_iter):

            if i >= 1:
                if dat_1['npk'] == 0:
                    continue
                start = dat_1
                end = dat_2

                r_pnts = self.plant.get_roadpnts(start['pk'], end['pk'],
                                                 start['npk'], start['npk'])
                self.vert.set_pnts_elev(r_pnts)

                if self.terr is not None:
                    self.terr.set_pnts_terr(r_pnts)

                for r_pnt in r_pnts:

                    dist_left = start['dist_left'] + \
                        ((r_pnt.npk - start['pk']) * (end['dist_left'] -
                         start['dist_left'])) / (end['pk'] - start['pk'])

                    dist_right = start['dist_right'] + \
                        ((r_pnt.npk - start['pk']) * (end['dist_right'] -
                         start['dist_right'])) / (end['pk'] - start['pk'])

                    trans = TransLine(r_pnt, dist_left, dist_right)
                    self.t_aligns.append(trans)
            dat_1 = dat_2

    def get_trans(self):
        """ Return
        """
        list_lines = []
        list_attrs = []
        for t_ali in self.t_aligns:
            list_lines.append(t_ali.get_line())
            list_attrs.append([t_ali.r_pnt.get_pk(),
                               t_ali.r_pnt.get_azi(),
                               t_ali.r_pnt.p_type,
                               round(t_ali.dist_left, 4),
                               round(t_ali.dist_right, 4), ''])
        return list_lines, list_attrs

    def get_pnts_trans(self, displ):
        """ Return
        """
        list_pnts = []
        list_attrs = []
        for t_ali in self.t_aligns:
            t_ali.set_displ(displ)

#            list_pnts.extend(t_ali.displ_left + t_ali.displ_right)
            for i, r_pnt in enumerate(t_ali.displ_left + t_ali.displ_right):
                if r_pnt is not None:
                    list_pnts.append(r_pnt)
                    list_attrs.append([r_pnt.get_pk(),
                                       r_pnt.get_azi(),
                                       t_ali.r_pnt.get_pk(),
                                       'Dist=' +
                                       str(round(r_pnt.dist_displ, 4)),
                                       'Displ=' + str(i + 1)])

        return list_pnts, list_attrs

    def get_pnts_trans_terr(self, displ, taludes, terr):
        """ Return
        """
        list_pnts = []
        list_attrs = []
        for t_ali in self.t_aligns:
            t_ali.set_talud(taludes, terr)

            for i, r_pnt in enumerate([t_ali.talud_left, t_ali.talud_right]):
                if r_pnt is not None and r_pnt.npk != -1:

                    list_pnts.append(r_pnt)
                    list_attrs.append([r_pnt.get_pk(),
                                       r_pnt.get_azi(),
                                       t_ali.r_pnt.get_pk(),
                                       'Dist=' +
                                       str(round(r_pnt.dist_displ, 4)),
                                       'Terr=' + str(i + 1)])
        return list_pnts, list_attrs

    def generate_pks(self, start, end, dpk, mpk, len_d, len_m):
        """ Return
        """
        r_pnts_d = self.plant.get_roadpnts(start, end, dpk, dpk)
        r_pnts_m = self.plant.get_roadpnts(start, end, mpk, mpk)

        list_trans = []
        list_attrs = []
        for r_pnt in r_pnts_d:
            if r_pnt in r_pnts_m:
                trans = TransLine(r_pnt, len_m, len_m)
            else:
                trans = TransLine(r_pnt, len_d, len_d)
            list_trans.append(trans.get_line())
            list_attrs.append([r_pnt.get_pk(), r_pnt.get_azi(), r_pnt.p_type,
                               ''])
        return list_trans, list_attrs

if __name__ == '__main__':
    import doctest
    doctest.testmod()
