# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 12:02:25 2014

@author: meskal
"""

#
# import pygrass modules
#
import math
import re

# from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line


def azimut(p_ini=None, p_end=None):
    """Return Azimut of two point (x1,y1) (x2,y2), Rad from North
    to clockwise

     >>> azimut(Point(0,0), Point(10,10))
     0.7853981633974483
    """
    if p_ini.x > p_end.x and p_ini.y == p_end.y:
        azi = 3 * math.pi / 2
    elif p_ini.x < p_end.x and p_ini.y == p_end.y:
        azi = math.pi / 2
    elif p_ini.x == p_end.x and p_ini.y > p_end.y:
        azi = math.pi
    elif p_ini.x == p_end.x and p_ini.y < p_end.y:
        azi = 2 * math.pi
    elif p_ini.x == p_end.x and p_ini.y == p_end.y:
        azi = 0
    else:
        azi = math.atan((p_end.x - p_ini.x) / (p_end.y - p_ini.y))
        # if x1> x2 and y1 == y2: az = az + pi # az>0 -> az > 0
        if p_ini.x < p_end.x and p_ini.y > p_end.y:
            azi = azi + math.pi  # az<0 -> az > 100
        elif p_ini.x > p_end.x and p_ini.y > p_end.y:
            azi = azi + math.pi  # az>0 -> az > 200
        elif p_ini.x > p_end.x and p_ini.y < p_end.y:
            azi = azi + 2 * math.pi  # az<0 -> az > 300
    return azi


# def fix_azimuth(azi):
#    """ Return
#    """
#    if azi > 2 * math.pi:
#        return azi - 2 * math.pi
#    else:
#        return azi + 2 * math.pi


def aprox_coord(leng, tau):
    """Return coord (x1,y1) of a clothoid given the angle Tau and length
    ::
    >>> aprox_coord(10, 5)
    [-50, -50]
    """
    n_iter = 10
    c_x = 0
    c_y = 0
    for n_i in range(n_iter):
        c_x += ((-1) ** n_i * tau ** (2 * n_i)) / (
            (4 * n_i + 1) * math.factorial(2 * n_i)
        )
        c_y += ((-1) ** n_i * tau ** (2 * n_i + 1)) / (
            (4 * n_i + 3) * math.factorial(2 * n_i + 1)
        )
    c_x = c_x * leng
    c_y = c_y * leng
    return [c_x, c_y]


def aprox_coord2(radio, tau):
    """Return coord (x1,y1) of a clothoid given the angle Tau and Radio
    ::
    >>> aprox_coord(100, 50)
    [-1411567899002100L, -3476091295999800L]
    """
    n_iter = 10
    c_x = 0
    c_y = 0
    for n_i in range(n_iter):
        c_x += (
            (-1) ** n_i
            * (2 * tau ** (2 * n_i + 1) / ((4 * n_i + 1) * math.factorial(2 * n_i)))
        ) - ((-1) ** n_i * (tau ** (2 * n_i + 1) / math.factorial(2 * n_i + 1)))

        c_y += (
            (-1) ** n_i
            * (2 * tau ** (2 * n_i + 2) / ((4 * n_i + 3) * math.factorial(2 * n_i + 1)))
        ) + ((-1) ** n_i * (tau ** (2 * n_i) / math.factorial(2 * n_i)))

    c_x = c_x * radio
    c_y = c_y * radio - radio
    return [c_x, c_y]


def cloth_local(radio, a_clot):
    """Return clothoid parameters in local coord
    ::
    >>> cloth_local(40,20)
    {'tau': 0, 'x_e': 10, 'leng': 10, 'x_o': 10.0, 'y_o': 0.0, 'y_e': 0}
    """
    if radio == 0:
        leng, tau = 0, 0
    else:
        leng = a_clot**2 / abs(radio)
        tau = leng / (2 * radio)
    x_e, y_e = aprox_coord(leng, tau)
    x_o = x_e - radio * math.sin(tau)
    y_o = y_e + radio * math.cos(tau) - radio

    return {"x_o": x_o, "y_o": y_o, "tau": tau, "leng": leng, "x_e": x_e, "y_e": y_e}


def clotoide_get_a(radio, yo_ent, sobreancho, izq):
    """Return param A of a clothoid in a curve with widening"""
    inc = math.pi / 200
    tau = 0.0001 * math.pi / 200
    y_o = aprox_coord2(abs(radio), tau)[1]
    if (izq and radio > 0) or (izq == 0 and radio < 0):
        sobreancho = sobreancho
    elif (izq and radio < 0) or (izq == 0 and radio > 0):
        sobreancho = sobreancho * (-1)

    # Comprobar que el sobreancho sea mayor que el retranqueo
    while abs(y_o - (yo_ent - sobreancho)) > 0.0001:

        y_o = aprox_coord2(abs(radio), tau)[1]
        if y_o > yo_ent - sobreancho:
            tau = tau - inc
            inc = inc / 10
        else:
            tau = tau + inc

    leng = tau * 2 * abs(radio)
    return math.sqrt(leng * abs(radio))


def bisecc(r_pnt, align):
    """Return cutoff roadpoint of a straight, given by a roadpoint with its
    azimuth, and a road object defined by the funct function
    """
    recta2 = r_pnt.normal(math.pi)
    len_a = -0.00001
    len_b = align.length()
    eq_a = align.funct(len_a, recta2)
    eq_b = align.funct(len_b, recta2)

    if round(eq_a[0], 5) * round(eq_b[0], 5) > 0:
        return None

    len_c = (len_a + len_b) / 2.0
    while (len_b - len_a) / 2.0 > 0.00001:
        eq_c = align.funct(len_c, recta2)
        eq_a = align.funct(len_a, recta2)
        if eq_c[0] == 0:
            continue
        elif eq_a[0] * eq_c[0] <= 0:
            len_b = len_c
        else:
            len_a = len_c
        len_c = (len_a + len_b) / 2.0

    return RoadPoint(Point(eq_c[1], eq_c[2], 0), len_c, r_pnt.azi, "")


def format_pk(funcion_f):
    """Return the pk format 10+000.001 of a funtion"""

    def funcion_r(*arg):
        """Return"""
        ipk = funcion_f(*arg)
        ipk = round(ipk, 4)
        if str(ipk).find(".") == -1:
            integer = str(ipk)
            decimal = "0"
        else:
            integer, decimal = str(ipk).split(".")
        integer = re.sub(r"\B(?=(?:\d{3})+$)", "+", "{:0>4}".format(integer))
        return integer + "." + decimal

    return funcion_r


def write_objs(allrectas, radio):
    """Return"""
    new2 = VectorTopo("AAAAA__" + str(int(radio)))
    # cols = [(u'cat',       'INTEGER PRIMARY KEY'),
    #        (u'elev',      'INTEGER')]

    new2.open("w")
    for obj in allrectas:
        new2.write(obj)
    # new2.table.conn.commit()
    new2.close()


# =============================================
# ROAD POINT
# =============================================


class RoadPoint(Point, object):
    """RoadPoint object, is a Point with pk and azimuth, and others params
    >>> r_pnt = RoadPoint(Point(1,1,0), 0, 0)
    """

    def __init__(self, point=None, npk=None, azi=None, p_type=None):
        """Return"""
        super(RoadPoint, self).__init__(point.x, point.y, point.z)

        self.x = point.x
        self.y = point.y
        self.z = point.z
        self.point2d = Point(self.x, self.y)

        self.npk = npk
        self.azi = azi
        self.p_type = p_type
        self.align = ""
        self.incli = 0

        self.v_param = 0
        self.v_type = "none"

        self.terr = 0
        self.terr_type = "none"

        self.dist_displ = 0
        self.acum_pk = 0

        if self.z is None:
            self.z = 0

    def __repr__(self):
        return (
            "RoadPoint("
            + str(self.x)
            + ", "
            + str(self.y)
            + ", "
            + str(self.z)
            + ", "
            + str(self.npk)
            + ", "
            + str(self.azi)
            + ", "
            + str(self.p_type)
            + ", "
            + str(self.align)
            + ", "
            + str(self.v_param)
            + ", "
            + str(self.v_type)
            + ", "
            + str(self.terr)
            + ", "
            + str(self.terr_type)
            + ", "
            + str(self.dist_displ)
            + ")"
        )

    def get_wkt(self):
        """Return a "well know text" (WKT) geometry string. ::

        >>> pnt = Point(10, 100)
        >>> pnt.get_wkt()
        'POINT(10.000000 100.000000)'
        """
        return (
            "ROADPOINT("
            + str(self.x)
            + ", "
            + str(self.y)
            + ", "
            + str(self.z)
            + ", "
            + str(self.npk)
            + ", "
            + str(self.azi)
            + ", "
            + str(self.p_type)
            + ", "
            + str(self.align)
            + ", "
            + str(self.v_param)
            + ", "
            + str(self.v_type)
            + ", "
            + str(self.terr)
            + ", "
            + str(self.terr_type)
            + ", "
            + str(self.dist_displ)
            + ")"
        )

    def get_info(self):
        """Return point pk"""
        sal = "ROADPOINT( \n"
        sal += " Point(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")\n"
        sal += " pk: " + str(self.npk) + "\n"
        sal += " azimuth: " + str(self.azi * 200 / math.pi) + "\n"
        sal += " p_type: " + str(self.p_type) + "\n"
        sal += " align: " + str(self.align) + "\n"
        sal += " v_param: " + str(self.v_param) + "\n"
        sal += " v_type: " + str(self.v_type) + "\n"
        sal += " z_terr: " + str(self.terr) + "\n"
        sal += " terr_type: " + str(self.terr_type) + "\n"
        sal += " dist displ: " + str(self.dist_displ) + "\n)"

        return sal

    @format_pk
    def get_pk(self):
        """Return point pk"""
        return float(self.npk)

    def get_azi(self):
        """Return azimuth of roadpoint in gon
        >>> r_pnt = RoadPoint(Point(1,1,0), 0, 0.7853981633974483)
        >>> r_pnt.get_azi()
        50.0
        """
        return round(self.azi * 200 / math.pi, 4)

    def azimuth(self, pnt2):
        """Return azimuth of this roadpoint with another one
        >>> r_pnt = RoadPoint(Point(1,1,0), 0, 0)
        >>> r_pnt2 = RoadPoint(Point(2,2,0), 0, 0)
        >>> r_pnt.azimuth(r_pnt2)
        0.7853981633974483
        """
        return azimut(self, pnt2)

    def distance2(self, pnt2):
        """Return point pk"""
        return math.sqrt((pnt2.x - self.x) ** 2 + (pnt2.y - self.y) ** 2)

    def slope(self, pnt2):
        """Return the slope between this point and the given one"""
        # leng = Point.distance(pnt2)
        leng = math.sqrt((pnt2.x - self.x) ** 2 + (pnt2.y - self.y) ** 2)
        if leng == 0:
            return 0
        else:
            return (pnt2.z - self.z) / leng

    def slope2(self, pnt2):
        """Return the slope between this point and the given one"""
        if self.npk == pnt2.npk:
            return 0
        else:
            return (pnt2.z - self.z) / (pnt2.npk - self.npk)

    def get_straight(self, dist=1):
        """Return"""
        pto_2 = self.project(dist, self.azi)
        return Straight(self, pto_2)

    def project(self, dist, azi, sig=1):
        """Return"""
        return RoadPoint(
            Point(
                self.x + sig * dist * math.sin(azi), self.y + sig * dist * math.cos(azi)
            ),
            self.npk,
            azi,
            "",
        )

    def parallel(self, dist, g90):
        """Return"""
        return RoadPoint(
            Point(
                self.x + dist * math.sin(self.azi + g90),
                self.y + dist * math.cos(self.azi + g90),
            ),
            self.npk,
            self.azi,
            self.p_type,
        )

    def normal(self, g90):
        """Return"""
        return Straight(self.point2d, None, self.azi + g90, 20)


# =============================================
# ROAD LINE
# =============================================


class RoadLine(object):
    """Class to manage list of roadpoints"""

    def __init__(self, list_r_pnts, attrs=None, name=None):
        """Return"""
        #        super(RoadLine, self).__init__(list_r_pnts)
        #        if isinstance(list_r_pnts[0], list):
        #            self.list_r_pnts = list_r_pnts
        #        else:
        #            self.list_r_pnts = [list_r_pnts]

        self.r_pnts = list_r_pnts
        self.attrs = attrs
        self.name = name

    #        self.pnts_char = pnts_char

    def __getitem__(self, index):
        return self.r_pnts[index]

    def __setitem__(self, index, value):
        self.r_pnts[index] = value

    def __delitem__(self, index):
        del self.r_pnts[index]

    def __len__(self):
        return len(self.r_pnts)

    def __repr__(self):
        return str(self.r_pnts)

    def length(self):
        """Return"""
        return len(self.r_pnts)

    def is_in(self, r_pnt):
        """Return"""
        if r_pnt.npk in [pnt.npk for pnt in self.r_pnts]:
            return True
        else:
            return False

    def insert(self, r_pnt):
        """Insert a roadpoint with pk like index"""
        #        if not self.is_in(r_pnt):
        for i, pnt in enumerate(self.r_pnts[:-1]):
            if pnt.npk < r_pnt.npk < self.r_pnts[i + 1].npk:
                self.r_pnts.insert(i + 1, r_pnt)

    #    def get_segments(self, charline):
    #        """Return
    #        """

    def get_by_pk(self, npk):
        """Return the roadpoint with npk"""
        for pnt in self.r_pnts:
            if pnt is not None:
                if pnt.npk == npk:
                    return pnt

    def get_pnts_attrs(self):
        """Return all roadpoints and their attributes"""
        list_pnts = []
        list_attrs = []
        for r_pnt in self.r_pnts:
            if r_pnt is not None:
                list_pnts.append(r_pnt)
                list_attrs.append(
                    [
                        r_pnt.npk,
                        self.name,
                        r_pnt.azi,
                        r_pnt.p_type,
                        r_pnt.align,
                        r_pnt.v_param,
                        r_pnt.v_type,
                        float(r_pnt.terr),
                        r_pnt.terr_type,
                        r_pnt.dist_displ,
                        r_pnt.x,
                        r_pnt.y,
                        r_pnt.z,
                        "",
                    ]
                )
        return list_pnts, list_attrs

    def get_line_attrs(self, set_leng=None):
        """Return Line or list of Lines, split if some roadpoint of the
        roadline is None, and attributes
        """
        list_lines = [[]]
        list_attrs = []
        lista_lineas = []
        for r_pnt in self.r_pnts:
            if r_pnt is not None:
                list_lines[-1].append(r_pnt)
            elif list_lines[-1] != []:
                list_lines.append([])
        for i, lin in enumerate(list_lines):
            if len(lin) != 0:
                lista_lineas.append(Line(lin))
                if set_leng:
                    self.attrs[set_leng] = round(lista_lineas[-1].length(), 6)
                list_attrs.append(self.attrs)
        return lista_lineas, list_attrs

    #    def get_segm_attrs(self):
    #        """Return
    #        """
    #        list_lines = []
    #        list_attrs = []
    #        for i, pnt_char in enumerate(self.pnts_char[1:]):
    #            list_lines.append([self.pnts_char[i - 1]])
    #            for r_pnt in self.r_pnts:
    #                if r_pnt is not None:
    #                    if round(self.pnts_char[i - 1].npk, 6) < r_pnt.npk < \
    #                            pnt_char.npk:
    #                        list_lines[-1].append(r_pnt)
    #            list_lines[-1].append(pnt_char)
    #
    #            list_attrs.append([pnt_char.npk, pnt_char.p_type])
    #
    #        return list_lines, list_attrs

    #    def get_ras(self, r_line):
    #        """Return
    #        """
    #        line = []
    #        for r_pnt in r_line:
    #            line.append(Point(r_pnt.npk + self.zero_x,
    #                              (r_pnt.z - self.min_elev) * self.scale +
    #                              self.zero_y))
    #        return Line(line)
    #
    #    def get_terr(self, r_line):
    #        """Return
    #        """
    #        line = []
    #        for r_pnt in r_line:
    #            line.append(Point(r_pnt.npk + self.zero_x,
    #                              (r_pnt.terr - self.min_elev) * self.scale +
    #                              self.zero_y))
    #        return Line(line)

    def get_area(self, pnts_line2):
        """Return a closed polyline with this roadline and the reverse of the
        given roadline
        """
        list_lines = []
        pnts_line1 = self.r_pnts
        line1, line2 = [[]], [[]]
        for i in range(len(pnts_line1)):
            if pnts_line1[i] is None or pnts_line2[i] is None:
                if line1[-1] != [] and line2[-1] != []:
                    line1.append([])
                    line2.append([])
            else:
                line1[-1].append(pnts_line1[i])
                line2[-1].append(pnts_line2[i])

        line1 = [lin for lin in line1 if lin != []]
        line2 = [lin for lin in line2 if lin != []]

        for i in range(len(line1)):

            line2[i] = line2[i][::-1]
            line2[i].append(line1[i][0])
            line1[i].extend(line2[i])

            line = Line(line1[i])
            list_lines.append(line)

        return list_lines


# =============================================
# ROAD OBJ
# =============================================


class RoadObj(object):
    """Road object, base of straight, curve, clothoid and parallel"""

    def __init__(self, leng_obj):
        """Return"""
        self.leng_obj = leng_obj
        self.leng_accum = 0

        self.pts_rest = 0
        self.pts_accum = 0

    def param(self):
        """Return string with length of the object"""
        return "L=" + str(round(self.leng_obj, 4))

    @format_pk
    def get_leng_accum(self):
        """Return the length accum"""
        return self.leng_accum

    @format_pk
    def get_leng_accum2(self):
        """Return the length accum and length of this"""
        return self.leng_accum + self.leng_obj

    def is_in(self, r_pnt):
        """Return"""
        if self.leng_accum <= r_pnt.npk < self.leng_accum + self.leng_obj:
            return True
        else:
            return False

    def grassrgb(self):
        """Return the default rgb color for each object"""
        if isinstance(self, Straight):
            return "0:0:255"
        elif isinstance(self, Curve):
            return "0:255:0"
        elif isinstance(self, Clothoid):
            return "255:0:0"
        else:
            return "255:255:255"

    def get_roadpoint(self, start):
        """Return a roadpoint found by pk"""
        if start == -1:
            start = self.leng_obj
        self.pts_accum = start
        r_pnt = self.get_roadpnts(start, start, 1)[0]
        r_pnt.npk = self.leng_accum + start
        if start == 0:
            # r_pnt.p_type = self.pto_ini()
            r_pnt.p_type = self.__class__.__name__ + "_in"
        elif start == self.leng_obj:
            # r_pnt.p_type = self.pto_end()
            r_pnt.p_type = self.__class__.__name__ + "_out"
        return [r_pnt]


#    def pto_ini(self):
#        """ Return
#        """
#        if isinstance(self, Straight):
#            return 'Straight_in'
#        elif isinstance(self, Curve):
#            return 'Curve_tan_in'
#        elif isinstance(self, Clothoid):
#            return 'Clothoid_tan_in'
#        else:
#            return 'No_name'
#
#    def pto_end(self):
#        """ Return
#        """
#        if isinstance(self, Straight):
#            return 'Straight_end'
#        elif isinstance(self, Curve):
#            return 'Curve_tan_out'
#        elif isinstance(self, Clothoid):
#            return 'Clothoid_tan_out'
#        else:
#            return 'No_name'

#    def get_line(self, start, end, interv):
#        """ Return
#        """
#        pnts = self.get_roadpnts(start, end, interv)
#        lastpnt = self.get_roadpoint(-1)[0]
#        if lastpnt not in pnts:
#            pnts.append(lastpnt)
#        return Line(pnts)


# =============================================
# STRAIGHT
# =============================================


class Straight(RoadObj, object):
    """Object straight, line with two points or point azimuth and leng
    ::
    >>> line = Straight(Point(0,0,0), Point(10,10,0), 0, 0)
    >>> line.length()
    14.142135623730951
    """

    def __init__(self, pstart=None, pend=None, azi=None, leng=None):
        """Return"""
        self.pstart = pstart
        self.pend = pend
        self.azi = azi
        self.leng = leng

        #        self.pts_rest = 0
        #        self.pts_accum = 0

        if self.azi and self.leng:
            self.pend = Point(
                self.pstart.x + self.leng * math.sin(self.azi),
                self.pstart.y + self.leng * math.cos(self.azi),
            )

        super(Straight, self).__init__(self.length())

    def __str__(self):
        if not self.pstart.z:
            self.pstart.z = 0.0
        return self.get_wkt()

    def __repr__(self):
        if not self.pstart.z:
            self.pstart.z = 0.0
        return (
            "Straight("
            + str(self.pstart.x)
            + ", "
            + str(self.pstart.y)
            + ", "
            + str(self.pstart.z)
            + ", "
            + str(self.length())
            + ", "
            + str(self.azimuth())
            + ", "
            + str(self.pend.x)
            + ", "
            + str(self.pend.y)
            + ")"
        )

    def get_wkt(self):
        """Return a "well know text" (WKT) geometry string. ::
        ::
        >>> pnt = Point(10, 100)
        >>> pnt.get_wkt()
        'POINT(10.000000 100.000000)'
        """
        return (
            "STRAIGHT("
            + str(self.pstart.x)
            + ", "
            + str(self.pstart.y)
            + ", "
            + str(self.pstart.z)
            + ", "
            + str(self.length())
            + ", "
            + str(self.azimuth())
            + ", "
            + str(self.pend.x)
            + ", "
            + str(self.pend.y)
            + ")"
        )

    def get_line(self):
        """Return length of the straight"""
        return Line([self.pstart, self.pend])

    def length(self):
        """Return length of the straight"""
        return self.pstart.distance(self.pend)

    def get_roadpnts(self, start, end, interv):
        """Return list of axis points of a straight
        ::
        >>> line = Straight(Point(0,0,0), Point(10,10,0), 0, 0)
        >>> line.get_roadpnts(3,7,1) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [RoadPoint(2.12132034356, 2.12132034356, 0.0, 0, 0.785398163397,
        ...
        """
        accum = self.pts_accum
        if end == -1:
            end = self.length()

        azi = self.azimuth()
        list_pts = []
        while start <= end:
            pnt = Point(
                self.pstart.x + start * math.sin(azi),
                self.pstart.y + start * math.cos(azi),
                self.pstart.z,
            )

            list_pts.append(RoadPoint(pnt, accum, round(azi, 6), "Line"))
            accum += interv
            start += interv

        self.pts_rest = end - (start - interv)
        self.pts_accum = accum - interv
        return list_pts

    def azimuth(self):
        """Return azimut of the straight
        ::
        >>> line = Straight(Point(0,0,0), Point(10,10,0), 0, 0)
        >>> line.azimuth()
        0.7853981633974483
        """
        return azimut(self.pstart, self.pend)

    def slope(self):
        """Return slope of the straight
        ::
        >>> line = Straight(Point(0,0,0), Point(10,10,10), 0, 0)
        >>> line.slope()
        1.0
        """
        return (self.pend.z - self.pstart.z) / (self.pend.x - self.pstart.x)

    def angle(self, recta2):
        """Return angle between two straights
        ::
        >>> line = Straight(Point(0,0,0), Point(10,10,10), 0, 0)
        >>> line2 = Straight(Point(30,0,0), Point(20,10,10), 0, 0)
        >>> line.angle(line2) * 200 / math.pi
        100.0
        """
        az_ent = azimut(self.pstart, self.pend)
        az_sal = azimut(recta2.pstart, recta2.pend)
        a_w = abs(azimut(self.pstart, self.pend) - azimut(recta2.pstart, recta2.pend))
        if (self.pstart.x <= self.pend.x and self.pstart.y <= self.pend.y) or (
            self.pstart.x <= self.pend.x and self.pstart.y >= self.pend.y
        ):
            if az_ent < az_sal and az_ent + math.pi < az_sal:
                a_w = 2 * math.pi - abs(az_ent - az_sal)

        if (self.pstart.x >= self.pend.x and self.pstart.y >= self.pend.y) or (
            self.pstart.x >= self.pend.x and self.pstart.y <= self.pend.y
        ):
            # "3er o 4to cuadrante"
            if az_ent > az_sal and az_ent - math.pi > az_sal:
                a_w = 2 * math.pi - abs(az_ent - az_sal)
        return a_w

    def cutoff(self, recta2):
        """Return the cutoff point between this straight an a given one.
        ::
        >>> line = Straight(Point(0,0,0), Point(10,10,10), 0, 0)
        >>> line2 = Straight(Point(30,0,0), Point(20,10,10), 0, 0)
        >>> line.cutoff(line2)
        RoadPoint(15.0, 15.0, 0.0, 21.2132034356, 0, , , 0, none, 0, none, 0)
        """
        if self.pstart.x == self.pend.x:
            m_2 = (recta2.pend.y - recta2.pstart.y) / (recta2.pend.x - recta2.pstart.x)
            coord_x = self.pstart.x
            coord_y = recta2.pstart.y + m_2 * (self.pstart.x - recta2.pstart.x)
        elif recta2.pstart.x == recta2.pend.x:
            m_1 = (self.pend.y - self.pstart.y) / (self.pend.x - self.pstart.x)
            coord_x = recta2.pstart.x
            coord_y = self.pstart.y + m_1 * (recta2.pstart.x - self.pstart.x)
        else:
            m_1 = (self.pend.y - self.pstart.y) / (self.pend.x - self.pstart.x)
            m_2 = (recta2.pend.y - recta2.pstart.y) / (recta2.pend.x - recta2.pstart.x)
            coord_x = (
                m_1 * self.pstart.x
                - m_2 * recta2.pstart.x
                - self.pstart.y
                + recta2.pstart.y
            ) / (m_1 - m_2)
            coord_y = m_1 * (coord_x - self.pstart.x) + self.pstart.y

        return RoadPoint(
            Point(coord_x, coord_y),
            self.pstart.distance(Point(coord_x, coord_y)),
            self.azi,
            "",
        )

    def funct(self, leng, recta2):
        """Funtion for use with bisecc"""
        x_1 = self.pstart.x + leng * math.sin(self.azimuth())
        y_1 = self.pstart.y + leng * math.cos(self.azimuth())
        eq1 = y_1 - (
            recta2.pstart.y - math.tan(recta2.azimuth()) * (x_1 - recta2.pstart.x)
        )
        return [eq1, x_1, y_1]

    def find_cutoff(self, r_pnt):
        """Return the cutoff between this straight and other, given a r_pnt
        with its azimuth.
        >>> line = Straight(Point(0,0,0), Point(20,20,10), 0, 0)
        >>> r_pnt = RoadPoint(Point(30,0,0), 0, line.azimuth(), 0)
        >>> line.find_cutoff(r_pnt) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        RoadPoint(14.9999997412, 14.9999997412, 0.0, 21.2132039637,
        ...
        """
        r_pnt_d = bisecc(r_pnt, self)
        if r_pnt_d is not None:
            r_pnt_d.p_type = "Line"
        return r_pnt_d

    def distance(self, pnt):
        """Return distace from a point to this straight
        >>> line = Straight(Point(0,0,0), Point(20,20,10), 0, 0)
        >>> line.distance(Point(10,0,0))
        7.071067811865475
        """
        if self.pstart.x == self.pend.x:
            slope = 0
        else:
            slope = (self.pend.x - self.pstart.x) / (self.pend.y - self.pstart.y)
        rest = self.pstart.y + slope * self.pstart.x
        return (slope * pnt.x + pnt.y - rest) / math.sqrt(slope**2 + 1)

    def parallel(self, dist, radio):
        """Return a parallel straight with a given distance and side given by
        the sing of radio.
        >>> line = Straight(Point(0,0,0), Point(20,20,10), 0, 0)
        >>> line.parallel(10, -1) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Straight(-7.07106781187, 7.07106781187, 0.0, 28.2842712475,
        ...
        """
        if radio > 0:
            g90 = math.pi / 2
        else:
            g90 = -math.pi / 2

        x_1 = self.pstart.x + dist * math.sin(self.azimuth() + g90)
        y_1 = self.pstart.y + dist * math.cos(self.azimuth() + g90)

        x_2 = self.pend.x + dist * math.sin(self.azimuth() + g90)
        y_2 = self.pend.y + dist * math.cos(self.azimuth() + g90)

        return Straight(Point(x_1, y_1), Point(x_2, y_2))


# =============================================
# CURVE
# =============================================


class Curve(RoadObj, object):
    """Object Curve, curve with radio, angle, initial azimuth and center
    ::
    >>> r_pnt = RoadPoint(Point(50,50,0), 0, 0, 0)
    >>> curve = Curve(10.0, 1.5707963268, 0.7853981633974483, r_pnt)
    >>> curve.length()
    15.707963268
    """

    def __init__(self, radio=0, alpha=0, az_ini=0, p_center=None):

        self.radio = radio
        self.alpha = alpha
        self.az_ini = az_ini

        self.p_center = p_center

        self.pts_rest = 0
        self.pts_accum = 0

        if self.radio > 0:
            self.az_fin = self.az_ini + self.alpha
        else:
            self.az_fin = self.az_ini - self.alpha

        if self.az_fin > 2 * math.pi:
            self.az_fin = self.az_fin - 2 * math.pi
        elif self.az_fin < 0:
            self.az_fin = self.az_fin + 2 * math.pi

        super(Curve, self).__init__(self.length())

    def __str__(self):
        return self.get_wkt()

    def __repr__(self):

        return (
            "Curve("
            + str(self.radio)
            + ", "
            + str(self.alpha)
            + ", "
            + str(self.p_center.x)
            + ", "
            + str(self.p_center.y)
            + ", "
            + str(self.az_ini)
            + ", "
            + str(self.az_fin)
            + ", "
            + str(self.length())
            + ", "
            + str(self.pnt_ar())
            + ", "
            + str(self.pnt_ra())
            + ", "
            + ")"
        )

    def get_wkt(self):
        """Return a "well know text" (WKT) geometry string. ::

        >>> pnt = Point(10, 100)
        >>> pnt.get_wkt()
        'POINT(10.000000 100.000000)'
        """
        return (
            "CURVE("
            + str(self.radio)
            + ", "
            + str(self.alpha)
            + ", "
            + str(self.p_center.x)
            + ", "
            + str(self.p_center.y)
            + ", "
            + str(self.az_ini)
            + ", "
            + str(self.az_fin)
            + ", "
            + str(self.length())
            + ", "
            + str(self.pnt_ar())
            + ", "
            + str(self.pnt_ra())
            + ", "
            + ")"
        )

    def param(self):
        """Return a string with the radio of the curve"""
        return "R=" + str(self.radio)

    def length(self):
        """Return length of the curve"""
        return abs(self.radio) * self.alpha

    def get_roadpnts(self, start, end, interv):
        """ Return list of points of the curve, and set length of last point
        to the end and accumulated length
        ::
        >>> r_pnt = RoadPoint(Point(50,50,0), 0, 0, 0)
        >>> curve = Curve(10.0, 1.5707963268, 0.7853981633974483, r_pnt)
        >>> curve.get_roadpnts(0, -1, 1.0) # doctest: +ELLIPSIS \
                                                      +NORMALIZE_WHITESPACE
        [RoadPoint(57.0710678119, 57.0710678119, 0.0, 0,
        ...
        """
        accum = self.pts_accum
        az_ini = self.az_ini
        if end == -1:
            end = self.length()
        list_pts = []
        interv = abs(float(interv) / float(self.radio))

        az_ini = az_ini + start / self.radio
        az_fin = az_ini + (end - start) / self.radio

        inc = az_ini
        if self.radio > 0:

            while inc <= az_fin:
                pnt_1 = self.p_center.project(self.radio, inc)
                az1 = inc + math.pi / 2
                inc += interv

                if az1 > 2 * math.pi:
                    az1 = az1 - 2 * math.pi

                list_pts.append(RoadPoint(pnt_1, accum, round(az1, 6), "Curve"))
                accum += interv * abs(self.radio)
            rest = (az_fin - (inc - interv)) * abs(self.radio)

        elif self.radio < 0:

            while inc >= az_fin:
                pnt_1 = self.p_center.project(self.radio, inc, -1)
                az1 = inc - math.pi / 2
                inc -= interv

                if az1 < 0:
                    az1 = az1 + 2 * math.pi

                list_pts.append(RoadPoint(pnt_1, accum, round(az1, 6), "Curve"))
                accum += interv * abs(self.radio)
            rest = ((inc + interv) - az_fin) * abs(self.radio)

        self.pts_rest = rest
        self.pts_accum = accum - interv * abs(self.radio)
        return list_pts

    def distance(self, pnt):
        """Return distance from a point to the curve
        ::
        >>> r_pnt = RoadPoint(Point(50,50,0), 0, 1.5707963268, 0)
        >>> curve = Curve(10.0, 1.5707963268, 0.7853981633974483, r_pnt)
        >>> curve.distance(Point(0,0))
        60.710678118654755
        """
        line = Straight(self.p_center, pnt)
        return line.length() - self.radio

    def pnt_ar(self):
        """Return the first point of the curve"""
        return self.p_center.project(abs(self.radio), self.az_ini)

    def pnt_ra(self):
        """Return the last point of the curve"""
        return self.p_center.project(abs(self.radio), self.az_fin)

    def cutoff(self, recta2):
        """Return the cutoff between this curve and a straight"""
        dist = recta2.distance(self.p_center)
        if dist == 0:
            pnt_1 = self.p_center.project(self.radio, recta2.azimuth())
        else:
            phi = math.acos(dist / self.radio)
            pnt_1 = self.p_center.project(
                self.radio, recta2.azimuth() + math.pi / 2 + phi
            )
        return pnt_1

    def funct(self, leng, recta2):
        """Funtion for use with bisecc"""
        if self.radio > 0:
            if self.az_ini > self.az_fin:
                self.az_ini = self.az_ini - 2 * math.pi
            x_1 = self.p_center.x + self.radio * math.sin(
                self.az_ini + leng / abs(self.radio)
            )
            y_1 = self.p_center.y + self.radio * math.cos(
                self.az_ini + leng / abs(self.radio)
            )
        elif self.radio < 0:
            if self.az_ini < self.az_fin:
                self.az_fin = self.az_fin - 2 * math.pi
            x_1 = self.p_center.x - self.radio * math.sin(
                self.az_ini - leng / abs(self.radio)
            )
            y_1 = self.p_center.y - self.radio * math.cos(
                self.az_ini - leng / abs(self.radio)
            )

        eq1 = y_1 - (
            recta2.pstart.y - math.tan(recta2.azimuth()) * (x_1 - recta2.pstart.x)
        )
        return [eq1, x_1, y_1]

    def find_cutoff(self, r_pnt):
        """Return the cutoff between this curve and a straight, given by r_pnt
        with its azimuth.
        """
        r_pnt_d = bisecc(r_pnt, self)
        if r_pnt_d is not None:
            r_pnt_d.p_type = "Curve_"
        return r_pnt_d


# =============================================
# CLOTHOID
# =============================================


class Clothoid(RoadObj, object):
    """Object Clothoid, with param A, radio, initial azimuth, in or out,
    and center of the curve. Other_local coord in local of other clothoid
    ::
    """

    def __init__(
        self, a_clot=0, radio=0, azi=0, inout="", other_local=None, p_center=None
    ):

        self.radio = radio
        self.a_clot = a_clot
        self.other_local = other_local
        self.azi = azi
        self.inout = inout
        self.p_center = p_center

        self.pts_rest = 0
        self.pts_accum = 0

        if self.radio > 0:
            self.g90 = math.pi / 2
        else:
            self.g90 = -math.pi / 2

        if self.other_local:
            self.leng_rest = self.other_local["leng"]
        else:
            self.leng_rest = 0

        self.pnt_r = None
        self.pnt_d = None
        self.pnt_p = None

        self.local = cloth_local(self.radio, self.a_clot)

        if self.inout == "in":

            if self.a_clot <= 0:
                self.pnt_r = self._pnt_ar()
                self.pnt_d = self.pnt_r
                self.pnt_p = self.pnt_r
            else:
                self.pnt_d = self._pnt_ad()
                self.pnt_r = self._pnt_ar()
                self.pnt_p = self.pnt_d

                if self.other_local:
                    self.leng_rest = self.other_local["leng"]
                    self.pnt_p = self._pnt_adp()
        else:
            if self.a_clot <= 0:
                self.pnt_r = self._pnt_ra()
                self.pnt_d = self.pnt_r
                self.pnt_p = self.pnt_r
            else:
                self.pnt_d = self._pnt_da()
                self.pnt_r = self._pnt_ra()
                self.pnt_p = self.pnt_d

                if self.other_local:
                    self.leng_rest = self.other_local["leng"]
                    self.pnt_p = self._pnt_dap()

        super(Clothoid, self).__init__(self.length())

    def __str__(self):
        return self.get_wkt()

    def __repr__(self):
        return (
            "Clothoid("
            + str(self.a_clot)
            + ", "
            + str(self.azi)
            + ", "
            + str(self.pnt_d)
            + ", "
            + str(self.pnt_r.x)
            + ", "
            + str(self.pnt_r.y)
            + ", "
            + str(self.length())
            + ", "
            + str(self.radio)
            + ", "
            + str(self.leng_rest)
            + ", "
            + str(self.pnt_p.x)
            + ", "
            + str(self.pnt_p.y)
            + ", "
            + self.inout
            + ")"
        )

    def get_wkt(self):
        """Return a "well know text" (WKT) geometry string. ::

        >>> pnt = Point(10, 100)
        >>> pnt.get_wkt()
        'POINT(10.000000 100.000000)'
        """
        return (
            "CLOTHOID("
            + str(self.a_clot)
            + ", "
            + str(self.azi)
            + ", "
            + str(self.pnt_d)
            + ", "
            + str(self.pnt_r)
            + ", "
            + str(self.length())
            + ", "
            + str(self.radio)
            + ", "
            + str(self.leng_rest)
            + ", "
            + str(self.pnt_p)
            + ", "
            + self.inout
            + ")"
        )

    def param(self):
        """Return a string with the parameter A of the clothoid"""
        return "A=" + str(self.a_clot)

    def length(self):
        """Return length of the clothoid"""
        if self.a_clot <= 0:
            return 0
        elif self.other_local:
            return self.other_local["leng"] - self.leng_rest
        else:
            return self.local["leng"]

    def get_roadpnts(self, start, end, interv):
        """Return list of points of the curve, and set length of last point
        to the end and accumulated length
        ::
        >>> r_pnt = RoadPoint(Point(50,50,0), 0, 0, 0)
        >>> cloth = Clothoid(20, 40, 0, 'in', None, r_pnt)
        >>> cloth.get_roadpnts(0, -1, 1) # doctest: +ELLIPSIS \
                                                      +NORMALIZE_WHITESPACE
        [RoadPoint(10.0, 40.0000001, 0.0, 0,
        ...
        """
        if end == -1:
            end = self.length()

        if self.inout == "in":
            return self._get_pts_clot_in(start, end, interv)
        elif self.inout == "out":
            return self._get_pts_clot_out(start, end, interv)

    def _get_pts_clot_in(self, start, end, interv):
        """Return list of axis points of clothoid in, and set the rest to
        the end of the clothoid and accum length
        """
        accum = self.pts_accum
        list_pts = []
        while start <= end:
            if start == 0:
                start = 0.0000001
            rad_clo = self.a_clot**2 / start
            tau_clo = start / (2 * rad_clo)
            x_o, y_o = aprox_coord(start, tau_clo)
            x_1, y_1 = self.cloth_global(x_o, y_o)
            azi1 = self.pnt_azimuth(tau_clo)
            list_pts.append(
                RoadPoint(Point(x_1, y_1, 0), accum, round(azi1, 6), "Clot_in")
            )
            accum += interv
            start = start + interv

        self.pts_rest = end - (start - interv)
        self.pts_accum = accum - interv
        return list_pts

    def _get_pts_clot_out(self, start, end, interv):
        """Return list of axis points of clothoid out, and set the rest to
        the end of the clothoid and accum length
        """
        accum = self.pts_accum
        list_pts = []
        start2 = self.length() - end
        end2 = self.length() - start

        while start2 <= end2:
            if end2 == 0:
                end2 = 0.0000001

            rad_clo = self.a_clot**2 / end2
            tau_clo = end2 / (2 * rad_clo)
            x_o, y_o = aprox_coord((end2), tau_clo)
            x_1, y_1 = self.cloth_global(x_o, y_o)
            azi1 = self.pnt_azimuth(tau_clo)
            list_pts.append(
                RoadPoint(Point(x_1, y_1, 0), accum, round(azi1, 6), "Clot_out")
            )
            accum += interv
            end2 = end2 - interv

        self.pts_rest = start2 + (end2 + interv)
        self.pts_accum = accum - interv

        return list_pts

    def _pnt_ar(self):
        """Return the first point of the clothoid in"""
        return self.p_center.project(
            abs(self.radio), self.azi - self.g90 + self.local["tau"]
        )

    def _pnt_ad(self):
        """Return the last point of the clothoid in"""
        pnt_t1 = self.p_center.project(
            abs(self.radio + self.local["y_o"]), self.azi - self.g90
        )

        return pnt_t1.project(self.local["x_o"], self.azi + math.pi)

    def _pnt_ra(self):
        """Return the first point of the clothoid out"""
        return self.p_center.project(
            abs(self.radio), self.azi - self.g90 - self.local["tau"]
        )

    def _pnt_da(self):
        """Return the last point of the clothoid out"""
        pnt_t1 = self.p_center.project(
            abs(self.radio + self.local["y_o"]), self.azi - self.g90
        )
        return pnt_t1.project(self.local["x_o"], self.azi)

    def _pnt_adp(self):
        """Return"""
        if self.radio > 0:
            xadp = (
                self.pnt_d.x
                - self.other_local["x_e"] * math.sin(-self.azi)
                + self.local["y_e"] * math.cos(-self.azi)
            )
            yadp = (
                self.pnt_d.y
                + self.other_local["x_e"] * math.cos(-self.azi)
                + self.local["y_e"] * math.sin(-self.azi)
            )

        elif self.radio < 0:
            xadp = (
                self.pnt_d.x
                + self.other_local["x_e"] * math.sin(-self.azi)
                - self.local["y_e"] * math.cos(-self.azi)
            )
            yadp = (
                self.pnt_d.y
                + self.other_local["x_e"] * math.cos(-self.azi)
                + self.local["y_e"] * math.sin(-self.azi)
            )
        return Point(xadp, yadp)

    def _pnt_dap(self):
        """Return"""
        if self.radio > 0:
            xdap = (
                self.pnt_d.x
                - self.other_local["x_e"] * math.sin(-self.azi)
                + self.local["y_e"] * math.cos(-self.azi)
            )
            ydap = (
                self.pnt_d.y
                - self.other_local["x_e"] * math.cos(-self.azi)
                - self.local["y_e"] * math.sin(-self.azi)
            )

        elif self.radio < 0:
            xdap = (
                self.pnt_d.x
                + self.other_local["x_e"] * math.sin(-self.azi)
                - self.local["y_e"] * math.cos(-self.azi)
            )
            ydap = (
                self.pnt_d.y
                - self.other_local["x_e"] * math.cos(-self.azi)
                - self.local["y_e"] * math.sin(-self.azi)
            )
        return Point(xdap, ydap)

    def pnt_azimuth(self, tau_clo):
        """Return azimuth of a point of the clothoid, given the angle tau"""
        if self.inout == "in":
            if self.radio > 0:
                azi1 = self.azi + tau_clo
            elif self.radio < 0:
                azi1 = self.azi - tau_clo
        elif self.inout == "out":
            if self.radio > 0:
                azi1 = self.azi - tau_clo
            elif self.radio < 0:
                azi1 = self.azi + tau_clo
        return azi1

    def cloth_global(self, x_local, y_local):
        """Return local coordinates in global coordinates"""
        if self.inout == "in":
            if self.radio > 0:
                x_1 = (
                    self.pnt_d.x
                    - x_local * math.sin(-self.azi)
                    + y_local * math.cos(-self.azi)
                )
                y_1 = (
                    self.pnt_d.y
                    + x_local * math.cos(-self.azi)
                    + y_local * math.sin(-self.azi)
                )
            elif self.radio < 0:
                x_1 = (
                    self.pnt_d.x
                    + x_local * math.sin(self.azi)
                    - y_local * math.cos(self.azi)
                )
                y_1 = (
                    self.pnt_d.y
                    + x_local * math.cos(self.azi)
                    + y_local * math.sin(self.azi)
                )
        elif self.inout == "out":
            if self.radio > 0:
                x_1 = (
                    self.pnt_d.x
                    - x_local * math.sin(self.azi)
                    + y_local * math.cos(self.azi)
                )
                y_1 = (
                    self.pnt_d.y
                    - x_local * math.cos(self.azi)
                    - y_local * math.sin(self.azi)
                )
            elif self.radio < 0:
                x_1 = (
                    self.pnt_d.x
                    + x_local * math.sin(-self.azi)
                    - y_local * math.cos(-self.azi)
                )
                y_1 = (
                    self.pnt_d.y
                    - x_local * math.cos(-self.azi)
                    - y_local * math.sin(-self.azi)
                )
        return x_1, y_1

    def funct(self, leng, recta2):
        """Funtion for use with bisecc"""
        rad_i = self.a_clot**2 / leng
        tau_i = leng / (2 * rad_i)
        x_o, y_o = aprox_coord(leng, tau_i)
        x_1, y_1 = self.cloth_global(x_o, y_o)

        eq1 = y_1 - (
            recta2.pstart.y - math.tan((recta2.azimuth())) * (x_1 - recta2.pstart.x)
        )
        return [eq1, x_1, y_1]

    def find_cutoff(self, r_pnt):
        """Return the cutoff between this clothoid and straight, given by r_pnt
        with its azimuth.
        """
        r_pnt_d = bisecc(r_pnt, self)
        if r_pnt_d is not None:
            if self.inout == "out":
                r_pnt_d.npk = self.length() - r_pnt_d.npk
            r_pnt_d.p_type = "Cloth_" + self.inout
        #            r_pnt_d.dist_displ = r_pnt.distance(r_pnt_d)
        return r_pnt_d


if __name__ == "__main__":
    import doctest

    doctest.testmod()
