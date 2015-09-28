@echo off

cd C:\Users\landa\grass_packager

REM
REM Clean-up
REM
REM rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.4.5svn
REM rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.5.svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-7.0.2svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-7.1.svn

REM
REM Compile GRASS versions
REM
C:\OSGeo4W\apps\msys\bin\bash.exe C:\Users\landa\grass_packager\grass_compile.sh

REM
REM Clean-up
REM
REM if exist .\grass64 rmdir /S/Q .\grass64
REM xcopy C:\OSGeo4W\usr\src\grass64_release\mswindows\* .\grass64 /S/V/F/I
REM if exist .\grass65 rmdir /S/Q .\grass65
REM xcopy C:\OSGeo4W\usr\src\grass6_devel\mswindows\* .\grass65 /S/V/F/I
if exist .\grass70 rmdir /S/Q .\grass70
xcopy C:\OSGeo4W\usr\src\grass70_release\mswindows\* .\grass70 /S/V/F/I
if exist .\grass71 rmdir /S/Q .\grass71
xcopy C:\OSGeo4W\usr\src\grass_trunk\mswindows\* .\grass71 /S/V/F/I

REM
echo Preparing packages...
REM
REM cd .\grass64
REM call .\GRASS-Packager.bat > .\GRASS-Packager.log
REM cd ..
REM cd .\grass65
REM call .\GRASS-Packager.bat
REM cd ..
cd .\grass70
call .\GRASS-Packager.bat > .\GRASS-Packager.log
cd ..
cd .\grass71
call .\GRASS-Packager.bat > .\GRASS-Packager.log
cd ..

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_osgeo4w.sh
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_svn_info.sh

REM
echo Creating standalone installer...
REM
REM C:\DevTools\makensis.exe .\grass64\GRASS-Installer.nsi > .\grass64\GRASS-Installer.log
REM C:\DevTools\makensis.exe .\grass65\GRASS-Installer.nsi
C:\DevTools\makensis.exe .\grass70\GRASS-Installer.nsi > .\grass70\GRASS-Installer.log
C:\DevTools\makensis.exe .\grass71\GRASS-Installer.nsi > .\grass71\GRASS-Installer.log

REM
REM Create md5sum files
REM
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_md5sum.sh

REM
REM Build Addons 
REM
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_addons.sh

REM
REM Copy packages
REM
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_copy_wwwroot.sh
