This is a script written in bash shell language, configured for grass 6.3 release.
Users of previous releases can use the r.inund.fluv_62 script (see the notes below) 

r.inund.fluv use the following fortran codes:
- find_main_channel.f90
- clean_inundation.f90
- 2d_path.f90
- correction_from_path.f90 

***************************REQUEST ********************************
The installation of this code requests a fortran compiler installed on your computer. 

For any other informations contact the autors of the script 
(see description.html)
******************************************************************
**************** Users of GRASS 6.3 ******************************
1) open the Makefile with a text editor
2) change the relative path MODULE_TOPDIR = ../.. with the GISBASE directory
3) make
4) go in the source grass directory 
5) make install 

**************** Users of GRASS 6.3 ******************************
Rename the grass scripts:
 r.inund.fluv --> r.inund.fluv_63
 r.inund.fluv_62 --> r.inund.fluv 
