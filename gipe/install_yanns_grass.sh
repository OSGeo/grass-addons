#!/bin/bash

# This is a try to install all these modules through a GRASS CVS tree
# It will copy, untar and make/make install as required.


#CHANGE THIS TO YOUR CVS TREE DIRECTORY 
GRASSCVSDIR=/home/yann/tmp/grass
ADDONSVNDIR=/home/yann/tmp/grass-addons

# This Assumes you start in GIPE directory
GIPEDIR=$ADDONSVNDIR/gipe
HFDIR=$ADDONSVNDIR/HydroFOSS

#INSTALL MODULES
#START RASTER STUFF
cd $GIPEDIR/
for directory in r.*
do
	cp -rf $GIPEDIR/$directory $GRASSCVSDIR/raster/
done

cd $HFDIR/
for directory in r.*
do
	cp -rf $HFDIR/$directory $GRASSCVSDIR/raster/
done
cp -rf $HFDIR/PM_Makefile $GRASSCVSDIR/raster/r.evapo.PM/Makefile

cp -f $GIPEDIR/Makefile $GRASSCVSDIR/raster/ 
cd $GRASSCVSDIR/raster/
make
#END RASTER STUFF

#START IMAGERY STUFF
cd $GIPEDIR/
for directory in i.*
do
	cp -rf $GIPEDIR/$directory $GRASSCVSDIR/imagery/ 
done

cd $ADDONSVNDIR/
for directory in i.*
do
	cp -rf $ADDONSVNDIR/$directory $GRASSCVSDIR/imagery/ 
done

cd $ADDONSVNDIR/i.pr/
for directory in i.*
do
	cp -rf $ADDONSVNDIR/i.pr/$directory $GRASSCVSDIR/imagery/ 
done

cp -f $GIPEDIR/imagery_Makefile $GRASSCVSDIR/imagery/Makefile 
cd $GRASSCVSDIR/imagery/
make
#END IMAGERY STUFF

#Install m.gem in /scripts
cp -rf $GIPEDIR/m.gem $GRASSCVSDIR/scripts/ 
cp -f $GIPEDIR/scripts_Makefile $GRASSCVSDIR/scripts/Makefile 
cd $GRASSCVSDIR/scripts/
make

cd $GRASSCVSDIR
make install

