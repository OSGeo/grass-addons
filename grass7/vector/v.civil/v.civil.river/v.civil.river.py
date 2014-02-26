#!/usr/bin/env python
# -*- coding: utf-8
############################################################################
#
# MODULE:       v.civil.river, v0.5.0
#
# AUTHOR:       Jesús Fernández-Capel Rosillo
#               Civil Engineer, Spain
#               jfc at alcd net
#
# PURPOSE:      Export - Import geometry data to/from an 1-D hydrodynamic model.
#
# COPYRIGHT:    (c) 2014 Jesús Fernández-Capel Rosillo.
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Export - Import geometry data to/from an 1-D hydrodynamic model.
#% keywords: vector, Hec-Ras, hydraulic, river
#%End

#### Required section ####

#%option
#% key: ini
#% type: string
#% key_desc: Iniciar
#% description: Title of project
#% required: yes
#%end


#### Export section ####

#%flag
#% key: e
#% description: Export to Hec-Ras
#% guisection: Export
#%end

#%option
#% key: mapcross
#% type: string
#% gisprompt: old,vector,vector
#% description: Name for croos section map
#% required: no
#% guisection: Export
#%end

#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: raster dem
#% description: Name of DEM raster map
#% guisection: Export
#%end

#%option
#% key: mapcrossdispl
#% type: string
#% gisprompt: old,vector,vector
#% description: Name for cross-displ map
#% required: no
#% guisection: Export
#%end

#%option
#% key: manning
#% type: string
#% description: Values for Manning three columns ej: 0.050,0.045,0.050
#% required: no
#% answer: 0.050,0.040,0.050
#% guisection: Export
#%end

#%option G_OPT_F_OUTPUT
#% description: Prefix name for output geometry csv files
#% required: no
#% guisection: Export
#%end

#### Import section ####

#%flag
#% key: i
#% description: Import from Hec-Ras
#% guisection: Import
#%end

#%flag
#% key: d
#% description: Create ASCII file describing the water surface profile along the channel axis (r.inund.fluv)
#% guisection: Import
#%end

#%option G_OPT_F_INPUT
#% key: inputfile
#% description: Name for input hec-ras file
#% required: no
#% guisection: Import
#%end

#%option G_OPT_V_OUTPUT
#% key: outwaterfile
#% description: Name for output water surface polygon
#% required: no
#% guisection: Import
#%end

#%option G_OPT_F_OUTPUT
#% key: outprofilefile
#% description: Name for output water surface profile file (r.inund.fluv)
#% required: no
#% guisection: Import
#%end





import os, sys
from math import *
import grass.script as grass
from grass.lib.gis    import *
from grass.lib.vector import *
from grass.lib.raster import *
import grass.pygrass.raster as raster
import grass.pygrass.vector as Vector
from grass.pygrass.gis.region import Region

###############################################################################

def write_Polygon(puntos,name):

    # Write Polygon
    sal_linea="B "+str(len(puntos)+1)+" 1\n"
    for pp in puntos:
        sal_linea+=''+str(pp[0])+" "+str(pp[1])+"\n"
    sal_linea+=''+str(puntos[0][0])+" "+str(puntos[0][1])+"\n"
    sal_linea+="1 1\n"
    #print sal_linea
    grass.write_command('v.in.ascii', flags='nz', output=name, stdin=sal_linea, input='-', format='standard', overwrite=True, quiet=True)
    return 0


###############################################################################

def azimut(a,b,c,d):

    Az=atan((c-a)/(d-b))
    #if a < c and b < d: Az=Az*1 # Az>0 -> Az > 0
    if a < c and b > d: Az=Az+pi # Az<0 -> Az > 100
    elif a > c and b > d: Az=Az+pi # Az>0 -> Az > 200
    elif a > c and b < d: Az=Az+2*pi # Az<0 -> Az > 300
    return Az


def discr_Lines(lines,discr):

    disLines=[]
    for pto in lines:
        resto,acum=0,0
        cat_r=1
        disptos=[]
        for i in range(len(pto[:-1])):

            disptos.append(pto[i])
            Az=azimut(pto[i][0],pto[i][1],pto[i+1][0],pto[i+1][1])
            Lrecta=sqrt((pto[i+1][0]-pto[i][0])**2+(pto[i+1][1]-pto[i][1])**2)
            Ptos_recta,resto,acum,cat_r=get_pts_Recta(pto[i][0],pto[i][1],0,Az,discr-resto,Lrecta,discr,acum,cat_r,i)
            disptos.extend(Ptos_recta)
        disptos.append(pto[i+1])
        disLines.append(disptos)
    return disLines

def get_pts_Recta(xo,yo,zo,Az,Ini,Fin,L_int,Lacum,cat,ali):
    # Return matriz de puntos, resto
    if L_int==0: L_int=1
    M=[]
    while  Ini <= Fin:
        x2=xo+Ini*sin(Az)
        y2=yo+Ini*cos(Az)
        Lacum+=L_int
        M.append([x2,y2,0,cat,Lacum,Az,'Recta',ali])
        cat=cat+1
        Ini+=L_int
    return M,Fin-(Ini-L_int),Lacum,cat


def drape_LinesPoints(lines,dem):

    elev = raster.RasterRowIO(dem)
    elev.open('r')
    region=Region()
    salida=[]
    for i,line in enumerate(lines):

        ptos=[]
        for j,pto in enumerate(line):
            #print j
            pto_col = int((pto[0] - region.west)/region.ewres)
            pto_row = int((region.north - pto[1])/region.nsres)
            ptos.append(lines[i][j][:2]+[elev[pto_row][pto_col]]+lines[i][j][3:])

        salida.append(ptos)
    elev.close()
    return salida

###############################################################################

def read_MapTrans(MapTrans):

    verti=grass.read_command('v.out.ascii', input=MapTrans, output='-', format='standard', layer=1)
    verti = re.findall(r'L  [0-9]* [0-9]*\n(.*?)1     ([0-9]*)',verti,re.S|re.I)
    verti.sort(key=lambda x: float(x[1]))
    lineas,cats=[],[]
    for line in verti:
        lineas.append([d.split() for d in line[0].splitlines(0)])
        cats.append(line[1])

    for i,line in enumerate(lineas):
        lineas[i]=[[float(p) for p in lin] for lin in line[:-1]]

    return lineas,cats


def get_Banks(MapTrans):

    lineas,cats=read_MapTrans(MapTrans)

    banks=[]
    for i,cat in enumerate(cats):

	dx1 = sqrt((lineas[i][0][0]-lineas[i][2][0])**2+(lineas[i][0][1]-lineas[i][2][1])**2)
	dx2 = sqrt((lineas[i][0][0]-lineas[i][4][0])**2+(lineas[i][0][1]-lineas[i][4][1])**2)

	banks.append([round(dx1,2),round(dx2,2)])

    return banks



###############################################################################

def write_HecRasGeom2(MapTrans,Dem,namesal):

    # puntos terreno transversales
    lineas,cats = read_MapTrans(MapTrans)
    lineas=discr_Lines(lineas,1)
    lineas = drape_LinesPoints(lineas,Dem)

    # Primer filtro. Eliminar ptos repetidos
    lineas2,distcota=[],[]
    for i,line in enumerate(lineas):
        line2=[]
        distcota.append([])
        for j,pto in enumerate(line[:-1]):

	    dx1 = sqrt((pto[0]-line[j+1][0])**2+(pto[1]-line[j+1][1])**2)
	    dx2 = sqrt((pto[0]-line[0][0])**2+(pto[1]-line[0][1])**2)
	    if dx1 != 0:
		distcota[-1].append([round(dx2,2),round(pto[2],2)])
		line2.append([round(pto[0],2),round(pto[1],2),round(pto[2],2)])

	line2.append([round(p,2) for p in line[j+1] ])
	lineas2.append(line2)

    # Pto mas bajo de cada seccion. cauce real
    creal=[]
    for j,line in enumerate(lineas2):
	cotaline=[p[2] for p in line]
        minline=min(cotaline)
        ind = cotaline.index(minline)
        creal.append(lineas2[j][ind])
    sal4=""
    for j,pto in enumerate(creal):
        sal4+=str(pto[0])+'\t'+str(pto[1])+"\r\n"

    # Ptos del eje de cada seccion
    eje = [p[4] for p in lineas]
    sal3=""
    for j,pto in enumerate(eje):
        sal3+=str(pto[0])+'\t'+str(pto[1])+"\r\n"


    sal="RS,X,Y,Z\r\n"
    for j,line in enumerate(lineas2):
        for pto in line:
            sal+=str(int(cats[-1])-int(cats[j]))+","+str(pto[0])+","+str(pto[1])+","+str(pto[2])+"\r\n"
    sal2="RS,ST,Z\r\n"
    for j,line in enumerate(distcota):
        for pto in line:
            sal2+=str(int(cats[-1])-int(cats[j]))+","+str(pto[0])+","+str(pto[1])+"\r\n"


    with open(namesal+'_format_xyz.csv', 'wb') as f:
        f.write(sal)
    f.closed
    with open(namesal+'_format_stations.csv', 'wb') as f:
        f.write(sal2)
    f.closed
    with open(namesal+'_schematic.txt', 'wb') as f:
        f.write(sal3)
    f.closed
    with open(namesal+'_schematic_real.txt', 'wb') as f:
        f.write(sal4)
    f.closed
    #print sal
    return 0




##############################################################################

def write_HecRasTables2(MapTrans,MapCrossDispl,manning,namesal):

    # puntos desplazados
    verti=grass.read_command('v.out.ascii', input=MapCrossDispl, output='-', format='point', columns='Type,PK', layer=1)
    verti=[p.split('|') for p in verti.splitlines(0)]

    linea_ptos=[]
    for pto in verti:
        if float(pto[-1]) == 0: linea_ptos.append([])
        linea_ptos[-1].append([float(p) for p in pto[:3]]+[float(pto[4][1:])]+[float(pto[5])])

    banks = get_Banks(MapTrans)
    bankstr = ""
    for i,bank in enumerate(banks):

	bankstr += str(bank[0])+'\t'+str(bank[1])+"\r\n"

    # Pks transversales
    pks_trans = grass.read_command('v.db.select', map=MapTrans, columns='pk')
    pks_trans = pks_trans.splitlines(0)
    pks_trans = [float(p.replace('+','')) for p in pks_trans[1:]]

    manning=manning.replace(',',' \t')
    manningsal=manning+'\r\n'
    distran = ""
    for i,punt in enumerate(linea_ptos[0][:-1]):
        manningsal+= manning+'\r\n'
        distran += str(linea_ptos[0][i+1][4]-linea_ptos[0][i][4])+'\t'+str(pks_trans[i+1]-pks_trans[i])+'\t'+str(linea_ptos[-1][i+1][4]-linea_ptos[-1][i][4])+'\r\n'

    with open(namesal+'_lengths.txt', 'wb') as f:
        f.write(distran)
    f.closed
    with open(namesal+'_manning.txt', 'wb') as f:
        f.write(manningsal)
    f.closed
    with open(namesal+'_banks.txt', 'wb') as f:
        f.write(bankstr)
    f.closed

    return 0

###############################################################################


def import_HecRas(nament,namesal):

    with open(nament, 'r') as f:
        fileH=f.read()
    f.closed

    eje = re.findall(r'CENTERLINE:(.*?)END:',fileH,re.S|re.I)
    eje = eje[0].split(', ,')
    eje = [d.split(',') for d in eje]
    eje = eje[0:-1]
    for j,punt in enumerate(eje):
        eje[j]= [d.strip() for d in punt]
    #print eje

    cotas = re.findall(r'WATER ELEVATION:(.*)',fileH)
    cotas = [d.strip() for d in cotas]

    inund=''
    for i,p in enumerate(eje):
        inund+= p[0]+' '+p[1]+' '+cotas[i]+' '+str(len(eje)-i)+'\n'
    inund+= eje[-1][0]+' '+eje[-1][0]+' '+cotas[-1]+' 1\n'

    with open(options['outprofilefile'], 'w') as f:
        f.write(inund)
    f.closed

    coor = re.findall(r'WATER SURFACE EXTENTS:(.*?)END:',fileH,re.S|re.I)
    coor = [d.split(',') for d in coor]
    for j,punt in enumerate(coor):
        coor[j]= [d.strip() for d in punt]

    polygon=[]
    polygon2=[]
    for j,punt in enumerate(coor):

        polygon.append(coor[j][0:2])
        polygon2.append(coor[j][2:])

    polygon2.reverse()
    for j,punt in enumerate(polygon2):
        polygon.append(punt)
    for j,punt in enumerate(polygon):
        polygon[j].append('0.0')
    #print polygon
    #print coor
    write_Polygon(polygon,namesal)

    return 0




# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #
# ### Main
# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

def main():

    MapTrans=options['mapcross']
    MapCrossDispl=options['mapcrossdispl']
    Dem=options['dem']

    #### Hec-Ras section ####

    if flags['e']:

        write_HecRasGeom2(MapTrans,Dem,options['output'])

        write_HecRasTables2(MapTrans,MapCrossDispl,options['manning'],options['output'])



    if flags['i']:

        infile = options['inputfile']
        import_HecRas(infile,options['outwaterfile'])


    sys.exit(0)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
