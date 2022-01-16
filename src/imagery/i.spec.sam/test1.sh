#!/bin/bash
#This is a test using nc_spm_08_grass7 sample dataset
#from the main grass website

# create R/G/B/NIR
i.group group=test1 input=sam_test_b1,sam_test_b2,sam_test_b3,sam_test_b4

# computational region
g.region raster=sam_test_b1 -p

# SAM
i.spec.sam group=test1 input=~/dev/grass-addons/src/imagery/i.spec.sam/spectrum.dat result=specang
# color table (TODO: should be reverse?)
for map in `seq 1 4` ; do r.colors specang.$map color=grey ; done

# visualize
d.mon wx1 ; sleep 2 ; d.rast specang.1; d.legend specang.1
d.mon wx2 ; sleep 2 ; d.rast specang.2; d.legend specang.2
d.mon wx3 ; sleep 2 ; d.rast specang.3; d.legend specang.3
d.mon wx4 ; sleep 2 ; d.rast specang.4; d.legend specang.4

