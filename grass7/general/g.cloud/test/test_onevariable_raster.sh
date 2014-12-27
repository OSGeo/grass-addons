#!/bin/sh

# Sample script to test g.cloud with one user defined variable and raster
# How to use test:
# - start GRASS with North Carolina dataset location
#
# - g.cloud conf=~/.gc_loginfile.txt server=giscluster grass=/PATH/TO/g.cloud/test/test_onevariable_raster.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh variables="{'TEXTURE' : ['var','corr']}" raster=lsat7_2002_40

g.region raster=lsat7_2002_40
r.texture input=lsat7_2002_40 prefix=lsat7_2002_40 method=$TEXTURE
