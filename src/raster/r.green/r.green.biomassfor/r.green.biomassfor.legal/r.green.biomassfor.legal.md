<h2>DESCRIPTION</h2>

Compute the legal biomass forestry residual potential, based on the annual/periodic forest yield.

<h2>NOTES</h2>
This module permits to evalute the maximum bio-energy from forest residual available in a particular area, on the base of the prescribed yield. The mandatory data input are a vector file with fields with values of yield, management, treatment, and forest surface. The yield value is expressed in cubic meters, the forest surface in hectares, the management is an integer value that can be 1 for high forest and 2 for coppice, the treatment is an integer field that can be 1 for final felling and 2 for thinning. The energy section contains the calorific parameters that permits to convert the biomass in energy. The output maps are expressed in Mwh.

<h2>EXAMPLE</h2>
This example shows a typical input vector file with a table composed by fields of increment, forest surface, management and treatment. This example is based on data of Maè Valley, one of the test area of the R.green project<br><br>
<center><img src="legal_input.png" alt="input" ></center><br><br>
<table border="1" align="center" cellpadding="5">
	<tr>
		<td>yield</td><td>surface</td><td>management</td><td>treatment</td>
	</tr>
	<tr>
		<td>35.87</td><td>800</td><td>1</td><td>1</td>
	</tr>
		<tr>
		<td>16.48</td><td>700</td><td>1</td><td>2</td>
	</tr>
	<tr>
		<td>24.82</td><td>300</td><td>2</td><td>1</td>
	</tr>
</table><br>
<div class="code">
<pre>r.green.biomassfor.legal --overwrite forest=forest@biomasfor boundaries=Boundary@biomasfor forest_column_yield=yield forest_column_yield_surface=surface forest_column_management=management forest_column_treatment=treatment energy_tops_hs=0.49 energy_cormometric_vol_hf=1.97 energy_tops_cops=0.55 output_basename=mae</pre>
</div>
<center><img src="legal_output.png" alt="output"></center><br><br>
The output map is a standardize energy map with the pixel value equal to the corresponding bioenergy stimated.

<h2>REFERENCE</h2>
Sacchelli, S., Zambelli, P., Zatelli, P., Ciolli, M., 2013. Biomasfor - an open-source holistic model for the assessment of sustainable forest bioenergy. iFor. Biogeosci. For. 6, 285-293

<h2>SEE ALSO</h2>
<em>
  <a href="r.green.biomassfor.theoretical.html">r.green.biomassfor.theoretical</a>,
  <a href="r.green.biomassfor.technical.html">r.green.biomassfor.technical</a>
</em>

<h2>AUTHORS</h2>

Francesco Geri,
Pietro Zambelli,
Sandro Sacchelli,
Marco Ciolli
