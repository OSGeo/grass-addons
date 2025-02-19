<h2>DESCRIPTION</h2>
<em>r.in.usgs</em> downloads and patches selected USGS datasets (NED, NAIP, lidar) to
the current GRASS computational region and coordinate reference system.
Associated parameters are automatically passed to
<a href="https://viewer.nationalmap.gov/tnmaccess/api/index">
The National Map Access API</a>, downloaded to a local cache directory,
then imported, and patched together.

<em>r.in.usgs</em> supports the following datasets:
<ul>
<li><b>ned</b>: National Elevation Dataset</li>
<li><b>naip</b>: NAIP orthoimagery</li>
<li><b>lidar</b>: Lidar Point Clouds (LPC)</li>
</ul>

National Land Cover Dataset (NLCD) is no longer available through the API.

<h2>NOTES</h2>
<p>
NED data are available at resolutions of 1 arc-second (about 30 meters),
1/3 arc-second (about 10 meters), and in limited areas at 1/9 arc-second (about 3 meters).

<p>
NAIP is available at 1 m resolution.

<p>
Lidar data is available only for part of the US but there can be multiple
spatially overlapping datasets from different years. All point clouds
will be imported as points using <a href="https://grass.osgeo.org/grass-stable/manuals/v.in.pdal.html">v.in.pdal</a>
and then patched and interpolated with <a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html">v.surf.rst</a>.
In some cases, lidar point clouds do not have SRS information, use <b>input_srs</b>
to specify it (e.g. "EPSG:2264"). If multiple tiles from different years
are available, use <b>title_filter</b> to filter by their titles (e.g. "Phase1").
Use <b>i</b> flag to list the tiles first.

<p>
If the <b>i</b> flag is set, only information about data meeting the input parameters
is displayed without downloading the data.
If the <b>d</b> flag is set, data is downloaded but not imported and processed.

<p>
By default, downloaded files are kept in a user cache directory according to
the operating system standards.
These files can be reused in case a different, but overlapping, computational
region is required.
However, unzipped files and imported rasters before patching are removed.
If the <b>k</b> flag is set, extracted files from compressed archives are also kept within the
cache directory after the import.
The location of the cache directory depends on the operating system.
You can clear the cache by deleting the directory.
Where this directory is depends on operating system,
for example on Linux, it is under <code>~/.cache</code>,
on macOS under <code>~/Library/Caches</code>,
and on Microsoft Windows under the Application Data directory.
If you have limited space or other special needs, you can set
<b>output_directory</b> to a custom directory,
e.g., <code>/tmp</code> on Linux.
The custom directory needs to exist before calling this module.

<p>
By default, resampling method is chosen based on the nature of the dataset,
bilinear for NED and nearest for NAIP. This can be changed with option
<b>resampling_method</b>.

<h2>EXAMPLE</h2>
We will download NED 1/9 arc-second digital elevation model in the extent of raster 'elevation'.
First, we just list the files to be downloaded:
<div class="code"><pre>
g.region raster=elevation
r.in.usgs product=ned ned_dataset=ned19sec output_name=ned -i
</pre></div>
<pre>
USGS file(s) to download:
-------------------------
Total download size:	826.95 MB
Tile count:	4
USGS SRS:	wgs84
USGS tile titles:
USGS NED ned19_n35x75_w078x75_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
USGS NED ned19_n36x00_w078x75_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
USGS NED ned19_n35x75_w079x00_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
USGS NED ned19_n36x00_w079x00_nc_statewide_2003 1/9 arc-second 2012 15 x 15 minute IMG
-------------------------
To download USGS data, remove i flag, and rerun r.in.usgs.
</pre>

We proceed with the download:
<div class="code"><pre>
r.in.usgs product=ned ned_dataset=ned19sec output_name=ned
r.colors map=ned_small color=grey
</pre></div>

We change the computational region to a smaller extent and create a new DEM,
downloaded files will be used.
<div class="code"><pre>
g.region n=224649 s=222000 w=633000 e=636000
r.in.usgs product=ned ned_dataset=ned19sec output_name=ned_small
</pre></div>

For a different extent we download NAIP imagery and we use a custom cache directory
(replace <code>/tmp</code> by an existing path suitable
for your operating system and needs):
<div class="code"><pre>
g.region n=224649 s=222000 w=636000 e=639000
r.in.usgs product=naip output_directory=/tmp output_name=ortho
</pre></div>

<div align="center" style="margin: 10px">
<a href="r_in_usgs.png">
<img src="r_in_usgs.png" width="600" height="600" alt="NED and ortho" border="0">
</a><br>
<i>Figure: Downloaded NED (large and small extent), NAIP orthoimagery,
and NLCD land cover (NLCD is not available since 2020 through the API)</i>
</div>



<h2>REFERENCES</h2>
<em>
<a href="https://viewer.nationalmap.gov/help/documents/TNMAccessAPIDocumentation/TNMAccessAPIDocumentation.pdf">TNM Access API Guide</a><br>
<a href="https://nationalmap.gov/elevation.html">National Elevation Dataset</a><br>
<a href="https://www.mrlc.gov/">National Land Cover Dataset</a>
</em>

<h2>SEE ALSO</h2>
<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/g.region.html">g.region</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.import.html">r.import</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.patch.html">r.patch</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.colors.html">r.colors</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.in.srtm.html">r.in.srtm</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.in.pdal.html">v.in.pdal</a>
</em>

<h2>AUTHORS</h2>

Zechariah Krautwurst, 2017 MGIST Candidate, North Carolina State University<br>
(initial version, Google Summer of Code 2017, mentors: Anna Petrasova, Vaclav Petras)

<p>
Anna Petrasova, <a href="https://geospatial.ncsu.edu/geoforall/">NCSU GeoForAll Lab</a><br>
Vaclav Petras, <a href="https://geospatial.ncsu.edu/geoforall/">NCSU GeoForAll Lab</a><br>
