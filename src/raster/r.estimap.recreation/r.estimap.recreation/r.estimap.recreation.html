<h2>DESCRIPTION</h2>

<em>r.estimap.recreation</em>
is an implementation of the ESTIMAP recreation algorithm
to support mapping and modelling of ecosystem services
(Zulian, 2014).

<p>
The algorithm
estimates the capacity of ecosystems to provide opportunities
for nature-based recreation
and leisure
(recreation opportunity spectrum).

First,
it bases upon look-up tables,
to score access to or the quality
of natural features
(land suitability, protected areas, infrastructure, water resources)
for their potential to support for outdoor recreation
(potential recreation).

Second,
it implements a proximity-remoteness concept
to integrate
the recreation potential
and the existing infrastructure.


<p>
The module offers two functionalities.

One is the production of recreation related maps by using pre-processed maps
that depict the quality of or the access to areas of recreational value.
The other is to transform maps that depict natural features into scored maps
that reflect the potential to support for outdoor recreational.

<em>Nevertheless, it is strongly advised to understand first the concepts and
  the terminology behind the algorithm, by reading the related sources.</em>


<h3>Terminology</h3>

First, an overview of definitions:

<dl>
  <dt> Recreation Potential</dt>
  <dd> is the potential of the ecosystems to offer recreation opportunities. It
  depends on the properties and conditions of an ecosystem.
  The recreation potential map,
  derives by adding and normalizing
  maps of natural <i>components</i>
  that may provide recreation opportunities.</dd>

  <dt> Recreation Demand</dt>
  <dd> is the number of households using a recreation service. By definition,
  population data are required in order to quantify the demand. </dd>

  <dt> Recreation (Opportunity) Spectrum</dt>
  <dd> also mentioned as <strong>ROS</strong>, is the range of recreation
  opportunities categorized by their distance to roads and residential areas.
  It derives by combining the recreation potential
  and maps that depict access (i.e. infrastructure) and/or
  areas that provide opportunities for recreational activities.

  <p>
  An important category is the one with the <em>Highest Recreation Spectrum</em>.
  It includes areas of very high recreational value which, at the same time,
  are very near to access.

  <div class="tg-wrap"><table>
      <tr>
        <th>Potential | Opportunity</th>
        <th>Near</th>
        <th>Midrange</th>
        <th>Far</th>
      </tr>
      <tr>
        <td>Near</td>
        <td>1</td>
        <td>2</td>
        <td>3</td>
      </tr>
      <tr>
        <td>Midrange</td>
        <td>4</td>
        <td>5</td>
        <td>6</td>
      </tr>
      <tr>
        <td>Far</td>
        <td>7</td>
        <td>8</td>
        <td>9</td>
      </tr>
    </table></div>
  </dd>

  <dt> Met Demand</dt>
  <dd> is the part of the population that has access to <em>high quality areas
    for daily recreation</em> (population that lives within 4km from areas of
  high recreational value.</dd>

  <dt> Unmet Demand</dt>
  <dd> is the part of the population whose access to <em>high
    quality areas for daily recreation</em> is not guaranteed (population that
  lives beyond 4km from areas of high recreational value.</dd>

  <dt> Actual Flow</dt>
  <dd> is the spatial relationship between potential and demand. In the case of
  recreation services, the <em>flow</em> is the number of visits in the areas
  of interest for daily recreation. </dd>

  <dt> The supply table</dt>
  <dd> presents the contribution of each ecosystem type to the actual flow of
  outdoor recreation as measured by the number of potential visits to areas for
  daily recreation per year.</dd>

  <dt> The Use table</dt>
  <dd> presents the allocation of the service flow to the users (inhabitants). </dd>
</dl>

<h3>Mathematical Background</h3>

<p>
The following equation represents the logic behind ESTIMAP:
<pre>
Recreation <strong>Spectrum</strong> = Recreation <strong>Potential</strong> + Recreation <strong>Opportunity</strong>
</pre>

<h5>Remoteness and Proximity</h5>

The base
<em>distance</em>
function
to quantify
<em>attractiveness</em>, is:

<div class="code"><pre>
( {Constant} + {Kappa} ) / ( {Kappa} + exp({alpha} * {Variable}) )
</pre></div>

where

<ul>
  <li>Constant</li>
  <li>Coefficients
    <ul>
      <li>Kappa</li>
      <li>Alpha</li>
    </ul>
  </li>
  <li>Variable</li>
</ul>


<h5>Normalization</h5>

As part of the algorithm,
each <em>component</em> is normalized.

That is,
all maps listed in a given component
are summed up and normalised.
Normalizing any raster map,
be it a single map
or the sum of a series of maps,
is performed by
subtracting its minimum value
and dividing by its range.

<h2>EXAMPLES</h2>
<p>For the sake of demonstrating the usage of the module, we use the following
<em>component</em> maps to derive a recreation <em>potential</em> map:

<ul>
  <li><code>input_area_of_interest</code></li>
  <li><code>input_land_suitability</code></li>
  <li><code>input_water_resources</code></li>
  <li><code>input_protected_areas</code></li>
</ul>
<div>
  <p float="center">
  <img alt="Area of interest" src="images/r_estimap_recreation_area_of_interest.png" width="190" >
  <img alt="Land suitability" src="images/r_estimap_recreation_land_suitability.png" width="190" >
  <img alt="Water resources"  src="images/r_estimap_recreation_water_resources.png"  width="190" >
  <img alt="Protected areas"  src="images/r_estimap_recreation_protected_areas.png"  width="190" >
  </p>
</div>

<p>
The maps shown above are available to download, among other sample maps, at: https://gitlab.com/natcapes/r.estimap.recreation.data.

<p>
Note, the prefix <code>input_</code> in front of all maps is purposive in order to make the examples easier to understand. Similarly, all output maps and files will be prefixed with the string <code>output_</code>.

<p>
Below,
a table overviewing
all input and output maps
used or produced in the examples.

<p>
<div class="tg-wrap"><table>
  <tr>
    <th></th>
    <th>Input map name</th>
    <th>Spatial Resolution</th>
    <th>Remarks</th>
  </tr>
  <tr>
    <td></td>
    <td>area_of_interest</td>
    <td>50 m</td>
    <td>A map that can be used as a 'mask'</td>
  </tr>
  <tr>
    <td></td>
    <td>land_suitability</td>
    <td>50 m</td>
    <td>A map scoring the potential for recreation over CORINE land classes</td>
  </tr>
  <tr>
    <td></td>
    <td>water_resources</td>
    <td>50 m</td>
    <td>A map scoring access to water resources</td>
  </tr>
  <tr>
    <td></td>
    <td>protected_areas</td>
    <td>50 m</td>
    <td>A map scoring the recreational value of natural protected areas</td>
  </tr>
  <tr>
    <td></td>
    <td>distance_to_infrastructure</td>
    <td>50 m</td>
    <td>A map scoring access to infrastructure</td>
  </tr>
  <tr>
    <td></td>
    <td>population_2015</td>
    <td>1000 m</td>
    <td>The resolution of the raster map given to the 'populatio' input option
      will define the resolution of the output maps 'demand', 'unmet' and
      'flow'</td>
  </tr>
  <tr>
    <td></td>
    <td>local_administrative_unit</td>
    <td>50 m</td>
    <td>A rasterised version of Eurostat's Local Administrative Units map</td>
  </tr>
  <tr>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <th>Output map name</th>
    <th>Spatial Resolution</th>
    <th>Remarks</th>
  </tr>
  <tr>
    <td></td>
    <td>potential<br></td>
    <td>50 m</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td>potential_1</td>
    <td>50 m</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td>potential_2</td>
    <td>50 m</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td>potential_3</td>
    <td>50 m</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td>potential_4</td>
    <td>50 m</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td>spectrum</td>
    <td>50 m</td>
    <td></td>
  </tr>
  <tr>
    <td></td>
    <td>opportunity</td>
    <td>50 m</td>
    <td>Requires to request for the 'spectrum' output</td>
  </tr>
  <tr>
    <td></td>
    <td>demand</td>
    <td>1000 m</td>
    <td>Depends on the 'flow' map which, in turn, depends on the 'population' input map</td>
  </tr>
  <tr>
    <td></td>
    <td>unmet</td>
    <td>1000 m</td>
    <td>Depends on the 'flow' map which, in turn, depends on the 'population' input map<br></td>
  </tr>
  <tr>
    <td></td>
    <td>flow</td>
    <td>1000 m</td>
    <td>Depends on the 'population' input map</td>
  </tr>
  <tr>
    <td></td>
    <th>Output table name</th>
    <th></th>
    <th></th>
  </tr>
  <tr>
    <td></td>
    <td>supply</td>
    <td>NA</td>
    <td></td>
  </tr>
</table></div>

<p>
Before anything, we need to define the extent of interest by executing
<div class="code"><pre>
  g.region  raster=input_area_of_interest  -p
</pre></div>

  which returns

  <div class="code"><pre>
  projection: 99 (ETRS89 / LAEA Europe)
  zone:       0
  datum:      etrs89
  ellipsoid:  grs80
  north:      2879700
  south:      2748850
  west:       4735600
  east:       4854650
  nsres:      50
  ewres:      50
  rows:       2617
  cols:       2381
  cells:      6231077
  </pre></div>

  <h3 id="using-pre-processed-maps">Using pre-processed maps</h3>
  <p>
  The first four input options of the module, are designed to receive
  pre-processed input maps that classify as either <code>land</code>,
  <code>natural</code>, <code>water</code>, and <code>infrastructure</code>
  resources that add to the recreational value of the area.
  <em>Pro-processing</em> means here to derive a map that scores the given
  resources, in the context of recreation and the ESTIMAP algorithm.

  <h4 id="potential">Potential</h4>
  <p>
  To produce a recreation <em>potential</em> map, the simplest command requires
  the user to define the input map option <code>land</code> and name the output
  map via the option <code>potential</code>. Using a pre-processed map that
  depicts the suitability of different land types to support for recreation
  (here the map named <code>land_suitability</code>), the command to execute
  is:
  <div class="code"><pre>
    r.estimap.recreation  land=input_land_suitability  potential=output_potential
  </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_potential.png" alt="Example of a recreation potential output map" >
    <p class="caption">Example of a recreation potential output map</p>
  </div>

  <p>
  Note, this will process the map <code>input_land_suitability</code> over the
  extent defined previously via <code>g.region</code>, which is the standard
  behaviour in GRASS GIS.
  <p>
  To exclude certain areas from the computations, we may use a raster map as a
  mask and feed it to the input option <code>mask</code>:

  <div class="code"><pre>
    r.estimap.recreation  land=input_land_suitability  mask=input_area_of_interest  potential=output_potential_1
    </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_potential_1.png" alt="Example of a recreation potential output map while using a MASK" >
    <p class="caption">Example of a recreation potential output map while using a MASK</p>
  </div>

  <p>
  The use of a mask (in GRASS GIS' terminology known as <strong>MASK</strong>)
  will ignore areas of <strong>No Data</strong> (pixels in the
  <code>area_of_interest</code> map assigned the NULL value). Successively,
  these areas will be empty in the output map <code>output_potential_1</code>.
  Actually, the same effect can be achieved by using GRASS GIS' native mask
  creation module <code>r.mask</code> and feed it with a raster map of
  interest. The result will be a raster map named <strong>MASK</strong> whose
  presence acts as a filter. In the following examples, it becomes obvious that
  if a single input map features such <strong>No Data</strong> areas, they will
  be propagated in the output map.

  <p>
  Nonetheless, it is good practice to use a <code>MASK</code> when one needs to
  ensure the exclusion of undesired areas from any computations. Note also the
  <code>--o</code> flag: it is required to overwrite the already existing map
  named <code>potential_1</code>.

  <p>
  Next, we add in the water component a map named <code>water_resources</code>,
  we modify the output map name to <code>potential_2</code> and execute the new
  command without a mask:

  <div class="code"><pre>
    r.estimap.recreation  land=input_land_suitability  water=input_water_resources  potential=output_potential_2
    </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_potential_2.png" alt="Example of a recreation potential output map while using a MASK, a land suitability map and a water resources map" >
    <p class="caption">Example of a recreation potential output map while using a MASK, a land suitability map and a water resources map</p>
  </div>

  <p>
  At this point it becomes clear that all <code>NULL</code> cells present in
  the water map, are propagated in the output map
  <code>output_potential_2</code>.
  <p>
  Following, we provide a map of protected areas named
  <code>input_protected_areas</code>, we modify the output map name to
  <code>output_potential_3</code> and execute the updated command:

  <div class="code"><pre>
    r.estimap.recreation  land=input_land_suitability  water=input_water_resources  natural=input_protected_areas  potential=output_potential_3
    </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_potential_3.png" alt="Example of a recreation potential output map while using a MASK, a land suitability map, a water resources map and a natural resources map" >
    <p class="caption">Example of a recreation potential output map while using a MASK, a land suitability map, a water resources map and a natural resources map</p>
  </div>

  <p>
  While the <code>land</code> option accepts only one map as an input, both the
  <code>water</code> and the <code>natural</code> options accept multiple maps
  as inputs. For example, we add a second map named
  <code>input_bathing_water_quality</code> to the <em>water</em> component and
  modify the output map name to <code>output_potential_4</code>:

  <div class="code"><pre>
    r.estimap.recreation  land=input_land_suitability  water=input_water_resources,input_bathing_water_quality  natural=input_protected_areas  potential=output_potential_4
  </pre></div>

  <p>
  In general, arbitrary number of maps, separated by comma, may be added to
  options that accept multiple inputs.

  <div class="figure">
    <img src="images/r_estimap_recreation_potential_4.png" alt="Example of a recreation potential output map while using a MASK, a land suitability map, two water resources maps and a natural resources map" >
    <p class="caption">Example of a recreation potential output map while using a MASK, a land suitability map, two water resources maps and a natural resources map</p>
  </div>

  <p>
  This example, features also a title and a legend, so as to make sense of the
  map (however, we will skip for now important cartographic elements).
  <div class="code"><pre>
    d.rast  output_potential_4
    d.legend  -c  -b  output_potential_4  at=0,15,0,1  border_color=white
    d.text  text="Potential"  bgcolor=white
  </pre></div>

  <p>
  The different output map names are purposefully selected so as to enable a
  visual comparison of the differences among the differenct examples. The
  output maps <code>output_potential_1</code>, <code>output_potential_2</code>,
  <code>output_potential_3</code> and <code>output_potential_4</code>, range
  within [0,3]. Yet, they differ in the distribution of values due to the
  different set of input maps.

  <p>
  <strong> All of the above examples base upon pre-processed maps that score the
  access to and quality of land, water and natural resources. For using
  <em>raw</em>, unprocessed maps, read section <em>Using unprocessed
  maps</em>. </strong>

  <p>
  We can remove all of the <em>potential</em> maps via

  <div class="code"><pre>
    g.remove raster pattern=output_potential* -f
  </pre></div>

  <h4 id="spectrum">Spectrum</h4>

  <p>
  To derive a map with the recreation (opportunity) <code>spectrum</code>, we
  need in addition an <code>infrastructure</code> component. In this example a
  map that scores distance to infrastructure (such as the road network) named
  <code>input_distance_to_infrastructure</code>, is defined as an additional
  input:
  <div class="figure">
    <img src="images/r_estimap_recreation_distance_to_infrastructure.png" alt="Example of an input map showing distances to infrastructure" >
    <p class="caption">Example of an input map showing distances to infrastructure</p>
  </div>

  <p>
  Naturally, we need to define the output map option <code>spectrum</code> too:
  <div class="code"><pre>
  r.estimap.recreation  \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    spectrum=output_spectrum
  </pre></div>

  <p>
  or, the same command in a copy-paste friendly way for systems that won't
  understand the special <code>\</code> character:

  <div class="code"><pre>
    r.estimap.recreation  land=input_land_suitability  water=input_water_resources,input_bathing_water_quality  natural=input_protected_areas  infrastructure=input_distance_to_infrastructure  spectrum=output_spectrum
  </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_spectrum.png" alt="Example of a recreation spectrum output map while using a MASK, a land suitability map, a water resources map and a natural resources map" >
    <p class="caption">Example of a recreation spectrum output map while using a MASK, a land suitability map, a water resources map and a natural resources map</p>
  </div>

  <p>
  Missing to define an <code>infrastructure</code> map, while asking for the
  <code>spectrum</code> output, the command will abort and inform about.

  <p>
  The image of the <em>spectrum</em> map was produced via the following native
  GRASS GIS commands

  <div class="code"><pre>
    d.rast  output_spectrum
    d.legend  -c  -b  output_spectrum  at=0,30,0,1  border_color=white
    d.text  text="Spectrum"  bgcolor=white
    </pre></div>

  <h5 id="opportunity">Opportunity</h5>

  <p>
  The <code>opportunity</code> map is actually an intermediate step of the
  algorithm. The option to output this map <code>opportunity</code> is meant
  for expert users who want to explore the fundamentals of the processing
  steps. As such, and by design, it requires to also request for the output
  option <code>spectrum</code>. Be aware that this design choice is applied in
  the case of the <code>unmet</code> output map option too. Building upon the
  previous command, we add the <code>opportunity</code> output option:

  <div class="code"><pre>
  r.estimap.recreation --o \
    mask=input_area_of_interest \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    opportunity=output_opportunity \
    spectrum=output_spectrum
  </pre></div>

  <p>
  or, the same command in a copy-paste friendly way:

  <div class="code"><pre>
    r.estimap.recreation  --o mask=input_area_of_interest  land=input_land_suitability  water=input_water_resources,input_bathing_water_quality  natural=input_protected_areas  infrastructure=input_distance_to_infrastructure  opportunity=output_opportunity  spectrum=output_spectrum
    </pre></div>

  <p>
  We also add the <code>--o</code> overwrite flag, because existing
  <code>output_spectrum</code> map will cause the module to abort.

  <div class="figure">
    <img src="images/r_estimap_recreation_opportunity.png" alt="Example of a recreation spectrum output map while using a MASK, a land suitability map, a water resources map and a natural resources map" >
    <p class="caption">Example of a recreation spectrum output map while using a MASK, a land suitability map, a water resources map and a natural resources map</p>
  </div>

  <p>
  The image of the <em>opportunity</em> map was produced via the following
  native GRASS GIS commands

  <div class="code"><pre>
  d.rast  output_opportunity
  d.legend  -c  -b  output_opportunity  at=0,20,0,1  border_color=white
  d.text  text="Opportunity"  bgcolor=white
    </pre></div>

  <h4 id="more-input-maps">More input maps</h4>

  <p>
  To derive the outputs met <code>demand</code> distribution,
  <code>unmet</code> demand distribution and the actual <code>flow</code>,
  additional requirements are a <code>population</code> map and one of
  boundaries, as an input to the option <code>base</code> within which to
  quantify the distribution of the population. Using a map of administrative
  boundaries for the latter option, serves for deriving comparable figures
  across these boundaries. The algorithm sets internally the spatial resolution
  of all related output maps (<code>demand</code>, <code>unmet</code> and
  <code>flow</code>) to the spatial resolution of the <code>population</code>
  input map.

  <h5 id="population">Population</h5>

  <div class="figure">
    <img src="images/r_estimap_recreation_population_2015.png" alt="Fragment of a population map (GHSL, 2015)" >
    <p class="caption">Fragment of a population map (GHSL, 2015)</p>
  </div>

  <p>
  In this example, the population map named <code>population_2015</code> is of
  1000m^2.

  <h5 id="local-administrative-units">Local administrative units</h5>

  <div class="figure">
    <img src="images/r_estimap_recreation_local_administrative_units.png" alt="Fragment of a local administrative units input map" >
    <p class="caption">Fragment of a local administrative units input map</p>
  </div>

  <p>
  The map named <code>local_administrative_units</code> serves in the following
  example as the base map for the zonal statistics to obtain the demand
  map.

  <h4 id="demand">Demand</h4>

  <p>
  In this example command, we remove the previously added
  <code>opportunity</code> and <code>spectrum</code> output options, and
  logically add the <code>demand</code> output option:

  <div class="code"><pre>
  r.estimap.recreation --o \
    mask=input_area_of_interest \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    population=input_population_2015 \
    base=input_local_administrative_units \
    demand=output_demand
  </pre></div>

  <p>
  Of course, the maps <code>output_opportunity</code>
  and <code>output_spectrum</code> still exist in our data base,
  unless explicitly removed.

  <div class="figure">
    <img src="images/r_estimap_recreation_demand.png" alt="Example of a demand distribution output map while using a MASK and inputs for land suitability, water resources, natural resources, infrastructure, population and base" >
    <p class="caption">Example of a demand distribution output map while using a MASK and inputs for land suitability, water resources, natural resources, infrastructure, population and base</p>
  </div>

  <h4 id="unmet-demand">Unmet Demand</h4>

  <p>
  In the following example, we add <code>unmet</code> output map option. In
  this case of the <em>unmet</em> distribution map too, by design the module
  requires the user to define the <code>demand</code> output map option.

  <div class="code"><pre>r.estimap.recreation --o \
    mask=input_area_of_interest \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    population=input_population_2015 \
    base=input_local_administrative_units \
    demand=output_demand \
    unmet=output_unmet_demand
  </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_unmet_demand.png" alt="Example of an 'unmet demand' output map while using a MASK and inputs for land suitability, water resources, natural resources, infrastructure, population and base" >
    <p class="caption">Example of an 'unmet demand' output map while using a MASK and inputs for land suitability, water resources, natural resources, infrastructure, population and base</p>
  </div>

  <p>
  It is left as an exercise to the user to create screenshots of the
  <em>met</em>, the <em>unmet</em> demand distribution and the <em>flow</em>
  output maps. For example, is may be similar to the command examples that
  demonstrate the use of the commands <code>d.rast</code>,
  <code>d.legend</code> and <code>d.text</code>, that draw the
  <em>potential</em>, the <em>spectrum</em> and the <em>opportunity</em>
  maps.

  <h4 id="flow">Flow</h4>

  <p>
  The <em>flow</em> bases upon the same function used to quantify the
  attractiveness of locations for their recreational value. It includes an
  extra <em>score</em> term.

  <p>
  The computation involves a <em>distance</em> map, reclassified in 5
  categories as shown in the following table. For each distance category, a
  unique pair of coefficient values is assigned to the basic equation.

  <div class="tg-wrap">
    <table>
      <thead>
        <tr class="header">
          <th align="left">Distance</th>
          <th align="left">Kappa</th>
          <th align="left">Alpha</th>
        </tr>
      </thead>
      <tbody>
        <tr class="odd">
          <td align="left">0 to 1</td>
          <td align="left">0.02350</td>
          <td align="left">0.00102</td>
        </tr>
        <tr class="even">
          <td align="left">1 to 2</td>
          <td align="left">0.02651</td>
          <td align="left">0.00109</td>
        </tr>
        <tr class="odd">
          <td align="left">2 to 3</td>
          <td align="left">0.05120</td>
          <td align="left">0.00098</td>
        </tr>
        <tr class="even">
          <td align="left">3 to 4</td>
          <td align="left">0.10700</td>
          <td align="left">0.00067</td>
        </tr>
        <tr class="odd">
          <td align="left">>4</td>
          <td align="left">0.06930</td>
          <td align="left">0.00057</td>
        </tr>
      </tbody>
    </table>
  </div>

  <p>
  Note, the last distance category is not considered in deriving the final "map
  of visits". The output is essentially a raster map with the distribution of
  the demand per distance category and within predefined geometric
  boundaries

  <div class="code"><pre>
  r.estimap.recreation --o \
    mask=input_area_of_interest \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    population=input_population_2015 \
    base=input_local_administrative_units \
    flow=output_flow
  </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_mobility.png" alt="Example of a flow output map while using a MASK and inputs for land suitability, water resources, natural resources, infrastructure, population and base" >
    <p class="caption">Example of a flow output map while using a MASK and inputs for land suitability, water resources, natural resources, infrastructure, population and base</p>
  </div>

  <p>
  If we check the output values for the <code>output_flow</code> map, they are
  rounded by the module automatically to integers! Here the first few lines
  reporting areal statistics on the <code>output_flow</code> map:

  <div class="code"><pre>
    r.stats output_flow -acpln --q |head
  </pre></div>

  <p>returns

  <div class="code"><pre>
    52  125000000.000000 50000 1.72%
    53  191000000.000000 76400 2.63%
    54  303000000.000000 121200 4.17%
    55  392000000.000000 156800 5.39%
    56  196000000.000000 78400 2.69%
    57  178000000.000000 71200 2.45%
    58  286000000.000000 114400 3.93%
    59  185000000.000000 74000 2.54%
    60  207000000.000000 82800 2.85%
    61  176000000.000000 70400 2.42%
  </pre></div>

  <p>
  If the user wants the real numbers, that derive from the mobility function,
  the <code>-r</code> flag comes in handy:

  <div class="code"><pre>
  r.estimap.recreation --o -r \
    mask=input_area_of_interest \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    population=input_population_2015 \
    base=input_local_administrative_units \
    flow=output_flow
  </pre></div>

  <p>
  Querying again areal statistics via

  <div class="code"><pre>
    r.stats output_flow -acpln --q |head
  </pre></div>

  returns

  <div class="code"><pre>
    52-52.139117 from  to  50000000.000000 20000 0.69%
    52.139117-52.278233 from  to  11000000.000000 4400 0.15%
    52.278233-52.41735 from  to  39000000.000000 15600 0.54%
    52.41735-52.556467 from  to  32000000.000000 12800 0.44%
    52.556467-52.695583 from  to  7000000.000000 2800 0.10%
    52.695583-52.8347 from  to  9000000.000000 3600 0.12%
    52.8347-52.973817 from  to  25000000.000000 10000 0.34%
    52.973817-53.112933 from  to  13000000.000000 5200 0.18%
    53.112933-53.25205 from  to  28000000.000000 11200 0.38%
    53.25205-53.391167 from  to  92000000.000000 36800 1.26%
  </pre></div>

  <h4 id="supply-and-use">Supply and Use</h4>

  <p>
  The module outputs by request
  the <em>supply</em>
  and <em>use</em> tables
  in form of CSV files.
  Here is how:

  <div class="code"><pre>
  r.estimap.recreation --o -r \
  mask=input_area_of_interest \
  land=input_land_suitability \
  water=input_water_resources,input_bathing_water_quality \
  natural=input_protected_areas \
  infrastructure=input_distance_to_infrastructure \
  population=input_population_2015 \
  base=input_local_administrative_units \
  supply=output_supply \
  use=output_use
  </pre></div>

  <p>
  <strong> Not surprisingly, the above command fails!</strong>
  It however informs that a <strong>land cover map</strong>
  and corresponding <strong>reclassification rules</strong>,
  for the classes of the <code>landcover</code> map, are required.
  Specifically, the algorithm's designers developed a MAES land classes scheme.
  The "translation" of the CORINE land classes (left) into this scheme
  (classes after the <code>=</code> sign) are for example:

  <div class="code"><pre>
  1 = 1 Urban
  2 = 1 Urban
  3 = 1 Urban
  4 = 1 Urban
  5 = 1 Urban
  6 = 1 Urban
  7 = 1 Urban
  8 = 1 Urban
  9 = 1 Urban
  10 = 1 Urban
  11 = 1 Urban
  12 = 2 Cropland
  13 = 2 Cropland
  14 = 2 Cropland
  15 = 2 Cropland
  16 = 2 Cropland
  17 = 2 Cropland
  18 = 4 Grassland
  19 = 2 Cropland
  20 = 2 Cropland
  21 = 2 Cropland
  22 = 2 Cropland
  23 = 3 Woodland and forest
  24 = 3 Woodland and forest
  25 = 3 Woodland and forest
  26 = 4 Grassland
  27 = 5 Heathland and shrub
  28 = 5 Heathland and shrub
  29 = 3 Woodland and forest
  30 = 6 Sparsely vegetated land
  31 = 6 Sparsely vegetated land
  32 = 6 Sparsely vegetated land
  33 = 6 Sparsely vegetated land
  34 = 6 Sparsely vegetated land
  35 = 7 Wetland
  36 = 7 Wetland
  37 = 8 Marine
  38 = 8 Marine
  39 = 8 Marine
  </pre></div>

  <p>
  We save this into a file named <code>corine_to_maes_land_classes.rules</code>
  and feed it to the <code>land_classes</code> option, then re-execute the
  command:

  <div class="code"><pre>
  r.estimap.recreation --o -r \
  mask=input_area_of_interest \
  land=input_land_suitability \
  water=input_water_resources,input_bathing_water_quality \
  natural=input_protected_areas \
  infrastructure=input_distance_to_infrastructure \
  population=input_population_2015 \
  base=input_local_administrative_units \
  landcover=input_corine_land_cover_2006 \
  land_classes=corine_to_maes_land_classes.rules \
  supply=output_supply \
  use=output_use
  </pre></div>

  <p>
  This time it works. Here the first few lines from the output CSV files:

  <div class="code"><pre>
    head -5 output_*.csv
  </pre></div>

  returns

  <div class="code"><pre>
  ==> output_supply.csv <==
  base,base_label,cover,cover_label,area,count,percents
  3,,1,723.555560,9000000.000000,9,7.76%
  3,,3,246142.186250,64000000.000000,64,55.17%
  3,,2,21710.289271,47000000.000000,47,40.52%
  1,,1,1235.207129,11000000.000000,11,7.97%

  ==> output_use.csv<==
  category,label,value
  3,,268576.031081
  4,,394828.563827
  5,,173353.69508600002
  1,,144486.484126
  </pre></div>

  <p>
  Using other land cover maps as input, would obviously require a similar set
  of land classes translation rules.

  <h4 id="all-in-one-call">All in one call</h4>

  <p>Of course it is possible to derive all output maps with one call:
  <div class="code"><pre>
  r.estimap.recreation --o \
    land=input_land_suitability \
    natural=input_protected_areas,input_urban_green  \
    water=input_water_resources,input_bathing_water_quality \
    infrastructure=input_distance_to_infrastructure \
    landcover=input_corine_land_cover_2006 \
    land_classes=corine_to_maes_land_classes.rules \
    mask=input_area_of_interest \
    potential=output_potential \
    opportunity=output_opportunity \
    spectrum=output_spectrum \
    base=input_local_administrative_units \
    aggregation=input_regions \
    population=input_population_2015 \
    demand=output_demand \
    unmet=output_unmet_demand \
    flow=output_flow \
    supply=output_supply \
    use=output_use \
    timestamp='2015'
  </pre></div>

  <p>
  Note the use of the <code>timestamp</code> parameter! This concerns the
  <code>spectrum</code> map. If plans include working with GRASS GIS' temporal
  framework on time-series, maybe this will be useful.

  <h4 id="vector-map">Vector map</h4>

  <p>A vector input map with the role of the <em>base</em> map, can be used too.
  <div>
    <div class="figure">
      <img src="images/r_estimap_recreation_input_vector_local_administrative_units.png" alt="Example of a vector map showing local administrative units" >
      <p class="caption">Example of a vector map showing local administrative units
    </div>
  </div>

  <div class="code"><pre>
    r.estimap.recreation --o -r \
    mask=input_area_of_interest \
    land=input_land_suitability \
    water=input_water_resources,input_bathing_water_quality \
    natural=input_protected_areas \
    infrastructure=input_distance_to_infrastructure \
    population=input_population_2015 \
    base=input_local_administrative_units \
    base_vector=input_vector_local_administrative_units \
    landcover=input_corine_land_cover_2006 \
    land_classes=corine_to_maes_land_classes.rules \
    supply=output_supply \
    use=output_use
  </pre></div>

  <p>This command will also:

  <ul>
    <li>export results of the mobility function in the files <code>output_supply.csv</code> and <code>output_use.csv</code></li>
    <li>add the following columns in the attribute table linked to the <code>input_vector_local_administrative_units</code> vector map:</li>
  </ul>

  <div class="code"><pre>
    spectrum_sum
    demand_sum
    unmet_sum
    flow_sum
    flow_1_sum
    flow_2_sum
    flow_3_sum
    flow_4_sum
    flow_5_sum
    flow_6_sum
  </pre></div>

  <p>
  all of which are of double precision.

  <p>For example, the

  <div class="code"><pre>
    v.db.select input_vector_local_administrative_units columns=lau2_no_name,spectrum_sum,demand_sum,unmet_sum,flow_sum where="flow_sum IS NOT NULL" |head
  </pre></div>

  <p>
  following the analysis, returns

  <div class="code"><pre>
    lau2_no_name|spectrum_sum|demand_sum|unmet_sum|flow_sum
    801 Bad Erlach|22096|2810||700
    841 Leopoldsdorf|8014|1800||426
    630 Rabensburg|23358|8474||1546
    468 Maissau|73168|6650||2580
    10 Müllendorf|19419|1902||718
    544 Straß im Straßertale|57314|4368||1471
    67 Forchtenstein|53009|272||848
    460 Guntersdorf|27408|12183||1955
    103 Sankt Andrä am Zicksee|45130|3833||1926
  </pre></div>

  <p>
  Here the vector map used for administrative boundaries with the sum of flow
  for each unit:

  <div>
    <div class="figure">
      <img src="images/r_estimap_recreation_sum_of_flow_per_local_administrative_unit.png" alt="Example of a vector map showing the flow per unit" >
      <p class="caption">Example of a vector map showing the flow per unit</p>
    </div>
  </div>

  <p>
  and the corresponding unmet demand, based on the analysis

  <div>
    <div class="figure">
      <img src="images/r_estimap_recreation_sum_of_unmet_demand_in_concerned_local_administrative_unit.png" alt="Example of a vector map showing the unmet demand in concerned units" >
      <p class="caption">Example of a vector map showing the unmet demand in concerned units</p>
    </div>
  </div>

  <p>
  In the latter screenshot, the units bearing the unmet demand results, are not
  the same as the raster map previously shown. The different results are due to
  the <code>-r</code> flag used in this last analysis. The <code>-r</code> flag
  will round up floating point values during computations, thus the results
  with or without it will differ. The reason to use, in this last example the
  <code>-r</code> flag, was to have short integer numbers to print as labels
  inside the units (in the vector map).

  <h3 id="using-unprocessed-input-maps">Using unprocessed input maps</h3>

  <p>
  The module offers a pre-processing functionality for all of the following
  input components:

  <ul>
    <li>landuse</li>
    <li>suitability_scores</li>
  </ul>
  <!-- -->
  <ul>
    <li>landcover</li>
    <li>land_classes</li>
  </ul>
  <!-- -->
  <ul>
    <li>lakes</li>
    <li>lakes_coefficients</li>
    <li>default is set to: euclidean,1,30,0.008,1</li>
  </ul>
  <!-- -->
  <ul>
    <li>coastline</li>
    <li>coastline_coefficients</li>
    <li>default is set to: euclidean,1,30,0.008,1</li>
    <li>coast_geomorphology</li>
  </ul>
  <!-- -->
  <ul>
    <li>bathing_water</li>
    <li>bathing_coefficients</li>
    <li>default is set to: euclidean,1,5,0.01101</li>
  </ul>
  <!-- -->
  <ul>
    <li>protected</li>
    <li>protected_scores</li>
    <li>11:11:0,12:12:0.6,2:2:0.8,3:3:0.6,4:4:0.6,5:5:1,6:6:0.8,7:7:0,8:8:0,9:9:0</li>
  </ul>
  <!-- -->
  <ul>
    <li>anthropic</li>
    <li>anthropic_distances</li>
    <li>0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5</li>
  </ul>
  <!-- -->
  <ul>
    <li>roads</li>
    <li>roads_distances</li>
    <li>0:500:1,500.000001:1000:2,1000.000001:5000:3,5000.000001:10000:4,10000.00001:*:5</li>
  </ul>

  <p>
  A first look on how this works, is to experiment with the
  <code>landuse</code> and <code>suitability_scores</code> input options.

  <p>
  Let's return to the first example, and use a fragment from the unprocessed
  CORINE land data set, instead of the <code>land_suitability</code> map. This
  requires a set of "score" rules, that correspond to the CORINE nomenclature,
  to translate the land cover types into recreation potential.

  <div>
    <img src="images/r_estimap_recreation_corine_land_cover_2006.png" alt="Fragment from the CORINE land data base" >
    <img src="images/r_estimap_recreation_corine_land_cover_legend.png" alt="Legend for the CORINE land data base" >
  </div>

  <p>
  In this case, the rules are a simple ASCII file (for example named
  <code>corine_suitability.scores</code>) that contains the following:

  <div class="code"><pre>
    1:1:0:0
    2:2:0.1:0.1
    3:9:0:0
    10:10:1:1
    11:11:0.1:0.1
    12:13:0.3:0.3
    14:14:0.4:0.4
    15:17:0.5:0.5
    18:18:0.6:0.6
    19:20:0.3:0.3
    21:22:0.6:0.6
    23:23:1:1
    24:24:0.8:0.8
    25:25:1:1
    26:29:0.8:0.8
    30:30:1:1
    31:31:0.8:0.8
    32:32:0.7:0.7
    33:33:0:0
    34:34:0.8:0.8
    35:35:1:1
    36:36:0.8:0.8
    37:37:1:1
    38:38:0.8:0.8
    39:39:1:1
    40:42:1:1
    43:43:0.8:0.8
    44:44:1:1
    45:45:0.3:0.3
  </pre></div>

  <p>
  This file is provided in the <code>suitability_scores</code> option:

  <div class="code"><pre>
    r.estimap.recreation  landuse=input_corine_land_cover_2006  suitability_scores=corine_suitability.scores  potential=output_potential_corine
  </pre></div>

  <div class="figure">
    <img src="images/r_estimap_recreation_potential_corine.png" alt="Example of a recreation spectrum output map while using a MASK, based on a fragment from the CORINE land data base" >
    <p class="caption">Example of a recreation spectrum output map while using a MASK, based on a fragment from the CORINE land data base</p>
  </div>

  <p>
  The same can be achieved with a long one-line string too:

  <div class="code"><pre>
  r.estimap.recreation \
      landuse=input_corine_land_cover_2006 \
      suitability_scores="1:1:0:0,2:2:0.1:0.1,3:9:0:0,10:10:1:1,11:11:0.1:0.1,12:13:0.3:0.3,14:14:0.4:0.4,15:17:0.5:0.5,18:18:0.6:0.6,19:20:0.3:0.3,21:22:0.6:0.6,23:23:1:1,24:24:0.8:0.8,25:25:1:1,26:29:0.8:0.8,30:30:1:1,31:31:0.8:0.8,32:32:0.7:0.7,33:33:0:0,34:34:0.8:0.8,35:35:1:1,36:36:0.8:0.8,37:37:1:1,38:38:0.8:0.8,39:39:1:1,40:42:1:1,43:43:0.8:0.8,44:44:1:1,45:45:0.3:0.3" \
      potential=potential_1
  </pre></div>

  <p>
  In fact, this very scoring scheme, for CORINE land data sets, is integrated
  in the module, so we obtain the same output even by discarding the
  <code>suitability_scores</code> option:

  <div class="code"><pre>
  r.estimap.recreation \
    landuse=input_corine_land_cover_2006  \
    suitability_scores=suitability_of_corine_land_cover.scores \
    potential=output_potential_1 --o
  </pre></div>

  <p>
  This is so because CORINE is a standard choice among existing land data bases
  that cover european territories. In case of a user requirement to provide an
  alternative scoring scheme, all what is required is either of

  <ul>
    <li>provide a new "rules" file with the desired set of scoring rules</li>
    <li>provide a string to the <code>suitability_scores</code> option</li>
  </ul>

  <h2 id="author">Author</h2>
  <p>Nikos Alexandris

  <h2 id="licence">Licence</h2>

  <p>
  Copyright 2018 European Union

  <p>
  Licensed under the EUPL, Version 1.2 or -- as soon they will be approved
  by the European Commission -- subsequent versions of the EUPL (the
  "Licence");

  <p>
  You may not use this work except in compliance with the Licence. You may
  obtain a copy of the Licence at:
  https://joinup.ec.europa.eu/collection/eupl/eupl-text-11-12

  <p>
  Unless required by applicable law or agreed to in writing, software
  distributed under the Licence is distributed on an "AS IS" basis, WITHOUT
  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
  Licence for the specific language governing permissions and limitations under
  the Licence.

  <p>Consult the LICENCE file for details.
