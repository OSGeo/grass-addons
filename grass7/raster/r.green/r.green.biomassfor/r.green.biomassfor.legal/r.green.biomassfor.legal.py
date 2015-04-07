#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.biomassfor.legal
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Francesco Geri reviewed by Marco Ciolli
# PURPOSE:     Calculates the potential Ecological Bioenergy contained in a forest
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#%Module
#% description: Estimates legal bioenergy depending on yield, forest management and forest treatment
#% keyword: raster
#% keyword: biomass
#%End
#%option
#% key: energy_tops_hf
#% type: double
#% description: Energy for tops and branches in high forest in MWh/m³
#% answer: 0.49
#% required : yes
#% guisection: Energy
#%end
#%option G_OPT_R_INPUT
#% key: yield1
#% type: string
#% description: Map of forest yield (cubic meters)
#% required : yes
#%end
#%option G_OPT_R_INPUT
#% key: yield_surface
#% type: string
#% description: Map of stand surface (ha)
#% required : yes
#%end
#%option G_OPT_R_INPUT
#% key: management
#% type: string
#% description: Map of forest management (1: high forest, 2:coppice)
#% required : yes
#%end
#%option G_OPT_R_INPUT
#% key: treatment
#% type: string
#% description: Map of forest treatment (1: final felling, 2:thinning)
#% required : yes
#%end
#%option 
#% key: output_prefix
#% type: string
#% description: Prefix for potential bioenergy (HF,CC and total)
#% key_desc : name
#% required : yes
#%end
#%option
#% key: energy_cormometric_vol_hf
#% type: double
#% description: Energy for the whole tree in high forest (tops, branches and stem) in MWh/m³
#% answer: 1.97
#% required : no
#% guisection: Energy
#%end
#%option
#% key: energy_tops_cop
#% type: double
#% description: Energy for tops and branches for Coppices in MWh/m³
#% answer: 0.55
#% required : no
#% guisection: Energy
#%end

from grass.script.core import run_command, parser, overwrite
from grass.pygrass.raster import RasterRow
import numpy as np


#ECOCC = 'ecological_bioenergyC = if(management==2, yield_pix1*%f)'


def main(opts, flgs):
    ow = overwrite()

    output = opts['output_prefix']

    yield_=opts['yield1']
    management=opts['management']
    treatment=opts['treatment']
    yield_surface=opts['yield_surface']

    l_bioenergyHF=output+'_l_bioenergyHF'
    l_bioenergyC=output+'_l_bioenergyC'
    l_bioenergy=output+'_l_bioenergy'


    #import pdb; pdb.set_trace()
    #treatment=1 final felling, treatment=2 thinning
    ECOHF = l_bioenergyHF+' = if('+management+'==1 && '+treatment+'==1 || '+management+' == 1 && '+treatment+'==99999, yield_pix1*%f, if('+management+'==1 && '+treatment+'==2, yield_pix1*%f + yield_pix1*%f))'                                     

    #ECOHF = 'ecological_bioenergyHF = if(management==1 && treatment==1 || management == 1 && treatment==99999,yield_pix1*'+opts['energy_tops_hf']+', if(management==1 && treatment==2, yield_pix1*'+opts['energy_tops_hf']+' + yield_pix1*'+opts['energy_cormometric_vol_hf']+'))'

    ECOCC = l_bioenergyC+' = if('+management+'==2, yield_pix1*'+opts['energy_tops_cop']+')'

    ECOT=l_bioenergy+' = ('+l_bioenergyHF+' + '+l_bioenergyC+')'

    run_command("r.mapcalc", overwrite=ow,expression='yield_pix1 = ('+yield_+'/'+yield_surface+')*((ewres()*nsres())/10000)')
       
    run_command("r.mapcalc", overwrite=ow,
                expression=ECOHF % tuple(map(float, (opts['energy_tops_hf'],
                                                     opts['energy_tops_hf'],
                                                     opts['energy_cormometric_vol_hf'])))
                                                     )

    run_command("r.mapcalc", overwrite=ow,expression=ECOCC)

    run_command("r.mapcalc", overwrite=ow,expression=ECOT)



    with RasterRow(l_bioenergy) as pT:
        T = np.array(pT)


    print "Resulted maps: "+output+"_l_bioenergyHF, "+output+"_l_bioenergyC, "+output+"_l_bioenergy"
    print ("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))



    #print ECOHF % tuple(map(float, (opts['energy_tops_hf'],opts['energy_tops_hf'],opts['energy_cormometric_vol_hf'])))

if __name__ == "__main__":
    main(*parser())
