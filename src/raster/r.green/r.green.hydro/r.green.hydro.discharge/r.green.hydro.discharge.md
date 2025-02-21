## DESCRIPTION

*r.green.hydro.discharge* calculates the average natural discharge and
the minimum flow discharge according to regional laws.

## NOTES

The natural discharge is the discharge of the streams which doesn't
consider the existing power plants and the other structures exploiting
the water of the river.  
The Minimal Flow Discharge (MFD) is the amount of water which has to
remain in the river to preserve the ecosystems. The legislation differs
in each region. The MFD can be considered as a percentage of the current
discharge, which is the discharge of the river considering the
structures exploiting the water. The current discharge is often
considered as the mean annual discharge.  
  
However, a percentage of the current discharge cannot define precisely
the MFD and each region has a different method to define it. For the
moment, this module only considers the legislation applied on Piave
basin in the Veneto region. New tabs with the legislation of other
regions could be added.  
  
The module computes two raster maps : the natural discharge and the MFD.
On Piave basin, the natural discharge can be computed thanks to the
input raster map with the values of specific discharge, and the MFD is
calculated thanks to this formula :  
  
Q<sub>MFD</sub> = ( K<sub>b</sub> + K<sub>n</sub> ) \* 177 \*
S<sup>0.85</sup> \* Q<sub>spec</sub> \* 10<sup>-6</sup>  

> where K<sub>b</sub> is the biological criticality index,  
> K<sub>n</sub> is the naturalistic criticality index,  
> S is the catchment area, in km<sup>2</sup>,  
> Q<sub>spec</sub> is the specific flow-rate per unit area of the
> catchment, in l/(s.km<sup>2</sup>)  

K<sub>b</sub> is typically within the range of 1-1.6; higher values are
chosen for a river whose aquatic ecosystem is considered to be of a
particular environmental value.  
K<sub>n</sub> is typically within the range of 0-0.6; higher values of
such index are used for basins having a particular naturalistic value,
for instance national parks.  
The values of K<sub>b</sub> and K<sub>n</sub> are imposed by the Piave
River Catchment Authority (PRCA). They have different values depending
on homogeneous segments which can be found in a table made by the PRCA.
Also the values of Q<sub>spec</sub> depend on the area and are available
in such a table.  
  
Thanks to three raster maps respectively with the values of
K<sub>b</sub>, K<sub>n</sub> and Q<sub>spec</sub>, and also the
elevation raster map and the streams vector map, the module creates the
two raster maps with the values of MFD and average natural discharge.

## EXAMPLE

This example is based on the case-study of Mis valley in Belluno
province, Veneto, Italy.  
  
Here is the map of the Mis valley with colored areas to define the
K<sub>n</sub>, K<sub>b</sub> and Q<sub>spec</sub> values.

![image-alt](r.green.hydro.discharge_input.png)  
Picture which gathers the input raster maps with K<sub>n</sub>,
K<sub>b</sub> and Q<sub>spec</sub> values

According to the legislation for the Piave basin explained above, the
legal values for the Mis valley are :  
K<sub>n</sub> = 0.4 in the whole region (yellow and red zones)  
K<sub>b</sub> = 1.4 in the yellow zone and 1.6 in the red zone  
Q<sub>spec</sub> = 44 l/(s.km<sup>2</sup>) in the yellow zone and 43
l/(s.km<sup>2</sup>) elsewhere (red and white zones)  
  
These values are put in three different raster maps : q\_spec, k\_b and
k\_n.  
Here is the code used to create the raster maps with the MFD and the
natural discharge. The basins are considered with a threshold of 10000
m.  
  
```sh
r.green.hydro.discharge q_spec=q_spec output_q_river=discharge k_b=k_b k_n=k_n output_mfd=mfd elevation=elevation output_streams=streams threshold=100000
```

The following picture gathers the two output raster maps mfd and
discharge which look like each other (yellow background with colored
points following the river and containing the values of discharge). For
a better understanding, the following picture also shows the border of
the Mis valley and the streams.  
  
![image-alt](r.green.hydro.discharge_output.png)  
Picture which gathers the output raster maps with valued of MFD and
natural discharge, also showing the vector maps with the borders and
streams of Mis valley

The white point is queried in GRASS to know the values of MFD and
natural discharge. The following picture shows these values in
m<sup>3</sup>/s.  
  
![image-alt](r.green.hydro.discharge_output_table.png)  
Values of MFD and natural discharge (in m<sup>3</sup>/s) at the white
point

## SEE ALSO

*[r.green.hydro.delplants](r.green.hydro.delplants.md)  
[r.green.hydro.theoretical](r.green.hydro.theoretical.md)  
[r.green.hydro.optimal](r.green.hydro.optimal.md)  
[r.green.hydro.recommended](r.green.hydro.recommended.md)  
[r.green.hydro.structure](r.green.hydro.structure.md)  
[r.green.hydro.technical](r.green.hydro.technical.md)  
[r.green.hydro.financial](r.green.hydro.financial.md)  
*

## REFERENCE

*Allegato alla delibera n. 4/2004 del Comitato Istituzionale del 3 marzo
2004  
Piano stralcio per la gestione delle risorse idriche del bacino del
Piave - Misure di Salvaguardia*  
from Autorità di bacino dei fiumi Isonzo, Tagliamento, Livenza, Piave,
Brenta-Bacchiglione

## AUTHORS

Giulia Garegnani (Eurac Research, Bolzano, Italy), Sara Biscaini
(University of Trento, Italy), manual written by Julie Gros.
