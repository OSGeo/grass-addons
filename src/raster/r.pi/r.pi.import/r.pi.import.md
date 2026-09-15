## DESCRIPTION

Import and generation of patch raster data based on individual patch
based raster data.

## NOTES

...

## EXAMPLE

An example for the North Carolina sample dataset: In order to run
*r.pi.import* we need an exported patch index raster:

```sh
r.pi.index input=landclass96 output=landclass96_forestclass5_area keyval=5 method=area
```

export this resulting map:

```sh
r.pi.export input=landclass96_forestclass5_area output=patch_area_out values=patch_area_values id_raster=forestclass5_ID stats=average,variance,min
```

modify it with R or just import the file again and assign the percentage
coverage to each fragment. You need the *patch\_area\_values* file and
the previously used input file *forestclass96* raster (important: the
same patch coverage is mandatory otherwise patch ID in the text file and
raster are not congruent\!):

```sh
r.pi.import input=patch_area_values raster=landclass96 output=imported_values keyval=5 id_col=1 val_col=2
```

if you want to export the patch values to R and do e.g. a linear
regression of two patch values and import them again in GRASS, do:  
apply r.pi.export with two indices (A and B), in `R`, do:

```R
resid.AB <- resid(lm(A[,3]~B[,3])) #write residuals of a linear regression
df.resid.AB <- data.frame(A[,1],resid.AB) #merge patch IDs and resid into same data frame
write.table(df.resid.AB,"resid.for.GRASS",row.names=F,col.names=F)
```

exit R and run in GRASS:

```sh
r.pi.import input=resid.for.GRASS raster=landclass96 output=resid.AB keyval=5 id_col=1 val_col=2
```

## SEE ALSO

*[r.pi.export](r.pi.export.md), [r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
