/* Surface pressure / altitude adjustment — ported from 6SV2.1 PRESSURE.f.
 *
 * Adjusts the standard atmosphere profile stored in ctx->atm so that its
 * surface (bottom) level corresponds to the given pressure or altitude.
 * The lower layers are interpolated; the upper layers are preserved as-is.
 *
 * Convention (matching Fortran):
 *   sp > 0  : surface pressure in hPa   (most common case for elevated terrain)
 *   sp < 0  : surface altitude in km    (negative sign triggers alt-mode)
 *   sp == 0 : no-op (standard atmosphere unchanged)
 */
#include "../include/sixs_ctx.h"
#include <math.h>
#include <string.h>

/**
 * \brief Integrate water vapour and ozone columns from the adjusted profile.
 *
 * Trapezoid-integrates the atmospheric profile in pressure-coordinate to
 * produce total column water vapour (g cm⁻²) and total ozone column
 * (Dobson units).  Called after sixs_pressure() has adjusted the profile.
 *
 * \param[in]  ctx   6SV context with the (possibly adjusted) atmospheric profile.
 * \param[out] uw    Integrated water vapour column (g cm⁻²).
 * \param[out] uo3   Integrated ozone column (Dobson units, 1 DU = 10⁻³ atm-cm).
 */
static void compute_columns(const SixsCtx *ctx, float *uw, float *uo3)
{
    const float g    = 98.1f;
    const float air  = 0.028964f / 0.0224f;
    const float ro3  = 0.048f / 0.0224f;

    float rmwh[NATM], rmo3[NATM];
    for (int k = 0; k < NATM - 1; k++) {
        float roair = air * 273.16f * ctx->atm.p[k]
                    / (1013.25f * ctx->atm.t[k]);
        rmwh[k] = ctx->atm.wh[k] / (roair * 1000.0f);
        rmo3[k] = ctx->atm.wo[k] / (roair * 1000.0f);
    }

    float uw_  = 0.0f, uo3_ = 0.0f;
    for (int k = 1; k < NATM - 1; k++) {
        float ds = (ctx->atm.p[k-1] - ctx->atm.p[k]) / ctx->atm.p[0];
        uw_  += 0.5f * (rmwh[k] + rmwh[k-1]) * ds;
        uo3_ += 0.5f * (rmo3[k] + rmo3[k-1]) * ds;
    }
    uw_  = uw_  * ctx->atm.p[0] * 100.0f / g;
    uo3_ = uo3_ * ctx->atm.p[0] * 100.0f / g;
    uo3_ = 1000.0f * uo3_ / ro3;

    *uw  = uw_;
    *uo3 = uo3_;
}

/**
 * \brief Adjust the atmospheric profile to a given surface pressure or altitude.
 *
 * Truncates and re-interpolates the standard atmosphere profile stored in
 * \c ctx->atm so that the surface level corresponds to the specified pressure
 * or altitude.  Layers above the new surface are preserved; the bottom level
 * is replaced by the interpolated state at the new surface.
 *
 * Ported from 6SV2.1 PRESSURE.f.
 *
 * \param[in,out] ctx  6SV context; \c ctx->atm is modified in place.
 * \param[in]     sp   Surface condition:
 *                     - \c sp > 0: surface pressure in hPa;
 *                     - \c sp < 0: surface altitude in km (negated);
 *                     - \c sp == 0: no-op (standard atmosphere unchanged).
 */
void sixs_pressure(SixsCtx *ctx, float sp)
{
    if (sp == 0.0f) return;

    int isup, iinf;
    float ps, xalt;

    if (sp < 0.0f) {
        /* ── Altitude mode: sp = -altitude_km ──────────────────────────── */
        float xps2 = -sp;
        if (xps2 >= 100.0f) xps2 = 99.99f;

        /* Find bracketing levels by altitude */
        int i = 0;
        while (i < NATM - 1 && ctx->atm.z[i] <= xps2) i++;
        isup = i;
        iinf = i - 1;

        /* Log-linear pressure interpolation */
        float xa = (ctx->atm.z[isup] - ctx->atm.z[iinf])
                 / logf(ctx->atm.p[isup] / ctx->atm.p[iinf]);
        float xb = ctx->atm.z[isup] - xa * logf(ctx->atm.p[isup]);
        ps   = expf((xps2 - xb) / xa);
        xalt = xps2;
    } else {
        /* ── Pressure mode: sp = surface_pressure_hPa ────────────────── */
        if (sp >= 1013.0f) {
            /* Surface pressure higher than standard — shift bottom layers */
            float dps = sp - ctx->atm.p[0];
            for (int i = 0; i < 9 && ctx->atm.p[i] > dps; i++)
                ctx->atm.p[i] += dps;
            return;
        }
        ps = sp;

        /* Find first level where p < ps (pressure decreases upward) */
        int i = 0;
        while (i < NATM - 1 && ctx->atm.p[i] >= ps) i++;
        isup = i;
        iinf = i - 1;

        /* Log-linear altitude interpolation */
        float xa = (ctx->atm.z[isup] - ctx->atm.z[iinf])
                 / logf(ctx->atm.p[isup] / ctx->atm.p[iinf]);
        float xb = ctx->atm.z[isup] - xa * logf(ctx->atm.p[isup]);
        xalt = logf(ps) * xa + xb;
    }

    /* Linearly interpolate T, wh, wo at xalt between iinf and isup */
    float dz  = ctx->atm.z[isup] - ctx->atm.z[iinf];
    float t_frac = (dz > 0.0f) ? (xalt - ctx->atm.z[iinf]) / dz : 0.0f;

    float xtemp = ctx->atm.t[iinf]  + t_frac * (ctx->atm.t[isup]  - ctx->atm.t[iinf]);
    float xwh   = ctx->atm.wh[iinf] + t_frac * (ctx->atm.wh[isup] - ctx->atm.wh[iinf]);
    float xwo   = ctx->atm.wo[iinf] + t_frac * (ctx->atm.wo[isup] - ctx->atm.wo[iinf]);

    /* Rebuild profile: new bottom = (xalt, ps, xtemp, xwh, xwo)
     * then copy layers from iinf onward into positions 1, 2, ...
     * Fortran: do i=2, 33-iinf+1  → 0-based: i=1 to 32-iinf */
    ctx->atm.z[0]  = xalt;
    ctx->atm.p[0]  = ps;
    ctx->atm.t[0]  = xtemp;
    ctx->atm.wh[0] = xwh;
    ctx->atm.wo[0] = xwo;

    int n_copy = 33 - iinf;   /* number of levels to copy */
    for (int i = 1; i <= n_copy; i++) {
        ctx->atm.z[i]  = ctx->atm.z[i + iinf];
        ctx->atm.p[i]  = ctx->atm.p[i + iinf];
        ctx->atm.t[i]  = ctx->atm.t[i + iinf];
        ctx->atm.wh[i] = ctx->atm.wh[i + iinf];
        ctx->atm.wo[i] = ctx->atm.wo[i + iinf];
    }

    /* Fill remaining levels with linear extrapolation to TOA */
    int l = n_copy;   /* last filled index (0-based) */
    for (int i = l + 1; i < NATM; i++) {
        float frac = (float)(i - l) / (float)(NATM - 1 - l);
        ctx->atm.z[i]  = ctx->atm.z[l]  + (ctx->atm.z[NATM-1]  - ctx->atm.z[l])  * frac;
        ctx->atm.p[i]  = ctx->atm.p[l]  + (ctx->atm.p[NATM-1]  - ctx->atm.p[l])  * frac;
        ctx->atm.t[i]  = ctx->atm.t[l]  + (ctx->atm.t[NATM-1]  - ctx->atm.t[l])  * frac;
        ctx->atm.wh[i] = ctx->atm.wh[l] + (ctx->atm.wh[NATM-1] - ctx->atm.wh[l]) * frac;
        ctx->atm.wo[i] = ctx->atm.wo[l] + (ctx->atm.wo[NATM-1] - ctx->atm.wo[l]) * frac;
    }
}

/**
 * \brief Adjust atmospheric profile and return integrated column amounts.
 *
 * Convenience wrapper: calls sixs_pressure() to adjust the profile to the
 * given surface condition, then calls compute_columns() to return the
 * integrated water vapour and ozone column amounts needed for gas transmittance
 * calculations.
 *
 * \param[in,out] ctx   6SV context; \c ctx->atm is modified in place.
 * \param[in]     sp    Surface pressure (hPa, >0), altitude (km, <0, negated),
 *                      or 0 to leave the profile unchanged.
 * \param[out]    uw    Integrated water vapour column (g cm⁻²).
 * \param[out]    uo3   Integrated ozone column (Dobson units).
 */
void sixs_pressure_columns(SixsCtx *ctx, float sp, float *uw, float *uo3)
{
    sixs_pressure(ctx, sp);
    compute_columns(ctx, uw, uo3);
}
