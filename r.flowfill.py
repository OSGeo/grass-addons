#!/usr/bin/env python
############################################################################
#
# MODULE:       r.flowfill
#
# AUTHOR(S):    Kerry Callaghan, Andrew Wickert
#
# PURPOSE:      Moves water across a landscape towards its eventual equilibrium 
#               position using an iterative, mass-conserving approach
#
# COPYRIGHT:    (c) 2019 Andrew Wickert
#               FlowFill is (c) 2018-2019 Kerry L. Callaghan
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS: FlowFill, libmpich-dev, libnetcdff-dev
 
# More information
# Started June 2019

#%module
#% description: Moves water downhill into pools or the ocean/map edge
#% keyword: raster
#% keyword: hydrology
#%end

#%option G_OPT_R_INPUT
#%  key: input
#%  label: Input DEM
#%  required: yes
#%end

#%option
#% key: np
#% type: integer
#% description: Number of processors to use (>= 3)
#% required: yes
#%end

#%option
#% key: threshold
#% type: double
#% label: Threshold water-surface elevation change to conclude calculation
#% answer: 0.001
#% required: yes
#%end

#%option
#% key: h_runoff
#% type: double
#% label: Initial depth of uniform runoff [thickness in map units]
#% required: no
#%end

#%option G_OPT_R_INPUT
#% key: h_runoff_raster
#% type: str
#% label: Initial depth of non-uniform runoff [thickness in map units]
#% required: no
#%end

#%option
#% key: ties
#% type: str
#% label: Tie-handling: clockwise from North (PREF) or random (RAND)
#% answer: PREF
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#%  key: output
#%  label: Output DEM + pooled/remaining runoff
#%  required: yes
#%end

##################
# IMPORT MODULES #
##################
# PYTHON
import os
import numpy as np
from netCDF4 import Dataset
# GRASS
from grass import script as gscript
from grass.script import array as garray
from grass.pygrass.modules.shortcuts import raster as r
        
###############
# MAIN MODULE #
###############

def main():
    """
    FlowFill
    """
    
    options, flags = gscript.parser()
    _input = options['input']
    _np = options['_np']
    _threshold = options['_threshold']
    _h_runoff = options['_h_runoff']
    _h_runoff_raster = options['_h_runoff_raster']
    _ties = options['_ties']
    _output = options['output']
    
    
    
    
    import os
    import numpy as np
    from netCDF4 import Dataset
    # GRASS
    from grass import script as gscript
    from grass.script import array as garray
    from grass.pygrass.modules.shortcuts import raster as r

    # FOR TESTING:
    _input = 'DEM'
    _np = 4
    _threshold = 0.001
    _h_runoff = 1.
    _h_runoff_raster = ''
    _ties = 'PREF'
    _output = 'tmpout.nc'
    
    # Check for overwrite
    _rasters = np.array(gscript.parse_command('g.list', type='raster').keys())
    if (_rasters == _output).any():
        g.message(flags='e', message="output would overwrite "+_output)

    # Check for proper option set
    if _h_runoff is not '': # ????? possible ?????
        if _h_runoff_raster is not '':
            g.message(flags='e', message='Only one of "h_runoff" and '+
                                         '"h_runoff_raster" may be set')
    elif _h_runoff_raster is '':             
            g.message(flags='e', message='Either "h_runoff" or '+
                                         '"h_runoff_raster" must be set')

    # Set up runoff options
    if _h_runoff_raster is not '':
        _runoff_bool = 'Y'
    else:
        _runoff_bool = 'N'

    # Get computational region
    n_columns = gscript.region()['cols']
    n_rows = gscript.region()['rows']
    
    # Output DEM as temporary file for FORTRAN
    temp_FlowFill_input_file = gscript.tempfile(create=False)
    dem = garray.array()
    dem.read(_input, null=0)#np.nan) # Can it handle nan?
    dem_array = np.array(dem[:]).astype(np.float32)
    newnc = Dataset(temp_FlowFill_input_file, "w", format="NETCDF4")
    newnc.createDimension('x', n_columns)
    newnc.createDimension('y', n_rows)
    newnc.createVariable('value', 'f4', ('y', 'x')) # z
    newnc.variables['value'][:] = dem_array
    newnc.close()
    #r.out_gdal(input=_input, output=temp_DEM_input_file, format='netCDF',
    #           overwrite=True)
    
    # Run FlowFill
    temp_FlowFill_output_file = gscript.tempfile(create=False)
    PATH_TO_FLOWFILL_EXECUTABLE = './test'
    os.system('mpirun -np '+str(_np)+' '+PATH_TO_FLOWFILL_EXECUTABLE+' '+
              str(_h_runoff)+' '+temp_FlowFill_input_file+' '+str(n_rows)+' '+
              str(n_columns)+' '+str(_threshold)+' '+
              temp_FlowFill_output_file+' '+
              _runoff_bool+' '+_h_runoff_raster+' '+_ties)



print 'mpirun -np '+str(_np)+' '+PATH_TO_FLOWFILL_EXECUTABLE+' '+\
              str(_h_runoff)+' '+temp_FlowFill_input_file+' '+str(n_rows)+' '+str(n_columns)+' '+\
              str(_threshold)+' '+temp_FlowFill_output_file+' '+\
              _runoff_bool+' '+_h_runoff_raster+' '+_ties

    # Bring in output
    # r.in.gdal?

if __name__ == "__main__":
    main()
    
