@echo off

cd C:\Users\landa\grass_packager

rem Compile GRASS versions
rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.4.4svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.5.svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-7.0.svn
rem native & osgeo4w
C:\OSGeo4W\apps\msys\bin\bash.exe C:\Users\landa\grass_packager\grass_compile.sh

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

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_osgeo4w.sh
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_svn_info.sh

C:\DevTools\makensis.exe .\grass64\GRASS-Installer.nsi

C:\DevTools\makensis.exe .\grass65\GRASS-Installer.nsi

C:\DevTools\makensis.exe .\grass70\GRASS-Installer.nsi

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_md5sum.sh

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_addons.sh

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_copy_wwwroot.sh
