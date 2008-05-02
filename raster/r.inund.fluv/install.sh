#!/bin/sh

echo "You must be root or have the permissions for installing a grass-script"
echo " "
echo "please, write your GRASS directory"
echo "       e.g. /usr/grass-xxxx     (look also in /usr/local or /usr/lib)"
read grass_directory

if [ -e $grass_directory/fortran_code ]; then  
    directory=$grass_directory'/fortran_code'
else
    echo "The fortran code will be put in $grass_directory/fortran_code" 
    directory=$grass_directory'/fortran_code'
    mkdir $directory
fi

initial_directory=`pwd` 
 
cp find_main_channel.f90 $directory
cp clean_inundation.f90 $directory
cp 2d_path.f90 $directory
cp correction_from_path.f90 $directory

cd $directory


# if you have gnu fortran compiler (gcc-gfortran.i386), use the following rows: 

gfortran -O1 -o find_main_channel.exe find_main_channel.f90 
gfortran -O1 -o clean_inundation.exe clean_inundation.f90
gfortran -O1 -o 2d_path.exe 2d_path.f90
gfortran -O1 -o correction_from_path.exe correction_from_path.f90

# if you have a intel fortran compiler, use the following rows  
#ifort -O3 -xW -o find_main_channel.exe find_main_channel.f90 
#ifort -O3 -xW -o clean_inundation.exe clean_inundation.f90
#ifort -O3 -xW -o 2d_path.exe 2d_path.f90
#ifort -O3 -xW -o correction_from_path.exe correction_from_path.f90

rm find_main_channel.f90
rm clean_inundation.f90
rm 2d_path.f90
rm correction_from_path.f90

cd $initial_directory

cp r.inund.fluv $grass_directory/scripts
chmod 777 $grass_directory/scripts/r.inund.fluv

if [ -e $grass_directory/docs ]; then
	cp r.inund.fluv.html $grass_directory/docs/html/
   else
	mkdir $grass_directory/docs
	mkdir $grass_directory/docs/html
	cp r.inund.fluv.html $grass_directory/docs/html/
fi

echo "OK now you've successfull installed "

exit


