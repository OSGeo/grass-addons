#!/usr/bin/env python 
# coding=utf-8
#
############################################################################
#
# MODULE:    i.sentinel.mask
# AUTHOR(S):    Roberta Fagandini, Moritz Lennert, Roberto Marzocchi
# PURPOSE:    Creates clouds and shadows masks for Sentinel-2 images
#
# COPYRIGHT:    (C) 2018 by the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
#
#############################################################################

#%Module
#% description: Creates clouds and shadows masks for Sentinel-2 images
#% keywords: imagery
#% keywords: sentinel 
#% keywords: cloud detection
#% keywords: shadow
#% keywords: reflectance
#%End
#%option
#% key: input_file
#% type: string
#% gisprompt: old,file,file
#% description: name of the .txt file with listed input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: blue
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: green
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: red
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: nir
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: nir8a
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: swir11
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option
#% key: swir12
#% type: string
#% gisprompt: old,cell,raster
#% description: input bands
#% required : no
#% multiple: no
#% guisection: Required
#%end
#%option 
#% key: cloud_mask
#% type: string
#% gisprompt: new,vector,vector
#% description: name of output vector cloud mask
#% required : yes
#% guisection: Output
#%end
#%option 
#% key: shadow_mask
#% type: string
#% gisprompt: new,vector,vector
#% description: name of output vector shadow mask
#% required : no
#% guisection: Output
#%end
#%option
#% key: cloud_threshold
#% type: integer
#% description: threshold for cleaning small areas from cloud mask
#% required : yes
#% answer: 50000
#% guisection: Output
#%end
#%option
#% key: shadow_threshold
#% type: integer
#% description: threshold for cleaning small areas from shadow mask
#% required : yes
#% answer: 10000
#% guisection: Output
#%end
#%option
#% key: mtd_file
#% type: string
#% gisprompt: old,file,file
#% description: name of the image metadata file (MTD_TL.xml)
#% required : no
#% multiple: no
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

import grass.script as gscript
import math
import os
import sys
import shutil
import re
import glob
import numpy
import time
import atexit
import xml.etree.ElementTree as et


def main ():


    #import bands atmospherically corrected using arcsi (scale factor 1000 instead of 10000)
    #############################################
    # INPUT
    #############################################
    #temporary map names
    global tmp, t, mapset
    tmp = {}
    mapset = gscript.gisenv()['MAPSET']
    mapset2 = '@{}'.format(mapset)
    processid = os.getpid()
    processid = str(processid)
    tmp["cloud_def"] = "cloud_def"+ processid
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
    
    #check temporary map names are not existing maps
    for key, value in tmp.items():
        if gscript.find_file(value,
            element = 'vector',
            mapset = mapset)['file']:
                gscript.fatal(("Temporary vector map <{}> already exists.").format(value))
        if gscript.find_file(value,
            element = 'cell',
            mapset = mapset)['file']:
                gscript.fatal(("Temporary raster map <{}> already exists.").format(value))

    #input file
    mtd_file = options['mtd_file']
    bands = {} 
    if options['input_file']=='':
        bands['blue'] = options['blue']
        bands['green'] = options['green']
        bands['red'] = options['red']
        bands['nir'] = options['nir']
        bands['nir8a'] = options['nir8a']
        bands['swir11'] = options['swir11']
        bands['swir12'] = options['swir12']
    else:
        input_file = options['input_file']
        for line in file(input_file):
            a = line.split('=')
            if len(a) != 2 or a[0] not in ['blue', 'green', 'red', 'nir', 'nir8a', 'swir11', 'swir12' ]:
                gscript.fatal("Syntax error in the txt file. See the manual for further information about the right syntax.")
            a[1] = a[1].strip()
            bands[a[0]] = a[1]
    d = 'double'
    f_bands = {}
    scale_fac = options['scale_fac']
    cloud_threshold = options['cloud_threshold']
    shadow_threshold = options['shadow_threshold']
    raster_max = {}
    cloud_mask = options['cloud_mask']
    shadow_mask = options['shadow_mask']

    if bands['blue'] == '' or bands['green'] == '' or bands['red'] == '' or bands['nir'] == '' or bands['nir8a'] == '' or bands['swir11'] == '' or bands['swir12'] == '':
        gscript.fatal(("All input bands (blue, green, red, nir, nir8a, swir11, swir12) are required"))

    for key, value in bands.items():
        if not gscript.find_file(value,
            element = 'cell',
            mapset = mapset)['file']:
                gscript.fatal(("Raster map <{}> not found.").format(value))

    if not flags["c"]:
        if options['mtd_file']== '':
            gscript.fatal("Metadata file is required for shadow mask computation. Please specified it")
        if options['shadow_mask']=='':
            gscript.fatal("Output name is required for shadow mask. Please specified it")

    if flags["r"]:
        gscript.use_temp_region()
        gscript.run_command('g.region',
            rast=bands.values(),
            flags='a')
        gscript.message(_("--- The computational region has been temporarily set to image max extent ---"))
    else:
        gscript.warning(_("All subsequent operations will be limited to the current computational region"))

    if flags["s"]:
        gscript.message(_('--- Start rescaling bands ---'))
        for key, b in bands.items():
            gscript.message(_(b))
            b = gscript.find_file(b, element = 'cell')['name']
            gscript.mapcalc('{r} = 1.0 * ({b})/{scale_fac}'.format(
                r=("{}_{}".format(b, d)),
                b=b,
                scale_fac=scale_fac))
            f_bands[key] = "{}_{}".format(b, d)
        gscript.message(_(f_bands.values()))
        gscript.message(_('--- All bands have been rescaled ---'))
    else:
        gscript.warning(_('Any rescale factor has been applied'))
        for key, b in bands.items():
            if gscript.raster_info(b)['datatype'] != "DCELL" and gscript.raster_info(b)['datatype'] != "FCELL":
                gscript.fatal("Raster maps must be DCELL o FCELL")
            else:
                f_bands = bands

    gscript.message(_('--- Start computing maximum values of bands ---'))
    for key, fb in f_bands.items():
        gscript.message(_(fb))
        stats = gscript.parse_command('r.univar', flags='g', map=fb)
        raster_max[key] = (float(stats['max']))
    gscript.message(_('--- Computed maximum value: {} ---'.format(raster_max.values())))
    gscript.message(_('--- Statistics have been computed! ---'))

    #### start of Clouds detection  (some rules from litterature)###
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
        tmp["cloud_def"],
        cloud_rules)
    gscript.mapcalc(expr_c, overwrite=True)
    gscript.message(_('--- Converting raster cloud mask into vector map ---'))
    gscript.run_command('r.to.vect',
        input=tmp["cloud_def"],
        output=tmp["cloud_v"],
        type='area',
        flags='s')
    gscript.message(_('--- Cleaning geometries ---'))
    gscript.run_command('v.clean',
        input=tmp["cloud_v"],
        output=cloud_mask,
        tool='rmarea',
        threshold=cloud_threshold)
    gscript.message(_('--- Finish cloud detection procedure ---'))
    ### end of Clouds detection ####

    if not flags["c"]:
        ### start of shadows detection ###
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
        gscript.message(_('--- Cleaning geometries ---'))
        gscript.run_command('v.clean',
            input=tmp["shadow_temp_v"],
            output=tmp["shadow_temp_mask"],
            tool='rmarea',
            threshold=shadow_threshold)
        gscript.message(_('--- Finish Shadows detection procedure ---'))
        ### end of shadows detection ###

        #####################################################################
        # START shadows cleaning Procedure (remove shadows misclassification)
        #####################################################################
        ### start shadow mask preparation ###

        gscript.message(_('--- Start removing misclassification from the shadow mask ---'))
        gscript.message(_('--- Data preparation... ---'))
        gscript.run_command('v.centroids',
            input=tmp["shadow_temp_mask"],
            output=tmp["centroid"],
            quiet=True)
        gscript.run_command('v.db.droptable',
            map=tmp["centroid"],
            flags='f')
        gscript.run_command('v.db.addtable',
            map=tmp["centroid"],
            columns='value')
        gscript.run_command('v.db.update',
            map=tmp["centroid"],
            layer=1,
            column='value',
            value=1)
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
            flags='f')
        gscript.run_command('v.db.addtable',
            map=tmp["addcat"],
            columns='value')

        ### end shadow mask preparation ###
        ### start cloud mask preparation ###

        gscript.run_command('v.db.droptable',
            map=cloud_mask,
            flags='f')
        gscript.run_command('v.db.addtable',
            map=cloud_mask,
            columns='value')

        ### end cloud mask preparation ###
        ### shift cloud mask using dE e dN ###
        ### start reading mean sun zenith and azimuth from xml file to compute dE and dN automatically ###
        gscript.message(_('--- Reading mean sun zenith and azimuth from MTD_TL.xml file to compute clouds shift ---'))
        xml_tree = et.parse(mtd_file)
        root = xml_tree.getroot()
        ZA = []

        for elem in root[1]:
            for subelem in elem[1]:
                ZA.append (subelem.text)
        z = float(ZA[0])
        a = float(ZA[1])
        gscript.message(_('--- the mean sun Zenith is: {:.3f} deg ---'.format(z)))
        gscript.message(_('--- the mean sun Azimuth is: {:.3f} deg ---'.format(a)))

        ### stop reading mean sun zenith and azimuth from xml file to compute dE and dN automatically ###
        ### start computing the east and north shift for clouds and the overlapping area between clouds and shadows at steps of 100m ###
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
                quiet=True)
            gscript.run_command('v.overlay',
                ainput=tmp["addcat"],
                binput=tmp["cl_shift"],
                operator='and',
                output=tmp["overlay"],
                overwrite=True,
                quiet=True)
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

        # find the maximum overlapping area between clouds and shadows#
        index_maxAA = numpy.argmax(AA)

        # clouds are shifted using the clouds height corresponding to the maximum overlapping area then are intersect with shadows#
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

        gscript.message(_('--- the estimated clouds height is: {} m ---'.format(HH[index_maxAA])))
        gscript.message(_('--- the estimated east shift is: {:.2f} m ---'.format(dE[index_maxAA])))
        gscript.message(_('--- the estimated north shift is: {:.2f} m ---'.format(dN[index_maxAA])))
    else:
        gscript.warning(_('No shadow mask will be computed'))

def cleanup():
    if flags["r"]:
        gscript.del_temp_region()
    gscript.message(_('--- The computational region has been reset to the previous one---'))
    if flags["t"]:
        gscript.message(_('--- No temporary files have been deleted ---'))
    else:
        for key, value in tmp.items():
            if gscript.find_file(value, element = 'vector', mapset = mapset)['file']:
                gscript.run_command("g.remove",
                    flags="f",
                    type='vector',
                    name=",".join([tmp[m] for m in tmp.keys()]),
                    quiet=True)
            if gscript.find_file(value, element = 'cell', mapset = mapset)['file']:
                gscript.run_command("g.remove",
                    flags="f",
                    type='raster',
                    name=",".join([tmp[m] for m in tmp.keys()]),
                    quiet=True)
            
if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()

