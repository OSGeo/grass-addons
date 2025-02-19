<h2>DESCRIPTION</h2>
<em>r.green.gshp.technical</em> calculates the lenght of the borehole for Groud Source Heat Pump plants.

<h2>NOTES</h2>

The required inputs are the ground source conductivity and the ground loads.


<h2>EXAMPLES</h2>

<div class="code"><pre>python r.green.gshp.technical.py --overwrite ground_conductivity=g_conductivity ground_diffusivity_rast=g_diffusivity ground_temp_rast=g_temperature g_loads_6h_rast=g_loads_6h g_loads_1m_rast=g_loads_1m g_loads_1y_rast=g_loads_1y fluid_capacity=4000. fluid_massflow=0.074 fluid_inlettemp=4.44 bh_radius=0.054 pipe_inner_radius=0.01365 pipe_outer_radius=0.0167 bh_convection=1000. pipe_distance=0.0471 k_pipe=0.45 k_grout=1.73 field_distance=6.1 field_number=120 field_ratio=1.2 bhe_length=len_bhe bhe_field_length=len_bhe_field -d
</pre></div>


<h2>SEE ALSO</h2>
<em>
<a href="r.green.gshp.technical.html">r.green.gshp.technical</a>
</em>

<h2>AUTHOR</h2>

Pietro Zambelli (Eurac Research, Bolzano, Italy)
