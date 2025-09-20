@echo off
REM Set environment variables for OSGeo4W
set PATH=C:\OSGeo4W\bin;%PATH%
set GDAL_DATA=C:\OSGeo4W\share\gdal
set PROJ_LIB=C:\OSGeo4W\share\proj

REM Get GDAL version number from gdalinfo
for /f "tokens=2 delims= " %%a in ('gdalinfo --version') do set GDAL_VER=%%a

REM Echo detected version
echo Detected GDAL version: %GDAL_VER%

REM Install matching GDAL Python package
pip install "gdal==%GDAL_VER%"
