@echo off

rem Download GRASS from SVN
rem
rem Eg.
rem svn checkout http://svn.osgeo.org/grass/grass/tags/release_20121024_grass_6_4_3RC1 grass643RC1
rem

cd C:\Users\landa\grass_packager

set MAJOR=6
set MINOR=4
set PATCH=3RC4
set REV=1

rem Compile GRASS versions
rmdir /s /q C:\OSGeo4W\apps\grass\grass-%MAJOR%.%MINOR%.%PATCH%
rem native & osgeo4w
C:\OSGeo4W\apps\msys\bin\bash.exe C:\Users\landa\grass_packager\grass_compile.sh %MAJOR%%MINOR%%PATCH%

rem Preparation
if exist .\grass%MAJOR%%MINOR%%PATCH% rmdir /S/Q .\grass%MAJOR%%MINOR%%PATCH%
xcopy C:\OSGeo4W\usr\src\grass%MAJOR%%MINOR%%PATCH%\mswindows\* .\grass%MAJOR%%MINOR%%PATCH% /S/V/F/I

cd .\grass%MAJOR%%MINOR%%PATCH%
call .\GRASS-Packager.bat
cd ..

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_osgeo4w.sh %MAJOR%%MINOR%%PATCH% %MAJOR%.%MINOR%.%PATCH% %REV%
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_svn_info.sh %MAJOR%%MINOR%%PATCH% %REV%

C:\DevTools\makensis.exe .\grass%MAJOR%%MINOR%%PATCH%\GRASS-Installer.nsi

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_md5sum.sh %MAJOR%%MINOR%%PATCH%

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_addons.sh %MAJOR%%MINOR%%PATCH%

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_copy_wwwroot.sh %MAJOR%%MINOR%%PATCH% %MAJOR%.%MINOR%.%PATCH% 

rem pscp.exe -r -i .\ssh\id_dsa.ppk .\grass%MAJOR%%MINOR%%PATCH%\addons\*.zip    landa@geo102:/work/wingrass/grass%MAJOR%%MINOR%/addons/grass-%MAJOR%.%MINOR%.%PATCH%
rem pscp.exe -r -i .\ssh\id_dsa.ppk .\grass%MAJOR%%MINOR%%PATCH%\addons\*.md5sum landa@geo102:/work/wingrass/grass%MAJOR%%MINOR%/addons/grass-%MAJOR%.%MINOR%.%PATCH%
rem pscp.exe -r -i .\ssh\id_dsa.ppk .\grass%MAJOR%%MINOR%%PATCH%\addons\logs     landa@geo102:/work/wingrass/grass%MAJOR%%MINOR%/addons/grass-%MAJOR%.%MINOR%.%PATCH%
