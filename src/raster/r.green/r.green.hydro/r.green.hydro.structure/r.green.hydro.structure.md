## DESCRIPTION

*r.green.hydro.structure* computes the derivation channel and the
penstock for each potential plant and for both sides of the river.

## NOTES

The input maps are the elevation raster map and the one with the
segments of potential plants (vector map which can be computed by
r.green.hydro.optimal or r.green.hydro.recommended).  
In the section "Input column", the column names in the table of the map
with potential plants have to be reported in order to read correctly the
corresponding values.  
The module returns a vector map with the structure for each plant on
both sides of the river. The derivation channel and the penstock are
distinguished and reported in the table.  
In option, the module can also compute the vector map with the intake
and restitution of each potential plant.  
  
As the current potential concerns especially small hydropower (inferior
to 20 MW), the structure suggested is the one for small hydropower
detailed in the picture below. It is composed of an intake (A) which
diverts water from the river. This water is conveyed into a derivation
channel (B) with a very low slope and arrives in a forebay tank (C)
which regulates the fluctuation of discharge. Finally, the penstock (D)
conveys the water with the highest possible head to the
turbine-alternator group (E) which produces electricity. The water is
then released in the river (restitution F). We use the following
vocabulary: the structure of the plant corresponds to the part with the
derivation channel, the forebay tank and the penstock, whereas the
segment of the plant corresponds to the part of the river (water not
diverted) between the intake (A) and the restitution (F).  
  

![image-alt](r_green_hydro_technical_picstruct.png)  
Structure of the plants considered in the module

  
  
The power is maximized for the highest head in the penstock so the
derivation channel is computed along the same quote (the low slope is
neglected here) until the point which maximizes the head along the
penstock. The structure is computed for both sides of the river in order
to determine which one produces the most power.

## EXAMPLE

This example is based on the case-study of Gesso and Vermenagna valleys
in the Natural Park of the Maritime Alps, Piedmont, Italy.  
  
Here is the input vector map potentialplants with the segments of
potential plants (in blue). The vector map with the intakes and
restitution of potential plants is also visibile in red on this
picture.  
  

![image-alt](r_green_hydro_structure_input.png)  
Input vector map potentialplants

  
The following command computes the derivation channel and the penstock
for each potential plant and for each side of the river :  

```sh
r.green.hydro.structure elevation=elevation plant=potentialplants output_struct=structplants
```

  
  
The result is shown in black in the following picture which gathers the
input and output maps.  
  

![image-alt](r_green_hydro_structure_output.png)  
Output vector map structplants in black

## SEE ALSO

*[r.green.hydro.discharge](r.green.hydro.discharge.md)  
[r.green.hydro.delplants](r.green.hydro.delplants.md)  
[r.green.hydro.theoretical](r.green.hydro.theoretical.md)  
[r.green.hydro.optimal](r.green.hydro.optimal.md)  
[r.green.hydro.recommended](r.green.hydro.recommended.md)  
[r.green.hydro.technical](r.green.hydro.technical.md)  
[r.green.hydro.financial](r.green.hydro.financial.md)  
*

## REFERENCE

Picture of the plant structure taken from Micro-hydropower Systems - A
Buyer's Guide, Natural Resources Canada, 2004

## AUTHORS

Pietro Zambelli (Eurac Research, Bolzano, Italy), Manual written by
Julie Gros.
