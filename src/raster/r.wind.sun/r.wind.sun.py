#!/usr/bin/env python
#
############################################################################
#
# MODULE:	r.wind.sun
# AUTHOR(S):	Annalisa Minelli & Ivan Marchesini
# PURPOSE:	Calculates visual impact of aerogenerators and photovoltaic panels
# COPYRIGHT:	(C) 2012 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################
#%Module
#%  description: Calculates visual impact of aerogenerators and photovoltaic panels
#%  keywords: visibility, photovoltaic, wind
#%End 
#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% description: Dem of the zone
#% required: yes
#%end
#%option
#% key: impact
#% type: string
#% gisprompt: new,cell,raster
#% description: Impact output map
#% required: yes
#%end
#%flag
#%  key: w
#%  description: Perform aerogenerators' analysis of visibility
#%end
#%flag
#%  key: f
#%  description: Perform photovoltaic analysis of visibility
#%end
#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% description: Vector file of points where to place aerogenerators
#% required : no
#% guisection: Wind
#%end
#%option
#% key: machine
#% type: string
#% gisprompt: old_file,file,input
#% key_desc: name
#% description: Ascii file of the aerogenerator model to simulate
#% required: no
#% guisection: Wind
#%end
#%option
#% key: high
#% type: double
#% description: Aerogenerator's height [m]
#% required: no
#% guisection: Wind
#%end
#%option
#% key: wind
#% type: integer
#% description: Wind direction in degree starting from North 
#% required: no
#% guisection: Wind
#%end
#%option
#% key: f
#% type: double
#% description: Maximum distance for computing visual impact [m]
#% required: no
#% guisection: Wind
#%end
#%option
#% key: windfarm2
#% type: string
#% gisprompt: new,vector,vector
#% description: Output vector map 2D of aerogenerators
#% required: no
#% guisection: Wind
#%end
#%option
#% key: windfarm3
#% type: string
#% gisprompt: new,vector,vector
#% description: Output vector map 3D of aerogenerators
#% required: no
#% guisection: Wind
#%end
#%option
#% key: panels
#% type: string
#% gisprompt: old,vector,vector
#% description: Vector map of panels
#% required : no
#% guisection: Photovoltaic
#%end
#%option
#% key: panels_height
#% type: double
#% description: Height (standard) of the panels [m]
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: panels_width
#% type: double
#% description: Width (standard) of the panels [m]
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: angle
#% type: double
#% description: Vertical inclination angle of the panel in degrees (above terrain surface, starting from horizontal)
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: orient
#% type: double
#% description: Orientation angle of the panel in degrees (starting from north, clockwise)
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: panels_center_height
#% type: double
#% description: Height of the panels' center on the terrain [m]
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: resolution
#% type: double
#% description: Choose a resolution to work [m]
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: min_dist_from_panel
#% type: double
#% description: Minimum distance for computing visual impact [m]
#% required: no
#% guisection: Photovoltaic
#%end
#%option
#% key: max_dist_from_panel
#% type: double
#% description: Maximum distance for computing visual impact [m]
#% required: no
#% guisection: Photovoltaic
#%end

import sys,os,re,numpy,math
import grass.script as grass

def main():
    dem=options["dem"];
    impact=options["impact"];
    input=options["input"];
    machine=options["machine"];
    high=options["high"];
    wind=options["wind"];
    f=options["f"];
    windfarm2=options["windfarm2"];
    windfarm3=options["windfarm3"];
    panels=options["panels"];
    panels_height=options["panels_height"];
    panels_width=options["panels_width"];
    angle=options["angle"];
    orient=options["orient"];
    panels_center_height=options["panels_center_height"];
    resolution=options["resolution"];
    min_dist_from_panel=options["min_dist_from_panel"];
    max_dist_from_panel=options["max_dist_from_panel"];
    fotov=flags["f"];
    eolic=flags["w"];
    grass.run_command('g.gisenv',set='OVERWRITE=1');
    if eolic:
        res_dem=float(re.split('=',re.split('\n',grass.read_command('r.info',flags='s',map=dem))[0])[1]);
        grass.write_command('r.mapcalc', stdin = '%s = float(%s)' % ('fdem',dem)); 
        grass.run_command('v.in.ascii', flags='z', input=machine,output='line',format='standard',fs='|',skip='0',x='1',y='2',z='0',cat='0');
        grass.run_command('g.copy',vect='line,face');
        a=grass.read_command('v.info',flags='g',map='line');
        t=float((re.split('=',re.split('\n',a)[4]))[1]);
        b=float((re.split('=',re.split('\n',a)[5]))[1]);
        e=float((re.split('=',re.split('\n',a)[2]))[1]);
        w=float((re.split('=',re.split('\n',a)[3]))[1]);
        att=(t - b ) - ( e - w )*0.577350269;
        pala_att=(e - w)/1.5;
        scal=float(high)/att;
        wind=int(wind);
        orien=180 - wind;
        grass.run_command('g.remove',vect='line_model,face_model,pointD');
        grass.run_command('v.transform',input='line',output='line_model',xshift='0.0',yshift='0.0',zshift='0.0',xscale=scal,yscale=scal,zscale=scal,zrot=orien,layer='1');
        grass.run_command('v.transform',input='face',output='face_model',xshift='0.0',yshift='0.0',zshift='0.0',xscale=scal,yscale=scal,zscale=scal,zrot=orien,layer='1');
        fdiam=( e - w ) * scal * 5;
        grass.run_command('g.region',vect='face_model');
        center=grass.read_command('g.region', flags='cg', vect='face_model');
        east=float(re.split('=',(re.split('\n',center)[0]))[1]);
        north=float(re.split('=',(re.split('\n',center)[1]))[1]);
        try:
            os.remove('txt');
        except OSError:
            print "the txt file does not exist yet but soon.. it will be created.";
        print "to be continued..";
        str1=[str(east-1000),' ',str(north+1000),' '];
        str3=[str(east+1000),' ',str(north+1000),' '];
        str5=[str(east+1000),' ',str(north-1000),' '];
        str7=[str(east-1000),' ',str(north-1000),' '];
        info=grass.read_command('v.info', flags='g', map='face_model');
        add=abs(float(re.split('=',re.split('\n',info)[5])[1]));
        grass.run_command('g.region',rast='fdem',res=res_dem);
        grass.run_command('v.drape',input=input,type='point',rast='fdem',scale='1.0',method='nearest',output='pointD');
        a=grass.read_command('v.to.db',flags='pc', map='pointD', type='point', layer='1', qlayer='1', option='coor', units='meters', columns='est,nord,z');
        b=re.split('\n',a)[1:-1];	
        n=int(re.split('\|',b[-1])[0]);
        bibidi='';
        bobidi='';
        stringa_linee='';
        stringa_facce='';
        for i in b:
            grass.run_command('g.region',vect=input);
            est=float(re.split('\|',i)[1]);
            nord=float(re.split('\|',i)[2]);
            more=float(re.split('\|',i)[3]);
            addmore=add+more;
            str2=[str(est-1000),' ',str(nord+1000)];
            str4=[str(est+1000),' ',str(nord+1000)];
            str6=[str(est+1000),' ',str(nord-1000)];
            str8=[str(est-1000),' ',str(nord-1000)];
            txt=open('txt','w');
            txt.writelines(str1+str2);
            txt.write('\n');
            txt.writelines(str3+str4);
            txt.write('\n');
            txt.writelines(str5+str6);
            txt.write('\n');
            txt.writelines(str7+str8);
            k=str(re.split('\|',i)[0]);
            palo_facce='palo_facce_'+k;
            palo_linee='palo_linee_'+k;
            txt='txt'
            grass.run_command('v.transform',flags='m',input='line_model',output=palo_linee,pointsfile=txt,xshift='0.0',yshift='0.0',zshift=addmore,xscale='1.0',yscale='1.0',zscale='1.0',zrot='0.0',layer='1');			
            grass.run_command('v.transform',flags='m',input='face_model',output=palo_facce,pointsfile=txt,xshift='0.0',yshift='0.0',zshift=addmore,xscale='1.0',yscale='1.0',zscale='1.0',zrot='0.0',layer='1');
            if k == n :
                stringa_linee=stringa_linee+palo_linee;
                stringa_facce=stringa_facce+palo_facce;
            else:
                stringa_linee=stringa_linee+palo_linee+',';
                stringa_facce=stringa_facce+palo_facce+',';
            grass.run_command('v.patch',input=stringa_linee,output=windfarm2);
            grass.run_command('v.patch',input=stringa_facce,output=windfarm3);
        grass.run_command('g.region',vect=windfarm3,n='n'+'+'+str(f),s='s'+'-'+str(f),e='e'+'+'+str(f),w='w'+'-'+str(f));
        tdiam=( e - w ) * scal * 3;
        sdiam=( e - w ) * scal * 7;
        grass.run_command('v.buffer',input=input,output='buf3',type='point,line,area',layer='1',distance=tdiam,scale='1.0',tolerance='0.01');
        grass.run_command('v.buffer',input=input,output='buf5',type='point,line,area',layer='1',distance=fdiam,scale='1.0',tolerance='0.01');
        grass.run_command('v.buffer',input=input,output='buf7',type='point,line,area',layer='1',distance=sdiam,scale='1.0',tolerance='0.01');
        grass.run_command('v.patch',input='buf7,buf5,buf3',output='areas');
        grass.run_command('nviz',elevation='fdem',vector=windfarm3);
        pala_scal= pala_att * scal;
        h=1;
        for i in b:
            grass.run_command('g.region',flags='a',vect=input,res=res_dem,n='n'+'+'+str(f),s='s'+'-'+str(f),e='e'+'+'+str(f),w='w'+'-'+str(f));
            ca=int(re.split('\|',i)[0]);
            xcoor=float(re.split('\|',i)[1]);
            ycoor=float(re.split('\|',i)[2]);
            more=float(re.split('\|',i)[3]);
            grass.write_command('r.mapcalc', stdin = '%s = x() - %s' % ('px',xcoor));
            grass.write_command('r.mapcalc', stdin = '%s = y() - %s' % ('py',ycoor));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((%s)^2) + ((%s)^2))' % ('dist_or','px','py'));
            m_u= float(high) + pala_scal;
            m_l= float(high);
            m_h= (m_u * 0.5) + (m_l * 0.5);
            moree= more + m_h;
            coordinate=str(xcoor)+','+str(ycoor);
            grass.run_command('r.viewshed',input=dem,output='step_up',coordinate=coordinate,obs_elev=m_u,max_dist=f);
            grass.run_command('r.viewshed',input=dem,output='step_low',coordinate=coordinate,obs_elev=m_l,max_dist=f);
            grass.run_command('r.viewshed',input=dem,output='step_half',coordinate=coordinate,obs_elev=m_h,max_dist=f);
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((abs(%s+%s-%s))^2)+((%s)^2))' % ('dist_up',more,m_u,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((abs(%s+%s-%s))^2)+((%s)^2))' % ('dist_low',more,m_l,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((abs(%s-%s))^2)+((%s)^2))' % ('dist_half',moree,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = %s-%s' % ('gamma_up','step_half','step_up'));
            grass.write_command('r.mapcalc', stdin = '%s = %s-%s' % ('gamma_low','step_low','step_half'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*tan(%s),%s*tan(%s))' % ('half_len',dem,moree,'dist_half','gamma_low','dist_half','gamma_up'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, abs(%s+%s-%s), abs(%s+%s-%s))' % ('disl',dem,moree,more,m_l,dem,more,m_u,dem));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((%s)^2)+((%s)^2))*(%s/%s)' % ('c_1','disl','dist_or','gamma_low','gamma_low'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*cos(%s), %s*cos(%s))' % ('h_1',dem,moree,'c_1','gamma_low','c_1','gamma_up'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s, %s/cos(%s))' % ('r',dem,moree,'c_1','h_1','gamma_low'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s, %s*%s/%s)' % ('pala',dem,moree,pala_scal,pala_scal,'r','dist_low'));
            grass.write_command('r.mapcalc', stdin = '%s = %s*%s/%s' % ('base_1','half_len','h_1','dist_half'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*tan(%s), %s*tan(%s))' % ('base_2',dem,moree,'h_1','gamma_up','h_1','gamma_low'));
            grass.write_command('r.mapcalc', stdin = '%s = %s+%s' % ('len','base_1','base_2'));
            grass.write_command('r.mapcalc', stdin = '%s = %s*%s*%s/2' % (str(h)+'area_semi',math.pi,'len','pala'));
            m_l= float(high) - pala_scal;
            m_h= float(high);
            moree= more + m_h;
            grass.run_command('r.viewshed',input=dem,output='step_up',coordinate=coordinate,obs_elev=m_u,max_dist=f);
            grass.run_command('r.viewshed',input=dem,output='step_low',coordinate=coordinate,obs_elev=m_l,max_dist=f);
            grass.run_command('r.viewshed',input=dem,output='step_half',coordinate=coordinate,obs_elev=m_h,max_dist=f);			
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((abs(%s+%s-%s))^2)+((%s)^2))' % ('dist_up',more,m_u,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((abs(%s+%s-%s))^2)+((%s)^2))' % ('dist_low',more,m_l,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((abs(%s-%s))^2)+((%s)^2))' % ('dist_half',moree,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = %s-%s' % ('gamma_up1','step_half','step_up'));
            grass.write_command('r.mapcalc', stdin = '%s = %s-%s' % ('gamma_low','step_low','step_half'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*tan(%s),%s*tan(%s))' % ('half_len',dem,moree,'dist_half','gamma_low','dist_half','gamma_up1'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, abs(%s+%s-%s), abs(%s+%s-%s))' % ('disl',dem,moree,more,m_l,dem,more,m_u,dem));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt(((%s)^2)+((%s)^2))*(%s/%s)' % ('c_2','disl','dist_or','gamma_low','gamma_low'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*cos(%s), %s*cos(%s))' % ('h_2',dem,moree,'c_2','gamma_low','c_2','gamma_up1'));
            grass.write_command('r.mapcalc', stdin = '%s = %s*%s/%s' % ('pala',pala_scal,'h_2','dist_half'));
            grass.write_command('r.mapcalc', stdin = '%s = %s*%s/%s' % ('base_1','half_len','h_2','dist_half'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*tan(%s), %s*tan(%s))' % ('base_2',dem,moree,'h_2','gamma_up1','h_2','gamma_low'));
            grass.write_command('r.mapcalc', stdin = '%s = %s+%s' % ('len','base_1','base_2'));
            grass.write_command('r.mapcalc', stdin = '%s = 0.5*%s*%s*%s' % (str(h)+'area_elli',math.pi,'len','pala'));
            m_l=0.0;
            m_h= m_u - pala_scal * 2;
            moree= more + m_h;
            grass.run_command('r.viewshed',input=dem,output='step_up',coordinate=coordinate,obs_elev=m_u,max_dist=f);
            grass.run_command('r.viewshed',input=dem,output='step_low',coordinate=coordinate,obs_elev=m_l,max_dist=f);
            grass.run_command('r.viewshed',input=dem,output='step_half',coordinate=coordinate,obs_elev=m_h,max_dist=f);
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s+%s-%s)^2+(%s)^2)' % ('dist_up',more,m_u,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s+%s-%s)^2+(%s)^2)' % ('dist_low',more,m_l,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s-%s)^2+(%s)^2)' % ('dist_half',moree,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = %s-%s' % ('gamma_up2','step_half','step_up'));
            grass.write_command('r.mapcalc', stdin = '%s = %s-%s' % ('gamma_low2','step_low','step_half'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*tan(%s),%s*tan(%s))' % ('half_len',dem,moree,'dist_half','gamma_low2','dist_half','gamma_up2'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, abs(%s+%s-%s), abs(%s+%s-%s))' % ('disl',dem,moree,more,m_l,dem,more,m_u,dem));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s)^2+(%s)^2)*(%s/%s)' % ('c_3','disl','dist_or','gamma_low','gamma_low'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*cos(%s), %s*cos(%s))' % ('h',dem,moree,'c_3','gamma_low2','c_3','gamma_up2'));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s+%s-%s)^2+(%s)^2)' % ('dist_centro_ellisse',moree,pala_scal,dem,'dist_or'));
            grass.write_command('r.mapcalc', stdin = '%s = %s*%s/%s' % ('base_1','half_len','h','dist_half'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*tan(%s), %s*tan(%s))' % ('base_2',dem,moree,'h','gamma_up2','h','gamma_low2'));
            grass.write_command('r.mapcalc', stdin = '%s = (%s/%s)*if(%s <= %s, 0.5*%s, 0.5*%s)' % ('h_3','dist_centro_ellisse',pala_scal,dem,moree,'base_2','base_1'));
            grass.write_command('r.mapcalc', stdin = '%s = %s*%s/%s' % ('pala',pala_scal,'h_3','dist_centro_ellisse'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s <= %s, %s*0.5, %s*0.5)' % ('semiasse_ell',dem,moree,'base_2','base_1'));
            grass.write_command('r.mapcalc', stdin = '%s = (%s*%s*%s)+((%s*(3+%s/%s))*%s*0.5)' % (str(h)+'area_composta',math.pi,'semiasse_ell','pala',scal,m_h,high,m_h));
            patch_aree=str(h)+'area_composta'+','+str(h)+'area_elli'+','+str(h)+'area_semi';
            grass.run_command('r.patch',flags='z',input=patch_aree,output=str(h)+'tot_area');
            grass.run_command('r.null',map=str(h)+'tot_area',null='0');
            grass.run_command('r.patch',input='c_3,c_2,c_1',output=str(h)+'tot_distance');
            grass.run_command('r.null',map=str(h)+'tot_distance',null='3000000');
            if h == n :
                bibidi=bibidi+str(h)+'tot_distance';
                bobidi=bobidi+str(h)+'tot_area';
            else:
                bibidi=bibidi+str(h)+'tot_distance'+',';
                bobidi=bobidi+str(h)+'tot_area'+',';
            h= h + 1;
        grass.write_command('r.mapcalc', stdin = '%s = min(%s)' % ('dist_min',bibidi));
        grass.run_command('r.null',map='dist_min',setnull='3000000');
        grass.write_command('r.mapcalc', stdin = '%s = 4*%s*%s^2' % ('fov',math.pi,'dist_min'));
        grass.write_command('r.mapcalc', stdin = '%s = 0' % ('area'));
        grass.write_command('r.mapcalc', stdin = '%s = 0' % ('what_map'));
        grass.write_command('r.mapcalc', stdin = '%s = 0' % ('area_others'));
        bu=[];
        for i in b:
            z= 0;
            t= 1;
            cat=int(re.split('\|',i)[0]);
            grass.write_command('r.mapcalc', stdin = '%s = if(min(%s) == %s, %s,%s)' % ('what_map',bibidi,str(cat)+'tot_distance',cat,'what_map'));
            for z in re.split(',',bibidi):
                grass.run_command('r.null',map=z,setnull='3000000');
                grass.run_command('r.null',map=z,null='0');
                bu.append(z);
            z= 0;
            c=bu[:];
            print "c vale: ",c
            print "cat ed n valgono rispett: ",cat,n
            for z in c:
                del c[cat-1];
                del c[n-1:];
                grass.write_command('r.mapcalc', stdin = '%s = %s+(%s*%s/%s)' % ('area_others','area_others',z,str(cat)+'tot_area',str(cat)+'tot_distance'));
                c=bu[:];
                print "c vale: ",c
            grass.write_command('r.mapcalc', stdin = '%s = if(%s = %s,%s+%s,%s+%s)' % ('area','what_map',cat,'area',str(cat)+'tot_area','area','area_others'));
        grass.write_command('r.mapcalc', stdin = '%s = %s/%s' % ('pre','area','fov'));
        grass.run_command('v.to.rast',input=input,output='out',use='cat',type='point',layer='1',value='1',rows='4096');
        grass.write_command('r.mapcalc', stdin = '%s = abs(if(isnull(%s),if(%s < 1,%s*100,100),0))' % (impact,'out','pre','pre'));
        grass.run_command('r.null',map=impact,setnull='0');
        grass.run_command('g.remove',flags='f',rast='out,pre,area,area_others,base_1,base_2,c_1,c_2,c_3,disl,dist_centro_ellisse,dist_half,dist_low,dist_or,dist_min,dist_up,fdem,fov,gamma_low,gamma_low2,gamma_up,gamma_up1,gamma_up2,h,h_1,h_2,h_3,half_len,len,pala,px,py,r,semiasse_ell,step_half,step_low,step_up,what_map',vect='areas,buf3,buf5,buf7,face,face_model,line,line_model,pointD');
        for i in b:
            num=str(re.split('\|',i)[0]);
            r2remove=num+'area_composta'+','+num+'area_elli'+','+num+'area_semi'+','+num+'tot_area'+','+num+'tot_distance';
            v2remove='palo_linee_'+num+','+'palo_facce_'+num;
            grass.run_command('g.remove',flags='f',rast=r2remove,vect=v2remove);
    elif fotov:
        grass.write_command('r.mapcalc', stdin = '%s = 0' % ('n_pann_visib'));
        grass.write_command('r.mapcalc', stdin = '%s = 0.0' % ('dist_or'));
        grass.write_command('r.mapcalc', stdin = '%s = 0.0' % (impact));
        n=0;
        grass.run_command('g.region',res=resolution);
        grass.run_command('v.drape',input=panels,type='point,centroid,line,boundary,face,kernel',rast=dem,output='panels3D',method='nearest',scale='1.0',layer='1');
        d=grass.read_command('v.to.db',flags='p', map='panels3D', type='point,centroid', layer='1', qlayer='1', option='coor', columns='x,y');
        e=re.split('\n',d)[1:-1];
        for i in e:
            n= n + 1;
            print n;
            x=float(re.split('\|',i)[1]);
            y=float(re.split('\|',i)[2]);
            z=float(re.split('\|',i)[3]);
            cat=int(re.split('\|',i)[0]);
            obs_elev= 1.70 + float(panels_center_height);
            grass.run_command('g.remove',rast='los_degree_'+str(cat));
            coordinate=str(x)+','+str(y);
            grass.run_command('r.viewshed',input=dem,output='los_degree_'+str(cat),coordinate=coordinate,obs_elev=obs_elev,max_dist=max_dist_from_panel);
            grass.write_command('r.mapcalc', stdin = '%s = %s/%s' % ('los_boolean','los_degree_'+str(cat),'los_degree_'+str(cat)));
            grass.run_command('r.null',map='los_boolean',null='0');
            grass.write_command('r.mapcalc', stdin = '%s = %s+%s' % ('n_pann_visib','n_pann_visib','los_boolean'));
            grass.write_command('r.mapcalc', stdin = '%s = if( %s == 0 ,null(),1)' % ('MASK','los_boolean'));
            grass.write_command('r.mapcalc', stdin = '%s = x()-%s' % ('px',x));
            grass.write_command('r.mapcalc', stdin = '%s = y()-%s' % ('py',y));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s)^2+(%s)^2)' % ('dist_or_'+str(cat),'px','py'));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s < %s,%s,%s)' % ('dist_or_'+str(cat),'dist_or_'+str(cat),min_dist_from_panel,min_dist_from_panel,'dist_or_'+str(cat)));
            grass.write_command('r.mapcalc', stdin = '%s = (if(%s >= 0 & %s >= 0,90-atan(%s/%s),if(%s >= 0 & %s < 0,90-atan(%s/%s),if(%s < 0 & %s < 0,270-atan(%s/%s),if(%s < 0 & %s >= 0,270-atan(%s/%s)))))) - %s' % ('azimuth_'+str(cat),'px','py','py','px','px','py','py','px','px','py','py','px','px','py','py','px',orient));
            grass.write_command('r.mapcalc', stdin = '%s = abs(2*(%s*0.5)*cos(%s)*(%s/(%s+(%s*0.5)*sin(%s))))' % ('apparent_width_'+str(cat),panels_width,'azimuth_'+str(cat),'dist_or_'+str(cat),'dist_or_'+str(cat),panels_width,'azimuth_'+str(cat)));
            grass.write_command('r.mapcalc', stdin = '%s = (%s+%s)-%s' % ('dist_ver_'+str(cat),z,panels_center_height,dem));
            grass.write_command('r.mapcalc', stdin = '%s = sqrt((%s)^2+(%s)^2)' % ('dist_'+str(cat),'dist_or_'+str(cat),'dist_ver_'+str(cat)));
            grass.write_command('r.mapcalc', stdin = '%s = if(%s < (90+%s),%s-90+%s,if(%s = (90+%s),90,%s-90-%s))' % ('angle','los_degree_'+str(cat),angle,'los_degree_'+str(cat),angle,'los_degree_'+str(cat),angle,'los_degree_'+str(cat),angle));
            grass.write_command('r.mapcalc', stdin = '%s = 2*((%s*0.5)*sin(abs(%s)))*(%s/(%s+((%s*0.5)*cos(%s))))' % ('apparent_height_'+str(cat),panels_height,'angle','dist_'+str(cat),'dist_'+str(cat),panels_height,'angle'));
            grass.write_command('r.mapcalc', stdin = '%s = 2*%s*%s' % ('circle',math.pi,'dist_or_'+str(cat)));
            grass.write_command('r.mapcalc', stdin = '%s = %s*(tan(75))' % ('b','dist_or_'+str(cat)));
            grass.write_command('r.mapcalc', stdin = '%s = %s*(tan(60))' % ('d','dist_or_'+str(cat)));
            grass.write_command('r.mapcalc', stdin = '%s = (%s+%s)*%s' % ('fov_'+str(cat),'b','d','circle'));
            grass.write_command('r.mapcalc', stdin = '%s = (%s*%s/%s)*100' % ('imp_'+str(cat),'apparent_height_'+str(cat),'apparent_width_'+str(cat),'fov_'+str(cat)));
            grass.run_command('g.remove',rast='MASK');
            grass.run_command('r.null',map='imp_'+str(cat),null='0');
            grass.write_command('r.mapcalc', stdin = '%s = %s+%s' % (impact,impact,'imp_'+str(cat)));
            grass.run_command('r.colors',flags='e',map=impact,color='rainbow');
            grass.run_command('r.univar',map=impact);
            r2remove='apparent_height_'+str(cat)+','+'apparent_width_'+str(cat)+','+'azimuth_'+str(cat)+','+'dist_'+str(cat)+','+'dist_or_'+str(cat)+','+'dist_ver_'+str(cat)+','+'fov_'+str(cat)+','+'imp_'+str(cat)+','+'los_degree_'+str(cat);
            grass.run_command('g.remove',flags='f',rast=r2remove);
        grass.run_command('r.null',map=impact,setnull='0');
        grass.run_command('g.remove',rast='angle,b,circle,d,dist_or,los_boolean,n_pann_visib,px,py',vect='panels3D');
    else:
        print "You must choose to perform one of the two possible analysis, pick the flag!"	


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
