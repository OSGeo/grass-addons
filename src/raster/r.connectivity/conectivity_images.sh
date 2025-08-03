#########################################
# r.connectivity.distance
#########################################

#########################################
# Costs
#########################################

# Generate image
#d.mon wx0
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_distance_costs.png
d.rast costs
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim r_connectivity_distance_costs.png
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../tools/svn-image.sh r_connectivity_distance_costs.png

#########################################
# Patches
#########################################

# Generate image
#d.mon wx0
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_distance_patches.png
#d.rast costs
d.vect patches_1ha
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim r_connectivity_distance_patches.png
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../tools/svn-image.sh r_connectivity_distance_patches.png

#########################################
# Shortest paths
#########################################

# Generate image
#d.mon wx0
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_distance_shortest_paths.png
d.vect patches_1ha
d.vect hws_connectivity_shortest_paths
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim r_connectivity_distance_shortest_paths.png
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../tools/svn-image.sh r_connectivity_distance_shortest_paths.png

#########################################
# Network
#########################################

# Generate image
#d.mon wx0
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_distance_network.png
d.vect hws_connectivity_vertices
d.vect hws_connectivity_edges
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim r_connectivity_distance_network.png
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../tools/svn-image.sh r_connectivity_distance_network.png

#########################################
# r.connectivity.network
#########################################

# Convert output from r.connectivity.network plots
convert -density 171 overview.eps -flatten r_connectivity_network_overview.png
../../../../tools/svn-image.sh r_connectivity_network_overview.png
convert -density 171 kernel.eps -flatten r_connectivity_network_kernel.png
../../../../tools/svn-image.sh r_connectivity_network_kernel.png

# degree centrality
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_network_deg_udc.png
d.vect map=hws_connectivity_edge_measures legend_label=Edges
d.vect.thematic map=hws_connectivity_vertex_measures column=deg_udc algorithm=qua nclasses=4 colors=red,orange,yellow,green icon=basic/circle size=8 legend_title="Degree centrality"
d.legend.vect at=0,100
d.mon stop=cairo
#convert -density 73 r_connectivity_network_deg_udc.svg -flatten r_connectivity_network_deg_udc.png
../../../../tools/svn-image.sh r_connectivity_network_deg_udc.png

d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_network_ebc_udc.png
d.vect -r map=hws_connectivity_vertex_measures icon=basic/circle size_column=pop_proxy legend_label=Vertices
d.vect.thematic map=hws_connectivity_edge_measures column=cf_eb_udc algorithm=qua nclasses=4 colors=191:191:191,184:218:184,92:176:92,0:128:0 where="cf_mst_udc = 1" legend_title="Edge betweenness"
d.legend.vect at=0,100
d.mon stop=cairo
#convert -density 73 r_connectivity_network_ebc_udc.svg -flatten r_connectivity_network_ebc_udc.png
../../../../tools/svn-image.sh r_connectivity_network_ebc_udc.png

#########################################
# r.connectivity.corridors
#########################################

### mst corridors weighted by edge betweenness
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_corridors_mst_eb.png
d.rast map=hws_connectivity_corridors_cd_eb_ud_sum_mst
d.legend raster=hws_connectivity_corridors_cd_eb_ud_sum_mst@stefan.blumentrath title="Edge betweenness"
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim r_connectivity_corridors_mst_eb.png
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../tools/svn-image.sh r_connectivity_corridors_mst_eb.png

### all corridors weighted by potential flow of organisms
d.mon start=cairo width=600  height=600 bgcolor=none output=r_connectivity_corridors_cf_u_sum_all.png
d.rast map=hws_connectivity_corridors_cf_u_sum_all
d.legend raster=hws_connectivity_corridors_cf_u_sum_all title="Potential flow"
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim r_connectivity_corridors_cf_u_sum_all.png
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../tools/svn-image.sh r_connectivity_corridors_cf_u_sum_all.png
