#!/bin/sh

# foo will be the number of processors available in the Cluster
foo=3
filename=ndvi1-new-$foo

time mpirun -np $foo i.vi.mpi viname=ndvi red=newL71092084_08420100126_B30 nir=newL71092084_08420100126_B40 output=$filename tmp=1

exit 0
