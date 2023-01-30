export grassdata_directory="/opt/comet/downscale/grass"
export base_location="california_albers"
export gregion="g.region rast=savanna_test@savanna_test"
export command="r.slope.aspect elevation=ned_ca_masked_epsg3310@ned \
slope=ned_ca_masked_epsg3310_comet_00008m_slope \
aspect=ned_ca_masked_epsg3310_comet_00008m_aspect \
format=degrees prec=float zfactor=1.0 min_slp_allowed=0.0"
# outputs should be a list or prefix
unset outputs
export outputs="ned_ca_masked_epsg3310_comet_00008m_*"
export tilexsize="500"
export tileysize="500"
export tileoverlap="10"
export mask="ned_ca_masked_epsg3310_comet_00008m"
