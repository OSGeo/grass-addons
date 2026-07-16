/**
 * \file sixs_ctx.h
 * \brief Internal 6SV2.1 computation context — C replacement for Fortran COMMON blocks.
 *
 * Each LUT computation thread owns one ::SixsCtx instance allocated on the
 * heap.  Separating per-thread context from global state enables OpenMP
 * parallelism over the AOD grid without locks.
 *
 * The struct layout mirrors the Fortran COMMON blocks in the 6SV2.1 source:
 *   - \c /sixs_atm/  → ::SixsAtm
 *   - \c /sixs_del/  → ::SixsDel
 *   - \c /sixs_aer/  → ::SixsAer
 *   - \c /sixs_disc/ → ::SixsDisc  (DISCOM output at 20 reference wavelengths)
 *   - \c /sixs_polar/→ ::SixsPolar (Legendre coefficients from TRUNCA)
 *   - etc.
 *
 * \warning After modifying this header, always rebuild with
 *          <tt>make clean && make</tt>.  The Makefile has no automatic
 *          header-dependency tracking; a stale \c SixsDisc layout
 *          causes a segfault inside \c sixs_gauss.
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once
#include <stdbool.h>
#include <stdint.h>

/** \defgroup sixs_dims 6SV array dimension constants
 *  Matching the corresponding \c paramdef.inc constants.
 *  @{ */
#define MU_P      25    /*!< Streams per hemisphere */
#define NT_P      30    /*!< Maximum atmospheric layers */
#define NP_P      49    /*!< φ grid points */
#define NQ_P      83    /*!< Default Gauss quadrature points */
#define NQ_MAX    1001  /*!< Maximum quadrature points */
#define NWL_DISC  20    /*!< Number of discrete reference wavelengths */
#define NATM      34    /*!< Standard atmosphere layers (ODRAYL / ABSTRA) */
/** @} */

/**
 * \brief Standard atmosphere profile (\c /sixs_atm/).
 *
 * Holds the 34-layer US Standard Atmosphere (or user-supplied profile)
 * used by the Rayleigh and gas-absorption subroutines.
 */
typedef struct {
    float z[NATM];   /*!< Layer altitude [km] */
    float p[NATM];   /*!< Layer pressure [hPa] */
    float t[NATM];   /*!< Layer temperature [K] */
    float wh[NATM];  /*!< Water-vapour density [g/m³] */
    float wo[NATM];  /*!< Ozone density [g/m³] */
} SixsAtm;

/**
 * \brief Depolarization factors (\c /sixs_del/).
 */
typedef struct {
    float delta;   /*!< Depolarization factor (King factor) */
    float sigma;   /*!< Unused in scalar mode */
} SixsDel;

/**
 * \brief Aerosol optical properties at NWL_DISC reference wavelengths (\c /sixs_aer/).
 */
typedef struct {
    float ext[NWL_DISC];    /*!< Extinction coefficient (normalised) */
    float ome[NWL_DISC];    /*!< Single-scattering albedo ω₀ */
    float gasym[NWL_DISC];  /*!< Asymmetry parameter g */
    float phase[NWL_DISC];  /*!< Phase function at the scattering angle */
} SixsAer;

/**
 * \brief Legendre expansion coefficients from TRUNCA (\c /sixs_polar/).
 *
 * Used by the successive-orders (OS/OSPOL) radiative-transfer solver.
 */
typedef struct {
    float pha[NQ_P];          /*!< Phase function at Gauss quadrature points */
    float alphal[NQ_P + 1];   /*!< Legendre coefficients for polarized RT */
    float betal[NQ_P + 1];    /*!< Legendre coefficients for scalar RT */
    float gammal[NQ_P + 1];   /*!< γ Legendre expansion */
    float zetal[NQ_P + 1];    /*!< ζ Legendre expansion */
} SixsPolar;

/**
 * \brief DISCOM output at NWL_DISC reference wavelengths (\c /sixs_disc/).
 *
 * Populated by sixs_discom() for a single AOD point; subsequently interpolated
 * to sensor wavelengths in sixs_interp() / sixs_interp_polar().
 *
 * All arrays have dimension [3][NWL_DISC] for [Rayleigh, mixed, aerosol].
 */
typedef struct {
    float roatm[3][NWL_DISC];   /*!< Atmospheric reflectance — Stokes I component */
    float roatmq[3][NWL_DISC];  /*!< Q Stokes component (filled only when ipol=1) */
    float roatmu[3][NWL_DISC];  /*!< U Stokes component (filled only when ipol=1) */
    float dtdir[3][NWL_DISC];   /*!< Downward direct transmittance */
    float dtdif[3][NWL_DISC];   /*!< Downward diffuse transmittance */
    float utdir[3][NWL_DISC];   /*!< Upward direct transmittance */
    float utdif[3][NWL_DISC];   /*!< Upward diffuse transmittance */
    float sphal[3][NWL_DISC];   /*!< Spherical albedo */
    float wldis[NWL_DISC];      /*!< Reference wavelengths [µm] */
    float trayl[NWL_DISC];      /*!< Rayleigh optical depth */
    float traypl[NWL_DISC];     /*!< Rayleigh OD above the sensor level */
} SixsDisc;

/**
 * \brief Gauss quadrature order (\c /num_quad/).
 */
typedef struct {
    int nquad; /*!< Current number of Gauss quadrature points */
} SixsQuad;

/**
 * \brief Maximum scattering order (\c /multorder/).
 */
typedef struct {
    int igmax; /*!< Maximum scattering orders (default: 20) */
} SixsMultiOrder;

/**
 * \brief Error / output state.
 */
typedef struct {
    int  iwr;  /*!< Output unit (unused in C port; always stdout) */
    bool ier;  /*!< Error flag; set on fatal RT failure */
} SixsErr;

/**
 * \brief Aerosol vertical profile discretised into NT_P layers (\c /aeroprof/).
 */
typedef struct {
    float ext_layer[NT_P]; /*!< Relative aerosol extinction per layer */
    float ome_layer[NT_P]; /*!< Single-scattering albedo per layer */
    int   n_layers;        /*!< Number of filled layers (≤ NT_P) */
} SixsAerProf;

/**
 * \brief Master 6SV computation context — one instance per OpenMP thread.
 *
 * Aggregates all Fortran COMMON-block equivalents.  The Gauss quadrature
 * arrays \c rm and \c gb are stored with an offset of \c MU_P so that the
 * original negative indices (−MU_P … MU_P) map to [0 … 2·MU_P].
 * Use the convenience macros RM() and GB() for indexed access.
 */
typedef struct {
    SixsAtm        atm;     /*!< Atmosphere profile */
    SixsDel        del;     /*!< Depolarization */
    SixsAer        aer;     /*!< Aerosol optical properties */
    SixsAerProf    aerprof; /*!< Aerosol vertical profile */
    SixsPolar      polar;   /*!< Legendre coefficients */
    SixsDisc       disc;    /*!< DISCOM output */
    SixsQuad       quad;    /*!< Quadrature order */
    SixsMultiOrder multi;   /*!< Max scattering order */
    SixsErr        err;     /*!< Error state */
    float rm[2 * MU_P + 1]; /*!< Gauss cosines (index offset by MU_P) */
    float gb[2 * MU_P + 1]; /*!< Gauss weights (index offset by MU_P) */
} SixsCtx;

/**
 * \brief Access \c rm[i] with the original Fortran index i ∈ [−MU_P, MU_P].
 * \param ctx Pointer to a ::SixsCtx.
 * \param i   Original (possibly negative) Fortran index.
 */
#define RM(ctx, i)  ((ctx)->rm[(i) + MU_P])

/**
 * \brief Access \c gb[i] with the original Fortran index i ∈ [−MU_P, MU_P].
 * \param ctx Pointer to a ::SixsCtx.
 * \param i   Original (possibly negative) Fortran index.
 */
#define GB(ctx, i)  ((ctx)->gb[(i) + MU_P])
