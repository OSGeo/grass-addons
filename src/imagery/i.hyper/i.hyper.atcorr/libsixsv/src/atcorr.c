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
 * The string includes the module name, semantic version, and build date:
 * \c "i.hyper.atcorr M.N.P (6SV2.1 port, <date>)".
 *
 * \return Pointer to a static NUL-terminated version string.
 */
const char *atcorr_version(void)
{
    return "i.hyper.atcorr 0.1.0 (6SV2.1 port, " __DATE__ ")";
}
