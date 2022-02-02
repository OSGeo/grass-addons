<h2>DESCRIPTION</h2>

<em>i.nightlights.intercalibration</em> is a GRASS GIS module performing
inter-satellite calibration on DMSP-OLS nighttime lights time series.
Based on &quot;well known&quot; emprirical regression models, it
calibrates average visible band Digital Number values.

<h3>Overview</h3>

<div class="code"><pre>
+----------------------------------------------------------------------+
|                                                                      |
|          +-----------------+                                         |
| DNi +--> |Calibration Model| +--> Calibrated DN                      |
|          +---^-------------+            ^                            |
|              |                          |                            |
|              |             +--Evaluation+Methods-------------------+ |
|              |             |                                       | |
|              |             | ?                                     | |
|              |             |                                       | |
|              |             +---------------------------------------+ |
|                                                                    | |
| +--Regression+Models-----------------------------------------------+ |
| |                                                                  | |
| | Elvidge, 2009/2014: DNc = C0 + C1xDN + C2xDNv2                   | |
| |                                                                  | |
| | Liu,2012: based on Elvidge's model + optimal threshold method    | |
| |                                                                  | |
| | Wu, 2014:           DNc + 1 = ax(DN + 1)^b                       | |
| |                                                                  | |
| | Others?                                                          | |
| |                                                                  | |
| +------------------------------------------------------------------+ |
|                                                                      |
+----------------------------------------------------------------------+
</pre></div>

<h3>Details</h3>

From a review paper:

<blockquote>
<p>&quot;Several methods were proposed to overcome the lack of inter-satellite
calibration. These include the invariant region and the quadratic regression
method proposed by Elvidge et al. [23], the second-order regression and optimal
threshold method proposed by Liu et al. [24], and a power-law regression method
proposed by Wu et al. [25]. Although studies based on these calibration methods
showed performance improvement after the rectification [24,25], the assumption
that the nighttime light remains stable over time in a particular area requires
a careful choice of the invariant region manually.&quot; [Huang 2014]
</blockquote>

<p>References above are:

[23] [Elvidge 2009]
[24] [Liu 2012]
[25] [Wu 2013]

<h2>EXAMPLES</h2>

Given all maps are imported in GRASS' data base, which are:
<div class="code"><pre>
g.list rast pattern="F*"
F101992
F101993
F101994
F121994
F121995
F121996
F121997
F121998
F121999
F141997
F141998
F141999
F142000
F142001
F142002
F142003
F152000
F152001
F152002
F152003
F152004
F152005
F152006
F152007
F162004
F162005
F162006
F162007
F162008
F162009
F182010
F182011
F182012
</pre></div>

<p>the default inter-calibration, based on [Elvidge 2014], can be performed as:
<div class="code"><pre>
i.nightlights.intercalibration image=$(g.list rast pattern="F*" sep=comma) suffix=calib_elv
</pre></div>
<p>
<p>An improved inter-calibration model is based on [Wu 2013], can be performed
as:
<div class="code"><pre>
i.nightlights.intercalibration image=$(g.list rast pattern="F*stable_lights*" sep=comma) model=wu2013 suffix=calib_wu
</pre></div>

<h2>Remarks</h2>
<p>In case the calibration models do not include regression coefficients for all of the
yearly products, the module will fail and inform with an error message like:
<div class="code"><pre>
i.nightlights.intercalibration image=$(g.list rast pattern="F??????" sep=comma) model=liu2012 --v
... ValueError: The selected model does not know about this combination of
Satellite + Year!
</pre></div>

<h3>Example figures</h3>

<p>To be added...


<h2>TODO</h2>
<p>in general:
<ul>
<li>improve missing key handling and error reporting</li>
<li>code deduplication</li>
<li>test -- will it compile in other systems?</li>
</ul>
<p>in <code>i.nightlights.intercalibration.py</code>:
<ul>
<li>use <code>*args</code> or <code>**kwargs</code> where appropriate</li>
</ul>
<p>in <code>calibration_models.py</code>:
<ul>
<li>improve checks for missing combinations of Satellite + Year in models</li>
<li>separate test_function from this &quot;module&quot;</li>
</ul>
<p>another module?
<ul>
<li>Accuracy assessment of inter-calibrated nighttime lights time series [Wu
  2013]:
    <tt>TLI = SUMi DNi * Ci</tt> where DNi is the grey value of i-level pixels
    and Ci is the number of i-level pixels</li>
</ul>

<h2>REFERENCES</h2>
<p>Review paper
<ul>
<li>Huang, Q., Yang, X., Gao, B., Yang, Y., Zhao, Y., 2014. Application of DMSP/OLS Nighttime Light Images: A Meta-Analysis and a Systematic Literature Review. Remote Sensing 6, 6844-6866. https://doi.org/10.3390/rs6086844</li>
</ul>

<p>Empirical second order regression model by Elvidge, 2009 | Y = C0 + C1*X + C2*X^2</p>
<ul>
<li>Zhang, L., Qu, G., Wang, W., 2015. Estimating Land Development Time Lags in China Using DMSP/OLS Nighttime Light Image. Remote Sensing 7, 882-904. https://doi.org/10.3390/rs70100882</li>
<li>Elvidge, C.D., Hsu, F.-C., Baugh, K.E., Ghosh, T., 2014. National trends in satellite-observed lighting. Global urban monitoring and assessment through earth observation 23, 97-118.</li>
<li>Fan, J., Ma, T., Zhou, C., Zhou, Y., Xu, T., 2014. Comparative Estimation of Urban Development in China's Cities Using Socioeconomic and DMSP/OLS Night Light Data. Remote Sensing 6, 7840-7856. https://doi.org/10.3390/rs6087840</li>
<li>Shao, Z., Liu, C., 2014. The Integrated Use of DMSP-OLS Nighttime Light and MODIS Data for Monitoring Large-Scale Impervious Surface Dynamics: A Case Study in the Yangtze River Delta. Remote Sensing 6, 9359-9378. https://doi.org/10.3390/rs6109359</li>
<li>Xu, T., Ma, T., Zhou, C., Zhou, Y., 2014. Characterizing Spatio-Temporal Dynamics of Urbanization in China Using Time Series of DMSP/OLS Night Light Data. Remote Sensing 6, 7708-7731. https://doi.org/10.3390/rs6087708</li>
<li>Small, C., Elvidge, C.D., 2013. Night on Earth: Mapping decadal changes of anthropogenic night light in Asia. International Journal of Applied Earth Observation and Geoinformation, Spatial Statistics for Mapping the Environment 22, 40-52. https://doi.org/10.1016/j.jag.2012.02.009</li>
</ul>

<p>Second order regression model &amp; optimal threshold method by Liu, 2012
<ul>
<li>Liang, H., Tanikawa, H., Matsuno, Y., Dong, L., 2014. Modeling In-Use Steel Stock in China's Buildings and Civil Engineering Infrastructure Using Time-Series of DMSP/OLS Nighttime Lights. Remote Sensing 6, 4780-4800. https://doi.org/10.3390/rs6064780</li>
<li>Gao, B., Huang, Q., He, C., Ma, Q., 2015. Dynamics of Urbanization Levels in China from 1992 to 2012: Perspective from DMSP/OLS Nighttime Light Data. Remote Sensing 7, 1721-1735. https://doi.org/10.3390/rs70201721</li>
</ul>

<p>Non-linear, power regression model
<ul>
<li>Wu, J., He, S., Peng, J., Li, W., Zhong, X., 2013. Intercalibration of DMSP-OLS night-time light data by the invariant region method. International Journal of Remote Sensing 34, 7356-7368. https://doi.org/10.1080/01431161.2013.820365</li>
</ul>

<h2>AUTHOR</h2>

Nikos Alexandris
