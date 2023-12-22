#!/bin/bash
# Author: IGB-Berlin,Johannes Radinger; Implementation: Geoinformatikbuero Dassau GmbH , Soeren Gebbert
# This tool was developed as part of the BiodivERsA-net project 'FISHCON'
# and has been funded by the German Federal Ministry for Education and
# Research (grant number 01LC1205).

# Generate the map and images for the HTML documentation
export GRASS_OVERWRITE=1

# Import the stream network and the outlet points
v.in.ascii input=data/stream_network.txt output=stream_network \
    format=standard
v.in.ascii input=data/stream_network_outlets.txt output=stream_network_outlets \
    format=standard

# Compute the different stream orders
v.stream.order input=stream_network points=stream_network_outlets \
    output=stream_network_order threshold=25 \
    order=strahler,shreve,drwal,scheidegger

# Set the correct region to visualize the 3 stream network
n=216770
s=215080
w=642660
e=644040
g.region s=${s} n=${n} e=${e} w=${w} -p

export GRASS_RENDER_WIDTH=400
export GRASS_RENDER_HIGHT=800
d.mon start=ps output=map.ps
d.erase
d.vect map=stream_network display=shape,dir \
    width=3 size=10 label_size=20

convert map.ps stream_network.pdf
convert stream_network.pdf stream_network.png

d.erase
d.vect map=stream_network_order display=shape,dir \
    width=3 width_column=strahler width_scale=3 size=15 \
    attribute_column=strahler label_size=35 where="network = 3"

convert map.ps stream_network_order_strahler.pdf
convert stream_network_order_strahler.pdf stream_network_order_strahler.png

d.erase
d.vect map=stream_network_order display=shape,dir \
    width=3 width_column=shreve width_scale=3 size=15 \
    attribute_column=shreve label_size=35 where="network = 3"

convert map.ps stream_network_order_shreve.pdf
convert stream_network_order_shreve.pdf stream_network_order_shreve.png

d.erase
d.vect map=stream_network_order display=shape,dir \
    width=3 width_column=drwal width_scale=3 size=15 \
    attribute_column=drwal label_size=35 where="network = 3"

convert map.ps stream_network_order_drwal.pdf
convert stream_network_order_drwal.pdf stream_network_order_drwal.png

d.erase
d.vect map=stream_network_order display=shape,dir \
    width=3 width_column=scheidegger width_scale=3 size=15 \
    attribute_column=scheidegger label_size=35 where="network = 3"

convert map.ps stream_network_order_scheidegger.pdf
convert stream_network_order_scheidegger.pdf stream_network_order_scheidegger.png
