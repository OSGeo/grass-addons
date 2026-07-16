/**
 * \file brdf.c
 * \brief BRDF surface models — C port of 6SV2.1 BRDF Fortran subroutines.
 *
 * Each kernel function provides a single-point evaluation; the Fortran
 * originals loop over (μ, φ) Gauss grids but the inner formula is
 * geometry-only, so we extract it for single (SZA, VZA, RAA) calls.
 *
 * Models implemented (single-point):
 *   LAMBERTIAN    — constant (handled by caller; brdf_eval returns 0)
 *   RAHMAN        — RAHMBRDF.f (RPV)
 *   ROUJEAN       — ROUJBRDF.f
 *   HAPKE         — HAPKBRDF.f
 *   OCEAN         — simplified Cox-Munk glint + whitecaps + water body
 *   WALTHALL      — WALTBRDF.f
 *   MINNAERT      — MINNBRDF.f
 *   ROSSLIMAIGNAN — ROSSLIMAIGNANBRDF.f (rlmaignanbrdf)
 *   VERSFELD      — stub (mvbp1 external dependency not ported)
 *   IAPI          — stub (complex canopy model not ported)
 */
#include "../include/brdf.h"
#include <math.h>
#include <stdlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ── Helpers ──────────────────────────────────────────────────────────────── */

static inline float clampf(float v, float lo, float hi)
{
    return (v < lo) ? lo : (v > hi) ? hi : v;
}

/* ── Rahman-Pinty-Verstraete (RPV) ──────────────────────────────────────── */
/* RAHMBRDF.f: rho0 intensity, af asymmetry factor, k structural parameter */
static float brdf_rahman(const BrdfParams *p,
                          float mu1, float mu2, float fi)
{
    float rho0 = p->rahman.rho0;
    float af   = p->rahman.af;
    float k    = p->rahman.k;

    float cospha = mu1*mu2 + sqrtf(1.0f - mu1*mu1)*sqrtf(1.0f - mu2*mu2)*cosf(fi);
    float tante1 = sqrtf(1.0f - mu1*mu1) / (mu1 + 1e-10f);
    float tante2 = sqrtf(1.0f - mu2*mu2) / (mu2 + 1e-10f);
    float geofac = sqrtf(tante1*tante1 + tante2*tante2
                        - 2.0f*tante1*tante2*cosf(fi));

    float coef1 = powf(mu1, k - 1.0f) * powf(mu2, k - 1.0f)
                / powf(mu1 + mu2, 1.0f - k);
    /* Phase function: HG with argument -cospha (backscatter convention) */
    float phafun = (1.0f - af*af)
                 / powf(1.0f + af*af - 2.0f*af*(-cospha), 1.5f);
    float coef2  = 1.0f + (1.0f - rho0) / (1.0f + geofac);

    return rho0 * coef1 * phafun * coef2;
}

/* ── Roujean volumetric kernel ────────────────────────────────────────────── */
/* ROUJBRDF.f: k0 isotropic, k1 geometric-optical, k2 volumetric */
static float brdf_roujean(const BrdfParams *p,
                            float xmus, float xmuv, float fi)
{
    const float pi = (float)M_PI;

    float tts = tanf(acosf(clampf(xmus, 1e-6f, 1.0f)));
    float ttv = tanf(acosf(clampf(xmuv, 1e-6f, 1.0f)));

    float cpsi = xmus*xmuv + sqrtf(1.0f - xmus*xmus)*sqrtf(1.0f - xmuv*xmuv)*cosf(fi);
    cpsi = clampf(cpsi, -1.0f, 1.0f);
    float psi  = (cpsi < 1.0f) ? acosf(cpsi) : 0.0f;

    /* fr = |fi| after acos(cos(fi)) — ensures range [0, pi] */
    float fr = acosf(clampf(cosf(fi), -1.0f, 1.0f));

    float f2 = 4.0f / (3.0f*pi*(xmus + xmuv))
             * ((pi/2.0f - psi)*cpsi + sinf(psi)) - 1.0f/3.0f;

    float f1 = 0.5f * ((pi - fr)*cosf(fr) + sinf(fr)) * tts * ttv
             - tts - ttv
             - sqrtf(tts*tts + ttv*ttv - 2.0f*tts*ttv*cosf(fr));
    f1 /= pi;

    return p->roujean.k0 + p->roujean.k1*f1 + p->roujean.k2*f2;
}

/* ── Hapke canopy model ───────────────────────────────────────────────────── */
/* HAPKBRDF.f: om albedo, af asymmetry, s0 hotspot amplitude, h hotspot width */
static float brdf_hapke(const BrdfParams *p,
                          float mu1, float mu2, float fi)
{
    float om = p->hapke.om;
    float af = p->hapke.af;
    float s0 = p->hapke.s0;
    float h  = p->hapke.h;

    float cg = mu1*mu2 + sqrtf(1.0f - mu1*mu1)*sqrtf(1.0f - mu2*mu2)*cosf(fi);
    cg = clampf(cg, -1.0f, 1.0f);

    float f    = om / 4.0f / (mu2 + mu1 + 1e-10f);
    float sq   = sqrtf(clampf(1.0f - om, 0.0f, 1.0f));
    float h1   = (1.0f + 2.0f*mu1) / (1.0f + 2.0f*sq*mu1);
    float h2   = (1.0f + 2.0f*mu2) / (1.0f + 2.0f*sq*mu2);

    float pg = (1.0f - af*af) / powf(1.0f + af*af + 2.0f*af*cg, 1.5f);
    float p0 = (1.0f - af*af) / powf(1.0f + af*af + 2.0f*af,    1.5f);

    float g   = acosf(cg);
    float bg_d = 1.0f + tanf(g * 0.5f) / (h + 1e-10f);
    float bg  = (om*p0 > 0.0f) ? s0 / (om*p0) / bg_d : 0.0f;

    return f * ((1.0f + bg)*pg + h1*h2 - 1.0f);
}

/* ── Ocean BRDF — simplified Cox-Munk + whitecaps + water body ───────────── */
/* Based on OCEABRDF.f; uses simplified Cox-Munk slope distribution.
 * Full treatment requires indwat/MORCASIWAT/gauss integration (not ported);
 * this provides a reasonable first-order approximation. */
static float brdf_ocean(const BrdfParams *p,
                          float mu1, float mu2, float fi)
{
    /* Cox-Munk slope variance from wind speed */
    float wspd = p->ocean.wspd;
    float azw  = p->ocean.azw * (float)(M_PI / 180.0);

    float sigma2 = 0.003f + 0.00512f * wspd;   /* isotropic approximation */

    /* Specular glint: find half-angle geometry */
    float theta1 = acosf(clampf(mu1, 0.0f, 1.0f));
    float theta2 = acosf(clampf(mu2, 0.0f, 1.0f));

    /* Normal to the specularly reflecting facet */
    float cos_n   = (cosf(theta1) + cosf(theta2));
    float sin1    = sinf(theta1), sin2 = sinf(theta2);
    float norm_n  = sqrtf(sin1*sin1 + sin2*sin2 + 2.0f*sin1*sin2*cosf(fi + azw)
                          + cos_n*cos_n);
    /* cos(tilt) of specular facet from vertical */
    float cos_tilt = (norm_n > 0.0f) ? cos_n / norm_n : 1.0f;
    float cos_tilt2 = cos_tilt*cos_tilt;

    /* Cox-Munk Gaussian slope distribution */
    float tan_tilt2 = (cos_tilt2 > 1e-6f)
                    ? (1.0f - cos_tilt2) / cos_tilt2 : 0.0f;
    float p_cox = (sigma2 > 0.0f)
                ? expf(-tan_tilt2 / (2.0f*sigma2)) / ((float)M_PI * sigma2 * cos_tilt2*cos_tilt2)
                : 0.0f;

    /* Fresnel reflectance for seawater at ~550 nm, nr≈1.34 */
    const float nr = 1.34f;
    float cos_i  = clampf((cosf(theta1) + cosf(theta2)) * 0.5f, 0.0f, 1.0f);
    float sin_t  = sqrtf(clampf(1.0f - cos_i*cos_i, 0.0f, 1.0f)) / nr;
    float cos_t  = sqrtf(clampf(1.0f - sin_t*sin_t, 0.0f, 1.0f));
    float rs     = (cos_i - nr*cos_t) / (cos_i + nr*cos_t + 1e-10f);
    float rp     = (nr*cos_i - cos_t) / (nr*cos_i + cos_t + 1e-10f);
    float fresnel = 0.5f * (rs*rs + rp*rp);

    /* Sunglint reflectance: π × fresnel × p_cox / (4 × μ1 × μ2) */
    float rog = (mu1 > 0.0f && mu2 > 0.0f)
              ? (float)M_PI * fresnel * p_cox / (4.0f * mu1 * mu2)
              : 0.0f;

    /* Whitecap reflectance (Koepke 1984) */
    float W   = 2.95e-6f * powf(wspd, 3.52f);
    float Rwc = W * 0.22f;   /* approximate whitecap reflectance ~0.22 */

    /* Water body below-surface reflectance (Morel simplified) */
    float C   = p->ocean.pcl;
    float wl  = p->ocean.wl;
    /* Approximate Rw (Gordon & Morel 1983) */
    float kw   = (wl < 0.5f) ? 0.01f : (wl < 0.7f) ? 0.05f : 1.0f;
    float kc   = 0.06f * powf(C + 1e-6f, 0.65f);
    float Rw   = 0.33f * kc / (kw + kc + 1e-10f);

    /* Combine: total = whitecaps + (1-W)*glint + water body */
    float nr2 = nr*nr;
    float Rwb = (nr2 > 0.0f) ? Rw / nr2 : Rw;

    return Rwc + (1.0f - W)*rog + (1.0f - Rwc)*Rwb;
}

/* ── Walthall polynomial ──────────────────────────────────────────────────── */
/* WALTBRDF.f */
static float brdf_walthall(const BrdfParams *p,
                              float xmus, float xmuv, float fi)
{
    float ts  = acosf(clampf(xmus, -1.0f, 1.0f));
    float tv  = acosf(clampf(xmuv, -1.0f, 1.0f));
    float phi = fi;

    return p->walthall.a  * (ts*ts*tv*tv)
         + p->walthall.ap * (ts*ts + tv*tv)
         + p->walthall.b  * ts*tv*cosf(phi)
         + p->walthall.c;
}

/* ── Minnaert ─────────────────────────────────────────────────────────────── */
/* MINNBRDF.f: par1=k (exponent), par2=b (albedo normalisation) */
static float brdf_minnaert(const BrdfParams *p,
                              float xmus, float xmuv)
{
    float k = p->minnaert.k;
    float b = p->minnaert.b;
    float prod = clampf(xmus * xmuv, 1e-10f, 1.0f);
    return 0.5f * b * (k + 1.0f) * powf(prod, k - 1.0f);
}

/* ── Ross-Thick + Li-Sparse + Maignan hot-spot ────────────────────────────── */
/* ROSSLIMAIGNANBRDF.f (rlmaignanbrdf): p1=f_iso, p2=f_vol, p3=f_geo */
static float brdf_rosslimaignan(const BrdfParams *p,
                                  float mu_s, float mu_v, float fi)
{
    const float pi = (float)M_PI;

    /* Clamp sza to 75°, vza to 65° as in Fortran */
    float rts = acosf(clampf(mu_s, cosf(75.0f*pi/180.0f), 1.0f));
    float rtv = acosf(clampf(mu_v, cosf(65.0f*pi/180.0f), 1.0f));
    float rfi = fabsf(fi);

    float cts = cosf(rts), ctv = cosf(rtv);
    float sts = sinf(rts), stv = sinf(rtv);
    float cfi = cosf(rfi), sfi = sinf(rfi);

    float cpha = cts*ctv + sts*stv*cfi;
    cpha = clampf(cpha, -1.0f, 1.0f);
    float rpha = acosf(cpha);

    /* Ross-Thick kernel (Maignan hot-spot modification) */
    float ct0 = 2.0f / (3.0f*pi);
    float rosselt = ct0 * (((pi - 2.0f*rpha)*cpha + 2.0f*sinf(rpha)) / (cts + ctv + 1e-10f));
    float rossthick = rosselt * (1.0f + 1.0f/(1.0f + rpha/(1.5f*pi/180.0f))) - 1.0f/3.0f;

    /* Li-Sparse geometric kernel */
    float tanti = tanf(rts);
    float tantv = tanf(rtv);

    float angdist = sqrtf(clampf(tanti*tanti + tantv*tantv - 2.0f*tanti*tantv*cfi, 0.0f, 1e10f));
    float angtemp = 1.0f/(cts + 1e-10f) + 1.0f/(ctv + 1e-10f);

    float cost = 2.0f * sqrtf(angdist*angdist + tanti*tanti*tantv*tantv*sfi*sfi)
               / (angtemp + 1e-10f);
    cost = clampf(cost, -1.0f, 1.0f);
    float tvar = acosf(cost);
    float sint = sqrtf(clampf(1.0f - cost*cost, 0.0f, 1.0f));
    float angover = (tvar - sint*cost) * angtemp / pi;
    float lispars = angover - angtemp + 0.5f*(1.0f + cpha) / (cts*ctv + 1e-10f);

    float result = p->rosslimaignan.f_iso
                 + p->rosslimaignan.f_vol * rossthick
                 + p->rosslimaignan.f_geo * lispars;
    return (result < 0.0f) ? 0.0f : result;
}

/* ══════════════════════════════════════════════════════════════════════════════
 * sixs_brdf_eval — dispatcher
 * ══════════════════════════════════════════════════════════════════════════════ */
float sixs_brdf_eval(BrdfType type, const BrdfParams *params,
                     float cos_sza, float cos_vza, float raa_deg)
{
    /* Convert raa to radians; both kernels use fi = relative azimuth in radians */
    float fi = raa_deg * (float)(M_PI / 180.0);

    /* Ensure non-degenerate cos values */
    float mu1 = clampf(cos_sza, 1e-4f, 1.0f);
    float mu2 = clampf(cos_vza, 1e-4f, 1.0f);

    switch (type) {
        case BRDF_LAMBERTIAN:
            /* Lambertian: caller uses params->lambertian.rho0 directly;
             * the RT is handled analytically in atcorr_invert(). */
            return params->lambertian.rho0;

        case BRDF_RAHMAN:
            return brdf_rahman(params, mu1, mu2, fi);

        case BRDF_ROUJEAN:
            return brdf_roujean(params, mu1, mu2, fi);

        case BRDF_HAPKE:
            return brdf_hapke(params, mu1, mu2, fi);

        case BRDF_OCEAN:
            return brdf_ocean(params, mu1, mu2, fi);

        case BRDF_WALTHALL:
            return brdf_walthall(params, mu1, mu2, fi);

        case BRDF_MINNAERT:
            return brdf_minnaert(params, mu1, mu2);

        case BRDF_ROSSLIMAIGNAN:
            return brdf_rosslimaignan(params, mu1, mu2, fi);

        case BRDF_VERSFELD:
        case BRDF_IAPI:
        default:
            /* Complex models with large external dependencies — stubs */
            return 0.0f;
    }
}

/* ══════════════════════════════════════════════════════════════════════════════
 * sixs_brdf_albe — directional-hemispherical albedo by numerical integration
 * ══════════════════════════════════════════════════════════════════════════════ */
float sixs_brdf_albe(BrdfType type, const BrdfParams *params,
                     float cos_sza, int n_phi, int n_theta)
{
    if (n_phi  < 2) n_phi  = 48;
    if (n_theta < 2) n_theta = 24;

    const float pi   = (float)M_PI;
    const float dphi = 2.0f * pi / (float)n_phi;
    const float dmu  = 1.0f / (float)n_theta;

    float albe = 0.0f;
    for (int it = 0; it < n_theta; it++) {
        float mu = (it + 0.5f) * dmu;         /* midpoint rule in cos(vza) */
        for (int ip = 0; ip < n_phi; ip++) {
            float phi = (ip + 0.5f) * dphi;   /* relative azimuth */
            float raa_deg = phi * 180.0f / pi;
            float brdf = sixs_brdf_eval(type, params, cos_sza, mu, raa_deg);
            albe += brdf * mu * dmu * dphi;
        }
    }
    albe /= pi;   /* normalise by π for hemispherical reflectance */
    return albe;
}

/* ══════════════════════════════════════════════════════════════════════════════
 * NBAR normalisation — MODIS MCD43 standard Ross-Thick + Li-Sparse kernels
 *
 * These are the unmodified kernels from Lucht et al. (2000, IEEE TGRS 38:977).
 * They differ from brdf_rosslimaignan() in that:
 *   - Ross-Thick: no Maignan hot-spot factor
 *   - Li-Sparse: b/r = 1 (no crown ellipsoid stretching), h/b = 2
 *
 * Input angles in degrees; uses cos/sin of those angles internally.
 * Both kernels return 0 at nadir (vza=0), which is used for f_nbar.
 * ══════════════════════════════════════════════════════════════════════════════ */

/* Ross-Thick volumetric kernel (standard MODIS, no hot-spot).
 * K_RT = [(π/2 − ξ)cos(ξ) + sin(ξ)] / (μs + μv) × (2/3π) − 1/3
 * where ξ = arccos(μs μv + √(1−μs²)√(1−μv²) cos(Δφ)). */
static float brdf_rossthick_std(float sza_deg, float vza_deg, float raa_deg)
{
    const float pi = (float)M_PI;

    float rts = sza_deg * (pi / 180.0f);
    float rtv = vza_deg * (pi / 180.0f);
    float rfi = raa_deg * (pi / 180.0f);

    float cts = cosf(rts), stv_s = sinf(rts);
    float ctv = cosf(rtv), stv_v = sinf(rtv);

    float cpha = clampf(cts*ctv + stv_s*stv_v*cosf(rfi), -1.0f, 1.0f);
    float rpha = acosf(cpha);

    float rosselt = (2.0f / (3.0f*pi))
                  * (((pi/2.0f - rpha)*cpha + sinf(rpha)) / (cts + ctv + 1e-10f));
    return rosselt - 1.0f/3.0f;
}

/* Li-Sparse geometric kernel (standard MODIS, b/r=1, h/b=2).
 * Uses the reciprocal overlap area O and the secant terms. */
static float brdf_lisparse_std(float sza_deg, float vza_deg, float raa_deg)
{
    const float pi = (float)M_PI;

    float rts = sza_deg * (pi / 180.0f);
    float rtv = vza_deg * (pi / 180.0f);
    float rfi = raa_deg * (pi / 180.0f);

    float cts  = cosf(rts), stv_s = sinf(rts);
    float ctv  = cosf(rtv), stv_v = sinf(rtv);
    float cfi  = cosf(rfi), sfi   = sinf(rfi);

    /* Phase angle for the (1 + cos ξ) term */
    float cpha = clampf(cts*ctv + stv_s*stv_v*cfi, -1.0f, 1.0f);

    /* tan(θs), tan(θv)  [b/r = 1 so θs' = θs, θv' = θv] */
    float tants = (cts > 1e-6f) ? stv_s / cts : stv_s / 1e-6f;
    float tantv = (ctv > 1e-6f) ? stv_v / ctv : stv_v / 1e-6f;

    float D2    = tants*tants + tantv*tantv - 2.0f*tants*tantv*cfi;
    float D     = sqrtf(clampf(D2, 0.0f, 1e10f));

    float sec_s  = (cts > 1e-6f) ? 1.0f / cts : 1.0f / 1e-6f;
    float sec_v  = (ctv > 1e-6f) ? 1.0f / ctv : 1.0f / 1e-6f;
    float sec_sum = sec_s + sec_v;

    /* cos(t): h/b = 2 factor */
    float cost = 2.0f * sqrtf(clampf(D2 + tants*tants*tantv*tantv*sfi*sfi,
                                      0.0f, 1e10f))
               / (sec_sum + 1e-10f);
    cost = clampf(cost, -1.0f, 1.0f);
    float t    = acosf(cost);
    float sint = sqrtf(clampf(1.0f - cost*cost, 0.0f, 1.0f));

    /* Overlap area O */
    float O = (t - sint*cost) * sec_sum / pi;

    return O - sec_sum + 0.5f*(1.0f + cpha) / (cts*ctv + 1e-10f);
}

/* ── Public: NBAR normalisation ─────────────────────────────────────────── */

float atcorr_brdf_normalize(float rho_boa,
                             float f_iso, float f_vol, float f_geo,
                             float sza_obs, float vza_obs, float raa_obs,
                             float sza_nbar)
{
    /* Short-circuit: Lambertian (no anisotropy) */
    if (f_vol == 0.0f && f_geo == 0.0f)
        return rho_boa;

    float K_vol_obs  = brdf_rossthick_std(sza_obs,  vza_obs, raa_obs);
    float K_geo_obs  = brdf_lisparse_std (sza_obs,  vza_obs, raa_obs);
    float K_vol_nbar = brdf_rossthick_std(sza_nbar, 0.0f,    0.0f);
    float K_geo_nbar = brdf_lisparse_std (sza_nbar, 0.0f,    0.0f);

    float f_obs  = f_iso + f_vol * K_vol_obs  + f_geo * K_geo_obs;
    float f_nbar = f_iso + f_vol * K_vol_nbar + f_geo * K_geo_nbar;

    /* Protect against division by zero */
    if (fabsf(f_obs) < 1e-6f)
        return rho_boa;

    return rho_boa * (f_nbar / f_obs);
}
