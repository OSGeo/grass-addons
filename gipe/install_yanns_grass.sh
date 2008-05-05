#!/bin/bash

# This is a try to install all these modules through a GRASS CVS tree
# It will copy, untar and make/make install as required.


#CHANGE THIS TO YOUR CVS TREE DIRECTORY 
GRASSCVSDIR=/home/yann/tmp/grass
ADDONSVNDIR=/home/yann/coding/grass-addons

# This Assumes you start in GIPE directory
GIPEDIR=$ADDONSVNDIR/gipe
HFDIR=$ADDONSVNDIR/HydroFOSS
RSTDIR=$ADDONSVNDIR/raster

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
cp -rf $GIPEDIR/PM_Makefile $GRASSCVSDIR/raster/r.evapo.PM/Makefile

cd $RSTDIR/
for directory in r.inund.fluv*
do
	cp -rf $RSTDIR/$directory $GRASSCVSDIR/raster/
done

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

cd $ADDONSVNDIR/imagery/
for directory in i.*
do
	cp -rf $ADDONSVNDIR/imagery/$directory $GRASSCVSDIR/imagery/ 
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

#Install GUI stuff
cp -rf $GIPEDIR/gmmenu.tcl $GRASSCVSDIR/gui/tcltk/gis.m/ 
cp -rf $GIPEDIR/menudata.py $GRASSCVSDIR/gui/wxpython/gui_modules/ 
cd $GRASSCVSDIR/gui
make

cd $GRASSCVSDIR
make install

