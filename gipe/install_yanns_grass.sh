#!/bin/bash

# This is a try to install all these modules through a GRASS CVS tree
# It will copy, untar and make/make install as required.


#CHANGE THIS TO YOUR CVS TREE DIRECTORY 
GRASSCVSDIR=/home/yann/tmp/grass

# This Assumes you start in GIPE directory
GIPEDIR=$('pwd')
cd ..
SVNDIR=$('pwd')
cd HydroFOSS
HFDIR=$('pwd')
cd ../GUI 
WXDIR=$('pwd')

#INSTALL GUI MODIFICATIONS
cp -f $GIPEDIR/gui_Makefile $GRASSCVSDIR/gui/Makefile 
#THIS ONE IS TCLTK
cp -f $GIPEDIR/gmmenu.tcl $GRASSCVSDIR/gui/tcltk/gis.m/gmmenu.tcl
cd $GRASSCVSDIR/gui/
make 
#THIS ONE IS WXGRASS
cp -f $GIPEDIR/menudata.py $WXDIR/gui_modules/menudata.py

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

cd $SVNDIR/
for directory in i.*
do
	cp -rf $GIPEDIR/$directory $GRASSCVSDIR/imagery/ 
done

cd $SVNDIR/
for directory in i.pr/i.*
do
	cp -rf $SVNDIR/i.pr/$directory $GRASSCVSDIR/imagery/ 
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

