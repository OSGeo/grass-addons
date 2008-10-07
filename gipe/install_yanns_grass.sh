#!/bin/bash

# This is a try to install all these modules through a GRASS SVN tree
# It will copy, untar and make/make install as required.


#CHANGE THIS TO YOUR SVN TREE DIRECTORY 
GRASSSVNDIR=/home/yann/tmp/grass
ADDONSVNDIR=/home/yann/coding/grass-addons

# This Assumes you start in GIPE directory
GIPEDIR=$ADDONSVNDIR/gipe
#HFDIR=$ADDONSVNDIR/HydroFOSS
RSTDIR=$ADDONSVNDIR/raster

#INSTALL MODULES
#START RASTER STUFF
cd $GIPEDIR/
for directory in r.*
do
	cp -rf $GIPEDIR/$directory $GRASSSVNDIR/raster/
done

#cd $HFDIR/
#for directory in r.*
#do
#	cp -rf $HFDIR/$directory $GRASSSVNDIR/raster/
#done
#cp -rf $GIPEDIR/Makefile.PM $GRASSSVNDIR/raster/r.evapo.PM/Makefile

#cd $RSTDIR/
#for directory in r.inund.fluv*
#do
#	cp -rf $RSTDIR/$directory $GRASSSVNDIR/raster/
#done

cp -f $GIPEDIR/Makefile.raster $GRASSSVNDIR/raster/Makefile.gipe 
cd $GRASSSVNDIR/raster/
make -f Makefile.gipe
#END RASTER STUFF

#START IMAGERY STUFF
cd $GIPEDIR/
for directory in i.*
do
	cp -rf $GIPEDIR/$directory $GRASSSVNDIR/imagery/ 
done

cd $ADDONSVNDIR/
for directory in i.*
do
	cp -rf $ADDONSVNDIR/$directory $GRASSSVNDIR/imagery/ 
done

cd $ADDONSVNDIR/imagery/
for directory in i.*
do
	cp -rf $ADDONSVNDIR/imagery/$directory $GRASSSVNDIR/imagery/ 
done

cp -f $GIPEDIR/Makefile.imagery $GRASSSVNDIR/imagery/Makefile.gipe
cd $GRASSSVNDIR/imagery/
make -f Makefile.gipe
#END IMAGERY STUFF

#Install m.gem in /scripts
#cp -rf $GIPEDIR/m.gem $GRASSSVNDIR/scripts/ 
#cp -f $GIPEDIR/Makefile.scripts $GRASSSVNDIR/scripts/Makefile.gipe 
#cd $GRASSSVNDIR/scripts/
#make -f Makefile.scripts

#Install GUI stuff
cp -rf $GIPEDIR/gmmenu.tcl $GRASSSVNDIR/gui/tcltk/gis.m/ 
cp -rf $GIPEDIR/menudata.py $GRASSSVNDIR/gui/wxpython/gui_modules/ 
cd $GRASSSVNDIR/gui
make

cd $GRASSSVNDIR
make install

