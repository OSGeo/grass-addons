<h2>DESCRIPTION</h2>

<em>v.tin.to.rast</em> converts (rasterizes) a TIN map into a raster map.

<h2>EXAMPLE</h2>

Example of <em>v.tin.to.rast</em> usage (North Carolina sample data set).
Preparation of a TIN (Delaunay triangulation) from geodetic points, then
rasterization of the TIN:

<div class="code"><pre>
# work on a copy of the original geodetic points map
g.copy vector=geodetic_pts,mygeodetic_pts

# data preparation: convert z-values from string to double format
v.db.addcolumn map=mygeodetic_pts columns="Z_VALUE_D double precision"
v.db.update map=mygeodetic_pts column=Z_VALUE_D qcolumn=Z_VALUE

# verify: should show identical z-values
v.db.select map=mygeodetic_pts columns=cat,Z_VALUE,Z_VALUE_D

# convert 2D vector point map to 3D based on attribute
v.to.3d input=mygeodetic_pts output=mygeodetic_pts_3d column=Z_VALUE_D

# create TIN
v.delaunay input=mygeodetic_pts_3d output=mygeodetic_pts_3d_delaunay

# rasterize TIN to 500m resolution raster map
g.region vector=mygeodetic_pts_3d_delaunay res=500 -p
v.tin.to.rast input=mygeodetic_pts_3d_delaunay output=mygeodetic_pts_3d_delaunay
r.colors mygeodetic_pts_3d_delaunay color=srtm_plus
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/v.delaunay.html">v.delaunay</a>
</em>

<h2>AUTHORS</h2>

Antonio Alliegro, Alexander Muriy<br>
Example: Markus Neteler
