## DESCRIPTION

*i.wi* calculates water indices based on biophysical parameters.

- AWEI: Automated Water Extraction Index (2 versions: no shadow or
    shadow
- LSWI: Land Surface Water Index
- NDWI: Normalized Difference Water Index (2 versions: McFeeters or
    Xu)
- TCW: Tasseled Cap Water
- WI: Water Index

## NOTES

Requirements (as of Landsat 5TM bands)

- awei\_noshadow needs greenchan, nirchan, chan5chan
- awei\_shadow needs bluechan, greenchan, nirchan, chan5chan,
    chan7chan
- ls\_wi needs nirchan, chan7chan
- ndwi\_mcfeeters needs greenchan, nirchan
- ndwi\_xu needs greenchan, chan5chan
- tcw needs bluechan, greenchan, redchan, nirchan, chan5chan,
    chan7chan
- wi needs greenchan, redchan, nirchan, chan5chan, chan7chan

## TODO

Find other water indices and add them.

## REFERENCES

AWEI: Automated Water Extraction Index  
Feyisa, G.L., Meilby, H., Fensholt, R., Proud, S.R. (2014). Automated
Water Extraction Index: A new technique for surface water mapping using
Landsat imagery. Remote Sensing of Environment, 140, 23-35.
https://doi.org/10.1016/j.rse.2013.08.029.

LSWI: Land Surface Water Index  
a kind of Normalized Difference Water Index Xiao X., Boles S., Frolking
S., Salas W., Moore B., Li C., et al. (2002) Landscape-scale
characterization of cropland in China using vegetation and Landsat TM
images. International Journal of Remote Sensing, 23:3579-3594.

NDWI McFeeters  
McFeeters, S.K. (1996). The use of the Normalized Difference Water Index
(NDWI) in the delineation of open water features. International Journal
of Remote Sensing, 17, 1425-1432.
https://doi.org/10.1080/01431169608948714.

NDWI Xu  
Xu, H. (2006). Modification of normalised difference water index (NDWI)
to enhance open water features in remotely sensed imagery. International
Journal of Remote Sensing, 27, 3025-3033.
https://doi.org/10.1080/01431160600589179.

TCW  
Crist, E.P. (1985). A TM tasseled cap equivalent transformation for
reflectance factor data. Remote Sensing of Environment, 17, 301-306.

WI  
Fisher, A., Flood, N., Danaher, T. (2016). Comparing Landsat water index
methods for automated water classification in eastern Australia. Remote
Sensing of Environment, 175, 167-182. ISSN 0034-4257,
https://doi.org/10.1016/j.rse.2015.12.055.

## SEE ALSO

*[i.vi](https://grass.osgeo.org/grass-stable/manuals/i.vi.html)*

## AUTHOR

Yann Chemin
