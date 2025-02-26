---
name: r.green
description: Toolset for computing the residual energy potential of different renewable energies
---

# Toolset for computing the residual energy potential of different renewable energies

## DESCRIPTION

The *r.green* suite computes the residual energy potential of different
renewable energies like biomass, ground source heat pumps, or
hydropower.

The tool is organized in the module groups:

- [r.green.biomassfor](r.green.biomassfor.md) - computes the energy
    potential of biomass from the forestry residues
- [r.green.gshp](r.green.gshp.md) - computes the Ground Source Heat
    Pump potential
- [r.green.hydro](r.green.hydro.md) - computes the hydropower
    potential

for which are composed of several programs considering different limits
(e.g. theoretical, recommended, legal, technical, ecological and
economic constraints).  
These different scenarios can be compared so that the residual energy
potential and the suitable places for constructing a new power plant can
be identified.  

All the modules of the tool r.green can be installed in GRASS GIS as
following (see also [r.green.install](r.green.install.md)):

```sh
g.extension r.green
```

## NOTES

The basis for creating the modules to calculate the energy potential is
shown in the following image:  
  
![image-alt](r_green.png)  

## REFERENCES

- Garegnani, G., Geri, F., Zambelli, P., Grilli, G., Sacchelli, S.,
    Paletto, A., Curetti, G., Ciolli, M., Vettorato, D. (2015). A new
    open source DSS for assessment and planning of renewable energy: r.
    green. Proceedings of FOSS4G Europe, Como, 14-17.
    ([PDF](http://www.academia.edu/download/42063487/A_new_open_source_DSS_for_assessment_and20160204-20913-vxe2wt.pdf))
- Garegnani, G., Zambelli, P., Geri, F., Gros, J., D'Alonzo, V.,
    Grilli, G., Sacchelli, S., Balest, J. Curetti, G., Paletto, A.,
    Ciolli, M., Vettorato, D. (2015): Evaluation of renewable energy
    potential in Pilot Areas: a Decision Support System.
    ([PDF](http://www.recharge-green.eu/wp-content/uploads/2015/02/Poster_r-green_v4.pdf))

## SEE ALSO

*[r.green.install](r.green.install.md),
[r.green.biomassfor](r.green.biomassfor.md),
[r.green.gshp](r.green.gshp.md), [r.green.hydro](r.green.hydro.md)*

## AUTHOR

For authors and references, please refer to the respective module of
*r.green*.
