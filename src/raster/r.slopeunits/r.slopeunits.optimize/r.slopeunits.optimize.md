<h2>DESCRIPTION</h2>
<em>r.slopeunits.optimize</em> determines optimal input values for slope units:
<ul>
<li>
"areamin" - Minimum area (m^2) below which the slope unit is not further segmented
</li>
<li>
"cvmin" - Minimum value of the circular variance (0.0-1.0) below which the slope unit is not further segmented
</li>
</ul>
It calls <em>r.slopeunits.create</em>, <em>r.slopeunits.clean</em> and <em>r.slopeunits.metrics</em> iteratively.
Output is a file <tt>opt.txt</tt> with optimal values in either specified folder or in folder <tt>output/</tt>"
in the current working directory. Also files <tt>calcd.dat</tt> and <tt>current.txt</tt> are created with
all determined and examined values and the four latest examined values (combination of <tt>areamin<tt>
and <tt>cvmin<tt> minimum and maximum) and <tt>center</tt> respectively.

<h2>NOTES</h2>

<h2>EXAMPLE</h2>

<div class="code"><pre>
r.slopeunits.optimize \
    basin=basin_chk \
    demmap=dem_italia_isolegrandi@su_test \
    plainsmap=flat \
    thresh=250000 \
    rf=2 \
    maxiteration=50 \
    cleansize=25000
</pre></div>

<h2>SEE ALSO</h2>
<em>
    <a href="r.slopeunits.create.html">r.slopeunits.create</a>,
    <a href="r.slopeunits.clean.html">r.slopeunits.clean</a>,
    <a href="r.slopeunits.metrics.html">r.slopeunits.metrics</a>
</em>

<h2>AUTHORS</h2>
Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI
<br>
Carmen Tawalika (translation to python, refactoring), <a href="https://www.mundialis.de/">mundialis</a>
