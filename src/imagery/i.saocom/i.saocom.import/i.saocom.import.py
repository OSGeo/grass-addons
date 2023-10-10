#!/usr/bin/env python3

############################################################################
#
# MODULE:	i.sa
#
# AUTHOR:   Santiago Seppi
#
# PURPOSE:	Read SAOCOM SLC files into real and imaginary bands
#
# COPYRIGHT: (C) 2002-2023 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#
#############################################################################

# %Module
# % description: Read SAOCOM SLC file into GRASS as real and imaginary bands
# % keyword: imagery
# % keyword: saocom
# % keyword: sar
# % keyword: radar
# % overwrite: yes
# %End
# %option
# % key: data
# % type: string
# % required: yes
# % multiple: no
# % description: Path to data directory (ZIP or folder)
# %end
# %option
# % key: is_zip
# % type: string
# % required: yes
# % multiple: no
# % answer: yes
# % options: yes,no
# % description: Whether the data directory is zipped or not
# %end
# %option
# % key: pols
# % type: string
# % required: yes
# % multiple: yes
# % answer: ['hh','hv','vh','vv']
# % description: Polarizations to process (Default:['hh','hv','vh','vv'])
# %end
# %option
# % key: multilook
# % type: integer
# % required: yes
# % multiple: yes
# % answer: 1,1
# % description: Azimuth and range factors to apply (eg: [4,2]))
# %end
# %option G_OPT_R_OUTPUT
# % key: basename
# % description: Prefix for output raster map
# % required: yes
# %end


import os
import numpy as np
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from zipfile import ZipFile
import rasterio
from rasterio.mask import mask
from rasterio.vrt import WarpedVRT
import geopandas as gpd
import numpy as np
from xml.etree import ElementTree as ET
from osgeo import gdal
from affine import Affine
import pandas as pd


def apply_multilook(dataset, azLooks, rgLooks):
    '''
    Esta función aplica un multilook dado a una imagen de entrada y actualiza la información de los metadatos
    para la imagen de salida.
    
    parámetros:
    dataset: diccionario de datos con las llaves:
        'array': contiene la matriz de datos
        'metadata': contiene los metadatos con el formato dado por la librería rasterio 
    azLooks: número de looks a aplicar en dirección de azimuth
    rgLooks: número de looks a aplicar en dirección de rango
    
    retorna:
    diccionario de datos con la estructura del dataset de entrada pero con el array resultante del 
    multilook y los metadatos actualizados
    '''
    
    import numpy as np
    from rasterio import Affine
    
    array = dataset['array'].copy()
    metadata = dataset['metadata'].copy()
    
    array = array[0]
    
    cols = metadata['width']
    rows = metadata['height']
    new_rows = rows//azLooks
    new_cols = cols//rgLooks
    new_shape = (new_rows, azLooks, new_cols, rgLooks)
    
    if rows%azLooks!=0 or cols%rgLooks!=0:
        array = array[:new_rows*azLooks,:new_cols*rgLooks]
    
    multilooked = array.reshape(new_shape).mean(-1).mean(1)
    metadata['width'] = new_cols
    metadata['height'] = new_rows
    geoTs = metadata['transform']
    metadata['transform'] = Affine(geoTs[0]*rgLooks, geoTs[1], geoTs[2], geoTs[3], geoTs[4]*azLooks, geoTs[5])
    
    return {'array': np.expand_dims(multilooked, axis=0), 'metadata': metadata}



def read_bands_zip(data, pols):
	with ZipFile(data,'r') as zfile:
		file_list = [img for img in zfile.namelist() if img.startswith('Data/') and not img.endswith('.xml')]
	bands = {}
	gcps = tuple()
	dataset_pols = []
	for l in file_list:
		pol = l.split('-')[6]
		dataset_pols.append(pol)
		if pol in pols:
			bands[pol] = {}
			filename = f'/vsizip/{data}/{l}'
			with rasterio.open(filename) as banda:
				bands[pol]['array'] = banda.read()
				bands[pol]['metadata'] = banda.meta
				gcps = banda.get_gcps()
	return bands,gcps,dataset_pols
	
def read_bands_folder(data, pols):
	file_list = [img for img in os.listdir(os.path.join(data,'Data')) if not img.endswith('.xml')]
	bands = {}
	gcps = tuple()
	dataset_pols = []
	for l in file_list:
		pol = l.split('-')[6]
		dataset_pols.append(pol)
		if pol in pols:
			bands[pol] = {}
			filename = os.path.join(data,'Data',l)
			with rasterio.open(filename) as banda:
				bands[pol]['array'] = banda.read()
				bands[pol]['metadata'] = banda.meta
				gcps = banda.get_gcps()
	return bands,gcps,dataset_pols


def save_bands(bands,basename):
	for band in bands:
		#Change the band metadata:
		#Data type must be changed from complex to float
		bands[band]['metadata']['dtype'] = np.float32
		#The Y-resolution must be set to negative, otherwise GRASS will interpret the map is flipped
		geoTs = bands[band]['metadata']['transform']
		bands[band]['metadata']['transform'] = Affine(geoTs[0], geoTs[1], geoTs[2], geoTs[3], -geoTs[4], geoTs[5])
		outputfn_r = f'{basename}_{band}_real.tif'
		outputfn_i = f'{basename}_{band}_imag.tif'
		with rasterio.open(outputfn_r, 'w', **bands[band]['metadata']) as dst:
			dst.write(bands[band]['array'].real)
		with rasterio.open(outputfn_i, 'w', **bands[band]['metadata']) as dst:
			dst.write(bands[band]['array'].imag)
		
def main():
	#xemt = options["xemt"]
	data = options["data"]
	zip_v = options["is_zip"]
	basename = options["basename"]
	pols = options['pols']
	multilook = options['multilook']
    
	if zip_v == 'yes':
		bands,gcps,dataset_pols = read_bands_zip(data, pols)
	else:
		bands,gcps,dataset_pols = read_bands_folder(data, pols)
	
	if len(bands) == 0 or len(gcps) == 0:
		grass.fatal(_(f'None of the specified polarizations were found in the dataset \n Please try one of the folowing: {dataset_pols}'))
		#pass
		
	else:
		#Create a dataframe containing GCP information
		cols = gcps[0][0].asdict().keys()
		df = pd.DataFrame(columns = cols)
		for i,gcp in enumerate(gcps[0]):
			df1 = pd.DataFrame(gcp.asdict(), index = [i])
			df = pd.concat((df,df1))
		
		
		if multilook[0] != 1 or multilook[2] != 1:
			# ~ print(f'Appying ML factor: {multilook}')
			grass.message(_(f'Appying ML factor: {multilook}'))
			for band in bands:
				dim = bands[band]['array'].shape
				# ~ print('Original shape ', bands[band]['array'].shape)
				grass.message(_(f'Original shape {dim}'))
				ml_dic =  apply_multilook(bands[band], int(multilook[0]), int(multilook[2]))
				bands[band]['array'] = ml_dic['array']
				bands[band]['metadata'] = ml_dic['metadata']
				dim = bands[band]['array'].shape
				# ~ print('Shape after ML', bands[band]['array'].shape)
				grass.message(_(f'Shape after ML {dim}'))
			# Update GCP information	
			# ~ print('Updating GCP information for later geocoding')
			grass.message(_('Updating GCP information for later geocoding'))
			df['row'] /= int(multilook[0])
			df['col'] /= int(multilook[2])
		
		# ~ print('Saving real and imaginary bands to intermediate GeoTiff outputs')	
		grass.message(_('Saving real and imaginary bands to intermediate GeoTiff outputs'))
		save_bands(bands,basename)
		
		# ~ print('Reading real and imaginary bands into GRASS GIS, and cleaning intermediate files')
		grass.message(_('Reading real and imaginary bands into GRASS GIS, and cleaning intermediate files'))
		for band in bands:
			input_r = f'{basename}_{band}_real.tif'
			input_i = f'{basename}_{band}_imag.tif'
			grass.run_command("r.import", input=input_r, output = input_r.split('.tif')[0])
			grass.run_command("r.import", input=input_i, output = input_i.split('.tif')[0])
			os.remove(input_r)
			os.remove(input_i)
		
		# ~ print('Saving GCP information as support file')
		grass.message(_('Saving GCP information as support file'))
		env = grass.gisenv()
		gcp_base_folder = os.path.join(env["GISDBASE"], env["LOCATION_NAME"], env["MAPSET"], "cell_misc",basename)
		if not os.path.isdir(gcp_base_folder):
			os.makedirs(gcp_base_folder)
		df.to_csv(os.path.join(gcp_base_folder,'GCPS.csv'))
		

if __name__ == "__main__":
	options, flags = grass.parser()
	main()
