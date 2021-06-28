#!/bin/sh

# Sample script to test g.cloud without user defined variables
# How to use test:
# - start GRASS with North Carolina dataset location
#
# - g.cloud conf=~/.gc_loginfile.txt server=giscluster grass=/PATH/TO/g.cloud/test/test_novariables_raster.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh

# using PID ($$) as name suffix
v.random output=random$$ n=123
g.region vect=random$$
v.buffer input=random$$ output=buffer$$ distance=200
