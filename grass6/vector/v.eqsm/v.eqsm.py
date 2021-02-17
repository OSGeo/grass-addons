#!/usr/bin/env python
#
###################################################################
#
# MODULE:    	v.eqsm.py
# AUTHOR(S): 	Annalisa Minelli <annalisa.minelli AT gmail.com>
# PURPOSE:   	Performs vertical sorting analysis prediction for one or more points in a river reach using Blom&Parker Equilibrium Sorting Model (2006)
# COPYRIGHT: 	(C) 2009 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
####################################################################
#
#%Module
#%  description: Implements Equilibrium Sorting Model at reach scale for a bimodal sediment mixture (Blom&Parker)
#%  keywords: eqsm
#%end
#%flag
#%  key: m
#%  description: Multiple point calculation
#%end
#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% description: Input dem of the zone
#% required: no
#%end
#%option
#% key: input_csv
#% type: string
#% gisprompt: old_file,file,input
#% key_desc: name
#% description: .csv file in output from the laser scanner - lab_mode only -
#% required: no
#% guisection: DEM importation
#%end
#%option
#% key: type
#% type: string
#% description: file type
#% options: key,mas,snr
#% required: no
#% guisection: DEM importation
#%end
#%option
#% key: outputDEM
#% type: string
#% gisprompt: new,cell,raster
#% description: DEM interpolated
#% required: no
#% guisection: DEM importation
#%end
#%option
#% key: vector
#% type: string
#% gisprompt: old,vector,vector
#% description: Input vector file of examined fluvial reach
#% required: yes
#%end
#%option
#% key: res
#% type: double
#% description: Resolution how to work [meters or mm for field or lab mode respectively]
#% required: yes
#%end
#%option
#% key: fiuno
#% type: double
#% description: Dimension of first grainsize examined [phi]
#% required: yes
#%end
#%option
#% key: fidue
#% type: double
#% description: Dimension of second grainsize examined [phi]
#% required: yes
#%end
#%option
#% key: dmax
#% type: double
#% description: Maximum depth where to perform the analysis [meters or mm for field or lab mode respectively]
#% required: yes
#%end
#%option
#% key: nstep
#% type: double
#% description: Number of steps (in depth) where to perform the analysis
#% required: yes
#%end
#%option
#% key: lee_out
#% type: string
#% gisprompt: new,vector,vector
#% description: Vector file of lee faces in output from model
#% required: yes
#%end
#%option
#% key: point_out
#% type: string
#% gisprompt: new,vector,vector
#% description: Vector file of point/s reporting results of the prediction
#% required: no
#%end
#%option
#% key: ros
#% type: double
#% description: Bed-load material density [N/mc]
#% required: yes
#% guisection: Bedload info
#%end
#%option
#% key: to
#% type: double
#% description: Averaged bed shear stress [Pa]
#% required: yes
#% guisection: Bedload info
#%end
#%option
#% key: fauno
#% type: double
#% description: Volume fraction of material of first grainsize in bed-load transport [%]
#% required: yes
#% guisection: Bedload info
#%end
#%option
#% key: fadue
#% type: double
#% description: Volume fraction of material of second grainsize in bed-load transport [%]
#% required: yes
#% guisection: Bedload info
#%end
#%option
#% key: n_iter
#% type: integer
#% description: Number of iterations to execute in performing Fi predictions
#% required: yes
#%end
#%option
#% key: txtout
#% type: string
#% description: Output text file where to store results of the prediction
#% required: yes
#%end
#%option
#% key: graphout
#% type: string
#% description: Prefix for output graphs of vertical sorting for each point selected (final format: prefix_point1, prefix_point2, ...)
#% required: yes
#%end

import sys,os,re,math,numpy
import grass.script as grass
import matplotlib.pyplot as plt

#OK FUNZIA
def import_csv(res,input_csv,type,outputDEM):
    """Cleans the .csv file in output from the laser scanner, imports points in GRASS GIS and interpolates bed surface using idw method"""
    prova1=open(input_csv,"rw")
    array=(prova1.readlines())
    if type == 'key':
        array2=array[20:]
    elif type == 'mas':
        array2=array[21:]
    elif type == 'snr':
        array2=array[33:]
    i=0
    p=open("p","w")
    for b in array2:
        s=re.split(",",array2[i])[5]
        if s == 'OutOfRange\r\n' or s == 'OutOfRange' or s == 'OutOfRange\r' or s == 'OutOfRange\r\n' or s == '"OutOfRange"\r\n' or s == '"OutOfRange"' or s == '"OutOfRange"\r' or s == '"OutOfRange\r\n"':
            i=i+1
            continue
        else:
            x=float(re.split(",",array2[i])[2])
            y=float(re.split(",",array2[i])[3])
            z=float(re.split("\r",s)[0])
            c=str(x)+'|'+str(y)+'|'+str(z)
            p.write(c)
            p.write('\n')
            i=i+1
    p.close()
    grass.run_command('v.in.ascii',input='p',output='provadb')
    grass.run_command('g.region',vect='provadb',n='n+100',e='e+100',w='w-100',s='s-100')
    grass.run_command('g.region',flags='a',res=res)
    grass.run_command('v.surf.idw',input='provadb',npoints='2',power='1.0',column='dbl_3',output=outputDEM)


#OK FUNZIA
def general_geom(vector,dem,res):
    """Defines some general information about geometry of the reach studied"""
    grass.run_command('g.region',vect=vector,n='n+100',s='s-100',e='e+100',w='w-100')
    grass.run_command('v.drape',input=vector,type='line',rast=dem,output='vector_drape',method='nearest',scale='1.0',layer='1')
    start=(grass.read_command('v.to.db',flags='p',map='vector_drape',option='start',columns='Estart,Nstart,Zstart').split('\n')[1]).split('|')[1:3]
    end=(grass.read_command('v.to.db',flags='p',map='vector_drape',option='end',columns='Eend,Nend,Zend').split('\n')[1]).split('|')[1:3]
    profilec=(grass.read_command('r.profile',input=dem,profile=start[0]+','+start[1]+','+end[0]+','+end[1],res=res)).split('\n')[0:-1]
    x=[]
    z=[]
    for i in profilec:
        x.append(float(i.split(' ')[0]))
        z.append(float(i.split(' ')[1]))
    xline=x[0],x[-1]
    zline=z[0],z[-1]
    length=float(((grass.read_command('v.to.db',flags='pc',map='vector_drape',type='line',layer='1',qlayer='1',option='length',units='meters')).split(' ')[-1]).split('\n')[0])
    deltatot=float(((grass.read_command('v.info',flags='g',map='vector_drape')).split('\n')[-3]).split('=')[-1])-float(((grass.read_command('v.info',flags='g',map='vector_drape')).split('\n')[-2]).split('=')[-1])
    rad=math.atan(deltatot/length)
    return x,z,xline,zline,length,deltatot,rad


#OK_FUNZIA
def lines_sl(vector,res,dem,stoss_dradd,lee_dradd):
    """Classifies segments of the original reach file in stoss and lee faces, in reason of the heigth of start and ending point of each one read by DEM, for calculation issues the reach is extended of an half resolution length, so the first segment (outlet of the reach) has not to be considered"""
    grass.run_command('g.remove',vect='preso_punto,presoo,preso_ok,vector_pezzi,vector_pezzi_add,vector_pezzi_del,vector_drape_pezzi,vector_lee,vector_stoss,tratti_leep,tratti_stossp,tratti_lee_del,lee_dradd')
    newE=float((re.split('\n',grass.read_command('v.to.db',flags='p',map=vector,option='start',column='Es,Ns'))[1]).split('|')[1])
    newN=float((re.split('\n',grass.read_command('v.to.db',flags='p',map=vector,option='start',column='Es,Ns'))[1]).split('|')[2])
    grass.write_command('v.in.ascii',output='preso_punto',stdin=str(newE)+'|'+str(newN))
    grass.run_command('v.net',input=vector,points='preso_punto',output='presoo',operation='connect',thresh=res)
    grass.run_command('v.edit',map='presoo',layer='1',type='line',tool='delete',thresh='-1,0,0',ids='1',snap='no')
    grass.run_command('v.edit',map='presoo',layer='1',type='point',tool='delete',thresh='-1,0,0',ids='1-999',snap='no')
    grass.run_command('v.build.polylines',input='presoo',output='preso_ok')
    grass.run_command('v.split',input='preso_ok',output='vector_pezzi',length=0.999*float(res))
    grass.run_command('v.category',input='vector_pezzi',output='vector_pezzi_del',option='del',type='line',cat='1',step='1')
    grass.run_command('v.category',input='vector_pezzi_del',output='vector_pezzi_add',option='add',type='line',cat='1',step='1')
    grass.run_command('v.drape',input='vector_pezzi_add',type='line',rast=dem,output='vector_drape_pezzi',method='nearest',scale='1.0',layer='1')
    grass.run_command('v.db.addtable',map='vector_drape_pezzi',columns='cat integer,startE double precision,startN double precision,startZ double precision,endE double precision,endN double precision,endZ double precision')
    grass.run_command('v.to.db',map='vector_drape_pezzi',type='line',layer='1',qlayer='1',option='start',units='meters',columns='startE,startN,startZ')
    grass.run_command('v.to.db',map='vector_drape_pezzi',type='line',layer='1',qlayer='1',option='end',units='meters',columns='endE,endN,endZ')
    firstcat_endZ=float((grass.read_command('db.select',flags='c',table='vector_drape_pezzi').split('\n')[0]).split('|')[-1])
    lastcat_endZ=float((grass.read_command('db.select',flags='c',table='vector_drape_pezzi').split('\n')[-2]).split('|')[-1])
    if lastcat_endZ < firstcat_endZ:
        grass.run_command('v.extract',input='vector_drape_pezzi',output='vector_lee',type='line',layer='1',where="endZ<=startZ",new='-1')
        grass.run_command('v.extract',input='vector_drape_pezzi',output='vector_stoss',type='line',layer='1',where="endZ>startZ",new='-1')
    else:
        grass.run_command('v.extract',input='vector_drape_pezzi',output='vector_lee',type='line',layer='1',where="endZ>=startZ",new='-1')
        grass.run_command('v.extract',input='vector_drape_pezzi',output='vector_stoss',type='line',layer='1',where="endZ<startZ",new='-1')
    grass.run_command('v.build.polylines',input='vector_lee',output='tratti_leep',cats='no')
    grass.run_command('v.build.polylines',input='vector_stoss',output='tratti_stossp',cats='no')
    grass.run_command('v.category',input='tratti_stossp',output='tratti_stoss_del',option='del',type='line',layer='1',cat='1',step='1')
    grass.run_command('v.category',input='tratti_stoss_del',output=stoss_dradd,option='add',type='line',layer='1',cat='1',step='1')
    grass.run_command('v.category',input='tratti_leep',output='tratti_lee_del',option='del',type='line',layer='1',cat='1',step='1')
    grass.run_command('v.category',input='tratti_lee_del',output=lee_dradd,option='add',type='line',layer='1',cat='1',step='1')
    return lastcat_endZ,firstcat_endZ

#OK FUNZIA!
def populate_lines(lee_dradd,vector_pezzi_add,firstcat_endZ,lastcat_endZ,rad,deltatot,length,stoss_dradd,lee_out,dem,point_out):
    """Populates database of lee faces vector file with start end ending point coords, length and delta of each segment, eta and lambda are evaluated as subroutines"""
    grass.run_command('g.remove',vect='vector_del,vector_add,take_this,point_del')
    grass.run_command('v.db.addtable',map=lee_dradd,columns='cat integer,startE double precision,startN double precision,startZ double precision,endE double precision,endN double precision,endZ double precision')
    grass.run_command('v.to.db',map=lee_dradd,type='line',layer='1',qlayer='1',option='start',units='meters',columns='startE,startN,startZ')
    grass.run_command('v.to.db',map=lee_dradd,type='line',layer='1',qlayer='1',option='end',units='meters',columns='endE,endN,endZ')
    grass.run_command('v.db.addtable',map=vector_pezzi_add,layer='1',columns='cat integer,length double precision,startE double precision,startN double precision,endE double precision,endN double precision')
    grass.run_command('v.to.db',map=vector_pezzi_add,option='length',type='line',units='meters',columns='length')
    grass.run_command('v.to.db',map=vector_pezzi_add,option='start',type='line',units='meters',columns='startE,startN')
    grass.run_command('v.to.db',map=vector_pezzi_add,option='end',type='line',units='meters',columns='endE,endN')
    grass.run_command('v.db.addcol',map=lee_dradd,column='delta double precision,etat double precision,etab double precision')
    vector_length=re.split('\n',grass.read_command('db.select',flags='c',table=vector_pezzi_add,driver='dbf'))[:-1]
    lee_drad=re.split('\n',grass.read_command('db.select',table=lee_dradd,driver='dbf'))[1:-1]
    for i in lee_drad:
        cat=str(i.split('|')[0])
        estart=str(i.split('|')[1])
        nstart=str(i.split('|')[2])
        eend=str(i.split('|')[4])
        nend=str(i.split('|')[5])
        if lastcat_endZ<firstcat_endZ:
            dtop=float(i.split('|')[3])
            dbottom=float(i.split('|')[6])
        else:
            dtop=float(i.split('|')[6])
            dbottom=float(i.split('|')[3])
        d=[]
        g=[]
        v=[]
        for c in vector_length:
            d.append(str(str(c.split('|')[2])+'|'+str(c.split('|')[3])+'|'+str(c.split('|')[0])))
            g.append(str(str(c.split('|')[4])+'|'+str(c.split('|')[5])+'|'+str(c.split('|')[0])))
            v.append(int(c.split('|')[0]))
        coord1=str(estart)+'|'+str(nstart)
        coord2=str(eend)+'|'+str(nend)
        if lastcat_endZ<firstcat_endZ:
            catt=[int(f.split('|')[2]) for f in d if re.match(coord1,f)]
            catb=[int(f.split('|')[2]) for f in g if re.match(coord2,f)]
            min=lastcat_endZ
            lb=(max(v)-catb[0]-1)*float(vector_length[1].split('|')[1])
            lt=(max(v)-catt[0])*float(vector_length[1].split('|')[1])
        else:
            min=firstcat_endZ
            catb=[int(f.split('|')[2]) for f in d if re.match(coord1,f)]
            catt=[int(f.split('|')[2]) for f in g if re.match(coord2,f)]
            lb=(catb[0]-1)*float(vector_length[1].split('|')[1])
            lt=(catt[0])*float(vector_length[1].split('|')[1])
        deltab=lb*deltatot/length
        deltat=lt*deltatot/length
        zt=dtop-min
        zb=dbottom-min
        etab=(zb-deltab)*float(math.cos(rad))
        etat=(zt-deltat)*float(math.cos(rad))
        delta=abs(etat-etab)
        grass.run_command('v.db.update',map=lee_dradd,layer='1',column='etab',value=etab,where='cat='+str(cat))
        grass.run_command('v.db.update',map=lee_dradd,layer='1',column='etat',value=etat,where='cat='+str(cat))
        grass.run_command('v.db.update',map=lee_dradd,layer='1',column='delta',value=delta,where='cat='+str(cat))
    grass.run_command('v.db.addtable',map=stoss_dradd,columns='cat integer,length double precision')
    grass.run_command('v.to.db',map=stoss_dradd,type='line',layer='1',option='length',units='meters',columns='length')
    stoss_lambda=re.split('\n',grass.read_command('db.select',table=stoss_dradd,driver='dbf'))[1:-1]
    grass.run_command('v.db.addcol',map=lee_dradd,columns='length double precision,lambda double precision')
    grass.run_command('v.to.db',map=lee_dradd,type='line',layer='1',option='length',units='meters',columns='length')
    lee_lambda=re.split('\n',grass.read_command('db.select',table=lee_dradd,driver='dbf'))[1:-1]
    grass.run_command('v.category',input=vector_pezzi_add,output='vector_del',option='del')
    grass.run_command('v.category',input='vector_del',output='vector_add',option='add')
    grass.run_command('v.drape',input='vector_add',rast=dem,output=vector_pezzi_add)
    grass.run_command('v.extract',flags='t',input=vector_pezzi_add,output='one_add',type='line',list='1',new='-1')
    grass.run_command('v.extract',flags='t',input=lee_dradd,output='one_lee',type='line',list='1',new='-1')
    grass.run_command('v.select',ainput='one_add',atype='line',binput='one_lee',btype='line',output='take_this1')
    grass.run_command('v.select',ainput='one_lee',atype='line',binput='one_add',btype='line',output='take_this2')
    info1=int((grass.read_command('v.info',flags='t',map='take_this1').split('\n')[2]).split('=')[1])
    info2=int((grass.read_command('v.info',flags='t',map='take_this2').split('\n')[2]).split('=')[1])
    for i in lee_lambda:
        l_cat=int(i.split('|')[0])
        l_catj=l_cat+1
        l_lee=float(i.split('|')[10])
        if info1 != 0 or info2 !=0:
            try:
                l_stoss=float((stoss_lambda[l_cat-1]).split('|')[1])
            except IndexError:
                break
        else:
            try:
                l_stoss=float(stoss_lambda[l_catj-1].split('|')[1])
            except IndexError:
                break
        lambd=(l_lee+l_stoss)/float(math.cos(rad))
        grass.run_command('v.db.update',map=lee_dradd,layer='1',column='lambda',value=lambd,where='cat='+str(int(l_cat)))
        lee_lambda=(grass.read_command('db.select',flags='c',table=lee_dradd,driver='dbf').split('\n'))[:-1]
    grass.run_command('g.copy',vect=str(lee_dradd)+','+str(lee_out))
    return lee_lambda






#OK FUNZIA
def point_selection(lee_dradd,m,nstep,point_out,dem):
    """Allows you to select one or more sections for the prediction"""
    grass.run_command('g.remove',vect=point_out)
    grass.run_command('v.in.ascii',output=point_out,flags='e')
    grass.run_command('v.db.addtable',map=point_out,columns='cat integer,lee integer,E double precision,N double precision')
    nstep=int(nstep)
    for j in range(nstep+1):
        grass.run_command('v.db.addcol',map=point_out,columns='F1'+str(j+1)+' double precision,F2'+str(j+1)+' double precision')
    id_section=[]
    east_section=[]
    north_section=[]
    z_avg=[]
    z_pt=[]
    grass.run_command('d.vect',map=lee_dradd,color='255:0:0')
    print "+--------------------------------------------------------------------+"
    print "  Please zoom on the zone where you want to perform the prediction"
    print "+--------------------------------------------------------------------+"
    grass.run_command('d.zoom')
    if m:
        print "+----------------------------------------------------------------+"
        print "  Please select multiple points where to perform your prediction"
        print "+----------------------------------------------------------------+"
        output=(grass.read_command('d.what.vect',flags='xt',map=lee_dradd)).split('\n')
        for i in output:
            if re.match('category:',i):
                id_section.append(int(i.split(': ')[1]))
            elif re.match('.*\(E\).*',i):
                east_section.append(float(i.split('(E) ')[0]))
                north_section.append(float(((i.split('(E) ')[1])).split('(N')[0]))
    else:
        print "+------------------------------------------------------------+"
        print "  Please select the point where to perform your prediction"
        print "+------------------------------------------------------------+"
        output=(grass.read_command('d.what.vect',flags='1xt',map=lee_dradd)).split('\n')
        id_section=[int(i.split(': ')[1]) for i in output if re.match('category:',i)]
        east_section=[float(i.split('(E) ')[0]) for i in output if re.match('.*\(E\).*',i)]
        north_section=[float(((i.split('(E) ')[1])).split('(N')[0]) for i in output if re.match('.*\(E\).*',i)]
    n=0
    for h in east_section:
        grass.run_command('v.in.ascii',flags='e',output='out'+str(n))
        grass.write_command('v.in.ascii',output='out'+str(n),x='1',y='2',fs='|',stdin='%s|%s' % (h,north_section[n]))
        grass.run_command('v.db.addtable',map='out'+str(n),columns='cat integer,lee integer,E double precision,N double precision')
        for j in range(nstep+1):
            grass.run_command('v.db.addcol',map='out'+str(n),columns='F1'+str(j+1)+' double precision,F2'+str(j+1)+' double precision')
        grass.run_command('v.patch',flags='ae',input='out'+str(n),output=point_out)
        grass.run_command('v.category',input=point_out,option='del',output='point_del')
        grass.run_command('v.category',input='point_del',option='add',output=point_out)
        grass.run_command('v.db.update',map=point_out,layer='1',column='lee',value=str(id_section[n]),where='cat='+str(n+1))
        grass.run_command('v.to.db',map=point_out,option='cat',columns='cat')
        grass.run_command('v.to.db',map=point_out,option='coor',columns='E,N')
        n=n+1
    grass.run_command('v.db.update',map=point_out,layer='1',column='lee',value=str(id_section[0]),where='cat=1')
    n=0
    for i in id_section:
        Z=(float(grass.read_command('db.select',flags='c',sql='select startZ from lee_dradd where cat='+str(i),table='lee_dradd'))+float(grass.read_command('db.select',flags='c',sql='select endZ from lee_dradd where cat='+str(i),table='lee_dradd')))/2
        z_pt.append(float((grass.read_command('r.what',input=dem,east_north=str(east_section[n])+','+str(north_section[n]))).split('|')[3]))
        z_avg.append(Z)
        n=n+1
    return id_section,east_section,north_section,z_avg,z_pt


#OK FUNZIA!
def graphics(lee_lambda,x,z,xline,zline):
    """Draws distribution graphics for the reach profile and point/s examined"""
    import pylab
    delta_list=[]
    delta_log=[]
    etat_list=[]
    etat_abs=[]
    etab_list=[]
    etab_abs=[]
    cc=0
    cv=0
    me=0
    for i in lee_lambda:
        delta_list.append(float(i.split('|')[7]))
        delta_log.append(math.log(float(i.split('|')[7])))
        etat_list.append(float(i.split('|')[8]))
        etab_list.append(float(i.split('|')[9]))
        etat_abs.append(abs(float(i.split('|')[8])))
        etab_abs.append(abs(float(i.split('|')[9])))
        if float(i.split('|')[8])>0 and float(i.split('|')[9])>0:
            cv=cv+1
        elif float(i.split('|')[8])<0 and float(i.split('|')[9])<0:
            cc=cc+1
        else:
            me=me+1
    totlee=int(lee_lambda[-1].split('|')[0])
    pylab.plot(x,z)
    pylab.plot(xline,zline)
    pylab.axis([min(x),max(x),min(z)-100,max(z)+100])
    pylab.figtext(x=0.05,y=0.95,s='The profile is concave for the '+str(cc*100/totlee)+'%, convex for the '+str(cv*100/totlee)+'%, and average for the '+str(me*100/totlee)+'%,')
    pylab.figtext(x=0.05,y=0.92,s='respect to the mean bed level')
    pylab.xlabel('x [mm]')
    pylab.ylabel('z [mm]')
    pylab.savefig('reach_profile')
    pylab.close()
    pylab.hist(delta_list)
    pylab.xlabel('delta [mm]')
    pylab.ylabel('frequency')
    pylab.savefig('delta_raw')
    pylab.close()
    pylab.hist(delta_log)
    pylab.xlabel('ln(delta)')
    pylab.ylabel('density')
    pylab.savefig('delta_log')
    pylab.close()
    pylab.hist(etat_list)
    pylab.xlabel('etat [mm]')
    pylab.ylabel('frequency')
    pylab.savefig('etat_raw')
    pylab.close()
    pylab.hist(etab_list)
    pylab.xlabel('etab [mm]')
    pylab.ylabel('frequency')
    pylab.savefig('etab_raw')
    pylab.close()
    rankt=numpy.array(range(len(etat_list)+1))[1:]
    rankb=numpy.array(range(len(etab_list)+1))[1:]
    setat=numpy.array(sorted(etat_abs))
    setab=numpy.array(sorted(etab_abs))
    Fetat=numpy.array(rankt-0.3)/(len(setat)+0.4)
    Fetab=numpy.array(rankb-0.3)/(len(setab)+0.4)
    xtweib=numpy.array(numpy.log(setat))
    xbweib=numpy.array(numpy.log(setab))
    ytweib=numpy.array(numpy.log(-numpy.log(1-Fetat)))
    ybweib=numpy.array(numpy.log(-numpy.log(1-Fetab)))
    (a,b)=pylab.polyfit(xtweib,ytweib,1)
    pylab.plot(xtweib,ytweib,'o', xtweib,a*xtweib+b,'-')
    pylab.xlabel('ln(F(etat))')
    pylab.ylabel('ln(-ln(1-F(etat)))')
    pylab.savefig('etat_weibull')
    pylab.close()
    (a,b)=pylab.polyfit(xbweib,ybweib,1)
    pylab.plot(xbweib,ybweib,'o', xbweib,a*xbweib+b,'-')
    pylab.xlabel('ln(F(etab))')
    pylab.ylabel('ln(-ln(1-F(etab)))')
    pylab.savefig('etab_weibull')
    pylab.close()
    k_etab=a
    l_etab=numpy.exp(-b/k_etab)
    return k_etab,l_etab,delta_list,etab_list


#CORRETTA:
def weibull(x,k,l):
    return [0 if (x<0) else ((k/l) * (x/l)**(k-1) * math.e**(-(x/l)**k))]

def integ1(x,jzeta,lambd,delta,deltauno,z_star,k,l):
    return (((jzeta**2)/(lambd*delta))+((jzeta*deltauno*z_star)/(lambd*delta)))*(numpy.array(weibull(x,k,l)))

def integ2(x,jzeta,lambd,delta,deltadue,z_star,k,l):
    return (((jzeta**2)/(lambd*delta))+((jzeta*deltadue*z_star)/(lambd*delta)))*(numpy.array(weibull(x,k,l)))

def integ3(x,jzeta,delta,lambd,k,l):
    return (((jzeta)/(lambd*delta)))*(numpy.array(weibull(x,k,l)))

def numeric(id_section,east_section,north_section,dmax,nstep,z_pt,z_avg,lee_lambda,delta_list,etab_list,rad,fiuno,fidue,fauno,fadue,to,ros,k,l,n_iter,point_out):
    """Executes the Eqsm prediction on the point/s examined"""
    import scipy.integrate as integrate
    k=float(k)
    l=float(l)
    fiuno=float(fiuno)
    fidue=float(fidue)
    ros=float(ros)
    to=float(to)
    fauno=float(fauno)
    fadue=float(fadue)
    dmax=float(dmax)
    nstep=int(nstep)
    lambda_list=[]
    for i in lee_lambda:
        lambda_list.append(float(i.split('|')[10]))
    try:
        step=float(dmax/nstep)
    except ZeroDivisionError:
        step=0.0
    dval=[]
    for i in range(nstep):
        dval.append((i+1)*step)
    dval.insert(0,0.0)
    print dval
    n=0	
    for i in id_section:
        g=0
        for j in dval:
            etabi=float(lee_lambda[i-1].split('|')[9])
            etati=float(lee_lambda[i-1].split('|')[8])
            delta=float(lee_lambda[i-1].split('|')[7])
            lambd=float(lee_lambda[i-1].split('|')[10])
            est_start=float(lee_lambda[i-1].split('|')[1])
            nord_start=float(lee_lambda[i-1].split('|')[2])
            alfa=math.atan(delta/lambd)
            x_coord=math.sqrt( (float(east_section[n])-est_start)**2 + ((float(north_section[n]))-nord_start)**2 )
            z_abs=z_pt[n] - j
            z_star=(z_abs-z_avg[n])/delta
            if abs(z_abs-z_avg[n]) <= delta:
                jzeta=1
            else:
                jzeta=0
                print "z out of range"
#			jzeta=1
            cosa=math.cos(rad)
            dmedia=numpy.mean(delta_list)
            emedia=numpy.mean(etab_list)
            estd=numpy.std(etab_list)
            lmedia=numpy.mean(lambda_list)
            etabmin=numpy.min(etab_list)
            etabmax=numpy.max(etab_list)
            n_iter=int(n_iter)
            for c in range(n_iter):
                if c==0:
                    fleeuno=0.5
                    fleedue=0.5
                fimlee=((fiuno*fleeuno)+(fidue*fleedue))
                sigma=numpy.sqrt((fleeuno*(fiuno-fimlee)**2)+(fleedue*(fidue-fimlee)**2))
                taustarb=(to/(((ros-999.972)*9.81*2**(-fimlee))/1000))
                deltauno=-0.3*((fimlee-fiuno)/sigma)*taustarb**(-0.5)
                deltadue=-0.3*((fimlee-fidue)/sigma)*taustarb**(-0.5)
                A=1/(jzeta*(1+deltauno*z_star))
                omega=1/A
                Aprimo=1/(jzeta*(1+deltadue*z_star))
                omegaprimo=1/Aprimo
                B=fauno*(1-(deltauno/6)+((deltauno*dmedia)/(6*lmedia)))**(-1)
                C=fadue*(1-(deltadue/6)+((deltadue*dmedia)/(6*lmedia)))**(-1)
                E=integrate.quad(lambda x:integ1(x,jzeta,lambd,delta,deltauno,z_star,k,l),etabmin,etabmax)
                E=float(E[0])
                Eprimo=integrate.quad(lambda x:integ2(x,jzeta,lambd,delta,deltadue,z_star,k,l),etabmin,etabmax)
                Eprimo=float(Eprimo[0])
                F=integrate.quad(lambda x:integ3(x,jzeta,delta,lambd,k,l),etabmin,etabmax)
                F=float(F[0])
                fleeunou=A*(B/(B+C))*(E/F)
                fleeuno=(fleeunou+fleeuno)/2
                fleedueu=Aprimo*(C/(B+C))*(Eprimo/F)
                fleedue=(fleedueu+fleedue)/2
                c=c+1
            funo=fleeunou*omega
            fdue=fleedueu*omegaprimo
            grass.run_command('v.db.update',map=point_out,column='F1'+str(g+1),value=str(funo),where='cat='+str(n+1))
            grass.run_command('v.db.update',map=point_out,column='F2'+str(g+1),value=str(fdue),where='cat='+str(n+1))
            g=g+1
        n=n+1
#	resultPoint=(grass.read_command('db.select',flags='c',table=point_out)).split('\n')[:-2]
    resultPoint=(grass.read_command('db.select',flags='c',table=point_out)).split('\n')[:-1]
    resultp=[]
    for i in resultPoint:
        elemi=i.split('|')[1]
        if elemi == '':
            continue
        else:
            resultp.append(i)
    return resultp,dval


def results(fiuno,fidue,fauno,fadue,fivalues,dval,lee_lambda,txtout,graphout):
    """Draws output graphs and a text file report for the point(s) examined"""
    import pylab
    fout=open(txtout,'w')
    fout.write("~~~ Input Data Summary ~~~")
    fout.write('\n')
    fout.writelines("Grainsize examined:")
    fout.write('\n')
    fout.writelines('phi_1='+str(fiuno))
    fout.write('\n')
    fout.writelines('phi_2='+str(fidue))
    fout.write('\n')
    fout.writelines("Bedload composition:")
    fout.write('\n')
    fout.writelines('Fa_1='+str(fauno))
    fout.write('\n')
    fout.writelines('Fa_2='+str(fadue))
    fout.write('\n')
    fout.write('\n')
    fout.writelines("~~~ Prediction Results ~~~")
    fout.write('\n')
    neg=[]
    for i in dval:
        neg.append(float(i*(-1)))
    for i in fivalues:
        f=i.split('|')[4:][::2]
        fi=[]
        for j in f:
            fi.append(float(j))
        pylab.plot(fi,neg,'o',color='b')
        pylab.fill_betweenx(neg,fi,facecolor='orange')
        pylab.axis([0.0,1.0,min(neg),max(neg)])
        pylab.xlabel('F1, F2 [%]')
        pylab.ylabel('Relative depth from the bed surface [mm]')
        pylab.savefig(str(graphout)+'_point'+str(i[0])+'.png')
        pylab.close()
        east=float(i.split('|')[2])
        north=float(i.split('|')[3])
        cat=int(i.split('|')[1])
        deltalee=float(lee_lambda[cat-1].split('|')[7])
        etat=float(lee_lambda[cat-1].split('|')[8])
        etab=float(lee_lambda[cat-1].split('|')[9])
        fout.write('\n')
        fout.writelines("Output for point #"+str(i.split('|')[0])+":")
        fout.write('\n')
        fout.writelines("E [mm or m]="+str(east))
        fout.write('\n')
        fout.writelines("N [mm or m]="+str(north))
        fout.write('\n')
        fout.writelines("Total heigth of the bedform [mm or m]="+str(deltalee))
        fout.write('\n')
        fout.writelines("Crest heigth of the bedform over the mean heigth of the reach [mm or m]="+str(etat))
        fout.write('\n')
        fout.writelines("Through heigth of the bedform over the mean heigth of the reach [mm or m]="+str(etab))
        fout.write('\n')
        fout.writelines("Prediction of vertical sorting of sediment over the bed surface for chosen grainsizes (phi_1,phi_2="+str(fiuno)+","+str(fidue)+"):")
        fout.write('\n')
        fout.writelines("(depth [m or mm], F1 [%], F2 [%])")
        fout.write('\n')
        f11=i.split('|')[4:][::2]
        f22=i.split('|')[5:][::2]
        m=0
        for i in neg:
            fout.writelines("("+str(i)+", "+str(float(f11[m]))+", "+str(float(f22[m]))+")")
            fout.write('\n')
            m=m+1
    fout.close()


#inizia qui lo script: 

def main():
    m=flags["m"];
    dem=options["dem"]
    input_csv=options["input_csv"]
    type=options["type"]
    outputDEM=options["outputDEM"]
    vector=options["vector"]
    dmax=options["dmax"]
    nstep=options["nstep"]
    res=options["res"]
    lee_out=options["lee_out"]
    point_out=options["point_out"]
    fiuno=options["fiuno"]
    fidue=options["fidue"]
    ros=options["ros"]
    to=options["to"]
    fauno=options["fauno"]
    fadue=options["fadue"]
    n_iter=options["n_iter"]
    txtout=options["txtout"]
    graphout=options["graphout"]
    grass.run_command('g.gisenv',set='OVERWRITE=1')

    if input_csv:
        import_csv(res,input_csv,type,outputDEM)
        dem=outputDEM

    grass.run_command('g.remove',rast='slope',vect='lee_dradd,take_this1,take_this2,one_lee,one_add,preso_ok,preso_punto,presoo,punti_lee,punti_stoss,stoss_dradd,tratti_lee,tratti_leep,tratti_stoss,tratti_stossp,vector_drape,vector_pezzi,vector_pezzi_add,vector_punti,vector_punti_add,vector_punti_del,vector_lee')
    grass.run_command('g.region',vect=vector,n='n+50',e='e+50',s='s-50',w='w-50')

    general=general_geom(vector,dem,res)
    x,z,xline,zline,length,deltatot,rad=general[0],general[1],general[2],general[3],general[4],general[5],general[6]

    lines=lines_sl(vector,res,dem,'stoss_dradd','lee_dradd')
    lastcat_endZ,firstcat_endZ=lines[0],lines[1]

    lee_lambda=populate_lines('lee_dradd','vector_pezzi_add',firstcat_endZ,lastcat_endZ,rad,deltatot,length,'stoss_dradd',lee_out,dem,point_out)

    point=point_selection('lee_dradd',m,nstep,point_out,dem)
    id_section,east_section,north_section,z_avg,z_pt=point[0],point[1],point[2],point[3],point[4]

    graph=graphics(lee_lambda,x,z,xline,zline)
    k,l,delta_list,etab_list=graph[0],graph[1],graph[2],graph[3]

    resultNum=numeric(id_section,east_section,north_section,dmax,nstep,z_pt,z_avg,lee_lambda,delta_list,etab_list,rad,fiuno,fidue,fauno,fadue,to,ros,k,l,n_iter,point_out)
    fivalues,dval=resultNum[0],resultNum[1]

    results(fiuno,fidue,fauno,fadue,fivalues,dval,lee_lambda,txtout,graphout)

    grass.run_command('g.remove',vect='lee_dradd,take_this1,take_this2,one_lee,one_add,preso_ok,preso_punto,presoo,point_del,stoss_dradd,tratti_lee_del,tratti_leep,tratti_stoss_del,tratti_stossp,vector_drape,vector_add,vector_del,vector_drape_pezzi,vector_lee,vector_pezzi,vector_pezzi_add,vector_pezzi_del,vector_stoss')


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
