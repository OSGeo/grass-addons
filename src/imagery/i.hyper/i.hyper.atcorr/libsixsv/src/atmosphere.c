/* Standard atmosphere profiles — ported from 6SV2.1 US62.f, MIDSUM.f etc. */
#include "../include/sixs_ctx.h"
#include <string.h>

/* ─── US Standard 1962 ────────────────────────────────────────────────────── */
static const float z6[NATM] = {
    0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,
    18.,19.,20.,21.,22.,23.,24.,25.,30.,35.,40.,45.,50.,70.,100.,99999.
};
static const float p6[NATM] = {
    1.013e3f,8.986e2f,7.950e2f,7.012e2f,6.166e2f,5.405e2f,4.722e2f,4.111e2f,
    3.565e2f,3.080e2f,2.650e2f,2.270e2f,1.940e2f,1.658e2f,1.417e2f,1.211e2f,
    1.035e2f,8.850e1f,7.565e1f,6.467e1f,5.529e1f,4.729e1f,4.047e1f,3.467e1f,
    2.972e1f,2.549e1f,1.197e1f,5.746e0f,2.871e0f,1.491e0f,7.978e-1f,
    5.520e-2f,3.008e-4f,0.0f
};
static const float t6[NATM] = {
    2.881e2f,2.816e2f,2.751e2f,2.687e2f,2.622e2f,2.557e2f,2.492e2f,2.427e2f,
    2.362e2f,2.297e2f,2.232e2f,2.168e2f,2.166e2f,2.166e2f,2.166e2f,2.166e2f,
    2.166e2f,2.166e2f,2.166e2f,2.166e2f,2.166e2f,2.176e2f,2.186e2f,2.196e2f,
    2.206e2f,2.216e2f,2.265e2f,2.365e2f,2.534e2f,2.642e2f,2.706e2f,
    2.197e2f,2.100e2f,2.100e2f
};
static const float wh6[NATM] = {
    5.900e0f,4.200e0f,2.900e0f,1.800e0f,1.100e0f,6.400e-1f,3.800e-1f,2.100e-1f,
    1.200e-1f,4.600e-2f,1.800e-2f,8.200e-3f,3.700e-3f,1.800e-3f,8.400e-4f,
    7.200e-4f,6.100e-4f,5.200e-4f,4.400e-4f,4.400e-4f,4.400e-4f,4.800e-4f,
    5.200e-4f,5.700e-4f,6.100e-4f,6.600e-4f,3.800e-4f,1.600e-4f,6.700e-5f,
    3.200e-5f,1.200e-5f,1.500e-7f,1.000e-9f,0.0f
};
static const float wo6[NATM] = {
    5.400e-5f,5.400e-5f,5.400e-5f,5.000e-5f,4.600e-5f,4.600e-5f,4.500e-5f,
    4.900e-5f,5.200e-5f,7.100e-5f,9.000e-5f,1.300e-4f,1.600e-4f,1.700e-4f,
    1.900e-4f,2.100e-4f,2.400e-4f,2.800e-4f,3.200e-4f,3.500e-4f,3.800e-4f,
    3.800e-4f,3.900e-4f,3.800e-4f,3.600e-4f,3.400e-4f,2.000e-4f,1.100e-4f,
    4.900e-5f,1.700e-5f,4.000e-6f,8.600e-8f,4.300e-11f,0.0f
};

/* ─── Mid-latitude winter (MIDWIN.f) ─────────────────────────────────────── */
static const float zmw[NATM] = {
    0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,
    18.,19.,20.,21.,22.,23.,24.,25.,30.,35.,40.,45.,50.,70.,100.,99999.
};
static const float pmw[NATM] = {
    1.018e3f,8.973e2f,7.897e2f,6.938e2f,6.081e2f,5.313e2f,4.627e2f,4.016e2f,
    3.473e2f,2.992e2f,2.568e2f,2.199e2f,1.882e2f,1.610e2f,1.378e2f,1.178e2f,
    1.007e2f,8.610e1f,7.350e1f,6.280e1f,5.370e1f,4.580e1f,3.910e1f,3.340e1f,
    2.860e1f,2.430e1f,1.110e1f,5.180e0f,2.530e0f,1.290e0f,6.820e-1f,
    4.670e-2f,3.000e-4f,0.0f
};
static const float tmw[NATM] = {
    2.722e2f,2.687e2f,2.652e2f,2.617e2f,2.557e2f,2.497e2f,2.437e2f,2.377e2f,
    2.317e2f,2.257e2f,2.197e2f,2.192e2f,2.187e2f,2.182e2f,2.177e2f,2.172e2f,
    2.167e2f,2.162e2f,2.157e2f,2.152e2f,2.152e2f,2.152e2f,2.152e2f,2.152e2f,
    2.152e2f,2.152e2f,2.174e2f,2.278e2f,2.432e2f,2.585e2f,2.657e2f,
    2.307e2f,2.102e2f,2.100e2f
};
static const float whmw[NATM] = {
    3.500e0f,2.500e0f,1.800e0f,1.200e0f,6.600e-1f,3.800e-1f,2.100e-1f,8.500e-2f,
    3.500e-2f,1.600e-2f,7.500e-3f,6.900e-3f,6.000e-3f,1.800e-3f,1.000e-3f,
    7.600e-4f,6.400e-4f,5.600e-4f,5.000e-4f,4.900e-4f,4.500e-4f,5.100e-4f,
    5.100e-4f,5.400e-4f,6.000e-4f,6.700e-4f,3.600e-4f,1.100e-4f,4.300e-5f,
    1.900e-5f,6.300e-6f,1.400e-7f,1.000e-9f,0.0f
};
static const float womw[NATM] = {
    6.000e-5f,5.400e-5f,4.900e-5f,4.900e-5f,4.900e-5f,5.800e-5f,6.400e-5f,
    7.700e-5f,9.000e-5f,1.200e-4f,1.600e-4f,2.100e-4f,2.600e-4f,3.000e-4f,
    3.200e-4f,3.400e-4f,3.600e-4f,3.900e-4f,4.100e-4f,4.300e-4f,4.500e-4f,
    4.300e-4f,4.300e-4f,3.900e-4f,3.600e-4f,3.400e-4f,1.900e-4f,9.200e-5f,
    4.100e-5f,1.300e-5f,4.300e-6f,8.600e-8f,4.300e-11f,0.0f
};

/* ─── Tropical (TROPIC.f) ────────────────────────────────────────────────── */
static const float ztr[NATM] = {
    0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,
    18.,19.,20.,21.,22.,23.,24.,25.,30.,35.,40.,45.,50.,70.,100.,99999.
};
static const float ptr[NATM] = {
    1.013e3f,9.040e2f,8.050e2f,7.150e2f,6.330e2f,5.590e2f,4.920e2f,4.320e2f,
    3.780e2f,3.290e2f,2.860e2f,2.470e2f,2.130e2f,1.820e2f,1.560e2f,1.320e2f,
    1.110e2f,9.370e1f,7.890e1f,6.660e1f,5.650e1f,4.800e1f,4.090e1f,3.500e1f,
    3.000e1f,2.570e1f,1.220e1f,6.000e0f,3.050e0f,1.590e0f,8.540e-1f,
    5.790e-2f,3.000e-4f,0.0f
};
static const float ttr[NATM] = {
    3.000e2f,2.940e2f,2.880e2f,2.840e2f,2.770e2f,2.700e2f,2.640e2f,2.570e2f,
    2.500e2f,2.440e2f,2.370e2f,2.300e2f,2.240e2f,2.170e2f,2.100e2f,2.040e2f,
    1.970e2f,1.950e2f,1.990e2f,2.030e2f,2.070e2f,2.110e2f,2.150e2f,2.170e2f,
    2.190e2f,2.210e2f,2.320e2f,2.430e2f,2.540e2f,2.650e2f,2.700e2f,
    2.190e2f,2.100e2f,2.100e2f
};
static const float whtr[NATM] = {
    1.900e1f,1.300e1f,9.300e0f,4.700e0f,2.200e0f,1.500e0f,8.500e-1f,4.700e-1f,
    2.500e-1f,1.200e-1f,5.000e-2f,1.700e-2f,6.000e-3f,1.800e-3f,1.000e-3f,
    7.600e-4f,6.400e-4f,5.600e-4f,5.000e-4f,4.900e-4f,4.500e-4f,5.100e-4f,
    5.100e-4f,5.400e-4f,6.000e-4f,6.700e-4f,3.600e-4f,1.100e-4f,4.300e-5f,
    1.900e-5f,6.300e-6f,1.400e-7f,1.000e-9f,0.0f
};
static const float wotr[NATM] = {
    5.600e-5f,5.600e-5f,5.400e-5f,5.100e-5f,4.700e-5f,4.500e-5f,4.300e-5f,
    4.100e-5f,3.900e-5f,3.900e-5f,3.900e-5f,4.100e-5f,4.300e-5f,4.500e-5f,
    4.500e-5f,4.700e-5f,4.700e-5f,6.900e-5f,9.000e-5f,1.400e-4f,1.900e-4f,
    2.400e-4f,2.800e-4f,3.200e-4f,3.400e-4f,3.400e-4f,2.400e-4f,9.200e-5f,
    4.100e-5f,1.300e-5f,4.300e-6f,8.600e-8f,4.300e-11f,0.0f
};

/* ─── Sub-arctic summer (SUBSUM.f) ───────────────────────────────────────── */
static const float zss[NATM] = {
    0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,
    18.,19.,20.,21.,22.,23.,24.,25.,30.,35.,40.,45.,50.,70.,100.,99999.
};
static const float pss[NATM] = {
    1.010e3f,8.960e2f,7.929e2f,7.000e2f,6.160e2f,5.410e2f,4.730e2f,4.130e2f,
    3.590e2f,3.107e2f,2.677e2f,2.300e2f,1.977e2f,1.700e2f,1.460e2f,1.250e2f,
    1.080e2f,9.280e1f,7.980e1f,6.860e1f,5.890e1f,5.070e1f,4.360e1f,3.750e1f,
    3.227e1f,2.780e1f,1.340e1f,6.610e0f,3.400e0f,1.810e0f,9.870e-1f,
    7.070e-2f,3.000e-4f,0.0f
};
static const float tss[NATM] = {
    2.870e2f,2.820e2f,2.760e2f,2.710e2f,2.660e2f,2.600e2f,2.530e2f,2.460e2f,
    2.390e2f,2.320e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,
    2.250e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,2.250e2f,
    2.260e2f,2.280e2f,2.350e2f,2.470e2f,2.620e2f,2.740e2f,2.770e2f,
    2.160e2f,2.100e2f,2.100e2f
};
static const float whss[NATM] = {
    9.100e0f,6.000e0f,4.200e0f,2.700e0f,1.700e0f,1.000e0f,5.400e-1f,2.900e-1f,
    1.300e-1f,4.200e-2f,1.500e-2f,9.400e-3f,6.000e-3f,1.800e-3f,1.000e-3f,
    7.600e-4f,6.400e-4f,5.600e-4f,5.000e-4f,4.900e-4f,4.500e-4f,5.100e-4f,
    5.100e-4f,5.400e-4f,6.000e-4f,6.700e-4f,3.600e-4f,1.100e-4f,4.300e-5f,
    1.900e-5f,6.300e-6f,1.400e-7f,1.000e-9f,0.0f
};
static const float woss[NATM] = {
    4.900e-5f,5.400e-5f,5.600e-5f,5.800e-5f,6.000e-5f,6.400e-5f,7.100e-5f,
    7.500e-5f,7.900e-5f,1.100e-4f,1.300e-4f,1.800e-4f,2.100e-4f,2.600e-4f,
    2.800e-4f,3.200e-4f,3.400e-4f,3.900e-4f,4.100e-4f,4.100e-4f,3.900e-4f,
    3.600e-4f,3.200e-4f,3.000e-4f,2.800e-4f,2.600e-4f,1.400e-4f,9.200e-5f,
    4.100e-5f,1.300e-5f,4.300e-6f,8.600e-8f,4.300e-11f,0.0f
};

/* ─── Sub-arctic winter (SUBWIN.f) ───────────────────────────────────────── */
static const float zsw[NATM] = {
    0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,
    18.,19.,20.,21.,22.,23.,24.,25.,30.,35.,40.,45.,50.,70.,100.,99999.
};
static const float psw[NATM] = {
    1.013e3f,8.878e2f,7.775e2f,6.798e2f,5.932e2f,5.158e2f,4.467e2f,3.853e2f,
    3.308e2f,2.829e2f,2.418e2f,2.067e2f,1.766e2f,1.510e2f,1.291e2f,1.103e2f,
    9.431e1f,8.058e1f,6.882e1f,5.875e1f,5.014e1f,4.277e1f,3.647e1f,3.109e1f,
    2.649e1f,2.256e1f,1.020e1f,4.701e0f,2.243e0f,1.113e0f,5.719e-1f,
    4.016e-2f,3.000e-4f,0.0f
};
static const float tsw[NATM] = {
    2.571e2f,2.591e2f,2.559e2f,2.527e2f,2.477e2f,2.409e2f,2.341e2f,2.273e2f,
    2.206e2f,2.172e2f,2.172e2f,2.172e2f,2.172e2f,2.172e2f,2.172e2f,2.172e2f,
    2.166e2f,2.160e2f,2.154e2f,2.148e2f,2.141e2f,2.136e2f,2.130e2f,2.124e2f,
    2.118e2f,2.112e2f,2.160e2f,2.222e2f,2.347e2f,2.470e2f,2.593e2f,
    2.457e2f,2.100e2f,2.100e2f
};
static const float whsw[NATM] = {
    1.200e0f,1.200e0f,9.400e-1f,6.800e-1f,4.100e-1f,2.000e-1f,9.800e-2f,5.400e-2f,
    1.100e-2f,8.400e-3f,5.500e-3f,3.800e-3f,2.600e-3f,1.800e-3f,1.000e-3f,
    7.600e-4f,6.400e-4f,5.600e-4f,5.000e-4f,4.900e-4f,4.500e-4f,5.100e-4f,
    5.100e-4f,5.400e-4f,6.000e-4f,6.700e-4f,3.600e-4f,1.100e-4f,4.300e-5f,
    1.900e-5f,6.300e-6f,1.400e-7f,1.000e-9f,0.0f
};
static const float wosw[NATM] = {
    4.100e-5f,4.100e-5f,4.100e-5f,4.300e-5f,4.500e-5f,4.700e-5f,4.900e-5f,
    7.100e-5f,9.000e-5f,1.600e-4f,2.400e-4f,3.200e-4f,4.300e-4f,4.700e-4f,
    4.900e-4f,5.600e-4f,6.200e-4f,6.200e-4f,6.200e-4f,6.000e-4f,5.600e-4f,
    5.100e-4f,4.700e-4f,4.300e-4f,3.600e-4f,3.200e-4f,1.500e-4f,9.200e-5f,
    4.100e-5f,1.300e-5f,4.300e-6f,8.600e-8f,4.300e-11f,0.0f
};

/* ─── Mid-latitude summer ─────────────────────────────────────────────────── */
static const float zms[NATM] = {
    0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,
    18.,19.,20.,21.,22.,23.,24.,25.,30.,35.,40.,45.,50.,70.,100.,99999.
};
static const float pms[NATM] = {
    1.013e3f,9.020e2f,8.020e2f,7.100e2f,6.280e2f,5.540e2f,4.870e2f,4.260e2f,
    3.720e2f,3.240e2f,2.810e2f,2.430e2f,2.090e2f,1.790e2f,1.530e2f,1.310e2f,
    1.110e2f,9.500e1f,8.120e1f,6.950e1f,5.950e1f,5.100e1f,4.370e1f,3.760e1f,
    3.220e1f,2.770e1f,1.320e1f,6.520e0f,3.330e0f,1.760e0f,9.510e-1f,
    6.710e-2f,3.000e-4f,0.0f
};
static const float tms[NATM] = {
    2.940e2f,2.900e2f,2.850e2f,2.790e2f,2.730e2f,2.670e2f,2.610e2f,2.545e2f,
    2.480e2f,2.420e2f,2.355e2f,2.290e2f,2.220e2f,2.160e2f,2.160e2f,2.160e2f,
    2.160e2f,2.160e2f,2.160e2f,2.175e2f,2.190e2f,2.210e2f,2.250e2f,2.290e2f,
    2.330e2f,2.370e2f,2.590e2f,2.730e2f,2.770e2f,2.690e2f,2.550e2f,
    2.190e2f,2.100e2f,2.100e2f
};
static const float whms[NATM] = {
    1.400e1f,9.300e0f,5.900e0f,3.300e0f,1.900e0f,1.000e0f,6.100e-1f,3.700e-1f,
    2.100e-1f,1.200e-1f,6.400e-2f,2.200e-2f,6.000e-3f,1.800e-3f,1.000e-3f,
    7.600e-4f,6.400e-4f,5.600e-4f,5.000e-4f,4.900e-4f,4.500e-4f,5.100e-4f,
    5.100e-4f,5.400e-4f,6.000e-4f,6.700e-4f,3.600e-4f,1.100e-4f,4.300e-5f,
    1.900e-5f,6.300e-6f,1.400e-7f,1.000e-9f,0.0f
};
static const float woms[NATM] = {
    6.000e-5f,6.000e-5f,6.000e-5f,6.200e-5f,6.400e-5f,6.600e-5f,6.900e-5f,
    7.500e-5f,7.900e-5f,1.100e-4f,1.500e-4f,2.100e-4f,2.700e-4f,2.900e-4f,
    3.200e-4f,3.400e-4f,3.800e-4f,4.100e-4f,4.300e-4f,4.500e-4f,4.300e-4f,
    4.300e-4f,3.900e-4f,3.600e-4f,3.400e-4f,3.200e-4f,1.500e-4f,9.200e-5f,
    4.100e-5f,1.300e-5f,4.300e-6f,8.600e-8f,4.300e-11f,0.0f
};

/**
 * \brief Initialise the standard atmosphere profile in a 6SV context.
 *
 * Copies the altitude, pressure, temperature, water-vapour, and ozone
 * profiles for the selected standard model into \c ctx->atm.
 *
 * Ported from 6SV2.1 US62.f / MIDSUM.f / MIDWIN.f / TROPICAL.f / SUBSUM.f / SUBWIN.f.
 *
 * \param[in,out] ctx         6SV context; writes \c ctx->atm on return.
 * \param[in]     atmo_model  Atmosphere model:
 *                            - \c ATMO_US62    (1) — US Standard 1962
 *                            - \c ATMO_MIDSUM  (2) — Mid-latitude summer
 *                            - \c ATMO_MIDWIN  (3) — Mid-latitude winter
 *                            - \c ATMO_TROPICAL (4) — Tropical
 *                            - \c ATMO_SUBSUM  (5) — Sub-arctic summer
 *                            - \c ATMO_SUBWIN  (6) — Sub-arctic winter
 */
void sixs_init_atmosphere(SixsCtx *ctx, int atmo_model) {
    const float *z, *p, *t, *wh, *wo;
    switch (atmo_model) {
        case 2:  z=zms; p=pms; t=tms; wh=whms; wo=woms; break;
        case 3:  z=zmw; p=pmw; t=tmw; wh=whmw; wo=womw; break;
        case 4:  z=ztr; p=ptr; t=ttr; wh=whtr; wo=wotr; break;
        case 5:  z=zss; p=pss; t=tss; wh=whss; wo=woss; break;
        case 6:  z=zsw; p=psw; t=tsw; wh=whsw; wo=wosw; break;
        default: z=z6;  p=p6;  t=t6;  wh=wh6;  wo=wo6; break;
    }
    for (int i = 0; i < NATM; i++) {
        ctx->atm.z[i]  = z[i];
        ctx->atm.p[i]  = p[i];
        ctx->atm.t[i]  = t[i];
        ctx->atm.wh[i] = wh[i];
        ctx->atm.wo[i] = wo[i];
    }
    /* Rayleigh depolarization factor for air (6SV standard) */
    ctx->del.delta = 0.0279f;
    ctx->del.sigma = 0.0f;
    /* Default quadrature */
    ctx->quad.nquad = NQ_P;
    ctx->multi.igmax = 20;
    ctx->err.ier = false;
}
