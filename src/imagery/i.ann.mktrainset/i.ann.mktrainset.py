#!/usr/bin/env python3

#
############################################################################
#
# MODULE:	    i.ann.mktrainset
# AUTHOR(S):	Yann Chemin <dr.yann.chemin@gmail.com>
# PURPOSE:	    Make a training set for any ANN train need
# COPYRIGHT:	(C) 2025 the GRASS Development Team
#
# 		This program is free software under the GNU General
# 		Public License (>=v2). Read the file COPYING that
# 		comes with GRASS for details.
#
#############################################################################
#
#%module
#% description: Export moving window samples from an imagery group and two rasters.
#% keyword: imagery
#% keyword: ANN
#% keyword: training
#% keyword: export
#%end
#%option G_OPT_I_GROUP
#% description: Imagery group name
#% required: yes
#%end
#%option G_OPT_R_INPUT
#% key: raster1
#% description: First raster input (clump)
#% required: yes
#%end
#%option G_OPT_R_INPUT
#% key: raster2
#% description: Second raster input (value)
#% required: yes
#%end
#%option
#% key: output_directory
#% type: string
#% description: Output directory
#% required: yes
#%end
#%option
#% key: window_width
#% type: integer
#% description: Moving window width in cells
#% required: yes
#% answer: 128 
#%end
#%option
#% key: window_height
#% type: integer
#% description: Moving window height in cells
#% required: yes
#% answer: 128 
#%end

import os
import numpy as np
import grass.script as gs
from grass.script import array as garray

def read_group_bands(group_name):
    bands = gs.read_command('i.group', group=group_name, format='shell').splitlines()
    return bands

def extract_window(array, row_off, col_off, height, width):
    return array[row_off:row_off+height, col_off:col_off+width]

def export_multiband_geotiff(band_arrays, out_path, transform, crs):
    import rasterio
    count = len(band_arrays)
    height, width = band_arrays[0].shape
    with rasterio.open(
        out_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=count,
        dtype=band_arrays[0].dtype,
        crs=crs,
        transform=transform
    ) as dst:
        for i, arr in enumerate(band_arrays, start=1):
            dst.write(arr, i)

def export_singleband_geotiff(array, out_path, transform, crs):
    import rasterio
    height, width = array.shape
    with rasterio.open(
        out_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=array.dtype,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(array, 1)

def r2np(raster, dtype='float32'):
    """raster to numpy"""
    return garray.array(mapname=raster, dtype=dtype)

def check_raster_exists(raster_name):
    """Return True if raster exists in current mapset/search path, else False."""
    found = gs.find_file(raster_name, element='cell')
    return bool(found and found['name'])

def main():
    options, flags = gs.parser()

    group = options['group']
    raster1 = options['raster1']
    raster2 = options['raster2']
    output_directory = options['output_directory']
    window_width = int(options['window_width'])
    window_height = int(options['window_height'])

    gs.verbose(f"Current LOCATION: {gs.gisenv()['LOCATION_NAME']}, MAPSET: {gs.gisenv()['MAPSET']}")

    # Get region info
    region = gs.region()
    nrows, ncols = region['rows'], region['cols']
    # Check existence of raster1 and raster2
    missing = []
    if not check_raster_exists(raster1):
        missing.append(raster1)
    if not check_raster_exists(raster2):
        missing.append(raster2)

    # Check existence of all group bands
    band_names = read_group_bands(group)
    for band in band_names:
        if not check_raster_exists(band):
            missing.append(band)

    print("End Check input group members")
    if missing:
        gs.fatal(_("The following raster maps do not exist: {}").format(", ".join(missing)))

    # Read rasters as numpy arrays
    band_arrays = [r2np(band, dtype='float32') for band in band_names]
    arr1 = r2np(raster1, dtype='int32')
    arr2 = r2np(raster2, dtype='int32')

    # Get CRS and transform
    xres = (region['e'] - region['w']) / ncols
    yres = (region['n'] - region['s']) / nrows
    from rasterio.transform import from_origin
    transform = from_origin(region['w'], region['n'], xres, yres)
    wkt = gs.read_command('g.proj', flags='w').strip()
    crs = wkt

    idx = 0
    for row in range(0, nrows - window_height + 1, window_height):
        for col in range(0, ncols - window_width + 1, window_width):
            window_bands = [extract_window(b, row, col, window_height, window_width) for b in band_arrays]
            win1 = extract_window(arr1, row, col, window_height, window_width)
            win2 = extract_window(arr2, row, col, window_height, window_width)

            clump_ids = np.unique(win1)
            for clump_id in clump_ids:
                if clump_id == 0:
                    continue
                mask = (win1 == clump_id)
                if not np.any(mask):
                    continue
                corresponding_value = win2[mask][0]
                # Create an output array: set all clump pixels to corresponding_value, others to 0 or np.nan
                out_array = np.zeros_like(win1, dtype=win2.dtype)
                out_array[mask] = corresponding_value
                out_subdir = os.path.join(output_directory, f"{idx:06d}")
                os.makedirs(out_subdir, exist_ok=True)
                out_group = os.path.join(out_subdir, f"group_{clump_id}_{corresponding_value}.tif")
                export_multiband_geotiff([b * mask for b in window_bands], out_group, transform, crs)
                out_r = os.path.join(out_subdir, f"{raster1}_clump{clump_id}_val{corresponding_value}.tif")
                export_singleband_geotiff(out_array, out_r, transform, crs)
                idx += 1


if __name__ == "__main__":
    main()
