# -*- coding: utf-8 -*-
"""
Created on Sat Aug  2 16:52:30 2014

@author: meskal
"""

#
# import pygrass modules
#
import math

# import grass.script as grass
import re
from grass.pygrass.vector import VectorTopo
import road_base as Base
from road_plant import Aligns

# from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line

# from grass.pygrass.vector.geometry import Boundary
# from grass.pygrass.vector.geometry import Area
import road_plant as Plant


def write_objs(allrectas, radio):
    """R"""
    new2 = VectorTopo("AACC__" + str(int(radio)))
    # cols = [(u'cat',       'INTEGER PRIMARY KEY'),
    #        (u'elev',      'INTEGER')]

    new2.open("w")
    for obj in allrectas:
        new2.write(obj)
    # new2.table.conn.commit()
    new2.close()


# =============================================
# Parallel
# =============================================


class Parallel(Base.RoadObj, object):
    """Return"""

    def __init__(self, pk1, pk2, dist1, dist2, g90, plant=None):
        """Return"""
        self.pk1 = pk1
        self.dist1 = dist1
        self.pk2 = pk2
        self.dist2 = dist2
        self.plant = plant

        self.g90 = g90

        self.line = None

        super(Parallel, self).__init__(self.length())

    def __str__(self):
        return (
            "PARALLEL("
            + str(self.pk1)
            + ", "
            + str(self.pk2)
            + ", "
            + str(self.dist1)
            + ", "
            + str(self.dist2)
            + ", "
            + str(self.g90)
            + ")"
        )

    def __repr__(self):

        return (
            "Parallel("
            + str(self.pk1)
            + ", "
            + str(self.pk2)
            + ", "
            + str(self.dist1)
            + ", "
            + str(self.dist2)
            + ", "
            + str(self.g90)
            + ")"
        )

    def length(self):
        """Return"""
        if self.line:
            return self.line.length()
        else:
            return -1

    def param(self):
        """Return"""
        return "L=" + str(round(self.length(), 3))

    def get_roadpoint(self, start, r_pnt=None):
        """Return"""
        distx = self.dist1 + ((start - self.pk1) * (self.dist2 - self.dist1)) / (
            self.pk2 - self.pk1
        )
        if not r_pnt:
            r_pnt = self.plant.get_roadpoint(start)
        if r_pnt.azi == 0:
            r_pnt.azi = math.pi / 2
        r_pnt_d = r_pnt.parallel(distx, self.g90)

        r_pnt_d.dist_displ = distx
        return [r_pnt_d]

    def get_roadpnts(self, start, end, interv):
        """Return"""
        if start == 0:
            start = int(self.pk1)
        if end == -1:
            end = int(self.pk2)
        list_pts = []
        for pki in range(start, end, interv):
            list_pts.append(self.get_roadpoint(pki)[0])
        self.line = Line(list_pts)
        return list_pts

    def find_cutoff(self, r_pnt):
        """Return"""
        return self.get_roadpoint(r_pnt.npk, r_pnt)[0]


# =============================================
# Parallel
# =============================================


class DisplLine(Aligns, object):
    """Return"""

    contador = 0
    contador_left = 0
    contador_right = 0

    def __init__(self, lists, left=True, polygon=None, plant=None):
        """Return"""
        DisplLine.contador += 1
        if left:
            DisplLine.contador_left += 1
        else:
            DisplLine.contador_right += 1

        self.pks = lists[0]
        self.dist = lists[1]
        self.elev = lists[2]
        self.typeline = lists[3]

        self.left = left
        self.polygon = polygon
        self.plant = plant

        self.list_lim = []
        self.elev_lim = []

        self.g90 = -math.pi / 2
        self.num = DisplLine.contador_left
        if not left:
            self.g90 = math.pi / 2
            self.num = DisplLine.contador_right

        self._fix_line()
        d_alings = self._init_aligns()

        super(DisplLine, self).__init__(d_alings)

    def __str__(self):
        """Return"""
        return str(self.dist)

    #    @staticmethod
    #    def total():
    #        """ Return
    #        """
    #        return DisplLine.contador

    def _intbool(self):
        """Return"""
        if self.left is True:
            return -1
        else:
            return 1

    def _fix_line(self):
        """Return"""
        dist = []
        pks = []
        elev = []
        typeline = []
        for j in range(len(self.dist)):
            if self.dist[j] == -1:
                continue
            if j != len(self.dist) - 1:
                if self.dist[j] == 0 and self.dist[j + 1] == 0:
                    continue
            dist.append(self.dist[j])
            pks.append(self.pks[j])
            elev.append(self.elev[j])
            typeline.append(self.typeline[j])
        self.dist = dist
        self.pks = pks
        self.elev = elev
        self.typeline = typeline

    def _polyg_parall(self, dist):
        """Return"""
        #        line = self.polygon.read(1)
        self.polygon.open("r")
        line = self.polygon.cat(1, "lines", 1)[0]
        self.polygon.close()

        pnts = []
        for i in range(len(line) - 1):

            straight = Base.Straight(line[i], line[i + 1])
            pnts.append(straight.parallel(dist, self._intbool()))

        parallel = Line([pnts[0].pstart])
        for i in range(len(pnts) - 1):
            parallel.append(pnts[i].cutoff(pnts[i + 1]))
        parallel.append(pnts[-1].pend)
        return parallel

    def _table_parall(self, dist):
        """Return"""
        layer = 2
        self.polygon.open("r")
        tabla_plant = self.polygon.dblinks.by_layer(layer).table()
        tabla_plant_sql = "SELECT * FROM {name};".format(name=tabla_plant.name)
        tabla_plant_iter = tabla_plant.execute(tabla_plant_sql)
        self.polygon.close()
        if self.left:
            contador = DisplLine.contador_left
        else:
            contador = DisplLine.contador_right

        tabla = []
        for dat in tabla_plant_iter:

            cat, pk, radio, ain, aout, sobre, superelev, dc, lr = dat

            if radio == 0:
                tabla.append(
                    {
                        "a_out": 0,
                        "dc_": 0,
                        "cat2": cat,
                        "radio": 0,
                        "pk_eje": 0,
                        "superelev": superelev,
                        "a_in": 0,
                        "lr_": 0,
                        "widening": sobre,
                    }
                )
                continue

            local_in = Base.cloth_local(abs(radio), ain)
            local_out = Base.cloth_local(abs(radio), aout)

            if self.left and radio < 0:
                radio = radio + dist - (contador * sobre)
            elif self.left and radio > 0:
                radio = radio + dist + (contador * sobre)
            elif not self.left and radio > 0:
                radio = radio - dist - (contador * sobre)
            elif not self.left and radio < 0:
                radio = radio - dist + (contador * sobre)

            if ain != 0:
                ain = Base.clotoide_get_a(
                    radio, local_in["y_o"], contador * sobre, self.left
                )
            if aout != 0:
                aout = Base.clotoide_get_a(
                    radio, local_out["y_o"], contador * sobre, self.left
                )

            #            tabla.append((0, 0, radio, ain, aout, sobre, ''))
            tabla.append(
                {
                    "a_out": aout,
                    "dc_": 0,
                    "cat2": cat,
                    "radio": radio,
                    "pk_eje": 0,
                    "superelev": superelev,
                    "a_in": ain,
                    "lr_": 0,
                    "widening": sobre,
                }
            )
        return tabla

    def _get_limits_plant(self, plant_d):
        """Return"""
        list_pnts = []
        pnts_charc = plant_d.get_charact()

        for i, pnt in enumerate(pnts_charc[:-1]):
            pnt2 = self.plant.list_aligns[i].find_cutoff(pnt)
            if pnt2:
                pnt2.npk += self.plant.leng_accum[i]

            if not pnt2:
                pnt2 = self.plant.list_aligns[i + 1].find_cutoff(pnt)
                if pnt2:
                    pnt2.npk += self.plant.leng_accum[i + 1]

            if not pnt2:
                pnt2 = self.plant.list_aligns[i - 1].find_cutoff(pnt)
                if pnt2:
                    pnt2.npk += self.plant.leng_accum[i - 1]
            list_pnts.append(pnt2)
        pnt2 = self.plant.list_aligns[-1].get_roadpoint(-1)[0]
        pnt2.npk = self.plant.leng_accum[-1]
        list_pnts.append(pnt2)

        return list_pnts

    def _mode_exact(self, index):
        """Return"""
        polyg = self._polyg_parall(self.dist[index])
        table = self._table_parall(self.dist[index])

        plantalignd = Plant.Plant(polyg, table)
        d_alings = []
        pnts_limits = self._get_limits_plant(plantalignd)

        for j, r_pnt in enumerate(pnts_limits):
            if self.pks[index] <= r_pnt.npk <= self.pks[index + 1]:
                self.list_lim.append(r_pnt.npk)
                self.elev_lim.append(self.elev[index])
                d_alings.append(plantalignd[j])

        return d_alings

    def _distx(self, rad, pc_d, pstart):
        """Return"""
        recta_pnt = pstart.normal(math.pi / 2)
        recta_c = Base.Straight(pc_d, None, pstart.azi, 10)
        pto_corte = recta_pnt.cutoff(recta_c)
        distxx = pc_d.distance(pto_corte)
        seno = math.sqrt(rad**2 - distxx**2)
        distx = pstart.distance(pto_corte) - seno
        return distx

    def _mode_curve(self, index):
        """Return"""
        rad, center = self.typeline[index].split(",")

        rad = float(rad[1:])
        center = float(center)

        pcenter = self.plant.get_roadpoint(self.pks[index] + center)
        pc_d = pcenter.parallel(self.dist[index] + rad, self.g90)

        pstart = self.plant.get_roadpoint(self.pks[index])
        distx = self._distx(rad, pc_d, pstart)

        p1_d = pstart.parallel(distx, self.g90)

        pend = self.plant.get_roadpoint(self.pks[index + 1])

        distx = self._distx(rad, pc_d, pend)
        p2_d = pend.parallel(distx, self.g90)

        az1 = pc_d.azimuth(p1_d)
        az2 = pc_d.azimuth(p2_d)

        alpha = abs(az2 - az1)
        if alpha > math.pi:
            alpha = 2 * math.pi - alpha

        curve = Base.Curve(self._intbool() * rad, alpha, az1, pc_d)

        return curve

    def _init_aligns(self):
        """Return"""
        d_alings = []
        for i in range(len(self.dist) - 1):

            if self.dist[i] == 0 or self.dist[i + 1] == 0:
                self.list_lim.append(self.pks[i])
                self.elev_lim.append(self.elev[i])
                d_alings.append(None)
                continue

            if self.typeline[i] == "e":
                self.list_lim.append(self.pks[i])
                self.elev_lim.append(self.elev[i])
                d_alings.extend(self._mode_exact(i))

            elif self.typeline[i] == "l":
                self.list_lim.append(self.pks[i])
                self.elev_lim.append(self.elev[i])

                paral = Parallel(
                    self.pks[i],
                    self.pks[i + 1],
                    self.dist[i],
                    self.dist[i + 1],
                    self.g90,
                    self.plant,
                )
                d_alings.append(paral)

            elif self.typeline[i] == "s":
                raise ValueError("s")
            #                pstart = plant.get_roadpoint(self.pks[i])
            #                p1_x = pstart.x + self.dist[i]*math.sin(pstart.azi+self.g90)
            #                p1_y = pstart.y + self.dist[i]*math.cos(pstart.azi+self.g90)
            #
            #                pend = plant.get_roadpoint(self.pks[i+1])
            #                p2_x = pend.x + self.dist[i]*math.sin(pend.azi+self.g90)
            #                p2_y = pend.y + self.dist[i]*math.cos(pend.azi+self.g90)
            #
            #                recta = Base.Straight(Point(p1_x, p1_y), Point(p2_x, p2_y))

            elif re.search(r"^r", self.typeline[i]):
                self.list_lim.append(self.pks[i])
                self.elev_lim.append(self.elev[i])
                d_alings.append(self._mode_curve(i))

            else:
                raise ValueError("Type not suported:" + self.typeline[i])

        if self.pks[-1] not in self.list_lim:
            self.list_lim.append(self.pks[-1])
            self.elev_lim.append(self.elev[-1])

        return d_alings

    def get_left(self):
        """Return"""
        if self.left:
            return "left"
        else:
            return "right"

    def _find_superelev(self, r_pnt, elev, dist_displ):
        """Return"""
        for line in self.plant.superelev_lim:

            if line == []:
                continue

            dist1, dist2, bom1, peralte, bom2, radio = line
            pks_1 = dist1 + dist2

            if pks_1[0] < r_pnt.npk < pks_1[-1]:
                break

        #        pend_1 = [-bom1, 0, bom1, peralte, peralte, bom2, 0, -bom2]
        #        pend_2 = [-bom1, -bom1, -bom1, -peralte, -peralte, -bom2, -bom2, -bom2]

        #        elev2 = elev / dist_displ
        bom1 = bom1 * dist_displ * 0.01
        bom2 = bom2 * dist_displ * 0.01
        peralte = peralte * dist_displ * 0.01
        pend_11 = [
            elev,
            elev + bom1,
            elev + bom1 + bom1,
            elev + bom1 + peralte,
            elev + bom1 + peralte,
            elev + bom2 + bom2,
            elev + bom2,
            elev,
        ]
        pend_22 = [elev, elev, elev, elev - peralte, elev - peralte, elev, elev, elev]

        pkini, pkfin = 0, 1
        #        z_1 = - bombeo * dist_displ * 0.01
        #        z_2 = - bombeo * dist_displ * 0.01
        z_1 = elev
        z_2 = elev

        if (self.left and radio > 0) or (not self.left and radio < 0):

            for i in range(len(pks_1) - 1):

                if pks_1[i] < r_pnt.npk < pks_1[i + 1]:
                    pkini, pkfin = pks_1[i], pks_1[i + 1]
                    z_1 = pend_11[i]
                    z_2 = pend_11[i + 1]
                    break

        elif (not self.left and radio > 0) or (self.left and radio < 0):

            for i in range(0, len(pks_1) - 1, 1):

                if pks_1[i] < r_pnt.npk < pks_1[i + 1]:
                    pkini, pkfin = pks_1[i], pks_1[i + 1]
                    z_1 = pend_22[i]
                    z_2 = pend_22[i + 1]
                    break

        z_x = z_1 + ((r_pnt.npk - pkini) * ((z_2 - z_1) / (pkfin - pkini)))

        return z_x

    def get_elev(self, index, r_pnt, dist_displ):
        """Return"""
        #        calzadas = 1
        #        if self.plant.bombeo:
        #            elev = self._find_superelev(index, r_pnt, self.plant.bombeo,
        #                                        dist_displ)
        #
        #        else:
        elev = self.elev_lim[index] + (
            (r_pnt.npk - self.list_lim[index])
            * (self.elev_lim[index + 1] - self.elev_lim[index])
        ) / (self.list_lim[index + 1] - self.list_lim[index])

        if self.plant.bombeo:
            elev = self._find_superelev(r_pnt, elev, dist_displ)

        return elev

    def find_cutoff(self, r_pnt):
        """Return"""

        for i in range(len(self.list_lim) - 1):
            if isinstance(self.list_aligns[i], Base.Curve):
                cuv_lim = r_pnt.npk <= self.list_lim[i + 1]
            else:
                cuv_lim = r_pnt.npk < self.list_lim[i + 1]

            if self.list_lim[i] <= r_pnt.npk and cuv_lim:

                if self.list_aligns[i] is not None:
                    r_pnt_d = self.list_aligns[i].find_cutoff(r_pnt)

                    if r_pnt_d is not None:
                        r_pnt_d.dist_displ = round(r_pnt_d.distance2(r_pnt.point2d), 4)
                        elev = self.get_elev(i, r_pnt, r_pnt_d.dist_displ)
                        r_pnt_d.z = elev + r_pnt.z
                        if r_pnt_d.dist_displ == 0:
                            r_pnt_d.incli = 0
                        else:
                            r_pnt_d.incli = math.atan(elev / r_pnt_d.dist_displ)

                        r_pnt_d.acum_pk = self.list_lim[i] + r_pnt_d.npk

                    return r_pnt_d

    def get_pnts_displ(self, list_r_pnts, line=False):
        """Return a displaced line of a given axis"""
        list_pnts_d = []

        for r_pnt in list_r_pnts:
            list_pnts_d.append(self.find_cutoff(r_pnt))

        if line:
            return Line(list_pnts_d)
        else:
            return list_pnts_d

    def set_roadline(self, roadline):
        """Return"""
        puntos = self.get_pnts_displ(roadline, line=False)

        # Name lenght type param rgb
        attrs = [
            "Displ_" + str(self.num),
            self.length(),
            self.get_left(),
            self.num,
            "0:128:128",
        ]
        self.roadline = Base.RoadLine(puntos, attrs, "Displ_" + str(self.num))


# =============================================
# Parallel
# =============================================


class Displaced(object):
    """Return"""

    def __init__(self, polygon, tabla_iter, plant):
        """Return"""
        self.polygon = polygon
        self.tabla_iter = tabla_iter
        self.plant = plant

        self.displines = []
        self.displines_left = []
        self.displines_right = []
        self.pks = []

        self._init_displ()

    def __getitem__(self, index):
        return self.displines[index]

    def __setitem__(self, index, value):
        self.displines[index] = value

    def __delitem__(self, index):
        del self.displines[index]

    def __len__(self):
        return len(self.displines)

    def __str__(self):
        """Return"""
        return "LINESTRING(%s)"

    def _init_displ(self):
        """Return"""
        d_left = []
        type_left = []
        d_right = []
        type_right = []

        for i, dat in enumerate(self.tabla_iter):

            self.pks.append(dat["pk"])
            if ";" in dat["sec_left"]:
                d_left.append(dat["sec_left"].split(";"))
            else:
                d_left.append(dat["sec_left"])

            if ";" in dat["sec_right"]:
                d_right.append(dat["sec_right"].split(";"))
            else:
                d_right.append(dat["sec_right"])

            if dat["type_left"] != "":
                type_left.append(dat["type_left"].split(";"))
            else:
                type_left.append(["l"] * len(d_left[i]))

            if dat["type_right"] != "":
                type_right.append(dat["type_right"].split(";"))
            else:
                type_right.append(["l"] * len(d_right[i]))

        self._generate(d_left, type_left, left=True)
        self._generate(d_right, type_right, left=False)

    def _generate(self, disp, types, left):
        """Return"""
        rango1 = range(len(types[0]))

        disp = [
            [[float(p) for p in row[i].split()] for row in disp]
            for i in range(len(disp[0]))
        ]
        types = [[row[i] for row in types] for i in rango1]

        if left:
            disp = disp[::-1]
            types = types[::-1]

        for i, lin in enumerate(disp):
            types2 = types[:]
            lin2 = [[row[j] for row in lin] for j in range(len(lin[0]))]

            displine = DisplLine(
                [self.pks[:], lin2[0], lin2[1], types2[i][:]],
                left,
                self.polygon,
                self.plant,
            )

            self.displines.append(displine)
            if left:
                self.displines_left.append(displine)
            else:
                self.displines_right.append(displine)

    def find_cutoff(self, r_pnt):
        """Return all displaced points of a given axis point"""
        list_pnts_d_left = []
        list_pnts_d_right = []
        for d_line in self.displines:
            pnt = d_line.find_cutoff(r_pnt)
            if d_line.left:
                #                if pnt is not None:
                list_pnts_d_left.append(pnt)
            else:
                #                if pnt is not None:
                list_pnts_d_right.append(pnt)
        return [list_pnts_d_left, list_pnts_d_right]

    def get_pnts_trans(self, list_r_pnts):
        """Return"""
        list_pnts_d = []
        for r_pnt in list_r_pnts:
            list_pnts_d.append(self.find_cutoff(r_pnt))
        return list_pnts_d

    def get_lines(self):
        """Return"""
        list_attrs = []
        list_lines = []
        for i, displ in enumerate(self.displines):

            objs, values = displ.roadline.get_line_attrs(1)
            list_lines.extend(objs)
            list_attrs.extend(values)
        return list_lines, list_attrs

    def get_charact(self):
        """Return"""
        list_lines = []
        list_attrs = []
        for i, displ in enumerate(self.displines):
            obj, attr = displ.get_charact_pnts()
            list_lines.extend(obj)
            for att in attr:
                att.append("Displ=" + str(i + 1))
            list_attrs.extend(attr)
        return list_lines, list_attrs

    def set_roadlines(self, roadline):
        """Return"""
        for displ in self.displines:
            displ.set_roadline(roadline)

    def get_areas(self, opts):
        """Return"""
        opts = [opt.split("-") for opt in opts.split(",") if "," in opts]

        list_lines = []
        list_attrs = []
        for j, opt in enumerate(opts):

            lines = self[int(opt[0]) - 1].roadline.get_area(
                self[int(opt[1]) - 1].roadline
            )
            list_attrs.extend([str(j + 1) for _ in range(len(lines))])
            list_lines.extend(lines)

        return list_lines, list_attrs


if __name__ == "__main__":
    import doctest

    doctest.testmod()
