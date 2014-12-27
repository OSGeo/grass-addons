#!/bin/sh

# Sample script to test g.cloud with more user defined variables and raster
# How to use this test:
# - start GRASS with North Carolina dataset location
#
# TEST 1: pairwise: use var with size 3; and corr with size 7
# - g.cloud conf=~/.diss server=giscluster grass=/PATH/TO/g.cloud/test/test_morevariables_raster.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh variables="{'TEXTURE' : ['var','corr'], 'SIZE' : [3,7]}" raster=lsat7_2002_40
#
# TEST 2: all-to-all: use var with size 3 and 7; use corr with size 3 and 7
# - g.cloud -c conf=~/.diss server=giscluster grass=/PATH/TO/g.cloud/test/test_morevariables_raster.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh variables="{'TEXTURE' : ['var','corr'], 'SIZE' : [3,7]}" raster=lsat7_2002_40

g.region raster=lsat7_2002_40
r.texture input=lsat7_2002_40 prefix=lsat7_2002_40_$SIZE method=$TEXTURE size=$SIZE

