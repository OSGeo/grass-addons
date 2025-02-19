<h2>DESCRIPTION</h2>
<em>r.slopeunits.clean</em> cleans slope units layer, e.g. results of <em>r.slopeunits.create</em>.

<h2>NOTES</h2>

<h2>EXAMPLE</h2>

<div class="code"><pre>
r.slopeunits.clean \
    demmap=dem_italia_isolegrandi@su_test \
    plainsmap=flat \
    slumap=su_tmp \
    slumapclean=su_tmp_cl \
    cleansize=25000 \
    -m
</pre></div>

<h2>SEE ALSO</h2>
<em>
    <a href="r.slopeunits.create.html">r.slopeunits.create</a>,
    <a href="r.slopeunits.metrics.html">r.slopeunits.metrics</a>,
    <a href="r.slopeunits.optimize.html">r.slopeunits.optimize</a>
</em>

<h2>AUTHORS</h2>
Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI
<br>
Markus Metz (refactoring, translation of "clean_method_3" to python), Carmen Tawalika (creation of extra addon), <a href="https://www.mundialis.de/">mundialis</a>
