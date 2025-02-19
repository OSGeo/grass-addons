<h2>DESCRIPTION</h2>
<em>r.slopeunits.metrics</em> creates metrics for slope units. Returns
output "areamin, cvmin, v_fin and i_fin" to stdout, optionally writes to a file.

<h2>NOTES</h2>

<h2>EXAMPLE</h2>

<div class="code"><pre>
r.slopeunits.metrics \
    basin=basin_chk \
    demmap=dem_italia_isolegrandi@su_test \
    slumapclean=su_tmp_cl \
    cleansize=25000 \
    areamin=50000.0 \
    cvmin=0.05 \
    resolution=625 \
    outfile=objf_1.dat
</pre></div>

<h2>SEE ALSO</h2>
<em>
    <a href="r.slopeunits.create.html">r.slopeunits.create</a>,
    <a href="r.slopeunits.clean.html">r.slopeunits.clean</a>,
    <a href="r.slopeunits.optimize.html">r.slopeunits.optimize</a>
</em>

<h2>AUTHORS</h2>
Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI
<br>
Carmen Tawalika (translation to python), <a href="https://www.mundialis.de/">mundialis</a>
