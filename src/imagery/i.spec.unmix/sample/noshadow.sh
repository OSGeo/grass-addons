r.mapcalc unmix1_noshade = "(unmix.1/(unmix.1-unmix.3)) + unmix.1"
r.mapcalc unmix2_noshade = "(unmix.2/(unmix.2-unmix.3)) + unmix.2"
cat unmix_reclass25.dat |r.reclass i=unmix1_noshade o=unmix1_noshade.recl
cat unmix_reclass25.dat |r.reclass i=unmix2_noshade o=unmix2_noshade.recl
cat unmix_reclass25.dat |r.reclass i=degree_soilcover95 o=bdgrad95.recl
r.kappa -mwz classification=unmix1_noshade.recl reference=bdgrad95.recl output=kappa.1
r.kappa -mwz classification=unmix2_noshade.recl reference=bdgrad95.recl output=kappa.2
textedit kappa.1 &
textedit kappa.2 &
