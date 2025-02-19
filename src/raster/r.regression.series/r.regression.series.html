<h2>DESCRIPTION</h2>

<em>r.regression.series</em> is a module to calculate linear
regression parameters between two time series, e.g. NDVI and
precipitation.
<p>
The module makes each output cell value a function of the values
assigned to the corresponding cells in the two input raster map series.
Following methods are available:

<ul>
 <li>offset: Linear regression offset
 <li>slope: Linear regression slope
 <li>corcoef: Correlation Coefficent R
 <li>rsq: Coefficient of determination = R squared
 <li>adjrsq: Adjusted coefficient of determination
 <li>f: F statistic
 <li>t: T statistic
 </ul>

<h2>DESCRIPTION</h2>

The module assumes a simple linear regression of the form
<div class="code"><pre>
    y = a + b * x
</pre></div>
<p>
<em>offset</em> is equivalent to <em>a</em> in the above equation, also
referred to as constant or intercept.
<p>
<em>slope</em> is equivalent to <em>b</em> in the above equation.
<p>
<em>corcoef</em> is the correlation coefficient R with a theoretical
range of -1,1.
<p>
<em>rsq</em> is the coefficient of determination, equivalent to
the squared correlation coefficient R<sup>2</sup>.
<p>
<em>adjrsq</em> is the coefficient of determination adjusted for the
number of samples, i.e. number of input maps per series.
<p>
<em>f</em> is the value of the F statistic.
<p>
<em>t</em> is the value of the T statistic.

<h2>NOTES</h2>

The number of maps in <em>xseries</em> and <em>yseries</em> must be
identical.
<p>
With <em>-n</em> flag, any cell for which any of the corresponding input cells are
NULL is automatically set to NULL (NULL propagation). The aggregate function is not
called, so all methods behave this way with respect to the <em>-n</em> flag.
<p>
Without <em>-n</em> flag, the complete list of inputs for each cell
(including NULLs) is passed to the function. Individual functions can
handle data as they choose. Mostly, they just compute the parameter
over the non-NULL values, producing a NULL result only if all inputs
are NULL.
<p>
Linear regression (slope, offset, coefficient of determination) requires
an equal number of <em>xseries</em> and <em>yseries</em> maps.
If the different time series have irregular time intervals, NULL raster
maps can be inserted into time series to make time intervals equal (see example).
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

Using <em>r.regression.series</em> with wildcards:
<br>
<div class="code"><pre>
r.regression.series xseries="`g.list pattern='insitu_data.*' sep=,`" \
	 yseries="`g.list pattern='invivo_data.*' sep=,`" \
         output=insitu_data.rsquared method=rsq
</pre></div>
<p>
Note the <em>g.list</em> module also supports regular expressions for
selecting map names.

<p>
Example for multiple parameters to be computed in one run (3 resulting
parameters from 8 input maps, 4 maps per time series):
<div class="code"><pre>
r.regression.series x=xone,xtwo,xthree,xfour y=yone,ytwo,ythree,yfour \
    out=res_offset,res_slope,res_adjrsq meth=offset,slope,adjrsq
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/g.list.html">g.list</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/g.region.html">g.region</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.series.html">r.series</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.regression.line.html">r.regression.line</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.regression.multi.html">r.regression.multi</a>
</em>

<h2>AUTHOR</h2>

Markus Metz
