#!/usr/bin/env python
#
##############################################################################
#
# MODULE:      r.rock.stability
# VERSION:     1.0
# AUTHOR(S):   Andrea Filipello & Daniele Strigaro
# PURPOSE:     Calculates SMR for a dtm 
# COPYRIGHT:   (C) 2014 by Andrea Filipello & Daniele Strigaro
#              andrea.filipello@gmail.com; daniele.strigaro@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
##############################################################################
#%Module
#%  description: Calculates SMR index for a slope area.
#%  keywords: rock mass, planar failure, toppling
#%End
#%option
#% key: dem
#% type: string
#% gisprompt: old,cell,raster
#% description: Dtm of the zone
#% required: yes
#%end
#%option
#% key: imme
#% type: integer
#% description: Dip direction of the joint (0-360)
#% options: 0-360
#% required: yes
#%end
#%option
#% key: incl
#% type: integer
#% description: Dip of the joint (0-90)
#% options: 0-90
#% required: yes
#%end
#%option
#% key: f4
#% type: string
#% description: F4 index 
#% options: Natural Slope +15,Pre-splitting +10,Smooth blasting +8,Normal blasting or mechanical excavation 0,Poor blasting -8
#% required: yes
#%end
#%option
#% key: rmr
#% type: string
#% gisprompt: old,raster,raster
#% description: RMR index 
#% required: yes
#%end
################ouput######################
#%option
#% key: prefix
#% type: string
#% description: Prefix for output maps
#% required: yes
#%end
#%option
#% key: tc
#% type: string
#% gisprompt: old,raster,raster
#% description: Total Condition of joint, for SSPC output
#% required: no
#% guisection: SSPC
#%end
#%option
#% key: imme2
#% type: integer
#% description: Dip direction of the joint (0-360). For SMR_wedge output
#% options: 0-360
#% required: no
#% guisection: SMR_wedge
#%end
#%option
#% key: incl2
#% type: integer
#% description: Dip of the joint (0-90). For SMR_wedge output
#% options: 0-90
#% required: no
#% guisection: SMR_wedge
#%end

import os, sys

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
############################################### leggo variabili###################################
    r_elevation = options['dem'].split('@')[0]
    imme = options['imme']
    incl = options['incl']
    f4 = options['f4']
    if (f4 == 'Natural Slope +15'):
        f4 = 15
    elif (f4 == 'Pre-splitting +10'):
        f4 = 10
    elif (f4 == 'Smooth blasting +8'):
        f4 = 8
    elif (f4 == 'Normal blasting or mechanical excavation 0'):
        f4 = 0
    elif (f4 == 'Poor blasting -8'):
        f4 = -8
    RMR = options['rmr']
    prefix = options['prefix']
    #SMRrib = options['SMRtoppling']
    grass.message('Starting to calculate SMR index')    
    grass.message('Waiting...')    
#calcolo slope ed aspect

    grass.run_command('r.slope.aspect',
        elevation = r_elevation ,
        slope = 'slopes_' ,
        format = 'degrees' ,
        #precision = 'float' ,
        aspect = 'aspects_' ,
        zfactor = '1.0' ,
        min_slp_allowed = '0.0' ,
        quiet = True)

# Correggi aspect per avere: N=0 E=90 S=180 W=270

    grass.mapcalc("aspects_1 = if (aspects_ > 90, 450 - aspects_, 90 - aspects_)" ,
        quiet = True)

# calcolo A (valore assoluto)che vale SCIVOL=abs(immersdelgiunto-aspect1); RIBAL=abs(immersdelgiunto-aspect1-180)

    grass.mapcalc("Asci = abs($imme - aspects_1)",
        imme = imme ,
        quiet = True)
    grass.mapcalc("Arib = abs(Asci - 180)" ,
        quiet = True)

# calcolo F1 
# la formula originale e' stata in parte modificata per tener conto dei valori di A compresi tra 270 e 360 sfavorevoli x la stabilita'

    grass.mapcalc("F1sci1 = if(Asci > 270, 0.64 - 0.006*atan(0.1*(abs(Asci - 360) - 17)), 0)" ,
        quiet = True)
    grass.mapcalc("F1sci2 = if(Asci < 270, 0.64 - 0.006*atan(0.1*(Asci - 17)), 0)" ,
        quiet = True)
    grass.mapcalc("F1sci = F1sci1 + F1sci2" ,
        quiet = True)
    grass.mapcalc("F1rib1 = if(Arib > 270, 0.64 - 0.006*atan(0.1*(abs(Arib - 360) - 17)), 0)" ,
        quiet = True)
    grass.mapcalc("F1rib2 = if(Arib < 270, 0.64 - 0.006*atan(0.1*(Arib - 17)), 0)" ,
        quiet = True)
    grass.mapcalc("F1rib = F1rib1 + F1rib2" ,
        quiet = True)

# calcolo F2 (per il toppling vale sempre 1)

    grass.mapcalc("F2sci = 0.56 + 0.005*(atan(0.17*abs($incl) - 5))" ,
        incl = incl ,
        quiet = True)

# calcolo F3 

    grass.mapcalc("F3sci = -30 + 0.33*atan($incl - slopes_)" ,
        incl = incl ,
        quiet = True)
    grass.mapcalc("F3rib = -13 - 0.143*atan($incl + slopes_ - 120)" ,
        incl = incl ,
        quiet = True)

# moltiplica F1xF2XF3

    grass.mapcalc("Isciv = F1sci * F2sci * F3sci" ,
        quiet = True)
    grass.mapcalc("Irib = F1rib * F3rib * 1" ,
        quiet = True)

# Calcola l'indice SMR 

    grass.mapcalc("$SMRsciv = Isciv + $RMR + $F4" ,
        SMRsciv = prefix + '_SMRsciv' ,
        RMR = RMR ,
        F4 = f4 ,
        quiet = True)

    grass.mapcalc("$SMRrib = Irib + $RMR + $F4" ,
        SMRrib = prefix + '_SMRrib' ,
        RMR = RMR ,
        F4 = f4 ,
        quiet = True)
########################################################
############################SMR_wedge###################
########################################################
    imme2 = options['imme2']
    incl2 = options['incl2']
    grass.message('SMR index done!')
    if (imme2 != '' and incl2 != ''):
#calcola trend del cuneo
        grass.message('Parameter set for SMR_wedge')
        grass.message('Starting to calculate SMR_wedge index')
        grass.message('Waiting...')
        grass.mapcalc("T = (-tan($incl) * cos($imme)+tan($incl2)*cos($imme2))/(tan($incl)*sin($imme)-tan($incl2)*sin($imme2))",
            imme = imme ,
            imme2 = imme2 ,
            incl = incl ,
            incl2 = incl2 ,
            quiet = True)

        grass.mapcalc("T1 = atan(T)" ,
            quiet = True)
#calcola plunge del cuneo P2 (sarebbe inclinazione)
        grass.mapcalc("P=((sin($incl)*sin($imme)*sin($imme2-$imme))/(sin($incl)*cos($imme)*cos($incl2)-sin($incl2)*cos($imme2)*cos($incl)))*sin(T1)" ,
            imme = imme ,
            imme2 = imme2 ,
            incl = incl ,
            incl2 = incl2 ,
            quiet = True)
        grass.mapcalc("P1=atan(P)" ,
            quiet = True)
        grass.mapcalc("P2=abs(P1)" ,
            quiet = True)
#calcola trend del cuneo corretto (TB) sarebbe immersione
        grass.mapcalc("TA=if(P1<0,T1+180,T1)" ,
            quiet = True)
        grass.mapcalc("TB=if(TA<0,TA+360,TA)" ,
            quiet = True)
#calcola slope e aspect
#...calcolo A (valore assoluto)che vale SCIVOL=abs(immersdelgiunto-aspect1); RIBAL=abs(immersdelgiunto-aspect1-180) 
        grass.mapcalc("Asci=abs(TB-aspects_1)" ,
            overwrite = True ,
            quiet = True)
        reclass_rules = "-360 thru 5 = 1\n5.1 thru 10 = 0.085\n10.1 thru 20 = 0.7\n20.1 thru 30 = 0.4\n30.1 thru 320 = 0.15"
        grass.write_command('r.reclass' , 
            input='Asci' , 
            output='F1sci_',
            rules='-', 
            stdin=reclass_rules,
            quiet = True)
# creo una mappa con valore dell'inclinazione
        grass.mapcalc('mappa=P2+slopes_*0' ,
            quiet = True)
# calcolo di F2
        reclass_rules2 = "0 thru 20 = 0.15\n20.1 thru 30 = 0.4\n30.1 thru 35 = 0.7\n35.1 thru 45 = 0.85\n45.1 thru 90 = 1"
        grass.write_command('r.reclass', 
            input='mappa', 
            output='F2',
            rules='-', 
            stdin=reclass_rules2, 
            quiet = True )
# Calcolo di F3 
# Calcolo C che vale SCIVOL=inclgiunto - slopes;
        grass.mapcalc("Csci=P2-slopes_" ,
            quiet = True)
# Reclass per F3 scivolamento
        reclass_rules3 = "180 thru 9 = 0\n10 thru 0.1 = -6\n0 = -25\n-0.1 thru -9 = -50\n-10 thru -180 = -60"
        grass.write_command('r.reclass', 
            input='Csci' , 
            output='F3sci_' ,
            rules='-' , 
            stdin=reclass_rules3)
        grass.mapcalc('Isciv_=F1sci_*F3sci_*F2' ,
            quiet = True)
        grass.mapcalc("$SMRsciv=Isciv_+$RMR+$F4" ,
            SMRsciv = prefix + '_SMRscivWedge' ,
            RMR = RMR ,
            F4 = f4 ,
            quiet = True)
        grass.run_command('g.remove' , 
            flags='f',
            type='rast',
            name=(
                'Asci' ,
                'Arib' ,
                'F1sci_' ,
                'F3sci_' ,
                'F2' ,
                'Csci' ,
                'P' ,
                'P1' ,
                'P2' ,
                'T' ,
                'TA' ,
                'T1' ,
                'mappa' ,
                'Isciv_' ) ,
            quiet = True)
        grass.message('SMR_wedge index done!')
    else:
        grass.message('No parameter set for SMR_wedge')
        
#####################################################
############################SSPC#####################
#####################################################

    TC = options['tc']
    if (TC != ''):
# calcolo DELTA=aspect-immersione
        grass.mapcalc("delta = aspects_1 - $imme",
            imme = imme ,
            quiet = True)
# calcola A=cosenoDELTA
        grass.mapcalc("A = cos(delta)" , 
            quiet = True)
# calcola B=tan(inclinazione)
        grass.mapcalc("B = tan($incl)" ,
            incl = incl ,
            quiet = True)
# calcola C=A*B
        grass.mapcalc("C = A * B" , 
            quiet = True)
# calcola AP
        grass.mapcalc("AP = atan(C)" , 
            quiet = True)
# additional condition per scivolamento (dip del pendio deve essere < di AP+5), AP deve essere < di 85
        grass.mapcalc("AP1 = slopes_ - AP - 5" , 
            quiet = True)
        grass.mapcalc("consci1 = if(AP1 > 0, 0, null())" , 
            quiet = True)
        grass.mapcalc("consci2 = if(AP < 85, 0, null())" , 
            quiet = True)
# additional condition per ribaltamento (AP deve essere> di 85)
        grass.mapcalc("conrib = if(AP > (-85), 0, null())" , 
            quiet = True)
# ANALISI SCIVOLAMENTO PLANARE AP * 0.0113
        grass.mapcalc("membro_sci = 0.0113 * AP" , 
            quiet = True)
        grass.mapcalc("sci = membro_sci - $TC" ,
            TC = TC , 
            quiet = True)
# se il risultato ottenuto e' minore di zero non ho cinematismo, maggiore e' il valore piu' alta sara' la propensione al distacco
        grass.mapcalc("cinem_sci = if(sci >= 0, 1, null())" ,
            TC = TC , 
            quiet = True)
        grass.mapcalc("$SSPCsciv = cinem_sci * sci + consci1 + consci2" ,
            SSPCsciv = prefix + '_SSPCsciv' , 
            quiet = True)
# ANALISI RIBALTAMENTO 0.0087*(-90-AP+INCLINAZIONE)
        grass.mapcalc("membro_RIB = 0.0087 * ((-90) - AP + $incl)" ,
            incl = incl , 
            quiet = True)
        grass.mapcalc("rib = membro_RIB - $TC" ,
            TC = TC ,
            quiet = True)
# se il risultato ottenuto e' minore di zero non ho cinematismo, maggiore e' il valore piu' alta sara' la propensione al distacco
        grass.mapcalc("cinem_rib = if(rib >= 0, 1, null())" ,
            quiet = True)
        grass.mapcalc("$SSPCrib = cinem_rib * rib + conrib" ,
            SSPCrib = prefix + '_SSPCrib' ,
            quiet = True)
# processo per sostituire i valori di cella nulli con 0 (passaggio importante per trovare poi il minimo
        grass.run_command("r.null" ,
            map = prefix + '_SSPCsciv' ,
            null = 0 ,
            quiet = True)
        grass.run_command("r.null" ,
            map = prefix + '_SSPCrib' ,
            null = 0 ,
            quiet = True)
#elimino mappe
        grass.run_command('g.remove' , 
            flags='f',
            type='rast',
            name=(
                'slopes_' ,
                'aspects_' ,
                'aspects_1' ,
                'Asci' ,
                'Arib' ,
                'F1sci1' ,
                'F1sci2' ,
                'F1sci' ,
                'F1rib1' ,
                'F1rib2' ,
                'F1rib' ,
                'F2sci' ,
                'F3sci' ,
                'F3rib' ,
                'Isciv' ,
                'Irib' ,
                'delta' ,
                'A' ,
                'B' ,
                'C' ,
                'AP' ,
                'membro_sci' ,
                'membro_RIB' ,
                'sci' ,
                'rib' ,
                'cinem_sci' ,
                'consci1' ,
                'consci2' ,
                'conrib' ,
                'AP1' ,
                'cinem_rib') ,
            quiet = True)
    else:
        grass.run_command('g.remove' , 
            flags='f',
            type='rast',
            name=(
                'slopes_' ,
                'aspects_' ,
                'aspects_1' ,
                'Asci' ,
                'Arib' ,
                'F1sci1' ,
                'F1sci2' ,
                'F1sci' ,
                'F1rib1' ,
                'F1rib2' ,
                'F1rib' ,
                'F2sci' ,
                'F3sci' ,
                'F3rib' ,
                'Isciv' ,
                'Irib' ) ,
            quiet = True)
    grass.message("Done!")
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
