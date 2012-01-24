#!/bin/sh

# Sample script to test g.cloud without user defined variables
# How to use test:
# - start GRASS with North Carolina dataset location
#
# TEST 1: pairwise: use number point 10 with buffer distance 100; and number point 20 with buffer distance 500
# - g.cloud conf=~/.diss server=giscluster grass=/PATH/TO/g.cloud/test/test_morevariables.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh variables="{'NPOINT' : [10,20], 'BUFFERDIST' : [100,500]}"
# TEST 2: all-to-all: use number point 10 with buffer distance 100 and 500; number point 20 with buffer distance 100 and 500
# - g.cloud -c conf=~/.diss server=giscluster grass=/PATH/TO/g.cloud/test/test_morevariables.sh qsub=/PATH/TO/g.cloud/test/test_launch_SGE_grassjob.sh variables="{'NPOINT' : [10,20], 'BUFFERDIST' : [100,500]}"

# using PID as name suffix
v.random output=random$$_$NPOINT n=$NPOINT
g.region vect=random$$_$NPOINT
v.buffer input=random$$_$NPOINT output=buffer$$_$NPOINT_$BUFFERDIST distance=$BUFFERDIST
