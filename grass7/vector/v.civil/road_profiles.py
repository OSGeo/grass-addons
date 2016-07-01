# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 00:29:15 2014

@author: meskal
"""

#
# import pygrass modules
#
import math

# import road_base as Base
# from grass.pygrass.raster import RasterRow

from grass.pygrass.vector.geometry import Point
from grass.pygrass.gis.region import Region
from grass.pygrass.vector.geometry import Line


class LongProfile(object):
    """ Return
    """
    def __init__(self, options, scale, offset='0,0'):
        """ Return
        """
        opts = options.split(',')
        self.mark_lon = float(opts[0])
        self.mark_x_dist = int(opts[1])
        self.mark_y_dist = int(opts[2])
        self.dist_ejes_x = float(opts[3])
        self.scale = float(scale)

        reg = Region()
        self.zero_x = int(reg.west) + int(offset.split(',')[0])
        self.zero_y = int(reg.south) + int(offset.split(',')[1])

        self.max_elev = 0
        self.min_elev = 0
        self.alt_y = 0

    def set_maxmin(self, r_line):
        """Return
        """
        max_z = max([r_pnt.z for r_pnt in r_line])
        max_t = max([r_pnt.terr for r_pnt in r_line])
        min_z = min([r_pnt.z for r_pnt in r_line])
        min_t = min([r_pnt.terr for r_pnt in r_line])

        self.max_elev = math.ceil(max(max_z, max_t))
        self.min_elev = math.floor(min(min_z, min_t))

        self.alt_y = int((self.max_elev - self.min_elev) * self.scale +
                         self.zero_y)
#        if self.alt_y % int(self.mark_y_dist * self.scale) != 0:
#            self.alt_y += int(self.mark_y_dist * self.scale)

    def _axis_y(self):
        """Return
        """
        return [Line([Point(self.zero_x, self.zero_y),
                      Point(self.zero_x, self.alt_y)])], [['Axis Y', '', '']]

    def _axis_x(self, r_line):
        """Return
        """
        lines = []
        for j in range(0, 4):
            lines.append(Line([Point(self.zero_x,
                                     self.zero_y - j * self.dist_ejes_x),
                               Point(self.zero_x + r_line[-1].npk,
                                     self.zero_y - j * self.dist_ejes_x)]))
        return lines, [['Axis X', '', ''], ['Elevation', '', ''],
                       ['Terrain', '', ''], ['Red elevation', '', '']]

    def get_axes(self, puntos):
        """Return
        """
        prof_axes, prof_axes_attrs = self._axis_y()
        prof_axes_x, prof_axes_attrs_x = self._axis_x(puntos)
        prof_axes.extend(prof_axes_x)
        prof_axes_attrs.extend(prof_axes_attrs_x)

        return prof_axes, prof_axes_attrs

    def _axis_y_marks(self):
        """Return
        """
        mark_y = []
        labels = []
        lim_sup = self.alt_y
        if lim_sup % int(self.mark_y_dist * self.scale) != 0:
            lim_sup += int(self.mark_y_dist * self.scale)
        for i in range(self.zero_y, lim_sup, int(self.mark_y_dist *
                                                 self.scale)):
            # labels.append(self.min_elev + i / self.scale)
            labels.append(self.min_elev + (i - self.zero_y) / self.scale)
            mark_y.append(Line([Point(self.zero_x - self.mark_lon, i),
                                Point(self.zero_x + self.mark_lon, i)]))
        return mark_y, labels

    def _axis_x_marks(self, r_line):
        """Return
        """
        lim_sup = int(r_line[-1].npk)
        if lim_sup % self.mark_x_dist != 0:
            lim_sup += self.mark_x_dist
        rang = range(0, lim_sup, self.mark_x_dist)

        label_npk, label_z, label_terr, label_cotaroja = [], [], [], []
        for r_pnt in r_line:
            if r_pnt.npk in rang:
                # pnts_marks.append(r_pnt)
                label_npk.append(r_pnt.npk)
                label_z.append(round(r_pnt.z, 4))
                label_terr.append(round(r_pnt.terr, 4))
                label_cotaroja.append(round(r_pnt.z - r_pnt.terr, 4))
        label_npk.append(int(r_line[-1].npk))
        label_z.append(r_line[-1].z)
        label_terr.append(r_line[-1].terr)
        label_cotaroja.append(r_line[-1].z - r_line[-1].terr)
        labels_lines = label_npk + label_z + label_terr + label_cotaroja

        rang = range(self.zero_x, self.zero_x + lim_sup, self.mark_x_dist)

        lines = []
        for j in range(0, 4):
            mark_x = []
            for i in rang:
                mark_x.append(Line([
                    Point(i, self.zero_y - self.mark_lon - j *
                          self.dist_ejes_x),
                    Point(i, self.zero_y + self.mark_lon - j *
                          self.dist_ejes_x)]))
            lines.extend(mark_x)

        return lines, labels_lines

    def get_axes_marks(self, puntos):
        """Return
        """
        prof_ticks, prof_ticks_attrs = self._axis_y_marks()
        prof_ticks_x, prof_ticks_attrs_x = self._axis_x_marks(puntos)
        prof_ticks.extend(prof_ticks_x)
        prof_ticks_attrs.extend(prof_ticks_attrs_x)
        prof_ticks_attrs = [[str(tick)] for tick in prof_ticks_attrs]
        return prof_ticks, prof_ticks_attrs

    def _ras_segments(self, vert_segs):
        """Return
        """
        lines = []
        for r_line in vert_segs:

            lines.append(self._ras(r_line))
        return lines

    def _ras(self, r_line):
        """Return(self.max_elev - self.min_elev)
        """
        line = []
        for r_pnt in r_line:
            line.append(Point(r_pnt.npk + self.zero_x,
                              (r_pnt.z - self.min_elev) * self.scale +
                              self.zero_y))
        return Line(line)

    def _terr(self, r_line):
        """Return
        """
        line = []
        for r_pnt in r_line:
            line.append(Point(r_pnt.npk + self.zero_x,
                              (r_pnt.terr - self.min_elev) * self.scale +
                              self.zero_y))
        return Line(line)

    def get_ras_terr(self, puntos, vert):
        """Return
        """
        vert_segs, vert_attrs = vert.get_segments_pnts(puntos)
        prof_segs = self._ras_segments(vert_segs)

        prof_terr = self._terr(puntos)
        prof_terr_attrs = ['0+000.0', 'Terrain', '0', '0', '']
        prof_segs.append(prof_terr)
        vert_attrs.append(prof_terr_attrs)

        return prof_segs, vert_attrs

    def charact_pnts(self, vert):
        """Return
        """
        char_r_pnts, char_r_pnts_attrs = vert.get_charact_pnts()
        list_r_pnts = []
        for r_pnt in char_r_pnts:
            list_r_pnts.append(Point(r_pnt.npk + self.zero_x,
                                     (r_pnt.z - self.min_elev) * self.scale +
                                     self.zero_y))
        return list_r_pnts, char_r_pnts_attrs


class TransProfiles(object):
    """ Return
    """
    def __init__(self, options1, options2, scale, offset='0,0'):
        """ Return
        """
        self.opts1 = dict(zip(['mark_lon', 'mark_x_dist', 'mark_y_dist'],
                              [int(opt) for opt in options1.split(',')]))

        self.opts2 = dict(zip(['rows', 'dist_axis_x', 'dist_axis_y'],
                              [int(opt) for opt in options2.split(',')]))

        self.scale = float(scale)

        self.cols = 0
        reg = Region()
        self.zero_x = int(reg.west) + int(offset.split(',')[0])
        self.zero_y = int(reg.south) + int(offset.split(',')[1])

        self.mat_trans = []

        self.rows_height = []
        self.cols_width_left = [0]
        self.cols_width_right = [0]

        self.centers = []

    def set_maxmin(self, trans, terr):
        """Return
        """
        self.cols = int(math.ceil(len(trans) / self.opts2['rows']))
        step = 0
        maxtix = []
        for i in range(self.cols):
            row = []
            for j in range(self.opts2['rows']):
                trans[step].set_terr_pnts(terr)
                row.append(trans[step])
                step = step + 1
            maxtix.append(row)

        transp = [[row1[i] for row1 in maxtix] for i in range(len(maxtix[0]))]
        for row in maxtix:
            max_col_left = math.ceil(max([tran.max_left_width()
                                          for tran in row]))
            max_col_right = math.ceil(max([tran.max_right_width()
                                           for tran in row]))
            if max_col_left % self.opts1['mark_x_dist']:
                max_col_left += self.opts1['mark_x_dist']
                max_col_left -= max_col_left % self.opts1['mark_x_dist']
            if max_col_right % self.opts1['mark_x_dist']:
                max_col_right += self.opts1['mark_x_dist']
                max_col_right -= max_col_right % self.opts1['mark_x_dist']

            self.cols_width_left.append(max_col_left)
            self.cols_width_right.append(max_col_right)

        for row in transp:

            difer = [tran.max_height() - tran.min_height() for tran in row]
            max_height = max(difer) * self.scale
            lim_sup = max([self._get_trans_lim_sup(tran) for tran in row])
            self.rows_height.append(max([max_height, lim_sup]))

        total_height = sum(self.rows_height) + (self.opts2['dist_axis_y'] *
                                                self.opts2['rows'])
        self.zero_y += total_height
        self.mat_trans = maxtix

    def set_centers(self):
        """Return
        """
        orig_x = self.zero_x
        for i in range(self.cols):
            orig_x += self.cols_width_left[i] + self.cols_width_right[i]
            row = []
            orig_y = self.zero_y
            for j in range(self.opts2['rows']):
                orig_y -= self.rows_height[j] + self.opts2['dist_axis_y']
                row.append(Point(orig_x, orig_y))
            orig_x += self.opts2['dist_axis_x']
            self.centers.append(row)

    def _get_trans_lim_sup(self, trans):
        """Return
        """
        lim_sup = ((trans.max_height() - trans.min_height()) * self.scale)

        if lim_sup % int(self.opts1['mark_y_dist'] * self.scale) != 0:
            lim_sup += int(self.opts1['mark_y_dist'] * self.scale)
            lim_sup -= lim_sup % int(self.opts1['mark_y_dist'] * self.scale)
        return lim_sup

    def _axes_y(self):
        """Return
        """
        list_lines = []
        list_attrs = []
        for i in range(self.cols):
            for j in range(self.opts2['rows']):
                lim_sup = self._get_trans_lim_sup(self.mat_trans[i][j])
                pnt2 = Point(self.centers[i][j].x, self.centers[i][j].y +
                             lim_sup)
                list_lines.append(Line([self.centers[i][j], pnt2]))
                list_attrs.append(['Axis Y', '', ''])
        return list_lines, list_attrs

    def _axes_y_marks(self):
        """Return
        """
        mark_y = []
        labels = []

        for i in range(self.cols):
            for j in range(self.opts2['rows']):
                lim_sup = self._get_trans_lim_sup(self.mat_trans[i][j])

                for k in range(0, int(lim_sup) + 1,
                               int(self.opts1['mark_y_dist'] * self.scale)):

                    labels.append([self.mat_trans[i][j].min_height() + k /
                                   self.scale])
                    mark_y.append(Line([Point(self.centers[i][j].x -
                                              self.opts1['mark_lon'], k +
                                              self.centers[i][j].y),
                                        Point(self.centers[i][j].x +
                                              self.opts1['mark_lon'], k +
                                              self.centers[i][j].y)]))
        return mark_y, labels

    def _axes_x(self):
        """Return
        """
        list_lines = []
        list_attrs = []
        for i in range(self.cols):
            for j in range(self.opts2['rows']):
                pnt2 = Point(self.centers[i][j].x +
                             self.cols_width_left[i + 1] +
                             self.cols_width_right[i + 1],
                             self.centers[i][j].y)
                list_lines.append(Line([self.centers[i][j], pnt2]))
                list_attrs.append(['Axis X', '', ''])
        return list_lines, list_attrs

    def _axes_x_marks(self):
        """Return
        """
        mark_x = []
        labels = []
        for i in range(self.cols):
            for j in range(self.opts2['rows']):

                for k in range(int(self.cols_width_left[i + 1]), 0,
                               -int(self.opts1['mark_x_dist'])):
                    pnt1 = Point(self.centers[i][j].x +
                                 self.cols_width_left[i + 1] - k,
                                 self.centers[i][j].y - self.opts1['mark_lon'])
                    pnt2 = Point(self.centers[i][j].x +
                                 self.cols_width_left[i + 1] - k,
                                 self.centers[i][j].y + self.opts1['mark_lon'])
                    mark_x.append(Line([pnt1, pnt2]))
                    labels.append([-k])

                pnt1 = Point(self.centers[i][j].x +
                             self.cols_width_left[i + 1],
                             self.centers[i][j].y - self.opts1['mark_lon'] - 1)
                pnt2 = Point(self.centers[i][j].x +
                             self.cols_width_left[i + 1],
                             self.centers[i][j].y + self.opts1['mark_lon'] + 1)
                mark_x.append(Line([pnt1, pnt2]))
                labels.append([0])

                for k in range(int(self.opts1['mark_x_dist']),
                               int(self.cols_width_right[i + 1]) + 1,
                               int(self.opts1['mark_x_dist'])):
                    pnt1 = Point(self.centers[i][j].x +
                                 self.cols_width_left[i + 1] + k,
                                 self.centers[i][j].y - self.opts1['mark_lon'])
                    pnt2 = Point(self.centers[i][j].x +
                                 self.cols_width_left[i + 1] + k,
                                 self.centers[i][j].y + self.opts1['mark_lon'])
                    mark_x.append(Line([pnt1, pnt2]))
                    labels.append([k])

        return mark_x, labels

    def get_axes(self):
        """Return
        """
        axes, axes_attrs = self._axes_y()
        axes_x, axes_x_attrs = self._axes_x()
        axes.extend(axes_x)
        axes_attrs.extend(axes_x_attrs)

        return axes, axes_attrs

    def get_axes_marks(self):
        """Return
        """
        prof_ticks, prof_ticks_attrs = self._axes_y_marks()
        prof_ticks_x, prof_ticks_attrs_x = self._axes_x_marks()
        prof_ticks.extend(prof_ticks_x)
        prof_ticks_attrs.extend(prof_ticks_attrs_x)

        return prof_ticks, prof_ticks_attrs

    def _ras(self):
        """Return
        """
        list_lines = []
        list_attrs = []
        for i, col in enumerate(self.mat_trans):
            for j, tran in enumerate(col):
                line = []
                for r_pnt in tran.get_ras_pnts():
                    diff = self.cols_width_left[i + 1] - tran.max_left_width()
                    line.append(Point(r_pnt.npk + self.centers[i][j].x + diff,
                                      (r_pnt.z - tran.min_height()) *
                                      self.scale + self.centers[i][j].y))
                list_lines.append(Line(line))
                list_attrs.append([tran.r_pnt.npk, 'Ras', tran.length(), '',
                                   '0:0:255'])
        return list_lines, list_attrs

    def ras_pnts(self):
        """Return
        """
        list_pnts = []
        list_attrs = []
        for i, col in enumerate(self.mat_trans):
            for j, tran in enumerate(col):
                for r_pnt in tran.get_ras_pnts():

                    diff = self.cols_width_left[i + 1] - tran.max_left_width()
                    list_pnts.append(Point(r_pnt.npk + self.centers[i][j].x +
                                           diff,
                                           (r_pnt.z - tran.min_height()) *
                                           self.scale +
                                           self.centers[i][j].y))
                    list_attrs.append([r_pnt.dist_displ, round(r_pnt.z, 4),
                                       round(r_pnt.z - tran.r_pnt.z, 4)])

        return list_pnts, list_attrs

    def _terr(self):
        """Return
        """
        list_lines = []
        list_attrs = []
        for i, col in enumerate(self.mat_trans):
            for j, tran in enumerate(col):
                line = []
                for r_pnt in tran.terr_pnts:
                    diff = self.cols_width_left[i + 1] - tran.max_left_width()
                    line.append(Point(r_pnt.npk + self.centers[i][j].x + diff,
                                      (r_pnt.terr - tran.min_height()) *
                                      self.scale + self.centers[i][j].y))
                list_lines.append(Line(line))
                list_attrs.append([tran.r_pnt.npk, 'Terr', tran.length(), '',
                                   '166:75:45'])
        return list_lines, list_attrs

    def get_ras_terr(self):
        """Return
        """
        ras, ras_attrs = self._ras()
        ras_terr, ras_terr_attrs = self._terr()
        ras.extend(ras_terr)
        ras_attrs.extend(ras_terr_attrs)

        return ras, ras_attrs

if __name__ == '__main__':
    import doctest
    doctest.testmod()
