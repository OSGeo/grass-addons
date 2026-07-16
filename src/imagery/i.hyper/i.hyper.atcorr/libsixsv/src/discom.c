/* DISCOM: scattering quantities at 20 reference wavelengths — ported from 6SV2.1 DISCOM.f
 * Fills ctx->disc with roatm, dtdir, dtdif, utdir, utdif, sphal at 20 wavelengths.
 * Call once per AOD value before interpolating to specific wavelengths. */
#include "../include/sixs_ctx.h"
#include "../include/aerosol_tables.h"
#include "rayleigh.h"
#include "trunca.h"
#include "rt.h"
#include "ospol.h"
#include "scatra.h"
#include "gauss.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

/* 20 reference wavelengths (µm) — same as AEROSO.f wldisc */
static const float wldisc[NWL_DISC] = {
    0.350f, 0.400f, 0.412f, 0.443f, 0.470f, 0.488f, 0.515f, 0.550f,
    0.590f, 0.633f, 0.670f, 0.694f, 0.760f, 0.860f, 1.240f, 1.536f,
    1.650f, 1.950f, 2.250f, 3.750f
};

/* Component scattering and phase function pointers (mirrors aerosol.c) */
/** \cond INTERNAL */
static const float *const comp_sca_d[4] = {
    aerosol_dust_sca, aerosol_wate_sca, aerosol_ocea_sca, aerosol_soot_sca
};
static const float (*const comp_pha_d[4])[83] = {
    aerosol_dust_pha, aerosol_wate_pha, aerosol_ocea_pha, aerosol_soot_pha
};
static const float std_mix_d[3][4] = {
    { 0.70f, 0.29f, 0.00f, 0.01f },
    { 0.05f, 0.95f, 0.00f, 0.00f },
    { 0.21f, 0.30f, 0.00f, 0.49f },
};
static const float vi_d[4] = { 0.09f, 0.25f, 1.00f, 0.01f };

/**
 * \brief Fill the phase function with the scattering-weighted aerosol mixture.
 *
 * Blends the four component phase-function tables (dust, water, ocean, soot)
 * using the volume mixing ratios for the chosen standard aerosol model and
 * stores the result in \c ctx->polar.pha[].
 *
 * \param[in,out] ctx     6SV context; writes \c ctx->polar.pha[].
 * \param[in]     iaer    Aerosol model index (0=none, 1=continental, 2=maritime, 3=urban).
 * \param[in]     wl_idx  Index into the 20-band reference wavelength table.
 */
static void set_mixed_pha(SixsCtx *ctx, int iaer, int wl_idx)
{
    int nquad = ctx->quad.nquad;
    memset(ctx->polar.pha, 0, nquad * sizeof(float));
    if (iaer == 0) return;

    int mix_idx = (iaer == 2) ? 1 : (iaer == 3 ? 2 : 0);
    const float *ci = std_mix_d[mix_idx];

    float sigm = 0.0f;
    for (int j = 0; j < 4; j++) if (ci[j] > 0.0f) sigm += ci[j] / vi_d[j];
    if (sigm < 1e-10f) return;

    /* Scattering-weighted sum */
    float sca_mix = 0.0f;
    for (int j = 0; j < 4; j++) {
        if (ci[j] <= 0.0f) continue;
        float cij = ci[j] / vi_d[j] / sigm;
        sca_mix += cij * comp_sca_d[j][wl_idx];
    }
    if (sca_mix < 1e-10f) return;

    for (int j = 0; j < 4; j++) {
        if (ci[j] <= 0.0f) continue;
        float cij    = ci[j] / vi_d[j] / sigm;
        float weight = cij * comp_sca_d[j][wl_idx] / sca_mix;
        const float (*pha_j)[83] = comp_pha_d[j];
        for (int k = 0; k < nquad; k++)
            ctx->polar.pha[k] += weight * pha_j[wl_idx][k];
    }
}

/**
 * \brief Initialise the quadrature cosine (rm) and weight (gb) arrays.
 *
 * Builds the offset quadrature arrays required by sixs_os(), sixs_ospol(),
 * and sixs_scatra():
 * - Interior points \c rm(±1 … ±(mu-1)) are Gauss-Legendre nodes on [0,1].
 * - \c rm(0) = −xmus (solar direction).
 * - \c rm(±mu) = ±xmuv (view direction).
 * - Weights \c gb(0) and \c gb(±mu) are zero (endpoints, no quadrature weight).
 *
 * All arrays use the Fortran offset convention: \c rm_off[j+mu] = rm(j).
 *
 * \param[in]  xmus    Cosine of the solar zenith angle.
 * \param[in]  xmuv    Cosine of the view zenith angle.
 * \param[in]  mu      Number of quadrature angles per hemisphere (= MU_P = 25).
 * \param[out] rm_off  Cosine array, size 2mu+1 (offset by mu).
 * \param[out] gb_off  Weight array, size 2mu+1 (offset by mu).
 */
static void setup_rm_gb(float xmus, float xmuv, int mu,
                         float *rm_off, float *gb_off)
{
    int nbmu = mu - 1;   /* interior Gauss points per hemisphere */
    float cgaus[MU_P], wgaus[MU_P];
    sixs_gauss(0.0f, 1.0f, cgaus, wgaus, nbmu);

    /* Zero entire array */
    memset(rm_off, 0, (2*mu+1) * sizeof(float));
    memset(gb_off, 0, (2*mu+1) * sizeof(float));

    /* Interior positive Gauss points: rm(1..mu-1), gb(1..mu-1) */
    for (int k = 1; k <= nbmu; k++) {
        rm_off[k + mu] = cgaus[k - 1];     /* rm(k) */
        rm_off[-k + mu] = -cgaus[k - 1];   /* rm(-k) */
        gb_off[k + mu]  = wgaus[k - 1];    /* gb(k) */
        gb_off[-k + mu] = wgaus[k - 1];    /* gb(-k) */
    }
    /* Special: solar (0) and view (±mu) directions */
    rm_off[0 + mu]   = -xmus;   /* rm(0)  = -xmus */
    rm_off[mu + mu]  =  xmuv;   /* rm(mu) = xmuv  */
    rm_off[-mu + mu] = -xmuv;   /* rm(-mu)= -xmuv */
    gb_off[0 + mu]   = 0.0f;
    gb_off[mu + mu]  = 0.0f;
    gb_off[-mu + mu] = 0.0f;
}

/** \endcond */

/**
 * \brief Compute scattering quantities at 20 reference wavelengths.
 *
 * For each of the 20 fixed reference wavelengths (0.35–3.75 µm), runs the
 * full aerosol initialisation + successive-orders solver to fill
 * \c ctx->disc with:
 * - \c roatm[] — atmospheric path reflectance,
 * - \c dtdir[] / \c dtdif[] — downward direct/diffuse transmittances,
 * - \c utdir[] / \c utdif[] — upward direct/diffuse transmittances,
 * - \c sphal[] — spherical albedo.
 *
 * These 20-wavelength tables are later interpolated by sixs_interp() to any
 * target wavelength.
 *
 * Ported from 6SV2.1 DISCOM.f.
 *
 * \param[in,out] ctx     6SV context; must have atm, aer, del, quad, multi initialised.
 *                        Writes \c ctx->disc on return.
 * \param[in]     idatmp  Sensor type: 0=ground, 4=aircraft at \c palt km, else=satellite.
 * \param[in]     iaer    Aerosol model (0=none, 1=continental, 2=maritime, 3=urban).
 * \param[in]     xmus    Cosine of solar zenith angle.
 * \param[in]     xmuv    Cosine of view zenith angle.
 * \param[in]     phi     Relative azimuth angle (degrees).
 * \param[in]     taer55  Total aerosol OD at 550 nm.
 * \param[in]     taer55p Aerosol OD at 550 nm above sensor plane.
 * \param[in]     palt    Sensor altitude in km (> 900 = satellite).
 * \param[in]     phirad  Relative azimuth angle in radians.
 * \param[in]     nt      Number of atmospheric integration levels.
 * \param[in]     mu      Gauss quadrature points per hemisphere (= MU_P = 25).
 * \param[in]     np      Number of azimuth planes in the xl arrays.
 * \param[in]     ftray   Fraction of Rayleigh OD above sensor (used for idatmp 1–3).
 * \param[in]     ipol    0 = scalar RT; non-zero = vector RT (Stokes I/Q/U).
 */
void sixs_discom(SixsCtx *ctx,
                  int idatmp, int iaer,
                  float xmus, float xmuv, float phi,
                  float taer55, float taer55p, float palt, float phirad,
                  int nt, int mu, int np,
                  float ftray, int ipol)
{
    (void)phi;  /* phi used for phase init (already done) */

    /* Save reference wavelengths */
    for (int l = 0; l < NWL_DISC; l++) ctx->disc.wldis[l] = wldisc[l];

    /* Set up Gauss quadrature arrays (rm/gb) */
    float rm_full[2*MU_P + 1], gb_full[2*MU_P + 1];
    setup_rm_gb(xmus, xmuv, mu, rm_full, gb_full);

    /* Azimuth planes (just one: phirad) */
    float rp[1] = { phirad };
    int   nfi   = 1;       /* minimum for xlphim */

    /* Allocate temporary xl/xlphim for os/ospol calls */
    size_t xl_sz  = (size_t)(2 * mu + 1) * np;
    float *xl     = (float*)calloc(xl_sz, sizeof(float));
    float *xlphim = (float*)calloc(nfi, sizeof(float));
    /* Q/U arrays for vector RT (only used when ipol=1) */
    float *xlq    = ipol ? (float*)calloc(xl_sz, sizeof(float)) : NULL;
    float *xlu    = ipol ? (float*)calloc(xl_sz, sizeof(float)) : NULL;
    if (!xl || !xlphim || (ipol && (!xlq || !xlu))) {
        free(xl); free(xlphim); free(xlq); free(xlu); return;
    }

    /* ===== Loop over 20 reference wavelengths ===== */
    for (int l = 0; l < NWL_DISC; l++) {
        float wl = wldisc[l];

        /* Rayleigh optical depth */
        float tray, trayp;
        sixs_odrayl(ctx, wl, &tray);

        /* Rayleigh OD above sensor */
        if (idatmp == 4)
            trayp = tray;
        else if (idatmp == 0)
            trayp = 0.0f;
        else
            trayp = tray * ftray;

        ctx->disc.trayl[l]  = tray;
        ctx->disc.traypl[l] = trayp;

        /* Aerosol optical depth at this wavelength */
        float taer  = taer55  * ctx->aer.ext[l];
        float taerp = taer55p * ctx->aer.ext[l];
        float piza  = ctx->aer.ome[l];

        /* Truncated values (coeff = 0 always in this 6SV version) */
        float coeff = 0.0f;
        float tamoy = taer,  tamoyp = taerp, pizmoy = piza;

        if (iaer != 0) {
            /* Load mixed phase function for this wavelength → polar.pha[] */
            set_mixed_pha(ctx, iaer, l);
            /* Decompose into Legendre betal[] */
            sixs_trunca(ctx, 0, &coeff);
            /* coeff = 0 always, so tamoy/tamoyp/pizmoy unchanged */
            tamoy  = taer   * (1.0f - piza * coeff);
            tamoyp = taerp  * (1.0f - piza * coeff);
            pizmoy = (fabsf(1.0f - piza * coeff) > 1e-10f) ?
                     piza * (1.0f - coeff) / (1.0f - piza * coeff) : piza;
        } else {
            /* No aerosol: reset betal to Rayleigh values */
            for (int k = 0; k <= ctx->quad.nquad - 3; k++) ctx->polar.betal[k] = 0.0f;
            ctx->polar.betal[0] = 1.0f;
            ctx->polar.betal[2] = 0.1f;  /* Rayleigh: simple 2-term approximation */
        }

        /* ---- Atmospheric reflectances via sixs_os or sixs_ospol ---- */
        float rorayl = 0.0f, roaero = 0.0f, romix = 0.0f;
        float rorayl_q = 0.0f, roaero_q = 0.0f, romix_q = 0.0f;
        float rorayl_u = 0.0f, roaero_u = 0.0f, romix_u = 0.0f;

        /* Helper macro: reset xl (and xlq/xlu when ipol) and call the right RT */
        #define RT_CALL(ta, tr, tap, trp) do { \
            memset(xl,     0, xl_sz * sizeof(float)); \
            memset(xlphim, 0, nfi   * sizeof(float)); \
            if (ipol) { \
                memset(xlq, 0, xl_sz * sizeof(float)); \
                memset(xlu, 0, xl_sz * sizeof(float)); \
                sixs_ospol(ctx, 0, (ta), (tr), pizmoy, (tap), (trp), palt, \
                           phirad, nt, mu, np, nfi, \
                           rm_full, gb_full, rp, xl, xlq, xlu, xlphim); \
            } else { \
                sixs_os(ctx, 0, (ta), (tr), pizmoy, (tap), (trp), palt, \
                        phirad, nt, mu, np, nfi, \
                        rm_full, gb_full, rp, xl, xlphim, NULL); \
            } \
        } while (0)

        /* Rayleigh-only reflectance: tamoy=0, trmoy=tray */
        RT_CALL(0.0f, tray, 0.0f, trayp);
        rorayl   = xl[0] / xmus;
        rorayl_q = xlq ? xlq[0] / xmus : 0.0f;
        rorayl_u = xlu ? xlu[0] / xmus : 0.0f;

        if (iaer != 0 && taer > 1e-6f) {
            /* Aerosol-only reflectance: tamoy=taer, trmoy=0 */
            RT_CALL(tamoy, 0.0f, tamoyp, 0.0f);
            roaero   = xl[0] / xmus;
            roaero_q = xlq ? xlq[0] / xmus : 0.0f;
            roaero_u = xlu ? xlu[0] / xmus : 0.0f;

            /* Combined (Rayleigh + aerosol) reflectance */
            RT_CALL(tamoy, tray, tamoyp, trayp);
            romix   = xl[0] / xmus;
            romix_q = xlq ? xlq[0] / xmus : 0.0f;
            romix_u = xlu ? xlu[0] / xmus : 0.0f;
        } else {
            roaero   = 0.0f; roaero_q = 0.0f; roaero_u = 0.0f;
            romix    = rorayl;
            romix_q  = rorayl_q;
            romix_u  = rorayl_u;
        }

        #undef RT_CALL

        ctx->disc.roatm[0][l]  = rorayl;
        ctx->disc.roatm[1][l]  = romix;
        ctx->disc.roatm[2][l]  = roaero;
        ctx->disc.roatmq[0][l] = rorayl_q;
        ctx->disc.roatmq[1][l] = romix_q;
        ctx->disc.roatmq[2][l] = roaero_q;
        ctx->disc.roatmu[0][l] = rorayl_u;
        ctx->disc.roatmu[1][l] = romix_u;
        ctx->disc.roatmu[2][l] = roaero_u;

        /* ---- Scattering transmittances ---- */
        float ddirtt, ddiftt, udirtt, udiftt, sphalbt;
        float ddirtr, ddiftr, udirtr, udiftr, sphalbr;
        float ddirta, ddifta, udirta, udifta, sphalba;

        sixs_scatra(ctx,
                    tamoy, tamoyp, tray, trayp,
                    pizmoy, palt, nt, mu,
                    rm_full, gb_full,
                    xmus, xmuv,
                    &ddirtt, &ddiftt, &udirtt, &udiftt, &sphalbt,
                    &ddirtr, &ddiftr, &udirtr, &udiftr, &sphalbr,
                    &ddirta, &ddifta, &udirta, &udifta, &sphalba);

        /* Store: [0]=Rayleigh, [1]=total, [2]=aerosol */
        ctx->disc.dtdir[0][l] = ddirtr; ctx->disc.dtdif[0][l] = ddiftr;
        ctx->disc.utdir[0][l] = udirtr; ctx->disc.utdif[0][l] = udiftr;
        ctx->disc.sphal[0][l] = sphalbr;

        ctx->disc.dtdir[1][l] = ddirtt; ctx->disc.dtdif[1][l] = ddiftt;
        ctx->disc.utdir[1][l] = udirtt; ctx->disc.utdif[1][l] = udiftt;
        ctx->disc.sphal[1][l] = sphalbt;

        ctx->disc.dtdir[2][l] = ddirta; ctx->disc.dtdif[2][l] = ddifta;
        ctx->disc.utdir[2][l] = udirta; ctx->disc.utdif[2][l] = udifta;
        ctx->disc.sphal[2][l] = sphalba;
    }

    free(xl);
    free(xlphim);
    free(xlq);
    free(xlu);
}
