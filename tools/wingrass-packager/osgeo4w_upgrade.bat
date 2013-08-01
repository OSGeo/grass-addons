@echo off

rem Upgrade OSGeo4W installations
rem Requires 'apt' package to be installed

set PATH_ORIG=%PATH%

rem
rem OSGeo4W (building environment GRASS 6 & 7)
rem
set PATH=C:\OSGeo4W\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade

rem
rem OSGeo4W_dev (testing environment for daily builds)
rem

set PATH=C:\OSGeo4W_dev\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade

rem
rem OSGeo4W_grass6 (GRASS 6 packaging)
rem

set PATH=C:\OSGeo4W_grass6\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade

rem
rem OSGeo4W_grass7 (GRASS 7 packaging)
rem

set PATH=C:\OSGeo4W_grass7\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade
