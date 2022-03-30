#!/usr/bin/env python

"""
Sample Python script to access vector data using GRASS Ctypes
interface
"""

import sys
import os

import math
import grass.script as grass
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point

# from grass.pygrass.vector.geometry import Line

sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), "", "v.road"))
import road_base as Base


def write_objs(allrectas, radio):
    """Return"""
    new2 = VectorTopo("bbbbb" + str(int(radio)))
    # cols = [(u'cat',       'INTEGER PRIMARY KEY'),
    #        (u'elev',      'INTEGER')]

    new2.open("w")
    for obj in allrectas:
        new2.write(obj)
    # new2.table.conn.commit()
    new2.close()


#########################################################


def generate_ptsround(radio, radio2, azimut, center):
    """Return"""
    x_o, y_o = center.split(",")
    radio = float(radio)
    radio2 = float(radio2)
    azi = float(azimut)

    x_1 = float(x_o) + radio2 * math.sin(azi)
    y_1 = float(y_o) + radio2 * math.cos(azi)

    x_2 = x_1 + radio * math.sin(azi + math.pi / 2)
    y_2 = y_1 + radio * math.cos(azi + math.pi / 2)

    x_3 = x_2 + 2 * radio2 * math.sin(azi + math.pi)
    y_3 = y_2 + 2 * radio2 * math.cos(azi + math.pi)

    x_4 = x_3 + 2 * radio * math.sin(azi + 3 * math.pi / 2)
    y_4 = y_3 + 2 * radio * math.cos(azi + 3 * math.pi / 2)

    x_5 = x_4 + 2 * radio2 * math.sin(azi)
    y_5 = y_4 + 2 * radio2 * math.cos(azi)

    x_6 = x_5 + (radio) * math.sin(azi + math.pi / 2)
    y_6 = y_5 + (radio) * math.cos(azi + math.pi / 2)

    return [
        [x_1, y_1, 0],
        [x_2, y_2, 0],
        [x_3, y_3, 0],
        [x_4, y_4, 0],
        [x_5, y_5, 0],
        [x_6, y_6, 0],
    ]


class InterAlign(object):
    """Return"""

    def __init__(self, name_map, cat):
        """Return"""
        self.cat = cat
        self.name = name_map
        self.izq = ""

        topo = VectorTopo(name_map)
        topo.open("r", layer=1)
        line1 = topo.read(cat)

        self.type = line1.attrs["type"]
        self.pk_ini = float("".join(line1.attrs["pk"].split("+")))
        self.pto_ini = Base.RoadPoint(line1[0])
        self.pto_fin = line1[-1]
        self.param = float(line1.attrs["param"].split("=")[1])
        self.center = None
        self.recta = None

        self.out = {"pks_in": [], "pks_out": [], "radios": [], "dif": []}

        topo.close()

        topo.open("r", layer=2)
        self.azimut_ini = topo.read(cat).attrs["azimut"]
        topo.close()

        if self.type == "Curve":
            self.init_curve(topo)

        elif self.type == "Straight":
            self.init_straight()
        else:
            grass.message(" not yet implemented")

    def init_curve(self, topo):
        """Return"""
        topo.open("r", layer=3)
        for center in range(1, topo.number_of("points") + 1):
            if isinstance(topo.read(center), Point):
                cat_curve = topo.read(center).attrs["param"][1:]
                if self.cat == int(cat_curve):
                    self.center = Base.RoadPoint(topo.read(center))
                    self.azimut_ini = self.center.azimuth(self.pto_ini)

        topo.close()

    def init_straight(self):
        """Return"""
        self.azimut_ini = self.pto_ini.azimuth(self.pto_fin)
        self.recta = Base.Straight(self.pto_ini, None, self.azimut_ini, 10)


class Intersections(object):
    """Return"""

    def __init__(
        self, name_map1, cat1, izq1, name_map2, cat2, izq2, inout=None, rounda=None
    ):
        """Return"""
        self.plant1 = InterAlign(name_map1, cat1)
        self.plant2 = InterAlign(name_map2, cat2)

        self.set_izq1(izq1)
        self.set_izq2(izq2)

        self.dist1 = []
        self.dist2 = []
        self.radios = []

        self.rounda = rounda

        if inout == "In":  # options 'In' or 'Out'
            self.inout = -1
        else:
            self.inout = 1

    def _get_dif(self, d_1, d_2, radio):
        """Return"""
        if d_1 > d_2:
            dtmp = d_1
            d_1 = d_2
            d_2 = dtmp
            dif = round(d_2 - d_1, 6)
        else:
            dif = 0
        return [round(d_1, 6), round(d_2, 6), radio, dif]

    def _get_radio_leng(self, plant, radio, dist):
        """Return"""
        if plant.param < 0:
            if plant.izq == "Izq":
                r_b = abs(plant.param) - radio - dist
            else:
                r_b = abs(plant.param) + radio + dist
        else:
            if plant.izq == "Izq":
                r_b = abs(plant.param) + radio + dist
            else:
                r_b = abs(plant.param) - radio - dist
        return r_b

    def _get_azi_inout(self, plant, azi_c1c2, ang_a):
        """Return"""
        if plant.param < 0:
            azi = azi_c1c2 - ang_a * self.inout
        else:
            azi = azi_c1c2 + ang_a * self.inout
        return azi

    def _get_alpha(self, azi_1, azi_2):
        """Return"""
        if azi_1 < 0:
            azi_1 = self._azi_neg(abs(azi_1))
        if azi_2 < 0:
            azi_2 = self._azi_neg(abs(azi_2))
        alpha = abs(azi_1 - azi_2)
        if alpha > math.pi:
            alpha = 2 * math.pi - alpha
        return alpha

    def _check_azimuth(self, azi):
        """Return"""
        if azi > math.pi:
            return azi - 2 * math.pi
        elif azi < 0:
            return azi + 2 * math.pi
        return azi

    def _azi_neg(self, azi):
        """Return"""
        if azi <= math.pi:
            return azi + math.pi
        else:
            return azi - math.pi

    def _get_azi_inout2(self, azi):
        """Return"""
        if self.inout == -1:
            return self._azi_neg(azi)
        else:
            return azi

    def set_izq1(self, izq):
        """Return"""
        if izq == "Izq":
            self.izq1 = -1
        else:
            self.izq1 = 1
        self.plant1.izq = izq

    def set_izq2(self, izq):
        """Return"""
        if izq == "Izq":
            self.izq2 = -1
        else:
            self.izq2 = 1
        self.plant2.izq = izq

    def get_intersect(self, ind):
        """Return"""
        dist1 = [p for p in self.dist1 if p != -1]
        dist2 = [p for p in self.dist2 if p != -1]
        if self.plant1.type == "Straight" and self.plant2.type == "Curve":

            grass.message("straight_curve")
            return self.straight_curve(self.radios[ind], dist1[ind], dist2[ind])

        elif self.plant1.type == "Straight" and self.plant2.type == "Straight":

            grass.message("straight_straight")
            return self.straight_straight(self.radios[ind], dist1[ind], dist2[ind])

        elif self.plant1.type == "Curve" and self.plant2.type == "Curve":

            grass.message("curve_curve")
            return self.curve_curve(self.radios[ind], dist1[ind], dist2[ind])

    def straight_straight(self, radio, dist1, dist2):
        """Return"""
        # Buscamos el centro del circulo
        recta11 = self.plant1.recta.parallel(dist1 + radio, self.izq1)
        recta22 = self.plant2.recta.parallel(dist2 + radio, self.izq2)
        pto_c = recta11.cutoff(recta22)

        recta_r1 = self.plant1.recta.parallel(dist1, self.izq1)
        recta_r2 = self.plant2.recta.parallel(dist2, self.izq2)
        pto_v = recta_r1.cutoff(recta_r2)

        # Punto de corte de la recta centro-vertice con el circulo
        pto_p = pto_c.project(radio, pto_c.azimuth(pto_v))

        # Rectas perpendiculares de xc,yc y xp,yp al eje 1
        azi_1 = recta11.azimuth() - self.izq1 * math.pi / 2
        pto_t1 = pto_c.project(dist1 + radio, azi_1)
        recta_p1 = Base.Straight(pto_p, None, azi_1, 10)
        pto_p1 = self.plant1.recta.cutoff(recta_p1)

        # Rectas perpendiculares de xc,yc y xp,yp al eje 2
        azi_2 = recta22.azimuth() - self.izq2 * math.pi / 2
        pto_t2 = pto_c.project(dist2 + radio, azi_2)
        recta_p2 = Base.Straight(pto_p, None, azi_2, 10)
        pto_p2 = self.plant2.recta.cutoff(recta_p2)

        d_1 = self.plant1.pto_ini.distance(pto_t1) + self.plant1.pk_ini
        d_2 = self.plant1.pto_ini.distance(pto_p1) + self.plant1.pk_ini
        d_3 = self.plant2.pto_ini.distance(pto_t2) + self.plant2.pk_ini
        d_4 = self.plant2.pto_ini.distance(pto_p2) + self.plant2.pk_ini

        return [self._get_dif(d_1, d_2, radio), self._get_dif(d_3, d_4, radio)]

    def curve_curve(self, radio, dist1, dist2):
        """Return"""
        azi_c1c2 = self.plant1.center.azimuth(self.plant2.center)

        r_b = self._get_radio_leng(self.plant1, radio, dist1)
        r_a = self._get_radio_leng(self.plant2, radio, dist2)
        r_c = self.plant1.center.distance(self.plant2.center)

        ang_a = math.acos((r_b**2 + r_c**2 - r_a**2) / (2 * r_b * r_c))
        # ang_b = math.acos((r_a ** 2 + r_c ** 2 - r_b ** 2) / (2 * r_a * r_c))
        # ang_c = math.pi - ang_a - ang_b

        azi_c1c = self._get_azi_inout(self.plant1, azi_c1c2, ang_a)

        pto_c = self.plant1.center.project(r_b, azi_c1c)

        alpha = self._get_alpha(azi_c1c, self.plant1.azimut_ini)
        pk_1 = self.plant1.pk_ini + alpha * abs(self.plant1.param)

        azi_c2c = self.plant2.center.azimuth(pto_c)
        alpha = self._get_alpha(azi_c2c, self.plant2.azimut_ini)
        pk_2 = self.plant2.pk_ini + alpha * abs(self.plant2.param)

        # roundabout
        if self.rounda:
            pto_p = pto_c.project(radio, azi_c2c, self.izq2)
        else:
            if self.plant1.param * self.plant2.param > 0:
                beta = self._get_alpha(-self.izq1 * azi_c1c, -self.izq2 * azi_c2c) / 2
            else:
                beta = -self._get_alpha(-self.izq1 * azi_c1c, self.izq2 * azi_c2c) / 2
            if self.plant1.izq == "Izq":
                pto_p = pto_c.project(
                    radio, azi_c1c - self.izq2 * self.izq1 * self.inout * beta
                )
            else:
                pto_p = pto_c.project(
                    radio,
                    self._azi_neg(azi_c1c) - self.izq2 * self.izq1 * self.inout * beta,
                )

        azi_c1p = self.plant1.center.azimuth(pto_p)
        azi_c2p = self.plant2.center.azimuth(pto_p)

        alpha = self._get_alpha(azi_c1p, self.plant1.azimut_ini)
        pk_11 = self.plant1.pk_ini + alpha * abs(self.plant1.param)

        alpha = self._get_alpha(azi_c2p, self.plant2.azimut_ini)
        pk_22 = self.plant2.pk_ini + alpha * abs(self.plant2.param)

        #
        recta_c2c = Base.Straight(self.plant2.center, pto_c)
        recta_c1c = Base.Straight(self.plant1.center, pto_c)

        write_objs([pto_c, pto_p, recta_c1c.get_line(), recta_c2c.get_line()], radio)

        return [self._get_dif(pk_1, pk_11, radio), self._get_dif(pk_2, pk_22, radio)]

    def straight_curve(self, radio, dist1, dist2):
        """Return"""
        azi_ini = self._get_azi_inout2(self.plant1.azimut_ini)
        # Giro a la der
        azi_1 = self._check_azimuth(self.plant1.azimut_ini + math.pi / 2)

        recta1 = Base.Straight(self.plant2.center, None, azi_1, 10)
        pto_c2 = self.plant1.recta.cutoff(recta1)
        d_2 = self.plant2.center.distance(pto_c2)
        azi_center = pto_c2.azimuth(self.plant2.center)

        if azi_1 == azi_center:
            l_s = abs(radio + dist1 + d_2 * self.izq1)
        else:
            l_s = abs(radio + dist1 - d_2 * self.izq1)

        hip = self._get_radio_leng(self.plant2, radio, dist2)
        alpha = math.asin(l_s / hip)

        l_t1 = hip * math.cos(alpha)
        pto_t1 = pto_c2.project(l_t1, azi_ini)

        pto_c = self.plant2.center.project(hip, azi_ini - self.inout * alpha)
        azi_c1c = self.plant2.center.azimuth(pto_c)

        if self.rounda:
            pto_p = pto_c.project(radio, azi_c1c, -self.izq2)
        else:
            if self.plant2.param < 0:
                beta = (
                    -1
                    * self.izq1
                    * self.izq2
                    * self._get_alpha(azi_c1c, pto_t1.azimuth(pto_c))
                )
            else:
                beta = (
                    self.izq1
                    * self.izq2
                    * self._get_alpha(azi_c1c, pto_c.azimuth(pto_t1))
                )

            pto_p = pto_c.project(radio, pto_c.azimuth(pto_t1) + beta / 2)

        recta_p = Base.Straight(
            pto_p, None, azi_ini - self.inout * self.izq1 * math.pi / 2, 10
        )
        pto_t2 = self.plant1.recta.cutoff(recta_p)

        d_1 = self.plant1.pto_ini.distance(pto_t1) + self.plant1.pk_ini
        d_2 = self.plant1.pto_ini.distance(pto_t2) + self.plant1.pk_ini

        azi_c1p = self.plant2.center.azimuth(pto_p)

        alpha = self._get_alpha(azi_c1c, self.plant2.azimut_ini)
        pk1 = self.plant2.pk_ini + alpha * abs(self.plant2.param)

        alpha = self._get_alpha(azi_c1p, self.plant2.azimut_ini)
        pk2 = self.plant2.pk_ini + alpha * abs(self.plant2.param)

        write_objs([pto_c2, self.plant2.center, pto_c, pto_t1, pto_p, pto_t2], radio)

        return [self._get_dif(d_1, d_2, radio), self._get_dif(pk1, pk2, radio)]

    def get_pklist(self):
        """Return"""
        dist1 = [p for p in self.dist1 if p != -1]
        dist2 = [p for p in self.dist2 if p != -1]

        if len(dist1) <= len(dist2):
            side = len(dist1)
        else:
            side = len(dist2)

        pklist = [[], []]
        pklist2 = [[], []]
        pklist_ini = [[], []]
        pklist_ini2 = [[], []]
        for i in range(side):

            intersec = self.get_intersect(i)

            for j, inter in enumerate(intersec):
                dista = dist1[i]
                if j == 1:
                    dista = dist2[i]
                if inter[0] not in pklist:
                    pklist[j].append(inter[0])
                    pklist_ini[j].append([inter[0], [inter[2]], [inter[3]], [dista], i])
                else:
                    ind = pklist[j].index(inter[0])
                    pklist_ini[j][ind][1].append(inter[2])
                    pklist_ini[j][ind][2].append(inter[3])
                    pklist_ini[j][ind][3].append(dista)

                if inter[1] not in pklist2:
                    pklist2[j].append(inter[1])
                    pklist_ini2[j].append([inter[1], [dista], i])
                else:
                    ind = pklist2[j].index(inter[1])
                    pklist_ini2[j][ind][1].append(dista)

        return [pklist, pklist2, pklist_ini, pklist_ini2]

    def make_intersect(self, write=False):
        """Return"""
        pklist, pklist2, pklist_ini, pklist_ini2 = self.get_pklist()

        sal1 = self.get_tablesql_in(pklist_ini[0], self.plant1, self.dist1)
        sal2 = self.get_tablesql_out(pklist_ini2[0], self.plant1, self.dist1)

        all_pklist1 = pklist[0] + pklist2[0]
        all_sal0 = sal1 + sal2

        sal0 = (
            "v.road add=row name="
            + self.plant1.name.split("__")[0]
            + ' tab_type=Displ pklist="'
            + ",".join([str(p) for p in all_pklist1])
            + '"'
        )

        grass.message(sal0)
        grass.message(all_sal0)
        if write:
            os.system(sal0)
            os.system(all_sal0)

        if self.plant1.izq != self.plant2.izq:
            sal1 = self.get_tablesql_in(pklist_ini[1], self.plant2, self.dist2[::-1])
            sal2 = self.get_tablesql_out(pklist_ini2[1], self.plant2, self.dist2[::-1])
        else:
            sal1 = self.get_tablesql_in(pklist_ini[1], self.plant2, self.dist2)
            sal2 = self.get_tablesql_out(pklist_ini2[1], self.plant2, self.dist2)

        all_pklist2 = pklist[1] + pklist2[1]
        all_sal0 = sal1 + sal2

        sal0 = (
            "v.road add=row name="
            + self.plant2.name.split("__")[0]
            + ' tab_type=Displ pklist="'
            + ",".join([str(p) for p in all_pklist2])
            + '"'
        )

        grass.message(sal0)
        grass.message(all_sal0)
        if write:
            os.system(sal0)
            os.system(all_sal0)

    def get_tablesql_in(self, pklist_ini, plant, distances):
        """Return"""
        name = plant.name.split("__")[0]

        sal = 'echo " \n'
        for i, npk in enumerate([p[0] for p in pklist_ini]):

            sal += "UPDATE " + name + "_Displ SET "
            if plant.izq == "Izq":
                sal += "sec_left='"
            else:
                sal += "sec_right='"

            for dist in distances:

                for len_d in pklist_ini[i][3]:
                    if dist == len_d:
                        sal += str(len_d) + " 0;"
                    else:
                        sal += "-1 0;"
            sal = sal[:-1] + "'"

            if plant.izq == "Izq":
                sal += ", type_left='"
            else:
                sal += ", type_right='"

            for dist in distances:

                for j, len_d in enumerate(pklist_ini[i][3]):
                    if dist == len_d:
                        sal += (
                            "r"
                            + str(pklist_ini[i][1][j])
                            + ","
                            + str(pklist_ini[i][2][j])
                            + ";"
                        )
                    else:
                        sal += "l;"
            sal = sal[:-1] + "'"

            sal += " WHERE pk=" + str(npk) + ";\n"
        sal += '" | db.execute input=- \n'
        return sal

    def get_tablesql_out(self, pklist_ini2, plant, distances):
        """Return"""
        name = plant.name.split("__")[0]
        sal = 'echo " \n'
        for i, npk in enumerate([p[0] for p in pklist_ini2]):

            sal += "UPDATE " + name + "_Displ SET "
            if plant.izq == "Izq":
                sal += "sec_left='"
            else:
                sal += "sec_right='"

            for dist in distances:

                for len_d in pklist_ini2[i][1]:
                    if dist == len_d:
                        sal += str(len_d) + " 0;"
                    else:
                        sal += "-1 0;"
            sal = sal[:-1] + "'"

            if plant.izq == "Izq":
                sal += ", type_left='"
            else:
                sal += ", type_right='"

            for dist in distances:
                sal += "l;"
            sal = sal[:-1] + "'"

            sal += " WHERE pk=" + str(npk) + ";\n"
        sal += '" | db.execute input=- \n'
        return sal


# =============================================
# Main
# =============================================

if __name__ == "__main__":
    import doctest

    doctest.testmod()
#
