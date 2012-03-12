#!/bin/sh

# foo will be the number of processors available in the Cluster
foo=3
filename=ndvi1-new-$foo

time mpirun -np $foo i.vi.mpi viname=ndvi red=p126r050_7t20001231_z48_nn30.tif nir=p126r050_7t20001231_z48_nn40.tif vi=$filename tmp=1

exit 0
