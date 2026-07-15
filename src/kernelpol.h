#pragma once
#include "../include/sixs_ctx.h"

/* Polarized scattering kernel — ported from 6SV2.1 KERNELPOL.f
 *
 * Extends sixs_kernel() to also compute the Q/U generalized spherical
 * functions (rsl, tsl) and the Müller matrix off-diagonal terms (arr, att,
 * art).  Aerosol is treated as spherical (gammal = zetal = 0, alphal =
 * betal): aerosol scattering maintains the polarisation state but does NOT
 * generate polarisation from unpolarised intensity (gr = gt = 0).  The
 * Rayleigh I↔Q,U coupling is handled in-line in sixs_ospol() via gamma2. */
void sixs_kernelpol(const SixsCtx *ctx, int is, int mu,
                    const float *rm_off,    /* rm_off[j+mu] = rm[j], j=-mu..mu */
                    double *xpl_off,        /* out: psl[2,:], 2mu+1 entries */
                    double *xrl_off,        /* out: rsl[2,:], 2mu+1 entries */
                    double *xtl_off,        /* out: tsl[2,:], 2mu+1 entries */
                    double *psl,            /* work: (NQ_P+2)*(2mu+1) */
                    double *rsl,            /* work: (NQ_P+2)*(2mu+1) */
                    double *tsl,            /* work: (NQ_P+2)*(2mu+1) */
                    double *bp,             /* out: I→I,   (mu+1)*(2mu+1) */
                    double *arr,            /* out: Q→Q,   (mu+1)*(2mu+1) */
                    double *art,            /* out: U→Q,   (mu+1)*(2mu+1) */
                    double *att);           /* out: U→U,   (mu+1)*(2mu+1) */
