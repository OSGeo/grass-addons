#!/bin/bash
# This script creates the water outlet points
# for different stream networks in the "streams@PERMANENT"
# vector map layer in the nc location
# Author: IGB-Berlin,Johannes Radinger; Implementation: Geoinformatikbuero Dassau GmbH , Soeren Gebbert
# This tool was developed as part of the BiodivERsA-net project 'FISHCON'
# and has been funded by the German Federal Ministry for Education and
# Research (grant number 01LC1205).

cat > points.csv << EOF
640781.56098|214897.033189
642228.347134|214979.370612
638470.926725|214984.99142
645247.580918|223346.644849
638470.926725|214984.99142
645247.580918|223346.644849
EOF

v.in.ascii output=stream_outflow input=points.csv x=1 y=2

