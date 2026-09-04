/* Ported from the 6SV2.1 DUST/WATE/OCEA/SOOT component routines. */
#pragma once

/* Aerosol component optical properties at 20 reference wavelengths (wldis).
 * Components: 0=dust, 1=wate(water-soluble), 2=ocea(oceanic), 3=soot.
 * Continental, maritime, and urban models mix these components; BDM desert
 * optical properties are independent tables.
 */

#define AEROSOL_NCOMP 4
#define AEROSOL_NWL   20
#define AEROSOL_NQUAD 83

extern const float aerosol_dust_ext[20];
extern const float aerosol_dust_sca[20];
extern const float aerosol_dust_asy[20];
extern const float aerosol_dust_pha[20][83];
extern const float aerosol_dust_qha[20][83];
extern const float aerosol_dust_uha[20][83];

extern const float aerosol_wate_ext[20];
extern const float aerosol_wate_sca[20];
extern const float aerosol_wate_asy[20];
extern const float aerosol_wate_pha[20][83];
extern const float aerosol_wate_qha[20][83];
extern const float aerosol_wate_uha[20][83];

extern const float aerosol_ocea_ext[20];
extern const float aerosol_ocea_sca[20];
extern const float aerosol_ocea_asy[20];
extern const float aerosol_ocea_pha[20][83];
extern const float aerosol_ocea_qha[20][83];
extern const float aerosol_ocea_uha[20][83];

extern const float aerosol_soot_ext[20];
extern const float aerosol_soot_sca[20];
extern const float aerosol_soot_asy[20];
extern const float aerosol_soot_pha[20][83];
extern const float aerosol_soot_qha[20][83];
extern const float aerosol_soot_uha[20][83];

extern const float aerosol_bdm_ext[20];
extern const float aerosol_bdm_sca[20];
extern const float aerosol_bdm_asy[20];
extern const float aerosol_bdm_pha[20][83];
extern const float aerosol_bdm_qha[20][83];
extern const float aerosol_bdm_uha[20][83];

/* Standard aerosol model mixing ratios [dust, wate, ocea, soot] */
/* Models: 0=continental, 1=maritime, 2=urban */
extern const float aerosol_std_mix[3][4];

/* Component volume integrals (vi) from DUST/WATE/OCEA/SOOT.f. */
extern const float aerosol_component_vi[4];
