@echo off

cd C:\Users\landa\grass_packager

REM
echo Clean-up...
REM
call :cleanUp 32
call :cleanUp 64

REM
echo Compiling GRASS GIS...
REM
C:\msys32\usr\bin\bash.exe .\grass_compile.sh 32
C:\msys64\usr\bin\bash.exe .\grass_compile.sh 64

REM
echo Clean-up for packaging...
REM
call:cleanUpPkg x86    32
call:cleanUpPkg x86_64 64

REM
echo Preparing packages...
REM
call:preparePkg x86    32
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
C:\msys32\usr\bin\bash.exe .\grass_addons.sh 32
C:\msys64\usr\bin\bash.exe .\grass_addons.sh 64

REM
echo Publishing packages...
REM
C:\msys32\usr\bin\bash.exe .\grass_copy_wwwroot.sh 32
C:\msys64\usr\bin\bash.exe .\grass_copy_wwwroot.sh 64

exit /b %ERRORLEVEL%

:cleanUp
	echo ...(%~1)
        for /d %%G in ("C:\OSGeo4W%~1\apps\grass\grass-7*svn") do rmdir /S/Q "%%G"
exit /b 0

:cleanUpPkg
	echo ...(%~1)
	if not exist "grass70" mkdir grass70
	if exist .\grass70\%~1 rmdir /S/Q .\grass70\%~1
	xcopy C:\msys%~2\usr\src\grass70_release\mswindows\* .\grass70\%~1 /S/V/I > NUL
	if not exist "grass71" mkdir grass71
	if exist .\grass71\%~1 rmdir /S/Q .\grass71\%~1
	xcopy C:\msys%~2\usr\src\grass_trunk\mswindows\*     .\grass71\%~1 /S/V/I > NUL
exit /b 0

:preparePkg
	echo ...(%~1)
	cd .\grass70\%~1
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
	cd .\grass71\%~1
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
exit /b 0

:createPkg
	echo ...(%~1)
	C:\DevTools\makensis.exe .\grass70\%~1\GRASS-Installer.nsi > .\grass70\%~1\GRASS-Installer.log
	C:\DevTools\makensis.exe .\grass71\%~1\GRASS-Installer.nsi > .\grass71\%~1\GRASS-Installer.log
exit /b 0
