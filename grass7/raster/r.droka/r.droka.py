#!/usr/bin/env python
#
############################################################################
#
# MODULE:	r.droka
# AUTHOR(S):	original idea by: HUNGR (1993)
#		implementation by: 
#               Andrea Filipello -filipello@provincia.verbania.it
#               Daniele Strigaro - daniele.strigaro@gmail.com
# PURPOSE:	Calculates run-out distance of a falling rock mass
# COPYRIGHT:	(C) 2009 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################
#%Module
#%  description: Calculates run-out distance of a falling rock mass
#%  keywords: rock mass, rockfall
#%End
#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% description: Digital Elevation Model
#% required: yes
#%end
#%option
#% key: start
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of existing rock mass start point 
#% required : yes
#%end
#%option
#% key: x
#% type: double
#% description: Est coordinate of source point
#% required: yes
#%end
#%option
#% key: y
#% type: double
#% description: North coordinate of source point
#% required: yes
#%end
#%option
#% key: z
#% type: double
#% description: Elevation of source point
#% required: yes
#%end
#%option
#% key: red
#% type: double
#% description: Reduction parameter
#% options : 0-1
#% required: yes
#%end
#%option
#% key: m
#% type: double
#% description: Rock block mass (Kg/m^3)
#% required: yes
#%end
#%option
#% key: vel
#% type: string
#% gisprompt: new,cell,raster
#% description: Translational velocity (corrected)
#% required : yes
#%end
#%option
#% key: en
#% type: string
#% gisprompt: new,cell,raster
#% description: Kinematic energy (kJ) (corrected)
#% required: yes
#%end

import os, sys, time, math, numpy , string, re

try:
    import grass.script as grass
except:
    try:
        from grass.script import core as grass
	#from grass.script import core as gcore
    except:
        sys.exit("grass.script can't be imported.")

if not os.environ.has_key("GISBASE"):
    print "You must be in GRASS GIS to run this program."
    sys.exit(1)

def main():
    
    # leggo variabili
    r_elevation = options['dem'].split('@')[0]
    mapname = options['dem'].replace("@", " ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".", "_")
    start = options['start']
    start_ = start.split('@')[0]
    gfile = grass.find_file(start, element = 'vector')
    if not gfile['name']:
        grass.fatal(_("Vector map <%s> not found") % infile)

    x = options['x']
    y = options['y']
    z = options['z']
    ang = 30
    red = options['red']
    m = options['m']
    vel = str(options['vel'])
    en = str(options['en'])

    print 'x = ' , x
    print 'y = ' , y
    print 'z = ' , z
#    print 'ang = ' , ang
    print 'red = ' , red
    print 'm = ' , m
    print 'vel = ' , vel
    print 'en = ' , en
    

    point = grass.read_command("v.out.ascii", input=start, format="standard")
    result = point.split("\n") 
    coords = []    
    for line in result:
        if re.findall(r'^.[0-9]+\.',line): 
            coords.append(line.strip().split("   "))
    print coords

    #creo raster (che sara' il DEM di input) con valore 1
    grass.mapcalc('uno=$dem*0+1', 
        dem = r_elevation)

    # Calcolo cost (sostituire i punti di partenza in start_raster al pusto di punto)
    grass.run_command('r.cost' , 
        flags="k",
        input = 'uno',
        output = 'costo',
        start_points = start )
    #trasforma i valori di distanza celle in valori metrici utilizzando la risoluzione raster
    grass.mapcalc('costo_m=costo*(ewres()+nsres())/2')
    # calcola A=tangente angolo visuale (INPUT) * costo in metri
    grass.mapcalc('A=tan($ang)*costo_m',
        ang = ang)
    grass.mapcalc('C=$z-A',
        z = z)
    grass.mapcalc('D=C-$dem',
        dem = r_elevation)
    # area di espansione
    grass.mapcalc('E=if(D>0,1,null())')
    # valore di deltaH (F)
    grass.mapcalc('F=D*E')
    # calcolo velocita
    grass.mapcalc('$vel=$red*sqrt(2*9.8*F)',
        vel = vel,
        red = red)
    # calcolo energia
    grass.mapcalc('$en=$m*9.8*F/1000',
        en = en,
        m = m)

    for i in xrange(len(coords)):
        row = coords[i]

#r.what map=DTM10_f211@modulo_issa points=point@modulo_issa

    grass.run_command('g.remove' , 
        rast=(
            'uno',
            'costo',
            'costo_m',
            'A',
            'C',
            'D',
            'E',
            'F'))

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
