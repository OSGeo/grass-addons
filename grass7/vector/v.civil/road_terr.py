# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 00:29:15 2014

@author: meskal
"""

import math
# import time

import road_base as Base
from grass.pygrass.raster import RasterRow

from grass.pygrass.vector.geometry import Point
from grass.pygrass.gis.region import Region
# from grass.pygrass.vector.geometry import Line
from grass.pygrass.vector.geometry import Boundary
# from grass.pygrass.vector.geometry import Area


def get_rgb(type_terr):
    """ Return
    """
    if type_terr == 'Cut':
        return '165:50:0'
    else:
        return '255:165:0'


def get_side(left):
    """ Return
    """
    if left:
        return 'left'
    else:
        return 'right'


# =============================================
# PLANT
# =============================================

class Talud(object):
    """ Return
    """

    def __init__(self, pks, cut, fill, left=True, terr=None):
        """ Return
        """
        self.pks = pks
        self.cut = [float(p) for p in cut]
        self.fill = [float(p) for p in fill]
        self.terr = terr

        self.left = left

        if self.left:
            self.g90 = -math.pi / 2
        else:
            self.g90 = math.pi / 2

        self.roadlines = []
        self.roadline = None

    def _get_cutfill_slope(self, r_pnt_d):
        """Return
        """
        for i in range(len(self.pks) - 1):
            if self.pks[i] <= r_pnt_d.npk < self.pks[i + 1]:

                if r_pnt_d.z < r_pnt_d.terr:
                    slope = self.cut
                else:
                    slope = self.fill

                if slope[i] is not None or slope[i + 1] is not None:

                    return slope[i] + ((r_pnt_d.npk - self.pks[i]) *
                                       (slope[i + 1] - slope[i])) / \
                                      (self.pks[i + 1] - self.pks[i])

    def _funct(self, r_pnt_d, len_i, sig, azim, slope):
        """ Return
        """
        x_1 = r_pnt_d.x + len_i * math.sin(azim)
        y_1 = r_pnt_d.y + len_i * math.cos(azim)
        z_t = self.terr.get_value(Base.Point(x_1, y_1))
        z_1 = r_pnt_d.z + sig * len_i * slope
        return dict(zip(['z_1', 'z_t', 'x_1', 'y_1'], [z_1, z_t, x_1, y_1]))

    def get_pnt_slope(self, r_pnt, r_pnt_d):
        """ Return
        """
        azim = r_pnt_d.azi + self.g90

        if r_pnt_d.z > r_pnt_d.terr:  # Terraplen
            sig = -1
            type_t = 'Fill'
        else:
            sig = 1
            type_t = 'Cut'

        z_t = r_pnt_d.terr
        z_1 = r_pnt_d.z

        slop = self._get_cutfill_slope(r_pnt_d)
        if slop is None:
            return None

        len_i = 0
        while -sig * z_1 > -sig * z_t or len_i > 1000:
            len_i += 1

            x_1 = r_pnt_d.x + len_i * math.sin(azim)
            y_1 = r_pnt_d.y + len_i * math.cos(azim)
            z_t = self.terr.get_value(Base.Point(x_1, y_1))
            z_1 = r_pnt_d.z + sig * len_i * slop

        len_a = len_i - 1
        len_b = len_i
        len_c = (len_a + len_b) / 2.0

        while (len_b - len_a) / 2.0 > 0.001:
            eq_c = self._funct(r_pnt_d, len_c, sig, azim, slop)
            eq_a = self._funct(r_pnt_d, len_a, sig, azim, slop)
            if eq_c['z_1'] == eq_c['z_t']:
                break
            elif (eq_a['z_1'] - eq_a['z_t']) * (eq_c['z_1'] - eq_c['z_t']) < 0:
                len_b = len_c
            else:
                len_a = len_c
            len_c = (len_a + len_b) / 2.0

        eq_c = self._funct(r_pnt_d, len_c, sig, azim, slop)
        pnt = Base.RoadPoint(Point(eq_c['x_1'], eq_c['y_1'], eq_c['z_1']),
                             r_pnt.npk, r_pnt_d.azi, '')
        pnt.terr_type = type_t
        pnt.dist_displ = pnt.distance(r_pnt)
        return pnt

    def get_pnts_slope(self, list_r_pnts, list_pnts_d):
        """Return
        """
        list_pnts_t = []
        for i, r_pnt_d in enumerate(list_pnts_d):
            if r_pnt_d is not None:
                pnt_t = self.get_pnt_slope(list_r_pnts[i], r_pnt_d)
                list_pnts_t.append(pnt_t)
            else:
                list_pnts_t.append(None)
        return list_pnts_t

    def split_slope_line(self, rline):
        """Return
        """
        list_pnts_t = [[]]
        for line in rline:
            if line is not None:
                pnt_ant = line
                break
        for pnt_t in rline:
            if pnt_t is not None:
                if pnt_ant.terr_type != pnt_t.terr_type:
                    list_pnts_t.append([])
                list_pnts_t[-1].append(pnt_t)
                pnt_ant = pnt_t
            elif list_pnts_t[-1] != []:
                list_pnts_t.append([])
        if list_pnts_t[-1] == []:
            del list_pnts_t[-1]
        return list_pnts_t

    def set_roadlines(self, roadline, roadline_d):
        """ Return
        """
        self.terr.set_pnts_terr(roadline_d)

        line1 = self.get_pnts_slope(roadline, roadline_d)
        name = 'Slope_' + get_side(self.left)
        attrs = [name, 1, get_side(self.left), 1, '0:0:0']
        self.roadline = Base.RoadLine(line1, attrs, name)
        lines = self.split_slope_line(line1)
        for i, line in enumerate(lines):
            if line != []:
                # Name lenght type param rgb
                name = 'Slope_' + get_side(self.left) + '_' + str(i + 1)
                attrs = [name, -1, line[-1].terr_type, i + 1,
                         get_rgb(line[-1].terr_type)]
                self.roadlines.append(Base.RoadLine(line, attrs, name))


# =============================================
# Taludes
# =============================================

class Taludes(object):
    """ Return
    """

    def __init__(self, polygon=None, tabla=None, terr=None):
        """ Return
        """
        self.polygon = polygon
        self.tabla = tabla
        self.terr = terr

        self.pks = []
        self.cut = {'left': [], 'right': []}
        self.fill = {'left': [], 'right': []}

        self._init_talud()

        self.talud_left = Talud(self.pks, self.cut['left'], self.fill['left'],
                                left=True, terr=self.terr)
        self.talud_right = Talud(self.pks, self.cut['right'],
                                 self.fill['right'], left=False,
                                 terr=self.terr)

    def __repr__(self):
        """ Return
        """
        return 'Taludes '

    def _init_talud(self):
        """ Return
        """
        for dat in self.tabla:

            self.pks.append(dat['pk'])
            self.cut['left'].append(dat['cut_left'])
            self.cut['right'].append(dat['cut_right'])
            self.fill['left'].append(dat['fill_left'])
            self.fill['right'].append(dat['fill_right'])

    def get_pnts(self, r_pnt, r_pnts_d):
        """ Return
        """
        pto1 = None
        pto2 = None
        if r_pnts_d[0][-1] is not None:
            pto1 = self.talud_left.get_pnt_slope(r_pnt, r_pnts_d[0][-1])
        if r_pnts_d[1][-1] is not None:
            pto2 = self.talud_right.get_pnt_slope(r_pnt, r_pnts_d[1][-1])
        return [pto1, pto2]

    def get_lines(self):
        """ Return
        """
        list_lines = []
        list_attrs = []
        for r_line in self.talud_left.roadlines:
            objs, values = r_line.get_line_attrs(set_leng=1)
            list_lines.extend(objs)
            list_attrs.extend(values)

        for r_line in self.talud_right.roadlines:
            objs, values = r_line.get_line_attrs(set_leng=1)
            list_lines.extend(objs)
            list_attrs.extend(values)

        return list_lines, list_attrs

    def set_roadlines(self, roadline, displ):
        """ Return
        """
        if displ.displines == []:
            return None, None

        self.talud_left.set_roadlines(roadline,
                                      displ.displines_left[-1].roadline)
        self.talud_right.set_roadlines(roadline,
                                       displ.displines_right[-1].roadline)

    def get_areas(self, displ):
        """ Return
        """
        areas = []
        list_attrs = []

        for r_line in self.talud_left.roadlines:
            line2 = [displ.displines_left[-1].roadline.get_by_pk(r_pnt.npk)
                     for r_pnt in r_line if r_pnt is not None]
            lines = r_line.get_area(line2)

            for j in range(len(lines)):
                list_attrs.extend([r_line.attrs])
            areas.extend(lines)

        for r_line in self.talud_right.roadlines:
            line2 = [displ.displines_right[-1].roadline.get_by_pk(r_pnt.npk)
                     for r_pnt in r_line if r_pnt is not None]
            lines = r_line.get_area(line2)

            for j in range(len(lines)):
                list_attrs.extend([r_line.attrs])
            areas.extend(lines)

        return areas, list_attrs

    def get_hull(self, displ):
        """ Return
        """
        line1 = []
        for i, pnt_t in enumerate(self.talud_left.roadline):
            if pnt_t is not None:
                line1.append(pnt_t)
            else:
                for dline in displ.displines_left[::-1]:
                    if dline.roadline[i] is not None:
                        line1.append(dline.roadline[i])
                        break
        line2 = []
        for i, pnt_t in enumerate(self.talud_right.roadline):
            if pnt_t is not None:
                line2.append(pnt_t)
            else:
                for dline in displ.displines_right[::-1]:
                    if dline.roadline[i] is not None:
                        line2.append(dline.roadline[i])
                        break
        line2 = line2[::-1]
        line2.append(line1[0])
        line1.extend(line2)
        for i, pto in enumerate(line1):
            line1[i].z = 0
        line = Boundary(points=line1)
        attrs = [['Hull', line.length()]]
        return [line], attrs


# =============================================
# Terrain
# =============================================

class Terrain(object):
    """ Return
    """

    def __init__(self, mapname=None):
        """ Return
        """
        self.mapname = mapname

        self.elev = []
        self._init_elev()

        region = Region()
        self.xref = region.west
        self.yref = region.north
        self.xres = region.ewres
        self.yres = region.nsres

    def _init_elev(self):
        """ Return
        """
        with RasterRow(self.mapname) as rrow:
            for row in rrow:
                self.elev.append([])
                for elem in row:
                    self.elev[-1].append(elem)

    def get_value(self, point):
        """ Return
        """
        pto_col = int((point.x - self.xref) / self.xres)
        pto_row = int((self.yref - point.y) / self.yres)

        return self.elev[pto_row][pto_col]

    def set_pnts_terr(self, list_r_pnts):
        """Return
        """
        for r_pnt in list_r_pnts:
            if r_pnt is not None:
                self.set_pnt_terr(r_pnt)
            else:
                return None

    def set_pnt_terr(self, r_pnt):
        """ Return
        """
        r_pnt.terr = self.get_value(r_pnt)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
