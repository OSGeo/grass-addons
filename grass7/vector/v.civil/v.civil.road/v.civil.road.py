#!/usr/bin/env python
# -*- coding: utf-8
############################################################################
#
# MODULE:       v.civil.road, v0.6.0
#
# AUTHOR:       Jesús Fernández-Capel Rosillo
#               Civil Engineer, Spain
#               jfc at alcd net
#
# PURPOSE:      Desing roads, channels, ports...
#
# COPYRIGHT:    (c) 2014 Jesús Fernández-Capel Rosillo.
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Generate a alignment for desing roads, channels, ports...
#% keywords: vector, ROADS, CHANNELS, PORTS.
#%End

#### Required section ####


#%option G_OPT_V_INPUT
#% key: edge
#% type: string
#% gisprompt: old,vector,vector
#% description: Name for alignment (horizontal polygon)
#% required: yes
#%end


#### Plant section ####

#%flag
#% key: y
#% description: Write central axis polyline
#% guisection: Plan
#%end

#%flag
#% key: h
#% description: Write horizontal alignment
#% guisection: Plan
#%end

#%option G_OPT_V_OUTPUT
#% key: plantpoly
#% description: Name for output central axis polyline
#% required: no
#% answer: _Poly
#% guisection: Plan
#%end

#%option G_OPT_V_OUTPUT
#% key: plant
#% description: Name for output horizontal alignment
#% required: no
#% answer: _Plant
#% guisection: Plan
#%end

####

#%flag
#% key: k
#% description: Write Pks marks
#% guisection: Plan
#%end

##%option
##% key: numpk
##% type: integer
##% description: Specific pk to draw
##% required: no
##% answer: 0
##% guisection: Plan
##%end

#%option
#% key: pkopt
#% type: string
#% description:  Pks marks options values. (npk,mpk,dist,m)
#% required: no
#% answer: 20,100,2,1
#% guisection: Plan
#%end

#%option G_OPT_V_OUTPUT
#% key: pks
#% description: Name of Pks marks
#% required: no
#% answer: _Pks
#% guisection: Plan
#%end

####

#%flag
#% key: d
#% description: Write plataform displaced lines
#% guisection: Plan
#%end

#%flag
#% key: a
#% description: Write plataform areas
#% guisection: Plan
#%end

#%option
#% key: areaopt
#% type: string
#% description:  Pair of displaced lines (1-2,2-5,5-6)
#% required: no
#% guisection: Plan
#%end

#%option G_OPT_V_OUTPUT
#% key: displ
#% description: Name of plataform displaced lines
#% required: no
#% answer: _Displ
#% guisection: Plan
#%end

#%option G_OPT_V_OUTPUT
#% key: displ_area
#% description: Name of plataform areas
#% required: no
#% answer: _Displ_Area
#% guisection: Plan
#%end

####

#%flag
#% key: m
#% description: Write marks
#% guisection: Plan
#%end

#%option G_OPT_V_OUTPUT
#% key: marksmap
#% description: Name of marks maps
#% required: no
#% answer: _Mark
#% guisection: Plan
#%end


#### Alz section ####

#%flag
#% key: v
#% description: Write vertical alignment in horizontal
#% guisection: Vertical
#%end

#%flag
#% key: l
#% description: Draw longitudinal profile (dem required)
#% guisection: Vertical
#%end

#%flag
#% key: j
#% description: Draw longitudinal profile coord axis (dem required)
#% guisection: Vertical
#%end

#%option
#% key: lpscale
#% type: integer
#% description: Long profile vertical scale (V/H, V/1)
#% options: 0-100
#% answer : 4
#% required: no
#% guisection: Vertical
#%end

#%option
#% key: lpopt
#% type: string
#% description: Long profile values of Longmark,distMark_x,distMark_y,DistGitarr.
#% required: no
#% answer: 2,20,1,20
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: raised
#% description: Name of vertical alignment
#% required: no
#% answer: _Vert
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpaxisx
#% description: Name of long profile axis x
#% required: no
#% answer: _LP_AxisX
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpaxisxmarks
#% description: Name of long profile axis x marks
#% required: no
#% answer: _LP_AxisXmarks
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpaxisy
#% description: Name of long profile axis y
#% required: no
#% answer: _LP_AxisY
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpaxisymarks
#% description: Name of long profile axis y marks
#% required: no
#% answer: _LP_AxisYmarks
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpterrain
#% description: Name of long profile terrain
#% required: no
#% answer: _LP_Terr
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpras
#% description: Name of long profile vertical alignment
#% required: no
#% answer: _LP_Ras
#% guisection: Vertical
#%end

#%option G_OPT_V_OUTPUT
#% key: lpejeref
#% description: Name of long profile vertical polygon
#% required: no
#% answer: _LP_Polygon
#% guisection: Vertical
#%end

#### Section section ####



#### Cross section ####

#%flag
#% key: c
#% description: Write transversals lines
#% guisection: Cross
#%end

#%flag
#% key: r
#% description: Write cutoff transversals lines with displaced lines
#% guisection: Cross
#%end



#%flag
#% key: f
#% description: Draw cross section (dem required)
#% guisection: Cross
#%end

#%flag
#% key: g
#% description: Draw cross section coord axis (dem required)
#% guisection: Cross
#%end



#%option
#% key: ltscale
#% type: double
#% description: Cross section vertical scale (V/H, V/1)
#% required: no
#% answer: 2
#% guisection: Cross
#%end

#%option
#% key: ltopt
#% type: string
#% description: Cross section options values for Longmark,distMark_x,distMark_y.
#% required: no
#% answer: 1,20,10
#% guisection: Cross
#%end

#%option
#% key: ltopt2
#% type: string
#% description: Cross section options values for nrows,distTP_x,distTP_y.
#% required: no
#% answer: 10,10,10
#% guisection: Cross
#%end

##%option G_OPT_V_TYPE
##% key: cross_opt
##% options: slope_left,displ_left,edge,displ_rigth,slope_rigth
##% answer: slope_left,displ_left,edge,displ_rigth,slope_rigth
##% required: no
##% description: Add lines to the cross section
##% guisection: Cross
##%end

#%option G_OPT_V_TYPE
#% key: displ_opt
#% options: displ_left0,displ_left,displ_left-1,displ_rigth0,displ_rigth,displ_rigth-1
#% required: no
#% answer: displ_left0,displ_left-1,displ_rigth0,displ_rigth-1
#% description: Cross points section-Displaced
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: cross
#% description: Name of cross section
#% required: no
#% answer: _Cross
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: crossdispl
#% description: Name of intersection cross section - displaced
#% required: no
#% answer: _CrossDispl
#% guisection: Cross
#%end



#%option G_OPT_V_OUTPUT
#% key: ltaxisx
#% description: Name of cross section coord axis x
#% required: no
#% answer: _TP_AxisX
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: ltaxisxmarks
#% description: Name of cross section coord axis x
#% required: no
#% answer: _TP_AxisXmarks
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: ltaxisy
#% description: Name of cross section coord axis y
#% required: no
#% answer: _TP_AxisY
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: ltaxisymarks
#% description: Name of cross section coord axis y
#% required: no
#% answer: _TP_AxisYmarks
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: ltterrain
#% description: Name of cross sections terrain
#% required: no
#% answer: _TP_Terr
#% guisection: Cross
#%end

#%option G_OPT_V_OUTPUT
#% key: ltras
#% description: Name of cross section plataform
#% required: no
#% answer: _TP_Ras
#% guisection: Cross
#%end


#### Terrain section ####

#%flag
#% key: t
#% description: Write central axis vertical proyection in dem
#% guisection: Terr
#%end

#%flag
#% key: q
#% description: Write terrain cross section
#% guisection: Terr
#%end

#%flag
#% key: s
#% description: Write slope soil
#% guisection: Terr
#%end

#%flag
#% key: e
#% description: Write slope soil areas
#% guisection: Terr
#%end

#%flag
#% key: p
#% description: Write points
#% guisection: Terr
#%end

#%flag
#% key: b
#% description: Write breaklines
#% guisection: Terr
#%end

#%flag
#% key: o
#% description: Write hull
#% guisection: Terr
#%end

#%option G_OPT_V_TYPE
#% key: pts_opt
#% options: slope_left,displ_left,edge,displ_rigth,slope_rigth
#% answer: slope_left,displ_left,edge,displ_rigth,slope_rigth
#% required: no
#% description: Points
#% guisection: Terr
#%end

#%option G_OPT_V_TYPE
#% key: break_opt
#% options: slope_left,displ_left,edge,displ_rigth,slope_rigth
#% answer: slope_left,displ_left,edge,displ_rigth,slope_rigth
#% required: no
#% description: Breaklines
#% guisection: Terr
#%end

#%option
#% key: disptin
#% type: string
#% description:  Cats of displaced to tin (default: all)
#% required: no
#% guisection: Terr
#%end


#%option G_OPT_V_TYPE
#% key: hull_opt
#% options: slope_left,slope_rigth
#% answer: slope_left,slope_rigth
#% required: no
#% description: Hull
#% guisection: Terr
#%end

#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: raster dem
#% description: Name of DEM raster
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outtlong
#% description: Name of terrain central axis vertical proyection
#% required: no
#% answer: _LongTerr
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outtcross
#% description: Name of terrain cross section
#% required: no
#% answer: _CrossTerr
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outslope
#% description: Name of slope soil
#% required: no
#% answer: _Slope
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outslopeareas
#% description: Name of slope soil areas
#% required: no
#% answer: _SlopeAreas
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outpoints
#% description: Name of points
#% required: no
#% answer: _Points
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outbreak
#% description: Name of breaklines
#% required: no
#% answer: _Breaklines
#% guisection: Terr
#%end

#%option G_OPT_V_OUTPUT
#% key: outhull
#% description: Name of hull
#% required: no
#% answer: _Hull
#% guisection: Terr
#%end


#### Options section ####

#%flag
#% key: n
#% description: Create/Update polygon
#%end

#%flag
#% key: u
#% description: Update solution
#%end

#%flag
#% key: i
#% description: Insert point in polygon layers (vertical, section an transversal)
#%end


#%option
#% key: pklayer
#% type: string
#% label: Layer to add Pks points
#% options: Vertical,Section,Trans,Marks
#% required: no
#%end

#%option
#% key: pklist
#% type: string
#% description: List of Pks points.
#% required: no
#%end

#%option
#% key: intervr
#% type: integer
#% description: Interval in straights
#% required: no
#% answer: 1
#%end

#%option
#% key: intervc
#% type: integer
#% description: Interval in curves
#% required: no
#% answer: 1
#%end



import os
import sys

from math import *
import grass.script as g
from grass.lib.gis    import *
from grass.lib.vector import *
from grass.lib.raster import *
#import numpy as np
#from grass.pygrass.raster import RasterNumpy
#from grass.pygrass.vector import VectorTopo
#from grass.pygrass.vector.geometry import Point
#from grass.pygrass.functions import pixel2coor
#import grass.pygrass.raster as raster
#import grass.pygrass.gis as gis
#from grass.pygrass.gis.region import Region
#from grass.script import array as garray
from itertools import groupby
#import time
from copy import deepcopy
#import Gnuplot
#import coverage
#cov = coverage.coverage(omit="*testsuite*")
#cov.start()

#def endcov(cov):
    #cov.stop()
    #cov.html_report(directory='testcodecoverage')

#import atexit
#atexit.register(endcov, cov)
#### Alineaciones

def aprox_coord(leng, tau):
    """Return coord (x1,y1) of a clothoid given the angle Tau and length

        >>> aprox_coord(10, 5)
        [-50, -50]
    """
    n_iter = 10
    x = 0
    y = 0
    for n in range(n_iter):
        x += (((-1)**n*tau**(2*n)) / ((4*n+1)*factorial(2*n)))
        y += (((-1)**n*tau**(2*n+1)) / ((4*n+3)*factorial(2*n+1)))
    x = x*leng
    y = y*leng
    return [x, y]


def aprox_coord2(radio, tau):
    """Return coord (x1,y1) of a clothoid given the angle Tau and Radio

        >>> aprox_coord(100, 50)
        [-1411567899002100L, -3476091295999800L]
    """
    n_iter = 10
    x = 0
    y = 0
    for n in range(n_iter):
        x += (((-1)**n*(2*tau**(2*n+1)/((4*n+1)*factorial(2*n)))) - \
              ((-1)**n*(tau**(2*n+1)/factorial(2*n+1))))
        y += (((-1)**n*(2*tau**(2*n+2)/((4*n+3)*factorial(2*n+1)))) + \
              ((-1)**n*(tau**(2*n)/factorial(2*n))))
    x = x*radio
    y = y*radio - radio
    return [x, y]


def azimut(x1, y1, x2, y2):
    """Return Azimut of two point (x1,y1) (x2,y2), Rad from North 
       to clockwise

        >>> azimut(638345.45551981, 220254.08548594, 638822.59583299, 220245.60700623)
        1.5885638205154133
    """
    if x1 > x2 and y1 == y2:
        az = 3*pi / 2
    elif x1 < x2 and y1 == y2:
        az = pi/2
    elif x1 == x2 and y1 > y2:
        az = pi
    elif x1 == x2 and y1 < y2:
        az = 2*pi
    elif x1 == x2 and y1 == y2:
        az = 0
    else:
        az = atan((x2-x1)/(y2-y1))
        #if x1> x2 and y1 == y2: az = az + pi # az>0 -> az > 0
        if x1 < x2 and y1 > y2:
            az = az + pi # az<0 -> az > 100
        elif x1 > x2 and y1 > y2:
            az = az + pi # az>0 -> az > 200
        elif x1 > x2 and y1 < y2:
            az = az + 2*pi # az<0 -> az > 300
    return az


def format_pk(pk):
    """Return the pk format 1+000.001

        >>> format_pk(10000.001)
        "'10+000.001'"
    """
    if str(pk).find(".") == -1:
        integer = str(pk)
        decimal = "0"
    else:
        integer, decimal = str(pk).split(".")
    integer = re.sub(r"\B(?=(?:\d{3})+$)", "+", "{:0>4}".format(integer))
    return "'" + integer + "." + decimal + "'"


def clotoide_Locales(A, R):
    """Return clothoid parameters in local coord

        >>> clotoide_Locales(40,80)
        (20.0, 0.0, 0, 20, 20, 0)
    """
    if R == 0:
        Leng,Tau = 0,0
    else:
        Leng = A**2 / abs(R)
        Tau = Leng / (2*R)
    xe, ye = aprox_coord(Leng,Tau)
    xo = xe - R*sin(Tau)
    yo = ye + R*cos(Tau) - R
    return xo, yo, Tau, Leng, xe, ye


def angulos_Alings(x1, y1, x2, y2, x3, y3):
    """Return angle between two straights and their azimuth
    given by three points e

        >>> angulos_Alings(638345.45551981, 220254.08548594, 638822.59583299, 220245.60700623, 638865.61614048, 220252.80207533)
        (1.5885638205154133, 1.4050818841165356, 0.18348193639887778)
    """
    Az_ent = azimut(x1,y1,x2,y2)
    Az_sal = azimut(x2,y2,x3,y3)

    if ((x1 <= x2 and y1 <= y2) or (x1 <= x2 and y1 >= y2)):
        #print "1er o 2do cuadrante"
        if (Az_ent < Az_sal and Az_ent+pi < Az_sal):
            w = 2*pi-abs(Az_ent-Az_sal)
        else:
            w = abs(Az_ent-Az_sal)

    if ((x1 >= x2 and y1 >= y2) or (x1 >= x2 and y1 <= y2)):
        #print "3er o 4to cuadrante"
        if (Az_ent > Az_sal and Az_ent-pi > Az_sal):
            w = 2*pi-abs(Az_ent-Az_sal)
        else:
            w = abs(Az_ent-Az_sal)
    #print Az_ent*200/pi,Az_sal*200/pi,w
    return Az_ent, Az_sal, w


def pto_corte_2_rectas(x1, y1, x2, y2, x3, y3, x4, y4):
    """ Return crossover,
    given by four points

    pto_corte_2_rectas()

    """
    if x1 == x2:
        m2 = (y4-y3) / (x4-x3)
        x = x1
        y = y3 + m2 * (x1-x3)
    elif x3 == x4:
        m1 = (y2-y1) / (x2-x1)
        x = x3
        y = y1 + m1 * (x3-x1)
    else:
        m1 = (y2-y1) / (x2-x1)
        m2 = (y4-y3) / (x4-x3)
        x = (m1*x1-m2*x3-y1+y3) / (m1-m2)
        y = m1*(x-x1)+y1
    return x, y



def get_pts_Clot_ent(A, xad, yad, Az, Ini, Fin, L_int, R, Lacum, cat, ali):
    """ Return list of axis points of clothoid in,
    length of last point to the end, accum length,
    and last cat of points

    """
    M = []
    while Ini <= Fin:
        Rclo = A**2/Ini
        Tau_clo = Ini / (2*Rclo)
        xclo, yclo = aprox_coord((Ini),Tau_clo)
        if R > 0:
            x_clo = xad - xclo*sin(-Az) + yclo*cos(-Az)
            y_clo = yad + xclo*cos(-Az) + yclo*sin(-Az)
            Az1 = Az + Tau_clo
        elif R < 0:
            x_clo = xad + xclo*sin(Az) - yclo*cos(Az)
            y_clo = yad + xclo*cos(Az) + yclo*sin(Az)
            Az1 = Az - Tau_clo
        Lacum += L_int
        M.append([x_clo,y_clo,0,cat,Lacum,Az1,'Clot_in',ali])
        cat = cat + 1
        Ini = Ini + L_int
    return M, Fin-(Ini-L_int), Lacum, cat


def get_pts_Clot_sal(A, xda, yda, Az, Ini, Fin, L_int, R, Lacum, cat, ali):
    """ Return list of axis points of clothoid out,
    length of last point to the end, accum length,
    and last cat of points

    """
    M = []
    while Ini <= Fin:
        #if Fin-Ini == 0: Fin=0; Ini=Ini*-1
        Rclo = A**2 / Fin
        Tau_clo = Fin / (2*Rclo)
        xclo, yclo = aprox_coord((Fin),Tau_clo)
        if R > 0:
            x_clo = xda - xclo*sin(Az) + yclo*cos(Az)
            y_clo = yda - xclo*cos(Az) - yclo*sin(Az)
            Az1 = Az - Tau_clo
        elif R < 0:
            x_clo = xda + xclo*sin(-Az) - yclo*cos(-Az)
            y_clo = yda - xclo*cos(-Az) - yclo*sin(-Az)
            Az1 = Az + Tau_clo
        Lacum += L_int
        M.append([x_clo,y_clo,0,cat,Lacum,Az1,'Clot_out',ali])
        cat = cat + 1
        Fin = Fin - L_int
        #Ini=Ini+L_int
    #print M,Ini-(Fin+L_int),Lacum,cat,Ini,Fin,L_int
    return M, Ini+(Fin+L_int), Lacum, cat

def get_pts_Curva(xc, yc, AzIni, AzFin, incremento, R, Lacum, dc, cat, ali):
    """ Return list of axis points of the curve,
    length of last point to the end, accum length,
    and last cat of points

    """
    M = []
    incremento = incremento/abs(R)
    if R > 0:
        if AzIni>AzFin:
            AzIni=AzIni-2*pi
        ii = AzIni+incremento
        while ii <= AzFin:
            x1 = xc + R*sin(ii)
            y1 = yc + R*cos(ii)
            Az1 = (ii+pi/2)
            ii += incremento
            Lacum += incremento*abs(R)
            if Az1 > 2*pi:
                Az1 = Az1 - 2*pi
            M.append([x1,y1,0,cat,Lacum,Az1,'Curve',ali])
            cat = cat+1
        resto = (AzFin-(ii-incremento))*abs(R)
    elif R < 0:
        if AzIni<AzFin:
            AzFin=AzFin-2*pi
        ii = AzIni-incremento
        while ii >= AzFin:
            x1 = xc - R*sin(ii)
            y1 = yc - R*cos(ii)
            Az1 = (ii-pi/2)
            ii -= incremento
            Lacum += incremento*abs(R)
            if Az1 < 0:
                Az1 = Az1 + 2*pi
            M.append([x1,y1,0,cat,Lacum,Az1,'Curve',ali])
            cat = cat + 1
        resto = ((ii+incremento)-AzFin)*abs(R)
    #print M,resto,Lacum,cat
    return M, resto, Lacum, cat


def get_pts_Recta(xo, yo, zo, Az, ini, Fin, L_int, Lacum, cat, ali):
    """ Return list of axis points of a straight,
    length of last point to the end, accum length,
    and last cat of points

    Points from NC road St1
    For one point, ini=Fin
        >>> get_pts_Recta(638345.45552,220254.085486,0,1.58856382113,10,10,1,9,1,0)
        ([[638355.4539416222, 220253.90782040468, 0, 1, 10, 1.58856382113, 'Line', 0]], 0, 10, 2)

    For some points
        >>> get_pts_Recta(638345.45552,220254.085486,0,1.58856382113,10,14,1,9,1,0)
        ([[638355.4539416222, 220253.90782040468, 0, 1, 10, 1.58856382113, 'Line', 0], \
[638356.4537837844, 220253.89005384516, 0, 2, 11, 1.58856382113, 'Line', 0], \
[638357.4536259467, 220253.87228728563, 0, 3, 12, 1.58856382113, 'Line', 0], \
[638358.4534681089, 220253.85452072608, 0, 4, 13, 1.58856382113, 'Line', 0], \
[638359.4533102711, 220253.83675416655, 0, 5, 14, 1.58856382113, 'Line', 0]], 0, 14, 6)
    """
    if L_int == 0: L_int=1
    M = []
    while  ini <= Fin:
        x2 = xo + ini*sin(Az)
        y2 = yo + ini*cos(Az)
        Lacum += L_int
        M.append([x2, y2, zo, cat, Lacum, Az, 'Line', ali])
        cat = cat + 1
        ini += L_int
    return M, Fin-(ini-L_int), Lacum, cat


def get_PlantaXY(PK, puntos_eje):
    """Return list with one point with the coord
    RoadPoint[x,y,z,cat,pk,azimuth,type,align]
    puntos_eje: list of aligns

    Aligns from NC road St1
        >>> table_plant = read_TablePlant('St1')
        >>> Puntos_Eje = get_PtosEjePlanta(table_plant)
        >>> get_PlantaXY(10,Puntos_Eje)
        [638355.4539416222, 220253.90782040468, 0, 1, 10, 1.58856382112969, 'Line', 0]
    """
    acum = 0
    for i in range(0, len(puntos_eje)-1, 1):

        x_ini,y_ini,z_ini,Lrecta,LrAcum,Az_ent = puntos_eje[i][0]
        Aent,Az_ent,xad,yad,xar,yar,Lent,LeAcum,R,Lini_e,xadp,yadp = puntos_eje[i][1]
        R,alpha,xc,yc,Az_ini,Az_fin,Dc,LcAcum = puntos_eje[i][2]
        Asal,Az_sal,xda,yda,xra,yra,Lsal,LsAcum,R,Lini_s,xdap,ydap = puntos_eje[i][3]
        M=[[0,0]]

        if 0 <= PK and PK <= LrAcum:

            M,rest,acum,cat = get_pts_Recta(x_ini,y_ini,z_ini,Az_ent,PK-acum,
                                            PK-acum,1,PK-1,1,i)
            break

        elif LrAcum < PK and PK <= LeAcum:
            M,rest,acum,cat = get_pts_Clot_ent(Aent,xad,yad,Az_ent,PK-LrAcum,
                                               PK-LrAcum,1,R,PK-1,1,i)
            break

        elif LeAcum < PK and PK <= LcAcum:
            a = Az_ini + (PK-LeAcum)/R
            M,rest,acum,cat = get_pts_Curva(xc,yc,a-1/R,a,1,R,PK-1,Dc,1,i)
            break

        elif LcAcum < PK and PK <= LsAcum:
            if LsAcum-PK == 0: distcond = PK
            else: distcond = LsAcum-PK
            M,rest,acum,cat = get_pts_Clot_sal(Asal,xda,yda,Az_sal,distcond,
                                               distcond,1,R,PK-1,1,i)
            break

        acum=LsAcum

    if PK > LsAcum:
        M,rest,acum,cat = get_pts_Recta(xda,yda,z_ini,Az_sal,PK-LsAcum,
                                        PK-LsAcum,1,PK-1,1,i)

    return M[0]


#### ############## Planta #### ##################

def get_PtosEjePlanta(table_plant):
    """Return list of aligns
    RoadAlign=[[x_ini,y_ini,0,Lrecta,Lacum,Az_ent],
               [Ae,Az_ent,xad,yad,xar,yar,Le,Lacum,R,Lini_e,xadp,yadp],
               [R,alpha,xc,yc,Az_ini,Az_fin,Dc,Lacum],
               [As,Az_sal,xda,yda,xra,yra,Ls,Lacum,R,Lini_s,xdap,ydap]]
    Table from NC road St1

        >>> table_plant = read_TablePlant('St1')
        >>> get_PtosEjePlanta(table_plant)
        [[[638345.45552, 220254.085486, 0, 469.85569852394906, 469.85569852394906, 1.58856382112969], \
[0.0, 1.58856382112969, 638815.2370575458, 220245.7377667612, 638815.2370575458, 220245.7377667612, 0, 469.85569852394906, -80.0, 0, 638815.2370575458, 220245.7377667612], \
[-80.0, 0.1834819366056495, 638816.6583823083, 220325.72513973917, 3.1593601479250033, 2.9758782113185123, 14.678554928451959, 484.534253452401], \
[0.0, 1.4050818845240405, 638829.8549445468, 220246.82107935514, 638829.8549445468, 220246.82107935514, 0, 484.534253452401, -80.0, 0, 638829.8549445468, 220246.82107935514]], \
[[638829.8549445468, 220246.82107935514, 0, 36.257901334031104, 520.7921547864321, 1.4050818845240405], \
[0, 1.4050818845240405, 638829.8549445468, 220246.82107935514, 0, 0, 0, 520.7921547864321, 0, 0, 638815.2370575458, 220245.7377667612], \
[0, 0, 0, 0, 0, 0, 0, 520.7921547864321], \
[0, 1.4050818845240405, 638829.8549445468, 220246.82107935514, 0, 0, 0, 520.7921547864321, 0, 0, 638829.8549445468, 220246.82107935514]]]
    """
    LAcum = 0
    x_ini,y_ini = table_plant[0][0],table_plant[0][1]
    puntos_eje = []
    #centros = []
    for i in range(1,len(table_plant)-1,1):

        a, b = table_plant[i-1][0], table_plant[i-1][1]
        c, d = table_plant[i][0], table_plant[i][1]
        e, f = table_plant[i+1][0], table_plant[i+1][1]

        Az_ent, Az_sal, w = angulos_Alings(a, b, c, d, e, f)

        R,Ae,As = table_plant[i][5],table_plant[i][6],table_plant[i][7]

        if R == 0:
            Lrecta = sqrt((c-x_ini)**2+(d-y_ini)**2)
            LAcum += Lrecta
            Lini_e,Lini_s=0,0
            xadp,yadp = c,d
            xdap,ydap = c,d
            puntos_eje.append([[x_ini,y_ini,0,Lrecta,LAcum,Az_ent],
                               [0,Az_ent,c,d,c,d,0,LAcum,0,Lini_e,xadp,yadp],
                               [0,0,0,0,0,0,0,LAcum],
                               [0,Az_sal,c,d,c,d,0,LAcum,0,Lini_s,xdap,ydap]])
            x_ini,y_ini=c,d
            continue

        xo_e,yo_e,Tau_e,Le,xe,ye=clotoide_Locales(Ae,R)
        xo_s,yo_s,Tau_s,Ls,xs,ys=clotoide_Locales(As,R)

        # Centros de las curvas dados por el corte de las rectas paralelas a R+AR
        if R > 0:
            g90 = pi/2
            alpha = abs(w - Tau_e - Tau_s)
        else:
            g90 = -pi/2
            alpha = abs(w + Tau_e + Tau_s)

        ac = a + abs(R+yo_e) * sin(Az_ent+g90)
        bc = b + abs(R+yo_e) * cos(Az_ent+g90)

        cc1 = c + abs(R+yo_e)*sin(Az_ent+g90)
        dc1 = d + abs(R+yo_e)*cos(Az_ent+g90)

        cc2 = c + abs(R+yo_s)*sin(Az_sal+g90)
        dc2 = d + abs(R+yo_s)*cos(Az_sal+g90)

        ec = e + abs(R+yo_s)*sin(Az_sal+g90)
        fc = f + abs(R+yo_s)*cos(Az_sal+g90)

        xc,yc = pto_corte_2_rectas(ac,bc,cc1,dc1,cc2,dc2,ec,fc)
        #centros.append([xc,yc,0])

        Lini_e, Lini_s = 0, 0
        if Ae <= 0:
            xar = xc + abs(R)*sin(Az_ent-g90-Tau_e)
            yar = yc + abs(R)*cos(Az_ent-g90-Tau_e)
            xad,yad = xar,yar

            Lrecta = sqrt((xad-x_ini)**2+(yad-y_ini)**2)
            if Ae < 0:
                x_ini, y_ini = xad, yad
                Lrecta = 0
            Le = 0
            xadp, yadp = xad, yad

        else:
            xt1= xc + abs(R+yo_e)*sin(Az_ent-g90)
            yt1= yc + abs(R+yo_e)*cos(Az_ent-g90)

            xad = xt1 + xo_e*sin(Az_ent+pi)
            yad = yt1 + xo_e*cos(Az_ent+pi)

            xar = xc + abs(R)*sin(Az_ent-g90+Tau_e)
            yar = yc + abs(R)*cos(Az_ent-g90+Tau_e)

            Lrecta = sqrt((xad-x_ini)**2+(yad-y_ini)**2)
            R1,Ae1,As1 = table_plant[i-1][5],table_plant[i-1][6],table_plant[i-1][7]
            xadp, yadp = xad, yad
            if As1 < 0:
                xo_s1,yo_s1,Tau_s1,Ls1,xs1,ys1 = clotoide_Locales(As1,R1)
                Lini_e =  Ls1
                Ptos_ent,resto,acum,cat = get_pts_Clot_ent(Ae,xad,yad,Az_ent,Lini_e,Lini_e,1,R,0,0,0)
                xadp, yadp = Ptos_ent[0][0], Ptos_ent[0][1]
                x_ini, y_ini = xadp, yadp
                Lrecta = 0

        Dc = abs(R)*alpha

        if As <= 0:
            xra = xc + abs(R)*sin(Az_sal-g90+Tau_s)
            yra = yc + abs(R)*cos(Az_sal-g90+Tau_s)
            xda, yda = xra, yra
            Ls = 0
            xdap, ydap = xda, yda

        else:
            xt1 = xc + abs(R+yo_s)*sin(Az_sal-g90)
            yt1 = yc + abs(R+yo_s)*cos(Az_sal-g90)

            xda = xt1 + xo_s*sin(Az_sal)
            yda = yt1 + xo_s*cos(Az_sal)

            xra = xc + abs(R)*sin(Az_sal-g90-Tau_s)
            yra = yc + abs(R)*cos(Az_sal-g90-Tau_s)

            R2,Ae2,As2 = table_plant[i+1][5],table_plant[i+1][6],table_plant[i+1][7]
            xdap, ydap = xda, yda
            if Ae2 < 0:
                xo_e2,yo_e2,Tau_e2,Le2,xe2,ye2=clotoide_Locales(Ae2,R2)
                Lini_s = Le2
                Ptos_sal,resto,acum,cat_s=get_pts_Clot_sal(As,xda,yda,Az_sal,Lini_s,Lini_s,1,R,0,0,0)
                xdap, ydap = Ptos_sal[0][0], Ptos_sal[0][1]

        #Az_ini = Az_ent-g90+Tau_e
        #Az_fin = Az_sal-g90-Tau_s
        Az_ini = azimut(xc, yc, xar, yar)
        Az_fin = azimut(xc, yc, xra, yra)

        puntos_eje.append([[x_ini,y_ini,0,Lrecta,LAcum+Lrecta,Az_ent],
                           [Ae,Az_ent,xad,yad,xar,yar,(Le-Lini_e),LAcum+Lrecta+(Le-Lini_e),R,Lini_e,xadp,yadp],
                           [R,alpha,xc,yc,Az_ini,Az_fin,Dc,LAcum+Lrecta+(Le-Lini_e)+Dc],
                           [As,Az_sal,xda,yda,xra,yra,(Ls-Lini_s),LAcum+Lrecta+(Le-Lini_e)+Dc+(Ls-Lini_s),R,Lini_s,xdap,ydap]])

        x_ini,y_ini = xdap,ydap
        LAcum = LAcum + Lrecta + (Le-Lini_e) + Dc + (Ls-Lini_s)

    Lrecta = sqrt((e-x_ini)**2+(f-y_ini)**2)
    puntos_eje.append([[x_ini,y_ini,0,Lrecta,LAcum+Lrecta,Az_sal],
                      [0,Az_sal,x_ini,y_ini,0,0,0,LAcum+Lrecta,0,Lini_e,xadp,yadp],
                      [0,0,0,0,0,0,0,LAcum+Lrecta],
                      [0,Az_sal,x_ini,y_ini,0,0,0,LAcum+Lrecta,0,Lini_s,xdap,ydap]])
    #for jj in puntos_eje:
        #for pp in jj: print pp
        #print ''
    return puntos_eje


def generate_Pts(puntos_eje, a, b, c, interv, intervC):
    """ Return list of axis points of all align,
    a=1: return list of axis points
    b=1: return list of axis points of each align
    c=1: return list of characteristic points
    interv: distance between points in straights
    intervC: distance between points in curves

    Table from NC road St2
        >>> table_plant = read_TablePlant('St2')
        >>> Points_Axis = get_PtosEjePlanta(table_plant)
        >>> Points = generate_Pts(Points_Axis,1,1,1,1,1)
        >>> len(Points[0]),len(Points[1]),len(Points[2]),len(Points[3])
        (659, 17, 18, 5)
        >>> Points = generate_Pts(Points_Axis,1,1,1,10,5)
        >>> len(Points[0]),len(Points[1]),len(Points[2]),len(Points[3])
        (106, 17, 18, 5)
    """
    x_ini, y_ini, z_ini, Lrecta, LAcum, Az_ent = puntos_eje[0][0]

    resto = 0
    cat = 2
    puntos, seg, puntos_caract, puntos_centros = [], [], [], []
    if a == 1: puntos=[[x_ini,y_ini,z_ini,1,0,Az_ent,'Ini',0]]
    if b == 1: puntos_caract=[[x_ini,y_ini,z_ini,1,0,Az_ent,"'Ini'",0]]

    Ini=[[x_ini,y_ini,z_ini,cat,0,Az_ent,"'Ini'",0]]

    acum = 0
    h = 1
    for i in range(0,len(puntos_eje)-1,1):
        x_ini,y_ini,z_ini,Lrecta,LrAcum,Az_ent=puntos_eje[i][0]
        Aent,Az_ent,xad,yad,xar,yar,Lent,LeAcum,R,Lini_e,xadp,yadp=puntos_eje[i][1]
        R,alpha,xc,yc,Az_ini,Az_fin,Dc,LcAcum=puntos_eje[i][2]
        Asal,Az_sal,xda,yda,xra,yra,Lsal,LsAcum,R,Lini_s,xdap,ydap=puntos_eje[i][3]

        Ptos_recta,resto,acum,cat_r = get_pts_Recta(x_ini,y_ini,z_ini,Az_ent,interv-resto,Lrecta,interv,acum,cat,i)
        if R != 0:
            if Aent > 0:
                Ptos_ent,resto,acum,cat_e = get_pts_Clot_ent(Aent,xad,yad,Az_ent,interv-resto+Lini_e,Lent,intervC,R,acum,cat_r,i)
            else:
                Ptos_ent=[]
                cat_e=cat_r
            #print xc,yc,Az_ini-resto/R,Az_fin,interv,R,acum,Dc,cat_e,i
            Ptos_curva,resto,acum,cat_c = get_pts_Curva(xc,yc,Az_ini-resto/R,Az_fin,intervC,R,acum,Dc,cat_e,i)
            if Asal > 0:
                #print Asal,xda,yda,Az_sal,interv-resto+Lini_s,Lsal,interv,R,acum,cat_c,i
                Ptos_sal,resto,acum,cat_s = get_pts_Clot_sal(Asal,xda,yda,Az_sal,0,Lsal-(intervC-resto+Lini_s),intervC,R,acum,cat_c,i)
            else:
                if Lini_s != 0: xda,yda = xdap,ydap
                Ptos_sal = []
                cat_s = cat_c
        else:
            Ptos_ent,Ptos_curva,Ptos_sal = [[],[],[]]
            cat = cat_r
            cat_r,cat_e,cat_c,cat_s = 1,2,3,4

        if a == 1:
            puntos.extend(Ptos_recta+Ptos_ent+Ptos_curva+Ptos_sal)
        if c == 1:
            puntos_centros.append([[xc,yc,0,i,"'C'",i],[0,0,0,h,LrAcum,"'Line'",Lrecta,0,Az_ent*200/pi],
                               [0,0,0,h+1,LeAcum,"'Clot_in'",Lent-Lini_e,Aent,Az_ent*200/pi],
                               [0,0,0,h+2,LcAcum,"'Curve'",abs(Dc),R,Az_ini*200/pi],
                               [0,0,0,h+3,LsAcum,"'Clot_out'",Lsal-Lini_s,Asal,Az_sal*200/pi]])
        if b == 1:
            puntos_caract.extend([[xadp,yadp,0,h+1,LrAcum,Az_ent*200/pi,"'Te'",i],
                              [xar,yar,0,h+2,LeAcum,Az_ini*200/pi,"'Tec'",i],
                              [xra,yra,0,h+3,LcAcum,Az_fin*200/pi,"'Tsc'",i],
                              [xdap,ydap,0,h+4,LsAcum,Az_sal*200/pi,"'Ts'",i]])
        if c == 1:
            seg.append(Ini+Ptos_recta+[[xadp,yadp,0,cat_r,LrAcum,"'Te'",i]])
            seg.append([[xadp,yadp,0,cat_r,LrAcum,"'Te'",i]]+Ptos_ent+[[xar,yar,0,cat_e,LeAcum,"'Tec'",i]])
            seg.append([[xar,yar,0,cat_e,LeAcum,"'Tec'",i]]+Ptos_curva+[[xra,yra,0,cat_c,LcAcum,"'Tsc'",i]])
            seg.append([[xra,yra,0,cat_c,LcAcum,"'Tsc'",i]]+Ptos_sal+[[xdap,ydap,0,cat_s,LsAcum,"'Ts'",i]])
        Ini = [[xdap,ydap,0,cat_s,LsAcum,"'Ts'",i]]
        cat = cat_s
        h = h + 4
        ult = i + 1
    x_ini,y_ini,z_ini,Lrecta,LAcum,Az_sal = puntos_eje[-1][0]
    Ptos_recta,resto,acum,cat = get_pts_Recta(x_ini,y_ini,z_ini,Az_sal,interv-resto,Lrecta,interv,acum,cat_s,ult)
    x_fin,y_fin,z_fin = get_pts_Recta(x_ini,y_ini,z_ini,Az_sal,Lrecta,Lrecta,interv,acum,cat_s,i+1)[0][0][:3]

    if a == 1: puntos.extend(Ptos_recta)
    if a == 1: puntos.append([x_fin,y_fin,z_fin,cat,LAcum,Az_sal,'End',ult])
    if b == 1: puntos_caract.append([x_fin,y_fin,z_fin,h+1,LAcum,Az_sal,"'End'",ult])
    if c == 1: puntos_centros.append([[],[x_fin,y_fin,z_fin,h,LAcum,"'Line'",Lrecta,0,Az_sal*200/pi]])
    if c == 1: seg.append(Ini+Ptos_recta+[[x_fin,y_fin,z_fin,cat,LAcum,"'End'",ult]])

    #for jj in puntos_caract: print jj
    return puntos,seg,puntos_caract,puntos_centros


#### ############## Alzado #### ##################

def get_Cota(puntos, puntos_eje_alz):
    """Return list of axis points with the heigth defined

    Table from NC road St2
        >>> table_plant = read_TablePlant('St2')
        >>> Points_Axis = get_PtosEjePlanta(table_plant)
        >>> Points = generate_Pts(Points_Axis,1,0,0,1,1)
        >>> table_alz = read_TableAlz('St2')
        >>> Points_VertAxis = get_PtosEjeAlzado(table_alz)
        >>> PointsV = get_Cota(Points[0],Points_VertAxis)
        >>> len(PointsV)
        659
    """
    ins = len(puntos[0])
    i = 0
    for pto in puntos:

        pk = float(pto[4])
        for h,pkalz in enumerate(puntos_eje_alz):

            pk_ini,zini,pke,ze,pks,zs,pkv,zv,Kv,L,pe,ps = pkalz

            if Kv == 0 and pk_ini <= pk and pk <= pkv:
                cota = zini + pe*(pk-pk_ini)
                pend = type_Pend(pe)
                aling = h
                continue
            elif pk_ini <= pk and pk < pke:
                cota = zini+pe*(pk-pk_ini)
                pend = type_Pend(pe)
                aling = h
                continue
            elif pke <= pk and pk <= pkv:
                cota = ze + pe*(pk-pke)-(1/(2*Kv))*(pk-pke)**2
                pend = type_Acuerdo(pe,ps)
                aling = h
                continue
            elif pkv < pk and pk <= pks:
                #cota=ze+ps*(pk-pkv)-(1/(2*Kv))*(pk-pkv)**2
                cota = ze + pe*(pk-pke)-(1/(2*Kv))*(pk-pke)**2
                pend = type_Acuerdo(pe,ps)
                aling = h
                continue
        if pks < pk:
            cota = puntos_eje_alz[-1][7]
            pend = puntos_eje_alz[-1][-1]
            aling = h
        puntos[i][2] = cota
        if ins == 8:
            puntos[i].extend([pend,aling])
        else:
            puntos[i][8],puntos[i][9]=pend,aling
        i=i+1
    #for jj in puntos: print jj
    return puntos


def get_PtosEjeAlzado(alz):
    """Return list of vertical aligns
    RoadVertAlign=[[pk_ini,zini,pke,ze,pks,zs,pkv,zv,Kv,L,pe,ps]]

    Table from NC road St1

        >>> table_alz=read_TableAlz('St2')
        >>> get_PtosEjeAlzado(table_alz)
        [[0.0, 124.5, 259.0712797017927, 119.83671696536773, 240.9287202982073, 119.83413057291965, 250.0, 120.0, 500.0, -18.142559403585405, -0.018, 0.018285118807170812], \
[240.9287202982073, 119.83413057291965, 657.98203603, 127.46, 657.98203603, 127.46, 657.98203603, 127.46, 0, 0, 0.018285118807170812, 0]]
    """
    pk_ini, zini = alz[0][4], alz[0][5]
    pkv, zv = [pk_ini,zini]
    puntos_eje_alz = []

    for i in range(1,len(alz)-1,1):

        pk1, z1 = alz[i-1][4], alz[i-1][5]
        pkv, zv = alz[i][4], alz[i][5]
        pk2, z2 = alz[i+1][4], alz[i+1][5]

        pe=(zv-z1) / (pkv-pk1)
        if pk2 == pkv:
            ps = 0
        else:
            ps = (z2-zv)/(pk2-pkv)

        if alz[i][6] != '':Kv=alz[i][6]
        else:
            puntos_eje_alz.append([pk_ini,zini,pkv,zv,pkv,zv,pkv,zv,0,0,pe,ps])
            pk_ini = pkv; zini = zv
            continue
        phi = (pe-ps)

        T = Kv * phi/2
        L = 2*T
        #B=Kv*phi**2/8
        pke = pkv - T
        pks = pkv + T
        ze = zv - pe*T
        zs = zv + ps*T

        puntos_eje_alz.append([pk_ini,zini,pke,ze,pks,zs,pkv,zv,Kv,L,pe,ps])
        pk_ini = pks; zini = zs

    pk_fin, zfin = alz[-1][4], alz[-1][5]
    pk2, z2 = [pk_fin,zfin]
    if pk2 == pkv:
        ps = 0
    else:
        ps = (z2-zv) / (pk2-pkv)
    puntos_eje_alz.append([pk_ini,zini,pk_fin,zfin,pk_fin,zfin,pk_fin,zfin,0,0,ps,0])
    #for jj in puntos_eje_alz: print jj
    return puntos_eje_alz

def type_Pend(pe):

    if pe>0: typep = "'Up'"
    else: typep = "'Down'"
    return typep

def type_Acuerdo(pe, ps):

    if ((pe > 0 and ps < 0) or abs(pe) < abs(ps)):
        return "'Convex'"
    else:
        return "'Concave'"



def generate_PtsAlz(puntos, puntos_eje, puntos_alz):

    p_seg,p_vert = [],[]
    ps = 0
    pk_ini, zini, pks, pe = puntos_alz[0][0],puntos_alz[0][1],0,puntos_alz[0][10]
    x0, y0 = get_PlantaXY(float(pk_ini),puntos_eje)[:2]
    p_caract = [[x0,y0,zini,1,pk_ini,"'Ini'",1]]
    Ini = [[x0,y0,zini,1,pk_ini,"'Ini'",1]]
    i,h,k = 1,1,1

    for i in range(0,len(puntos_alz)-1,1):

        pk_ini, zini, pke, ze, pks, zs, pkv, zv, Kv, L, pe, ps = puntos_alz[i]
        if Kv == 0:
            cota = zv
        else:
            cota = ze + pe*(pkv-pke) - (1/(2*Kv))*(pkv-pke)**2

        x1,y1 = get_PlantaXY(float(pke),puntos_eje)[:2]
        x2,y2 = get_PlantaXY(float(pkv),puntos_eje)[:2]
        x3,y3 = get_PlantaXY(float(pks),puntos_eje)[:2]

        p_caract.append([x1,y1,ze,k+1,pke,"'Ae'",i+1])
        p_caract.append([x2,y2,cota,k+2,pkv,"'v'",i+1])
        p_caract.append([x3,y3,zs,k+3,pks,"'As'",i+1])

        p_vert.append([[x2,y2,zv,i,"'V'",i],
                       [0,0,0,h,pk_ini,type_Pend(pe),pke-pk_ini,pe],
                       [0,0,0,h+1,pke,type_Acuerdo(pe,ps),L/2,Kv],
                       [0,0,0,h+2,pkv,type_Acuerdo(pe,ps),L/2,Kv]])

        p_seg.append(Ini+[p for p in puntos if (p[4]> pk_ini and p[4]< pke)]+
                      [[x1,y1,ze,1,pke,"'Ae'",i+1]])
        p_seg.append([[x1,y1,ze,1,pke,"'Ae'",i+1]]+
                      [p for p in puntos if (p[4]> pke and p[4]< pkv)]+
                      [[x2,y2,cota,1,pkv,"'V'",i+1]])
        p_seg.append([[x2,y2,cota,1,pkv,"'V'",i+1]]+
                      [p for p in puntos if (p[4]> pkv and p[4]< pks)]+
                      [[x3,y3,zs,1,pks,"'As'",i+1]])
        Ini=[[x3,y3,zs,i,pks,"'As'",i+1]]

        h = h + 3
        k = k + 3

    pk_fin, zfin = puntos_alz[-1][2], puntos_alz[-1][3]

    x4, y4 = get_PlantaXY(float(pk_fin), puntos_eje)[:2]

    p_caract.append([x4,y4,zfin,k+1,pk_fin,"'End'",i+1])
    p_seg.append(Ini+[p for p in puntos if (p[4]> pks and p[4]< pk_fin)]+
                 [[x4,y4,zfin,1,pk_fin,"'End'",i+1]])
    p_vert.append([[x4,y4,zfin,h,0,"'V'",i],
                   [x4,x4,zfin,h,pk_fin,type_Pend(pe),pk_fin-pks,ps]])
    #for jj in p_seg: print jj
    return p_seg, p_caract, p_vert


#### ############## Section #### ##################

def read_ColumnSecc(table_secc, column):

    Sec, Cota, pks, type1 = [], [], [], []
    for i in range(0,len(table_secc), 1):

        if table_secc[i][column] != '':

            if table_secc[i][column].find(';') == -1: # not found
                Sec.append([table_secc[i][column]])
            else:
                Sec.append(table_secc[i][column].split(';'))
            pks.append(table_secc[i][4])
            if table_secc[i][column+2] != '':
                type1.append(table_secc[i][column+2].split(';'))
            else:
                type1.append([ 'l' for p in Sec[i]])

    if Sec != []:
        Sec = map(lambda *row: [elem or '0 0' for elem in row], *Sec) #transp
        for i,line in enumerate(Sec):
            Sec[i] = [float(p.split(' ')[0]) for p in line]
            Cota.append([float(p.split(' ')[1]) for p in line])
        type1 = map(lambda *row: [elem or 'l' for elem in row], *type1) #transp

    return Sec, Cota, pks, type1


def get_Desplaz(table_plant, Sec, Cota, pks, type1, Puntos, izq):

    M_ptos = []
    M_ptos_caract = []
    type2 = []
    sobrei = 0
    #print Sec,Cota
    for i, line in enumerate(Sec):

        Puntos_Despl = [[0]]
        Pc_izq = []
        pkant = 0.0
        npks = pks[:]
        Dist = line[:]
        Cotas = Cota[i][:]
        type2 = type1[i][:]
        if 'e' in type2: sobrei = sobrei+1

        for j, dist in enumerate(Dist[:-1]):

            if Dist[j] != -1 and Dist[j+1] == -1:
                Dist[j+1] = Dist[j]
                Cotas[j+1] = Cotas[j]
                npks[j+1] = npks[j]
                type2[j+1] = type2[j]
                continue

            #incremento de sobreancho a cada desplazado
            if type2[j] == "e":
                sobre2 = sobrei
            else:
                sobre2 = 0

            pkini = npks[j]
            pkfin = npks[j+1]

            ptosDes,Pc = get_PtosDesplazdos(Puntos,table_plant,Dist[j],
                                            Cotas[j],Dist[j+1],Cotas[j+1],
                                            sobre2,izq,pkini,pkfin,type2[j])

            for h,row in enumerate(ptosDes):

                if len(ptosDes[h]) > 1:
                    ptosDes[h][4] = row[4]+pkant

                if Puntos_Despl[-1][-1] != ptosDes[h][-1]:
                    Puntos_Despl.append(ptosDes[h])

                elif Puntos_Despl[-1][-1] == ptosDes[h][-1] and len(ptosDes[h]) > 1:
                    del Puntos_Despl[-1]
                    Puntos_Despl.append(ptosDes[h])

            if len(Puntos_Despl[-1]) > 1:
                pkant = Puntos_Despl[-1][4]

            Pc_izq.extend(Pc)

        M_ptos.append(Puntos_Despl)
        if Pc_izq != []:
            M_ptos_caract.append(Pc_izq)

    return M_ptos,M_ptos_caract



def generate_Desplaz(table_plant, table_secc, Puntos):

    M_ptos_izq,M_ptos_der,M_ptos_caract = [],[],[]
    SecIzq,CotaIzq,pks,typel = read_ColumnSecc(table_secc,5)
    SecDer,CotaDer,pks,typer = read_ColumnSecc(table_secc,6)

    M_ptos_izq,M_ptos_caract = get_Desplaz(table_plant,SecIzq[::-1],CotaIzq[::-1],pks,typel[::-1],Puntos,1)
    M_ptos_der,M_ptos_caract2 = get_Desplaz(table_plant,SecDer,CotaDer,pks,typer,Puntos,0)

    M_ptos_caract = M_ptos_caract + M_ptos_caract2

    M_ptos_caract = [m for p in M_ptos_caract for m in p]

    return M_ptos_izq[::-1], M_ptos_der, M_ptos_caract



def clotoide_GetA(radio, yo_ent, sobreancho, izq):

    h = 1*pi/200
    Tau = 0.0001*pi/200
    xo, yo = aprox_coord2(abs(radio), Tau)
    if (izq and radio > 0) or (izq == 0 and radio < 0): sobreancho = sobreancho
    elif (izq and radio < 0) or (izq == 0 and radio > 0): sobreancho = sobreancho*(-1)

    #Comprobar que el sobreancho sea mayor que el retranqueo
    while abs(yo-(yo_ent-sobreancho))>0.000001:

        xo, yo = aprox_coord2(abs(radio), Tau)
        if yo > yo_ent - sobreancho:
            Tau = Tau - h
            h = h / 10
        else:
            Tau = Tau + h

    L = Tau*2*abs(radio)
    A = sqrt(L*abs(radio))
    return A


def get_Paralles(table_plant, dist, sobreancho, izq):

    a,b,z1 = float(table_plant[0][0]),float(table_plant[0][1]),float(table_plant[0][2])
    c,d,z2 = float(table_plant[1][0]),float(table_plant[1][1]),float(table_plant[1][2])
    r = sqrt((c-a)**2+(d-b)**2)
    v = [(d-b)/r,-(c-a)/r]
    if izq: v[0] = v[0]*-1;  v[1] = v[1]*-1
    salida = []
    salida.append([v[0]*dist+a,v[1]*dist+b,table_plant[0][2],table_plant[0][3],0,0.0,0.0,0.0,0.0])
    Lrecta = 0
    for ii in range(1,len(table_plant)-1,1):

        sobreanchoTable=float(table_plant[ii][8])
        a,b,z1=float(table_plant[ii-1][0]),float(table_plant[ii-1][1]),float(table_plant[ii-1][2])
        c,d,z2=float(table_plant[ii][0]),float(table_plant[ii][1]),float(table_plant[ii][2])
        e,f,z3=float(table_plant[ii+1][0]),float(table_plant[ii+1][1]),float(table_plant[ii+1][2])

        r=sqrt((c-a)**2+(d-b)**2)
        v=[(d-b)/r,-(c-a)/r]
        if izq: v[0]=v[0]*-1;  v[1]=v[1]*-1
        a1 = v[0]*dist + a
        b1 = v[1]*dist + b
        c1 = v[0]*dist + c
        d1 = v[1]*dist + d

        s = sqrt((e-c)**2 + (f-d)**2)
        w = [(f-d)/s,-(e-c)/s]
        if izq: w[0] = w[0]*-1;  w[1] = w[1]*-1
        e1 = w[0]*dist + e
        f1 = w[1]*dist + f
        c2 = w[0]*dist + c
        d2 = w[1]*dist + d

        c3,d3 = pto_corte_2_rectas(a1,b1,c1,d1,e1,f1,c2,d2)

        Lrecta += sqrt((c3-a1)**2+(d3-b1)**2)
        R = float(table_plant[ii][5])
        if R == 0:
            salida.append([c3,d3,table_plant[ii][2],table_plant[ii][3],Lrecta,0.0,0.0,0.0,0.0])
            continue

        Aent,Asal = table_plant[ii][6],table_plant[ii][7]

        # Clotoide de entrada en locales
        xo_ent,yo_ent,Tau_ent,Lent,xe,ye=clotoide_Locales(Aent,abs(R))
        # Clotoide de salida en locales
        xo_sal,yo_sal,Tau_sal,Lsal,xs,ys=clotoide_Locales(Asal,abs(R))

        if izq != 0 and R < 0: radio = R + dist - (sobreancho*sobreanchoTable)
        elif izq != 0 and R > 0: radio = R + dist + (sobreancho*sobreanchoTable)
        elif izq == 0 and R > 0: radio = R - dist - (sobreancho*sobreanchoTable)
        elif izq == 0 and R < 0: radio = R - dist + (sobreancho*sobreanchoTable)

        # Parametro A de entrada
        if Aent == 0: Aent1 = 0
        else: Aent1 = clotoide_GetA(radio,yo_ent,sobreancho*sobreanchoTable,izq)
        # Parametro A de salida
        if Asal == 0: Asal1 = 0
        else: Asal1 = clotoide_GetA(radio,yo_sal,sobreancho*sobreanchoTable,izq)

        salida.append([c3,d3,table_plant[ii][2],table_plant[ii][3],Lrecta,radio,Aent1,Asal1,0])

    a=float(table_plant[-2][0]); b=float(table_plant[-2][1]); z1=float(table_plant[-2][2])
    c=float(table_plant[-1][0]); d=float(table_plant[-1][1]); z2=float(table_plant[-1][2])
    r = sqrt((c-a)**2+(d-b)**2)
    v = [(d-b)/r,-(c-a)/r]
    if izq: v[0]=v[0]*-1;  v[1]=v[1]*-1
    Lrecta += sqrt((c-a)**2+(d-b)**2)
    salida.append([v[0]*dist+c,v[1]*dist+d,table_plant[-1][2],table_plant[-1][3],Lrecta,0.0,0.0,0.0,0.0])
    #print salida
    return salida

#### ############## Transversales #### ##################

#Pto de corte entre la perpendicular a un pto de una recta y una recta
def get_PtoCorte_Perpend_Recta(Az, x, y, xref_d, yref_d, Az_d, Lrecta_d):

    h = Lrecta_d / 2
    Li = -0.00001
    eq = -0.001
    while abs(eq) > 0.00001 and Li <= Lrecta_d:

        eq_ant = eq
        x1 = xref_d + Li*sin(Az_d)
        y1 = yref_d + Li*cos(Az_d)
        eq = y1 - (y-tan((Az))*(x1-x))
        if (eq_ant > 0 and eq < 0) or (eq_ant < 0 and eq > 0):
            Li = Li - h
            h = h / 2
        else:
            Li = Li + h

    if abs(eq) > 0.001: 
        x1, y1 = [0,0]
    if Li > Lrecta_d: Li = Lrecta_d
    return x1, y1, Li

#Pto de corte entre la perpendicular a un pto de un circulo y un circulo
def get_PtoCorte_Perpend_Circulo(Az, x, y, xref_d, yref_d, Az_ini_d, Az_fin_d, Dc_d, R_d):

    h = Dc_d/2
    Li = -0.000001
    eq = -0.001
    cond = True
    if R_d>0:
        if Az_ini_d>Az_fin_d: Az_ini_d = Az_ini_d-2*pi
        while abs(eq)>0.0001 and cond:
            eq_ant = eq
            x1 = xref_d+R_d*sin(Az_ini_d+abs(Li/R_d))
            y1 = yref_d+R_d*cos(Az_ini_d+abs(Li/R_d))
            eq = y1-(y-tan((Az))*(x1-x))
            if (eq_ant>0 and eq<0) or (eq_ant<0 and eq>0):
                Li = Li-h
                h = h/2
            else:
                Li = Li+h
            cond = (Az_ini_d+(Li/R_d)<=Az_fin_d)
    elif R_d<0:
        if Az_ini_d<Az_fin_d: Az_fin_d = Az_fin_d-2*pi
        while abs(eq)>0.0001 and cond:
            eq_ant = eq
            #print (Az_ini_d-abs(Li/R_d))*200/pi
            x1 = xref_d-R_d*sin(Az_ini_d-abs(Li/R_d))
            y1 = yref_d-R_d*cos(Az_ini_d-abs(Li/R_d))
            eq = y1-(y-tan((Az))*(x1-x))
            if (eq_ant>0 and eq<0) or (eq_ant<0 and eq>0):
                Li = Li-h
                h = h/2
            else:
                Li = Li+h
            cond = (Az_ini_d-abs(Li/R_d)>=Az_fin_d)
    if abs(eq)>0.001: 
        x1, y1 = [0,0]
    return x1, y1, Li

#Pto de corte entre la perpendicular de una clotoide y la clotoide desplazada
def get_PtoCorte_Perpend_Clot(Az, x, y, xref_d, yref_d, Az_d, A_d, L_d, R_d, tipo):

    h = L_d/2
    Li = -0.000001
    eq = -0.001
    while abs(eq)>0.0001 and Li<=L_d:
        eq_ant = eq
        Ri = A_d**2/Li
        Tau_i = Li/(2*Ri)
        xo, yo = aprox_coord(Li, Tau_i)
        if tipo=="ent":
            if R_d>0:
                x1 = xref_d-xo*sin(-Az_d)+yo*cos(-Az_d)
                y1 = yref_d+xo*cos(-Az_d)+yo*sin(-Az_d)
            elif R_d<0:
                x1 = xref_d+xo*sin(Az_d)-yo*cos(Az_d)
                y1 = yref_d+xo*cos(Az_d)+yo*sin(Az_d)
        elif tipo=="sal":
            if R_d>0:
                x1 = xref_d-xo*sin(Az_d)+yo*cos(Az_d)
                y1 = yref_d-xo*cos(Az_d)-yo*sin(Az_d)
            elif R_d<0:
                x1 = xref_d+xo*sin(-Az_d)-yo*cos(-Az_d)
                y1 = yref_d-xo*cos(-Az_d)-yo*sin(-Az_d)
        eq = y1-(y-tan((Az))*(x1-x))
        if (eq_ant > 0 and eq < 0) or (eq_ant < 0 and eq > 0):
            Li = Li - h
            h = h / 2
        else:
            Li = Li + h
    if abs(eq) > 0.001: 
        x1, y1 = [0,0]
    return x1, y1, Li


# busca desde la alineacion anterior a la posterior
def get_ptoDesplaz(x, y, PK, Az, tipo, align, puntos_DesplEje):

    x1, y1, PK2 = 0, 0, 0
    x_ini_d,y_ini_d,z_ini_d,Lrecta_d,LrAcum_d,Az_ent_d = puntos_DesplEje[align][0]
    Aent_d,Az_ent_d,xad_d,yad_d,xar_d,yar_d,Lent_d,LeAcum_d = puntos_DesplEje[align][1][0:8]
    R_d,alpha_d,xc_d,yc_d,Az_ini_d,Az_fin_d,Dc_d,LcAcum_d = puntos_DesplEje[align][2][0:8]
    Asal_d,Az_sal_d,xda_d,yda_d,xra_d,yra_d,Lsal_d,LsAcum_d = puntos_DesplEje[align][3][0:8]

    if tipo=='Line' or tipo=='Ini' or tipo=='End':
        if align < len(puntos_DesplEje)-1:
            x1,y1,Li = get_PtoCorte_Perpend_Recta(Az,x,y,x_ini_d,y_ini_d,Az_ent_d,Lrecta_d)
        else:
            x1,y1,Li = get_PtoCorte_Perpend_Recta(Az,x,y,xda_d,yda_d,Az_sal_d,Lrecta_d)
        PK2 = LrAcum_d-Lrecta_d+Li
        if x1 == 0 and y1 == 0 and R_d != 0:
            x1,y1,Li = get_PtoCorte_Perpend_Clot(Az,x,y,xad_d,yad_d,Az_ent_d,Aent_d,Lent_d,R_d,"ent")
            PK2 = LeAcum_d-Lent_d+Li
        if x1 == 0 and y1 == 0 and R_d != 0:
            R_d = puntos_DesplEje[align-1][2][0]
            Asal_d,Az_sal_d,xda_d,yda_d,xra_d,yra_d,Lsal_d,LsAcum_d = puntos_DesplEje[align-1][3][0:8]
            x1,y1,Li = get_PtoCorte_Perpend_Clot(Az,x,y,xda_d,yda_d,Az_sal_d,Asal_d,Lsal_d,R_d,"sal")
            PK2 = LsAcum_d-Lsal_d+Li

    elif tipo=='Clot_in':
        x1,y1,Li = get_PtoCorte_Perpend_Clot(Az,x,y,xad_d,yad_d,Az_ent_d,Aent_d,Lent_d,R_d,"ent")
        PK2 = LeAcum_d-Lent_d+Li
        if x1 == 0 and y1 == 0:
            x1,y1,Li = get_PtoCorte_Perpend_Circulo(Az,x,y,xc_d,yc_d,Az_ini_d,Az_fin_d,Dc_d,R_d)
            PK2 = LcAcum_d-Dc_d+abs(Li)
        if x1 == 0 and y1 == 0:
            x1,y1,Li = get_PtoCorte_Perpend_Recta(Az,x,y,x_ini_d,y_ini_d,Az_ent_d,Lrecta_d)
            PK2 = LrAcum_d-Lrecta_d+Li

    elif tipo=='Curve':
        x1,y1,Li = get_PtoCorte_Perpend_Circulo(Az,x,y,xc_d,yc_d,Az_ini_d,Az_fin_d,Dc_d,R_d)
        PK2 = LcAcum_d - Dc_d + abs(Li)
        if x1 == 0 and y1 == 0:
            x1, y1, Li = get_PtoCorte_Perpend_Clot(Az,x,y,xad_d,yad_d,Az_ent_d,Aent_d,Lent_d,R_d,"ent")
            PK2 = LeAcum_d - Lent_d + Li
        if x1 == 0 and y1 == 0:
            x1, y1, Li = get_PtoCorte_Perpend_Clot(Az,x,y,xda_d,yda_d,Az_sal_d,Asal_d,Lsal_d,R_d,"sal")
            PK2 = LsAcum_d-Lsal_d+Li

    elif tipo=='Clot_out':
        x1,y1,Li = get_PtoCorte_Perpend_Clot(Az,x,y,xda_d,yda_d,Az_sal_d,Asal_d,Lsal_d,R_d,"sal")
        PK2 = LsAcum_d-Lsal_d+Li
        if x1 == 0 and y1 == 0:
            x1,y1,Li = get_PtoCorte_Perpend_Circulo(Az,x,y,xc_d,yc_d,Az_ini_d,Az_fin_d,Dc_d,R_d)
            PK2 = LsAcum_d-Dc_d+abs(Li)
        if x1 == 0 and y1 == 0:
            if align < len(puntos_DesplEje)-2:
                x_ini_d,y_ini_d,z_ini_d,Lrecta_d,LrAcum_d,Az_ent_d = puntos_DesplEje[align+1][0]
                Az_ent_d = puntos_DesplEje[align+1][1][1]
                x1,y1,Li = get_PtoCorte_Perpend_Recta(Az,x,y,x_ini_d,y_ini_d,Az_ent_d,Lrecta_d)
            else:
                Lrecta_d = puntos_DesplEje[align+1][0][3]
                Asal_d,Az_sal_d,xda_d,yda_d,xra_d,yra_d,Lsal_d,LsAcum_d = puntos_DesplEje[align+1][3][0:8]
                x1,y1,Li = get_PtoCorte_Perpend_Recta(Az,x,y,xda_d,yda_d,Az_sal_d,Lrecta_d)
            PK2 = LsAcum_d - Lrecta_d + Li

    if x1 == 0 and y1 == 0: 
        print 'Point not found ', PK, PK2, tipo

    return x1,y1,PK2



def get_PtosDesplazdos(puntos, table_plant, dist, cota, dist2, cota2, sobrea, izq, pkini, pkfin, type1):

    lin, Pc = [], []
    ptos = []
    #print dist,cota,dist2,cota2,pkini,pkfin
    for pp in puntos:
        if pkini <= pp[4] and pp[4] <= pkfin:
            ptos.append(pp)

    if dist != 0 and dist2==0: dist = 0
    if dist==dist2 and dist != 0 and type1=='e':

        desplaz = get_Paralles(table_plant,dist,sobrea,izq)
        puntos_DesplEje = get_PtosEjePlanta(desplaz)

        x, y, z, cat, PK, Az, tipo, align = ptos[0][0:8]
        x1,y1,PK2_ini = get_ptoDesplaz(x,y,PK,Az,tipo,align,puntos_DesplEje)
        for pt in ptos:

            x,y,z,cat,PK,Az,tipo,align = pt[0:8]

            cota0 = cota + ((pt[4]-pkini)*(cota2-cota))/(pkfin-pkini)
            x1,y1,PK2 = get_ptoDesplaz(x,y,PK,Az,tipo,align,puntos_DesplEje)
            if x1 != 0 and y1 != 0:
                lin.append([x1,y1,z + cota0,cat,PK2-PK2_ini,Az,'d' + str(dist),PK])
            else:
                lin.append([])

        a, b, Pc, c = generate_Pts(puntos_DesplEje,0,1,0,1,1)
        Pc = [row for row in Pc  if row[4]>=pkini and row[4]<=pkfin]

    elif dist != 0 and dist2 != 0:

        l_ant = 0
        x_ant = 0
        y_ant = 0

        for pt in ptos:

            x,y,z,cat,PK,Az,tipo,align = pt[0:8]

            if type1 == 'l' or type1 == '':
                distx = dist + ((pt[4]-pkini)*(dist2-dist))/(pkfin-pkini)

            elif type1 == 'c':
                if dist2 < dist:
                    distx = (dist)-sqrt((dist2-dist)**2*(1-cos(acos((pkfin-pt[4])/(pkfin-pkini)))**2))
                else:
                    distx = (dist2)-sqrt((dist2-dist)**2*(1-cos(acos((pt[4]-pkini)/(pkfin-pkini)))**2))

            elif re.search(r'^r', type1):
                rad, center = type1[1:].split(",")
                rad = float(rad)
                center = float(center)

                if rad > 0:
                    if (rad**2-((pt[4]-pkini)-center)**2) > 0:
                        distx = (rad+dist)-sqrt(rad**2-((pt[4]-pkini)-center)**2)
                    elif (pt[4]-pkini)==0:
                        distx = (rad+dist)
                    else:
                        distx = dist2
                else:
                    if (rad**2-((pt[4]-pkini)-center)**2) > 0:
                        distx = (rad+dist) + sqrt(rad**2-((pt[4]-pkini)-center)**2)
                        #distx = (dist)-sqrt(rad**2-((pt[4]-pkini)+rad)**2)
                    else:
                        distx = (rad + dist)

            cota0 = cota + ((pt[4]-pkini)*(cota2-cota))/(pkfin-pkini)

            if izq==1: Az1 = Az-pi/2
            else: Az1 = Az + pi/2

            x2 = x + (distx)*sin(Az1)
            y2 = y + (distx)*cos(Az1)

            if x_ant == 0: x_ant = x2
            if y_ant == 0: y_ant = y2

            l = sqrt((x2-x_ant)**2 + (y2-y_ant)**2)
            PK2 = l + l_ant
            lin.append([x2,y2,z+cota0,cat,PK2,Az,'d'+str(round(distx,6)),PK])

            x_ant = x2
            y_ant = y2
            l_ant = PK2

    elif dist==0:

        for pt in ptos:
            lin.append([pt[4]])

    return lin, Pc


def get_Trans(puntos, npk, mpk, m, perpizq, perpder, perpizq2, perpder2, discr, pkini, pkfin):

    trans, pklist = [], []

    ptos = []
    for pp in puntos:
        if pkini <= pp[4] and pp[4] < pkfin and pp[4]%npk==0:
            ptos.append(pp)

    if pkfin == puntos[-1][4]: ptos.append(puntos[-1])

    for pt in ptos:

        if mpk != 0 and (pt[4]%mpk == 0):
            h1 = m*perpizq
            h2 = m*perpizq
            ini_izq,ini_der = perpizq+h1,perpder+h2
        elif mpk != 0 :
            h1,h2 = 0,0
            ini_izq,ini_der = perpizq,perpder
        elif discr==0:
            h1 = ((pt[4]-pkini)*(perpizq2-perpizq))/(pkfin-pkini)
            h2 = ((pt[4]-pkini)*(perpder2-perpder))/(pkfin-pkini)
            ini_izq,ini_der = perpizq+h1,perpder+h2
        else:
            h1 = ((pt[4]-pkini)*(perpizq2-perpizq))/(pkfin-pkini)
            h2 = ((pt[4]-pkini)*(perpder2-perpder))/(pkfin-pkini)
            ini_izq,ini_der = discr,discr

        x,y,z,cat,PK,Az,tipo,align = pt[0:8]

        Ptos_recta_izq,resto,acum,cat = get_pts_Recta(x,y,z,Az-pi/2,ini_izq,perpizq+h1,discr,0,cat,align)
        Ptos_recta_der,resto,acum,cat = get_pts_Recta(x,y,z,Az+pi/2,ini_der,perpder+h2,discr,0,cat-1,align)
        trans.append(Ptos_recta_izq[::-1]+[pt]+Ptos_recta_der)
        pklist.append(pt)
        #for jj in trans: print jj
    return trans, pklist


def generate_Transv(puntos, table_transv): #Para modificarlos deben tener cota cero

    tra, trans_pklist = [], []
    #table_transv.append([0,0,0,0,table_transv[-1][4]+1,0,0,1])
    for j,line in enumerate(table_transv[:-1]):

        pkini,pkfin = line[4],table_transv[j+1][4]
        if line[7] == 0.0: continue

        trans,pklist = get_Trans(puntos,int(line[7]),0,0,line[5],line[6],table_transv[j+1][5],table_transv[j+1][6],0,pkini,pkfin)
        tra.extend(trans)
        trans_pklist.extend(pklist)

    return tra, trans_pklist


def generate_DesplazAreas(despl_izq, puntos, despl_der):

    if despl_izq == [] and despl_der == []: return []
    areas = []
    despl = despl_izq + despl_der
    if options['areaopt']:
        pair = [p.split('-') for p in options['areaopt'].split(',')]

        for p in pair:
            lin1,lin2 = [],[]
            for d in despl[int(p[0])-1]:
                if len(d) > 1:
                    lin1.append(d)

            for d in despl[int(p[1])-1]:
                if len(d) > 1:
                    lin2.append(d)

            areas.append(lin1 + lin2[::-1] + [lin1[0]])

    return areas


#def get_Terrain(puntos,tinmap):

    ##
    #map_info = pointer(Map_info())
    #Vect_set_open_level(2)
    #Vect_open_old(map_info, tinmap, MapSet)
    #z = c_double()
    #puntos_terr = []
    #for i,punt in enumerate(puntos):

        #Vect_tin_get_z(map_info, float(punt[0]), float(punt[1]), byref(z), None, None)

        #puntos_terr.append([punt[0], punt[1],z.value, punt[3], punt[4]])
    #Vect_close(map_info)
    #return puntos_terr


###############################################################################

def p_Type(data_type):
    ptype = POINTER(c_int)
    if data_type == 0:
        ptype = POINTER(c_int)
    elif data_type == 1:
        ptype = POINTER(c_float)
    elif data_type == 2:
        ptype = POINTER(c_double)
    return ptype



def get_Terrain(demmap):

    # Get Dem map and return array dem
    global xref, yref, xres, yres
    fd = Rast_open_old(demmap, MapSet)
    data_type = Rast_get_map_type(fd)

    #data_type = G_raster_map_type(demmap, MapSet)
    ptype = p_Type(data_type)
    #fd = G_open_cell_old(demmap, MapSet)
    rast = Rast_allocate_buf(data_type)
    rast = cast(c_void_p(rast), ptype)
    window = pointer(Cell_head())
    G_get_window(window)
    nrows = window.contents.rows
    ncols = window.contents.cols
    xref = window.contents.west
    yref = window.contents.north
    xres = window.contents.ew_res
    yres = window.contents.ns_res

    dem = [[0 for c in range(ncols)] for r in range(nrows)]
    for i in range(nrows):
        Rast_get_row(fd, rast, i, data_type)
        for j in range(ncols):
            dem[i][j] =  rast[j]

    Rast_close(fd)
    return dem

def drape_Points(puntos, dem):

    salida = []
    for i,punt in enumerate(puntos):
        pto_col = int((punt[0] - xref)/xres)
        pto_row = int((yref - punt[1])/yres)
        salida.append(punt[:2]+[dem[pto_row][pto_col]]+punt[3:])
    return salida


def drape_LinesPoints(lines, dem):

    salida = []
    for i,line in enumerate(lines):
        ptos = []
        for j,pto in enumerate(line):
            pto_col = int((pto[0] - xref)/xres)
            pto_row = int((yref - pto[1])/yres)
            ptos.append(lines[i][j][:2]+[dem[pto_row][pto_col]]+lines[i][j][3:])
        salida.append(ptos)
    return salida

#def drape_Points2(puntos,dem):

    #elev = raster.RasterRow('elev1')
    #elev.open('r')
    #region=Region()
    #salida=[]
    #for i,punt in enumerate(puntos):
        #pto_col = int((punt[0] - region.west)/region.ewres)
        #pto_row = int((region.north - punt[1])/region.nsres)
        #salida.append(punt[:2]+[elev[pto_row][pto_col]]+punt[3:])
    #elev.close()
    #return salida


#def drape_LinesPoints2(lines,dem):

    #elev = raster.RasterRow('elev1')
    #elev.open('r')
    #region=Region()
    #salida=[]
    #for i,line in enumerate(lines):
        #ptos=[]
        #for j,pto in enumerate(line):
            #pto_col = int((pto[0] - region.west)/region.ewres)
            #pto_row = int((region.north - pto[1])/region.nsres)
            #ptos.append(lines[i][j][:2]+[elev[pto_row][pto_col]]+lines[i][j][3:])

        #salida.append(ptos)
    #elev.close()
    #return salida


def get_Taludes(puntos,puntos_Despl,des,ter,des2,ter2,dem,pkini,pkfin):

    puntos_talud = []
    pta = []
    for i,pt in enumerate(puntos):

        pta = puntos_Despl[i]
        if len(pta)>1 and des != 0 and ter != 0:
            a = pt[0]; b = pt[1]; z = pt[2]
            c = pta[0]; d = pta[1]; z1 = pta[2]

            if c != 0 and d != 0:
                Az = azimut(a,b,c,d)
                pto_col = int((c - xref)/xres)
                pto_row = int((yref - d)/yres)
                zt = dem[pto_row][pto_col]
                h = 1.0
                Li = 0.0
                zini = z1
                Li_ant = Li
                p = 0
                if z1>zt: #Terraplen
                    tipo = "Terraplen"
                    talud = ter + ((pt[4]-pkini)*(ter2-ter))/(pkfin-pkini)
                    while abs(z1-zt)>0.001:
                        x1 = c + Li*sin(Az)
                        y1 = d + Li*cos(Az)
                        pto_col = int((x1 - xref)/xres)
                        pto_row = int((yref - y1)/yres)
                        zt = dem[pto_row][pto_col]
                        if p and zt != zt_ant:
                            zt = zt_ant
                        z1 = zini-Li*talud
                        if z1<zt:
                            p = 1
                            Li = Li_ant
                            h = h/2
                        else:
                            Li_ant = Li
                            zt_ant = zt
                            Li = Li + h

                elif z1<zt: #Desmonte
                    tipo = "Desmonte"
                    talud = des + ((pt[4]-pkini)*(des2-des))/float(pkfin-pkini)
                    while abs(zt-z1)>0.001:
                        x1 = c + Li*sin(Az)
                        y1 = d + Li*cos(Az)
                        pto_col = int((x1 - xref)/xres)
                        pto_row = int((yref - y1)/yres)
                        zt = dem[pto_row][pto_col]
                        if p and zt != zt_ant:
                            zt = zt_ant #Por si cambia zt en el ultimo instante
                        z1 = zini + Li*talud
                        if z1>zt:
                            p = 1
                            Li = Li_ant
                            h = h/2
                        else:
                            Li_ant = Li
                            zt_ant = zt
                            Li = Li + h

                puntos_talud.append([x1,y1,z1]+pt[3:]+[tipo]+[pt[4]])
        else:
            puntos_talud.append(pta)

    return puntos_talud


def generate_Taludes(puntos, puntos_Despl_izq, puntos_Despl_der, table_secc, dem):

    tal_izq, tal_der = [[0]],[[0]]
    if puntos_Despl_izq == [] and puntos_Despl_der == []: return [], []

    for j,line in enumerate(table_secc[:-1]):

        pkini,pkfin = line[4],table_secc[j+1][4]
        ptos,ptos_izq = [],[]
        for i,pp in enumerate(puntos):
            if pkini <= pp[4] and pp[4] <= pkfin:
                ptos.append(pp)
                ptos_izq.append(puntos_Despl_izq[0][i])

        taludes = get_Taludes(ptos,ptos_izq,float(line[9]),float(line[11]),
                            float(table_secc[j+1][9]),float(table_secc[j+1][11]),dem,pkini,pkfin)

        for h,row in enumerate(taludes):

            if tal_izq[-1][-1] != taludes[h][-1]:
                tal_izq.append(taludes[h])

            elif tal_izq[-1][-1] == taludes[h][-1] and len(taludes[h]) > 1:
                del tal_izq[-1]
                tal_izq.append(taludes[h])

    for j,line in enumerate(table_secc[:-1]):

        pkini,pkfin = line[4],table_secc[j+1][4]
        ptos,ptos_der = [],[]
        for i,pp in enumerate(puntos):
            if pkini <= pp[4] and pp[4] <= pkfin:
                ptos.append(pp)
                ptos_der.append(puntos_Despl_der[-1][i])

        taludes = get_Taludes(ptos,ptos_der,float(line[10]),float(line[12]),
                            float(table_secc[j+1][10]),float(table_secc[j+1][12]),dem,pkini,pkfin)

        for h,row in enumerate(taludes):

            if tal_der[-1][-1] != taludes[h][-1]:
                tal_der.append(taludes[h])

            elif tal_der[-1][-1] == taludes[h][-1] and len(taludes[h]) > 1:
                del tal_der[-1]
                tal_der.append(taludes[h])

    return tal_izq, tal_der


def split_LineasTalud(Puntos_Talud, Despl):

    linT = [[]]
    linD = [[]]
    for i,pto in enumerate(Puntos_Talud):
        if len(pto) == 1: continue
        else:
            talud_ant = Puntos_Talud[i][-2]
            break

    for i,pto in enumerate(Puntos_Talud):
        if len(pto) > 1:
            talud = pto[-2]
            if talud == talud_ant or (talud and talud_ant==''):
                linT[-1].append(pto)
                linD[-1].append(Despl[0][i])
            else:

                if linT[-1] != []:
                    linT.append([])
                    linD.append([])
                    linT[-1].append(Puntos_Talud[i-1])
                    linD[-1].append(Despl[0][i-1])
                    linT[-1].append(pto)
                    linD[-1].append(Despl[0][i])
            talud_ant = talud
        else:
            if linT[-1] != []:
                linT.append([])
                linD.append([])
            talud_ant = ''
    if linT[-1] == []:
        del linT[-1]
        del linD[-1]

    return linT, linD


def generate_TaludesAreas(Puntos_Talud_izq, Desplazados_izq, Desplazados_der, Puntos_Talud_der):

    # despl_izq[0] [line1,[],line2,...] --> [[ line1,linet1 ],[ line12,linet2 ],...]
    # taludes      [linet1,[],linet2,...]
    Tal_izq, Des_izq = split_LineasTalud(Puntos_Talud_izq,Desplazados_izq)
    Tal_der, Des_der = split_LineasTalud(Puntos_Talud_der,Desplazados_der[::-1])

    TalDesm, DesDesm = [],[]
    for j,line in enumerate(Tal_izq):
        if line[-1][-2] == 'Desmonte':
            TalDesm.append(line)
            DesDesm.append(Des_izq[j])

    for j,line in enumerate(Tal_der):
        if line[-1][-2] == 'Desmonte':
            TalDesm.append(line)
            DesDesm.append(Des_der[j])

    TalTerr,DesTerr = [],[]
    for j,line in enumerate(Tal_izq):
        if line[-1][-2] == 'Terraplen':
            TalTerr.append(line)
            DesTerr.append(Des_izq[j])

    for j,line in enumerate(Tal_der):
        if line[-1][-2] == 'Terraplen':
            TalTerr.append(line)
            DesTerr.append(Des_der[j])

    areas_desm = []
    for j,line in enumerate(TalDesm):
        tline = DesDesm[j]
        areas_desm.append(line+tline[::-1]+[line[0]])

    areas_terr = []
    for j,line in enumerate(TalTerr):
        tline = DesTerr[j]
        areas_terr.append(line+tline[::-1]+[line[0]])

    #print areas_desm,areas_terr
    return areas_desm, areas_terr


def rellenar_linea(puntos, talud,despl):

    # talud  [pto,[],pto,[],...] --> [pto,pto2,pto,pto1,...]
    # despl  [pto1,[],[],pto1,...]
    # puntos [pto2,pto2,pto2,pto2,...]
    new = []
    for i,pto in enumerate(talud):
        if pto == [] or len(pto) == 1:
            if len(despl[i]) >1:
                new.append(despl[i])
        else:
            new.append(talud[i])
    return new


def generate_ContornoAreas(puntos, talud_izq, despl_izq, despl_der, talud_der):

    talud_izq_rell = rellenar_linea(puntos,talud_izq,despl_izq[0])
    talud_der_rell = rellenar_linea(puntos,talud_der,despl_der[-1])

    uniq = []
    for i in talud_izq_rell + talud_der_rell[::-1]:
        if i not in uniq:
            uniq.append(i)
    return uniq


##############################################################################

def discr_Lines(lines, discr):

    disLines = []
    for pto in lines:
        resto, acum = 0, 0
        cat_r = 1
        disptos = []
        for i in range(len(pto[:-1])):

            disptos.append(pto[i])
            Az = azimut(pto[i][0],pto[i][1],pto[i+1][0],pto[i+1][1])
            Lrecta = sqrt((pto[i+1][0]-pto[i][0])**2+(pto[i+1][1]-pto[i][1])**2)
            Ptos_recta,resto,acum,cat_r = get_pts_Recta(pto[i][0],pto[i][1],0,Az,discr-resto,Lrecta,discr,acum,cat_r,i)
            disptos.extend(Ptos_recta)
        disptos.append(pto[i+1])
        disLines.append(disptos)
    return disLines


def get_TransDespl(Trans, desplaz_izq, desplaz_der):
    # Añade los ptos de corte de los desplazados con los trasversales a los mismos.
    # Cota cero para poder mover los ptos del transv
    TransDespl = []
    for i, line in enumerate(Trans):


        # Cuidado con la asignacion de listas que se pasan por referencia/mutables
        tmpline = [line[0][:2]+[0]+line[0][3:]+[0]]
        for line_desp in desplaz_izq:
            for i_izq,pto in enumerate(line_desp):
                if len(pto) > 1 and line[1][4] == pto[-1]:
                    dist_izq = sqrt((line[1][0]-pto[0])**2+(line[1][1]-pto[1])**2)
                    tmpline.append(pto[:2]+[0]+pto[3:]+[round(dist_izq,6)]) # Cota cero para poder mover los ptos del transv
                    continue

        tmpline.append(line[1][:2]+[0]+line[1][3:]+[0])

        for line_desp in desplaz_der:
            for i_der,pto in enumerate(line_desp):
                if len(pto) > 1 and line[1][4] == pto[-1]:
                    dist_der = sqrt((line[1][0]-pto[0])**2+(line[1][1]-pto[1])**2)
                    tmpline.append(pto[:2]+[0]+pto[3:]+[round(dist_der,6)])
                    continue
        tmpline.append(line[2][:2]+[0]+line[2][3:]+[0])

        TransDespl.append(tmpline)

    return TransDespl


def get_ptoByPk(Trans_Pklist, listaPtos, flagDespl):

    salida = []
    for ptoss in Trans_Pklist:
        esta = 0
        for ptot in listaPtos:
            if flagDespl == 1:
                if len(ptot)>1 and ptoss[4] == ptot[-1]:
                    salida.append(ptot)
                    esta = 1
                    continue
            else:
                if len(ptot)>1 and ptoss[4] == ptot[4]:
                    salida.append(ptot)
                    esta = 1
                    continue
        if esta==0:
            salida.append([])
    return salida

def get_SeccTerr(Trans_Pklist, Desplaz_izq, Desplaz_der, Puntos_Talud_izq, Puntos_Talud_der):

    talud_izq = get_ptoByPk(Trans_Pklist,Puntos_Talud_izq,0)
    talud_der = get_ptoByPk(Trans_Pklist,Puntos_Talud_der,0)

    secc_izq = [talud_izq]
    for desp in Desplaz_izq:
        secc_izq.append(get_ptoByPk(Trans_Pklist,desp,1))

    secc_der = []
    for desp in Desplaz_der:
        secc_der.append(get_ptoByPk(Trans_Pklist,desp,1))

    secc_der.append(talud_der)
    secc = secc_izq + [Trans_Pklist] + secc_der
    secc = [[row[i] for row in secc] for i in range(len(secc[0]))] # transpuesta

    return secc


# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #



def gen_LongProfileGuitarr(ASegmentos,APuntos_caract,puntos,puntos_terr,table_alz,escala,opt1):

    mark_lon,mark_x_dist,mark_y_dist,DistGitarr = opt1.split(',')
    mark_lon,mark_x_dist,mark_y_dist,DistGitarr = int(mark_lon),int(mark_x_dist),int(mark_y_dist),float(DistGitarr)

    dist_ejes_x = DistGitarr

    alto_guit = dist_ejes_x*6
    cerox = 100
    ceroy = 100 + alto_guit

    cotaMax_eje = max([p[2] for p in puntos])
    cotaMin_eje = min([p[2] for p in puntos])
    cotaMax_terr = max([p[2] for p in puntos_terr])
    cotaMin_terr = min([p[2] for p in puntos_terr])
    cotaMax = max([cotaMax_eje,cotaMax_terr])
    cotaMin = min([cotaMin_eje,cotaMin_terr])

    dif_y_ref = (cotaMin)-int(cotaMin)
    cero_y_ref = (cotaMin*escala-ceroy)-dif_y_ref*escala

    # Perfil del eje
    ASeg_ref = []
    for seg in ASegmentos:

        ASeg_ref.append([[cerox+p[4],p[2]*escala-cero_y_ref,0,p[3:]] for p in seg])

    APtos_caract_ref = [[cerox+p[4],p[2]*escala-cero_y_ref,0,p[3],p[4],p[5],p[6],] for p in APuntos_caract]
    #ptos_ref = [[cerox+p[4],p[2]*escala-cero_y_ref,0] for p in puntos]

    # Perfil del terreno
    ptos_terr_ref = [[cerox+p[4],p[2]*escala-cero_y_ref,0] for p in puntos_terr]

    dist_orig,dist_par,cras,cterr,croja = [],[],[],[],[]
    d_ant = 0

    for pt in puntos:
        for j in range(0,int(puntos[-1][4]),mark_x_dist):

            if j == int(pt[4]):

                dist_orig.append(pt[4])
                dist_par.append(pt[4]-d_ant)
                d_ant = pt[4]
                continue
    dist_orig.append(puntos[-1][4])
    dist_par.append(puntos[-1][4]-d_ant)

    cras = [p[2] for p in puntos if p[4] in dist_orig ]
    cterr = [p[2] for p in puntos_terr if p[4] in dist_orig ]
    croja = [cras[i]-cterr[i] for i in range(len(cras))]

    # Ejes de coordenadas
    # Eje y
    eje_y = [[[cerox,ceroy,0,1,"'Elev'"],[cerox,(cotaMax)*escala-cero_y_ref,0,1]]]

    # Marcas eje y
    mark_y = []
    cat = 1
    for i in range(int(ceroy),int((cotaMax)*escala-cero_y_ref),int(mark_y_dist*escala)):
        labely = (cotaMin+(i-ceroy)/escala)-dif_y_ref
        mark_y.append([[cerox-mark_lon,i,0,cat,labely],[cerox+mark_lon,i,0,cat,labely]])
        cat = cat + 1
    mark_y.append([[cerox-mark_lon,cotaMax*escala-cero_y_ref,0,cat,round(cotaMax,2)],
                   [cerox+mark_lon,cotaMax*escala-cero_y_ref,0,cat,cotaMax]])

    # Eje x
    eje_x = [[[cerox,ceroy,0,1,"'Origin distance'"],[cerox+puntos[-1][4],ceroy,0,1]]]

    # Ejes x de distancias y cotas
    eje_x_labels = ["'Origin distance'","'Partial distance'","'Aling elev'","'Ground elev'","'Cota roja'","'Nada'"]
    for i in range(1,6):
        eje_x.append([[cerox,ceroy-i*dist_ejes_x,0,i+1,eje_x_labels[i]],[cerox+puntos[-1][4],ceroy-i*dist_ejes_x,0,i+1]])

    # Marcas eje x
    mark_x = []
    cat = 1
    for j in range(0,6):
        t = 0
        for pt in puntos:
            for k in range(0,int(puntos[-1][4]),mark_x_dist):
                if k == int(pt[4]):
                    if j==0: label = round(dist_orig[t],2)
                    elif j==1: label = round(dist_par[t],2)
                    elif j==2: label = round(cras[t],2)
                    elif j==3: label = round(cterr[t],2)
                    elif j==4: label = round(croja[t],2)
                    else: label = 0
                    t = t + 1
                    mark_x.append([[cerox+k,ceroy-mark_lon-j*dist_ejes_x,0,cat,label],[cerox+k,ceroy+mark_lon-j*dist_ejes_x,0,cat,label]])
                    cat = cat + 1
                    continue
        if j==0: label = round(dist_orig[-1],2)
        elif j==1: label = round(dist_par[-1],2)
        elif j==2: label = round(cras[-1],2)
        elif j==3: label = round(cterr[-1],2)
        elif j==4: label = round(croja[-1],2)
        else: label = 0
        mark_x.append([[cerox+puntos[-1][4],ceroy-mark_lon-j*dist_ejes_x,0,cat,label],[cerox+puntos[-1][4],ceroy+mark_lon-j*dist_ejes_x,0,cat,label]])
        cat = cat + 1

    ptos_eje = [[cerox+p[4],p[5]*escala-cero_y_ref,0,p[3],p[4],p[6]] for p in table_alz]

    return eje_x, eje_y, mark_x, mark_y, ptos_terr_ref, ptos_eje, ASeg_ref, APtos_caract_ref


def gen_TransProfile(Trans, Trans_Terr, Trans_Pklist, secc, escala, opt1, opt2):

    cerox = 0
    ceroy = 0

    mark_lon,mark_x_dist,mark_y_dist = [ int(p) for p in opt1.split(',')]
    #mark_lon,mark_x_dist,mark_y_dist = int(mark_lon),int(mark_x_dist),int(mark_y_dist)

    filas,sep_x,sep_y = [int(p) for p in opt2.split(',')]
    #filas,sep_x,sep_y = int(filas),float(sep_x),float(sep_y)

    columnas = len(Trans_Pklist) / float(filas)
    columnas = int(ceil(columnas))
    # Ancho y alto de cada fila/columna
    h = 0
    ancho_colum,centro_secc,max_filas,min_filas,dif_filas = [],[],[],[],[]
    for j in range (0,columnas):
        anchos_colum,centros_colum,maxfila,minfila,dif_fila = [],[],[],[],[]
        for i in range(0,filas):

            ancho_secc = round(sqrt((Trans[h][0][0]-Trans[h][-1][0])**2+(Trans[h][0][1]-Trans[h][-1][1])**2),6)
            centro_s = round(sqrt((Trans[h][0][0]-Trans[h][1][0])**2+(Trans[h][0][1]-Trans[h][1][1])**2),6)
            anchos_colum.append(ancho_secc)
            centros_colum.append(centro_s)

            max_trans = max([p[2] for p in secc[h]+Trans_Terr[h] if p != []])
            maxfila.append(max_trans)

            min_trans = min([p[2] for p in secc[h]+Trans_Terr[h] if p != []])
            minfila.append(min_trans)

            dif_fila.append((max_trans-min_trans)*escala)
            h = h + 1
            if h == len(Trans_Pklist):break
        ancho_colum.append(max(anchos_colum))
        centro_secc.append(max(centros_colum))
        max_filas.append(maxfila)
        min_filas.append(minfila)
        dif_filas.append(dif_fila)

    for k in range(len(dif_filas[0])-len(dif_filas[-1])):
        dif_filas[-1].append(0)

    dif_filas2 = [[row[i] for row in dif_filas] for i in range(len(dif_filas[0]))] # transpuesta
    alto_filas = [max(row) for row in dif_filas2]

    hy_tot = sum(alto_filas) + sep_y*filas
    ceroy = ceroy + hy_tot


    puntos_terr_ref,ptos_eje_ref = [],[]
    ejes_x,ejes_y,mark_x,mark_y = [],[],[],[]
    h,q,w,t = 0,0,0,0
    for j in range (0,columnas):

        sep_eje_x = sep_x/10
        # origen, final y centro del eje x
        orig_x = cerox + (sep_x*j) + sum(ancho_colum[0:j]) + sep_eje_x
        final_x = cerox + (sep_x*j) + sum(ancho_colum[0:j]) + ancho_colum[j] + sep_eje_x
        centro_x = orig_x + centro_secc[j]

        orig_y = ceroy
        for i in range(0,filas):

            cotaMax = max_filas[j][i]
            cotaMin = min_filas[j][i]
            dif_y_ref = (cotaMin)-int(cotaMin)

            # origen y final del eje y
            orig_y = orig_y - (alto_filas[i]) - sep_y
            final_y = orig_y + dif_filas[j][i] + dif_y_ref

            #cero_y_ref = (cotaMin-orig_y)-dif_y_ref

            ptos_terr = []
            b = 0
            for pto in Trans_Terr[h]:
                dist = sqrt((Trans_Pklist[h][0]-pto[0])**2 + (Trans_Pklist[h][1]-pto[1])**2)
                if dist == 0: b = 1
                if b == 0: dist = -dist
                ptos_terr.append([centro_x + dist, orig_y + (pto[2]-cotaMin)*escala + dif_y_ref,0,h+1,Trans_Pklist[h][4]])
            puntos_terr_ref.append(ptos_terr)

            ptos_eje = []
            b = 0
            for pto in secc[h]:

                if len(pto)>1:
                    dist = sqrt((Trans_Pklist[h][0]-pto[0])**2 + (Trans_Pklist[h][1]-pto[1])**2)
                    if dist == 0: b = 1
                    if b == 0: dist = -dist
                    cota_ras = orig_y + (pto[2]-cotaMin)*escala + dif_y_ref
                    t = t + 1
                    ptos_eje.append([centro_x+dist,cota_ras,0,t,h+1,Trans_Pklist[h][4],round(pto[2],2),round(dist,2)])
            ptos_eje_ref.append(ptos_eje)

            # Eje y
            ejes_y.append([[orig_x-sep_eje_x,final_y,0,h+1,"'Y'"],[orig_x-sep_eje_x,orig_y,0,h+1,"'Y'"]])
            # Eje x
            ejes_x.append([[orig_x-sep_eje_x,orig_y,0,h+1,"'X'",format_pk(Trans_Pklist[h][4])],[final_x,orig_y,0,h+1,"'X'",Trans_Pklist[h][4]]])

            # Marcas eje x desde el centro
            mark2_x,mark2_x2 = [],[]
            mark2_x.append([[orig_x,orig_y-2*mark_lon,0,q+1,-(centro_x-orig_x)],[orig_x,orig_y+2*mark_lon,0]])
            q = q + 1
            for k in range(mark_x_dist,int(centro_x-orig_x),mark_x_dist):
                mark2_x2.append([[centro_x-k,orig_y-mark_lon,0,q+1,-((centro_x-orig_x)-((centro_x-orig_x) % mark_x_dist)-k+mark_x_dist)],
                                [centro_x-k,orig_y+mark_lon,0]])
                q = q + 1
            mark2_x.extend(mark2_x2[::-1])

            mark2_x.append([[centro_x,orig_y-2*mark_lon,0,q+1,0.0],[centro_x,orig_y+2*mark_lon,0]])
            q = q + 1
            for k in range(mark_x_dist,int(final_x-centro_x),mark_x_dist):
                mark2_x.append([[centro_x+k,orig_y-mark_lon,0,q+1,float(k)],[centro_x+k,orig_y+mark_lon,0]])
                q = q + 1
            mark2_x.append([[final_x,orig_y-2*mark_lon,0,q+1,final_x-centro_x],[final_x,orig_y+2*mark_lon,0]])
            q = q + 1

            # Marcas eje y
            for k in range(0,int(final_y)-int(orig_y),int(mark_y_dist*escala)):
                w = w + 1
                mark_y.append([[orig_x-mark_lon-sep_eje_x,k+orig_y,0,w,k/escala+cotaMin-dif_y_ref],[orig_x+mark_lon-sep_eje_x,k+orig_y,0]])
            w = w + 1
            mark_y.append([[orig_x-mark_lon-sep_eje_x,final_y,0,w,round(cotaMax-dif_y_ref,2)],[orig_x+mark_lon-sep_eje_x,final_y,0]])
            mark_x.extend(mark2_x)


            h = h + 1
            if h == len(Trans_Pklist):break

    return ejes_x, ejes_y, mark_x, mark_y, puntos_terr_ref, ptos_eje_ref


# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

#-----------------------------------------------------------------------------


def write_Plant(segmentos, puntos_caract, puntos_centros, EjeMap, ext):

    write_Polylines(segmentos, EjeMap+ext,1)
    g.run_command('v.db.addtable', map=EjeMap+ext, layer=1, key='cat', table=EjeMap+ext,
                  columns='pk double, type varchar(25), long double, \
                  param double, azimut double, GRASSRGB varchar(12)', quiet=True)
    puntos_s = [m for p in puntos_centros for m in p[1:]]
    update_Layer(EjeMap,ext,'',puntos_s,'pk,type,long,param,azimut')

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=2, key='cat2', table=EjeMap+ext+'_PC',
                  columns='pk double, azimut double, type varchar(25), scat int', quiet=True)
    update_Table(EjeMap+ext,'_PC',2,puntos_caract,'pk,azimut,type,scat')

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=3, key='cat3', table=EjeMap+ext+'_Centers',
                  columns='type varchar(25), scat int', quiet=True)
    puntos_c = [p[0] for p in puntos_centros[:-1]]
    update_Table(EjeMap+ext,'_Centers',3,puntos_c,'type,scat')
    return 0


def write_Alz(asegmentos, p_caract, p_vert, EjeMap,ext):

    write_Polylines(asegmentos,EjeMap+ext,1)

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=1, key='cat', table=EjeMap+ext,
                  columns='pk double, type varchar(25), long double, \
                  param double, GRASSRGB varchar(12)', quiet=True)
    puntos_s = [m for p in p_vert for m in p[1:]]
    update_Layer(EjeMap,ext,'',puntos_s,'pk,type,long,param')

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=2, key='cat2', table=EjeMap+ext+'_PC',
                  columns='pk double, type varchar(25), scat int', quiet=True)
    update_Table(EjeMap+ext,'_PC',2,p_caract,'pk,type,scat')

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=3, key='cat3', table=EjeMap+ext+'_Vert',
                  columns='type varchar(25), scat int', quiet=True)
    puntos_c = [p[0] for p in p_vert[:-1]]

    update_Table(EjeMap+ext,'_Vert',3,puntos_c,'type,scat')
    return 0

def write_Despl(dlines_izq, dlines_der, p_caract, p_vert, EjeMap, ext):

    dlines = deepcopy(dlines_izq)
    dlines2 =  deepcopy(dlines_der)
    dlines.extend(dlines2)

    write_Polylines(dlines,EjeMap+ext,1)
    sdlines,cats = splitdlines(dlines)

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=1, key='cat', table=EjeMap+ext,
                  columns='long double, param double, GRASSRGB varchar(12)', quiet=True)
    puntos_s = [p[-1][:3]+[cats[i]]+[p[-1][4]] for i,p in enumerate(sdlines)]
    update_Layer(EjeMap,ext,'',puntos_s,'long')

    g.run_command('v.db.addtable', map=EjeMap+ext, layer=2, key='cat2', table=EjeMap+ext+'_PC',
                  columns='pk double, azimut double, type varchar(25), scat int', quiet=True)
    update_Table(EjeMap+ext,'_PC',2,p_caract,'pk,azimut,type,scat')

    return 0


def write_Transv(lines, trans_Pklist, p_vert, EjeMap, ext):

    write_Polylines(lines,EjeMap+ext,1)
    g.run_command('v.db.addtable', map=EjeMap+ext, layer=1, key='cat', table=EjeMap+ext,
                  columns='pk varchar(25), azimut double, type varchar(25),x double, y double, z double, GRASSRGB varchar(12)', quiet=True)
    #puntos_s = [pto[:9] for line in lines for pto in line if len(pto)>8]
    puntos_s = [pto[:3]+[i+1]+[format_pk(pto[4])]+[pto[5]]+["'"+pto[6]+"'"]+pto[:3] for i,pto in enumerate(trans_Pklist)]

    update_Layer(EjeMap,ext,'',puntos_s,'pk,azimut,type,x,y,z')

    return 0

def splitdlines(lines):

    # line = [[],[],...]
    #[[line11,[],line12,...],line3,line4,...] --> [line11,line12,line3,line4,...]
    #                                         --> [   1 ,    1 ,    2 ,   3 ,...]
    tolines,cats = [],[]
    for j,line in enumerate(lines):
        for h,pt in enumerate(line):
            if len(pt) == 1:
                line[h] = []
        if [] in line:
            splitlist = [list(group) for k, group in groupby(line, lambda x: x == []) if not k] # split list
            tolines.extend(splitlist)
            for i in range(len(splitlist)):
                cats.append(j+1)
        else:
            tolines.append(line)
            cats.append(j+1)

    return tolines,cats


#### ############## Out maps #### ##################

def write_Polylines(lines, name, layer):

    sal_linea = ""
    #if layer > 1:  tool = "add"
    #else:  tool = "create"
    tolines,cats = splitdlines(lines)

    for j,line in enumerate(tolines):
        sal_linea += "L " + str(len(line)) + " 1\n"
        for pto in line:
            sal_linea += str(pto[0]) + " " + str(pto[1]) + " " + str(pto[2]) + "\n"
        sal_linea += str(layer) + " " + str(cats[j]) + "\n"

    g.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea,
                    input='-', format='standard', overwrite=True, quiet=True)
    #g.write_command('v.edit', flags='n', tool=tool, map=name, input='-', stdin=sal_linea, overwrite=True, quiet=True)
    return 0

def write_PtosPoints(lines, name):

    sal_puntos = ""
    i = 0
    for j,line in enumerate(lines):
        for pp in line:
            if len(pp)==1 or pp == []: continue
            sal_puntos += str(i)+"|"+str(pp[4])+"|"+str(pp[5])+"|"+str(pp[6])+"|"+str(pp[0])+"|"+str(pp[1])+"|"+str(pp[2])+"\n"
            i = i + 1
    g.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_puntos, input='-',
                    columns='cat int, PK double, Az double, Type varchar(25), x double, y double, z double',
                    x=5, y=6, z=7, cat=1, overwrite=True, quiet=True)
    return 0

def write_Points(puntos, name):

    sal_puntos = ""
    for i,pp in enumerate(puntos):
        #if len(pp)==6: pp[4]=pp[5]
        sal_puntos += str(i)+"|"+str(pp[4])+"|"+str(pp[5])+"|"+str(pp[6])+"|"+str(pp[0])+"|"+str(pp[1])+"|"+str(pp[2])+"\n"
    g.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_puntos, input='-',
                    columns='cat int, PK double, Az double, Type varchar(25), x double, y double, z double',
                    x=5, y=6, z=7, cat=1, overwrite=True, quiet=True)
    return 0

def write_Polyline(puntos, name):

    # Write Polyline
    sal_linea = "L "+str(len(puntos))+" 1\n"
    for i,pp in enumerate(puntos):
        sal_linea += str(pp[0])+" "+str(pp[1])+" "+str(pp[2])+"\n"
    sal_linea += "1 1\n"
    g.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea,
                    input='-', format='standard', overwrite=True, quiet=True)
    return 0

def write_Polygon(puntos, name):

    # Write Polygon
    sal_linea = "B "+str(len(puntos)+1)+" 1\n"
    h = 0
    for pp in puntos:
        if pp==[]: h = h + 1; continue
        sal_linea += str(pp[0])+" "+str(pp[1])+"\n"

    sal_linea += str(puntos[0][0])+" "+str(puntos[0][1])+"\n"
    sal_linea += "1 1\n"
    #print sal_linea
    g.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea,
                        input='-', format='standard', overwrite=True, quiet=True)
    return 0

def write_Polygonos(lines, name, cat):

    sal_linea = ""
    for j,line in enumerate(lines):
        longLine = 1
        sal_linea2 = ""
        for i,pp in enumerate(line):
            if len(pp) > 1:
                longLine += 1
                sal_linea2 += str(pp[0])+" "+str(pp[1])+"\n"

        sal_linea += "B "+str(longLine)+" 1\n"
        sal_linea += sal_linea2
        sal_linea += str(line[0][0])+" "+str(line[0][1])+"\n"
        if cat:
            sal_linea += "1 "+str(cat)+"\n"
        else:
            sal_linea += "1 "+str(j+1)+"\n"

    g.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea,
                        input='-', format='standard', overwrite=True, quiet=True)
    return 0




# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

def read_Table2(EjeMap, layer, columns):

    tableD = dict()
    cols = ['x','y','z','cat']+columns.split(',')
    table = g.read_command('v.out.ascii', input=EjeMap, output='-',
                       format='point', layer=layer, columns=columns, quiet=True)
    table = [d.split('|') for d in table.splitlines(0)]
    if len(table[0]) < len(columns.split(',')) + 4:
        for i in range(len(table)):
            table[i].insert(2,0.0)
    table = [[row[i] for row in table] for i in range(len(table[0]))]
    for i,key in enumerate(cols):
        tableD[key] = table[i]

    return tableD


def read_Table(EjeMap, layer, columns):

    table = g.read_command('v.out.ascii', input=EjeMap, output='-',
                       format='point', layer=layer, columns=columns, quiet=True)
    table = [d.split('|') for d in table.splitlines(0)]
    if len(table[0]) < len(columns.split(',')) + 4:
        for i in range(len(table)):
            table[i].insert(2,0.0)
    return table

def read_TablePlant(EjeMap):

    plant = read_Table(EjeMap,2,'pk_eje,radio,a_in,a_out,widening,superelev')
    for i in range(len(plant)):
        plant[i][:9] = [float(p) for p in plant[i][:9]]
    return plant

def read_TableAlz(EjeMap):

    alzado = read_Table(EjeMap,3, 'pk,elev,kv,l,b')
    alzado = float_List(alzado)
    return alzado

def read_TableSection(EjeMap):

    section = read_Table(EjeMap,4,'pk,sec_left,sec_right,type_left,type_right,cut_left,cut_right,fill_left,fill_right')
    for i in range(len(section)):
        section[i][:5] = [float(p) for p in section[i][:5]]
    return section

def read_TableTransv(EjeMap):

    trans = read_Table(EjeMap,5,'pk,dist_left,dist_right,npk')
    trans = float_List(trans)
    return trans

def read_TableMarks(EjeMap):

    marks = read_Table(EjeMap,6,'pk,dists,elevs,name')
    for i in range(len(marks)):
        marks[i][:5] = [float(p) for p in marks[i][:5]]
    return marks


#-----------------------------------------------------------------------------

def remove_Layer(EjeMap, ext, layer):

    g.write_command('db.execute', database = database1, driver = 'sqlite',
                 stdin="DELETE FROM "+EjeMap+ext+" WHERE cat"+str(layer)+">=0",
                 input='-', quiet=True)
    g.run_command('v.edit', map=EjeMap, layer=layer, tool='delete',
                  cats='0-100000', quiet=True)
    return 0

def remove_Plant(EjeMap):

    remove_Layer(EjeMap, '_Plan', 2)
    return 0

def remove_Alz(EjeMap):

    remove_Layer(EjeMap, '_Vertical', 3)
    return 0

def remove_Section(EjeMap):

    remove_Layer(EjeMap, '_Section', 4)
    return 0

def remove_Transv(EjeMap):

    remove_Layer(EjeMap, '_Transv', 5)
    return 0

def remove_Marks(EjeMap):

    remove_Layer(EjeMap, '_Marks', 6)
    return 0

#-----------------------------------------------------------------------------

def update_Table(EjeMap, ext, layer, ptsList, columns):

    input_Points(EjeMap, layer, ptsList)
    update_Layer(EjeMap, ext, layer, ptsList, columns)
    return 0

def input_Points(EjeMap, layer, ptsList):

    sal = ''
    for i,coord in enumerate(ptsList):
        sal += 'P  1 1'+'\n'
        sal += str(coord[0])+' '+str(coord[1])+' '+str(coord[2])+'\n'
        sal += str(layer)+' '+str(coord[3])+'\n'
    #print sal
    os.system('echo "'+sal+'" | v.edit -n tool=add map='+EjeMap+' input=- --quiet')
    g.run_command('v.to.db', map=EjeMap, layer=layer, type='point',
                  option='cat', columns='cat'+str(layer), quiet=True)
    return 0

def update_Layer(EjeMap, ext, layer, ptsList, columns):

    sql = ''
    columns = columns.split(',')
    for i in range(len(ptsList)):
        sql += "UPDATE "+EjeMap+ext+" SET "
        sql += ', '.join(a + "=" +str(b) for a,b in zip(columns,ptsList[i][4:]))
        sql += " WHERE cat"+str(layer)+"="+str(ptsList[i][3])+";\n"
    #print sql
    g.write_command('db.execute', database=database1, driver='sqlite', stdin=sql, input='-', quiet=True)
    return 0


def update_TablePlan(EjeMap, ptsList):

    for i, pts in enumerate(ptsList):
        if str(ptsList[i][-1]).find("'") == -1:
            ptsList[i][-1] = "'"+ptsList[i][-1]+"'"
    update_Table(EjeMap,'_Plan',2,ptsList,'pk_eje,radio,a_in,a_out,widening,superelev')

    return 0

def update_TableAlz(EjeMap, ptsList):

    update_Table(EjeMap,'_Vertical',3,ptsList,'pk,elev,kv,l,b')
    return 0

def update_TableSection(EjeMap, ptsList):

    for i, pts in enumerate(ptsList):
        ptsList[i][5:] = ["'"+str(p)+"'" for p in ptsList[i][5:] if str(p).find("'") == -1]
    update_Table(EjeMap,'_Section',4,ptsList,'pk,sec_left,sec_right,type_left,\
                 type_right,cut_left,cut_right,fill_left,fill_right')
    return 0

def update_TableTransv(EjeMap, ptsList):

    update_Table(EjeMap,'_Transv',5,ptsList,'pk,dist_left,dist_right,npk')
    return 0

def update_TableMarks(EjeMap, ptsList):

    for i,pts in enumerate(ptsList):
        ptsList[i][5:] = ["'"+str(p)+"'" for p in ptsList[i][5:] if str(p).find("'") == -1]
    update_Table(EjeMap,'_Marks',6,ptsList,'pk,dists,elevs,name')
    return 0

#-----------------------------------------------------------------------------

def corregir_tabla(puntos_eje, tabla):

    pklist,tabla2 = [],[]
    for i,t in enumerate(tabla):
        if t[4] not in pklist:
            pklist.append(t[4])
            tabla2.append(t)
    tabla2.sort(key=lambda x: float(x[4]))
    for i in range(1,len(tabla2),1):
        if i < len(tabla2)-1:
            tabla2[i][0], tabla2[i][1] = get_PlantaXY(float(tabla2[i][4]),puntos_eje)[:2]
        tabla2[i][3] = i + 1
    tabla2[-1][4] = puntos_eje[-1][-1][7]
    tabla2[-1][0], tabla2[-1][1], tabla2[-1][2] = puntos_eje[-1][0][:3]
    return tabla2


def corrige_Alzado(puntos_eje, alz, EjeMap):

    alz_out = corregir_tabla(puntos_eje,alz)
    remove_Alz(EjeMap)
    update_TableAlz(EjeMap,alz_out)
    return 0

def corrige_Section(puntos_eje, secc, EjeMap):

    secc_out = corregir_tabla(puntos_eje,secc)
    remove_Section(EjeMap)
    update_TableSection(EjeMap,secc_out)
    return 0

def corrige_Transv(puntos_eje, trans, EjeMap):

    trans_out = corregir_tabla(puntos_eje,trans)
    remove_Transv(EjeMap)
    update_TableTransv(EjeMap,trans_out)
    return 0

def corrige_Marks(puntos_eje, marks, EjeMap):

    marks_out = corregir_tabla(puntos_eje,marks)
    remove_Marks(EjeMap)
    update_TableMarks(EjeMap,marks_out)
    return 0

#-----------------------------------------------------------------------------

def float_List(list):
    for j,punt in enumerate(list):
        for i,elem in enumerate(punt):

            if list[j][i] == '':
                list[j][i] = 0.0
            else:
                list[j][i] = float(list[j][i])
    return list


def update_EdgeMap(EjeMap):

    g.message(_("Reading polygon vertices"))
    verti = g.read_command('v.out.ascii', input=EjeMap, output='-', 
                           format='standard', layer=1)
    verti = [d.strip().split() for d in verti.splitlines(0)]
    verti = verti[11:-1]

    if len(verti[0]) == 2:
        for i in range(len(verti)):
            verti[i].append('0.0')
    verti = float_List(verti)
    pk_eje = [0.0]
    for i in range(len(verti)-1):
        pk_eje.append(sqrt((verti[i+1][0]-verti[i][0])**2+(verti[i+1][1]-verti[i][1])**2)+pk_eje[-1])

    dbs = g.vector_db(EjeMap)

    if len(dbs) == 6 : # if layers exist

        g.message(_("Reading old configuration"))
        planta = read_TablePlant(EjeMap)
        alzado = read_TableAlz(EjeMap)
        seccion = read_TableSection(EjeMap)
        transv = read_TableTransv(EjeMap)
        marks = read_TableMarks(EjeMap)

        g.message(_("Updating tables"))
        planta2 = []
        for i in range(len(pk_eje)):
            if i >= len(planta):
                planta2.append([verti[i][0],verti[i][1],verti[i][2],i+1,pk_eje[i]]+[0.0,0.0,0.0,0.0,"'aa'"])
            else:
                planta2.append([verti[i][0],verti[i][1],verti[i][2],i+1,pk_eje[i]]+planta[i][5:])

        alzado[0][:5] = verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0]
        alzado[-1][:5] = verti[-1][0],verti[-1][1],verti[-1][2],len(alzado),pk_eje[-1]

        seccion[0][:5] = verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0]
        seccion[-1][:5] = verti[-1][0],verti[-1][1],verti[-1][2],len(seccion),pk_eje[-1]

        transv[0][:5] = verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0]
        transv[-1][:5] = verti[-1][0],verti[-1][1],verti[-1][2],len(transv),pk_eje[-1]

        marks[0][:5] = verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0]
        marks[-1][:5] = verti[-1][0],verti[-1][1],verti[-1][2],len(marks),pk_eje[-1]

        #g.message(_("Deleting old tables"))
        remove_Plant(EjeMap)
        update_TablePlan(EjeMap, planta2)

        remove_Alz(EjeMap)
        update_TableAlz(EjeMap, alzado)

        remove_Section(EjeMap)
        update_TableSection(EjeMap, seccion)

        remove_Transv(EjeMap)
        update_TableTransv(EjeMap, transv)

        remove_Marks(EjeMap)
        update_TableMarks(EjeMap, marks)

    else:

        namesdbs = []
        for k,v in dbs.items():
            namesdbs.append(v['name'])

        if EjeMap + '_Plan' not in namesdbs:
            g.message(_("Adding table"+EjeMap+'_Plan'))
            g.run_command('v.db.addtable', map=EjeMap, layer=2, key='cat2', table=EjeMap+'_Plan',
                      columns='pk_eje double, radio double, a_in double, \
                      a_out double, widening double, superelev varchar(10)', quiet=True)
            g.message(_("Updating table "+EjeMap+'_Plan'))
            planta = []
            for i in range(len(pk_eje)):
                planta.append([verti[i][0],verti[i][1],verti[i][2],i+1,pk_eje[i],0.0,0.0,0.0,0.0,"'aa'"])
            update_TablePlan(EjeMap, planta)

        if EjeMap + '_Vertical' not in namesdbs:
            g.message(_("Adding table"+EjeMap+'_Vertical'))
            g.run_command('v.db.addtable', map=EjeMap, layer=3, key='cat3', table=EjeMap+'_Vertical',
                          columns='pk double, elev double, \
                          kv double, l double, b double', quiet=True)
            g.message(_("Updating table "+EjeMap+'_Vertical'))
            alzado = [[verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0],0.0,0.0,0.0,0.0],
                    [verti[-1][0],verti[-1][1],verti[-1][2],2,pk_eje[-1],0.0,0.0,0.0,0.0]]
            update_TableAlz(EjeMap, alzado)

        if EjeMap + '_Section' not in namesdbs:
            g.message(_("Adding table"+EjeMap+'_Section'))
            g.run_command('v.db.addtable', map=EjeMap, layer=4, key='cat4', table=EjeMap+'_Section',
                      columns='pk double, sec_left varchar(25), sec_right varchar(25), \
                      type_left varchar(25), type_right varchar(25), \
                      cut_left varchar(25), cut_right varchar(25), fill_left varchar(25), \
                      fill_right varchar(25)', quiet=True)
            g.message(_("Updating table "+EjeMap+'_Section'))
            seccion = [[verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0],'','','','','','',''],
		     [verti[-1][0],verti[-1][1],verti[-1][2],2,pk_eje[-1],'','','','','','','']]
            update_TableSection(EjeMap, seccion)

        if EjeMap + '_Transv' not in namesdbs:
            g.message(_("Adding table"+EjeMap+'_Transv'))
            g.run_command('v.db.addtable', map=EjeMap, layer=5, key='cat5', table=EjeMap+'_Transv',
                      columns='pk double, dist_left double, dist_right double, npk double', quiet=True)
            g.message(_("Updating table "+EjeMap+'_Transv'))
            transv = [[verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0],0.0,0.0,0.0],
		    [verti[-1][0],verti[-1][1],verti[-1][2],2,pk_eje[-1],0.0,0.0,0.0]]
            update_TableTransv(EjeMap, transv)

        if EjeMap + '_Marks' not in namesdbs:
            g.message(_("Adding table"+EjeMap+'_Marks'))
            g.run_command('v.db.addtable', map=EjeMap, layer=6, key='cat6', table=EjeMap+'_Marks',
                      columns='pk double, dists varchar(25), elevs varchar(25), name varchar(25)', quiet=True)
            g.message(_("Updating table "+EjeMap+'_Marks'))
            marks = [[verti[0][0],verti[0][1],verti[0][2],1,pk_eje[0],"'d'","'e'","'n'"],
                   [verti[-1][0],verti[-1][1],verti[-1][2],2,pk_eje[-1],"'d'","'e'","'n'"]]
            update_TableMarks(EjeMap, marks)


#------------------------------------------------------------------------------


def lista_PksEje(Puntos_Eje, Puntos_EjeAlz, puntos, table_alz, table_secc, table_transv):

    pkpuntos = [round(p[4],6) for p in puntos]
    for alz in table_secc + table_transv:
        if round(alz[4],6) not in pkpuntos:
            pkpuntos.append(alz[4])
            x,y,z,cat,PK,Az,tipo,align = get_PlantaXY(round(alz[4],6),Puntos_Eje)[:8]
            z = get_Cota([[x,y,z,cat,PK,Az,tipo,align]],Puntos_EjeAlz)[0][2]
            puntos.append([x,y,z,cat,PK,Az,tipo,align])

    puntos.sort(key=lambda x: x[4])
    for i,pp in enumerate(puntos):
        puntos[i][3] = i

    return puntos


# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #
# ### Main
# ###

def main():

    global database1, MapSet, driver
    global xref, yref, xres, yres
    MapSet = g.gisenv()['MAPSET']

    EjeMap = options['edge']
    if '@' in EjeMap:
        NameMap,MapSet = EjeMap.split('@')
    else:
        NameMap = EjeMap


    if g.find_file(EjeMap, element = 'vector', mapset = MapSet)['file'] is '':
        g.fatal(_("Vector map %s not found in current mapset") % options['edge'])
    try:
        f = g.vector_db(options['edge'])[1]
    except KeyError:
        #g.fatal(_("There is no table connected to this map. \
                      #Run v.db.connect or v.db.addtable first."))
        g.message(_("There is no table connected to this map. Adding table in layer 1."))
        g.run_command('v.db.addtable', map=EjeMap, quiet=True)
        f = g.vector_db(options['edge'])[1]

    table = f['table']
    database1 = f['database']
    driver = f['driver']

    #g.message(_("Creating backup"))
    #g.run_command('g.rename', vector = NameMap+"_old"+","+NameMap+"_old2")
    #g.run_command('g.copy', vector = NameMap+","+NameMap+"_old")
    #g.run_command('g.remove', flags='bf', type='vector', name=NameMap+"_old2")
    #g.message(_("Finish backup"))


#### Edges section ####

    if flags['i']:

        pklist = options["pklist"].split(",")
        pklist = [float(p) for p in pklist]
        pklist.sort()

        if options["pklayer"] == "Vertical":
            table = read_TableAlz(NameMap)
        elif options["pklayer"] == "Section":
            table = read_TableSection(NameMap)
        elif options["pklayer"] == "Trans":
            table = read_TableTransv(NameMap)
        elif options["pklayer"] == "Marks":
            table = read_TableMarks(NameMap)
        else:
            g.message(_("Layer no editable"))

        tablepks = []
        for i, line in enumerate(table):
            tablepks.append(line[4])
        pklist2 = []
        for p in pklist:
            if p not in tablepks and p < tablepks[-1]: pklist2.append(p)

        if pklist2 != []:

            tablepks = tablepks + pklist2
            tablepks.sort()
            posi = tablepks.index(pklist2[0])
            table2 = []
            categ = len(table) + 1

            secleft,secright = "",""
            typeleft,typeright = "",""

            table_plant = read_TablePlant(NameMap)
            Puntos_Eje = get_PtosEjePlanta(table_plant)

            if options["pklayer"] == "Vertical":
                for i,pk in enumerate(pklist2):
                    table2.append([table[posi-1][0]+i,table[posi-1][1]+i,table[posi-1][2]+i,categ+i,pk]+[table[posi-1][5]]+[0,0,0])
                update_TableAlz(NameMap, table2)
                table_alz = read_TableAlz(NameMap)
                corrige_Alzado(Puntos_Eje, table_alz, NameMap)

            elif options["pklayer"] == "Section":
                for i,pk in enumerate(pklist2):
                    secleft,typeleft,secright,typeright = '','','',''
                    for num in range(len(table[posi-1][5].split(';'))):
                        secleft += "-1 0;"
                        typeleft += "l;"
                    secleft = secleft[:-1]
                    typeleft = typeleft[:-1]
                    for num in range(len(table[posi-1][6].split(';'))):
                        secright += "-1 0;"
                        typeright += "l;"
                    secright = secright[:-1]
                    typeright = typeright[:-1]
                    table2.append([table[posi-1][0]+i,table[posi-1][1]+i,table[posi-1][2]+i,categ+i,pk]+[secleft,secright,typeleft,typeright]+['1','1','1','1'])
                update_TableSection(NameMap, table2)
                table_secc = read_TableSection(NameMap)
                corrige_Section(Puntos_Eje, table_secc, NameMap)

            elif options["pklayer"] == "Trans":
                for i,pk in enumerate(pklist2):
                    table2.append([table[posi-1][0]+i,table[posi-1][1]+i,table[posi-1][2]+i,categ+i,pk]+table[posi-1][5:])
                update_TableTransv(NameMap, table2)
                table_transv = read_TableTransv(NameMap)
                corrige_Transv(Puntos_Eje, table_transv, NameMap)

            elif options["pklayer"] == "Marks":
                for i,pk in enumerate(pklist2):
                    table2.append([table[posi-1][0]+i,table[posi-1][1]+i,table[posi-1][2]+i,categ+i,pk]+table[posi-1][5:])
                update_TableMarks(NameMap, table2)
                table_marks = read_TableMarks(NameMap)
                corrige_Marks(Puntos_Eje, table_marks, NameMap)

        else: g.message(_("Pk exist or list empty"))


    if flags['n']:

        g.message(_("Creating/Updating polygon map"))
        update_EdgeMap(NameMap)


    if flags['u']:

        g.message(_("Reading polygon tables"))
        ### Lectura tablas eje

        table_plant = read_TablePlant(NameMap)
        Puntos_Eje = get_PtosEjePlanta(table_plant)

        table_alz = read_TableAlz(NameMap)
        corrige_Alzado(Puntos_Eje, table_alz, NameMap)
        table_alz = read_TableAlz(NameMap)

        table_secc = read_TableSection(NameMap)
        corrige_Section(Puntos_Eje, table_secc, NameMap)
        table_secc = read_TableSection(NameMap)

        table_transv = read_TableTransv(NameMap)
        corrige_Transv(Puntos_Eje, table_transv, NameMap)
        table_transv = read_TableTransv(NameMap)

        table_marks = read_TableMarks(NameMap)
        corrige_Marks(Puntos_Eje, table_marks, NameMap)
        table_marks = read_TableMarks(NameMap)

        ######################################################################
        g.message(_("Generating alings"))

        Puntos, Segmentos, Puntos_caract, Puntos_centros = generate_Pts(Puntos_Eje,1,1,1,int(options['intervr']),int(options['intervc']))
        Puntos_EjeAlz = get_PtosEjeAlzado(table_alz)

        Puntos = get_Cota(Puntos, Puntos_EjeAlz)

        Puntos_caract = get_Cota(Puntos_caract, Puntos_EjeAlz)
        #Segmentos = get_Cota(Segmentos,Puntos_EjeAlz,0)
        Puntos2 = lista_PksEje(Puntos_Eje,Puntos_EjeAlz,Puntos[:],table_alz,table_secc,table_transv)

        ASegmentos, APuntos_caract, APuntos_vert = generate_PtsAlz(Puntos2, Puntos_Eje, Puntos_EjeAlz)

        Desplazados_izq, Desplazados_der, DPtos_caract = generate_Desplaz(table_plant, table_secc, Puntos2)

        Desplaz_Areas = generate_DesplazAreas(Desplazados_izq[:], Puntos2[:], Desplazados_der[:])

        Transversales, Trans_Pklist = generate_Transv(Puntos, table_transv)

        Transv_Despl = get_TransDespl(Transversales, Desplazados_izq[:], Desplazados_der[:])

        Transv_Discr =  discr_Lines(Transv_Despl, 1)

        T_Pklist = [p[4] for p in Trans_Pklist]

        ######################################################################
        g.message(_("Writing Plant/Raised/Section maps"))

        if flags['y']:
            #write_Points(Puntos,name+"_Ptos")
            if re.search(r'^_', options['plantpoly']): name1 = NameMap + options['plantpoly']
            else: name1 = options['plantpoly']
            write_Polyline(Puntos, name1)

        if flags['h']:
            if re.search(r'^_', options['plant']): name1 = NameMap + options['plant']
            else: name1 = options['plant']
            write_Plant(Segmentos, Puntos_caract, Puntos_centros, name1,'')

        if flags['v']:
            if re.search(r'^_', options['raised']): name1 = NameMap + options['raised']
            else: name1 = options['raised']
            write_Alz(ASegmentos, APuntos_caract, APuntos_vert, name1,'')

        if flags['d']:
            if re.search(r'^_', options['displ']): name1 = NameMap + options['displ']
            else: name1 = options['displ']
            write_Despl(Desplazados_izq, Desplazados_der, DPtos_caract, [], name1, '')

        if flags['a']:
            if re.search(r'^_', options['displ_area']): name1 = NameMap + options['displ_area']
            else: name1 = options['displ_area']
            if Desplaz_Areas != []:
                write_Polygonos(Desplaz_Areas, NameMap+"_tmp2", 0)
                g.run_command('v.centroids', input=NameMap+"_tmp2", output=name1, overwrite=True, quiet=True)
                g.run_command('g.remove', flags='f', type='vector', name=NameMap+"_tmp2", quiet=True)

        if flags['c']:

            if re.search(r'^_', options['cross']): name1 = NameMap + options['cross']
            else: name1 = options['cross']

            write_Transv(Transv_Despl, Trans_Pklist, [], name1, '')

        if flags['r']:

            conj = []
            displ_opt = options['displ_opt'].split(',')

            if Desplazados_izq != []:
                if 'displ_left0' in displ_opt:
                    conj.append([pto for pto in Desplazados_izq[0] if pto != [] and pto[-1] in T_Pklist])

                if 'displ_left-1' in displ_opt:
                    conj.append([pto for pto in Desplazados_izq[-1] if pto != [] and pto[-1] in T_Pklist])

            if Desplazados_der != []:
                if 'displ_rigth0' in displ_opt:
                    conj.append([pto for pto in Desplazados_der[0] if pto != [] and pto[-1] in T_Pklist])

                if 'displ_rigth-1' in displ_opt:
                    conj.append([pto for pto in Desplazados_der[-1] if pto != [] and pto[-1] in T_Pklist])

            if re.search(r'^_', options['crossdispl']): name1 = NameMap + options['crossdispl']
            else: name1 = options['crossdispl']
            write_PtosPoints(conj, name1)

        if flags['k']:

            npk, mpk, dist, m = options['pkopt'].split(',')
            npk, mpk, dist, m = int(npk),int(mpk),float(dist),float(m)
            Pks, Pkslist = get_Trans(Puntos,npk,mpk,m,dist,dist,dist,dist,0,0,int(Puntos[-1][4]))

            if re.search(r'^_', options['pks']): name1 = NameMap + options['pks']
            else: name1 = options['pks']
            write_Transv(Pks, Trans_Pklist, [], name1, '')

        if flags['m']:

            nameMark = list(set([p[-1] for p in table_marks]))
            ptoslist = []
            j = 1
            for nam in nameMark:
                if nam != '':
                    ptoslist.append([])
                    for line in table_marks:
                        if nam == line[-1]:
                            ptoM = get_PlantaXY(float(line[4]), Puntos_Eje)
                            heigt = line[6].split(',')
                            dists = line[5].split(',')
                            for i,dis in enumerate(dists):

                                ptoslist[-1].append([ptoM[0]+float(dis)*sin(ptoM[5]+pi/2),
                                                     ptoM[1]+float(dis)*cos(ptoM[5]+pi/2),
                                                     get_Cota([ptoM],Puntos_EjeAlz)[0][2]+float(heigt[i]),
                                                     j,line[4],(pi-ptoM[5])*180/pi,nam])
                                j = j + 1

            if re.search(r'^_', options['marksmap']): name1 = NameMap + options['marksmap']
            else: name1 = options['marksmap']
            if ptoslist != []:
                write_PtosPoints(ptoslist, name1)

        ##################################################################
        if options['dem']:

            g.message(_("Reading terrain map"))
            Terreno_Array = get_Terrain(options['dem'])

            ##################################################################
            g.message(_("Generating terrain maps"))

            Puntos_Talud_izq,Puntos_Talud_der = generate_Taludes(Puntos2,Desplazados_izq,Desplazados_der,table_secc,Terreno_Array)

            Areas_Desm,Areas_Terr = generate_TaludesAreas(Puntos_Talud_izq,Desplazados_izq,Desplazados_der,Puntos_Talud_der)

            Transversales_Terreno = drape_LinesPoints(Transv_Discr, Terreno_Array)
            Puntos_Long_Terreno = drape_Points(Puntos, Terreno_Array)

            ##################################################################
            g.message(_("Writing terrain maps"))

            if flags['t']:
                if re.search(r'^_', options['outtlong']): name1 = NameMap + options['outtlong']
                else: name1 = options['outtlong']
                write_Polyline(Puntos_Long_Terreno, name1)

            if flags['q']:
                if re.search(r'^_', options['outtcross']): name1 = NameMap + options['outtcross']
                else: name1 = options['outtcross']
                write_Transv(Transversales_Terreno, Trans_Pklist, [], name1, '')

            if flags['s']:
                if re.search(r'^_', options['outslope']): name1 = NameMap + options['outslope']
                else: name1 = options['outslope']
                #write_Polyline(Puntos_Talud_izq,NameMap+"_Talud_izq")
                #write_Polyline(Puntos_Talud_der,NameMap+"_Talud_der")
                write_Polylines([Puntos_Talud_izq, Puntos_Talud_der], name1, 1)

            if flags['e']:
                if re.search(r'^_', options['outslopeareas']): name1 = NameMap + options['outslopeareas']
                else: name1 = options['outslopeareas']

                if Areas_Desm != []:
                    write_Polygonos(Areas_Desm, NameMap+"_tmp3", 0)
                    g.run_command('v.centroids', input=NameMap+"_tmp3", output=name1+'_Cut', overwrite=True, quiet=True)
                    g.run_command('g.remove', flags='f', type='vector', name=NameMap+"_tmp3", quiet=True)

                if Areas_Terr != []:
                    write_Polygonos(Areas_Terr, NameMap+"_tmp3", 0)
                    g.run_command('v.centroids', input=NameMap+"_tmp3", output=name1+'_Fill', overwrite=True, quiet=True)
                    g.run_command('g.remove', flags='f', type='vector', name=NameMap+"_tmp3", quiet=True)

            if flags['p']:

                if options['disptin'] != '':
                    desp1, desp2 = [], []
                    lista1 = [p + 1 for p in range(len(Desplazados_izq))]
                    lista2 = [p + len(lista1) + 1 for p in range(len(Desplazados_der))]
                    lineas = [int(p) for p in options['disptin'].split(',')]
                    for nlin in lineas:
                        if nlin in lista1:
                            desp1.append(Desplazados_izq[nlin-1])
                        if nlin in lista2:
                            desp2.append(Desplazados_der[(nlin-len(lista1))-1])
                else:
                    desp1 = Desplazados_izq
                    desp2 = Desplazados_der

                conj = []
                pts_opt = options['pts_opt'].split(',')
                if 'slope_left' in pts_opt:
                    conj.append(Puntos_Talud_izq)
                if 'displ_left' in pts_opt:
                    conj.extend(desp1)
                if 'edge' in pts_opt:
                    conj.append(Puntos2)
                if 'displ_rigth' in pts_opt:
                    conj.extend(desp2)
                if 'slope_rigth' in pts_opt:
                    conj.append(Puntos_Talud_der)

                if re.search(r'^_', options['outpoints']): name1 = NameMap + options['outpoints']
                else: name1 = options['outpoints']
                write_PtosPoints(conj, name1)

            if flags['b']:

                conj = []
                break_opt = options['break_opt'].split(',')
                if 'slope_left' in break_opt:
                    conj.append(Puntos_Talud_izq)
                if 'displ_left' in break_opt:
                    conj.extend(desp1)
                if 'edge' in break_opt:
                    conj.append(Puntos2)
                if 'displ_rigth' in break_opt:
                    conj.extend(desp2)
                if 'slope_rigth' in break_opt:
                    conj.append(Puntos_Talud_der)

                if re.search(r'^_', options['outbreak']): name1 = NameMap + options['outbreak']
                else: name1 = options['outbreak']
                write_Polylines(conj, name1, 1)

            if flags['o']:

                conj = []
                hull_opt = options['hull_opt'].split(',')
                if 'slope_left' in hull_opt and 'slope_rigth' in hull_opt:
                    conj = generate_ContornoAreas(Puntos2,Puntos_Talud_izq,Desplazados_izq,Desplazados_der,Puntos_Talud_der)
                elif 'slope_left' in hull_opt:
                    conj = rellenar_linea(Puntos2, Puntos_Talud_izq, Desplazados_izq)
                elif 'slope_rigth' in hull_opt:
                    conj = rellenar_linea(Puntos2, Puntos_Talud_der, Desplazados_der)

                if re.search(r'^_', options['outhull']): name1 = NameMap + options['outhull']
                else: name1 = options['outhull']
                write_Polygon(conj, NameMap+"_tmp1")

                g.run_command('v.centroids', input=NameMap+"_tmp1", output=name1, overwrite=True, quiet=True)
                #g.run_command('v.to.rast', input=NameMap+"_Contorno", output=options['outhull'], use='val', overwrite=True, quiet=True)
                g.run_command('g.remove', flags='f', type='vector', name=NameMap+"_tmp1", quiet=True)

            ##################################################################

            if flags['l']:

                scale = float(options['lpscale'])
                opt1 = options['lpopt']

                if re.search(r'^_', options['lpterrain']): nameTerr = NameMap + options['lpterrain']
                else: nameTerr = options['lpterrain']

                if re.search(r'^_', options['lpras']): nameRas = NameMap + options['lpras']
                else: nameRas = options['lpras']

                (eje_x, eje_y, mark_x, mark_y, ptos_terr_ref, ptos_eje_ref, ASeg_ref,
                APtos_caract_ref) = gen_LongProfileGuitarr(ASegmentos,APuntos_caract,Puntos,Puntos_Long_Terreno,table_alz,scale,opt1)

                # Terreno alzado
                write_Polyline(ptos_terr_ref, nameTerr)
                #write_Polyline(ptos_ref,nameRas)

                # Eje alzado
                if re.search(r'^_', options['lpejeref']): nameEdgeRef = NameMap + options['lpejeref']
                else: nameEdgeRef = options['lpejeref']

                write_Polyline(ptos_eje_ref, nameEdgeRef)
                g.run_command('v.db.addtable', map=nameEdgeRef, layer=1, key='cat', table=nameEdgeRef+"_Lin", columns='label varchar(25)', quiet=True)
                g.run_command('v.db.addtable', map=nameEdgeRef, layer=2, key='cat2', table=nameEdgeRef+"_Ptos", columns='pk double,slope double,kv double', quiet=True)

                update_Table(nameEdgeRef, '_Ptos', 2, ptos_eje_ref[1:-1], 'pk,slope,kv')

                # Segmentos alzado
                write_Polylines(ASeg_ref, nameRas, 1)

                g.run_command('v.db.addtable', map=nameRas, layer=1, key='cat', table=nameRas,
                  columns = 'pk double, type varchar(25), long double, \
                  param double, GRASSRGB varchar(12)', quiet=True)
                puntos_s=[m for p in APuntos_vert for m in p[1:]]
                update_Layer(nameRas, "", '', puntos_s, 'pk,type,long,param')

                g.run_command('v.db.addtable', map=nameRas, layer=2, key='cat2', table=nameRas+'_PC',
                  columns = 'pk double, type varchar(25), scat int', quiet=True)
                update_Table(nameRas, '_PC', 2, APtos_caract_ref, 'pk,type,scat')

                if flags['j']:

                    if re.search(r'^_', options['lpaxisx']): nameEdgeX = NameMap + options['lpaxisx']
                    else: nameEdgeX = options['lpaxisx']

                    if re.search(r'^_', options['lpaxisxmarks']): nameEdgeXmarks = NameMap + options['lpaxisxmarks']
                    else: nameEdgeXmarks = options['lpaxisxmarks']

                    if re.search(r'^_', options['lpaxisy']): nameEdgeY = NameMap + options['lpaxisy']
                    else: nameEdgeY = options['lpaxisy']

                    if re.search(r'^_', options['lpaxisymarks']): nameEdgeYmarks = NameMap + options['lpaxisymarks']
                    else: nameEdgeYmarks = options['LPedgeYmarks']

                    write_Polylines(eje_x, nameEdgeX, 1)
                    write_Polylines(mark_x, nameEdgeXmarks, 1)
                    write_Polylines(eje_y, nameEdgeY, 1)
                    write_Polylines(mark_y, nameEdgeYmarks, 1)

                    g.run_command('v.db.addtable', map=nameEdgeX, layer=1, key='cat', table=nameEdgeX+"_x", columns='label varchar(25)', quiet=True)
                    eje_x2 = [p[0] for p in eje_x]
                    update_Layer(nameEdgeX, '_x', '', eje_x2, 'label')

                    g.run_command('v.db.addtable', map=nameEdgeXmarks, layer=1, key='cat', table=nameEdgeXmarks+"_Marks", columns='label double', quiet=True)
                    mark_x2 = [p[0] for p in mark_x]
                    update_Layer(nameEdgeXmarks, '_Marks', '', mark_x2, 'label')

                    g.run_command('v.db.addtable', map=nameEdgeY, layer=1, key='cat', table=nameEdgeY+"_y", columns='label varchar(25)', quiet=True)
                    eje_y2 = [p[0] for p in eje_y]
                    update_Layer(nameEdgeY, '_y', '', eje_y2, 'label')

                    g.run_command('v.db.addtable', map=nameEdgeYmarks, layer=1, key='cat', table=nameEdgeYmarks+"_Marks", columns='label double', quiet=True)
                    mark_y2 = [p[0] for p in mark_y]
                    update_Layer(nameEdgeYmarks, '_Marks', '', mark_y2, 'label')


            if flags['f']:

                scale2 = float(options['ltscale'])
                opt1 = options['ltopt']
                opt2 = options['ltopt2']

                if re.search(r'^_', options['ltterrain']): nameTTerr = NameMap + options['ltterrain']
                else: nameTTerr = options['ltterrain']

                if re.search(r'^_', options['ltras']): nameTRas = NameMap + options['ltras']
                else: nameTRas = options['ltras']

                secc_despl = get_SeccTerr(Trans_Pklist,Desplazados_izq,Desplazados_der,Puntos_Talud_izq,Puntos_Talud_der)
                #print secc_despl
                (ejes_x, ejes_y, mark_x, mark_y, ptos_terr_ref,
                ptos_eje) = gen_TransProfile(Transversales,Transversales_Terreno,Trans_Pklist,secc_despl,scale2,opt1,opt2)

                # Terreno
                write_Polylines(ptos_terr_ref, nameTTerr, 1)

                write_Polylines(ptos_eje, nameTRas, 1)

                g.run_command('v.db.addtable', map=nameTRas, layer=1, key='cat', table=nameTRas, columns='pk varchar(25)', quiet=True)
                ptos_eje2 = [p[0][:3] + p[0][4:] for p in ptos_eje]
                update_Layer(nameTRas, '', '', ptos_eje2, 'pk')

                g.run_command('v.db.addtable', map=nameTRas, layer=2, key='cat2', table=nameTRas+"_ptos", columns='section varchar(25), pk double, elev double, dist double', quiet=True)
                ptos_eje2 = [p for line in ptos_eje for p in line]
                update_Table(nameTRas, '_ptos', 2, ptos_eje2, 'section,pk,elev,dist')

                if flags['g']:

                    if re.search(r'^_', options['ltaxisx']): nameTEdgeX = NameMap + options['ltaxisx']
                    else: nameTEdgeX = options['ltaxisx']

                    if re.search(r'^_', options['ltaxisxmarks']): nameTEdgeXmarks = NameMap + options['ltaxisxmarks']
                    else: nameTEdgeXmarks = options['ltaxisxmarks']

                    if re.search(r'^_', options['ltaxisy']): nameTEdgeY = NameMap + options['ltaxisy']
                    else: nameTEdgeY = options['ltaxisy']

                    if re.search(r'^_', options['ltaxisymarks']): nameTEdgeYmarks = NameMap + options['ltaxisymarks']
                    else: nameTEdgeYmarks = options['ltaxisymarks']

                    write_Polylines(ejes_x, nameTEdgeX, 1)
                    write_Polylines(mark_x, nameTEdgeXmarks, 1)
                    write_Polylines(ejes_y, nameTEdgeY, 1)
                    write_Polylines(mark_y, nameTEdgeYmarks, 1)

                    g.run_command('v.db.addtable', map=nameTEdgeX, layer=1, key='cat', table=nameTEdgeX+"_x", columns='label varchar(25),pk varchar(10)', quiet=True)
                    ejes_x2 = [p[0] for p in ejes_x]
                    update_Layer(nameTEdgeX, '_x', '', ejes_x2, 'label,pk')

                    g.run_command('v.db.addtable', map=nameTEdgeXmarks, layer=1, key='cat', table=nameTEdgeXmarks+"_Marks", columns='label double', quiet=True)
                    mark_x2 = [p[0] for p in mark_x]
                    update_Layer(nameTEdgeXmarks, '_Marks', '', mark_x2, 'label')

                    g.run_command('v.db.addtable', map=nameTEdgeY, layer=1, key='cat', table=nameTEdgeY+"_y", columns='label varchar(25)', quiet=True)
                    eje_y2 = [p[0] for p in ejes_y]
                    update_Layer(nameTEdgeY, '_y', '', eje_y2, 'label')

                    g.run_command('v.db.addtable', map=nameTEdgeYmarks, layer=1, key='cat', table=nameTEdgeYmarks+"_Marks", columns='label double', quiet=True)
                    mark_y2 = [p[0] for p in mark_y]
                    update_Layer(nameTEdgeYmarks, '_Marks', '', mark_y2, 'label')



###########################################################################

    sys.exit(0)

#if __name__ == "__main__":
    #options, flags = g.parser()
    #main()

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == '--doctest':
        import doctest
        doctest.testmod()
    else:
        options, flags = g.parser()
        main()
