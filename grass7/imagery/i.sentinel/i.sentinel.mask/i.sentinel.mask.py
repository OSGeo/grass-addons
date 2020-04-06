#!/usr/bin/env python
# coding=utf-8
#
############################################################################
#
# MODULE:       i.sentinel.mask
# AUTHOR(S):    Roberta Fagandini, Moritz Lennert, Roberto Marzocchi
# PURPOSE:      Creates clouds and shadows masks for Sentinel-2 images
#
# COPYRIGHT:    (C) 2018 by Roberta Fagandini, and the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
#
#############################################################################

#%Module
#% description: Creates clouds and shadows masks for Sentinel-2 images.
#% keyword: imagery
#% keyword: satellite
#% keyword: Sentinel
#% keyword: cloud detection
#% keyword: shadow
#% keyword: reflectance
#%End
#%option G_OPT_F_INPUT
#% key: input_file
#% description: name of the .txt file with listed input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: blue
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: green
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: red
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: nir
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: nir8a
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: swir11
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_R_INPUT
#% key: swir12
#% description: input bands
#% required : no
#% guisection: Required
#%end
#%option G_OPT_V_OUTPUT
#% key: cloud_mask
#% description: name of output vector cloud mask
#% required : no
#% guisection: Output
#%end
#%option G_OPT_R_OUTPUT
#% key: cloud_raster
#% description: Name of output raster cloud mask
#% required : no
#% guisection: Output
#%end
#%option G_OPT_V_OUTPUT
#% key: shadow_mask
#% description: name of output vector shadow mask
#% required : no
#% guisection: Output
#%end
#%option G_OPT_R_OUTPUT
#% key: shadow_raster
#% description: name of output vector shadow mask
#% required : no
#% guisection: Output
#%end
#%option
#% key: cloud_threshold
#% type: integer
#% description: threshold for cleaning small areas from cloud mask (in square meters)
#% required : yes
#% answer: 50000
#% guisection: Output
#%end
#%option
#% key: shadow_threshold
#% type: integer
#% description: threshold for cleaning small areas from shadow mask (in square meters)
#% required : yes
#% answer: 10000
#% guisection: Output
#%end
#%option G_OPT_F_INPUT
#% key: mtd_file
#% description: name of the image metadata file (MTD_TL.xml)
#% required : no
#% guisection: Metadata
#%end
#%option G_OPT_F_INPUT
#% key: metadata
#% description: Name of Sentinel metadata json dump
#% required : no
#% guisection: Metadata
#%end
#%option
#% key: scale_fac
#% type: integer
#% description: rescale factor
#% required : no
#% answer: 10000
#% guisection: Rescale
#%end
#%flag
#% key: r
#% description: Set computational region to maximum image extent
#%end
#%flag
#% key: t
#% description: Do not delete temporary files
#%end
#%flag
#% key: s
#% description: Rescale input bands
#% guisection: Rescale
#%end
#%flag
#% key: c
#% description: Compute only the cloud mask
#%end

#%rules
#% collective: blue,green,red,nir,nir8a,swir11,swir12
#% requires: shadow_mask,mtd_file,metadata
#% requires: shadow_raster,mtd_file,metadata
#% excludes: mtd_file,metadata
#% required: cloud_mask,cloud_raster,shadow_mask,shadow_raster
#% excludes: -c,shadow_mask,shadow_raster
#% required: input_file,blue,green,red,nir,nir8a,swir11,swir12,mtd_file
#% excludes: input_file,blue,green,red,nir,nir8a,swir11,swir12,mtd_file
#%end

import math
import os
import sys
import shutil
import subprocess
import re
import glob
import time
import atexit
import json
import xml.etree.ElementTree as et

import numpy
import grass.script as gscript


def main ():


    # Temporary map names
    global tmp, t, mapset
    tmp = {}
    mapset = gscript.gisenv()['MAPSET']
    mapset2 = '@{}'.format(mapset)
    processid = os.getpid()
    processid = str(processid)
    tmp["shadow_temp"] = "shadow_temp"+ processid
    tmp["cloud_v"] = "cloud_v_" + processid
    tmp["shadow_temp_v"] = "shadow_temp_v_" + processid
    tmp["shadow_temp_mask"] = "shadow_temp_mask_" + processid
    tmp["centroid"] = "centroid_" + processid
    tmp["dissolve"] = "dissolve_" + processid
    tmp["delcat"] = "delcat_" + processid
    tmp["addcat"] = "addcat_" + processid
    tmp["cl_shift"] = "cl_shift_" + processid
    tmp["overlay"] = "overlay_" + processid

    # Check temporary map names are not existing maps
    for key, value in tmp.items():
        if gscript.find_file(value,
            element = 'vector',
            mapset = mapset)['file']:
            gscript.fatal(('Temporary vector map <{}> already exists.').format(value))
        if gscript.find_file(value,
            element = 'cell',
            mapset = mapset)['file']:
            gscript.fatal(('Temporary raster map <{}> already exists.').format(value))

    # Input file
    mtd_file = options['mtd_file']
    metadata_file = options['metadata']
    bands = {}
    error_msg = 'Syntax error in the txt file. See the manual for further information about the right syntax.'
    if options['input_file'] == '':
        bands['blue'] = options['blue']
        bands['green'] = options['green']
        bands['red'] = options['red']
        bands['nir'] = options['nir']
        bands['nir8a'] = options['nir8a']
        bands['swir11'] = options['swir11']
        bands['swir12'] = options['swir12']
    else:
        txt_bands = []
        with open(options['input_file'], 'r') as input_file:
            for line in input_file:
                a = line.split('=')
                if len(a) != 2:
                    gscript.fatal(error_msg)
                elif a[0] == 'MTD_TL.xml' and not mtd_file:
                    mtd_file = a[1].strip()
                elif a[0] == 'metadata' and not metadata_file:
                    metadata_file = a[1].strip()
                elif a[0] in ['blue',
                    'green',
                    'red',
                    'nir',
                    'nir8a',
                    'swir11',
                    'swir12']:
                    txt_bands.append(a[0])
                    bands[a[0]] = a[1].strip()
            if len(txt_bands) < 7:
                gscript.fatal(('One or more bands are missing in the input text file.\n Only these bands have been found: {}').format(txt_bands))
            if mtd_file and metadata_file:
                gscript.fatal(('Metadata json file and mtd_file are both given as input text files.\n Only one of these should be specified.'))

    d = 'double'
    f_bands = {}
    scale_fac = options['scale_fac']
    cloud_threshold = options['cloud_threshold']
    shadow_threshold = options['shadow_threshold']
    raster_max = {}
    check_cloud = 1 #by default the procedure finds clouds
    check_shadow = 1 #by default the procedure finds shadows

    if options['cloud_raster']:
        cloud_raster = options['cloud_raster']
    else:
        tmp["cloud_def"] = "cloud_def"+ processid
        cloud_raster = tmp["cloud_def"]
    if options['cloud_mask']:
        cloud_mask = options['cloud_mask']
        if '.' in options['cloud_mask']:
            gscript.fatal('Name for cloud_mask output \
                           is not SQL compliant'.format(options['cloud_mask']))
    else:
        tmp["cloud_mask"] = "cloud_mask"+ processid
        cloud_mask = tmp["cloud_mask"]
    if options['shadow_mask']:
        shadow_mask = options['shadow_mask']
        if '.' in options['shadow_mask']:
            gscript.fatal('Name for shadow_mask output \
                           is not SQL compliant'.format(options['shadow_mask']))
    else:
        tmp["shadow_mask"] = "shadow_mask"+ processid
        shadow_mask = tmp["shadow_mask"]
    shadow_raster = options['shadow_raster']

    # Check if all required input bands are specified in the text file
    if (bands['blue'] == '' or
        bands['green'] == '' or
        bands['red'] == '' or
        bands['nir'] == '' or
        bands['nir8a'] == ''or
        bands['swir11'] == '' or
        bands['swir12'] == ''):
        gscript.fatal('All input bands (blue, green, red, nir, nir8a, swir11, swir12) are required')

    # Check if input bands exist
    for key, value in bands.items():
        if not gscript.find_file(value,
            element = 'cell',
            mapset = mapset)['file']:
            gscript.fatal(('Raster map <{}> not found.').format(value))

    # Check input and output for shadow mask
    if not flags["c"]:
        if mtd_file == '' and metadata_file == '':
            gscript.fatal('Metadata (file) is required for shadow mask computation. Please specifiy it')
        if mtd_file != '':
            if not os.path.exists(mtd_file):
                 gscript.fatal('Metadata file <{}> not found. Please select the right .xml file'.format(mtd_file))
        elif metadata_file != '':
            if not os.path.exists(metadata_file):
                 gscript.fatal('Metadata file <{}> not found. Please select the right file'.format(metadata_file))

    if flags["r"]:
        gscript.use_temp_region()
        gscript.run_command('g.region',
            rast=bands.values(),
            flags='a')
        gscript.message(_('--- The computational region has been temporarily set to image max extent ---'))
    else:
        gscript.warning(_('All subsequent operations will be limited to the current computational region'))

    if flags["s"]:
        gscript.message(_('--- Start rescaling bands ---'))
        for key, b in bands.items():
            gscript.message(b)
            b = gscript.find_file(b, element = 'cell')['name']
            gscript.mapcalc('{r} = 1.0 * ({b})/{scale_fac}'.format(
                r=("{}_{}".format(b, d)),
                b=b,
                scale_fac=scale_fac))
            f_bands[key] = "{}_{}".format(b, d)
        gscript.message(f_bands.values())
        gscript.message(_('--- All bands have been rescaled ---'))
    else:
        gscript.warning(_('Any rescale factor has been applied'))
        for key, b in bands.items():
            if (gscript.raster_info(b)['datatype'] != "DCELL" and
                gscript.raster_info(b)['datatype'] != "FCELL"):
                gscript.fatal('Raster maps must be DCELL o FCELL')
            else:
                f_bands = bands

    gscript.message(_('--- Start computing maximum values of bands ---'))
    for key, fb in f_bands.items():
        gscript.message(fb)
        stats = gscript.parse_command('r.univar', flags='g', map=fb)
        raster_max[key] = (float(stats['max']))
    gscript.message('--- Computed maximum value: {} ---'.format(
        raster_max.values()))
    gscript.message(_('--- Statistics have been computed! ---'))

    # Start of Clouds detection  (some rules from litterature)
    gscript.message(_('--- Start clouds detection procedure ---'))
    gscript.message(_('--- Computing cloud mask... ---'))
    first_rule = '(({} > (0.08*{})) && ({} > (0.08*{})) && ({} > (0.08*{})))'.format(
        f_bands['blue'],
        raster_max['blue'],
        f_bands['green'],
        raster_max['green'],
        f_bands['red'],
        raster_max['red'])
    second_rule = '(({} < ((0.08*{})*1.5)) && ({} > {}*1.3))'.format(
        f_bands['red'],
        raster_max['red'],
        f_bands['red'],
        f_bands['swir12'])
    third_rule = '(({} < (0.1*{})) && ({} < (0.1*{})))'.format(
        f_bands['swir11'],
        raster_max['swir11'],
        f_bands['swir12'],
        raster_max['swir12'])
    fourth_rule = '(if({} == max({}, 2 * {}, 2 * {}, 2 * {})))'.format(
        f_bands['nir8a'],
        f_bands['nir8a'],
        f_bands['blue'],
        f_bands['green'],
        f_bands['red'])
    fifth_rule = '({} > 0.2)'.format(f_bands['blue'])
    cloud_rules = '({} == 1) && ({} == 0) && ({} == 0) && ({} == 0) && ({} == 1)'.format(
        first_rule,
        second_rule,
        third_rule,
        fourth_rule,
        fifth_rule)
    expr_c = '{} = if({}, 0, null())'.format(
        cloud_raster,
        cloud_rules)
    gscript.mapcalc(expr_c, overwrite=True)
    gscript.message(_('--- Converting raster cloud mask into vector map ---'))
    gscript.run_command('r.to.vect',
        input=cloud_raster,
        output=tmp["cloud_v"],
        type='area',
        flags='s')
    info_c = gscript.parse_command('v.info',
        map=tmp["cloud_v"],
        flags='t')
    if info_c['areas'] == '0':
        gscript.warning(_('No clouds have been detected'))
        check_cloud = 0
    else:
        gscript.message(_('--- Cleaning geometries ---'))
        gscript.run_command('v.clean',
            input=tmp["cloud_v"],
            output=cloud_mask,
            tool='rmarea',
            threshold=cloud_threshold)
        info_c_clean = gscript.parse_command('v.info',
            map=cloud_mask,
            flags='t')
        if info_c_clean['areas'] == '0':
            gscript.warning(_('No clouds have been detected'))
            check_cloud = 0
        else:
            check_cloud = 1
    gscript.message(_('--- Finish cloud detection procedure ---'))
    # End of Clouds detection

    if options['shadow_mask'] or options['shadow_raster']:
        # Start of shadows detection
        gscript.message(_('--- Start shadows detection procedure ---'))
        gscript.message(_('--- Computing shadow mask... ---'))
        sixth_rule = '((({} > {}) && ({} < {}) && ({} < 0.1) && ({} < 0.1)) \
        || (({} < {}) && ({} < {}) && ({} < 0.1) && ({} < 0.1) && ({} < 0.1)))'.format(
            f_bands['blue'],
            f_bands['swir12'],
            f_bands['blue'],
            f_bands['nir'],
            f_bands['blue'],
            f_bands['swir12'],
            f_bands['blue'],
            f_bands['swir12'],
            f_bands['blue'],
            f_bands['nir'],
            f_bands['blue'],
            f_bands['swir12'],
            f_bands['nir'])
        seventh_rule = '({} - {})'.format(
            f_bands['green'],
            f_bands['blue'])
        shadow_rules = '(({} == 1) && ({} < 0.007))'.format(
            sixth_rule,
            seventh_rule)
        expr_s = '{} = if({}, 0, null())'.format(
            tmp["shadow_temp"],
            shadow_rules)
        gscript.mapcalc( expr_s, overwrite=True)
        gscript.message(_('--- Converting raster shadow mask into vector map ---'))
        gscript.run_command('r.to.vect',
            input=tmp["shadow_temp"],
            output=tmp["shadow_temp_v"],
            type='area',
            flags='s',
            overwrite=True)
        info_s = gscript.parse_command('v.info',
            map=tmp["shadow_temp_v"],
            flags='t')
        if info_s['areas'] == '0':
            gscript.warning(_('No shadows have been detected'))
            check_shadow = 0
        else:
            gscript.message(_('--- Cleaning geometries ---'))
            gscript.run_command('v.clean',
                input=tmp["shadow_temp_v"],
                output=tmp["shadow_temp_mask"],
                tool='rmarea',
                threshold=shadow_threshold)
            info_s_clean = gscript.parse_command('v.info',
                map=tmp["shadow_temp_mask"],
                flags='t')
            if info_s_clean['areas'] == '0':
                gscript.warning(_('No shadows have been detected'))
                check_shadow = 0
            else:
                check_shadow = 1
            gscript.message(_('--- Finish Shadows detection procedure ---'))
            # End of shadows detection

            # START shadows cleaning Procedure (remove shadows misclassification)
            # Start shadow mask preparation
            if check_shadow == 1 and check_cloud == 1:
                gscript.message(_('--- Start removing misclassification from the shadow mask ---'))
                gscript.message(_('--- Data preparation... ---'))
                gscript.run_command('v.centroids',
                    input=tmp["shadow_temp_mask"],
                    output=tmp["centroid"], quiet=True)
                gscript.run_command('v.db.droptable',
                    map=tmp["centroid"],
                    flags='f', quiet=True)
                gscript.run_command('v.db.addtable',
                    map=tmp["centroid"],
                    columns='value', quiet=True)
                gscript.run_command('v.db.update',
                    map=tmp["centroid"],
                    layer=1,
                    column='value',
                    value=1, quiet=True)
                gscript.run_command('v.dissolve',
                    input=tmp["centroid"],
                    column='value',
                    output=tmp["dissolve"],
                    quiet=True)
                gscript.run_command('v.category',
                    input=tmp["dissolve"],
                    type='point,line,boundary,centroid,area,face,kernel',
                    output=tmp["delcat"],
                    option='del',
                    cat=-1,
                    quiet=True)
                gscript.run_command('v.category',
                    input=tmp["delcat"],
                    type='centroid,area',
                    output=tmp["addcat"],
                    option='add',
                    quiet=True)
                gscript.run_command('v.db.droptable',
                    map=tmp["addcat"],
                    flags='f', quiet=True)
                gscript.run_command('v.db.addtable',
                    map=tmp["addcat"],
                    columns='value', quiet=True)

                # End shadow mask preparation
                # Start cloud mask preparation

                gscript.run_command('v.db.droptable',
                    map=cloud_mask,
                    flags='f', quiet=True)
                gscript.run_command('v.db.addtable',
                    map=cloud_mask,
                    columns='value', quiet=True)

                # End cloud mask preparation
                # Shift cloud mask using dE e dN
                # Start reading mean sun zenith and azimuth from xml file to compute
                #dE and dN automatically
                gscript.message(_('--- Reading mean sun zenith and azimuth from metadata file to compute clouds shift ---'))
                if mtd_file != '':
                    try:
                        xml_tree = et.parse(mtd_file)
                        root = xml_tree.getroot()
                        ZA = []
                        try:
                            for elem in root[1]:
                                for subelem in elem[1]:
                                    ZA.append(subelem.text)
                            if ZA == ['0', '0']:
                                zenith_val = root[1].find('Tile_Angles').find('Sun_Angles_Grid').find('Zenith').find('Values_List')
                                ZA[0] = numpy.mean([numpy.array(elem.text.split(' '), dtype=numpy.float) for elem in zenith_val])
                                azimuth_val = root[1].find('Tile_Angles').find('Sun_Angles_Grid').find('Azimuth').find('Values_List')
                                ZA[1] = numpy.mean([numpy.array(elem.text.split(' '), dtype=numpy.float) for elem in azimuth_val])
                            z = float(ZA[0])
                            a = float(ZA[1])
                            gscript.message('--- the mean sun Zenith is: {:.3f} deg ---'.format(z))
                            gscript.message('--- the mean sun Azimuth is: {:.3f} deg ---'.format(a))
                        except:
                            gscript.fatal('The selected input metadata file is not the right one. Please check the manual page.')
                    except:
                        gscript.fatal('The selected input metadata file is not an .xml file. Please check the manual page.')
                elif metadata_file != '':
                    with open(metadata_file) as json_file:
                        data = json.load(json_file)
                    z = float(data['MEAN_SUN_ZENITH_ANGLE'])
                    a = float(data['MEAN_SUN_AZIMUTH_ANGLE'])

                # Stop reading mean sun zenith and azimuth from xml file to compute dE
                #and dN automatically
                # Start computing the east and north shift for clouds and the
                #overlapping area between clouds and shadows at steps of 100m
                gscript.message(_('--- Start computing the east and north clouds shift at steps of 100m of clouds height---'))
                H = 1000
                dH = 100
                HH = []
                dE = []
                dN = []
                AA = []
                while H <= 4000:
                    z_deg_to_rad = math.radians(z)
                    tan_Z = math.tan(z_deg_to_rad)
                    a_deg_to_rad = math.radians(a)
                    cos_A = math.cos(a_deg_to_rad)
                    sin_A = math.sin(a_deg_to_rad)

                    E_shift = (-H * tan_Z * sin_A)
                    N_shift = (-H * tan_Z * cos_A)
                    dE.append (E_shift)
                    dN.append (N_shift)

                    HH.append(H)
                    H = H + dH

                    gscript.run_command('v.transform',
                        input=cloud_mask,
                        output=tmp["cl_shift"],
                        xshift=E_shift,
                        yshift=N_shift,
                        overwrite=True,
                        quiet=True, stderr=subprocess.DEVNULL)
                    gscript.run_command('v.overlay',
                        ainput=tmp["addcat"],
                        binput=tmp["cl_shift"],
                        operator='and',
                        output=tmp["overlay"],
                        overwrite=True,
                        quiet=True, stderr=subprocess.DEVNULL)
                    gscript.run_command('v.db.addcolumn',
                        map=tmp["overlay"],
                        columns='area double')
                    area = gscript.read_command('v.to.db',
                        map=tmp["overlay"],
                        option='area',
                        columns='area',
                        flags='c')
                    area2 = gscript.parse_key_val(area, sep='|')
                    AA.append(float(area2['total area']))

                # Find the maximum overlapping area between clouds and shadows
                index_maxAA = numpy.argmax(AA)

                # Clouds are shifted using the clouds height corresponding to the
                #maximum overlapping area then are intersected with shadows
                gscript.run_command('v.transform',
                    input=cloud_mask,
                    output=tmp["cl_shift"],
                    xshift=dE[index_maxAA],
                    yshift=dN[index_maxAA],
                    overwrite=True,
                    quiet=True)
                gscript.run_command('v.select',
                    ainput=tmp["addcat"],
                    atype='point,line,boundary,centroid,area',
                    binput=tmp["cl_shift"],
                    btype='point,line,boundary,centroid,area',
                    output=shadow_mask,
                    operator='intersects',
                    quiet=True)
                if gscript.find_file(name=shadow_mask, element='vector')['file']:
                    info_cm = gscript.parse_command('v.info', map=shadow_mask,
                                                    flags='t')
                else:
                    info_cm = None
                    gscript.warning(_('No cloud shadows detected'))

                if options['shadow_raster'] and info_cm:
                    if info_cm['areas'] > '0':
                        gscript.run_command('v.to.rast', input=tmp["shadow_temp_mask"],
                                            output=shadow_raster, use='val')
                    else:
                         gscript.warning(_('No cloud shadows detected'))


                gscript.message('--- the estimated clouds height is: {} m ---'.format(HH[index_maxAA]))
                gscript.message('--- the estimated east shift is: {:.2f} m ---'.format(dE[index_maxAA]))
                gscript.message('--- the estimated north shift is: {:.2f} m ---'.format(dN[index_maxAA]))
            else:
                if options['shadow_mask']:
                    gscript.run_command("g.rename",
                        vector=(tmp["shadow_temp_mask"],shadow_mask))
                if options['shadow_raster']:
                    gscript.run_command('v.to.rast', input=shadow_mask,
                        output=shadow_raster, use='val')
                gscript.warning(_('The removing misclassification procedure from shadow mask was not performed since no cloud have been detected'))
    else:
        if shadow_mask != '':
            gscript.warning(_('No shadow mask will be computed'))

def cleanup():
    if flags["r"]:
        gscript.del_temp_region()
        gscript.message(_('--- The computational region has been reset to the previous one---'))
    if flags["t"]:
        gscript.message(_('--- No temporary files have been deleted ---'))
    else:
        for key, value in tmp.items():
            if gscript.find_file(value,
                element = 'vector',
                mapset = mapset)['file']:
                gscript.run_command("g.remove",
                    flags="f",
                    type='vector',
                    name=",".join([tmp[m] for m in tmp.keys()]),
                    quiet=True)
            if gscript.find_file(value,
                element = 'cell',
                mapset = mapset)['file']:
                gscript.run_command("g.remove",
                    flags="f",
                    type='raster',
                    name=",".join([tmp[m] for m in tmp.keys()]),
                    quiet=True)

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
