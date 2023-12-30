<h2>DESCRIPTION</h2>

<em>r.series.decompose</em> is a module to calculate decomposintion of signal X.
<div class="code"><pre>
X(t) = B0 + B1*t + B2*sin(B1*t) + B3 * cos(B1*t) + ... + B{n-1}*sin(Bk*t) + Bn * cos(Bk*t) + e
</pre></div>
<p>
where <em>X</em> is a raster time series, <em>t</em> is time (<em>t</em>
in <em>[0, pi]</em>), <em>sin(Fi*t)</em> and <em>cos(Fi*t)</em> are time
variables; <em>Fi</em> are user specifed frequencies; <em>e</em> is a error.
<p>
The module used r.mregression.series to find the regression coefficients
<em>Bi</em>, then it produces the fitted rasters series <em>X(t)</em>
using the coefficients.
<p>
So the module makes each output cell value a function of the values
assigned to the corresponding cells in the time variable raster map series
and the rasters of the coefficients.

<p>
<em>input</em>   Raster names of equally spaced time series <em>X</em>
<p>
<em>result_prefix</em> Prefix for raster names of filterd <em>X(t)</em>
<p>
<em>coef_prefix</em>   Prefix for names of result raster
	(rasters of coefficients)
<p>
<em>timevar_prefix</em>   Prefix for names of result raster
	(rasters of time variables)
<p>
<em>freq</em>   List of frequencies for sin and cos functions
<p>


<h2>NOTES</h2>

<em>X</em> must be equally spaced time serie. If the serie isn't equally
spaced, insert NULL raster maps into <em>X</em>.
<p>
The list of inputs for each cell (including NULLs) is passed to the
regression function. The functin compute the parameters over the
non-NULL values, producing a NULL result only if there aren't enough
non-NULL values for computing.

The regression coefficients <em>Bi</em> are stored in raster maps.
They can be used for construct more detail time series via the equation:
<div class="code"><pre>
X(t) = B0 + B1*t + B2*sin(B1*t) + B3 * cos(B1*t) + ... + B{n-1}*sin(Bk*t) + Bn * cos(Bk*t) + e
</pre></div>
<p>
To do that the user have to create time variables (<em>t</em>,
<em>sin(Fi*t)</em> and <em>cos(Fi*t)</em>) at desired time <em>T0</em>
and then use r.mapcalc to produce the <em>X(T0)</em>.

<p>
The maximum number of raster maps to be processed is limited by the
operating system. For example, both the hard and soft limits are
typically 1024. The soft limit can be changed with e.g. <tt>ulimit -n
1500</tt> (UNIX-based operating systems) but not higher than the hard
limit. If it is too low, you can as superuser add an entry in

<div class="code"><pre>
/etc/security/limits.conf
# &lt;domain&gt;      &lt;type&gt;  &lt;item&gt;         &lt;value&gt;
your_username  hard    nofile          1500
</pre></div>

This would raise the hard limit to 1500 file. Be warned that more
files open need more RAM.


<h2>EXAMPLES</h2>
Suppose we have time series of MODIS NDVI data (from 01 jan to 27 dec):
<pre>
> g.mlist rast pattern="mod*", separator=','
mod2003_01_01,mod2003_01_09,...,mod2003_12_27
</pre>
<p>
We use one year data, so we suppose the there is a half of sinusoid signal
in the data (NDVI values icrease, then decrease usualy). So 01 jan is t0==0,
27 dec is tn==2*pi, there is a frequence 0.5 in the data (and there are more
frequencies, for example 1.0 and 1.5).
<p>
Decompose the signal:
<pre>
> maps = $(g.list rast pattern="mod*", separator=',')
> r.series.decompose input=$maps coef_prefix="coef." \
	timevar_prefix="dec." result_pref="res." \
	freq=0.5,1.0,1.5
</pre>
<p>
The command creates rasters of the coefficiens <em>coef.*</em>:
<pre>
coef.const
coef.time
coef.sin_fr0.5
coef.cos_fr0.5
coef.sin_fr1.0
coef.cos_fr1.0
coef.cos_fr1.5
coef.sin_fr1.5
</pre>
and rasters of fitted NDVI <em>res.*</em>:
<pre>
res.mod2003_01_01
res.mod2003_01_09
...
</pre>
<p>
To compute NDVI for 03 jan we need: (1) find time <em>T</em> for 03 jan
(2) create time variables for 02 jan.
<p>
The length (in days) of the NDVI time series is 362, 03 jan
is the third day of the series, so <em>T</em> = <em>3 * (2*pi/362)</em>
radians. But r.mapcalc uses degrees for <em>sin()</em> and <em>cos()</em>
functions. So <em>T</em> = <em>3 * 360/362</em> degrees.
<p>
Create time variables:
<pre>
r.mapcalc "T = 3.0 * 360.0/362.0"
r.mapcalc "sin0.5 = sin(0.5*3.0*360.0/362.0)"
r.mapcalc "cos0.5 = cos(0.5*3.0*360.0/362.0)"
r.mapcalc "sin1 = sin(3.0*360.0/362.0)"
r.mapcalc "cos1 = cos(3.0*360.0/362.0)"
r.mapcalc "sin1.5 = sin(1.5*3.0*360.0/362.0)"
r.mapcalc "cos1.5 = cos(1.5*3.0*360.0/362.0)"
</pre>
<p>
Create NDVI for 03 jan:
<pre>
r.mapcals "ndvi03jan = coef.const + coef.time*T +\
	coef.sin_fr0.5*sin0.4 + coef.cos_fr0.5*cos0.5 +\
	coef.sin_fr1.0*sin1 + coef.cos_fr1.0*cos1 +\
	coef.sin_fr1.5*sin1.5 + coef.cos_fr1.5*cos1.5"
</pre>

<h2>SEE ALSO</h2>

<em><a href="addons/r.mregression.series.html">r.regression.series</a></em>,
<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.series.html">r.series</a></em>,
<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.regression.line.html">r.regression.line</a></em>,
<em><a href="https://grass.osgeo.org/grass-stable/manuals/g.list.html">g.list</a></em>,

<h2>AUTHOR</h2>

Dmitry Kolesov
