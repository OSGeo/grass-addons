@echo off

rem Upgrade OSGeo4W installations

set PATH_ORIG=%PATH%

rem
rem OSGeo4W (building environment)
rem
set PATH=C:\OSGeo4W\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade

rem
rem OSGeo4W (dev)
rem

set PATH=C:\OSGeo4W_dev\bin;%PATH_ORIG%
call o4w_env.bat

apt update
apt upgrade
