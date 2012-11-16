@echo off

rem Upgrade OSGeo4W Dev installation

set PATH=C:\OSGeo4W_dev\bin;%PATH%
call o4w_env.bat

apt update
apt upgrade
