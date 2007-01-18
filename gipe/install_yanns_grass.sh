#!/bin/bash

# This is a try to install all these modules through a GRASS CVS tree
# It will copy, untar and make/make install as required.


#CHANGE THIS TO YOUR CVS TREE DIRECTORY 
GRASSCVSDIR=/home/yann/tmp/grass

#INSTALL GUI MODIFICATIONS
cp gui_Makefile $GRASSCVSDIR/gui/Makefile -f
cp gmmenu.tcl $GRASSCVSDIR/gui/tcltk/gis.m/gmmenu.tcl
cd $GRASSCVSDIR/gui/
make 

#INSTALL MODULES
cp r.*.tar.gz $GRASSCVSDIR/raster/ -f
cp Makefile $GRASSCVSDIR/raster/ -f
cd $GRASSCVSDIR/raster/
for file in r.*.tar.gz
	do
		tar xvzf $file
	done
make
cp i.*.tar.gz $GRASSCVSDIR/imagery/ -f
cp Makefile $GRASSCVSDIR/imagery/ -f
cd $GRASSCVSDIR/imagery/
for file in i.*.tar.gz
	do
		tar xvzf $file
	done
make
cd $GRASSCVSDIR
make install

