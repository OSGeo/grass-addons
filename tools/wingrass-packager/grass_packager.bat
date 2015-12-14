@echo off

cd C:\Users\landa\grass_packager

REM
echo Clean-up...
REM
call :cleanUp x86
call :cleanUp x86_64

REM
echo Compiling GRASS GIS...
REM
C:\msys32\usr\bin\bash.exe .\grass_compile.sh 32
C:\msys64\usr\bin\bash.exe .\grass_compile.sh 64

REM
echo Clean-up for packaging...
REM
call:cleanUpPkg x86
call:cleanUpPkg x86_64

REM
echo Preparing packages...
REM
call:preparePkg x86 32
call:preparePkg x86_64 64

REM
echo Finding latest package and update info...
REM
C:\msys32\usr\bin\bash.exe .\grass_osgeo4w.sh  32
C:\msys64\usr\bin\bash.exe .\grass_osgeo4w.sh  64
C:\msys32\usr\bin\bash.exe .\grass_svn_info.sh 32
C:\msys64\usr\bin\bash.exe .\grass_svn_info.sh 64

REM
echo Creating standalone installer...
REM
call:createPkg x86
call:createPkg x86_64

REM
REM Create md5sum files
REM
C:\msys32\usr\bin\bash.exe .\grass_md5sum.sh 32
C:\msys64\usr\bin\bash.exe .\grass_md5sum.sh 64

REM
echo Building addons...
REM
REM REM C:\msys32\usr\bin\bash.exe .\grass_addons.sh 32
REM REM C:\msys64\usr\bin\bash.exe .\grass_addons.sh 64

REM
REM Copy packages
REM
REM REM C:\msys32\usr\bin\bash.exe .\grass_copy_wwwroot.sh 32
REM REM C:\msys64\usr\bin\bash.exe .\grass_copy_wwwroot.sh 64

exit /b %ERRORLEVEL%

:cleanUp
for /d %%G in ("C:\OSGeo4W%~1\apps\grass\grass-7*svn") do rmdir /s /q "%%G"
exit /b 0

:cleanUpPkg
	if not exist "%~1" mkdir %~1
	if exist .\%~1\grass70 rmdir /S/Q .\%~1\grass70
	xcopy C:\msys32\usr\src\grass70_release\mswindows\* .\%~1\grass70 /S/V/I > NUL
	if exist .\%~1\grass71 rmdir /S/Q .\%~1\grass71
	xcopy C:\msys32\usr\src\grass_trunk\mswindows\*     .\%~1\grass71 /S/V/I > NUL
exit /b 0

:preparePkg
	cd .\%~1\grass70
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
	cd .\%~1\grass71
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
exit /b 0

:createPkg
	C:\DevTools\makensis.exe .\%~1\grass70\GRASS-Installer.nsi > .\%~1\grass70\GRASS-Installer.log
	C:\DevTools\makensis.exe .\%~1\grass71\GRASS-Installer.nsi > .\%~1\grass71\GRASS-Installer.log
exit /b 0
