# Example script to process ETPOT directly from tif.gz downloaded files
# of Landsat 7 ETM+ from GLCF website for example 
# LGPL, Yann Chemin ychemin_AT_gmail.com
#!/bin/bash

#rename to your wish
new_location=landsat

# Decompress files
for file in *gz
do
	gzip -d $file
done

# Import files in GRASS GIS
# Warning: This is setting the processing resolution at 30x30m!
for file in *nn10.tif
do
	r.in.gdal input=$file output=$file location=landsat
done

g.mapset location=landsat mapset=PERMANENT

# Continue to import files in GRASS GIS
for file in *nn20.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn30.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn40.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn50.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn61.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn62.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn70.tif
do
	r.in.gdal input=$file output=$file
done
for file in *nn80.tif
do
	r.in.gdal input=$file output=$file
done


#Process
i.dn2potrad.l7 metfile=p126r050_7x20001231.met tsw=0.7 roh_w=1010.0 tempk_band=5 output=etpot --overwrite 

echo "Job Done"
