<h2>DESCRIPTION</h2>

<em>i.zero2null</em> replaces zero cells with NULL cells at the edges
of imagery, e.g. Sentinel-2 scenes.

<p>
Sentinel-2 scenes can also have small patches of zero cells, typically
in water bodies. These patches are removed and filled with neighboring
cells.


<h2>EXAMPLE</h2>

The Sentinel-2 scene <tt>S2B_MSIL2A_20190724T103029_N0213_R108_T32ULA_20190724T130550,
uuid: 0a7cb5ee-80d4-4d15-be19-0b3fdf40791f</tt> shows unexpected no-data pixels
in lakes.

<div class="code"><pre>
# download S2 scene affected by no.data pixels within the scene
i.sentinel.download settings=credentials.txt \
  uuid=0a7cb5ee-80d4-4d15-be19-0b3fdf40791f output=test_s2_scene

# show lst of granules in scene
i.sentinel.import -p input=test_s2_scene

# import selected bands of scene
i.sentinel.import input=test_s2_scene pattern='B0(2|3|4|8)_10m'
g.list raster
g.region raster=T32ULA_20190724T103029_B04_10m -p
</pre></div>


<div align="center" style="margin: 10px">
<a href="i_zero2null_s2_uncorr.png">
<img src="i_zero2null_s2_uncorr.png" width="500" height="348" alt="i.zero2null example 1" border="0">
</a><br>
<i>Figure: Sentinel-2 red band with undesired 0-value pixels</i>
</div>

<div class="code"><pre>
# zoom to scene subset with undesired 0-value pixels
g.region n=5516940 s=5516840 w=334410 e=334550 res=10
# visualize pixel values, e.g. in red band
d.rast T32ULA_20190724T103029_B04_10m
d.rast.num T32ULA_20190724T103029_B04_10m text_color=blue

# fix 0-value pixels
i.zero2null map=T32ULA_20190724T103029_B02_10m,T32ULA_20190724T103029_B03_10m,T32ULA_20190724T103029_B04_10m,T32ULA_20190724T103029_B08_10m
# visualize updated pixel values (0 values now replaced), e.g. in red band
d.rast T32ULA_20190724T103029_B04_10m
d.rast.num T32ULA_20190724T103029_B04_10m text_color=blue
</pre></div>

<div align="center" style="margin: 10px">
<a href="i_zero2null_s2_corr.png">
<img src="i_zero2null_s2_corr.png" width="500" height="347" alt="i.zero2null example 2" border="0">
</a><br>
<i>Figure: Sentinel-2 red band after correction with <em>i.zero2null</em></i>
</div>


<h2>SEE ALSO</h2>

<em>
<a href="i.sentinel.html">i.sentinel</a> module set
</em>

<h2>AUTHOR</h2>

Markus Metz, mundialis
