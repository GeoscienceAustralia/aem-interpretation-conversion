#!/bin/bash
#
# originally contributed by @rbuffat to Toblerity/Fiona
set -e

GDALOPTS="  --with-geos \
            --with-expat \
            --without-libtool \
            --with-libz=internal \
            --with-libtiff=internal \
            --with-geotiff=internal \
            --without-gif \
            --without-pg \
            --without-grass \
            --without-libgrass \
            --without-cfitsio \
            --without-pcraster \
            --with-netcdf \
            --with-png=internal \
            --with-jpeg=internal \
            --without-gif \
            --without-ogdi \
            --without-fme \
            --without-hdf4 \
            --with-hdf5 \
            --without-jasper \
            --without-ecw \
            --without-kakadu \
            --without-mrsid \
            --without-jp2mrsid \
            --without-mysql \
            --without-ingres \
            --without-xerces \
            --without-odbc \
            --with-curl \
            --without-sqlite3 \
            --without-idb \
            --without-sde \
            --without-perl \
            --without-python"

# Create build dir if not exists
if [ ! -d "/home/runner/gdalbuild" ]; then
  mkdir -p /home/runner/gdalbuild;
fi

if [ ! -d "/home/runner/gdalinstall" ]; then
  mkdir -p /home/runner/gdalinstall;
fi

ls -l /home/runner/gdalinstall


PROJOPT="--with-proj=/home/runner/gdalinstall/gdal-3.10.2"

if [ ! -d "/home/runner/gdalinstall/gdal-3.10.2/share/gdal" ]; then
    cd /home/runner/gdalbuild
    gdalver=$(expr "3.10.2" : '\([0-9]*.[0-9]*.[0-9]*\)')
    wget -q http://download.osgeo.org/gdal/$gdalver/gdal-3.10.2.tar.gz
    tar -xzf gdal-3.10.2.tar.gz
    cd gdal-$gdalver
    ./configure --prefix=/home/runner/gdalinstall/gdal-3.10.2 $GDALOPTS $PROJOPT
    make -s -j 2
    make install
fi
