## DESCRIPTION

Compute the theoretical biomass forestry residual potential, based on
the annual/periodic forest increment.

## NOTES

This module permits to evalute the maximum bio-energy from forest
residual available in a particular area, on the base of the
annual/periodic forest increment. The mandatory data input are a vector
file with fields with values of increment, management, treatment, and
forest surface. The increment value is expressed in cubic meters, the
forest surface in hectares, the management is an integer value that can
be 1 for high forest and 2 for coppice, the treatment is an integer
field that can be 1 for final felling and 2 for thinning. The energy
section contains the calorific parameters that permits to convert the
biomass in energy. The output maps are expressed in Mwh.

## EXAMPLE

This example shows a typical input vector file with a table composed by
fields of increment, forest surface, management and treatment. This
example is based on data of Maè Valley, one of the test area of the
R.green project  
  

![image-alt](theoretical_input.png)

  
  

|           |         |            |           |
| --------- | ------- | ---------- | --------- |
| increment | surface | management | treatment |
| 35.87     | 1500    | 1          | 1         |
| 16.48     | 900     | 1          | 2         |
| 24.82     | 500     | 2          | 1         |

  

```sh
r.green.biomassfor.theoretical --overwrite forest=forest@biomasfor boundaries=Boundary@biomasfor forest_column_increment=increment forest_column_yield_surface=surface forest_column_management=management forest_column_treatment=treatment energy_tops_hs=0.49 energy_cormometric_vol_hf=1.97 energy_tops_cops=0.55 output_basename=mae
```

![image-alt](theoretical_output.png)

  
  
The output map is a standardize energy map with the pixel value equal to
the corresponding bioenergy stimated.

## REFERENCE

Sacchelli, S., Zambelli, P., Zatelli, P., Ciolli, M., 2013. Biomasfor -
an open-source holistic model for the assessment of sustainable forest
bioenergy. iFor. Biogeosci. For. 6, 285-293

## SEE ALSO

*[r.green.biomassfor.legal](r.green.biomassfor.legal.md),
[r.green.biomassfor.technical](r.green.biomassfor.technical.md)*

## AUTHORS

Francesco Geri, Pietro Zambelli, Sandro Sacchelli, Marco Ciolli
