@echo off

cd C:\Users\landa\grass_packager

rem Compile GRASS versions
rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.4.0svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.5.svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-7.0.svn
C:\OSGeo4W\apps\msys\bin\bash.exe C:\Users\landa\grass_packager\grass_compile.sh
C:\OSGeo4W\apps\msys\bin\bash.exe C:\Users\landa\grass_packager\grass_install_70.sh

rem Preparation
if exist .\grass64 rmdir /S/Q .\grass64
xcopy C:\OSGeo4W\usr\src\grass64_release\mswindows\* .\grass64 /S/V/F/I
if exist .\grass65 rmdir /S/Q .\grass65
xcopy C:\OSGeo4W\usr\src\grass6_devel\mswindows\* .\grass65 /S/V/F/I
if exist .\grass70 rmdir /S/Q .\grass70
xcopy C:\OSGeo4W\usr\src\grass_trunk\mswindows\* .\grass70 /S/V/F/I

cd .\grass64
call .\GRASS-Packager.bat
cd ..
cd .\grass65
call .\GRASS-Packager.bat
cd ..
cd .\grass70
call .\GRASS-Packager.bat
cd ..

copy .\msys.bat .\grass64\GRASS-64-Dev-Package\msys\
copy .\msys.bat .\grass65\GRASS-65-Dev-Package\msys\
copy .\msys.bat .\grass70\GRASS-70-Dev-Package\msys\

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_svn_info.sh

C:\DevTools\makensis.exe .\grass64\GRASS-Installer.nsi
C:\DevTools\makensis.exe .\grass65\GRASS-Installer.nsi
C:\DevTools\makensis.exe .\grass70\GRASS-Installer.nsi

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_md5sum.sh

pscp.exe -i .\ssh\id_dsa.ppk .\grass64\WinGRASS*.exe* landa@josef:/var/www/wingrass/grass64
pscp.exe -i .\ssh\id_dsa.ppk .\grass65\WinGRASS*.exe* landa@josef:/var/www/wingrass/grass65
pscp.exe -i .\ssh\id_dsa.ppk .\grass70\WinGRASS*.exe* landa@josef:/var/www/wingrass/grass70
