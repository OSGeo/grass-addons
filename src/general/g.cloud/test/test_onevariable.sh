#!/bin/sh

# Sample script to test g.cloud without user defined variables
# How to use test:
# - start GRASS with North Carolina dataset location
#
# - g.cloud conf=~/.gc_loginfile.txt server=giscluster grass=/PATH/TO/g.cloud/test/test_onevariable.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh variables="{'NPOINT' : [20,50,100]}" raster=lsat7_2002_40

# using PID ($$) as name suffix
v.random output=random$$_$NPOINT n=$NPOINT
g.region vector=random$$_$NPOINT
v.buffer input=random$$_$NPOINT output=buffer$$ distance=1
