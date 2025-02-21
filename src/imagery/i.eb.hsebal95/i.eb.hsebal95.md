## DESCRIPTION

*i.eb.h\_sebal95* computes the *sensible heat flux* \[W/m2\] after
Bastiaanssen, 1995 in \[1\].

*i.eb.h\_sebal95* given the vegetation height (hc), humidity (RU), wind
speed at two meters height (WS), temperature (T), digital terrain model
(DEM), and net radiation (NSR) raster input maps, calculates the
sensible heat flux map (h0).

Optionally the user can activate a flag (-z) that allows him setting to
zero all of the negative evapotranspiration cells; in fact these
negative values motivated by the condensation of the air water vapour
content, are sometime undesired because they can produce computational
problems. The usage of the flag -n detect that the module is run in
night hours and the appropriate soil heat flux is calculated.

The algorithm implements well known approaches: the hourly
Penman-Monteith method as presented in Allen et al. (1998) for land
surfaces and the Penman method (Penman, 1948) for water surfaces.  

Land and water surfaces are idenfyied by Vh:  
\- where Vh less than 0 vegetation is present and evapotranspiration is
calculated;  
\- where Vh=0 bare ground is present and evapotranspiration is
calculated;  
\- where Vh more than 0 water surface is present and evaporation is
calculated;  

For more details on the algorithms see \[1\].

### Parameters:

- **DEM**=*name*  
    Input elevation raster \[m a.s.l.\]. Required.
- **T**=*name*  
    Input temperature raster \[°C\]. Required.
- **RH** =*name*  
    Input relative humidity raster \[%\]. Required.
- **WS** =*name*  
    Input wind speed at two meters raster \[m/s\]. Required.
- **NSR** =*name*  
    Input net solar radiation raster \[MJ/(m2\*h)\]. Required.
- **Vh** =*name*  
    Input vegetation heigth raster \[m\]. Required.
- **ETP** =*name*  
    Output evapotranspiration raster \[mm/h\]. Required.

## NOTES

Net solar radiation map in MJ/(m2\*h) can be computed from the
combination of the *r.sun*, run in mode 1, and the r.mapcalc commands.**

The sum of the three radiation components outputted by r.sun (beam,
diffuse, and reflected) multiplied by the Wh to Mj conversion factor
(0.0036) and optionally by a clear sky factor \[0-1\] allows the
generation of a map to be used as an NSR input for the *i.evapo.pm*
command.  
example:  
r.sun elev\_in=dem asp\_in=aspect slope\_in=slope lin=2 albedo=alb\_Mar
\\ incidout=out beam\_rad=beam diff\_rad=diffuse refl\_rad=reflected
day=73 time=13:00 dist=100;  
r.mapcalc 'NSR=0.0036\*(beam+diffuse+reflected)';

## SEE ALSO

*[i.eb.h\_iter](i.eb.h_iter.md), [i.eb.h0](i.eb.h0.md),
[i.evapo.pm](i.evapo.pm.md)*

## REFERENCES

\[1\] Bastiaanssen, W.G.M., 1995. Estimation of Land surface paramters
by remote sensing under clear-sky conditions. PhD thesis, Wageningen
University, Wageningen, The Netherlands.

\[2\] Allen, R.G., L.S. Pereira, D. Raes, and M. Smith. 1998. Crop
Evapotranspiration: Guidelines for computing crop water requirements.
Irrigation and Drainage Paper 56, Food and Agriculture Organization of
the United Nations, Rome, pp. 300

\[3\] Penman, H. L. 1948. Natural evaporation from open water, bare soil
and grass. Proc. Roy. Soc. London, A193, pp. 120-146.

## AUTHOR

Yann Chemin  
International Rice Research Institute, Los Banos, The Philippines.  
International Water management Institute, Colombo, Sri Lanka.

Contact: [Yann Chemin](mailto:y.chemin@cgiar.org)
