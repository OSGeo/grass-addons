This is a script written in bash shell language, configured for grass 6.3 release.
Users of previous releases can use the r.inund.fluv_62 script (see the notes below) 

r.inund.fluv use the following fortran codes:
- find_main_channel.f90
- clean_inundation.f90
- 2d_path.f90
- correction_from_path.f90 

***************************REQUEST ********************************
The installation of this code requests a fortran compiler installed on your computer. 
The installation script (install.sh) is written for gnu fortran compiler with optimization.
(http://www.gnu.org/software/gcc/fortran/)
If you have an other compiler you may change the install script  (install.sh)

e.g.
gfortran -O1 -o ***.exe ***.f90

where 
*) `gfortran´ is the name of your compiler
*) `-O1´  is the optimization option
*) `-o ***.exe´ is the name of output executable (DO NOT CHANGE!)
*) `***.f90´ is the name of code                 (DO NOT CHANGE!)

For any other informations contact the autors of the script 
(see description.html)
******************************************************************

Now we're adjusting the Makefile and a simple installation is wi



**************** Users of GRASS 6.3 ******************************
1) 


**************** Users of GRASS 6.2 ******************************
1) Change the name of the script for GRASS 6.3.x releases
mv r.inund.fluv r.inund.fluv_63
2) Change the name of script for grass 6.2.x releases
mv r.inund.fluv_62 r.inund.fluv
3) 

