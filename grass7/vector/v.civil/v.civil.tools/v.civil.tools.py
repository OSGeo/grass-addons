#!/usr/bin/env python
# -*- coding: utf-8
############################################################################
#
# MODULE:       v.civil.tools, v0.5.0
#
# AUTHOR:       Jesús Fernández-Capel Rosillo
#               Civil Engineer, Spain
#               jfc at alcd net
#
# PURPOSE:      Road tools for use with v.civil.road
#
# COPYRIGHT:    (c) 2014 Jesús Fernández-Capel Rosillo.
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Road tool for use with v.civil.road
#% keywords: vector, Road, civil
#%end

#### Input section ####

#%option G_OPT_V_OUTPUT
#% key: outmap
#% description: Name for output map
#% required: yes
#%end



#### Curves section ####

#%flag
#% key: c
#% description: Generate align
#% guisection: Align
#%end


#%option
#% key: cradio1
#% type: double
#% description: Radio of curve1
#% required: no
#% guisection: Align
#%end

#%option G_OPT_M_COORDS
#% key: ccenter
#% description: Center of curve1
#% required: no
#% guisection: Align
#%end

#%option
#% key: casal1
#% type: double
#% description: Parameter A of clothoid out
#% required: no
#% guisection: Align
#%end

#%option G_OPT_M_COORDS
#% key: cpoint1
#% type: string
#% description: Point of curve1
#% required: no
#% guisection: Align
#%end

#%option
#% key: cradio2
#% type: string
#% description: Radios of curve2
#% required: no
#% guisection: Align
#%end

#%option
#% key: caent2
#% type: string
#% description: Parameter A of clothoid in
#% required: no
#% guisection: Align
#%end

#%option
#% key: casal2
#% type: string
#% description: Parameter A of clothoid out
#% required: no
#% guisection: Align
#%end

#%option
#% key: len2
#% type: string
#% description: Longitud of alignment
#% required: no
#% guisection: Align
#%end


#### Round section ####

#%flag
#% key: r
#% description: Write roundabout edge
#% guisection: Round
#%end

#%option
#% key: rround1
#% type: string
#% description: Minus radio for roundabout edge
#% required: no
#% guisection: Round
#%end

#%option
#% key: rround2
#% type: string
#% description: Mayor radio for roundabout edge
#% required: no
#% guisection: Round
#%end

#%option
#% key: azround
#% type: string
#% description: Azimut for roundabout start point
#% required: no
#% guisection: Round
#%end

#%option
#% key: cround
#% type: string
#% description: Center for roundabout
#% required: no
#% guisection: Round
#%end


##### Tools section ####

##%flag
##% key: o
##% description: Calculate cross point of two straights
##% guisection: Tools
##%end

##%flag
##% key: t
##% description: Calculate tangencial point of a straight and a circle
##% guisection: Tools
##%end

##%flag
##% key: l
##% description: along a straight
##% guisection: Tools
##%end

##%option
##% key: tcenter
##% type: string
##% description: Center of circle
##% required: no
##% guisection: Tools
##%end

##%option
##% key: tradio
##% type: double
##% description: Radio of circle
##% required: no
##% guisection: Tools
##%end

##%option
##% key: tpoint1
##% type: string
##% description: Point 1 of straight1
##% required: no
##% guisection: Tools
##%end

##%option
##% key: tpoint2
##% type: string
##% description: Point 2 of straight1
##% required: no
##% guisection: Tools
##%end

##%option
##% key: tpoint3
##% type: string
##% description: Point 1 of straight2
##% required: no
##% guisection: Tools
##%end

##%option
##% key: tpoint4
##% type: string
##% description: Point 2 of straight2
##% required: no
##% guisection: Tools
##%end

##%option
##% key: dist
##% type: double
##% description: Distance to along
##% required: no
##% guisection: Tools
##%end

#### Street section ####

#%flag
#% key: s
#% description: Curve between two straights
#% guisection: Street1
#%end

#%option
#% key: sradio
#% type: double
#% description: Radio of circle for intersection
#% required: no
#% guisection: Street1
#%end

#%option
#% key: spoint1
#% type: string
#% description: Point 1 of straight1
#% required: no
#% guisection: Street1
#%end

#%option
#% key: spoint2
#% type: string
#% description: Point 2 of straight1
#% required: no
#% guisection: Street1
#%end

#%option
#% key: lado1
#% type: string
#% label: left or right side
#% options: Izq,Der
#% required: no
#% guisection: Street1
#%end

#%option
#% key: dist_despl1
#% type: double
#% description: Distance displaced
#% required: no
#% guisection: Street1
#%end

#%option
#% key: pkref1
#% type: double
#% description: Fist point pk's of straight1
#% required: no
#% answer: 0
#% guisection: Street1
#%end

#%option
#% key: spoint3
#% type: string
#% description: Point 1 of straight2
#% required: no
#% guisection: Street1
#%end

#%option
#% key: spoint4
#% type: string
#% description: Point 2 of straight2
#% required: no
#% guisection: Street1
#%end

#%option
#% key: lado2
#% type: string
#% label: left or right side
#% options: Izq,Der
#% required: no
#% guisection: Street1
#%end

#%option
#% key: dist_despl2
#% type: double
#% description: Distance displaced
#% required: no
#% guisection: Street1
#%end

#%option
#% key: pkref2
#% type: double
#% description: Fist point pk's of straight2
#% required: no
#% answer: 0
#% guisection: Street1
#%end

#### Street2 section ####

#%flag
#% key: h
#% description: Curve between a straight and a roundabout
#% guisection: Street2
#%end

#%option
#% key: inout
#% type: string
#% label: In or out from roundabout
#% options: In,Out
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hradio
#% type: double
#% description: Radio of circle for intersection
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hpoint1
#% type: string
#% description: Point 1 of straight1
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hpoint2
#% type: string
#% description: Point 2 of straight1
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hlado
#% type: string
#% label: left or right side
#% options: Izq,Der
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hdist_despl
#% type: double
#% description: Distance displaced
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hpkref
#% type: double
#% description: Fist point pk's of straight1
#% required: no
#% answer: 0
#% guisection: Street2
#%end

#%option
#% key: hcenter
#% type: string
#% description: Center of circle
#% required: no
#% guisection: Street2
#%end

#%option
#% key: hradio1
#% type: double
#% description: Radio of circle
#% required: no
#% guisection: Street2
#%end

#### Displaced section ####

#%flag
#% key: a
#% description: Add column to section and type
#% guisection: Displaced
#%end

#%flag
#% key: d
#% description: Delete column from section and type
#% guisection: Displaced
#%end

#%option G_OPT_V_INPUT
#% key: edge
#% description: Name for alignment (horizontal polygon)
#% required: no
#% guisection: Displaced
#%end

#%option
#% key: lado
#% type: string
#% label: left or right side
#% options: left,right
#% required: no
#% guisection: Displaced
#%end


#%option
#% key: ncol
#% type: integer
#% description: Number of column to insert
#% required: no
#% guisection: Displaced
#%end

#%option
#% key: startd
#% type: string
#% description: start distance and height
#% required: no
#% guisection: Displaced
#%end

#%option
#% key: endd
#% type: string
#% description: end distance and height
#% required: no
#% guisection: Displaced
#%end

import os, sys
from math import *
import grass.script as grass



###############################################################################

def splitdlines(lines):

    # line = [[],[],...]
    #[[line11,[],line12,...],line3,line4,...] --> [line11,line12,line3,line4,...]
    #                                         --> [   1 ,    1 ,    2 ,   3 ,...]
    tolines,cats=[],[]
    for j,line in enumerate(lines):
        if [] in line:
            splitlist=[list(group) for k, group in groupby(line, lambda x: x == []) if not k] # split list
            tolines.extend(splitlist)
            for i in range(len(splitlist)):
                cats.append(j+1)
        else:
            tolines.append(line)
            cats.append(j+1)

    return tolines,cats

def write_Polylines(lines,name):

    sal_linea=""

    tolines,cats=splitdlines(lines)

    for j,line in enumerate(tolines):

        sal_linea+="L "+str(len(line))+" 1\n"
        for i,pto in enumerate(line):
            sal_linea+=str(pto[0])+" "+str(pto[1])+" "+str(pto[2])+"\n"
        sal_linea+="1 "+str(cats[j])+"\n"
    #print sal_linea
    grass.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea,
                    input='-', format='standard', overwrite=True, quiet=True)
    return 0

def write_Polyline(puntos,name):

    # Write Polyline
    sal_linea="L "+str(len(puntos))+" 1\n"
    for i,pp in enumerate(puntos):
        sal_linea+=str(pp[0])+" "+str(pp[1])+" "+str(pp[2])+"\n"
    sal_linea+="1 1\n"
    grass.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea,
                    input='-', format='standard', overwrite=True, quiet=True)
    return 0

def write_edge(polygon,radios,A1,A2,outmap):

    write_Polyline(polygon,outmap)

    #grass.run_command('v.db.addtable', map=outmap, quiet=True)
    grass.run_command('v.civil.road', flags='n', edge=outmap)

    f = grass.vector_db(outmap)[1]
    table    = f['table']
    database1 = f['database']
    driver   = f['driver']

    sql = ""
    for i,ra in enumerate(radios):
        sql += "UPDATE "+outmap+"_Plan SET "
        sql += "radio="+str(ra)+", a_in="+str(A1[i])+", a_out="+str(A2[i])
        sql += " WHERE cat2="+str(i+1)+" ;\n"

    grass.write_command('db.execute', database = database1, driver = driver, stdin = sql, input='-', quiet=True)
    grass.run_command('v.civil.road', flags='hyu', edge=outmap)

    return 0

###############################################################################

def aprox_coord(L, Tau):

    n_iter=10;x=0;y=0
    for n in range(n_iter):
        x+=(((-1)**n*Tau**(2*n))/((4*n+1)*factorial(2*n)))
        y+=(((-1)**n*Tau**(2*n+1))/((4*n+3)*factorial(2*n+1)))
    x=x*L
    y=y*L
    return [x,y]

def clotoide_Locales(A,R):

    if R==0:
        L,Tau=0,0
    else:
        L=A**2/abs(R)
        Tau=L/(2*R)
    xe,ye=aprox_coord(L,Tau)
    xo=xe-R*sin(Tau)
    yo=ye+R*cos(Tau)-R
    return xo,yo,Tau,L,xe,ye

def azimut(a,b,c,d):

    if a > c and b == d: Az=3*pi/2
    elif a < c and b == d: Az=pi/2
    elif a == c and b > d: Az=pi
    elif a == c and b < d: Az=2*pi
    elif a == c and b == d: Az=0
    else: Az=atan((c-a)/(d-b))
    #if a > c and b == d: Az=Az+pi # Az>0 -> Az > 0
    if a < c and b > d: Az=Az+pi # Az<0 -> Az > 100
    elif a > c and b > d: Az=Az+pi # Az>0 -> Az > 200
    elif a > c and b < d: Az=Az+2*pi # Az<0 -> Az > 300
    return Az

def cambio_coord(x,y,Az,c,d,R):

    if R>0:
        x1=c-x*sin(Az)+y*cos(Az)
        y1=d-x*cos(Az)-y*sin(Az)
    else:
        x1=c-x*sin(Az)+y*cos(Az)
        y1=d-x*cos(Az)-y*sin(Az)
    return [x1,y1]



def recta_tg_circulo(xo,yo,R,xc,yc):

    a=(R**2-xc**2+2*xc*xo-xo**2)
    b=2*(xc*yc-xc*yo-xo*yc+xo*yo)
    c=(R**2-yc**2+2*yc*yo-yo**2)

    m1=(-b+sqrt(b**2-4*a*c))/(2*a)
    m2=(-b-sqrt(b**2-4*a*c))/(2*a)

    x1=(xc+xo*m1**2+yc*m1-yo*m1)/(m1**2+1)
    y1=-1/m1*(x1-xc)+yc

    x2=(xc+xo*m2**2+yc*m2-yo*m2)/(m2**2+1)
    y2=m2*(x2-xo)+yo

    if options['izq']=='0':
        xt,yt=x1,y1
    else: xt,yt=x2,y2

    return xt,yt


def pto_corte_2_rectas(x1,y1,x2,y2,x3,y3,x4,y4):

    if x2 == x1: m11=(y2-y1)/0.0000001
    else: m11=(y2-y1)/(x2-x1)

    if x3 == x4: m22=(y4-y3)/0.0000001
    else: m22=(y4-y3)/(x4-x3)

    x=(m11*x1-m22*x3-y1+y3)/(m11-m22)
    y=m11*(x-x1)+y1

    return x,y


def alargar_recta(x1,y1,x2,y2,d):

    Az=azimut(x1,y1,x2,y2)

    x=x2+d*sin(Az)
    y=y2+d*cos(Az)

    return x,y,x-x2,y-y2

def angulos_Alings(a,b,c,d,e,f):

    Az_ent = azimut(a,b,c,d)
    Az_sal = azimut(c,d,e,f)

    if ((a <= c and b <= d) or (a <= c and b >= d)): #1er cuadrante o 2do cuadrante

        if (Az_ent < Az_sal and Az_ent+pi < Az_sal):
            w=2*pi-abs(Az_ent-Az_sal)
        else:
            w=abs(Az_ent-Az_sal)

    if ((a >= c and b >= d) or (a >= c and b <= d)): #3er cuadrante o 4to cuadrante

        if (Az_ent > Az_sal and Az_ent-pi > Az_sal):
            w=2*pi-abs(Az_ent-Az_sal)
        else:
            w=abs(Az_ent-Az_sal)

    return Az_ent,Az_sal,w

###############################################################################

def curva_recta(center,radio,param,izq,point):

    xc,yc=center.split(',')
    xc=float(xc)
    yc=float(yc)
    R=float(radio)
    A=float(param)
    xo,yo=point.split(',')
    xo,yo=float(xo),float(yo)

    xo_ent,yo_ent,Tau_ent,Lent,xe,ye=clotoide_Locales(A,R)
    #print xo_ent,yo_ent,Tau_ent,Lent,xe,ye,A
    R1=R+yo_ent

    xt,yt=recta_tg_circulo(xo,yo,R1,xc,yc)

    xl=(R+yo_ent)*tan(Tau_ent)
    d=sqrt((xo-xt)**2+(yo-yt)**2)
    #print xl,d
    Az=azimut(xo,yo,xt,yt)

    xv=xo+(d+xl)*sin(Az)
    yv=yo+(d+xl)*cos(Az)

    x3=xv+(d+xl)*sin(Az-Tau_ent*2)
    y3=yv+(d+xl)*cos(Az-Tau_ent*2)


    write_edge([[x3,y3,0],[xv,yv,0],[xo,yo,0]],[0,R,0],[0,A,0],[0,A,0],options['outmap'].split('@')[0])

    write_Polyline([[xc,yc,0],[xt,yt,0]],'acc')
    write_Polyline([[xc,yc,0],[xv,yv,0]],'avv')

    return 0

###############################################################################

###############################################################################
def get_pts_Clot_ent(A,xad,yad,Az,Ini,Fin,L_int,R,Lacum,cat,ali):
    # Return matriz de puntos, resto
    M = []
    while Ini <= Fin:
        Rclo=A**2/(Ini)
        Tau_clo=(Ini)/(2*Rclo)
        xclo,yclo=aprox_coord((Ini),Tau_clo)
        if R>0:
            x_clo=xad-xclo*sin(-Az)+yclo*cos(-Az)
            y_clo=yad+xclo*cos(-Az)+yclo*sin(-Az)
            Az1=Az+Tau_clo
        elif R<0:
            x_clo=xad+xclo*sin(Az)-yclo*cos(Az)
            y_clo=yad+xclo*cos(Az)+yclo*sin(Az)
            Az1=Az-Tau_clo
        Lacum+=L_int
        M.append([x_clo,y_clo,0,cat,Lacum,Az1,'Clot_in',ali])
        cat=cat+1
        Ini=Ini+L_int
    return M,Fin-(Ini-L_int),Lacum,cat

def get_pts_Clot_sal(A,xda,yda,Az,Ini,Fin,L_int,R,Lacum,cat,ali):
    # Return matriz de puntos, resto
    M = []
    while Ini <= Fin:
        if Fin-Ini==0: Fin=0; Ini=Ini*-1
        Rclo=A**2/(Fin-Ini)
        Tau_clo=(Fin-Ini)/(2*Rclo)
        xclo,yclo=aprox_coord((Fin-Ini),Tau_clo)
        if R>0:
            x_clo=xda-xclo*sin(Az)+yclo*cos(Az)
            y_clo=yda-xclo*cos(Az)-yclo*sin(Az)
            Az1=Az-Tau_clo
        elif R<0:
            x_clo=xda+xclo*sin(-Az)-yclo*cos(-Az)
            y_clo=yda-xclo*cos(-Az)-yclo*sin(-Az)
            Az1=Az+Tau_clo
        Lacum+=L_int
        M.append([x_clo,y_clo,0,cat,Lacum,Az1,'Clot_out',ali])
        cat=cat+1
        Ini=Ini+L_int
    return M,Fin-(Ini-L_int),Lacum,cat

def get_pts_Curva(xc,yc,AzIni,AzFin,incremento,R,Lacum,dc,cat,ali):

    M = []
    incremento=incremento/abs(R)
    if R>0:
        if AzIni>AzFin: AzIni=AzIni-2*pi
        ii = AzIni+incremento
        while ii <= AzFin:
            x1=xc+R*sin(ii)
            y1=yc+R*cos(ii)
            Az1=(ii+pi/2)
            ii += incremento
            Lacum+=incremento*abs(R)
            if Az1>2*pi: Az1=Az1-2*pi
            M.append([x1,y1,0,cat,Lacum,Az1,'Curve',ali])
            cat=cat+1
        resto=(AzFin-(ii-incremento))*abs(R)
    elif R<0:
        if AzIni<AzFin: AzFin=AzFin-2*pi
        ii = AzIni-incremento
        while ii >= AzFin:
            x1=xc-R*sin(ii)
            y1=yc-R*cos(ii)
            Az1=(ii-pi/2)
            ii -= incremento
            Lacum+=incremento*abs(R)
            if Az1<0: Az1=Az1+2*pi
            M.append([x1,y1,0,cat,Lacum,Az1,'Curve',ali])
            cat=cat+1
        resto= ((ii+incremento)-AzFin)*abs(R)
    return M,resto,Lacum,cat

def get_pts_Recta(xo,yo,zo,Az,Ini,Fin,L_int,Lacum,cat,ali):
    # Return matriz de puntos, resto
    if L_int==0: L_int=1
    M=[]
    while  Ini <= Fin:
        x2=xo+Ini*sin(Az)
        y2=yo+Ini*cos(Az)
        Lacum+=L_int
        M.append([x2,y2,zo,cat,Lacum,Az,'Line',ali])
        cat=cat+1
        Ini+=L_int
    return M,Fin-(Ini-L_int),Lacum,cat




###############################################################################

def curva_R_r(xc1,yc1,R1,xp1,yp1,As1,R2,Ae2,As2,alpha,h,Lacum):

    # R1>R2
    #Calculamos los puntos de tangencia de la clotoide con los dos circulos
    xo1_s,yo1_s,Tau1_s,Ls1,xe1,ye1=clotoide_Locales(As1,R1)
    xo2_e,yo2_e,Tau2_e,Le2,xe2,ye2=clotoide_Locales(Ae2,R2)
    Az1=azimut(xc1,yc1,xp1,yp1)

    if R1 > 0 and R2 > 0:
        g90 = pi/2
        g180 = pi

    elif R1 < 0 and R2 < 0:
        alpha=-alpha
        g90 = -pi/2
        g180 = -pi

    else:
        print "Error: For change the radio sing a straight must be between the radios"
        return 0

    xt1=xc1+abs(R1+yo1_s)*sin(Az1-Tau1_s)
    yt1=yc1+abs(R1+yo1_s)*cos(Az1-Tau1_s)

    xt2=xt1+(xo2_e-xo1_s)*sin((Az1-Tau1_s)+g90)
    yt2=yt1+(xo2_e-xo1_s)*cos((Az1-Tau1_s)+g90)

    xad2=xt1-(xo1_s)*sin((Az1-Tau1_s)+g90)
    yad2=yt1-(xo1_s)*cos((Az1-Tau1_s)+g90)

    xc2=xt2+abs(R2+yo2_e)*sin((Az1-Tau1_s)+g180)
    yc2=yt2+abs(R2+yo2_e)*cos((Az1-Tau1_s)+g180)

    xar2=xc2+abs(R2)*sin(Az1-Tau1_s+Tau2_e)
    yar2=yc2+abs(R2)*cos(Az1-Tau1_s+Tau2_e)

    xra2=xc2+abs(R2)*sin((Az1-Tau1_s)+(Tau2_e+alpha))
    yra2=yc2+abs(R2)*cos((Az1-Tau1_s)+(Tau2_e+alpha))


    Azent=azimut(xad2,yad2,xt2,yt2)
    Azini=azimut(xc2,yc2,xar2,yar2)
    Azfin=azimut(xc2,yc2,xra2,yra2)

    aligns = [["C_ent",[Ae2,Azent,xad2,yad2,xar2,yar2,Le2,Lacum,R2,Le2-Ls1]]]
    aligns.append(["Curva",[R2,alpha,xc2,yc2,Azini,Azfin,alpha*abs(R2),Lacum]])

    return xc2,yc2,R2,xra2,yra2,[xad2,yad2,xt1,yt1],Lacum,aligns

####-------------

def curva_r_R(xc1,yc1,R1,xp1,yp1,As1,R2,Ae2,As2,alpha,h,Lacum):

    # R1<R2
    xo1_s,yo1_s,Tau1_s,Ls1,xe1,ye1=clotoide_Locales(As1,R1)
    xo2_e,yo2_e,Tau2_e,Le2,xe2,ye2=clotoide_Locales(Ae2,R2)
    Az1=azimut(xc1,yc1,xp1,yp1)

    if R1 > 0 and R2 > 0:
        g90 = pi/2
        g180 = pi

    elif R1 < 0 and R2 < 0:
        alpha=-alpha
        g90 = -pi/2
        g180 = -pi

    else:
        print "Error: For change the radio sing a straight must be between the radios"
        return 0

    xt1=xc1+abs(R1+yo1_s)*sin(Az1+Tau1_s)
    yt1=yc1+abs(R1+yo1_s)*cos(Az1+Tau1_s)

    xt2=xt1+(xo1_s-xo2_e)*sin((Az1+Tau1_s)+g90)
    yt2=yt1+(xo1_s-xo2_e)*cos((Az1+Tau1_s)+g90)

    xda1=xt1+(xo1_s)*sin((Az1+Tau1_s)+g90)
    yda1=yt1+(xo1_s)*cos((Az1+Tau1_s)+g90)

    xc2=xt2+abs(R2+yo2_e)*sin((Az1+Tau1_s)+g180)
    yc2=yt2+abs(R2+yo2_e)*cos((Az1+Tau1_s)+g180)

    xar2=xc2+abs(R2)*sin(Az1+Tau1_s-Tau2_e)
    yar2=yc2+abs(R2)*cos(Az1+Tau1_s-Tau2_e)

    xra2=xc2+abs(R2)*sin(Az1+Tau1_s-Tau2_e+alpha)
    yra2=yc2+abs(R2)*cos(Az1+Tau1_s-Tau2_e+alpha)

    Azsal=azimut(xt1,yt1,xda1,yda1)
    Azini=azimut(xc2,yc2,xar2,yar2)
    Azfin=azimut(xc2,yc2,xra2,yra2)

    aligns = [["C_sal",[As1,Azsal,xda1,yda1,xp1,yp1,Ls1,Lacum,R1,Ls1-Le2]]]
    aligns.append(["Curva",[R2,alpha,xc2,yc2,Azini,Azfin,alpha*abs(R2)]])

    return xc2,yc2,R2,xra2,yra2,[xt1,yt1,xda1,yda1],Lacum,aligns

####-------------

def curva_recta2(xc1,yc1,R1,xp1,yp1,As1,R2,Ae2,As2,len2,h,Lacum):

    # R1 != 0 y R2 = 0
    xo1_s,yo1_s,Tau1_s,Ls1,xe1,ye1=clotoide_Locales(As1,R1)
    Az1=azimut(xc1,yc1,xp1,yp1)

    xra1=xp1
    yra1=yp1

    if R1 > 0:
        g90 = pi/2
    else:
        g90 = -pi/2

    xt1=xc1+abs(R1+yo1_s)*sin(Az1+Tau1_s)
    yt1=yc1+abs(R1+yo1_s)*cos(Az1+Tau1_s)

    xda1=xt1+(xo1_s)*sin((Az1+Tau1_s)+g90)
    yda1=yt1+(xo1_s)*cos((Az1+Tau1_s)+g90)

    if As1 == 0:

        xda1=xra1
        yda1=yra1

    xp1=xda1+len2*sin((Az1+Tau1_s)+g90)
    yp1=yda1+len2*cos((Az1+Tau1_s)+g90)


    Az1=azimut(xt1,yt1,xp1,yp1)
    dist=sqrt((xda1-xp1)**2+(yda1-yp1)**2)

    aligns = [["C_sal",[As1,Az1,xda1,yda1,xra1,yra1,Ls1,Lacum,R2]]]
    aligns.append(["Recta",[xp1,yp1,0,dist,Lacum,Az1]])

    return xda1,yda1,R2,xp1,yp1,[xt1,yt1,xp1,yp1],Lacum,aligns

####-------------

def recta_curva(xc1,yc1,R1,xp1,yp1,As1,R2,Ae2,As2,alpha,h,Lacum):

    # R1 = 0 y R2 != 0
    xo2_e,yo2_e,Tau2_e,Le2,xe2,ye2=clotoide_Locales(Ae2,R2)

    Az0=azimut(xc1,yc1,xp1,yp1)
    xad2=xp1
    yad2=yp1

    xt2=xad2+(xo2_e)*sin(Az0)
    yt2=yad2+(xo2_e)*cos(Az0)

    if R2 > 0:
        g90 = pi/2

    else:
        alpha=-alpha
        g90 = -pi/2

    xc2=xt2+abs(R2+yo2_e)*sin(Az0+g90)
    yc2=yt2+abs(R2+yo2_e)*cos(Az0+g90)

    Az1=Az0-g90

    xar2=xc2+abs(R2)*sin(Az1+Tau2_e)
    yar2=yc2+abs(R2)*cos(Az1+Tau2_e)

    if Ae2 == 0:

        xar2=xad2
        yar2=yad2

    xra2=xc2+abs(R2)*sin(Az1+Tau2_e+alpha)
    yra2=yc2+abs(R2)*cos(Az1+Tau2_e+alpha)


    aligns = [["C_ent",[Ae2,Az0,xad2,yad2,xar2,yar2,Le2,Lacum,R2]]]
    aligns.append(["Curva",[R2,alpha,xc2,yc2,Az1,Az1+alpha,alpha*abs(R2),Lacum]])

    return xc2,yc2,R2,xra2,yra2,[xc1,yc1,xp1,yp1],Lacum,aligns

####-------------

def generate_edge_polygon(center,radio1,param1,point1,radio2,param21,param22,len2):

    xc1,yc1=center.split(',')
    xc1,yc1=float(xc1),float(yc1)
    R1=float(radio1)
    As1=float(param1)

    xp1,yp1=point1.split(',')
    xp1,yp1=float(xp1),float(yp1)

    R2 = [float(p) for p in radio2.split(',')]+[0,0]
    Ae2 = [float(p) for p in param21.split(',')]+[0,0]
    As2 = [float(p) for p in param22.split(',')]+[0,0]
    len2 = [float(p) for p in len2.split(',')]+[0,0]

    Lacum=0
    if R1 == 0:
        dist=sqrt((xc1-xp1)**2+(yc1-yp1)**2)
        Lacum=Lacum+dist

    else:
        # corregimos xp1
        Az1=azimut(xc1,yc1,xp1,yp1)
        xp1=xc1+(R1)*sin(Az1)
        yp1=yc1+(R1)*cos(Az1)

    h=1

    tabla=[[R1,0,As1]]
    ppolyg,peje,aligns=[],[],[]
    for i,ra in enumerate(R2[:-1]):

        if h == 3: h=1

        if R1 == 0 and R2[i] == 0:
            #print "R1=0 and R2=0"
            continue

        elif R1 == 0:
            xc1,yc1,R1,xp1,yp1,pts_polyg,Lacum,align=recta_curva(xc1,yc1,R1,xp1,yp1,As1,R2[i],Ae2[i],As2[i],len2[i]/abs(R2[i]),h,Lacum)
            #write_Polyline(ptos_eje,options['outmap']+'recta1')

        elif R2[i] == 0:
            xc1,yc1,R1,xp1,yp1,pts_polyg,Lacum,align=curva_recta2(xc1,yc1,R1,xp1,yp1,As1,R2[i],Ae2[i],As2[i],len2[i],h,Lacum)
            #write_Polyline(ptos_eje,options['outmap']+'recta2')

        elif abs(R1) > abs(R2[i]) :
            xc1,yc1,R1,xp1,yp1,pts_polyg,Lacum,align=curva_R_r(xc1,yc1,R1,xp1,yp1,As1,R2[i],Ae2[i],As2[i],len2[i]/abs(R2[i]),h,Lacum)
            #write_Polyline(ptos_eje,options['outmap']+'recta3')

        elif abs(R1) < abs(R2[i]):
            xc1,yc1,R1,xp1,yp1,pts_polyg,Lacum,align=curva_r_R(xc1,yc1,R1,xp1,yp1,As1,R2[i],Ae2[i],As2[i],len2[i]/abs(R2[i]),h,Lacum)
            #write_Polyline(ptos_eje,options['outmap']+'recta4')

        h=h+1

        aligns.extend(align)
        ppolyg.append(pts_polyg)

        if R2[i] != 0:
            tabla.append([R2[i],Ae2[i],As2[i]])

        #peje.append(ptos_eje)

        As1=As2[i]

    tabla.append([0,0,0])

    polygon = [ppolyg[0][:2]+[0]]

    for i,pto in enumerate(ppolyg[:-1]):

        Az_1 = azimut(ppolyg[i][0],ppolyg[i][1],ppolyg[i][2],ppolyg[i][3])
        Az_2 = azimut(ppolyg[i+1][0],ppolyg[i+1][1],ppolyg[i+1][2],ppolyg[i+1][3])

        if round(Az_1,8) == round(Az_2,8): continue

        xv,yv=pto_corte_2_rectas(ppolyg[i][0],ppolyg[i][1],ppolyg[i][2],ppolyg[i][3],ppolyg[i+1][0],ppolyg[i+1][1],ppolyg[i+1][2],ppolyg[i+1][3])
        polygon.append([xv,yv,0])

    polygon.append(ppolyg[-1][2:]+[0])

    #for jj in aligns: print jj
    return polygon,tabla

###############################################################################





###############################################################################

def generate_Aligns(poly,tabla):

    LAcum=0
    #for jj in tabla: print jj
    x_ini,y_ini = poly[0][0],poly[0][1]
    puntos_eje=[]
    centros = []
    for i in range(1,len(poly)-1,1):

        a,b = poly[i-1][0],poly[i-1][1]
        c,d = poly[i][0],poly[i][1]
        e,f = poly[i+1][0],poly[i+1][1]

        Az_ent,Az_sal,w=angulos_Alings(a,b,c,d,e,f)

        R,Ae,As = tabla[i][0],tabla[i][1],tabla[i][2]

        if R == 0:
            Lrecta=sqrt((c-x_ini)**2+(d-y_ini)**2)
            LAcum+=Lrecta
            Lini_e,Lini_s=0,0
            puntos_eje.append([[x_ini,y_ini,0,Lrecta,LAcum,Az_ent],
                               [0,Az_ent,c,d,c,d,0,LAcum,0,Lini_e,0,0],
                               [0,0,0,0,0,0,0,LAcum],
                               [0,Az_sal,c,d,c,d,0,LAcum,0,Lini_s,0,0]])
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

        ac=a+abs(R+yo_e)*sin(Az_ent+g90)
        bc=b+abs(R+yo_e)*cos(Az_ent+g90)

        cc1=c+abs(R+yo_e)*sin(Az_ent+g90)
        dc1=d+abs(R+yo_e)*cos(Az_ent+g90)

        cc2=c+abs(R+yo_s)*sin(Az_sal+g90)
        dc2=d+abs(R+yo_s)*cos(Az_sal+g90)

        ec=e+abs(R+yo_s)*sin(Az_sal+g90)
        fc=f+abs(R+yo_s)*cos(Az_sal+g90)

        xc,yc=pto_corte_2_rectas(ac,bc,cc1,dc1,cc2,dc2,ec,fc)
        centros.append([xc,yc,0])

        Lini_e,Lini_s=0,0
        if Ae <= 0:

            xar = xc+abs(R)*sin(Az_ent-g90-Tau_e)
            yar = yc+abs(R)*cos(Az_ent-g90-Tau_e)
            xad,yad = xar,yar

            Lrecta = sqrt((xad-x_ini)**2+(yad-y_ini)**2)
            if Ae < 0:
                x_ini,y_ini = xad,yad
                Lrecta = 0
            Le = 0
            xadp,yadp = xad,yad

        else:

            xt1= xc+abs(R+yo_e)*sin(Az_ent-g90)
            yt1= yc+abs(R+yo_e)*cos(Az_ent-g90)

            xad = xt1+xo_e*sin(Az_ent+pi)
            yad = yt1+xo_e*cos(Az_ent+pi)

            xar = xc+abs(R)*sin(Az_ent-g90+Tau_e)
            yar = yc+abs(R)*cos(Az_ent-g90+Tau_e)

            Lrecta = sqrt((xad-x_ini)**2+(yad-y_ini)**2)
            R1,Ae1,As1 = tabla[i-1][0],tabla[i-1][1],tabla[i-1][2]
            if As1 < 0:
                xo_s1,yo_s1,Tau_s1,Ls1,xs1,ys1=clotoide_Locales(As1,R1)
                Lini_e =  Ls1
                Ptos_ent,resto,acum,cat=get_pts_Clot_ent(Ae,xad,yad,Az_ent,Lini_e,Lini_e,1,R,0,0,0)
                xadp,yadp = Ptos_ent[0][0],Ptos_ent[0][1]
                x_ini,y_ini = xadp,yadp
                Lrecta = 0

        Dc = abs(R)*alpha

        if As <= 0:

            xra = xc+abs(R)*sin(Az_sal-g90+Tau_s)
            yra = yc+abs(R)*cos(Az_sal-g90+Tau_s)
            xda,yda = xra,yra
            Ls = 0
            xdap,ydap = xda,yda

        else:
            xt1= xc+abs(R+yo_s)*sin(Az_sal-g90)
            yt1= yc+abs(R+yo_s)*cos(Az_sal-g90)

            xda = xt1+xo_s*sin(Az_sal)
            yda = yt1+xo_s*cos(Az_sal)

            xra = xc+abs(R)*sin(Az_sal-g90-Tau_s)
            yra = yc+abs(R)*cos(Az_sal-g90-Tau_s)

            R2,Ae2,As2 = tabla[i+1][0],tabla[i+1][1],tabla[i+1][2]
            if Ae2 < 0:
                xo_e2,yo_e2,Tau_e2,Le2,xe2,ye2=clotoide_Locales(Ae2,R2)
                Lini_s = Le2
                Ptos_sal,resto,acum,cat_s=get_pts_Clot_sal(As,xda,yda,Az_sal,Lini_s,Lini_s,1,R,0,0,0)
                xdap,ydap = Ptos_sal[0][0],Ptos_sal[0][1]

        #Az_ini = Az_ent-g90+Tau_e
        #Az_fin = Az_sal-g90-Tau_s
        Az_ini=azimut(xc,yc,xar,yar)
        Az_fin=azimut(xc,yc,xra,yra)

        puntos_eje.append([[x_ini,y_ini,0,Lrecta,LAcum+Lrecta,Az_ent],
                           [Ae,Az_ent,xad,yad,xar,yar,Le,LAcum+Lrecta+(Le-Lini_e),R,Lini_e],
                           [R,alpha,xc,yc,Az_ini,Az_fin,Dc,LAcum+Lrecta+(Le-Lini_e)+Dc],
                           [As,Az_sal,xda,yda,xra,yra,Ls,LAcum+Lrecta+(Le-Lini_e)+Dc+(Ls-Lini_s),R,Lini_s]])

        x_ini,y_ini = xda,yda
        LAcum = LAcum+Lrecta+(Le-Lini_e)+Dc+(Ls-Lini_s)

    Lrecta = sqrt((e-x_ini)**2+(f-y_ini)**2)
    puntos_eje.append([[x_ini,y_ini,0,Lrecta,LAcum+Lrecta,Az_sal],
                      [0,Az_sal,x_ini,y_ini,0,0,0,LAcum+Lrecta,0,Lini_e],
                      [0,0,0,0,0,0,0,LAcum+Lrecta],
                      [0,Az_sal,x_ini,y_ini,0,0,0,LAcum+Lrecta,0,Lini_s]])
    #for jj in puntos_eje:
        #for pp in jj: print pp
    return puntos_eje

###############################################################################


def generate_Pts(puntos_eje,a):

    #x_ini,y_ini,z_ini,Lrecta,LAcum,Az_ent=puntos_eje[0][0]

    Az_ent=puntos_eje[1][1][1]
    resto=1
    interv=1
    cat=1
    puntos,seg,puntos_caract,puntos_centros=[],[],[],[]

    acum=0
    h=1
    for i in range(0,len(puntos_eje),1):

        Ptos_recta,Ptos_ent,Ptos_curva,Ptos_sal=[],[],[],[]

        x_ini,y_ini,z_ini,Lrecta,LrAcum,Az_ent=puntos_eje[i][0]
        Aent,Az_ent,xad,yad,xar,yar,Lent,LeAcum,R,Lini_e=puntos_eje[i][1]
        R,alpha,xc,yc,Az_ini,Az_fin,Dc,LcAcum=puntos_eje[i][2]
        Asal,Az_sal,xda,yda,xra,yra,Lsal,LsAcum,R,Lini_s=puntos_eje[i][3]

        Ptos_recta,resto,acum,cat=get_pts_Recta(x_ini,y_ini,z_ini,Az_ent,interv-resto,Lrecta,interv,acum,cat,i+1)

        if R != 0:
            if Aent != 0:
                Ptos_ent,resto,acum,cat=get_pts_Clot_ent(Aent,xad,yad,Az_ent,interv-resto+Lini_e,Lent,interv,R,acum,cat,i+1)

            Ptos_curva,resto,acum,cat=get_pts_Curva(xc,yc,Az_ini-resto/R,Az_fin,interv,R,acum,Dc,cat,i+1)

            if Asal != 0:
                Ptos_sal,resto,acum,cat=get_pts_Clot_sal(Asal,xda,yda,Az_sal,interv-resto+Lini_s,Lsal,interv,R,acum,cat,i+1)
        else:
            Ptos_ent,Ptos_curva,Ptos_sal=[[],[],[]]

        x_ini,y_ini=xda,yda

        puntos.extend(Ptos_recta+Ptos_ent+Ptos_curva+Ptos_sal)

        h=h+4

    #x_fin,y_fin,z_fin,Lrecta,LAcum=[ float(t) for t in puntos_eje[-1][0]]
    #puntos.append([x_fin,y_fin,z_fin,cat,LAcum,Az_sal,'End',i+2])

    #for jj in puntos: print jj

    return puntos

###############################################################################
###############################################################################
###############################################################################
###############################################################################



def generate_PtsRound(radio,radio2,azimut,center):

    xo,yo=center.split(',')
    radio=float(radio)
    radio2=float(radio2)
    Az=float(azimut)

    x1=float(xo)+radio2*sin(Az)
    y1=float(yo)+radio2*cos(Az)

    x2=x1+radio*sin(Az+pi/2)
    y2=y1+radio*cos(Az+pi/2)

    x3=x2+2*radio2*sin(Az+pi)
    y3=y2+2*radio2*cos(Az+pi)

    x4=x3+2*radio*sin(Az+3*pi/2)
    y4=y3+2*radio*cos(Az+3*pi/2)

    x5=x4+2*radio2*sin(Az)
    y5=y4+2*radio2*cos(Az)

    x6=x5+(radio)*sin(Az+pi/2)
    y6=y5+(radio)*cos(Az+pi/2)

    return [[x1,y1,0],[x2,y2,0],[x3,y3,0],[x4,y4,0],[x5,y5,0],[x6,y6,0]]

###############################################################################


def edges_intersec(R,point1,point2,izq1,dist1,point3,point4,izq2,dist2):

    R=float(R)
    dist1=float(dist1)
    dist2=float(dist2)
    x1,y1=point1.split(',')
    x1,y1=float(x1),float(y1)
    x2,y2=point2.split(',')
    x2,y2=float(x2),float(y2)
    x3,y3=point3.split(',')
    x3,y3=float(x3),float(y3)
    x4,y4=point4.split(',')
    x4,y4=float(x4),float(y4)

    Az1=azimut(x1,y1,x2,y2)
    Az2=azimut(x3,y3,x4,y4)
    #alpha=abs(Az1-Az2)

    if izq1=="Izq": izq1=-1
    else: izq1=1

    # Recta paralela a dist1+R
    x11=x1+(dist1+R)*sin(Az1+izq1*pi/2)
    y11=y1+(dist1+R)*cos(Az1+izq1*pi/2)
    x22=x2+(dist1+R)*sin(Az1+izq1*pi/2)
    y22=y2+(dist1+R)*cos(Az1+izq1*pi/2)

    # Recta paralela a dist1 para poner el vertice en el punto medio
    xr1=x1+(dist1)*sin(Az1+izq1*pi/2)
    yr1=y1+(dist1)*cos(Az1+izq1*pi/2)
    xr2=x2+(dist1)*sin(Az1+izq1*pi/2)
    yr2=y2+(dist1)*cos(Az1+izq1*pi/2)

    if izq2=="Izq": izq2=-1
    else: izq2=1

    # Recta paralela a dist2+R
    x33=x3+(dist2+R)*sin(Az2+izq2*pi/2)
    y33=y3+(dist2+R)*cos(Az2+izq2*pi/2)
    x44=x4+(dist2+R)*sin(Az2+izq2*pi/2)
    y44=y4+(dist2+R)*cos(Az2+izq2*pi/2)

    # Recta paralela a dist1 para poner el vertice en el punto medio
    xr3=x3+(dist2)*sin(Az2+izq2*pi/2)
    yr3=y3+(dist2)*cos(Az2+izq2*pi/2)
    xr4=x4+(dist2)*sin(Az2+izq2*pi/2)
    yr4=y4+(dist2)*cos(Az2+izq2*pi/2)

    xv,yv=pto_corte_2_rectas(xr1,yr1,xr2,yr2,xr3,yr3,xr4,yr4)
    xc,yc=pto_corte_2_rectas(x11,y11,x22,y22,x33,y33,x44,y44)

    Az3=azimut(xc,yc,xv,yv)

    # Punto de corte de la recta centro-vertice con el circulo
    xp=xc+R*sin(Az3)
    yp=yc+R*cos(Az3)

    # Rectas perpendiculares de xc,yc y xp,yp al eje 1
    xt1=xc+(dist1+R)*sin(Az1-izq1*pi/2)
    yt1=yc+(dist1+R)*cos(Az1-izq1*pi/2)
    xp1=xp+(dist1+R)*sin(Az1-izq1*pi/2)
    yp1=yp+(dist1+R)*cos(Az1-izq1*pi/2)

    xt2,yt2=pto_corte_2_rectas(x1,y1,x2,y2,xp,yp,xp1,yp1)

    # Rectas perpendiculares de xc,yc y xp,yp al eje 2
    xt3=xc+(dist2+R)*sin(Az2-izq2*pi/2)
    yt3=yc+(dist2+R)*cos(Az2-izq2*pi/2)
    xp2=xp+(dist2+R)*sin(Az2-izq2*pi/2)
    yp2=yp+(dist2+R)*cos(Az2-izq2*pi/2)

    xt4,yt4=pto_corte_2_rectas(x3,y3,x4,y4,xp,yp,xp2,yp2)

    # Distancias al primer punto de cada eje
    d1=sqrt((x1-xt1)**2+(y1-yt1)**2)+float(options['pkref1'])
    d2=sqrt((x1-xt2)**2+(y1-yt2)**2)+float(options['pkref1'])
    d3=sqrt((x3-xt3)**2+(y3-yt3)**2)+float(options['pkref2'])
    d4=sqrt((x3-xt4)**2+(y3-yt4)**2)+float(options['pkref2'])

    if d1 > d2:
        dtmp=d1
        d1=d2
        d2=dtmp
        dif=d2-d1
    else:
        dif=0

    grass.message("Edge 1:")
    grass.message(" pk1="+str(d1)+", dist="+str(dist1)+", radio: r"+str(R)+","+str(dif))
    grass.message(" pk2="+str(d2)+", dist="+str(dist1)+", radio: ")

    if d3 > d4:
        dtmp=d3
        d3=d4
        d4=dtmp
        dif=d4-d3
    else:
        dif=0

    grass.message("Edge 2:")
    grass.message(" pk1="+str(d3)+", dist="+str(dist2)+", radio: r"+str(R)+","+str(dif))
    grass.message(" pk2="+str(d4)+", dist="+str(dist2)+", radio: ")

    write_Polylines([[[x11,y11,0],[x22,y22,0]],
                     [[x33,y33,0],[x44,y44,0]],
                     [[xc,yc,0],[xv,yv,0]],
                     [[xc,yc,0],[xt1,yt1,0]],
                     [[xp,yp,0],[xt2,yt2,0]],
                     [[xc,yc,0],[xt3,yt3,0]],
                     [[xp,yp,0],[xt4,yt4,0]]],options['outmap'])

    return 0

###############################################################################

def edge_circ_intersec(R,point1,point2,izq1,dist1,center,radio1):

    R=float(R)
    dist1=float(dist1)
    x1,y1=point1.split(',')
    x1,y1=float(x1),float(y1)
    x2,y2=point2.split(',')
    x2,y2=float(x2),float(y2)

    xc,yc=center.split(',')
    xc,yc=float(xc),float(yc)
    radio1=float(radio1)

    if izq1=="Izq": izq1=-1
    else: izq1=1

    Az1=azimut(x1,y1,x2,y2)

    # Recta paralela a dist1+R
    x11=x1+(dist1+R)*sin(Az1+izq1*pi/2)
    y11=y1+(dist1+R)*cos(Az1+izq1*pi/2)
    x22=x2+(dist1+R)*sin(Az1+izq1*pi/2)
    y22=y2+(dist1+R)*cos(Az1+izq1*pi/2)

    xc1=xc+radio1*sin(Az1-izq1*pi/2)
    yc1=yc+radio1*cos(Az1-izq1*pi/2)

    d1=sqrt((xc-xc1)**2+(yc-yc1)**2)

    # Distancia del centro del circulo al eje
    xc2,yc2=pto_corte_2_rectas(x1,y1,x2,y2,xc,yc,xc1,yc1)

    d2=sqrt((xc-xc2)**2+(yc-yc2)**2)

    if d1 > d2: d2=-d2

    s=(R+dist1)+d2*izq1

    alpha=asin(s/(R+radio1))

    c1=radio1*cos(alpha)
    c2=(R+radio1)*cos(alpha)

    print d1,d2,R,radio1,s,alpha
    if options['inout']=='Out':

        # Centro del circulo requerido
        xcc=xc+(R+radio1)*sin(Az1+izq1*alpha)
        ycc=yc+(R+radio1)*cos(Az1+izq1*alpha)

        # Punto tangencia dos circulos
        xp=xc+radio1*sin(Az1+izq1*alpha)
        yp=yc+radio1*cos(Az1+izq1*alpha)

        xt1=xc2+c2*sin(Az1)
        yt1=yc2+c2*cos(Az1)

        xt2=xc2+c1*sin(Az1)
        yt2=yc2+c1*cos(Az1)

    else:

        xcc=xc+(R+radio1)*sin(Az1+izq1*(pi-alpha))
        ycc=yc+(R+radio1)*cos(Az1+izq1*(pi-alpha))

        # Punto tangencia dos circulos
        xp=xc+radio1*sin(Az1+izq1*(pi-alpha))
        yp=yc+radio1*cos(Az1+izq1*(pi-alpha))

        xt1=xc2+c2*sin(Az1+pi)
        yt1=yc2+c2*cos(Az1+pi)

        xt2=xc2+c1*sin(Az1+pi)
        yt2=yc2+c1*cos(Az1+pi)

    xpp=xcc+s*sin(Az1-izq1*pi/2)
    ypp=ycc+s*cos(Az1-izq1*pi/2)

    d3=sqrt((x1-xt1)**2+(y1-yt1)**2)+float(options['hpkref'])
    d4=sqrt((x1-xt2)**2+(y1-yt2)**2)+float(options['hpkref'])

    if d3 > d4:
        dtmp=d3
        d3=d4
        d4=dtmp
        dif=d4-d3
    else:
        dif=0

    grass.message("Edge 1:")
    grass.message(" pk1="+str(d3)+", dist="+str(dist1)+", radio: r"+str(R)+","+str(dif))
    grass.message(" pk2="+str(d4)+", dist="+str(dist1)+", radio: ")
    grass.message(" azimut: "+str(azimut(xc,yc,xcc,ycc)*200/pi))
    grass.message(" azimut: "+str(azimut(xc,yc,xcc,ycc)))
    write_Polylines([[[xc,yc,0],[xc1,yc1,0]],
                     [[xc,yc,0],[xcc,ycc,0]],
                     [[xcc,ycc,0],[xt1,yt1,0]],
                     [[xc,yc,0],[xpp,ypp,0]],
                     [[xp,yp,0],[xt2,yt2,0]]],options['outmap'])

    return 0

# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

def read_Table(EjeMap,layer,columns):

    table=grass.read_command('v.out.ascii', input=EjeMap, output='-',
                          format='point', layer=layer, columns=columns, quiet=True)
    table = [d.split('|') for d in table.splitlines(0)]
    if len(table[0])<len(columns.split(','))+4:
        for i in range(len(table)):
            table[i].insert(2,0.0)

    return table

def read_TableSection(EjeMap):

    section = read_Table(EjeMap,4,'pk,sec_left,sec_right,type_left,type_right,cut_left,cut_right,fill_left,fill_right')
    for i in range(len(section)):
        section[i][:5]=[float(p) for p in section[i][:5]]
    return section


def update_Layer(EjeMap,ext,layer,ptsList,columns):

    sql=''
    columns=columns.split(',')
    for i in range(len(ptsList)):
        sql+="UPDATE "+EjeMap+ext+" SET "
        sql+=', '.join(a + "=" +str(b) for a,b in zip(columns,ptsList[i][4:]))
        sql+=" WHERE cat"+str(layer)+"="+str(int(ptsList[i][3]))+";\n"
    #print sql
    grass.write_command('db.execute', database = database1, driver = 'sqlite', stdin = sql, input='-', quiet=True)
    return 0


def update_TableSection(EjeMap,ptsList):

    for i,pts in enumerate(ptsList):
        ptsList[i][5:]=["'"+str(p)+"'" for p in ptsList[i][5:] if str(p).find("'")==-1]
    update_Layer(EjeMap,'_Section',4,ptsList,'pk,sec_left,sec_right,type_left,type_right,cut_left,cut_right,fill_left,fill_right')
    return 0

# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #
# ### Main
# ###

def main():


    #if flags['a']:
        #curva_recta(options['acenter'],options['aradio'],options['aparam'],options['izq'],options['apoint'])

    if flags['c']:

        polyg,tabla=generate_edge_polygon(options['ccenter'],options['cradio1'],options['casal1'],options['cpoint1'],options['cradio2'],options['caent2'],options['casal2'],options['len2'])
        pts=generate_Aligns(polyg,tabla)
        list_ptos=generate_Pts(pts,1)


        radios,A1,A2=[],[],[]
        for p in tabla:
            radios.append(p[0])
            A1.append(p[1])
            A2.append(p[2])
        write_Polyline(list_ptos,options['outmap'].split('@')[0]+'_poly2')
        write_edge(polyg,radios,A1,A2,options['outmap'].split('@')[0])



#### Roudabout ###

    if flags['h']:
        edge_circ_intersec(options['hradio'],
                           options['hpoint1'],options['hpoint2'],options['hlado'],options['hdist_despl'],
                           options['hcenter'],options['hradio1'])

    if flags['s']:
        edges_intersec(options['sradio'],
                        options['spoint1'],options['spoint2'],options['lado1'],options['dist_despl1'],
                        options['spoint3'],options['spoint4'],options['lado2'],options['dist_despl2'])

#### Roudabout ###

    if flags['r']:
        if options['rround2']=='0': options['rround2']=options['rround1']

        az=float(options['azround'])
        PtsRound=generate_PtsRound(options['rround1'],options['rround2'],az*pi/200,options['cround'])

        radios,A1,A2=[0],[0],[0]
        for p in PtsRound[1:-1]:
            radios.append(options['rround1'])
            A1.append(0)
            A2.append(0)
        write_edge(PtsRound,radios,A1,A2,options['outmap'].split('@')[0])
        #write_Polyline(PtsRound,options['outmap'])

#### Tools ###

    #if flags['o']:

        #x1,y1=options['tpoint1'].split(',')
        #x1,y1=float(x1),float(y1)
        #x2,y2=options['tpoint2'].split(',')
        #x2,y2=float(x2),float(y2)
        #x3,y3=options['tpoint3'].split(',')
        #x3,y3=float(x3),float(y3)
        #x4,y4=options['tpoint4'].split(',')
        #x4,y4=float(x4),float(y4)

        #xx,yy=pto_corte_2_rectas(x1,y1,x2,y2,x3,y3,x4,y4)
        #grass.message("Coord: "+str(xx)+","+str(yy))

    #if flags['t']:

        #R=float(options['tradio'])
        #x1,y1=options['tpoint1'].split(',')
        #x1,y1=float(x1),float(y1)
        #xc,yc=options['tcenter'].split(',')
        #xc,yc=float(xc),float(yc)

        #xx,yy=recta_tg_circulo(x1,y1,R,xc,yc)
        #grass.message("Coord: "+str(xx)+","+str(yy))

    #if flags['l']:

        #x1,y1=options['tpoint1'].split(',')
        #x1,y1=float(x1),float(y1)
        #x2,y2=options['tpoint2'].split(',')
        #x2,y2=float(x2),float(y2)
        #d=float(options['dist'])

        #xx,yy,dx,dy=alargar_recta(x1,y1,x2,y2,d)
        #grass.message("Coord: "+str(xx)+","+str(yy))
        #grass.message("Dist: "+str(dx)+","+str(dy))


#### Displaced ###

    if flags['a'] or flags['d']:

        global database1

        EjeMap=options['edge']
        if '@' in EjeMap:
            NameMap,MapSet=EjeMap.split('@')
        else:
            NameMap=EjeMap

        f = grass.vector_db(options['edge'])[1]
        table    = f['table']
        database1 = f['database']
        driver   = f['driver']

        seccion=read_TableSection(EjeMap)

        num1=len(seccion[0][5].split(';'))
        num2=len(seccion[0][6].split(';'))
        for i,lin in enumerate(seccion):
            if lin[7] == '':
                seccion[i][7]=';'.join(['l' for p in range(num1)])
            if lin[8] == '':
                seccion[i][8]=';'.join(['l' for p in range(num2)])

        if options['lado'] == 'left':
            lado=[p[5].split(';') for p in seccion]
            tipo=[p[7].split(';') for p in seccion if p[7]!='']
        else:
            lado=[p[6].split(';') for p in seccion]
            tipo=[p[8].split(';') for p in seccion if p[8]!='']

        if flags['a']:

            lado[0].insert(int(options['ncol'])-1,options['startd'])
            tipo[0].insert(int(options['ncol'])-1,'l')
            lado[-1].insert(int(options['ncol'])-1,options['endd'])
            tipo[-1].insert(int(options['ncol'])-1,'l')

            if len(lado) > 2:
                for i,lin in enumerate(lado[1:-1]):
                    lado[i+1].insert(int(options['ncol'])-1,'-1 0')
                    if tipo[i+1]!=[]:
                        tipo[i+1].insert(int(options['ncol'])-1,'l')

        if flags['d']:
            for i,lin in enumerate(lado):
                del lado[i][int(options['ncol'])-1]
                del tipo[i][int(options['ncol'])-1]

        for i,lin in enumerate(seccion):
            if options['lado'] == 'left':
                seccion[i][5]=';'.join(lado[i])
                seccion[i][7]=';'.join(tipo[i])
            else:
                seccion[i][6]=';'.join(lado[i])
                seccion[i][8]=';'.join(tipo[i])
        #for jj in seccion: print jj
        update_TableSection(NameMap,seccion)

    sys.exit(0)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
