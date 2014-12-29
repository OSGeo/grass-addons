#!/usr/bin/env python
# -*- coding: utf-8
############################################################################
#
# MODULE:       v.civil.topo, v0.5.0
#
# AUTHOR:       Jesús Fernández-Capel Rosillo
#               Civil Engineer, Spain
#               jfc at alcd net
#
# PURPOSE:      Create and modific Points-Breaklines maps, and triangulate,
#               using triangle with v.triangle and nn with r.surf.nnbathy
#
# COPYRIGHT:    (c) 2014 Jesús Fernández-Capel Rosillo.
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Create and modify Points-Breaklines maps, and triangulate, with triangle with v.triangle and nn with r.surf.nnbathy
#% keywords: vector
#% keywords: TOPO
#% keywords: topography
#%end

#### Input section ####

#%option
#% key: points
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of input points vector map
#% required: yes
#% guisection: Input
#%end

#%option
#% key: breaklines
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of input break lines vector map
#% required: no
#% guisection: Input
#%end

#%option
#% key: contorno
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of area vector map for mask
#% required: no
#% guisection: Input
#%end


#### Topo section ####

#%flag
#% key: e
#% description: Patch for edit, points and breaklines maps
#% guisection: Topo
#%end


#%flag
#% key: u
#% description: Update topo map
#% guisection: Topo
#%end

#%flag
#% key: s
#% description: Split maps in points and breaklines maps
#% guisection: Topo
#%end

#%flag
#% key: l
#% description: Split breaklines in segments
#% guisection: Topo
#%end

#%flag
#% key: p
#% description: Create points in vertices of polylines
#% guisection: Topo
#%end

#%option G_OPT_V_OUTPUT
#% key: topomap
#% gisprompt: new,vector,vector
#% description: Name for output topo map
#% required: no
#% guisection: Topo
#%end

#%option
#% key: cats
#% type: string
#% description: Cats of lines
#% required: no
#% guisection: Topo
#%end

#%option
#% key: splitlength
#% type: double
#% description: Split segment length
#% answer: 10
#% required: no
#% guisection: Topo
#%end


#### Sup section ####

#%flag
#% key: t
#% description: Triangulate, create Dem and Contours using triangle
#% guisection: Sup
#%end

#%flag
#% key: y
#% description: Create Dem and Contours using nnbathy
#% guisection: Sup
#%end

#%flag
#% key: f
#% description: Patch tindem with dem and generate contours
#% guisection: Sup
#%end

#%flag
#% key: n
#% description: Patch nnbathydem with dem and generate contours
#% guisection: Sup
#%end


#%option
#% key: step
#% type: double
#% description: Increment between contour levels
#% answer: 1
#% guisection: Sup
#% required: no
#%end

##%option
##% key: cut
##% type: integer
##% description: It acts like a filter omitting spurs single points etc
##% answer: 0
##% guisection: Sup
##% required: no
##%end

#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: raster dem
#% description: Name of DEM raster map
#% guisection: Sup
#% required: no
#%end


#%option G_OPT_V_OUTPUT
#% key: tin
#% description: Name of tin map
#% required: no
#% answer: _Tin
#% guisection: Sup
#%end

#%option G_OPT_R_OUTPUT
#% key: tindem
#% description: Name of dem map created with tin
#% required: no
#% answer: _TinDem
#% guisection: Sup
#%end

#%option G_OPT_V_OUTPUT
#% key: tincontour
#% description: Name of tin dem curves map
#% required: no
#% answer: _TinDemCurves
#% guisection: Sup
#%end

#%option G_OPT_R_OUTPUT
#% key: nndem
#% description: Name of dem map created with nnbathy
#% required: no
#% answer: _NNbathyDem
#% guisection: Sup
#%end

#%option G_OPT_V_OUTPUT
#% key: nncontour
#% description: Name of nnbathy dem curves map
#% required: no
#% answer: _NNbathyDemCurves
#% guisection: Sup
#%end

#%option G_OPT_R_OUTPUT
#% key: tindemDem
#% description: Name of dem map created with tin
#% required: no
#% answer: _TinDemDem
#% guisection: Sup
#%end

#%option G_OPT_V_OUTPUT
#% key: tinDemcontour
#% description: Name of tin dem curves map
#% required: no
#% answer: _TinDemDemCurves
#% guisection: Sup
#%end

#%option G_OPT_R_OUTPUT
#% key: nndemDem
#% description: Name of dem map created with nnbathy
#% required: no
#% answer: _NNbathyDemDem
#% guisection: Sup
#%end

#%option G_OPT_V_OUTPUT
#% key: nnDemcontour
#% description: Name of nnbathy dem curves map
#% required: no
#% answer: _NNbathyDemDemCurves
#% guisection: Sup
#%end


import os, sys, re
from math import *
import grass.script as grass

###############################################################################

def get_pts_Recta(xo,yo,zo,Az,Ini,Fin,difcotas,L_int,Lacum,cat,ali):
    # Return matriz de puntos, resto
    if L_int==0: L_int=1
    M=[]
    Lz=0
    alpha=atan(difcotas/Fin)
    print Ini,Fin,difcotas,alpha
    while  Ini <= Fin:
        x2=xo+Ini*sin(Az)
        y2=yo+Ini*cos(Az)
        Lacum+=L_int
        Lz+=L_int
        print Lz,L_int,Lacum,Ini
        z2=zo+(Lz)*tan(alpha)
        print zo,z2
        M.append([x2,y2,z2,cat,Lacum,Az,'Line',ali])
        cat=cat+1
        Ini+=L_int
    return M,Fin-(Ini-L_int),Lacum,cat

def discr_Lines(lines,discr):

    disLines=[]
    for pto in lines:
        resto,acum=0,0
        cat_r=1
        disptos=[]
        for i in range(len(pto[:-1])):

            disptos.append(pto[i])
            Az=azimut(pto[i][0],pto[i][1],pto[i+1][0],pto[i+1][1])
            difcotas=pto[i+1][2]-pto[i][2]
            print difcotas
            Lrecta=sqrt((pto[i+1][0]-pto[i][0])**2+(pto[i+1][1]-pto[i][1])**2)
            Ptos_recta,resto,acum,cat_r=get_pts_Recta(pto[i][0],pto[i][1],pto[i][2],Az,discr-resto,Lrecta,difcotas,discr,acum,cat_r,i)
            disptos.extend(Ptos_recta)
        disptos.append(pto[i+1])
        disLines.append(disptos)
    return disLines

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

def write_Polylines(lines,name,layer,catt):

    sal_linea=""
    if layer > 1: tool="add"
    else: tool="create"
    tolines,cats=splitdlines(lines)

    for j,line in enumerate(tolines):
        sal_linea+="L "+str(len(line))+" 1\n"
        for i,pto in enumerate(line):
            sal_linea+=str(pto[0])+" "+str(pto[1])+" "+str(pto[2])+"\n"
        sal_linea+=str(layer)+" "+str(cats[j]+catt-1)+"\n"

    grass.write_command('v.edit', flags='n', tool=tool, map=name, input='-', stdin=sal_linea, overwrite=True, quiet=True)
    return 0

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

# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

def generate_Segments(splitlength,catts,tmpMap):

    lines=grass.read_command('v.out.ascii', input=tmpMap, output='-', type='line', cats=catts, format='standar', layer=2, quiet=True)
    lines = lines.split('L  ')

    lines = [d.splitlines(0) for d in lines[1:]]
    for i,line in enumerate(lines):
        lines[i]=[p.split() for p in line[1:-1]]
    for i,line in enumerate(lines):
        for j,pto in enumerate(line):
            lines[i][j]=[float(p) for p in pto]

    lines = discr_Lines(lines,float(splitlength))

    grass.run_command('v.edit', map=tmpMap, layer=2, tool='delete', where='cat2='+str(catts), quiet=True)
    #grass.run_command('v.edit', map=tmpMap, layer=2, tool='catdel', where='cat2='+str(cats))
    write_Polylines(lines,tmpMap,2,int(catts))
    return 0

def generate_Points(catts,tmpMap):

    lines=grass.read_command('v.out.ascii', input=tmpMap, output='-', type='line', cats=catts, format='standar', layer=2, quiet=True)
    lines = lines.split('L  ')

    lines = [d.splitlines(0) for d in lines[1:]]
    for i,line in enumerate(lines):
        lines[i]=[p.split() for p in line[1:-1]]

    ptos=grass.read_command('v.out.ascii', input=tmpMap, type='point')
    ptos = ptos.splitlines(0)
    i = int(ptos[-1].split("|")[-1])

    sal_puntos=""
    for j,line in enumerate(lines):
        for pp in line:
            if pp==[]: continue
            sal_puntos+="P  1 1 \n"
            sal_puntos+=" "+str(pp[0])+" "+str(pp[1])+" "+str(pp[2])+" \n"
            sal_puntos+=" 1  "+str(i+1)+" \n"
            i=i+1
    print sal_puntos
    grass.write_command('v.edit', tool='add', map=tmpMap, flags='n', type='point', input='-', stdin=sal_puntos, overwrite=True)
    grass.run_command('v.to.db', map=tmpMap, option='cat', columns='cat')

    return 0

# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #

def patch_maps(pointsMap,linesMap,tmpMap):

    grass.run_command('g.copy', vector=pointsMap+','+tmpMap)

    # lee las columnas de mapa de puntos y inserta las columnas si no existen
    columsPts=grass.read_command('db.columns', table=tmpMap)
    columsPts=columsPts.splitlines(0)
    if 'x' not in columsPts:
        grass.run_command('v.db.addcolumn', map=tmpMap, columns='x double')
    if 'y' not in columsPts:
        grass.run_command('v.db.addcolumn', map=tmpMap, columns='y double')
    if 'z' not in columsPts:
        grass.run_command('v.db.addcolumn', map=tmpMap, columns='z double')
    if 'action' not in columsPts:
        grass.run_command('v.db.addcolumn', map=tmpMap, columns='action varchar(4)')

    # Inserta una nueva tabla en layer 2
    grass.run_command('v.db.addtable', map=tmpMap, layer=2, key='cat2', table=tmpMap+"_breaklines")

    # lee mapa de lineas e incrementa el layer a 2
    lines=grass.read_command('v.out.ascii', input=linesMap, output='-', format='standar', layer=1, quiet=True)
    lines=lines.replace(' 1     ',' 2     ')

    grass.write_command('v.edit',  tool='add', map=tmpMap, input='-', stdin=lines, overwrite=True)
    grass.run_command('v.to.db', map=tmpMap, layer=2, option='cat', columns='cat2')

    # Insertamos las columnas de breaklines si existen
    tables=grass.read_command('db.tables', flags='p')
    tables=tables.splitlines(0)

    if linesMap.split('@')[0] in tables:
        columsLines=grass.read_command('db.columns', table=linesMap.split('@')[0])
        columsLines=columsLines.splitlines(0)[1:]
        columsLines=','.join(columsLines)

        grass.run_command('v.db.join', map=tmpMap, layer=2, column='cat2', otable=linesMap.split('@')[0], ocolumn='cat', scolumns=columsLines)

    return 0

###############################################################################

def update_tmpMap(tmpMap):

    # leemos las coordenadas de la tabla y la accion
    lines = grass.read_command('v.db.select', map=tmpMap, columns='cat,x,y,z,action', quiet=True)
    lines = [d.split('|') for d in lines.splitlines(0)]
    del lines[0]

    # leemos las coordenadas originales de los puntos
    lines_org = grass.read_command('v.to.db', flags='p', map=tmpMap, layer=1, option='coor', columns='x,y,z', quiet=True)
    lines_org = [d.split('|') for d in lines_org.splitlines(0)]

    # Calculamos las distancias entre las dos coordenadas
    distances=[]
    for i,pto in enumerate(lines):
        if pto[4] != '' and pto[4] != ' ':
            for j,pto_org in enumerate(lines_org):
                if pto[0] == pto_org[0]:

                    distan=[pto[0]]
                    if pto[1] != '':
                        distan.append(float(pto[1])-float(pto_org[1]))
                    else:
                        distan.append(0)
                    if pto[2] != '':
                        distan.append(float(pto[2])-float(pto_org[2]))
                    else:
                        distan.append(0)
                    if pto[3] != '':
                        distan.append(float(pto[3])-float(pto_org[3]))
                    else:
                        distan.append(0)
                    break
            distances.append(distan)

    if distances != []:
        # Movemos los puntos seleccionados en action
        for dist in distances:

            g.message(dist[0]+','+str(dist[1])+','+str(dist[2])+','+str(dist[3]))
            grass.run_command('v.edit', map=tmpMap, type='point', tool='move',
                              move=str(dist[1])+','+str(dist[2])+','+str(dist[3]), cats=dist[0], quiet=True)
            # Actualizamos action en la tabla
            grass.run_command('v.db.update', map=tmpMap, layer=1, column='action', value=' ', where='cat='+dist[0])

    return 0

###############################################################################

def split_maps(pointsMap,linesMap,tmpMap):

    grass.run_command('v.extract', input=tmpMap, type='point', where='cat>0', output=pointsMap, quiet=True)

    lines=grass.read_command('v.out.ascii', input=tmpMap, output='-', format='standar', layer=2, quiet=True)
    lines=lines.replace(' 2     ',' 1     ')
    grass.write_command('v.edit',  tool='create', map=linesMap, input='-', stdin=lines, quiet=True)
    grass.run_command('v.db.addtable', map=linesMap, layer=1, key='cat', quiet=True)
    grass.run_command('v.to.db', map=linesMap, layer=1, option='cat', columns='cat', quiet=True)

    columsLines=grass.read_command('db.columns', table=tmpMap+"_breaklines", quiet=True)

    if len(columsLines) > 1:
        columsLines=columsLines.splitlines(0)[1:]
        columsLines=','.join(columsLines)
        grass.run_command('v.db.join', map=linesMap, layer=1, column='cat', otable=tmpMap+"_breaklines", ocolumn='cat2', scolumns=columsLines, quiet=True)

    return 0

# ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### #
# ### Main
# ###

def main():

    PtosMap=options['points']
    BreakMap=options['breaklines']
    HullMap=options['contorno']

    if re.search(r'_Points', options['points']):
        OutName=PtosMap.replace("_Points","")
    else:
        OutName=options['points']

    OutName=OutName.split('@')[0]

    if re.search(r'^_', options['tin']): nameTin=OutName+options['tin']
    else: nameTin=options['tin']

    if re.search(r'^_', options['tindem']): nameTinDem=OutName+options['tindem']
    else: nameTinDem=options['tindem']

    if re.search(r'^_', options['tincontour']): nameTinDemC=OutName+options['tincontour']
    else: nameTinDemC=options['tincontour']

    if re.search(r'^_', options['nndem']): nameNNDem=OutName+options['nndem']
    else: nameNNDem=options['nndem']

    if re.search(r'^_', options['nncontour']): nameNNDemC=OutName+options['nncontour']
    else: nameNNDemC=options['nncontour']


    if re.search(r'^_', options['tindemDem']): nameTinDemDem=OutName+options['tindemDem']
    else: nameTinDemDem=options['tindemDem']

    if re.search(r'^_', options['tinDemcontour']): nameTinDemDemC=OutName+options['tinDemcontour']
    else: nameTinDemDemC=options['tinDemcontour']

    if re.search(r'^_', options['nndemDem']): nameNNDemDem=OutName+options['nndemDem']
    else: nameNNDemDem=options['nndemDem']

    if re.search(r'^_', options['nnDemcontour']): nameNNDemDemC=OutName+options['nnDemcontour']
    else: nameNNDemDemC=options['nnDemcontour']



#### Point section ####

    if flags['e']:
        grass.message("Patching points and breaklines maps")
        patch_maps(PtosMap,BreakMap,options['topomap'])

    if flags['u']:
        grass.message("Updating topo map")
        update_tmpMap(options['topomap'])

    if flags['s']:
        grass.message("Spliting in points and breaklines maps")
        split_maps(PtosMap,BreakMap,options['topomap'])

#### Breaklines section ####

    if flags['p']:
        grass.message("Generate points in vertices of polylines")
        generate_Points(int(options['cats']),options['topomap'])

    if flags['l']:
        grass.message("Spliting breaklines map")
        generate_Segments(options['splitlength'],int(options['cats']),options['topomap'])

#### Sup section ####

    if flags['t']:
        grass.message("Triangulating tin")
        cmd='/mnt/trb/addons/v.triangle/v.triangle.v7 points='+PtosMap
        if BreakMap != "": cmd += ' lines='+BreakMap
        cmd += ' tin='+nameTin+' --o --q'
        os.system(cmd)
        print cmd

        grass.run_command('v.tin.to.raster', map=nameTin, output=OutName+"_TinDem_borrar", overwrite=True)
        grass.run_command('v.to.rast', input=HullMap, output=HullMap, use='val', overwrite=True, quiet=True)

        os.system("r.mapcalc '"+nameTinDem+" = if("+HullMap+"==1"+", "+OutName+"_TinDem_borrar"+", null())' --o --q")
        grass.run_command('r.contour', input=nameTinDem, output=nameTinDemC, step=options['step'], overwrite=True, quiet=True)
        grass.run_command('g.remove', flags='f', type='raster', name=OutName+"_TinDem_borrar")

    if flags['y']:
        grass.message("Triangulating nnbathy")
        grass.run_command('v.to.rast', input=PtosMap, output=PtosMap, use='z', overwrite=True, quiet=True)

        os.system('/mnt/trb/addons/r.surf.nnbathy/r.surf.nnbathy.sh input='+PtosMap+' output='+OutName+"_NNbathyDem_borrar"+' alg=l --o --q')

        grass.run_command('v.to.rast', input=HullMap, output=HullMap, use='val', overwrite=True, quiet=True)

        os.system("r.mapcalc '"+nameNNDem+" = if("+HullMap+"==1"+", "+OutName+"_NNbathyDem_borrar"+", null())' --o --q")
        grass.run_command('r.contour', input=nameNNDem, output=nameNNDemC, step=options['step'], overwrite=True, quiet=True)
        grass.run_command('g.remove', flags='f', type='raster', name=OutName+"_NNbathyDem_borrar")

    if flags['f']:
	grass.message("Patching timdem with dem")
        grass.run_command('r.patch', input=nameTinDem+","+options['dem'], output=nameTinDemDem, overwrite=True, quiet=True)
        grass.run_command('r.contour', input=nameTinDemDem, output=nameTinDemDemC, step=1, overwrite=True, quiet=True)

    if flags['n']:
        grass.message("Patching nnbathydem with dem")
	grass.run_command('r.patch', input=nameNNDem+","+options['dem'], output=nameNNDemDem, overwrite=True, quiet=True)
        grass.run_command('r.contour', input=nameNNDemDem, output=nameNNDemDemC, step=1, overwrite=True, quiet=True)

    sys.exit(0)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
