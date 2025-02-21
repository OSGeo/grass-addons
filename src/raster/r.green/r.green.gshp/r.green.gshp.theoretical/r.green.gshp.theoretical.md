## DESCRIPTION

*r.green.gshp.theoretical* assess the shallow geothermal potential
defined as the thermal power exchanged by a Borehole Heat Exchanger of a
certain depth. This potential depends on the thermal properties of the
ground and the plant features. This module returns two output raster
maps with the the energy potential (MWh/year) and the power potential
(W). In this module the output is the theoretical maximum energy that
can be converted in the ideal case without considering the financial and
spatial constraints.

## NOTES

The required inputs are the the thermal conductivity. If not specific
values are indicated, reference values have been assumed for the ground
features and the plant.  
  
## EXPLANATION

*r.green.gshp.theoretical* calculates the potential of shallow
geothermal energy by means of and empirical relationship proposed by
Casasso et al. (2016) as:

> *P<sub>gshp</sub>=8\*(T<sub>0</sub> - T<sub>lim</sub>) λ L
> t'<sub>c</sub>/(-0.619 t'<sub>c</sub> log(u'<sub>s</sub>)-0.455
> t'<sub>c</sub>-1.619+4 π R<sub>b</sub>)*  
>
> where
>
> > T<sub>0</sub> is the undisturbed ground temperature (°C),  
> > T<sub>lim</sub> the threshold temperature of the heat carrier fluid
> > setting to 2°C,  
> > λ is the the thermal conductivity of the ground (W/(mK)),  
> > L the borehole length (m),  
> > t'<sub>c</sub> is is the operating time ratio ,  
> > u'<sub>s</sub> is a parameter depending on the simulaion time and
> > the borehole radius ,  
> > R<sub>b</sub> is the thermal resistance (K/W)

## EXAMPLES

This example is based on the case-study of the EUSALP region, located in
Europe and covering part of Italian, Slovenian, Austrian, German, Swiss
and France territories. The data can be downloades at the following
repositories [EUSALP
dataset](https://gitlab.inf.unibz.it/URS/GRETA/eusalp-shallow-geothermal-energy)
.

```sh
r.green.gshp.theoretical \
    ground_conductivity=conductivity \
    heating_season_raster=season_heating \
    ground_temp_raster=ground_temperature \
    ground_capacity_value=2.3 \
    power=gpot_power \
    energy=gpot_energy \
```

## REFERENCES

Alessandro Casasso, Rajandrea Sethi, 2016,  
"G.POT: A quantitative method for the assessment and mapping of the
shallow geothermal potential"  
Energy 106, p 765 --  
<https://doi.org/10.1016/j.energy.2016.03.091>  

## SEE ALSO

*[r.green.hydro.technical](r.green.md),
[r.green.hydro.technical](r.green.gshp.technical.md)*

## AUTHORS

Pietro Zambelli (Eurac Research, Bolzano, Italy), Tested by and manual
written by Giulia Garegnani
