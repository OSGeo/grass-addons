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

# %module
# % description: Moves water downhill into pools or the ocean/map edge
# % keyword: raster
# % keyword: hydrology
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  label: Input DEM
# %  required: yes
# %end

# %option
# % key: np
# % type: integer
# % description: Number of processors to use (>= 3)
# % required: yes
# %end

# %option
# % key: threshold
# % type: double
# % label: Threshold water-surface elevation change to conclude calculation
# % answer: 0.001
# % required: no
# %end

# %option
# % key: h_runoff
# % type: double
# % label: Initial depth of uniform runoff [thickness in map units]
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: h_runoff_raster
# % type: string
# % label: Initial depth of non-uniform runoff [thickness in map units]
# % required: no
# %end

# %option
# % key: ties
# % type: string
# % label: Tie-handling: counterclockwise from Northwest (PREF) or random (RAND)
# % answer: PREF
# % options: PREF,RAND
# % required: no
# %end

# %option
# % key: ffpath
# % type: string
# % label: Path to the FlowFill executable
# % answer: flowfill
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  label: Output DEM + pooled/remaining runoff
# %  required: no
# %end

# %option G_OPT_R_OUTPUT
# %  key: water
# %  label: Output water depth at the end of the run
# %  required: no
# %end

##################
# IMPORT MODULES #
##################
# PYTHON
import os
import numpy as np
import subprocess

# GRASS
from grass import script as gscript
from grass.script import array as garray
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import general as g

###############
# MAIN MODULE #
###############


def main():
    """
    FlowFill
    """
    # netCDF4
    try:
        from netCDF4 import Dataset
    except:
        g.fatal(
            _(
                "netCDF4 not detected. Install pip3 and "
                "then type at the command prompt: "
                '"pip3 install netCDF4".'
            )
        )

    options, flags = gscript.parser()
    _input = options["input"]
    _np = options["np"]
    _threshold = options["threshold"]
    _h_runoff = options["h_runoff"]
    _h_runoff_raster = options["h_runoff_raster"]
    _ties = options["ties"]
    _ffpath = options["ffpath"]
    _output = options["output"]
    _water = options["water"]

    """
    import os
    import numpy as np
    from netCDF4 import Dataset
    # GRASS
    from grass import script as gscript
    from grass.script import array as garray
    from grass.pygrass.modules.shortcuts import raster as r
    from grass.pygrass.modules.shortcuts import general as g

    # FOR TESTING:
    _input = 'DEM_MODFLOW'
    _np = 4
    _threshold = 0.001
    #_h_runoff = 1.
    _h_runoff = ''
    #_h_runoff_raster = ''
    _h_runoff_raster = 'DEM_MODFLOW'
    _ties = 'PREF'
    _ffpath = 'flowfill'
    _output = 'tmpout'
    _water = 'tmpout_water'
    """

    # Check for overwrite -- should be unnecessary thanks to GRASS parser
    _rasters = np.array(gscript.parse_command("g.list", type="raster").keys())
    if (_rasters == _output).any() or (_water == _output).any():
        if gscript.overwrite() is False:
            g.fatal(_("output would overwrite " + _output))

    # Check for proper number of processors
    try:
        _np = int(_np)
    except:
        g.fatal(_("Number of processors must be an integer."))

    if _np < 3:
        g.fatal(_("FlowFill requires 3 or more processors."))

    # Check for proper option set
    if _h_runoff is not "":  # ????? possible ?????
        if _h_runoff_raster is not "":
            g.fatal(_('Only one of "h_runoff" and "h_runoff_raster" may be set'))
    elif _h_runoff_raster is "":
        g.fatal(_('Either "h_runoff" or "h_runoff_raster" must be set'))

    if _output is "" and _water is "":
        g.warning(_("No output is set."))

    # Set up runoff options
    if _h_runoff_raster is not "":
        _runoff_bool = "Y"
    else:
        _h_runoff = float(_h_runoff)
        _runoff_bool = "N"

    # Get computational region
    n_columns = gscript.region()["cols"]
    n_rows = gscript.region()["rows"]

    # Output DEM as temporary file for FORTRAN
    temp_FlowFill_input_file = gscript.tempfile(create=False)
    dem = garray.array(_input, null=-999999)
    dem_array = np.array(dem[:]).astype(np.float32)
    del dem
    newnc = Dataset(temp_FlowFill_input_file, "w", format="NETCDF4")
    newnc.createDimension("x", n_columns)
    newnc.createDimension("y", n_rows)
    newnc.createVariable("value", "f4", ("y", "x"))  # z
    newnc.variables["value"][:] = dem_array
    newnc.close()
    del newnc
    # r.out_gdal(input=_input, output=temp_DEM_input_file, format='netCDF',
    #           overwrite=True)

    # Output runoff raster as temporary file for FORTRAN
    if _h_runoff_raster is not "":
        temp_FlowFill_runoff_file = gscript.tempfile(create=False)
        rr = garray.array(_h_runoff_raster, null=0.0)
        rr_array = np.array(rr[:]).astype(np.float32)
        del rr
        newnc = Dataset(temp_FlowFill_runoff_file, "w", format="NETCDF4")
        newnc.createDimension("x", n_columns)
        newnc.createDimension("y", n_rows)
        newnc.createVariable("value", "f4", ("y", "x"))  # z
        newnc.variables["value"][:] = rr_array
        newnc.close()
        # Get the mean value for the floating-point depressions correction
        _h_runoff = np.mean(rr_array[dem_array != -999999])
    else:
        _h_runoff_raster = "NoRaster"  # A dummy value for the parser
        temp_FlowFill_runoff_file = ""

    # Run FlowFill
    temp_FlowFill_output_file = gscript.tempfile(create=False)
    mpirunstr = (
        "mpirun -np "
        + str(_np)
        + " "
        + _ffpath
        + " "
        + str(_h_runoff)
        + " "
        + temp_FlowFill_input_file
        + " "
        + str(n_columns)
        + " "
        + str(n_rows)
        + " "
        + str(_threshold)
        + " "
        + temp_FlowFill_output_file
        + " "
        + _runoff_bool
        + " "
        + temp_FlowFill_runoff_file
        + " "
        + _ties
    )
    print("")
    print("Sending command to FlowFill:")
    print(mpirunstr)
    print("")

    _mpirun_error_flag = False

    popen = subprocess.Popen(
        mpirunstr, stdout=subprocess.PIPE, shell=True, universal_newlines=True
    )
    for stdout_line in iter(popen.stdout.readline, ""):
        print(stdout_line),
        if "mpirun was unable to find the specified executable file" in stdout_line:
            _mpirun_error_flag = True
    popen.stdout.close()
    if _mpirun_error_flag:
        print("")
        g.fatal(
            _(
                "FlowFill executable not found.\n"
                "If you have not installed FlowFill, please download it "
                "from https://github.com/KCallaghan/FlowFill, "
                "and follow the directions in the README to compile and "
                "install it on your system.\n"
                'This should then work with the default "ffpath". '
                "Otherwise, you may simply have typed in an incorrect "
                '"ffpath".'
            )
        )

    # _stdout = subprocess.Popen(mpirunstr, shell=True, stdout=subprocess.PIPE)
    #
    # if 'mpirun was unable to find the specified executable file' in \
    #                              ''.join(_stdout.stdout.readlines()):
    # else:
    #    g.message('FlowFill Executable Found.')
    #    print('')

    # subprocess.Popen(mpirunstr, shell=True).wait()
    # os.system(mpirunstr)
    # subprocess.Popen(mpirunstr, shell=True)

    # Import the output -- padded by two cells (remove these)
    outrast = np.fromfile(temp_FlowFill_output_file + ".dat", dtype=np.float32)
    outrast_water = np.fromfile(
        temp_FlowFill_output_file + "_water.dat", dtype=np.float32
    )
    outrast = outrast.reshape(n_rows + 2, n_columns + 2)[:-2, 1:-1]
    outrast_water = outrast_water.reshape(n_rows + 2, n_columns + 2)[:-2, 1:-1]

    # Mask to return NAN to NAN in GRASS -- FIX SHIFT ISSUE WITH KERRY
    dem_array_mask = dem_array.copy()
    dem_array_mask[dem_array_mask == -999999] = np.nan
    dem_array_mask = dem_array_mask * 0 + 1
    outrast *= dem_array_mask
    outrast_water *= dem_array_mask

    # Save the output to GRASS GIS
    dem = garray.array()
    dem[:] = outrast
    dem.write(_output, overwrite=gscript.overwrite())
    dem[:] = outrast_water
    dem.write(_water, overwrite=gscript.overwrite())
    del dem


if __name__ == "__main__":
    main()
