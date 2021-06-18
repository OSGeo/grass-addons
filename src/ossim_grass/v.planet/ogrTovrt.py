#!/usr/bin/env python
################################################################################
#
# MODULE:       r.planet.py
#
# AUTHOR(S):    Massimo Di Stefano 2010-02-7 - massimodisasha@yahoo.it
#               (original code : ogr2vrt.py - Frank Warmerdam, warmerdam@pobox.com)
#               
#
# PURPOSE:      Create OGR VRT from source datasource and 
#               OMD associated style-file
#
# COPYRIGHT:    (c) 2010 by Massimo Di Stefano 
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# REQUIRES:     Gdal - python
#                 
#               
#
################################################################################


try:
    from osgeo import osr, ogr, gdal
except ImportError:
    import osr, ogr, gdal

import string
import sys

def GeomType2Name( type ):
    if type == ogr.wkbUnknown:
        return 'wkbUnknown'
    elif type == ogr.wkbPoint:
        return 'wkbPoint'
    elif type == ogr.wkbLineString:
        return 'wkbLineString'
    elif type == ogr.wkbPolygon:
        return 'wkbPolygon'
    elif type == ogr.wkbMultiPoint:
        return 'wkbMultiPoint'
    elif type == ogr.wkbMultiLineString:
        return 'wkbMultiLineString'
    elif type == ogr.wkbMultiPolygon:
        return 'wkbMultiPolygon'
    elif type == ogr.wkbGeometryCollection:
        return 'wkbGeometryCollection'
    elif type == ogr.wkbNone:
        return 'wkbNone'
    elif type == ogr.wkbLinearRing:
        return 'wkbLinearRing'
    else:
        return 'wkbUnknown'

def Esc(x):
    return gdal.EscapeString( x, gdal.CPLES_XML )

def makestile(outfile, brush, pen, size, fill, thickness):
    brush = brush.split(',')
    pen = pen.split(',')
    size = size.split(',')
    outfile = outfile.replace('.vrt','')
    outfile = outfile+'.omd'
    omd = '// vector file rendering options\n'
    omd += 'brush_color: %s %s %s \n' % (brush[0], brush[1], brush[2])
    omd += 'pen_color: %s %s %s \n' % (pen[0], pen[1], pen[2])
    omd += 'point_width_height: %s %s \n' % (size[0], size[1])
    omd += 'fill_flag: %s \n' % (fill)
    omd += 'thickness: %s \n' % (thickness)
    open(outfile,'w').write(omd)

def ogrvrt(infile,outfile):
    layer_list = []
    relative = "0"
    schema=0
    src_ds = ogr.Open( infile, update = 0 )
    if len(layer_list) == 0:
        for layer in src_ds:
            layer_list.append( layer.GetLayerDefn().GetName() )
    vrt = '<OGRVRTDataSource>\n'
    for name in layer_list:
        layer = src_ds.GetLayerByName(name)
        layerdef = layer.GetLayerDefn()
        vrt += '  <OGRVRTLayer name="%s">\n' % Esc(name)
        vrt += '    <SrcDataSource relativeToVRT="%s" shared="%d">%s</SrcDataSource>\n' \
        % (relative,not schema,Esc(infile))
        if schema:
            vrt += '    <SrcLayer>@dummy@</SrcLayer>\n' 
        else:
            vrt += '    <SrcLayer>%s</SrcLayer>\n' % Esc(name)
        vrt += '    <GeometryType>%s</GeometryType>\n' \
        % GeomType2Name(layerdef.GetGeomType())
        srs = layer.GetSpatialRef()
        if srs is not None:
            vrt += '    <LayerSRS>%s</LayerSRS>\n' \
            % (Esc(srs.ExportToWkt()))
        # Process all the fields.
        for fld_index in range(layerdef.GetFieldCount()):
            src_fd = layerdef.GetFieldDefn( fld_index )
            if src_fd.GetType() == ogr.OFTInteger:
                type = 'Integer'
            elif src_fd.GetType() == ogr.OFTString:
                type = 'String'
            elif src_fd.GetType() == ogr.OFTReal:
                type = 'Real'
            elif src_fd.GetType() == ogr.OFTStringList:
                type = 'StringList'
            elif src_fd.GetType() == ogr.OFTIntegerList:
                type = 'IntegerList'
            elif src_fd.GetType() == ogr.OFTRealList:
                type = 'RealList'
            elif src_fd.GetType() == ogr.OFTBinary:
                type = 'Binary'
            elif src_fd.GetType() == ogr.OFTDate:
                type = 'Date'
            elif src_fd.GetType() == ogr.OFTTime:
                type = 'Time'
            elif src_fd.GetType() == ogr.OFTDateTime:
                type = 'DateTime'
            else:
                type = 'String'

            vrt += '    <Field name="%s" type="%s"' \
            % (Esc(src_fd.GetName()), type)
            if not schema:
                vrt += ' src="%s"' % Esc(src_fd.GetName())
            if src_fd.GetWidth() > 0:
                vrt += ' width="%d"' % src_fd.GetWidth()
            if src_fd.GetPrecision() > 0:
                vrt += ' precision="%d"' % src_fd.GetPrecision()
            vrt += '/>\n'
        vrt += '  </OGRVRTLayer>\n'
    vrt += '</OGRVRTDataSource>\n' 
    open(outfile,'w').write(vrt)
