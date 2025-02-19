<h2>DESCRIPTION</h2>

<em>i.sam2</em> allows users to segment orthoimagery based on text prompts using <a href="https://samgeo.gishub.org/">SamGeo</a>.

<h2>REQUIREMENTS</h2>

<ul>
    <li><a href="https://pillow.readthedocs.io/en/stable/">Pillow>=10.2.0</a></li>
    <li><a href="https://numpy.org/">numpy>=1.26.1</a></li>
    <li><a href="https://pytorch.org/">torch>=2.5.1</a></li>
    <li><a href="https://samgeo.gishub.org/">segment-geospatial>=0.12.3</a></li>
</ul>

<div class="code">
    <pre>
        pip install pillow numpy torch segment-geospatial
    </pre>
</div>

<h2>EXAMPLES</h2>

Segment orthoimagery using SamGeo2:

<div class="code">
    <pre>
    i.sam2 group=rgb_255 output=tree_mask text_prompt="trees"
    </pre>
</div>

<img src="./i_sam2_trees.jpg" height="600" alt="i.sam2 example" />

<h2>NOTES</h2>
The first time use will be longer as the model needs to be downloaded. Subsequent runs will be faster.
Additionally, Cuda is required for GPU acceleration. If you do not have a GPU, you can use the CPU by setting the environment variable `CUDA_VISIBLE_DEVICES` to `-1`.

<h2>REFERENCES</h2>
<ul>
<li>Wu, Q., & Osco, L. (2023). samgeo: A Python package for segmenting geospatial data with the Segment Anything Model (SAM). Journal of Open Source Software, 8(89), 5663. <a href="https://doi.org/10.21105/joss.05663">https://doi.org/10.21105/joss.05663</a></li>
<li>Osco, L. P., Wu, Q., de Lemos, E. L., Gonçalves, W. N., Ramos, A. P. M., Li, J., & Junior, J. M. (2023). The Segment Anything Model (SAM) for remote sensing applications: From zero to one shot. International Journal of Applied Earth Observation and Geoinformation, 124, 103540. <a href="https://doi.org/10.1016/j.jag.2023.103540">https://doi.org/10.1016/j.jag.2023.103540</a></li>
</ul>

<h2>SEE ALSO</h2>
<em>
    <a href="i.segment.gsoc.html">i.segment.gsoc</a> for region growing and merging segmentation,
    <a href="i.segment.hierarchical">i.segment.hierarchical</a> performs a hierarchical segmentation,
    <a href="i.superpixels.slic">i.superpixels.slic</a> for superpixel segmentation.
</em>

<h2>AUTHOR</h2>
Corey T. White (NCSU GeoForAll Lab & OpenPlains Inc.)
