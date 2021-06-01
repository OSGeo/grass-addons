# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 18:37:36 2014

@author: meskal
"""

import math
import time
import road_base as Base

# import grass.script as grass
# from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line

# from grass.pygrass.vector.geometry import Attrs


def time_func(funcion_f):
    """Return"""

    def funcion_r(*arg):
        """Return"""
        t_1 = time.clock()
        res = funcion_f(*arg)
        t_2 = time.clock()
        print("%s tarda %0.5f ms" % (funcion_f.__name__, (t_2 - t_1) * 1000.0))
        return res

    return funcion_r


# =============================================
# ALIGNS
# =============================================


class Aligns(object):
    """Return"""

    def __init__(self, list_aligns=None):
        """Return"""
        self.list_aligns = list_aligns

        self.leng_accum = [0]

        self.length_accums()

        self.roadline = None

    def __getitem__(self, index):
        return self.list_aligns[index]

    def __setitem__(self, index, value):
        self.list_aligns[index] = value

    def __delitem__(self, index):
        del self.list_aligns[index]

    def __len__(self):
        return len(self.list_aligns)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        string = "["

        for i in self.list_aligns:
            string += str(i) + "\n"

        string += "]"
        return string

    def length_accums(self):
        """Return"""
        lon = 0
        for ali in self.list_aligns:
            if ali is not None:
                ali.leng_accum = lon
                lon += ali.length()
                self.leng_accum.append(lon)

    def length(self):
        """Return"""
        return self.leng_accum[-1]

    def get_roadpoint(self, npk):
        """Return"""
        if npk == -1:
            npk = self.length()
        for i in range(len(self.leng_accum) - 1):

            if self.leng_accum[i] <= npk <= self.leng_accum[i + 1]:

                pnt = self.list_aligns[i].get_roadpoint(npk - self.leng_accum[i])[0]
                pnt.npk = npk

                pnt.align = self.list_aligns[i].__class__.__name__ + "_" + str(i + 1)
                return pnt

    #    def get_line(self, list_r_pnts):
    #        """ Return
    #        """
    #        return Line([r_pnt for r_pnt in list_r_pnts
    #                     if r_pnt is not None])

    def get_roadpnts(self, start, end, interv, interv_c=None):
        """Return"""
        if not interv_c:
            interv_c = interv

        if end == -1:
            end = self.length()
        resto = interv
        accum = start
        list_pts = []
        ini = 0
        fin = len(self.leng_accum)
        for i in range(len(self.leng_accum) - 1):
            if self.leng_accum[i] <= start <= self.leng_accum[i + 1]:
                ini = i
            if self.leng_accum[i] <= end <= self.leng_accum[i + 1]:
                fin = i + 1

        rang_int = range(0, int(self.leng_accum[-1]), int(interv))
        rang_int_c = range(0, int(self.leng_accum[-1]), int(interv_c))

        # int_ant = interv
        rango_ant = []
        for i in range(ini, fin):

            rango = []
            if isinstance(self.list_aligns[i], Base.Straight):
                inter = interv
                for j in range(len(rang_int) - 1):
                    if self.leng_accum[i] <= rang_int[j] <= self.leng_accum[i + 1]:
                        rango.append(rang_int[j])
            else:
                inter = interv_c
                for j in range(len(rang_int_c) - 1):
                    if self.leng_accum[i] <= rang_int_c[j] <= self.leng_accum[i + 1]:
                        rango.append(rang_int_c[j])

            if inter > self.list_aligns[i].length() + resto:
                resto = resto + self.list_aligns[i].length()
                continue

            if rango == []:
                rango = [rango_ant[-1] + inter]
            accum = rango[0]
            start2 = rango[0] - self.leng_accum[i]

            if i == ini:
                start2 = start - self.leng_accum[i]

            end2 = -1
            if i == fin:
                end2 = end - self.leng_accum[i]

            self.list_aligns[i].pts_accum = accum

            pnts = self.list_aligns[i].get_roadpnts(start2, end2, inter)
            for pnt in pnts:
                pnt.align = self.list_aligns[i].__class__.__name__ + "_" + str(i + 1)
            list_pts.extend(pnts)

            resto = self.list_aligns[i].pts_rest
            accum = self.list_aligns[i].pts_accum
            # int_ant = inter
            rango_ant = rango

        r_pnt = self.list_aligns[-1].get_roadpoint(-1)[0]
        r_pnt.align = (
            self.list_aligns[-1].__class__.__name__ + "_" + str(len(self.list_aligns))
        )
        if list_pts[-1].npk != r_pnt.npk:
            r_pnt.npk = round(r_pnt.npk, 6)
            list_pts.append(r_pnt)

        return list_pts

    def get_segments_pnts(self, puntos, vert=None, line=False):
        """Return"""
        list_lines = []
        list_attrs = []
        for i, ali in enumerate(self.list_aligns):
            pnt_ini = ali.get_roadpoint(0)[0]
            pnt_ini.align = i + 1
            pnts_align = [pnt_ini]
            pnts_align.extend([r_pnt for r_pnt in puntos if ali.is_in(r_pnt)])
            pnt_end = ali.get_roadpoint(-1)[0]
            pnt_end.align = i + 1
            pnts_align.append(pnt_end)

            if vert is not None:
                vert.set_pnts_elev(pnts_align)
            if line:
                list_lines.append(Line(pnts_align))
            else:
                list_lines.append(pnts_align)
            list_attrs.append(
                [
                    ali.get_leng_accum(),
                    ali.__class__.__name__,
                    round(ali.length(), 3),
                    ali.param(),
                    ali.grassrgb(),
                ]
            )
        return list_lines, list_attrs

    def get_charact_pnts(self, lines=False):
        """Return"""
        list_attrs = []
        list_obj = []

        for i, ali in enumerate(self.list_aligns):
            if ali is not None:
                r_pnt = ali.get_roadpoint(0)[0]
                if lines:
                    pnt2 = r_pnt.project(10, r_pnt.azi - math.pi / 2)
                    list_obj.append(Line([r_pnt, pnt2]))
                else:
                    r_pnt.align = ali.__class__.__name__ + "_" + str(i + 1)
                    list_obj.append(r_pnt)
                list_attrs.append(
                    [r_pnt.get_pk(), r_pnt.get_azi(), r_pnt.p_type, ali.param()]
                )
        for i, ali in enumerate(self.list_aligns[::-1]):
            if ali is not None:
                r_pnt = ali.get_roadpoint(-1)[0]
                break
        if lines:
            pnt2 = r_pnt.project(10, r_pnt.azi - math.pi / 2)
            list_obj.append(Line([r_pnt, pnt2]))
        else:
            r_pnt.align = (
                self.list_aligns[-1].__class__.__name__
                + "_"
                + str(len(self.list_aligns) + 1)
            )
            list_obj.append(r_pnt)
        for i, ali in enumerate(self.list_aligns[::-1]):
            if ali is not None:

                list_attrs.append(
                    [ali.get_leng_accum2(), r_pnt.get_azi(), r_pnt.p_type, "L=0"]
                )
                break
        return list_obj, list_attrs

    #    def get_charact_pnts2(self):
    #        """ Return
    #        """
    #        list_obj = []
    #        r_pnt = self.list_aligns[0].get_roadpoint(0)[0]
    #        r_pnt.align = self.list_aligns[0].__class__.__name__ + '_' + str(1)
    #        list_obj.append(r_pnt)
    #        for i, ali in enumerate(self.list_aligns):
    #            if ali is not None:
    #                r_pnt = ali.get_roadpoint(-1)[0]
    #                r_pnt.align = ali.__class__.__name__ + '_' + str(i + 1)
    #                list_obj.append(r_pnt)
    #
    #        return list_obj

    def get_curves_centers(self):
        """Return"""
        list_centers = []
        list_attrs = []
        for i, ali in enumerate(self.list_aligns):
            if isinstance(ali, Base.Curve):
                list_centers.append(ali.p_center)
                list_attrs.append(["C" + str(i + 1)])
        return list_centers, list_attrs


# =============================================
# PLANT ALIGN
# =============================================


class PlantAlign(object):
    """Return"""

    def __init__(self, dat, dat1=None, dat2=None, recta1=None, recta2=None):
        """Return"""
        self.radio = dat["radio"]
        self.a_in = dat["a_in"]
        self.a_out = dat["a_out"]
        self.dat = dat
        self.recta1 = recta1
        self.recta2 = recta2
        self.dat1 = dat1
        self.dat2 = dat2

        self.straight = None
        self.cloth_in = None
        self.curve = None
        self.cloth_out = None

        self.in_local = None
        self.out_local = None

        self._init_align()

    def __str__(self):
        return self.get_wkt()

    def __repr__(self):
        return (
            "PlantAlign( \n"
            + str(self.straight)
            + ", \n"
            + str(self.cloth_in)
            + ", \n"
            + str(self.curve)
            + ", \n"
            + str(self.cloth_out)
            + ")\n"
        )

    def _alpha(self):
        """Return"""
        a_w = self.recta1.angle(self.recta2)
        if self.radio > 0:
            return abs(a_w - self.in_local["tau"] - self.out_local["tau"])
        else:
            return abs(a_w + self.in_local["tau"] + self.out_local["tau"])

    def _center(self):
        """Return the cutoff point between this straight an a given one."""
        if self.radio == 0:
            return Base.RoadPoint(self.recta1.pend, 0, 0)
        else:
            recta11 = self.recta1.parallel(
                abs(self.radio + self.in_local["y_o"]), self.radio
            )
            recta22 = self.recta2.parallel(
                abs(self.radio + self.out_local["y_o"]), self.radio
            )
            return recta11.cutoff(recta22)

    def _init_align(self):
        """Return"""
        local2_in = False
        local2_out = False

        if self.radio != 0:
            self.in_local = Base.cloth_local(self.radio, self.a_in)
            self.out_local = Base.cloth_local(self.radio, self.a_out)

            alpha = self._alpha()
        else:
            alpha = 0

        p_center = self._center()

        if self.dat1["a_out"] < 0 and self.radio != 0:
            local2_out = Base.cloth_local(self.dat1["radio"], self.dat1["a_out"])
        self.cloth_in = Base.Clothoid(
            self.a_in, self.radio, self.recta1.azimuth(), "in", local2_out, p_center
        )

        self.recta1.pend = self.cloth_in.pnt_d

        if self.dat1["a_out"] < 0 and self.radio != 0:
            self.recta1.pstart = self.cloth_in.pnt_p

        if self.radio == 0:
            az_ini = self.recta1.azimuth()
        else:
            az_ini = Base.azimut(p_center, self.cloth_in.pnt_r)
        self.curve = Base.Curve(self.radio, alpha, az_ini, p_center)

        if self.dat2["a_in"] < 0:
            local2_in = Base.cloth_local(self.dat2["radio"], self.dat2["a_in"])
        self.cloth_out = Base.Clothoid(
            self.a_out, self.radio, self.recta2.azimuth(), "out", local2_in, p_center
        )

        self.straight = Base.Straight(self.recta1.pstart, self.recta1.pend, None, None)

    def set_lengs_accum(self, leng_accum):
        """Return the lenght accum of the aling and set the superelev limits"""

        self.straight.leng_accum = leng_accum
        self.cloth_in.leng_accum = self.straight.leng_accum + self.straight.length()
        self.curve.leng_accum = self.cloth_in.leng_accum + self.cloth_in.length()
        self.cloth_out.leng_accum = self.curve.leng_accum + self.curve.length()

        return self.cloth_out.leng_accum + self.cloth_out.length()

    def get_aligns(self):
        """Return"""
        list_aligns = []
        if self.straight.length() != 0:
            list_aligns.append(self.straight)
        if self.cloth_in.a_clot != 0:
            list_aligns.append(self.cloth_in)
        if self.curve.radio != 0:
            list_aligns.append(self.curve)
        if self.cloth_out.a_clot != 0:
            list_aligns.append(self.cloth_out)

        return list_aligns

    def get_super_lim(self, bombeo):
        """Return"""
        super_lim = []
        tot_accum = self.cloth_out.leng_accum + self.cloth_out.length()

        if (
            self.dat["superelev"] != ""
            and self.dat["superelev"] is not None
            and self.dat["superelev"] != "None"
        ):

            dist1, dist2, bom1, peral, bom2, dist3, dist4 = [
                float(p) for p in self.dat["superelev"].split(",")
            ]
            # d1, d2, b, p, b, d2, d1
            super_lim = [
                [
                    self.cloth_in.leng_accum - dist1,
                    self.cloth_in.leng_accum,
                    self.cloth_in.leng_accum + dist2,
                    self.curve.leng_accum,
                ],
                [
                    self.cloth_out.leng_accum,
                    tot_accum - dist3,
                    tot_accum,
                    tot_accum + dist4,
                ],
                bom1,
                peral,
                bom2,
                self.radio,
            ]
        elif (
            bombeo != 0 and self.cloth_in.length() != 0 and self.cloth_out.length() != 0
        ):

            super_lim = [
                [
                    self.cloth_in.leng_accum - self.cloth_in.length() / 2,
                    self.cloth_in.leng_accum,
                    self.cloth_in.leng_accum + self.cloth_in.length() / 2,
                    self.curve.leng_accum,
                ],
                [
                    self.cloth_out.leng_accum,
                    tot_accum - self.cloth_out.length() / 2,
                    tot_accum,
                    tot_accum + self.cloth_out.length() / 2,
                ],
                bombeo,
                bombeo,
                bombeo,
                self.radio,
            ]

        return super_lim

    def get_endpnt(self):
        """Return"""
        return self.cloth_out.pnt_d

    def length(self):
        """Return"""
        return (
            self.straight.length()
            + self.cloth_in.length()
            + self.curve.length()
            + self.cloth_out.length()
        )


# =============================================
# PLANT
# =============================================


class Plant(Aligns, object):
    """Return"""

    def __init__(self, polygon=None, road_table=None, table_to_plan=False, bombeo=0):
        """Return"""
        self.bombeo = bombeo
        self.polygon = polygon
        self.road_table = road_table

        self.straight_curve_lengs = [0]
        self.list_aligns = []
        self.superelev_lim = []

        if table_to_plan is False:
            self._init_poly_to_plant()
        else:
            self._init_table_to_plant()

        super(Plant, self).__init__(self.list_aligns)

    def __str__(self):
        return self.get_wkt()

    #    def __repr__(self):
    #        return "[" + self.align + "]"

    #    def get_wkt(self):
    #        """Return a "well know text" (WKT) geometry string. ::
    #        """
    #        return "[" + str(self.align) + "]"

    def _init_poly_to_plant(self):
        """Return"""
        dat1 = []
        dat2 = []

        line = self.polygon
        leng_accum = 0

        for i, dat3 in enumerate(self.road_table):

            if i >= 2:
                if i == 2:
                    end_pnt = line[0]

                recta1 = Base.Straight(end_pnt, line[i - 1])
                recta2 = Base.Straight(line[i - 1], line[i])

                alig = PlantAlign(dat2, dat1, dat3, recta1, recta2)

                leng_accum = alig.set_lengs_accum(leng_accum)
                self.list_aligns.extend(alig.get_aligns())
                end_pnt = alig.get_endpnt()

                self.straight_curve_lengs.append(alig.straight.length())
                self.straight_curve_lengs.append(alig.curve.length())

                self.superelev_lim.append(alig.get_super_lim(self.bombeo))

            dat1 = dat2
            dat2 = dat3

            if i == len(self.road_table) - 1:
                if len(self.road_table) == 2:
                    end_pnt = line[i - 1]

                recta1 = Base.Straight(end_pnt, line[-1])
                recta1.leng_accum = leng_accum
                self.list_aligns.append(recta1)
                self.straight_curve_lengs.append(recta1.length())

    def _init_table_to_plant(self):
        """Return"""
        pnt_center = Base.RoadPoint(self.polygon[0])
        pnt_1 = Base.RoadPoint(self.polygon[1])
        recta_1 = Base.Straight(pnt_center, pnt_1)

        rectas = []
        new_rows = []

        for i, dat in enumerate(self.road_table):

            new_rows.append(dat)

            if dat["lr_"] != 0:
                new_rows.append(
                    {
                        "radio": 0.0,
                        "a_in": 0.0,
                        "a_out": 0.0,
                        "dc_": dat["dc_"],
                        "lr_": dat["lr_"],
                    }
                )

        for i, dat in enumerate(new_rows[:-1]):

            dat1 = new_rows[i]
            dat2 = new_rows[i + 1]

            if dat1["radio"] == 0 and dat2["radio"] == 0:
                continue
            elif dat1["radio"] == 0:
                pnt_center, pnt_1, recta_1 = self._staight_curve(
                    pnt_center, pnt_1, dat1, dat2
                )
                if i == 1:
                    self.list_aligns.insert(0, recta_1)
                    self.straight_curve_lengs.insert(1, recta_1.length())
            elif dat2["radio"] == 0:
                pnt_center, pnt_1, recta_1 = self._curve_straight(
                    pnt_center, pnt_1, dat1, dat2
                )

            elif abs(dat1["radio"]) > abs(dat2["radio"]) and dat1["a_out"] < 0:
                pnt_center, pnt_1, recta_1 = self._curve_high_low(
                    pnt_center, pnt_1, dat1, dat2
                )

            elif abs(dat1["radio"]) > abs(dat2["radio"]) and dat2["a_in"] < 0:
                pnt_center, pnt_1, recta_1 = self._curve_low_high(
                    pnt_center, pnt_1, dat1, dat2
                )
            else:
                raise ValueError("Error")

            rectas.append(recta_1)

        new_polygon = [rectas[0].pstart]
        for i, recta in enumerate(rectas[:-1]):
            if round(recta.azimuth(), 8) == round(rectas[i + 1].azimuth(), 8):
                continue
            new_polygon.append(recta.cutoff(rectas[i + 1]))
        new_polygon.append(rectas[-1].pend)
        self.polygon = Line(new_polygon)
        self.road_table.polyline = new_polygon

    def _curve_high_low(self, pnt_center, pnt_1, dat1, dat2):
        """Return"""
        # R1>R2
        # Calculamos los puntos de tangencia de la clotoide con los dos circulo
        out_local = Base.cloth_local(dat1["radio"], dat1["a_out"])
        in_local = Base.cloth_local(dat2["radio"], dat2["a_in"])

        azi_in = pnt_center.azimuth(pnt_1)
        alpha = dat2["dc_"] / dat2["radio"]

        if dat1["radio"] > 0 and dat2["radio"] > 0:
            g90 = math.pi / 2
        elif dat1["radio"] < 0 and dat2["radio"] < 0:
            g90 = -math.pi / 2
        else:
            raise ValueError(
                "Error: For change the radio sing a straight must be \
                             between the radios"
            )
        #            return [None, None, None]

        pnt_t1 = pnt_center.project(
            abs(dat1["radio"] + out_local["y_o"]), azi_in - out_local["tau"]
        )

        pnt_t2 = pnt_t1.project(
            in_local["x_o"] - out_local["x_o"], azi_in - out_local["tau"] + g90
        )

        pnt_ad2 = pnt_t1.project(out_local["x_o"], azi_in - out_local["tau"] + g90)

        pnt_c2 = pnt_t2.project(
            abs(dat2["radio"] + in_local["y_o"]), azi_in - out_local["tau"] + 2 * g90
        )

        pnt_ar2 = pnt_c2.project(
            abs(dat2["radio"], azi_in - out_local["tau"] + in_local["tau"])
        )

        pnt_ra2 = pnt_c2.project(
            abs(dat2["radio"]), azi_in - out_local["tau"] + in_local["tau"] + alpha
        )

        if dat2["a_in"] != 0:
            cloth = Base.Clothoid(
                dat2["a_in"], dat2["radio"], pnt_ad2.azimuth(pnt_t2), "in", None, pnt_c2
            )
            self.list_aligns.append()
            self.straight_curve_lengs.append(cloth.length())

        curve = Base.Curve(dat2["radio"], alpha, pnt_c2.azimuth(pnt_ar2), pnt_c2)
        self.list_aligns.append(curve)
        self.straight_curve_lengs.append(curve.length())

        return pnt_c2, pnt_ra2, Base.Straight(pnt_ad2, pnt_t1)

    def _curve_low_high(self, pnt_center, pnt_1, dat1, dat2):
        """Return"""
        # R1<R2
        out_local = Base.cloth_local(dat1["radio"], dat1["a_out"])
        in_local = Base.cloth_local(dat2["radio"], dat2["a_in"])

        azi_in = pnt_center.azimuth(pnt_1)
        alpha = dat2["dc_"] / dat2["radio"]

        if dat1["radio"] > 0 and dat2["radio"] > 0:
            g90 = math.pi / 2
        elif dat1["radio"] < 0 and dat2["radio"] < 0:
            g90 = -math.pi / 2
        else:
            raise ValueError(
                "Error: For change the radio sing a straight \
                             must be between the radios"
            )
        #            return (None, None, None)

        pnt_t1 = pnt_center.project(
            abs(dat1["radio"] + out_local["y_o"]), azi_in + out_local["tau"]
        )

        pnt_t2 = pnt_t1.project(
            in_local["x_o"] - out_local["x_o"], azi_in + out_local["tau"] + g90
        )

        pnt_da1 = pnt_t1.project(out_local["x_o"], azi_in + out_local["tau"] + g90)

        pnt_c2 = pnt_t2.project(
            abs(dat2["radio"] + in_local["y_o"]), azi_in + out_local["tau"] + 2 * g90
        )

        pnt_ra2 = pnt_c2.project(
            abs(dat2["radio"]), azi_in + out_local["tau"] - in_local["tau"] + alpha
        )

        if dat1["a_out"] != 0:
            cloth = Base.Clothoid(
                dat1["a_out"],
                dat1["radio"],
                pnt_t1.azimuth(pnt_da1),
                "out",
                None,
                pnt_c2,
            )
            self.list_aligns.append(cloth)
            self.straight_curve_lengs.append(cloth.length())

        curve = Base.Curve(dat2["radio"], alpha, pnt_c2.azimuth(pnt_ra2), pnt_c2)
        self.list_aligns.append(curve)
        self.straight_curve_lengs.append(curve.length())

        return pnt_c2, pnt_ra2, Base.Straight(pnt_t1, pnt_da1)

    def _curve_straight(self, pnt_center, pnt_1, dat1, dat2):
        """Return"""
        # R1 != 0 y R2 = 0
        out_local = Base.cloth_local(dat1["radio"], dat1["a_out"])

        azi_in = pnt_center.azimuth(pnt_1)
        # pnt_ra = pnt_1

        if dat1["radio"] > 0:
            g90 = math.pi / 2
        else:
            g90 = -math.pi / 2

        pnt_t1 = pnt_center.project(
            abs(dat1["radio"] + out_local["y_o"]), azi_in + out_local["tau"]
        )

        pnt_da = pnt_t1.project(out_local["x_o"], azi_in + out_local["tau"] + g90)

        azi_out = pnt_center.azimuth(pnt_t1) + g90

        if dat1["a_out"] == 0:
            # pnt_da = pnt_ra
            pnt_da = pnt_1
        else:
            cloth = Base.Clothoid(
                dat1["a_out"], dat1["radio"], azi_out, "out", None, pnt_center
            )
            self.list_aligns.append(cloth)
            self.straight_curve_lengs.append(cloth.length())

        pnt_out = pnt_da.project(dat2["lr_"], azi_in + out_local["tau"] + g90)

        recta = Base.Straight(pnt_da, pnt_out)
        self.list_aligns.append(recta)
        self.straight_curve_lengs.append(recta.length())

        return pnt_da, pnt_out, Base.Straight(pnt_da, pnt_out)

    def _staight_curve(self, pnt_center, pnt_1, dat1, dat2):
        """Return"""
        # R1 = 0 y R2 != 0
        in_local = Base.cloth_local(dat2["radio"], dat2["a_in"])

        alpha = dat2["dc_"] / dat2["radio"]

        azi_in = pnt_center.azimuth(pnt_1)
        pnt_ad = pnt_center.project(dat1["lr_"], azi_in)

        pnt_t2 = pnt_ad.project(in_local["x_o"], azi_in)

        if dat2["radio"] > 0:
            g90 = math.pi / 2
        else:
            g90 = -math.pi / 2

        pnt_c2 = pnt_t2.project(abs(dat2["radio"] + in_local["y_o"]), azi_in + g90)
        pnt_c2.npk = dat1["lr_"]

        az_in_c = azi_in + in_local["tau"] - g90
        if az_in_c < 0:
            az_in_c += 2 * math.pi

        pnt_ra = pnt_c2.project(abs(dat2["radio"]), az_in_c + alpha)
        pnt_ra.npk = dat1["lr_"]

        if dat2["a_in"] != 0:
            cloth = Base.Clothoid(
                dat2["a_in"], dat2["radio"], azi_in, "in", None, pnt_c2
            )
            self.list_aligns.append(cloth)
            self.straight_curve_lengs.append(cloth.length())

        curve = Base.Curve(dat2["radio"], abs(alpha), az_in_c, pnt_c2)
        self.list_aligns.append(curve)
        self.straight_curve_lengs.append(curve.length())

        return pnt_c2, pnt_ra, Base.Straight(pnt_center, pnt_ad)

    def get_charact(self):
        """Return"""
        list_pnt = []
        #        list_pnt.append(self.list_aligns[0].get_roadpoint(0)[0])
        for i, ali in enumerate(self.list_aligns):
            pnt = ali.get_roadpoint(-1)[0]
            pnt.npk = self.leng_accum[i + 1]
            list_pnt.append(pnt)
        return list_pnt

    # @time_func
    def set_roadline(self, start, end, intr, intc):
        """Return"""
        puntos = self.get_roadpnts(start, end, intr, intc)
        #        pnts_char = self.get_charact_pnts2()
        # Name lenght type param rgb
        attrs = ["Central_Axis", self.length(), "axis", 0, "255:0:0"]
        self.roadline = Base.RoadLine(puntos, attrs, "Central_Axis")

    def add_pks(self, list_pks):
        """Return"""
        for npk in list_pks:
            self.roadline.insert(self.get_roadpoint(npk))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
