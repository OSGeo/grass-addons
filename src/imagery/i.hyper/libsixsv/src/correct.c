/**
 * \file correct.c
 * \brief LUT bilinear (AOD × H₂O) slice for bulk per-wavelength interpolation.
 */
#include "atcorr.h"

/**
 * \brief Extract a per-wavelength LUT slice at a fixed (AOD, H₂O) point.
 *
 * Performs bilinear interpolation in the [AOD × H₂O] plane of the precomputed
 * LUT and fills the output arrays with the correction parameters for every
 * wavelength in the LUT grid.  Values outside the grid are clamped to the
 * boundary.
 *
 * This is more efficient than atcorr_lut_interp_pixel() when the same
 * (AOD, H₂O) values are applied to all pixels (scalar correction mode).
 *
 * \param[in]  cfg      LUT configuration (grid axes and dimensions).
 * \param[in]  lut      Precomputed LUT arrays.
 * \param[in]  aod_val  AOD at 550 nm.
 * \param[in]  h2o_val  Column water vapour (g cm⁻²).
 * \param[out] Rs       Atmospheric path reflectance [cfg->n_wl].
 * \param[out] Tds      Downward transmittance [cfg->n_wl].
 * \param[out] Tus      Upward transmittance [cfg->n_wl].
 * \param[out] ss       Spherical albedo [cfg->n_wl].
 * \param[out] Tdds     Direct downward transmittance [cfg->n_wl]; may be NULL.
 */
void atcorr_lut_slice(const LutConfig *cfg, const LutArrays *lut,
                      float aod_val, float h2o_val,
                      float *Rs, float *Tds, float *Tus, float *ss,
                      float *Tdds)
{
    int na = cfg->n_aod, nh = cfg->n_h2o, nw = cfg->n_wl;

    /* AOD bracket */
    int ia0 = 0;
    while (ia0 < na - 2 && cfg->aod[ia0 + 1] <= aod_val) ia0++;
    int ia1 = (ia0 < na - 1) ? ia0 + 1 : ia0;
    float ta = (ia1 != ia0)
                   ? (aod_val - cfg->aod[ia0]) / (cfg->aod[ia1] - cfg->aod[ia0])
                   : 0.0f;
    if (ta < 0.0f) ta = 0.0f;
    if (ta > 1.0f) ta = 1.0f;

    /* H2O bracket */
    int ih0 = 0;
    while (ih0 < nh - 2 && cfg->h2o[ih0 + 1] <= h2o_val) ih0++;
    int ih1 = (ih0 < nh - 1) ? ih0 + 1 : ih0;
    float th = (ih1 != ih0)
                   ? (h2o_val - cfg->h2o[ih0]) / (cfg->h2o[ih1] - cfg->h2o[ih0])
                   : 0.0f;
    if (th < 0.0f) th = 0.0f;
    if (th > 1.0f) th = 1.0f;

#define IDX(ia, ih, iw) ((size_t)(ia) * nh * nw + (size_t)(ih) * nw + (iw))
#define BI4(arr) \
    ((arr)[IDX(ia0,ih0,iw)] * (1.f-ta)*(1.f-th) + \
     (arr)[IDX(ia1,ih0,iw)] *      ta *(1.f-th) + \
     (arr)[IDX(ia0,ih1,iw)] * (1.f-ta)*      th + \
     (arr)[IDX(ia1,ih1,iw)] *      ta *      th)

    for (int iw = 0; iw < nw; iw++) {
        Rs[iw]  = BI4(lut->R_atm);
        Tds[iw] = BI4(lut->T_down);
        Tus[iw] = BI4(lut->T_up);
        ss[iw]  = BI4(lut->s_alb);
        if (Tdds && lut->T_down_dir)
            Tdds[iw] = BI4(lut->T_down_dir);
        else if (Tdds)
            Tdds[iw] = Tds[iw];  /* fallback: no direct/diffuse split */
    }
#undef BI4
#undef IDX
}
