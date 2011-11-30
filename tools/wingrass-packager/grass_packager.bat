@echo off

cd C:\Users\landa\grass_packager

rem Compile GRASS versions
rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.4.2svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-6.5.svn
rmdir /s /q C:\OSGeo4W\apps\grass\grass-7.0.svn
rem native & osgeo4w
C:\OSGeo4W\apps\msys\bin\bash.exe C:\Users\landa\grass_packager\grass_compile.sh

rem Preparation
if exist .\grass64 rmdir /S/Q .\grass64
xcopy C:\OSGeo4W\usr\src\grass64_release\mswindows\* .\grass64 /S/V/F/I
xcopy C:\OSGeo4W\usr\src\grass64_release\package\grass64\* .\grass64\ /S/V/F/I
if exist .\grass65 rmdir /S/Q .\grass65
xcopy C:\OSGeo4W\usr\src\grass6_devel\mswindows\* .\grass65 /S/V/F/I
xcopy C:\OSGeo4W\usr\src\grass6_devel\package\grass65\* .\grass65\ /S/V/F/I
if exist .\grass70 rmdir /S/Q .\grass70
xcopy C:\OSGeo4W\usr\src\grass_trunk\mswindows\* .\grass70 /S/V/F/I
xcopy C:\OSGeo4W\usr\src\grass_trunk\package\grass70\* .\grass70\ /S/V/F/I

cd .\grass64
call .\GRASS-Packager.bat
cd ..
cd .\grass65
call .\GRASS-Packager.bat
cd ..
cd .\grass70
call .\GRASS-Packager.bat
cd ..

copy .\msys.bat .\grass64\GRASS-64-Package\msys\
copy .\msys.bat .\grass65\GRASS-65-Package\msys\
copy .\msys.bat .\grass70\GRASS-70-Package\msys\

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_osgeo4w.sh
C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_svn_info.sh

C:\DevTools\makensis.exe .\grass64\GRASS-Installer.nsi
C:\DevTools\makensis.exe .\grass65\GRASS-Installer.nsi
C:\DevTools\makensis.exe .\grass70\GRASS-Installer.nsi

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_md5sum.sh

C:\OSGeo4W\apps\msys\bin\sh.exe .\grass_addons.sh

pscp.exe -i    .\ssh\id_dsa.ppk .\grass64\WinGRASS*.exe* landa@geo102:/work/wingrass/grass64
pscp.exe -i    .\ssh\id_dsa.ppk .\grass64\grass*.tar.bz2 landa@geo102:/work/wingrass/grass64/osgeo4w
pscp.exe -i    .\ssh\id_dsa.ppk .\grass65\WinGRASS*.exe* landa@geo102:/work/wingrass/grass65
pscp.exe -i    .\ssh\id_dsa.ppk .\grass65\grass*.tar.bz2 landa@geo102:/work/wingrass/grass65/osgeo4w
pscp.exe -i    .\ssh\id_dsa.ppk .\grass70\WinGRASS*.exe* landa@geo102:/work/wingrass/grass70
pscp.exe -i    .\ssh\id_dsa.ppk .\grass70\grass*.tar.bz2 landa@geo102:/work/wingrass/grass70/osgeo4w

pscp.exe -r -i .\ssh\id_dsa.ppk .\grass65\addons\*.zip .\grass65\addons\*.md5sum landa@geo102:/work/wingrass/grass65/addons
pscp.exe -r -i .\ssh\id_dsa.ppk .\grass65\addons\log .\grass65\addons\make.log   landa@geo102:/work/wingrass/grass65/addons
pscp.exe -r -i .\ssh\id_dsa.ppk .\grass70\addons\*.zip .\grass70\addons\*.md5sum landa@geo102:/work/wingrass/grass70/addons
pscp.exe -r -i .\ssh\id_dsa.ppk .\grass70\addons\log .\grass70\addons\make.log   landa@geo102:/work/wingrass/grass70/addons

