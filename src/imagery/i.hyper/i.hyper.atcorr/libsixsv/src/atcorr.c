/**
 * \file atcorr.c
 * \brief Shared library entry point: version string and input validation.
 *
 * Implements atcorr_version() and the input-validation wrapper around
 * atcorr_compute_lut().  The actual LUT computation is in lut.c.
 */
#include "../include/atcorr.h"
#include "../include/sixs_ctx.h"
#include <string.h>

/**
 * \brief Return the grass_sixsv library version string.
 *
 * The string includes the library name and semantic version.
 *
 * \return Pointer to a static NUL-terminated version string.
 */
const char *atcorr_version(void)
{
    return "libsixsv 2.0.0 (6SV2.1 port)";
}
