## DESCRIPTION

*r.green.hydro.delplants* deletes segments of river where there is an
existing plant.

## NOTES

This command is used to select the segments of river which are not
already exploited by a plant or another structure.  
The required inputs are the elevation raster map, the map with the
streams and the one with the intakes and restitution of the existing
plants. In option, it is possible to add the map with the intakes and
restitution of the other structures such aqueducts or irrigation in
order to delete these segments too.  
It is necessary to verify in "Optional" that the intakes and restitution
are well reported in the table of the input maps (hydro and other).

## EXAMPLE

This example is based on the case-study of Mis valley in Belluno
province, Veneto, Italy.  
  
![image-alt](r_green_hydro_delplants_input.png)  
Input vector maps : streams of Mis Valley in black and intakes and
restitution of existing plants in red

We use the following code to compute the available streams and obtain
the next map :

```sh
r.green.hydro.delplants hydro=existingplants river=streams output=availablestreams elevation=elevation

d.vect map=existingplants color=red
```

![image-alt](r_green_hydro_delplants_output.png)  
Output vector map in black : streams of Mis Valley without the existing
plants (intakes and restitution of existing plants are added there in
red)

## SEE ALSO

*[r.green.hydro.discharge](r.green.hydro.discharge.md)  
[r.green.hydro.financial](r.green.hydro.financial.md)  
[r.green.hydro.theoretical](r.green.hydro.theoretical.md)  
[r.green.hydro.optimal](r.green.hydro.optimal.md)  
[r.green.hydro.recommended](r.green.hydro.recommended.md)  
[r.green.hydro.structure](r.green.hydro.structure.md)  
[r.green.hydro.technical](r.green.hydro.technical.md)  
*

## AUTHORS

Giulia Garegnani and Pietro Zambelli (Eurac Research, Bolzano, Italy),
Manual written by Julie Gros.
