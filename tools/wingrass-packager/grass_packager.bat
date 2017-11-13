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
	rem if not exist "grass70" mkdir grass70
	rem if exist .\grass70\%~1 rmdir /S/Q .\grass70\%~1
	rem xcopy C:\msys%~2\usr\src\grass70_release\mswindows\* .\grass70\%~1 /S/V/I > NUL
	if not exist "grass72" mkdir grass72
	if exist .\grass72\%~1 rmdir /S/Q .\grass72\%~1
	xcopy C:\msys%~2\usr\src\grass72_release\mswindows\* .\grass72\%~1 /S/V/I > NUL
	if not exist "grass74" mkdir grass74
	if exist .\grass74\%~1 rmdir /S/Q .\grass74\%~1
	xcopy C:\msys%~2\usr\src\grass74_release\mswindows\* .\grass74\%~1 /S/V/I > NUL
	if not exist "grass75" mkdir grass75
	if exist .\grass75\%~1 rmdir /S/Q .\grass75\%~1
	xcopy C:\msys%~2\usr\src\grass_trunk\mswindows\*     .\grass75\%~1 /S/V/I > NUL
exit /b 0

:preparePkg
	echo ...(%~1)
	rem cd .\grass70\%~1
	rem call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	rem cd ..\..
	cd .\grass72\%~1
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
	cd .\grass74\%~1
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
	cd .\grass75\%~1
	call .\GRASS-Packager.bat %~2 > .\GRASS-Packager.log
	cd ..\..
exit /b 0

:createPkg
	echo ...(%~1)
	rem C:\DevTools\makensis.exe .\grass70\%~1\GRASS-Installer.nsi > .\grass70\%~1\GRASS-Installer.log
	C:\DevTools\makensis.exe .\grass72\%~1\GRASS-Installer.nsi > .\grass72\%~1\GRASS-Installer.log
	C:\DevTools\makensis.exe .\grass74\%~1\GRASS-Installer.nsi > .\grass74\%~1\GRASS-Installer.log        
        C:\DevTools\makensis.exe .\grass75\%~1\GRASS-Installer.nsi > .\grass75\%~1\GRASS-Installer.log
exit /b 0
