<h2>DESCRIPTION</h2>

<em>r.in.ahn</em> imports the Actueel Hoogtebestand Nederland (<a
href="https://www.ahn.nl">AHN</a>, version 4) for the current region.
The AHN is a digital elevation model (DEM) of the Netherlands with a
resolution of of 0.5 meter.

<p>
There are two different layers available: the digital terrain model
(DTM) and a digital surface model (DSM). The user needs to select which
to download. The selected product will be downloaded for the
computation region. However, note that the region will adjusted to
ensure that the imported raster layer neatly aligns with and has the
same resolution (0.5 meter) as the original AHN data. The resulting
will always have the same or a larger extent than the original
computation region. If you want to store the current computational
region, make sure to first save it using <em>g.region</em>.

<p>
The AHN can also be downloaded in map sheets (tiles) of 6.5 by 5
kilometer. To download the area covered by one or more of these tiles,
the user can set the <b>-t</b> flag. This wil to download the area for
the tiles that overlap with the current computational region.

<h2>NOTE</h2>

This location only works in a location with the project 'RD New'
(EPSG:28992). Attempts to run it in a location with another CRS will
result in an error message.

<p>
The region will be adjusted to ensure that the imported raster layer
neatly aligns with and has the same resolution (0.5 meter) as the
original AHN data. The user can set the <b>-g</b> flag to return the
region to the original computation region after the data is imported.

<p>
The addon uses the <em>r.in.wcs</em> addon in the background, so the
user will first need to install this addon.

<h2>EXAMPLE</h2>

<h3>Example 1</h3>

Import the DTM for Fort Crèvecoeur, an fortress where the river <i>Old
Dieze</i> flows into the <i>Maas</i> river.

<p>
<div class="code"><pre>
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn product=dsm output=dsm_crevecoeur
</pre></div>

<p>
<div align="center" style="margin: 10px">
<a href="r_in_ahn_01.png">
<img src="r_in_ahn_01.png" alt="r.in.ahn example" width="600" border="0">
</a><br>
<i>Figure: DSM map of Fort Crèvecoeur</i>
</div>

<h3>Example 2</h3>

Import the DTM for the tile that overlaps with the current region. Do
this by setting the <b>-t flag</b>.

<p>
<div class="code"><pre>
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn -t product=dsm output=dsm_crevecoeur2
</pre></div>

<p>
The result will be a raster layer <i>dsm_crevecoeur2</i> and a vector
layer <i>dsm_crevecoeur2_tiles</i>

<p>
<div align="center" style="margin: 10px">
<a href="r_in_ahn_02.png">
<img src="r_in_ahn_02.png" alt="r.in.ahn example" width="600" border="0">
</a><br>
<i>Figure: DSM map of Fort Crèvecoeur. Left shows the extent (red
outline) after running example 2. The extent equals the extent of the
area (tile) for which the data was downloaded. Right shows the extent
(red outline) after running example 3. In this case, the extent is the
same as before running the example because the <b>-g</b> flag was
set.</i>
</div>

<h3>Example 3</h3>

Set the <b>-t</b> flag to import the DTM for the tile that overlaps
with the current region. Set the <b>-g</b> flag to keep the current
computation region after importing the requested data. Note, the
imported data will still have the resolution of, and will be aligned
to, the original AHN data.

<p>
<div class="code"><pre>
# Set the region for Fort Crèvecoeur
g.region n=416562 s=415957 w=145900 e=147003 res=0.5

# Download the DSM
r.in.ahn -t -g product=dsm output=dsm_crevecoeur3
</pre></div>

<p>
The result will be a raster layer <i>dsm_crevecoeur3</i> and a vector
layer <i>dsm_crevecoeur3_tiles</i>


<h2>REFERENCES</h2>

See the <a href="https://ahn.nl">AHN</a> webpage for more information
about the AHN data (in Dutch).

<h2>AUTHORS</h2>

Paulo van Breugel  |  <a href="https://has.nl">HAS green academy</a>,
University of Applied Sciences  |  <a
href="https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/">Climate-robust
Landscapes research group</a>  |
<a href="https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/">Innovative Bio-Monitoring research group</a>  |
Contact: <a href="https://ecodiv.earth">Ecodiv.earth</a>
