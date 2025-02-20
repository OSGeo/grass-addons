## DESCRIPTION

**r.shalstab** allows to apply the algorithm developed by Montgomery and
Dietrich (1994) in GRASS GIS. According to these authors, the models
associate the theories of infinite slope, where the strength of soil
share at the discretion of rupture of Mohr Coulomb, with the
hydrological model O'Loughlin (1986), resulting in equation. Requested
input and output.

The command requires some input:

  - DEM a digital terrain model of the study area;
  - Raster map or single value for soil cohesion (N/m^2);
  - Raster map or single value for soil friction angle (°);
  - Raster map or single value for soil density (kg/m^3);
  - Raster map or single value for vertical thickness of soil (m);
  - Raster map or single value for hydraulic conductivity k (m/h);
  - Raster map or single value for root cohesion (N/m^2); (default = 0)
  - Raster map or single value for wet soil density (kg/m^3). (default =
    2100)

The outputs are: A landslide susceptibility map (value range from 1 to
7):

  - 1 Unconditionally Unstable
  - 2 0-30 mm/day
  - 3 31-100 mm/day
  - 4 101-150 mm/day
  - 5 151-200 mm/day
  - 6 201-999 mm/day
  - 7 Stable

A map for of critical rainfall map (mm/day).

## REFERENCES

Montgomery, D. R. and Dietrich, W. E.: A physically based model for the
topographic control of shallow landsliding,Water Resour. Res., 30,
1153-1171, 1994.

## AUTHORS

Andrea Filipello, University of Turin, Italy  
Daniele Strigaro, University of Milan, Italy
