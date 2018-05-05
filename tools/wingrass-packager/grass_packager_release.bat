@echo off

REM Download GRASS from SVN
REM
REM eg. svn checkout http://svn.osgeo.org/grass/grass/tags/release_20140625_grass_6_4_4 grass644
REM

REM
REM TODO: merge with grass_packager.bat
REM

cd C:\Users\landa\grass_packager

set MAJOR=7
set MINOR=4
set PATCH=1RC1
set REV=1

set GVERSION=%MAJOR%%MINOR%%PATCH%

REM
echo Clean-up...
REM
call :cleanUp 32
call :cleanUp 64

REM
echo Compiling GRASS GIS...
REM
C:\msys32\usr\bin\bash.exe .\grass_compile.sh 32 %GVERSION%
C:\msys64\usr\bin\bash.exe .\grass_compile.sh 64 %GVERSION%

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
C:\msys32\usr\bin\bash.exe .\grass_osgeo4w.sh  32 %GVERSION% %MAJOR%.%MINOR%.%PATCH% %REV%
C:\msys64\usr\bin\bash.exe .\grass_osgeo4w.sh  64 %GVERSION% %MAJOR%.%MINOR%.%PATCH% %REV%
C:\msys32\usr\bin\bash.exe .\grass_svn_info.sh 32 %GVERSION% %REV%
C:\msys64\usr\bin\bash.exe .\grass_svn_info.sh 64 %GVERSION% %REV%

REM
echo Creating standalone installer...
REM
call:createPkg x86
call:createPkg x86_64

REM
REM Create md5sum files
REM
C:\msys32\usr\bin\bash.exe .\grass_md5sum.sh 32 %GVERSION%
C:\msys64\usr\bin\bash.exe .\grass_md5sum.sh 64 %GVERSION%

exit /b %ERRORLEVEL%

:cleanUp
	echo ...(%~1)
        if exist "C:\OSGeo4W%~1\apps\grass\grass-%MAJOR%.%MINOR%.%PATCH%" rmdir /S/Q "C:\OSGeo4W%~1\apps\grass\grass-%MAJOR%.%MINOR%.%PATCH%"
exit /b 0

:cleanUpPkg
	echo ...(%~1)
	if not exist "grass%GVERSION%" mkdir grass%GVERSION%
	if exist .\grass%GVERSION%\%~1 rmdir /S/Q .\grass%GVERSION%\%~1
	xcopy C:\msys%~2\usr\src\grass%GVERSION%\mswindows\* .\grass%GVERSION%\%~1 /S/V/I > NUL
exit /b 0

:preparePkg
	echo ...(%~1)
	cd .\grass%GVERSION%\%~1
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
exit /b 0

:createPkg
	echo ...(%~1)
	C:\DevTools\makensis.exe .\grass%GVERSION%\%~1\GRASS-Installer.nsi > .\grass%GVERSION%\%~1\GRASS-Installer.log
exit /b 0

