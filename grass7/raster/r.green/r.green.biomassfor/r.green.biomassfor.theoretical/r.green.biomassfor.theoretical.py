#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.biomassfor.potential
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Pietro Zambelli and Francesco Geri, reviewed by Marco Ciolli
# PURPOSE:     Calculates the potential Ecological Bioenergy contained in a forest
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#%Module
#% description: Estimates potential bioenergy depending on forest increment, forest management and forest treatment
#% keyword: raster
#% keyword: biomass
#%End
#%option
#% key: energy_tops_hf
#% type: double
#% description: Energy for tops and branches in high forest in MWh/m³
#% answer: 0.49
#% guisection: Energy
#%end
#%option G_OPT_R_INPUT
#% key: increment
#% type: string
#% description: Map of increment
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
#% key: output_basename
#% type: string
#% gisprompt: new
#% description: Basename for potential bioenergy (HF,CC and total)
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




def main(opts, flgs):
    ow = overwrite()

    output = opts['output_prefix']

    increment=opts['increment']
    management=opts['management']
    treatment=opts['treatment']
    yield_surface=opts['yield_surface']

    p_bioenergyHF=output+'_t_bioenergyHF'
    p_bioenergyC=output+'_t_bioenergyC'
    p_bioenergy=output+'_t_bioenergy'


    #import pdb; pdb.set_trace()
    ECOHF = p_bioenergyHF+' = if('+management+'==1 && '+treatment+'==1 || '+management+' == 1 && '+treatment+'==99999, yield_pixp*%f, if('+management+'==1 && '+treatment+'==2, yield_pixp*%f + yield_pixp*%f))'                                     


    ECOCC = p_bioenergyC+' = if('+management+'==2, yield_pixp*'+opts['energy_tops_cop']+')'

    ECOT=p_bioenergy+' = ('+p_bioenergyHF+' + '+p_bioenergyC+')'

    run_command("r.mapcalc", overwrite=ow,expression='yield_pixp = ('+increment+'/'+yield_surface+')*((ewres()*nsres())/10000)')
       
    run_command("r.mapcalc", overwrite=ow,
                expression=ECOHF % tuple(map(float, (opts['energy_tops_hf'],
                                                     opts['energy_tops_hf'],
                                                     opts['energy_cormometric_vol_hf'])))
                                                     )

    run_command("r.mapcalc", overwrite=ow,expression=ECOCC)

    run_command("r.mapcalc", overwrite=ow,expression=ECOT)
    

    with RasterRow(p_bioenergy) as pT:
        T = np.array(pT)


    print "Resulted maps: "+output+"_t_bioenergyHF, "+output+"_t_bioenergyC, "+output+"_t_bioenergy"
    print ("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))

if __name__ == "__main__":
    main(*parser())
