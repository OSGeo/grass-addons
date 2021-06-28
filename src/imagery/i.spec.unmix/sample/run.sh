i.spec.unmix gr=96corr err=error97 iter=iter97 res=unmix97 mat=diplom97.dat
cat unmix_reclass25.dat |r.reclass i=unmix97.1 o=unmix971.recl
cat unmix_reclass25.dat |r.reclass i=unmix97.2 o=unmix972.recl
cat unmix_reclass25.dat |r.reclass i=bdg_wrede o=bdg_wrede.recl

cat unmix_reclass25.dat |r.reclass i=unmix97.3 o=unmix973.recl
cat unmix_reclass25.dat |r.reclass i=unmix97.4 o=unmix974.recl
cat unmix_reclass25.dat |r.reclass i=unmix97.5 o=unmix975.recl
#cat unmix_reclass25.dat |r.reclass i=unmix.6 o=unmix6.recl

r.kappa -mwz classification=unmix971.recl reference=bdg_wrede.recl output=kappa.1
r.kappa -mwz classification=unmix972.recl reference=bdg_wrede.recl output=kappa.2
#r.kappa -mwz classification=unmix3.recl reference=degree_soilcover95 output=kappa.3
#r.kappa -mwz classification=unmix4.recl reference=degree_soilcover95 output=kappa.4
#r.kappa -mwz classification=unmix5.recl reference=degree_soilcover95 output=kappa.5
#r.kappa -mwz classification=unmix6.recl reference=degree_soilcover95 output=kappa.6
textedit kappa.1 &
textedit kappa.2 &
