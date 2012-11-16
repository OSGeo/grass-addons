@echo off

rem Upgrade OSGeo4W installations

set PATH_ORIG=%PATH%

rem
rem OSGeo4W (GRASS 6)
rem
set PATH=C:\OSGeo4W\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade

rem
rem OSGeo4W (GRASS 7)
rem
set PATH=C:\OSGeo4W_g7\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade

rem
rem OSGeo4W (Dev)
rem

set PATH=C:\OSGeo4W_dev\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade
