This is a script written in bash shell language, configured for grass 6.3 release.
(Users of previous releases can use the r.inund.fluv_62 file as described below) 

r.inund.fluv use the following fortran codes:
- find_main_channel.f90
- clean_inundation.f90
- 2d_path.f90
- correction_from_path.f90 

***************************REQUEST **************************************
The installation of this code requests a fortran compiler installed on your computer. 

For any other informations contact the autors of the script 
(see description.html)
*************************************************************************
**************** Users of GRASS 6.4 or 6.3 ******************************
1) open the Makefile with a text editor
2) insert the path to the source grass directory in MODULE_TOPDIR = ../..  
(for example: MODULE_TOPDIR = /root/grass-6.3.0_source)
3) run the following command to compile a single GRASS command (as sudo user)
INST_NOW=y make

**************** Users of GRASS 6.2 **************************************
Rename the grass script as follows: 
 r.inund.fluv --> r.inund.fluv_63
 r.inund.fluv_62 --> r.inund.fluv 
Hence follows the procedure described for users of GRASS 6.3

