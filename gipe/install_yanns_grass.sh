#!/bin/bash

# This is a try to install all these modules through a GRASS CVS tree
# It will copy, untar and make/make install as required.


#CHANGE THIS TO YOUR CVS TREE DIRECTORY 
GRASSCVSDIR=/home/yann/tmp/grass

GIPEDIR=$('pwd')

#INSTALL GUI MODIFICATIONS
cp -f $GIPEDIR/gui_Makefile $GRASSCVSDIR/gui/Makefile 
cp -f $GIPEDIR/gmmenu.tcl $GRASSCVSDIR/gui/tcltk/gis.m/gmmenu.tcl
cd $GRASSCVSDIR/gui/
make 

#INSTALL MODULES
cd $GIPEDIR/
for directory in r.*
do
	cp -rf $GIPEDIR/$directory $GRASSCVSDIR/raster/
done
cp -f $GIPEDIR/Makefile $GRASSCVSDIR/raster/ 
cd $GRASSCVSDIR/raster/
make

for directory in i.*
do
	cp -rf $GIPEDIR/$directory $GRASSCVSDIR/imagery/ 
done
cp -f $GIPEDIR/imagery_Makefile $GRASSCVSDIR/imagery/Makefile 
cd $GRASSCVSDIR/imagery/
make

cd $GRASSCVSDIR
make install

