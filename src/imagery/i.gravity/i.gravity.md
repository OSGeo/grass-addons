## DESCRIPTION

*i.gravity* calculates the Bouguer gravity anomaly (after Mussett and
Khan).  
Bouguer anomaly computation require:

- g\_obs=observed gravity
- freeair\_corr=free air correction
- bouguer\_corr=bouguer correction
- terrain\_corr=terrain correction
- latitude\_corr=latitude correction
- eotvos\_corr=eotvos correction

## NOTES

- International Gravity Formula (mGal), lambda=latitude (dd)
- Eotvos correction (mGal), v=velocity (kph), lambda=latitude (dd),
    alpha=direction of travel measured clockwise from North
- Free air Correction (mGal), h=height (m)
- Bouguer Correction (mGal), rho=density of slab (Mg/m3), h=height (m)
-

For more details on the algorithms see \[1\].

## SEE ALSO

*[i.latlon](i.latlon.md)*

## REFERENCES

\[1\] Mussett, A.E. and Khan, M.A, M.A. Looking into the Earth: An
Introduction to Geological Geophysics.

## AUTHOR

Yann Chemin, University of London at Birkbeck, United Kingdom.
