/**
 * \file main.c
 * \brief GRASS GIS module \c i.hyper.atcorr — 6SV2.1-based atmospheric correction.
 *
 * MODULE:      i.hyper.atcorr
 * AUTHOR(S):   Yann Chemin, Seilio Douar EI; Tomaž Žagar,
 *              Geodetic Institute of Slovenia
 * PURPOSE:     6SV2.1-based atmospheric correction for hyperspectral imagery.
 *
 * COPYRIGHT:   (C) 2024-2026 by Yann Chemin, Tomaž Žagar and the GRASS
 *              Development Team
 *
 *              This program is free software under the GNU General Public
 *              License (>=v2).  Read the file COPYING that comes with GRASS
 *              for details.
 *
 * Two operational modes (at least one output must be requested):
 *
 *   lut=   — write a binary LUT file [R_atm, T_down, T_up, s_alb] on an
 *             [AOD × H2O × wavelength] grid for use by i.hyper.smac.
 *
 *   input= / output= — correct a Raster3D radiance cube to surface (BOA)
 *             reflectance using the computed LUT.  Band centre wavelengths are
 *             read from the map's r3.info metadata; fallback to the LUT grid.
 *
 * Physics (6SV standard):
 *   ρ_toa = (π × L × d²) / (E₀ × cos θs)
 *   ρ_boa = (ρ_toa − R_atm) / (T_down × T_up × (1 + s_alb × ρ_boa))
 *
 * ISOFIT-inspired improvements (all optional):
 *   #1 Per-pixel AOD/H2O raster maps + Gaussian spatial smoothing
 *   #2 In-loop Vermote adjacency effect correction (adj_psf= option)
 *   #3 Surface prior MAP regularisation (-r flag)
 *   #4 Per-band reflectance uncertainty output (-u flag, uncertainty= option)
 *   #5 Analytical MAP inner loop via surface_model_regularize()
 *   #6 Per-band model discrepancy floor (added in quadrature to σ² before MAP)
 *
 * LUT file format (host-endian binary):
 *   magic     uint32  0x4C555400 ("LUT\0")
 *   version   uint32  1
 *   n_aod, n_h2o, n_wl  int32 each
 *   aod[n_aod]  float32
 *   h2o[n_h2o]  float32
 *   wl [n_wl]   float32  (µm)
 *   R_atm, T_down, T_up, s_alb  float32[n_aod*n_h2o*n_wl] each (C order)
 ****************************************************************************/

#define _POSIX_C_SOURCE 200112L

/* Use standalone ras3d library when available (outside GRASS GIS).
 * ras3d.h provides drop-in replacements for all four GRASS headers below. */
#if defined(HAVE_RAS3D) && !defined(GRASS_VERSION_MAJOR)
#  include <ras3d/ras3d.h>
#else
#  include <grass/gis.h>
#  include <grass/glocale.h>
#  include <grass/raster.h>
#  include <grass/raster3d.h>
#  include <grass/spawn.h>
#endif

#include <ctype.h>
#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "atcorr.h"
#include "solar_table.h"
#include "spatial.h"
#include "adjacency.h"
#include "surface_model.h"
#include "uncertainty.h"
#include "retrieve.h"
#include "terrain.h"
#include "oe_invert.h"
#include "spectral_brdf.h"

#define LUT_MAGIC   0x4C555400u
#define LUT_VERSION 1u

/* ── ISOFIT improvement parameters ──────────────────────────────────────────── */

typedef struct {
    /* #1 Per-pixel atmospheric maps + smoothing */
    const char *aod_map;      /* 2-D raster name, or NULL for scalar */
    const char *h2o_map;      /* 2-D raster name, or NULL for scalar */
    float      *aod_data;     /* pre-computed AOD [nrows*ncols], or NULL (overrides aod_map) */
    float      *h2o_data;     /* pre-computed H2O [nrows*ncols], or NULL (overrides h2o_map) */
    float       smooth_sigma; /* Gaussian σ in pixels (0 = disabled) */

    /* #2 Adjacency correction */
    float adj_psf_km;         /* Environmental PSF radius in km (0 = disabled) */
    float pixel_size_m;       /* Pixel size in metres (0 = auto from region) */

    /* #3/#5 Surface prior MAP regularisation */
    int   do_surface_prior;   /* 0 = disabled */

    /* #4/#6 Uncertainty */
    int         do_uncertainty;
    const char *unc_output;   /* Output Raster3D name, or NULL */

    /* Terrain illumination correction */
    const char *slope_map;        /* 2-D slope raster [°], or NULL */
    const char *aspect_map;       /* 2-D aspect raster [°, CW from North], or NULL */
    float       sun_azimuth;      /* solar azimuth [°, CW from North] */
    const char *vza_map;          /* 2-D per-pixel VZA raster [°], or NULL */
    const char *vaa_map;          /* 2-D per-pixel VAA raster [°, CW from North], or NULL */

    /* NBAR normalization (Ross-Li kernel weights, e.g. from MCD43) */
    const char *brdf_fiso_map;    /* f_iso raster, or NULL */
    const char *brdf_fvol_map;    /* f_vol raster, or NULL */
    const char *brdf_fgeo_map;    /* f_geo raster, or NULL */

    /* Per-pixel O₂-A surface pressure (hPa) */
    float      *pressure_data;    /* float[nrows*ncols] or NULL */

    /* Pre-computed quality bitmask (RETRIEVE_MASK_*) */
    uint8_t    *quality_data;     /* uint8_t[nrows*ncols] or NULL */

    /* FlexBRDF: spectrally disaggregated MCD43 kernel weights [n_wl] */
    float      *flex_fiso_wl;     /* float[n_wl] or NULL (= scalar NBAR) */
    float      *flex_fvol_wl;     /* float[n_wl] or NULL */
    float      *flex_fgeo_wl;     /* float[n_wl] or NULL */
    float       flex_fiso_ref;    /* f_iso at NIR reference (858 nm) */
    float       flex_fvol_ref;    /* f_vol at NIR reference (858 nm) */
    float       flex_fgeo_ref;    /* f_geo at NIR reference (858 nm) */
    int         have_flex_brdf;   /* 1 = FlexBRDF disaggregation active */

    /* DASF retrieval output */
    const char *dasf_output;      /* 2-D raster name, or NULL */
    int         do_dasf;          /* 1 = accumulate + write DASF */
} IsoFitParams;

/* ── Metadata handling (i.hyper.metadata schema) ─────────────────────────── */

/**
 * \brief Hyperspectral metadata fields read from the input map's hyper.json
 *        sidecar (i.hyper.metadata schema).
 *
 * Populated by read_hyperjson_meta(); used to apply metadata fallback for
 * the overridable CLI options.
 */
typedef struct {
    /* Band info (wavelengths/FWHM are handled separately by parse_band_wl) */
    char   dataset_id[64];

    /* Extended-metadata fields (from extended_metadata key). */
    /* Geometry */
    int    has_sun_zenith;
    float  sun_zenith_deg;
    int    has_view_zenith;
    float  view_zenith_deg;
    int    has_relative_azimuth;
    float  relative_azimuth_deg;
    int    has_sun_azimuth;
    float  sun_azimuth_deg;
    int    has_altitude;
    float  altitude_km;

    /* Atmosphere */
    int    has_aod;
    float  aod_550;
    int    has_h2o;
    float  h2o_g_cm2;
    int    has_ozone;
    float  ozone_du;
    int    has_atmo_model;
    char   atmosphere_model[32];
    int    has_aerosol_model;
    char   aerosol_model[32];

    /* Acquisition */
    int    has_doy;
    int    day_of_year;
} HyperMeta;

/* ── Internal JSON scanner helpers ───────────────────────────────────────── */

/** \cond INTERNAL — forward declarations from existing JSON scanner */
static int json_extract_array(const char *json, const char *key,
                               double *out, int max_n);
/** \endcond */

/**
 * \brief Extract a JSON string value by key from a JSON text buffer.
 *
 * Finds the first occurrence of ``"key": "value"`` and copies the
 * unquoted value into \c out.
 *
 * \param[in]  json  NUL-terminated JSON text.
 * \param[in]  key   Key name (without quotes).
 * \param[out] out   Destination buffer.
 * \param[in]  n     Size of \c out.
 * \return 1 on success, 0 if key not found.
 */
static int json_extract_string(const char *json, const char *key,
                                char *out, size_t n)
{
    char pattern[64];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char *p = strstr(json, pattern);
    if (!p) return 0;
    p = strchr(p + strlen(pattern), ':');
    if (!p) return 0;
    p++; while (*p && isspace((unsigned char)*p)) p++;
    if (*p != '"') return 0;
    p++;
    size_t i = 0;
    while (*p && *p != '"' && i + 1 < n) out[i++] = *p++;
    out[i] = '\0';
    return (i > 0) ? 1 : 0;
}

/**
 * \brief Extract a nested JSON float by dotted path.
 *
 * Finds ``"parent": { ... "key": <number> ... }`` in the JSON text.
 * Path is a single dot-separated name like \c "geometry.sun_zenith_deg".
 * Only two-level nesting is supported.
 *
 * \param[in]  json  NUL-terminated JSON text.
 * \param[in]  path  Dotted path, e.g. \c "geometry.sun_zenith_deg".
 * \param[out] out   Parsed double value.
 * \return 1 on success, 0 if path not found.
 */
static int json_extract_nested_float(const char *json, const char *path,
                                      double *out)
{
    /* Split path into parent and key */
    const char *dot = strchr(path, '.');
    if (!dot) return 0;
    size_t plen = (size_t)(dot - path);
    char parent[64], key[64];
    if (plen >= sizeof(parent)) return 0;
    memcpy(parent, path, plen); parent[plen] = '\0';
    snprintf(key, sizeof(key), "%s", dot + 1);

    /* Find parent object */
    char pbuf[80];
    snprintf(pbuf, sizeof(pbuf), "\"%s\"", parent);
    const char *p = strstr(json, pbuf);
    if (!p) return 0;
    p = strchr(p + strlen(pbuf), ':');
    if (!p) return 0;
    p = strchr(p, '{');
    if (!p) return 0;
    p++;

    /* Within the parent object, scan for the key */
    size_t klen = strlen(key);
    while (*p && *p != '}') {
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p == '}') break;
        if (*p == '"') {
            const char *kp = p + 1;
            const char *ke = strchr(kp, '"');
            if (ke && (size_t)(ke - kp) == klen && strncmp(kp, key, klen) == 0) {
                p = ke + 1;
                while (*p && isspace((unsigned char)*p)) p++;
                if (*p == ':') {
                    p++;
                    while (*p && isspace((unsigned char)*p)) p++;
                    char *endp;
                    *out = strtod(p, &endp);
                    if (endp > p) return 1;
                    break;
                }
            }
            else if (ke) {
                p = ke + 1;
            }
        }
        while (*p && *p != ',' && *p != '}') p++;
        if (*p == ',') p++;
    }
    return 0;
}

/**
 * \brief Extract a nested JSON string by dotted path.
 *
 * Like json_extract_nested_float() but for string values.
 *
 * \param[in]  json  NUL-terminated JSON text.
 * \param[in]  path  Dotted path, e.g. \c "atmosphere.model".
 * \param[out] out   Destination buffer.
 * \param[in]  n     Size of \c out.
 * \return 1 on success, 0 if path not found.
 */
static int json_extract_nested_string(const char *json, const char *path,
                                       char *out, size_t n)
{
    const char *dot = strchr(path, '.');
    if (!dot) return 0;
    size_t plen = (size_t)(dot - path);
    char parent[64], key[64];
    if (plen >= sizeof(parent)) return 0;
    memcpy(parent, path, plen); parent[plen] = '\0';
    snprintf(key, sizeof(key), "%s", dot + 1);

    char pbuf[80];
    snprintf(pbuf, sizeof(pbuf), "\"%s\"", parent);
    const char *p = strstr(json, pbuf);
    if (!p) return 0;
    p = strchr(p + strlen(pbuf), ':');
    if (!p) return 0;
    p = strchr(p, '{');
    if (!p) return 0;
    p++;

    size_t klen = strlen(key);
    while (*p && *p != '}') {
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p == '}') break;
        if (*p == '"') {
            const char *kp = p + 1;
            const char *ke = strchr(kp, '"');
            if (ke && (size_t)(ke - kp) == klen && strncmp(kp, key, klen) == 0) {
                p = ke + 1;
                while (*p && isspace((unsigned char)*p)) p++;
                if (*p == ':') {
                    p++;
                    while (*p && isspace((unsigned char)*p)) p++;
                    if (*p == '"') {
                        p++;
                        size_t i = 0;
                        while (*p && *p != '"' && i + 1 < n) out[i++] = *p++;
                        out[i] = '\0';
                        return (i > 0) ? 1 : 0;
                    }
                }
            }
            else if (ke) p = ke + 1;
        }
        while (*p && *p != ',' && *p != '}') p++;
        if (*p == ',') p++;
    }
    return 0;
}

/**
 * \brief Read hyperspectral metadata from a JSON string buffer.
 *
 * Extracts band wavelengths, FWHM (calling json_extract_array), as well as
 * the nested extended_metadata fields used for CLI-override resolution.
 *
 * \param[in]  json  NUL-terminated JSON text.
 * \param[out] wl    Band centre wavelengths (µm), length \c max_n.
 * \param[out] fwhm  Band FWHM values (µm), may be NULL.
 * \param[in]  max_n Maximum number of bands.
 * \param[out] meta  Populated HyperMeta struct.
 * \return Number of bands parsed (0 = not found / parse error).
 */
static int parse_hyperjson_buffer(const char *json, float *wl, float *fwhm,
                                   int max_n, HyperMeta *meta)
{
    if (!json || !json[0]) return 0;

    /* Band wavelengths / FWHM */
    double *wl_nm = G_malloc(sizeof(double) * (size_t)max_n);
    int n = json_extract_array(json, "wavelength", wl_nm, max_n);
    if (n == 0) { G_free(wl_nm); return 0; }

    double *fwhm_nm = fwhm ? G_malloc(sizeof(double) * (size_t)max_n) : NULL;
    int n_fwhm = fwhm ? json_extract_array(json, "fwhm", fwhm_nm, max_n) : 0;

    for (int i = 0; i < max_n; i++) {
        wl[i] = (i < n) ? (float)(wl_nm[i] * 1e-3) : -1.0f;
        if (fwhm)
            fwhm[i] = (i < n_fwhm) ? (float)(fwhm_nm[i] * 1e-3) : 0.0f;
    }
    G_free(wl_nm);
    if (fwhm_nm) G_free(fwhm_nm);

    /* Dataset ID */
    json_extract_string(json, "dataset_id", meta->dataset_id,
                         sizeof(meta->dataset_id));

    /* Extended metadata */
    double dv;
    if (json_extract_nested_float(json, "geometry.sun_zenith_deg", &dv)) {
        meta->sun_zenith_deg = (float)dv; meta->has_sun_zenith = 1;
    }
    if (json_extract_nested_float(json, "geometry.view_zenith_deg", &dv)) {
        meta->view_zenith_deg = (float)dv; meta->has_view_zenith = 1;
    }
    if (json_extract_nested_float(json, "geometry.relative_azimuth_deg", &dv)) {
        meta->relative_azimuth_deg = (float)dv; meta->has_relative_azimuth = 1;
    }
    if (json_extract_nested_float(json, "geometry.sun_azimuth_deg", &dv)) {
        meta->sun_azimuth_deg = (float)dv; meta->has_sun_azimuth = 1;
    }
    if (json_extract_nested_float(json, "atmosphere.aod_550", &dv)) {
        meta->aod_550 = (float)dv; meta->has_aod = 1;
    }
    if (json_extract_nested_float(json, "atmosphere.h2o_g_cm2", &dv)) {
        meta->h2o_g_cm2 = (float)dv; meta->has_h2o = 1;
    }
    if (json_extract_nested_float(json, "atmosphere.ozone_du", &dv)) {
        meta->ozone_du = (float)dv; meta->has_ozone = 1;
    }
    if (json_extract_nested_float(json, "acquisition.day_of_year", &dv)) {
        meta->day_of_year = (int)dv; meta->has_doy = 1;
    }
    if (json_extract_nested_float(json, "sensor.sensor_altitude_km", &dv)) {
        meta->altitude_km = (float)dv; meta->has_altitude = 1;
    }
    if (json_extract_nested_string(json, "atmosphere.model",
                                    meta->atmosphere_model,
                                    sizeof(meta->atmosphere_model))) {
        meta->has_atmo_model = 1;
    }
    if (json_extract_nested_string(json, "atmosphere.aerosol_model",
                                    meta->aerosol_model,
                                    sizeof(meta->aerosol_model))) {
        meta->has_aerosol_model = 1;
    }

    return n;
}

/**
 * \brief Read hyperspectral metadata from the input map.
 *
 * Tries \c i.hyper.metadata via \c G_popen_read() first (provides schema
 * normalisation), then falls back to reading \c hyper.json directly from
 * the filesystem (existing \c parse_band_wl_hyperjson() path).
 *
 * \param[in]  mapname  Name of the input Raster3D map.
 * \param[out] wl       Band centre wavelengths (µm), length \c max_n.
 * \param[out] fwhm     Band FWHM (µm), may be NULL.
 * \param[in]  max_n    Maximum number of bands.
 * \param[out] meta     Populated HyperMeta struct.
 * \return Number of bands parsed (0 on failure).
 */
static int read_hyperjson_meta(const char *mapname, float *wl, float *fwhm,
                                int max_n, HyperMeta *meta)
{
    memset(meta, 0, sizeof(*meta));

    /* Try i.hyper.metadata via G_popen_read */
    char maparg[GPATH_MAX];
    snprintf(maparg, sizeof(maparg), "map=%s", mapname);

    const char *args[5];
    args[0] = "i.hyper.metadata";
    args[1] = maparg;
    args[2] = "operation=full";
    args[3] = "format=json";
    args[4] = NULL;

    struct Popen child;
    FILE *fp = G_popen_read(&child, "i.hyper.metadata", args);
    if (fp) {
        /* Read entire JSON output into a buffer */
        size_t cap = 65536, len = 0;
        char *buf = G_malloc(cap);
        size_t nrd;
        while ((nrd = fread(buf + len, 1, cap - len - 1, fp)) > 0) {
            len += nrd;
            if (len + 1 >= cap) {
                cap *= 2;
                buf = G_realloc(buf, cap);
            }
        }
        buf[len] = '\0';

        int n = parse_hyperjson_buffer(buf, wl, fwhm, max_n, meta);
        G_free(buf);
        G_popen_close(&child);
        if (n > 0) return n;
    }
    else {
        /* G_popen_read failed; try direct file access */
        char nbuf[512], mset[512];
        const char *at = strchr(mapname, '@');
        if (at) {
            size_t nlen = (size_t)(at - mapname);
            if (nlen >= sizeof(nbuf)) return 0;
            memcpy(nbuf, mapname, nlen); nbuf[nlen] = '\0';
            snprintf(mset, sizeof(mset), "%s", at + 1);
        }
        else {
            snprintf(nbuf, sizeof(nbuf), "%s", mapname);
            const char *found = G_find_raster3d(mapname, "");
            if (!found) return 0;
            snprintf(mset, sizeof(mset), "%s", found);
        }

        char path[GPATH_MAX];
        snprintf(path, sizeof(path), "%s/%s/%s/grid3/%s/hyper.json",
                 G_gisdbase(), G_location(), mset, nbuf);

        FILE *ff = fopen(path, "rb");
        if (!ff) return 0;
        fseek(ff, 0, SEEK_END);
        long fsz = ftell(ff);
        fseek(ff, 0, SEEK_SET);
        if (fsz <= 0) { fclose(ff); return 0; }
        char *fbuf = G_malloc((size_t)fsz + 1);
        size_t nrd = fread(fbuf, 1, (size_t)fsz, ff);
        fclose(ff);
        fbuf[nrd] = '\0';

        int n = parse_hyperjson_buffer(fbuf, wl, fwhm, max_n, meta);
        G_free(fbuf);
        return n;
    }

    return 0;
}

/** \brief Resolve a double option: CLI → metadata → hardcoded default.
  *
  * \param[in]  opt        GRASS Option (may be NULL for unconditional default).
  * \param[in]  meta_val   Metadata value (used only when \c has_meta is set).
  * \param[in]  has_meta   Non-zero if the metadata field was found.
  * \param[in]  def_val    Hardcoded fallback default.
  * \param[in]  required   If 1 and no value is resolved, calls G_fatal_error.
  * \return Resolved value.
  */
static float resolve_float_opt(struct Option *opt, float meta_val,
                                int has_meta, float def_val, int required)
{
    if (opt && opt->answer)
        return (float)atof(opt->answer);
    if (has_meta)
        return meta_val;
    if (required)
        G_fatal_error(_("Required option <%s> not provided and not in metadata"),
                      opt ? opt->key : "?");
    return def_val;
}

/** \brief Resolve a string option: CLI → metadata → hardcoded default. */
static const char *resolve_str_opt(struct Option *opt,
                                    const char *meta_val, int has_meta,
                                    const char *def_val)
{
    if (opt && opt->answer)
        return opt->answer;
    if (has_meta && meta_val && meta_val[0])
        return meta_val;
    return def_val;
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */

/** \cond INTERNAL */

/**
 * \brief Parse a comma-separated string of floating-point numbers.
 *
 * \param[in]  str    Input string (e.g. \c "0.35,0.55,0.85").
 * \param[out] out    Output float array; must hold at least \c max_n elements.
 * \param[in]  max_n  Maximum number of values to parse.
 * \return Number of values successfully parsed, or -1 on conversion error.
 */
static int parse_csv_floats(const char *str, float *out, int max_n)
{
    char *buf = G_store(str);
    char *tok, *saveptr = NULL;
    int   n = 0;

    tok = strtok_r(buf, ",", &saveptr);
    while (tok && n < max_n) {
        char *end;
        out[n] = (float)strtod(tok, &end);
        if (end == tok) { G_free(buf); return -1; }
        n++;
        tok = strtok_r(NULL, ",", &saveptr);
    }
    G_free(buf);
    return n;
}

/** \brief Write an unsigned 32-bit value to a binary file. */
static void write_u32(FILE *fp, unsigned int v) { fwrite(&v, 4, 1, fp); }
/** \brief Write a signed 32-bit value to a binary file. */
static void write_i32(FILE *fp, int v)          { fwrite(&v, 4, 1, fp); }
/**
 * \brief Write an array of 32-bit float values to a binary file.
 * \param[in]  fp  Open file pointer.
 * \param[in]  v   Source float array.
 * \param[in]  n   Number of elements to write.
 */
static void write_f32a(FILE *fp, const float *v, size_t n)
{
    fwrite(v, sizeof(float), n, fp);
}

/**
 * \brief Extract a numeric or boolean JSON array by key from a JSON text buffer.
 *
 * Minimal, schema-specific scanner (not a general JSON parser): finds the
 * first occurrence of the given key and reads the bracketed comma-separated
 * array of numbers or true/false tokens that follows its ':'. Sufficient for
 * i.hyper.import's flat hyper.json band-metadata layout; not a substitute
 * for a real JSON library on arbitrary input.
 *
 * \param[in]  json  Full JSON text (NUL-terminated).
 * \param[in]  key   Key name to search for (without quotes).
 * \param[out] out   Destination array of doubles (1.0/0.0 for booleans).
 * \param[in]  max_n Capacity of \c out.
 * \return Number of elements parsed (0 if key not found or array empty).
 */
static int json_extract_array(const char *json, const char *key,
                               double *out, int max_n)
{
    char pattern[64];
    snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    const char *p = strstr(json, pattern);
    if (!p) return 0;
    p = strchr(p + strlen(pattern), ':');
    if (!p) return 0;
    p = strchr(p, '[');
    if (!p) return 0;
    p++;

    int n = 0;
    while (*p && *p != ']' && n < max_n) {
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p == ']') break;
        if (strncmp(p, "true", 4) == 0) {
            out[n++] = 1.0;
            p += 4;
        }
        else if (strncmp(p, "false", 5) == 0) {
            out[n++] = 0.0;
            p += 5;
        }
        else {
            char *endp;
            double v = strtod(p, &endp);
            if (endp == p) break; /* malformed entry */
            out[n++] = v;
            p = endp;
        }
        while (*p && isspace((unsigned char)*p)) p++;
        if (*p == ',') p++;
    }
    return n;
}

/**
 * \brief Parse per-band centre wavelengths and FWHM from i.hyper.import's
 *        grid3/<map>/hyper.json sidecar (HyperMetadata JSON schema).
 *
 * i.hyper.import stores band-level wavelength/FWHM/validity metadata in this
 * JSON sidecar rather than in Raster3D history text, so it must be tried
 * before falling back to parse_band_wl()'s r3.info -h parsing.
 *
 * \param[in]  mapname  Name of the GRASS Raster3D map (``name`` or
 *                      ``name@mapset``).
 * \param[out] wl       Array of band centre wavelengths (µm); length \c max_n.
 *                      Entries for unparsed bands are set to -1.
 * \param[out] fwhm     Array of band FWHM values (µm); may be NULL to skip.
 * \param[in]  max_n    Maximum number of bands to parse.
 * \return Number of bands successfully parsed (0 if sidecar not found or
 *         has no wavelength array).
 */
static int parse_band_wl_hyperjson(const char *mapname, float *wl,
                                    float *fwhm, int max_n)
{
    char name[512], mapset[512];
    const char *at = strchr(mapname, '@');
    if (at) {
        size_t nlen = (size_t)(at - mapname);
        if (nlen >= sizeof(name)) return 0;
        memcpy(name, mapname, nlen);
        name[nlen] = '\0';
        snprintf(mapset, sizeof(mapset), "%s", at + 1);
    }
    else {
        snprintf(name, sizeof(name), "%s", mapname);
        const char *found = G_find_raster3d(mapname, "");
        snprintf(mapset, sizeof(mapset), "%s", found ? found : G_mapset());
    }

    char path[GPATH_MAX];
    snprintf(path, sizeof(path), "%s/%s/%s/grid3/%s/hyper.json",
             G_gisdbase(), G_location(), mapset, name);

    FILE *f = fopen(path, "rb");
    if (!f) return 0;

    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (fsize <= 0) {
        fclose(f);
        return 0;
    }

    char *buf = G_malloc((size_t)fsize + 1);
    size_t nread = fread(buf, 1, (size_t)fsize, f);
    fclose(f);
    buf[nread] = '\0';

    double *wl_nm = G_malloc(sizeof(double) * (size_t)max_n);
    int n = json_extract_array(buf, "wavelength", wl_nm, max_n);
    if (n == 0) {
        G_free(wl_nm);
        G_free(buf);
        return 0;
    }

    double *fwhm_nm = fwhm ? G_malloc(sizeof(double) * (size_t)max_n) : NULL;
    int n_fwhm = fwhm ? json_extract_array(buf, "fwhm", fwhm_nm, max_n) : 0;

    for (int i = 0; i < max_n; i++) {
        wl[i] = (i < n) ? (float)(wl_nm[i] * 1e-3) : -1.0f;
        if (fwhm)
            fwhm[i] = (i < n_fwhm) ? (float)(fwhm_nm[i] * 1e-3) : 0.0f;
    }

    G_free(wl_nm);
    if (fwhm_nm) G_free(fwhm_nm);
    G_free(buf);
    return n;
}

/**
 * \brief Parse per-band centre wavelengths and FWHM from a Raster3D map's metadata.
 *
 * Invokes \c r3.info \c -h to obtain the hyperspectral band metadata written
 * by write_band_wl_hist() or compatible tools.  Wavelengths are stored in µm.
 *
 * \param[in]  mapname  Name of the GRASS Raster3D map.
 * \param[out] wl       Array of band centre wavelengths (µm); length \c max_n.
 *                      Entries for unparsed bands are set to -1.
 * \param[out] fwhm     Array of band FWHM values (µm); may be NULL to skip.
 * \param[in]  max_n    Maximum number of bands to parse.
 * \return Number of bands successfully parsed (0 if no metadata found).
 */
static int parse_band_wl(const char *mapname, float *wl, float *fwhm, int max_n)
{
    int n_json = parse_band_wl_hyperjson(mapname, wl, fwhm, max_n);
    if (n_json > 0) return n_json;

    const char *gisbase = getenv("GISBASE");
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "%s/bin/r3.info -h map=%s 2>/dev/null",
             gisbase ? gisbase : "", mapname);

    FILE *fp = popen(cmd, "r");
    if (!fp) return 0;

    for (int i = 0; i < max_n; i++) {
        wl[i] = -1.0f;
        if (fwhm) fwhm[i] = 0.0f;
    }

    char line[512];
    int  n = 0;
    while (fgets(line, sizeof(line), fp)) {
        int    bnum;
        double wl_nm;
        if (sscanf(line, " Band %d: %lf nm", &bnum, &wl_nm) == 2) {
            if (bnum >= 1 && bnum <= max_n) {
                wl[bnum - 1] = (float)(wl_nm * 1e-3);
                if (fwhm) {
                    const char *fp_str = strstr(line, "FWHM:");
                    if (fp_str) {
                        double fwhm_nm;
                        if (sscanf(fp_str, "FWHM: %lf nm", &fwhm_nm) == 1)
                            fwhm[bnum - 1] = (float)(fwhm_nm * 1e-3);
                    }
                }
                n++;
            }
        }
    }
    pclose(fp);
    return n;
}

/**
 * \brief Append per-band wavelength metadata to a Raster3D history file.
 *
 * Writes band centre wavelengths and optional FWHM values (in nm) to the
 * \c hist file of the given Raster3D map so that parse_band_wl() can read
 * them back in subsequent sessions.
 *
 * \param[in]  mapname  Name of the output Raster3D map.
 * \param[in]  wl       Band centre wavelengths (µm), length \c n.
 * \param[in]  fwhm     Band FWHM values (µm), length \c n; may be NULL.
 * \param[in]  n        Number of bands.
 */
static void write_band_wl_hist(const char *mapname,
                                const float *wl, const float *fwhm, int n)
{
    const char *gisdbase = G_gisdbase();
    const char *location = G_location();
    const char *mapset   = G_mapset();
    char histpath[GPATH_MAX];
    snprintf(histpath, sizeof(histpath), "%s/%s/%s/grid3/%s/hist",
             gisdbase, location, mapset, mapname);
    FILE *f = fopen(histpath, "a");
    if (!f) {
        G_warning(_("Cannot append wavelength metadata to history of <%s>"), mapname);
        return;
    }
    fprintf(f, "\nHyperspectral Metadata:\n");
    fprintf(f, "Valid Bands: %d\n", n);
    for (int i = 0; i < n; i++) {
        if (wl[i] > 0.0f) {
            float wl_nm = wl[i] * 1000.0f;
            if (fwhm && fwhm[i] > 0.0f)
                fprintf(f, "Band %d: %g nm, FWHM: %g nm\n", i + 1, wl_nm, fwhm[i] * 1000.0f);
            else
                fprintf(f, "Band %d: %g nm\n", i + 1, wl_nm);
        }
    }
    fclose(f);
}

/**
 * \brief 1-D linear interpolation of a LUT array to a target wavelength.
 *
 * Clamps to boundary values when \c wl_um is outside the LUT range.
 *
 * \param[in]  arr    Source array (length \c n), sampled at \c lut_wl.
 * \param[in]  lut_wl LUT wavelength axis (µm), strictly increasing, length \c n.
 * \param[in]  n      Number of LUT points.
 * \param[in]  wl_um  Target wavelength (µm).
 * \return Linearly interpolated value.
 */
static float interp_wl(const float *arr, const float *lut_wl, int n, float wl_um)
{
    if (n <= 0)                  return 0.0f;
    if (wl_um <= lut_wl[0])     return arr[0];
    if (wl_um >= lut_wl[n - 1]) return arr[n - 1];
    int i = 0;
    while (i < n - 2 && lut_wl[i + 1] <= wl_um) i++;
    float t = (wl_um - lut_wl[i]) / (lut_wl[i + 1] - lut_wl[i]);
    return arr[i] * (1.0f - t) + arr[i + 1] * t;
}

/**
 * \brief Load a 2-D GRASS raster map into a heap-allocated float array.
 *
 * Null cells in the raster are converted to NaN and subsequently replaced by
 * \c fill_value.  If the map cannot be found a warning is issued and the
 * entire array is filled with \c fill_value.
 *
 * \param[in]  mapname     GRASS raster map name.
 * \param[in]  nrows       Number of rows in the current region.
 * \param[in]  ncols       Number of columns in the current region.
 * \param[in]  fill_value  Value to use for null/missing pixels.
 * \return G_malloc()'d float array of size \c nrows × \c ncols.
 *         The caller is responsible for calling G_free().
 */
static float *load_raster2d(const char *mapname, int nrows, int ncols,
                             float fill_value)
{
    float *data = G_malloc((size_t)nrows * ncols * sizeof(float));

    char *mname = G_store(mapname);   /* non-const copy for G_find_raster */
    const char *mapset = G_find_raster(mname, "");
    G_free(mname);
    if (!mapset) {
        G_warning(_("2-D raster <%s> not found; using fill value %.4f"),
                  mapname, fill_value);
        for (int i = 0; i < nrows * ncols; i++) data[i] = fill_value;
        return data;
    }

    int fd = Rast_open_old(mapname, mapset);
    DCELL *row_buf = Rast_allocate_d_buf();

    for (int r = 0; r < nrows; r++) {
        Rast_get_d_row(fd, row_buf, r);
        for (int c = 0; c < ncols; c++) {
            if (Rast_is_d_null_value(&row_buf[c]))
                data[r * ncols + c] = NAN;
            else
                data[r * ncols + c] = (float)row_buf[c];
        }
    }

    Rast_close(fd);
    G_free(row_buf);

    /* Fill NaN with fill_value */
    int n_nan = 0;
    for (int i = 0; i < nrows * ncols; i++) {
        if (isnan(data[i])) { data[i] = fill_value; n_nan++; }
    }
    if (n_nan > 0)
        G_verbose_message(_("Filled %d NaN pixels in <%s> with %.4f"),
                          n_nan, mapname, fill_value);

    return data;
}

/**
 * \brief Write a float array to a new 2-D GRASS FCELL raster map.
 *
 * Non-finite values (NaN, ±Inf) are written as GRASS null cells.
 *
 * \param[in]  mapname  Name of the output raster map to create.
 * \param[in]  data     Source float array, row-major, size \c nrows × \c ncols.
 * \param[in]  nrows    Number of rows.
 * \param[in]  ncols    Number of columns.
 */
static void write_raster2d(const char *mapname, const float *data,
                             int nrows, int ncols)
{
    int fd = Rast_open_new(mapname, FCELL_TYPE);
    FCELL *row_buf = Rast_allocate_f_buf();
    for (int r = 0; r < nrows; r++) {
        for (int c = 0; c < ncols; c++) {
            float v = data[r * ncols + c];
            if (isfinite(v))
                row_buf[c] = (FCELL)v;
            else
                Rast_set_f_null_value(&row_buf[c], 1);
        }
        Rast_put_f_row(fd, row_buf);
    }
    G_free(row_buf);
    Rast_close(fd);
}

/**
 * \brief Write a 2-D float band into a depth slice of an open Raster3D map.
 *
 * Non-finite values are replaced by \c null_d.
 *
 * \param[in,out] outmap   Open GRASS Raster3D map (must be writable).
 * \param[in]     band     Source float array, row-major, size \c nrows × \c ncols.
 * \param[in]     nrows    Number of rows.
 * \param[in]     ncols    Number of columns.
 * \param[in]     z        Depth index to write into (band index, 0-based).
 * \param[in]     null_d   Replacement value for non-finite pixels.
 */
static void write_band_to_rast3d(RASTER3D_Map *outmap,
                                  const float *band, int nrows, int ncols, int z,
                                  double null_d)
{
    for (int row = 0; row < nrows; row++) {
        for (int col = 0; col < ncols; col++) {
            float v = band[row * ncols + col];
            Rast3d_put_double(outmap, col, row, z,
                              isfinite(v) ? (double)v : null_d);
        }
    }
}

/**
 * \brief Find the band index whose centre wavelength is closest to \c target.
 *
 * \param[in]  wl      Array of band centre wavelengths (µm), length \c n.
 * \param[in]  n       Number of bands.
 * \param[in]  target  Target wavelength (µm).
 * \return Zero-based index of the closest band.
 */
static int find_closest_band(const float *wl, int n, float target)
{
    int   best = 0;
    float bd   = fabsf(wl[0] - target);
    for (int i = 1; i < n; i++) {
        float d = fabsf(wl[i] - target);
        if (d < bd) { bd = d; best = i; }
    }
    return best;
}

/**
 * \brief Extract one Z slice from a Raster3D map into a float buffer via
 *        bulk tile reads.
 *
 * Uses Rast3d_get_block(), which takes the fast tile-bulk path
 * (Rast3d_get_block_nocache) only when the map was opened with
 * RASTER3D_NO_CACHE (map->useCache == 0).  The caller is responsible for
 * opening the map with RASTER3D_NO_CACHE and supplying a scratch buffer
 * \c dcell_tmp of size \c nrows × \c ncols to avoid per-band allocation.
 *
 * Rast3d_get_block block layout for nz=1: buf[row * ncols + col].
 * Null voxels and non-positive values are stored as NaN in \c out.
 *
 * \param[in]  map        Open Raster3D map (must use RASTER3D_NO_CACHE).
 * \param[in]  z          Depth (band) index to extract (0-based).
 * \param[in]  nrows      Number of rows.
 * \param[in]  ncols      Number of columns.
 * \param[in]  dcell_tmp  Caller-allocated DCELL[nrows*ncols] scratch buffer.
 * \param[out] out        Caller-allocated float[nrows*ncols] output buffer.
 */
static void extract_z_slice(RASTER3D_Map *map, int z, int nrows, int ncols,
                              DCELL *dcell_tmp, float *out)
{
    Rast3d_get_block(map, 0, 0, z, ncols, nrows, 1, dcell_tmp, DCELL_TYPE);
    int npix = nrows * ncols;
    for (int i = 0; i < npix; i++) {
        DCELL v = dcell_tmp[i];
        out[i] = (Rast_is_d_null_value(&v) || v <= 0.0) ? NAN : (float)v;
    }
}

/**
 * \brief Load multiple depth slices from an open Raster3D map.
 *
 * Reads \c nb depth slices at the specified depth indices into pre-allocated
 * output buffers.  Invalid or null voxel values, and non-positive values, are
 * stored as NaN.
 *
 * The map must have been opened with RASTER3D_NO_CACHE so that
 * extract_z_slice() uses the fast tile-bulk read path.
 *
 * \param[in]  map     Open GRASS Raster3D map (RASTER3D_NO_CACHE); may be NULL.
 * \param[in]  depths  Array of depth (band) indices to load, length \c nb.
 * \param[in]  nb      Number of bands to load.
 * \param[in]  nrows   Number of rows per slice.
 * \param[in]  ncols   Number of columns per slice.
 * \param[out] bufs    Array of \c nb pre-allocated float[nrows×ncols] buffers.
 */
static void load_bands_from_cube(RASTER3D_Map *map,
                                  const int *depths, int nb,
                                  int nrows, int ncols,
                                  float **bufs)
{
    int npix = nrows * ncols;
    for (int b = 0; b < nb; b++)
        for (int i = 0; i < npix; i++)
            bufs[b][i] = NAN;
    if (!map) return;

    DCELL *dcell_tmp = G_malloc((size_t)npix * sizeof(DCELL));
    for (int b = 0; b < nb; b++)
        extract_z_slice(map, depths[b], nrows, ncols, dcell_tmp, bufs[b]);
    G_free(dcell_tmp);
}

/** \endcond */

/**
 * \brief Apply the full 6SV2.1 atmospheric correction pipeline to a Raster3D cube.
 *
 * Reads the input hyperspectral radiance cube, converts each band from TOA
 * radiance to bottom-of-atmosphere reflectance using the precomputed LUT, and
 * writes the result to a new Raster3D map.  Optionally applies all ISOFIT-
 * inspired extensions controlled by the \c iso parameter structure:
 *
 * - **#1** Per-pixel AOD/H₂O maps with optional Gaussian spatial smoothing.
 * - **#2** Vermote 1999 adjacency effect correction (Lambertian environment model).
 * - **#3/#5** Surface prior MAP regularisation via surface_model_regularize().
 * - **#4/#6** Per-band NEdL-based reflectance uncertainty output.
 *
 * Band centre wavelengths are read from the map's \c r3.info metadata; if
 * absent the LUT wavelength grid is used as fallback.  Sub-25 nm FWHM sensors
 * trigger an automatic reptran fine SRF gas-absorption correction.
 *
 * Physics applied per pixel per band:
 * \f[
 *   \rho_\text{toa} = \frac{\pi L d^2}{E_0 \cos\theta_s}
 * \f]
 * \f[
 *   \rho_\text{boa} = \frac{\rho_\text{toa} - R_\text{atm}}{T_\downarrow T_\uparrow
 *                     (1 + s \rho_\text{boa})}
 * \f]
 *
 * \param[in]  input_name   Name of the input GRASS Raster3D radiance map.
 * \param[in]  output_name  Name of the output GRASS Raster3D reflectance map.
 * \param[in]  cfg          LUT configuration (grid axes and dimensions).
 * \param[in]  lut          Precomputed LUT arrays (may be modified in place by
 *                          SRF correction).
 * \param[in]  aod_val      Scene-average AOD at 550 nm (used when no per-pixel
 *                          AOD map is provided).
 * \param[in]  h2o_val      Scene-average column water vapour (g cm⁻²).
 * \param[in]  doy          Day of year for Earth-Sun distance and E₀ computation.
 * \param[in]  sza_deg      Solar zenith angle (degrees).
 * \param[in]  iso          ISOFIT improvement parameters; may be NULL to disable
 *                          all extensions.
 */
static void correct_raster3d(const char *input_name, const char *output_name,
                              const LutConfig *cfg, LutArrays *lut,
                              float aod_val, float h2o_val,
                              int doy, float sza_deg,
                              const IsoFitParams *iso)
{
    /* ── Open input map ── */
    const char *in_mapset = G_find_raster3d(input_name, "");
    if (!in_mapset)
        G_fatal_error(_("3D raster map <%s> not found"), input_name);

    RASTER3D_Region region;
    Rast3d_get_window(&region);

    RASTER3D_Map *inmap = Rast3d_open_cell_old(
        input_name, in_mapset, &region,
        RASTER3D_TILE_SAME_AS_FILE, RASTER3D_NO_CACHE);
    if (!inmap)
        G_fatal_error(_("Cannot open 3D raster <%s>"), input_name);

    Rast3d_get_region_struct_map(inmap, &region);
    int nrows   = region.rows;
    int ncols   = region.cols;
    int ndepths = region.depths;
    int npix    = nrows * ncols;

    /* Scratch buffer for extract_z_slice(); allocated once, reused per band. */
    DCELL *dcell_slice = G_malloc((size_t)npix * sizeof(DCELL));

    G_verbose_message(_("Input <%s>: %d rows × %d cols × %d bands"),
                      input_name, nrows, ncols, ndepths);

    /* ── Parse per-band wavelengths ── */
    float *band_wl   = G_malloc(ndepths * sizeof(float));
    float *band_fwhm = G_malloc(ndepths * sizeof(float));
    int    n_parsed  = parse_band_wl(input_name, band_wl, band_fwhm, ndepths);

    if (n_parsed == 0) {
        G_warning(_("No wavelength metadata in <%s>; using LUT grid"), input_name);
        for (int b = 0; b < ndepths; b++)
            band_wl[b] = (b < cfg->n_wl) ? cfg->wl[b] : cfg->wl[cfg->n_wl - 1];
    } else if (n_parsed < ndepths) {
        G_warning(_("Parsed %d of %d band wavelengths"), n_parsed, ndepths);
    } else {
        G_verbose_message(_("Band wavelengths: %.4f–%.4f µm"),
                          band_wl[0], band_wl[ndepths - 1]);
    }

    /* ── SRF correction for sub-nm sensors ── */
    {
        float min_fwhm_nm = 1e9f;
        int   n_fwhm = 0;
        for (int b = 0; b < ndepths; b++) {
            if (band_fwhm[b] > 0.0f) {
                n_fwhm++;
                float fn = band_fwhm[b] * 1000.0f;
                if (fn < min_fwhm_nm) min_fwhm_nm = fn;
            }
        }
        if (n_fwhm > 0 && min_fwhm_nm < 25.0f) {
            G_message(_("Sensor FWHM=%.2f nm: "
                        "applying reptran fine SRF gas correction..."),
                      min_fwhm_nm);
            SrfConfig srf_cfg = { .fwhm_um = band_fwhm, .threshold_um = 0.025f };
            SrfCorrection *srf = atcorr_srf_compute(&srf_cfg, cfg);
            if (srf) {
                atcorr_srf_apply(srf, cfg, lut);
                atcorr_srf_free(srf);
                G_verbose_message(_("SRF gas correction applied."));
            } else {
                G_warning(_("SRF correction failed; proceeding without it"));
            }
        }
    }

    /* Warn on bands outside LUT range */
    {
        int n_out = 0;
        for (int b = 0; b < ndepths; b++)
            if (band_wl[b] < cfg->wl[0] || band_wl[b] > cfg->wl[cfg->n_wl-1])
                n_out++;
        if (n_out > 0)
            G_warning(_("%d bands outside LUT range [%.4f, %.4f] µm"),
                      n_out, cfg->wl[0], cfg->wl[cfg->n_wl-1]);
    }

    /* ── #1: Load and optionally smooth per-pixel AOD/H2O maps ── *
     * Pre-loaded retrieval arrays (iso->aod_data / iso->h2o_data) take
     * priority over raster map names (iso->aod_map / iso->h2o_map).
     * free_aod_map / free_h2o_map track ownership for cleanup. */
    float *aod_map_data = NULL;
    float *h2o_map_data = NULL;
    int    have_aod_map = 0;
    int    have_h2o_map = 0;
    int    free_aod_map = 0;
    int    free_h2o_map = 0;

    if (iso && iso->aod_data) {
        aod_map_data = iso->aod_data;
        have_aod_map = 1;
        G_verbose_message(_("Using pre-retrieved per-pixel AOD"));
    } else if (iso && iso->aod_map && iso->aod_map[0]) {
        G_message(_("Loading per-pixel AOD map <%s>..."), iso->aod_map);
        aod_map_data = load_raster2d(iso->aod_map, nrows, ncols, aod_val);
        /* Clamp to valid AOD range */
        for (int i = 0; i < npix; i++) {
            if (aod_map_data[i] < 0.001f) aod_map_data[i] = 0.001f;
            if (aod_map_data[i] > 5.0f)   aod_map_data[i] = 5.0f;
        }
        if (iso->smooth_sigma > 0.0f) {
            G_message(_("  Gaussian smoothing AOD map (σ=%.1f px)..."),
                      iso->smooth_sigma);
            spatial_gaussian_filter(aod_map_data, nrows, ncols, iso->smooth_sigma);
        }
        have_aod_map = 1;
        free_aod_map = 1;
    }

    if (iso && iso->h2o_data) {
        h2o_map_data = iso->h2o_data;
        have_h2o_map = 1;
        G_verbose_message(_("Using pre-retrieved per-pixel H2O"));
    } else if (iso && iso->h2o_map && iso->h2o_map[0]) {
        G_message(_("Loading per-pixel H2O map <%s>..."), iso->h2o_map);
        h2o_map_data = load_raster2d(iso->h2o_map, nrows, ncols, h2o_val);
        for (int i = 0; i < npix; i++) {
            if (h2o_map_data[i] < 0.01f) h2o_map_data[i] = 0.01f;
            if (h2o_map_data[i] > 8.0f)  h2o_map_data[i] = 8.0f;
        }
        if (iso->smooth_sigma > 0.0f) {
            G_message(_("  Gaussian smoothing H2O map (σ=%.1f px)..."),
                      iso->smooth_sigma);
            spatial_gaussian_filter(h2o_map_data, nrows, ncols, iso->smooth_sigma);
        }
        have_h2o_map = 1;
        free_h2o_map = 1;
    }

    /* ── Per-pixel surface pressure (O₂-A derived) ── */
    int     have_pressure_map = (iso && iso->pressure_data);
    float  *pressure_data     = have_pressure_map ? iso->pressure_data : NULL;
    float   P_lut             = (cfg->surface_pressure > 0.0f)
                                    ? cfg->surface_pressure : 1013.25f;

    /* ── Quality bitmask (pre-correction; passed through from main) ── */
    uint8_t *quality_data = (iso && iso->quality_data) ? iso->quality_data : NULL;
    (void)quality_data;   /* available for future per-pixel masking */

    int use_per_pixel = have_aod_map || have_h2o_map || have_pressure_map;

    /* ── Load terrain rasters ── */
    float *slope_data  = NULL;
    float *aspect_data = NULL;
    float *vza_data    = NULL;
    float *vaa_data    = NULL;
    int    have_terrain = (iso && iso->slope_map && iso->aspect_map
                           && lut->T_down_dir != NULL);
    if (have_terrain) {
        G_message(_("Loading terrain rasters for illumination correction..."));
        slope_data  = load_raster2d(iso->slope_map,  nrows, ncols, 0.0f);
        aspect_data = load_raster2d(iso->aspect_map, nrows, ncols, 0.0f);
        if (iso->vza_map && iso->vza_map[0])
            vza_data = load_raster2d(iso->vza_map, nrows, ncols, cfg->vza);
        if (iso->vaa_map && iso->vaa_map[0])
            vaa_data = load_raster2d(iso->vaa_map, nrows, ncols, iso->sun_azimuth);
    }

    /* ── Load NBAR kernel-weight rasters ── */
    float *fiso_data = NULL;
    float *fvol_data = NULL;
    float *fgeo_data = NULL;
    int    have_nbar = (iso && iso->brdf_fiso_map && iso->brdf_fvol_map
                        && iso->brdf_fgeo_map);
    if (have_nbar) {
        G_message(_("Loading BRDF kernel rasters for NBAR normalization..."));
        fiso_data = load_raster2d(iso->brdf_fiso_map, nrows, ncols, 1.0f);
        fvol_data = load_raster2d(iso->brdf_fvol_map, nrows, ncols, 0.0f);
        fgeo_data = load_raster2d(iso->brdf_fgeo_map, nrows, ncols, 0.0f);
    }

    /* ── FlexBRDF: spectral kernel weight scales (band-indexed during loop) ── */
    int have_flex = (iso && iso->have_flex_brdf
                     && iso->flex_fiso_wl && iso->flex_fvol_wl && iso->flex_fgeo_wl);

    /* ── DASF accumulators (band-major: [n_dasf_max × npix]) ── *
     * We accumulate on-the-fly per pixel to avoid a large temporary buffer.
     * Two float[npix] arrays hold the per-pixel sums; DASF bands are those
     * within [0.710, 0.790] µm. Red (660 nm) and NIR (870 nm) bands are saved
     * for NDVI masking of non-vegetation pixels. */
    int     do_dasf       = (iso && iso->do_dasf && iso->dasf_output);
    float  *dasf_sum_xy   = NULL;
    float  *dasf_sum_yy   = NULL;
    float  *dasf_red_band = NULL;   /* refl at ~660 nm for NDVI */
    float  *dasf_nir_band = NULL;   /* refl at ~870 nm for NDVI */
    int     n_dasf_bands  = 0;      /* count of DASF bands accumulated so far */
    int     dasf_red_z    = -1;     /* band index of closest band to 660 nm */
    int     dasf_nir_z    = -1;     /* band index of closest band to 870 nm */

    if (do_dasf) {
        dasf_sum_xy   = G_calloc((size_t)npix, sizeof(float));
        dasf_sum_yy   = G_calloc((size_t)npix, sizeof(float));
        dasf_red_band = G_malloc((size_t)npix * sizeof(float));
        dasf_nir_band = G_malloc((size_t)npix * sizeof(float));
        for (int i = 0; i < npix; i++) {
            dasf_red_band[i] = NAN;
            dasf_nir_band[i] = NAN;
        }
        /* Find red / NIR band indices for NDVI masking */
        dasf_red_z = find_closest_band(band_wl, ndepths, 0.660f);
        dasf_nir_z = find_closest_band(band_wl, ndepths, 0.870f);
    }

    /* ── Pre-compute scalar LUT slice (used when no per-pixel maps) ── */
    int    n_wl = cfg->n_wl;
    float *Rs   = G_malloc(n_wl * sizeof(float));
    float *Tds  = G_malloc(n_wl * sizeof(float));
    float *Tus  = G_malloc(n_wl * sizeof(float));
    float *ss   = G_malloc(n_wl * sizeof(float));
    float *Tdds = have_terrain ? G_malloc(n_wl * sizeof(float)) : NULL;
    atcorr_lut_slice(cfg, lut, aod_val, h2o_val, Rs, Tds, Tus, ss, Tdds);

    G_verbose_message(
        _("Correction slice at AOD=%.3f, H2O=%.2f g/cm²: "
          "R_atm(550nm)=%.4f  T_down=%.4f  T_up=%.4f  s=%.4f"),
        aod_val, h2o_val,
        interp_wl(Rs,  cfg->wl, n_wl, 0.55f),
        interp_wl(Tds, cfg->wl, n_wl, 0.55f),
        interp_wl(Tus, cfg->wl, n_wl, 0.55f),
        interp_wl(ss,  cfg->wl, n_wl, 0.55f));

    /* ── Physical constants ── */
    double d2      = sixs_earth_sun_dist2(doy);
    float  d2f     = (float)d2;
    double cos_sza = cos(sza_deg * (M_PI / 180.0));
    float  cos_szaf = (float)cos_sza;

    /* ── #2: Auto-detect pixel size for adjacency correction ── */
    float pixel_size_m = iso ? iso->pixel_size_m : 0.0f;
    if (iso && iso->adj_psf_km > 0.0f && pixel_size_m <= 0.0f) {
        struct Cell_head win;
        G_get_window(&win);
        pixel_size_m = (float)((win.ew_res + win.ns_res) / 2.0);
        G_verbose_message(_("Auto-detected pixel size: %.1f m"), pixel_size_m);
    }

    /* ── Open output map ── */
    RASTER3D_Map *outmap = Rast3d_open_new_opt_tile_size(
        output_name, RASTER3D_USE_CACHE_X, &region, DCELL_TYPE, 32);
    if (!outmap)
        G_fatal_error(_("Cannot create 3D raster <%s>"), output_name);
    Rast3d_min_unlocked(outmap, RASTER3D_USE_CACHE_X);

    /* ── Open uncertainty output map if requested ── */
    RASTER3D_Map *uncmap = NULL;
    if (iso && iso->do_uncertainty && iso->unc_output && iso->unc_output[0]) {
        uncmap = Rast3d_open_new_opt_tile_size(
            iso->unc_output, RASTER3D_USE_CACHE_X, &region, DCELL_TYPE, 32);
        if (!uncmap)
            G_fatal_error(_("Cannot create uncertainty map <%s>"),
                          iso->unc_output);
        Rast3d_min_unlocked(uncmap, RASTER3D_USE_CACHE_X);
    }

    double null_d;
    Rast_set_d_null_value(&null_d, 1);

    /* ── Allocate working buffers ── */
    /* Per-band buffers (reused each iteration) */
    float *rad_band  = G_malloc((size_t)npix * sizeof(float));
    float *refl_band = G_malloc((size_t)npix * sizeof(float));
    float *sigma_band = (iso && iso->do_uncertainty)
                        ? G_malloc((size_t)npix * sizeof(float)) : NULL;

    /* Full cube needed for MAP regularisation (#3/#5) */
    float *refl_cube  = NULL;
    float *sigma_cube = NULL;

    if (iso && iso->do_surface_prior) {
        refl_cube = G_malloc((size_t)ndepths * npix * sizeof(float));
        if (iso->do_uncertainty)
            sigma_cube = G_malloc((size_t)ndepths * npix * sizeof(float));
        /* Initialise to NaN so unprocessed bands stay NaN */
        for (size_t i = 0; i < (size_t)ndepths * npix; i++) refl_cube[i] = NAN;
        if (sigma_cube)
            for (size_t i = 0; i < (size_t)ndepths * npix; i++) sigma_cube[i] = NAN;
    }

    /* ── #3/#5: Initialise surface model ── */
    SurfaceModelImpl *surf_mdl = NULL;
    float *sigma_model = NULL;   /* per-band model discrepancy */

    if (iso && iso->do_surface_prior) {
        float *wl_bands = G_malloc(ndepths * sizeof(float));
        for (int b = 0; b < ndepths; b++) wl_bands[b] = band_wl[b];
        surf_mdl = surface_model_alloc(wl_bands, ndepths);
        sigma_model = G_malloc(ndepths * sizeof(float));
        if (surf_mdl && sigma_model)
            surface_model_discrepancy(wl_bands, ndepths, sigma_model);
        G_free(wl_bands);
    }

    /* ── BRDF white-sky albedo for the s_alb coupling ── */
    /* Computed once per scene: BrdfParams are spectrally uniform scalars. */
    float rho_albe_brdf = 0.0f;
    if (cfg->brdf_type != BRDF_LAMBERTIAN)
        rho_albe_brdf = sixs_brdf_albe(cfg->brdf_type, &cfg->brdf_params,
                                        cos_szaf, 48, 24);
    const int use_brdf = (cfg->brdf_type != BRDF_LAMBERTIAN);

    /* ── Correction loop: band by band ── */
    G_message(_("Correcting %d bands × %d rows × %d cols..."),
              ndepths, nrows, ncols);

    for (int z = 0; z < ndepths; z++) {
        G_percent(z, ndepths, 2);

        float wl  = band_wl[z];
        float E0  = sixs_E0(wl);

        /* Scalar LUT values for this wavelength (fallback / adjacency) */
        float R_a_s = interp_wl(Rs,  cfg->wl, n_wl, wl);
        float T_d_s = interp_wl(Tds, cfg->wl, n_wl, wl);
        float T_u_s = interp_wl(Tus, cfg->wl, n_wl, wl);
        float s_a_s = interp_wl(ss,  cfg->wl, n_wl, wl);

        /* ── Load radiance band ── */
        extract_z_slice(inmap, z, nrows, ncols, dcell_slice, rad_band);

        /* ── FlexBRDF: spectral scale factors at this wavelength ── *
         * wl_scale_* = f_iso/vol/geo at band z relative to the NIR (858 nm) reference.
         * When have_flex=0: all scales=1 → identical to non-FlexBRDF path.
         * When have_flex=1 but have_nbar=0: fiso_wl[z] applied directly as scene mean. */
        float wl_scale_iso = 1.0f, wl_scale_vol = 1.0f, wl_scale_geo = 1.0f;
        if (have_flex) {
            wl_scale_iso = (iso->flex_fiso_ref > 1e-6f)
                           ? iso->flex_fiso_wl[z] / iso->flex_fiso_ref : 1.0f;
            wl_scale_vol = (fabsf(iso->flex_fvol_ref) > 1e-6f)
                           ? iso->flex_fvol_wl[z] / iso->flex_fvol_ref : 1.0f;
            wl_scale_geo = (fabsf(iso->flex_fgeo_ref) > 1e-6f)
                           ? iso->flex_fgeo_wl[z] / iso->flex_fgeo_ref : 1.0f;
        }

        /* ── Per-pixel inversion ── */

        /* Scalar direct T_d for this band (terrain); cos(vza_ref) for T_up scaling */
        float T_d_dir_s   = Tdds ? interp_wl(Tdds, cfg->wl, n_wl, wl) : T_d_s;
        float cos_vza_ref = cosf(cfg->vza * (float)(M_PI / 180.0));

        if (use_per_pixel || have_terrain || have_nbar || have_flex) {
            /* Per-pixel path: AOD/H2O LUT interp + terrain + NBAR */
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
            for (int i = 0; i < npix; i++) {
                float L = rad_band[i];
                if (!isfinite(L) || E0 <= 0.0f) { refl_band[i] = NAN; continue; }

                float R_a, T_d, T_u, s_a;
                if (use_per_pixel) {
                    float a_px = have_aod_map ? aod_map_data[i] : aod_val;
                    float h_px = have_h2o_map ? h2o_map_data[i] : h2o_val;
                    atcorr_lut_interp_pixel(cfg, lut, a_px, h_px, wl,
                                             &R_a, &T_d, &T_u, &s_a);
                } else {
                    R_a = R_a_s; T_d = T_d_s; T_u = T_u_s; s_a = s_a_s;
                }

                /* Terrain illumination correction */
                if (have_terrain) {
                    float slope_px  = isfinite(slope_data[i])  ? slope_data[i]  : 0.0f;
                    float aspect_px = isfinite(aspect_data[i]) ? aspect_data[i] : 0.0f;
                    float vza_px    = vza_data
                        ? (isfinite(vza_data[i]) ? vza_data[i] : cfg->vza)
                        : cfg->vza;
                    float cos_i = cos_incidence(cfg->sza, iso->sun_azimuth,
                                                slope_px, aspect_px);
                    float V_d   = skyview_factor(slope_px);
                    T_d = atcorr_terrain_T_down(T_d, T_d_dir_s, cos_szaf, cos_i, V_d);
                    T_u = atcorr_terrain_T_up(T_u, cos_vza_ref, vza_px);
                }

                /* Per-pixel surface pressure correction (O₂-A derived).
                 * Rayleigh OD ∝ P; correct R_atm and transmittances for the
                 * pressure difference between the pixel and the LUT reference.
                 *   τ_R(λ,P) = 0.00877 × λ^(−4.05) × P/P_ref  (Hansen & Travis 1974)
                 *   ΔP_frac  = (P_pixel − P_lut) / P_lut
                 *   R_atm   *= P_pixel / P_lut          (Rayleigh ∝ P)
                 *   T_down  *= exp(−τ_R(λ,P_lut) × ΔP_frac / cos_sza)
                 *   T_up    *= exp(−τ_R(λ,P_lut) × ΔP_frac / cos_vza) */
                if (have_pressure_map && isfinite(pressure_data[i])) {
                    float P_px     = pressure_data[i];
                    float dP_frac  = (P_px - P_lut) / P_lut;
                    if (fabsf(dP_frac) > 0.001f) {
                        float tau_R    = 0.00877f * powf(wl, -4.05f);
                        float cos_vza_px = cos_vza_ref;
                        if (vza_data && isfinite(vza_data[i]))
                            cos_vza_px = cosf(vza_data[i] * (float)(M_PI/180.0));
                        if (cos_vza_px < 0.05f) cos_vza_px = 0.05f;
                        R_a *= (P_px / P_lut);
                        T_d *= expf(-tau_R * dP_frac / cos_szaf);
                        T_u *= expf(-tau_R * dP_frac / cos_vza_px);
                    }
                }

                float rho_toa = (float)(M_PI * L * d2) / (E0 * cos_szaf);
                float rho_boa = use_brdf
                    ? atcorr_invert_brdf(rho_toa, R_a, T_d, T_u, s_a, rho_albe_brdf)
                    : atcorr_invert(rho_toa, R_a, T_d, T_u, s_a);

                /* NBAR normalization (Ross-Li MCD43 kernels)
                 * FlexBRDF: per-pixel amplitude × spectral shape from MCD43 disaggregation.
                 * wl_scale_* carries the spectral variation relative to the 858 nm reference;
                 * fiso_data / fvol_data / fgeo_data carry the per-pixel spatial amplitude.
                 * When have_flex=0: wl_scale_*=1.0 → identical to original NBAR. */
                if ((have_nbar || have_flex) && isfinite(rho_boa)) {
                    float f_iso = (have_nbar && fiso_data && isfinite(fiso_data[i]))
                                  ? fiso_data[i] : (have_flex ? iso->flex_fiso_ref : 1.0f);
                    float f_vol = (have_nbar && fvol_data && isfinite(fvol_data[i]))
                                  ? fvol_data[i] : (have_flex ? iso->flex_fvol_ref : 0.0f);
                    float f_geo = (have_nbar && fgeo_data && isfinite(fgeo_data[i]))
                                  ? fgeo_data[i] : (have_flex ? iso->flex_fgeo_ref : 0.0f);
                    /* Apply spectral shape from MCD43 disaggregation */
                    f_iso *= wl_scale_iso;
                    f_vol *= wl_scale_vol;
                    f_geo *= wl_scale_geo;
                    float vza_obs = vza_data
                        ? (isfinite(vza_data[i]) ? vza_data[i] : cfg->vza)
                        : cfg->vza;
                    float vaa_obs = vaa_data
                        ? (isfinite(vaa_data[i]) ? vaa_data[i] : iso->sun_azimuth)
                        : iso->sun_azimuth;
                    float raa_obs = iso->sun_azimuth - vaa_obs;
                    rho_boa = atcorr_brdf_normalize(rho_boa, f_iso, f_vol, f_geo,
                                                     cfg->sza, vza_obs, raa_obs,
                                                     cfg->sza);
                }

                refl_band[i] = rho_boa;
            }
        } else {
            /* Scalar correction (original path) */
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
            for (int i = 0; i < npix; i++) {
                float L = rad_band[i];
                if (!isfinite(L) || E0 <= 0.0f) { refl_band[i] = NAN; continue; }
                float rho_toa = (float)(M_PI * L * d2) / (E0 * cos_szaf);
                refl_band[i]  = use_brdf
                    ? atcorr_invert_brdf(rho_toa, R_a_s, T_d_s, T_u_s, s_a_s, rho_albe_brdf)
                    : atcorr_invert(rho_toa, R_a_s, T_d_s, T_u_s, s_a_s);
            }
        }

        /* Clip valid values; NaN stays NaN */
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
        for (int i = 0; i < npix; i++) {
            float r = refl_band[i];
            if (isfinite(r))
                refl_band[i] = (r < -0.01f) ? -0.01f
                             : (r >  1.5f)  ?  1.5f : r;
        }

        /* Gas absorption mask: T_round_trip < 0.10 → correction ill-conditioned.
         * 0.10 catches the 940nm H2O core (T≈0.06) and 2040nm CO2 (T≈0.07)
         * in addition to deep 1430nm / 1900nm bands (T≈0.001). */
        if (T_d_s * T_u_s < 0.10f) {
            for (int i = 0; i < npix; i++) refl_band[i] = NAN;
        }

        /* ── DASF accumulation + red/NIR band saving ── */
        if (do_dasf) {
            /* Save red (~660 nm) and NIR (~870 nm) bands for NDVI masking */
            if (z == dasf_red_z)
                memcpy(dasf_red_band, refl_band, (size_t)npix * sizeof(float));
            if (z == dasf_nir_z)
                memcpy(dasf_nir_band, refl_band, (size_t)npix * sizeof(float));

            /* Accumulate DASF sums if this band is within the NIR plateau */
            if (wl >= 0.710f && wl <= 0.790f) {
                float omega = leaf_albedo_nir(wl);
                if (omega > 0.0f) {
                    for (int i = 0; i < npix; i++) {
                        if (isfinite(refl_band[i])) {
                            dasf_sum_xy[i] += refl_band[i] * omega;
                            dasf_sum_yy[i] += omega * omega;
                        }
                    }
                    n_dasf_bands++;
                }
            }
        }

        /* ── #2: In-loop adjacency correction ── */
        if (iso && iso->adj_psf_km > 0.0f && pixel_size_m > 0.0f) {
            /* Use scene-average AOD for T_dir (good approximation) */
            float aod_mean = aod_val;
            if (have_aod_map) {
                double s = 0.0; int n = 0;
                for (int i = 0; i < npix; i++)
                    if (isfinite(aod_map_data[i])) { s += aod_map_data[i]; n++; }
                if (n > 0) aod_mean = (float)(s / n);
            }
            /* T_scat: use scalar slice (adequate for diffuse fraction) */
            float T_scat = T_d_s * T_u_s;
            adjacency_correct_band(refl_band, nrows, ncols,
                                   iso->adj_psf_km, pixel_size_m,
                                   T_scat, s_a_s,
                                   wl, aod_mean,
                                   cfg->surface_pressure > 0.0f
                                       ? cfg->surface_pressure : 1013.25f,
                                   sza_deg, cfg->vza);
        }

        /* ── #4: Per-band uncertainty ── */
        if (iso && iso->do_uncertainty && sigma_band) {
            uncertainty_compute_band(
                rad_band, refl_band, npix,
                E0, d2f, cos_szaf,
                T_d_s, T_u_s, s_a_s, R_a_s,
                0.0f,  /* nedl = 0 → estimate from rad_band */
                0.04f, /* aod_sigma */
                cfg, lut, wl, aod_val, h2o_val,
                sigma_band);
        }

        /* ── Store or write results ── */
        if (refl_cube) {
            /* Deferred write: accumulate for MAP regularisation */
            memcpy(refl_cube  + (size_t)z * npix, refl_band,
                   (size_t)npix * sizeof(float));
            if (sigma_cube && sigma_band)
                memcpy(sigma_cube + (size_t)z * npix, sigma_band,
                       (size_t)npix * sizeof(float));
        } else {
            /* Immediate write */
            write_band_to_rast3d(outmap, refl_band, nrows, ncols, z, null_d);
            if (uncmap && sigma_band)
                write_band_to_rast3d(uncmap, sigma_band, nrows, ncols, z, null_d);
        }
    }
    G_percent(1, 1, 1);

    /* ── DASF finalization and 2-D raster output ── */
    if (do_dasf) {
        G_message(_("Computing DASF from %d NIR plateau bands (710–790 nm)..."),
                  n_dasf_bands);

        float *dasf_out = G_malloc((size_t)npix * sizeof(float));
        for (int i = 0; i < npix; i++) {
            if (dasf_sum_yy[i] > 1e-6f) {
                float d = dasf_sum_xy[i] / dasf_sum_yy[i];
                dasf_out[i] = (d < 0.01f) ? 0.01f : (d > 1.0f) ? 1.0f : d;
            } else {
                dasf_out[i] = NAN;
            }
        }

        /* NDVI masking: set DASF=NaN for non-vegetation pixels (NDVI < 0.2) */
        int n_masked = 0;
        for (int i = 0; i < npix; i++) {
            float r = dasf_red_band[i];
            float n = dasf_nir_band[i];
            float ndvi = (isfinite(r) && isfinite(n) && (r + n) > 0.01f)
                         ? (n - r) / (n + r) : -1.0f;
            if (ndvi < 0.2f) { dasf_out[i] = NAN; n_masked++; }
        }
        G_verbose_message(_("DASF: masked %d non-vegetation pixels (NDVI<0.2)"),
                          n_masked);

        write_raster2d(iso->dasf_output, dasf_out, nrows, ncols);
        G_message(_("DASF written to <%s>"), iso->dasf_output);

        G_free(dasf_out);
        G_free(dasf_sum_xy);   G_free(dasf_sum_yy);
        G_free(dasf_red_band); G_free(dasf_nir_band);
    }

    /* ── #3/#5: Surface prior MAP regularisation ── */
    if (refl_cube && surf_mdl) {
        G_message(_("Applying surface prior MAP regularisation..."));

        /* If uncertainty available, add model discrepancy in quadrature (#6) */
        float *sigma2_full = NULL;
        if (sigma_cube && sigma_model) {
            sigma2_full = G_malloc((size_t)ndepths * npix * sizeof(float));
            for (int b = 0; b < ndepths; b++) {
                float sd_mdl = sigma_model[b];
                float *sc = sigma_cube + (size_t)b * npix;
                float *s2 = sigma2_full + (size_t)b * npix;
                for (int i = 0; i < npix; i++) {
                    float sc_i = sc[i];
                    if (!isfinite(sc_i)) { s2[i] = NAN; continue; }
                    s2[i] = sc_i * sc_i + sd_mdl * sd_mdl;
                }
            }
        }

        surface_model_regularize(surf_mdl, refl_cube, sigma2_full,
                                  ndepths, npix, 0.1f);

        G_free(sigma2_full);
        G_message(_("  MAP regularisation complete."));
    }

    /* ── Write cube to output (if deferred) ── */
    if (refl_cube) {
        G_message(_("Writing reflectance bands..."));
        for (int z = 0; z < ndepths; z++)
            write_band_to_rast3d(outmap,
                                  refl_cube + (size_t)z * npix,
                                  nrows, ncols, z, null_d);

        if (uncmap && sigma_cube) {
            G_message(_("Writing uncertainty bands..."));
            for (int z = 0; z < ndepths; z++)
                write_band_to_rast3d(uncmap,
                                      sigma_cube + (size_t)z * npix,
                                      nrows, ncols, z, null_d);
        }
    }

    /* ── Close maps ── */
    if (!Rast3d_close(inmap))
        G_fatal_error(_("Cannot close input map <%s>"), input_name);
    if (!Rast3d_close(outmap))
        G_fatal_error(_("Cannot close output map <%s>"), output_name);
    if (uncmap && !Rast3d_close(uncmap))
        G_fatal_error(_("Cannot close uncertainty map <%s>"), iso->unc_output);

    /* ── Propagate band wavelength metadata to output hist ── */
    write_band_wl_hist(output_name, band_wl, band_fwhm, ndepths);
    if (iso->unc_output)
        write_band_wl_hist(iso->unc_output, band_wl, band_fwhm, ndepths);

    /* ── Cleanup ── */
    G_free(band_wl);    G_free(band_fwhm);
    G_free(Rs);         G_free(Tds);     G_free(Tus);   G_free(ss);
    G_free(Tdds);
    G_free(slope_data); G_free(aspect_data);
    G_free(vza_data);   G_free(vaa_data);
    G_free(fiso_data);  G_free(fvol_data);  G_free(fgeo_data);
    G_free(dcell_slice);
    G_free(rad_band);   G_free(refl_band);
    G_free(sigma_band);
    G_free(refl_cube);  G_free(sigma_cube);
    if (free_aod_map) G_free(aod_map_data);
    if (free_h2o_map) G_free(h2o_map_data);
    G_free(sigma_model);
    surface_model_free(surf_mdl);

    G_message(_("Surface reflectance written to <%s>"), output_name);
    if (uncmap)
        G_message(_("Uncertainty written to <%s>"), iso->unc_output);
}

/* ── main ────────────────────────────────────────────────────────────────── */

/**
 * \brief GRASS module entry point for \c i.hyper.atcorr.
 *
 * Parses command-line options, optionally builds or loads a 3-D
 * [AOD × H₂O × λ] LUT, and — if an \c input= / \c output= pair is given —
 * invokes correct_raster3d() to apply the full ISOFIT-extended 6SV2.1
 * correction pipeline to a hyperspectral Raster3D radiance cube.
 *
 * At least one of \c lut= (write a LUT file) or \c output= (write a corrected
 * Raster3D map) must be specified.  Image-based retrievals (\c -a, \c -w,
 * \c -p, \c -m flags), NBAR normalisation, terrain illumination correction,
 * MAP regularisation (\c -r), per-band uncertainty output (\c -u), and DASF
 * retrieval are all activated via flags and options parsed here.
 *
 * \param[in]  argc  Argument count.
 * \param[in]  argv  Argument vector.
 * \return \c EXIT_SUCCESS on success; exits via G_fatal_error() on failure.
 */
int main(int argc, char *argv[])
{
    G_gisinit(argv[0]);
    Rast3d_init_defaults();

    struct GModule *module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("atmospheric correction"));
    G_add_keyword(_("radiative transfer"));
    G_add_keyword(_("6SV"));
    G_add_keyword(_("LUT"));
    G_add_keyword(_("hyperspectral"));
    module->description =
        _("Atmospheric correction of hyperspectral Raster3D radiance imagery "
          "using the 6SV2.1 radiative transfer algorithm.");

    /* ── I/O ── */
    struct Option *opt_input = G_define_standard_option(G_OPT_R3_INPUT);
    opt_input->required    = NO;
    opt_input->label       = _("Input radiance Raster3D map");
    opt_input->description = _("TOA radiance in W/(m² sr µm); "
                               "band wavelengths read from r3.info metadata");
    opt_input->guisection  = _("Correction");

    struct Option *opt_output = G_define_standard_option(G_OPT_R3_OUTPUT);
    opt_output->required    = NO;
    opt_output->label       = _("Output surface reflectance Raster3D map");
    opt_output->guisection  = _("Correction");

    struct Option *opt_lut = G_define_option();
    opt_lut->key         = "lut";
    opt_lut->type        = TYPE_STRING;
    opt_lut->required    = NO;
    opt_lut->gisprompt   = "new,file,file";
    opt_lut->label       = _("Output LUT binary file");
    opt_lut->description = _("Binary LUT (*.lut) with R_atm, T_down, T_up, s_alb "
                             "on an [AOD × H2O × wavelength] grid");
    opt_lut->guisection  = _("LUT");

    /* ── Geometry ── */
    struct Option *opt_sza = G_define_option();
    opt_sza->key = "sza"; opt_sza->type = TYPE_DOUBLE; opt_sza->required = NO;
    opt_sza->label = _("Solar zenith angle (degrees, 0–89) (overrides metadata)");
    opt_sza->guisection = _("Geometry");

    struct Option *opt_vza = G_define_option();
    opt_vza->key = "vza"; opt_vza->type = TYPE_DOUBLE;
    opt_vza->required = NO; opt_vza->answer = "0";
    opt_vza->label = _("View zenith angle (degrees, 0–60) (overrides metadata)");
    opt_vza->guisection = _("Geometry");

    struct Option *opt_raa = G_define_option();
    opt_raa->key = "raa"; opt_raa->type = TYPE_DOUBLE;
    opt_raa->required = NO; opt_raa->answer = "0";
    opt_raa->label = _("Relative azimuth angle (degrees) (overrides metadata)");
    opt_raa->guisection = _("Geometry");

    struct Option *opt_altitude = G_define_option();
    opt_altitude->key = "altitude"; opt_altitude->type = TYPE_DOUBLE;
    opt_altitude->required = NO; opt_altitude->answer = "1000";
    opt_altitude->label = _("Sensor altitude (km; > 900 = satellite) (overrides metadata)");
    opt_altitude->guisection = _("Geometry");

    /* ── Atmosphere ── */
    struct Option *opt_atmo = G_define_option();
    opt_atmo->key = "atmosphere"; opt_atmo->type = TYPE_STRING;
    opt_atmo->required = NO; opt_atmo->answer = "us62";
    opt_atmo->options = "us62,midsum,midwin,tropical,subsum,subwin";
    opt_atmo->description = _("Standard atmosphere model (overrides metadata)");
    opt_atmo->guisection = _("Atmosphere");

    struct Option *opt_aerosol = G_define_option();
    opt_aerosol->key = "aerosol"; opt_aerosol->type = TYPE_STRING;
    opt_aerosol->required = NO; opt_aerosol->answer = "continental";
    opt_aerosol->options = "none,continental,maritime,urban,desert,custom";
    opt_aerosol->description = _("Aerosol model (use 'custom' with mie_r/mie_sigma/mie_mr/mie_mi) (overrides metadata)");
    opt_aerosol->guisection = _("Atmosphere");

    struct Option *opt_mie_r = G_define_option();
    opt_mie_r->key = "mie_r"; opt_mie_r->type = TYPE_DOUBLE;
    opt_mie_r->required = NO; opt_mie_r->answer = "0.10";
    opt_mie_r->description = _("Custom Mie: log-normal mode radius [µm] (AERONET fine-mode r_eff~0.10-0.15)");
    opt_mie_r->guisection = _("Atmosphere");

    struct Option *opt_mie_sigma = G_define_option();
    opt_mie_sigma->key = "mie_sigma"; opt_mie_sigma->type = TYPE_DOUBLE;
    opt_mie_sigma->required = NO; opt_mie_sigma->answer = "1.50";
    opt_mie_sigma->description = _("Custom Mie: geometric standard deviation σ_g (typical 1.4-1.8)");
    opt_mie_sigma->guisection = _("Atmosphere");

    struct Option *opt_mie_mr = G_define_option();
    opt_mie_mr->key = "mie_mr"; opt_mie_mr->type = TYPE_DOUBLE;
    opt_mie_mr->required = NO; opt_mie_mr->answer = "1.45";
    opt_mie_mr->description = _("Custom Mie: real refractive index at 550 nm (dust~1.55, carbon~1.75, marine~1.38)");
    opt_mie_mr->guisection = _("Atmosphere");

    struct Option *opt_mie_mi = G_define_option();
    opt_mie_mi->key = "mie_mi"; opt_mie_mi->type = TYPE_DOUBLE;
    opt_mie_mi->required = NO; opt_mie_mi->answer = "0.005";
    opt_mie_mi->description = _("Custom Mie: imaginary refractive index at 550 nm (absorbing 0.01-0.05, scattering <0.005)");
    opt_mie_mi->guisection = _("Atmosphere");

    struct Option *opt_ozone = G_define_option();
    opt_ozone->key = "ozone"; opt_ozone->type = TYPE_DOUBLE;
    opt_ozone->required = NO; opt_ozone->answer = "300";
    opt_ozone->description = _("Total ozone column (Dobson units) (overrides metadata)");
    opt_ozone->guisection = _("Atmosphere");

    /* ── Surface BRDF ── */
    struct Option *opt_brdf = G_define_option();
    opt_brdf->key         = "brdf";
    opt_brdf->type        = TYPE_STRING;
    opt_brdf->required    = NO;
    opt_brdf->answer      = "lambertian";
    opt_brdf->options     = "lambertian,rahman,roujean,hapke,ocean,"
                            "walthall,minnaert,rosslimaignan";
    opt_brdf->description = _("Surface BRDF model for non-Lambertian correction");
    opt_brdf->guisection  = _("Surface");

    struct Option *opt_brdf_params = G_define_option();
    opt_brdf_params->key         = "brdf_params";
    opt_brdf_params->type        = TYPE_STRING;
    opt_brdf_params->required    = NO;
    opt_brdf_params->answer      = NULL;
    opt_brdf_params->label       = _("BRDF model parameters (comma-separated floats)");
    opt_brdf_params->description =
        _("Up to 5 comma-separated floats for the chosen BRDF model:\n"
          "  lambertian: rho0\n"
          "  rahman:     rho0, af, k\n"
          "  roujean:    k0, k1, k2\n"
          "  hapke:      om, af, s0, h\n"
          "  ocean:      wspd_ms, azw_deg, sal_ppt, pcl_mgl, wl_um\n"
          "  walthall:   a, ap, b, c\n"
          "  minnaert:   k, b\n"
          "  rosslimaignan: f_iso, f_vol, f_geo");
    opt_brdf_params->guisection  = _("Surface");

    /* ── LUT grid ── */
    struct Option *opt_aod = G_define_option();
    opt_aod->key = "aod"; opt_aod->type = TYPE_STRING;
    opt_aod->required = NO; opt_aod->answer = "0.0,0.05,0.1,0.2,0.4,0.8";
    opt_aod->label = _("AOD at 550 nm grid (comma-separated)");
    opt_aod->guisection = _("LUT");

    struct Option *opt_h2o = G_define_option();
    opt_h2o->key = "h2o"; opt_h2o->type = TYPE_STRING;
    opt_h2o->required = NO; opt_h2o->answer = "0.5,1.0,1.5,2.0,3.5,5.0";
    opt_h2o->label = _("Column water vapour grid in g/cm² (comma-separated)");
    opt_h2o->guisection = _("LUT");

    struct Option *opt_wl_min = G_define_option();
    opt_wl_min->key = "wl_min"; opt_wl_min->type = TYPE_DOUBLE;
    opt_wl_min->required = NO; opt_wl_min->answer = "0.40";
    opt_wl_min->description = _("Minimum wavelength (µm)");
    opt_wl_min->guisection = _("LUT");

    struct Option *opt_wl_max = G_define_option();
    opt_wl_max->key = "wl_max"; opt_wl_max->type = TYPE_DOUBLE;
    opt_wl_max->required = NO; opt_wl_max->answer = "2.50";
    opt_wl_max->description = _("Maximum wavelength (µm)");
    opt_wl_max->guisection = _("LUT");

    struct Option *opt_wl_step = G_define_option();
    opt_wl_step->key = "wl_step"; opt_wl_step->type = TYPE_DOUBLE;
    opt_wl_step->required = NO; opt_wl_step->answer = "0.01";
    opt_wl_step->description = _("Wavelength step (µm)");
    opt_wl_step->guisection = _("LUT");

    /* ── Correction parameters ── */
    struct Option *opt_doy = G_define_option();
    opt_doy->key = "doy"; opt_doy->type = TYPE_INTEGER;
    opt_doy->required = NO; opt_doy->answer = "180";
    opt_doy->label = _("Day of year for Earth-Sun distance (1–365) (overrides metadata)");
    opt_doy->guisection = _("Correction");

    struct Option *opt_aod_val = G_define_option();
    opt_aod_val->key = "aod_val"; opt_aod_val->type = TYPE_DOUBLE;
    opt_aod_val->required = NO; opt_aod_val->answer = "0.1";
    opt_aod_val->label = _("Scene AOD at 550 nm for correction (scalar fallback) (overrides metadata)");
    opt_aod_val->guisection = _("Correction");

    struct Option *opt_h2o_val = G_define_option();
    opt_h2o_val->key = "h2o_val"; opt_h2o_val->type = TYPE_DOUBLE;
    opt_h2o_val->required = NO; opt_h2o_val->answer = "2.0";
    opt_h2o_val->label = _("Scene column water vapour g/cm² (scalar fallback) (overrides metadata)");
    opt_h2o_val->guisection = _("Correction");

    /* ── ISOFIT improvements ── */

    /* #1 Per-pixel maps */
    struct Option *opt_aod_map = G_define_standard_option(G_OPT_R_INPUT);
    opt_aod_map->key = "aod_map"; opt_aod_map->required = NO;
    opt_aod_map->label = _("Per-pixel AOD raster (overrides aod_val= where non-null)");
    opt_aod_map->description = _("2-D raster of AOD at 550 nm");
    opt_aod_map->guisection = _("ISOFIT");

    struct Option *opt_h2o_map = G_define_standard_option(G_OPT_R_INPUT);
    opt_h2o_map->key = "h2o_map"; opt_h2o_map->required = NO;
    opt_h2o_map->label = _("Per-pixel water vapour raster (overrides h2o_val= where non-null)");
    opt_h2o_map->description = _("2-D raster of column water vapour in g/cm²");
    opt_h2o_map->guisection = _("ISOFIT");

    struct Option *opt_smooth = G_define_option();
    opt_smooth->key = "smooth"; opt_smooth->type = TYPE_DOUBLE;
    opt_smooth->required = NO; opt_smooth->answer = "0";
    opt_smooth->label = _("Gaussian smoothing σ in pixels for AOD/H2O maps");
    opt_smooth->description =
        _("Spatially smooths aod_map= and h2o_map= before correction. "
          "0 = disabled. Typical value: 2–5 pixels.");
    opt_smooth->guisection = _("ISOFIT");

    /* #2 Adjacency */
    struct Option *opt_adj_psf = G_define_option();
    opt_adj_psf->key = "adj_psf"; opt_adj_psf->type = TYPE_DOUBLE;
    opt_adj_psf->required = NO; opt_adj_psf->answer = "0";
    opt_adj_psf->label = _("Adjacency effect PSF radius (km; 0 = disabled)");
    opt_adj_psf->description =
        _("Environmental PSF radius for Vermote 1997 adjacency correction. "
          "Typical value: 0.5–2 km. 0 = disabled.");
    opt_adj_psf->guisection = _("ISOFIT");

    struct Option *opt_pixel_size = G_define_option();
    opt_pixel_size->key = "pixel_size"; opt_pixel_size->type = TYPE_DOUBLE;
    opt_pixel_size->required = NO; opt_pixel_size->answer = "0";
    opt_pixel_size->label = _("Pixel size in metres (0 = auto-detect from region)");
    opt_pixel_size->guisection = _("ISOFIT");

    /* #4/#6 Uncertainty output */
    struct Option *opt_uncertainty;
    opt_uncertainty = G_define_standard_option(G_OPT_R3_OUTPUT);
    opt_uncertainty->key = "uncertainty"; opt_uncertainty->required = NO;
    opt_uncertainty->label = _("Output uncertainty Raster3D map (requires -u flag)");
    opt_uncertainty->guisection = _("ISOFIT");

    /* Flags */
    struct Flag *flag_u = G_define_flag();
    flag_u->key = 'u';
    flag_u->label = _("Compute per-band reflectance uncertainty");
    flag_u->description =
        _("Propagates instrument noise and AOD uncertainty through the "
          "inversion. Stores σ_rfl per pixel per band. "
          "Write to Raster3D with uncertainty= option.");
    flag_u->guisection = _("ISOFIT");

    struct Flag *flag_r = G_define_flag();
    flag_r->key = 'r';
    flag_r->label = _("Apply surface prior MAP regularisation");
    flag_r->description =
        _("After inverting all bands, blends retrieved reflectance with a "
          "3-component Gaussian mixture surface prior (vegetation/soil/water) "
          "using diagonal MAP estimation. Requires loading the full cube into "
          "memory. Uses per-band model discrepancy as uncertainty floor (#6).");
    flag_r->guisection = _("ISOFIT");

    /* ── Image-based retrieval flags ── */
    struct Flag *flag_a = G_define_flag();
    flag_a->key = 'a';
    flag_a->label = _("Retrieve AOD from Dark Dense Vegetation (DDV)");
    flag_a->description =
        _("Estimates per-pixel AOD at 550 nm from dark vegetated pixels "
          "(MODIS dark-target: 470/660/860/2130 nm bands). "
          "Updates aod_val= and provides a per-pixel AOD map. "
          "Requires input= with wavelength metadata.");
    flag_a->guisection = _("Retrieval");

    struct Flag *flag_w = G_define_flag();
    flag_w->key = 'w';
    flag_w->label = _("Retrieve column water vapour from 940 nm absorption");
    flag_w->description =
        _("Estimates per-pixel WVC [g/cm²] from the 940 nm band depth "
          "(continuum interpolation: 865/940/1040 nm). "
          "Provides a per-pixel H2O map for correction. "
          "Requires input= with wavelength metadata.");
    flag_w->guisection = _("Retrieval");

    struct Flag *flag_z = G_define_flag();
    flag_z->key = 'z';
    flag_z->label = _("Retrieve O3 column from Chappuis absorption");
    flag_z->description =
        _("Estimates scene-mean ozone [DU] from 600 nm band depth "
          "(continuum: 540/600/680 nm). "
          "Updates the ozone= value used in LUT computation. "
          "Requires input= with wavelength metadata.");
    flag_z->guisection = _("Retrieval");

    struct Flag *flag_p = G_define_flag();
    flag_p->key = 'p';
    flag_p->label = _("Retrieve per-pixel surface pressure from O₂-A band (760 nm)");
    flag_p->description =
        _("Estimates per-pixel surface pressure [hPa] from the O₂-A band depth "
          "(continuum: 740/760/780 nm). "
          "Applies per-pixel Rayleigh scaling to R_atm, T_down, T_up. "
          "K_O2=0.25 calibrated to ~10 nm FWHM sensors. "
          "Requires input= with wavelength metadata.");
    flag_p->guisection = _("Retrieval");

    struct Flag *flag_m = G_define_flag();
    flag_m->key = 'm';
    flag_m->label = _("Compute pre-correction cloud / shadow / water / snow bitmask");
    flag_m->description =
        _("Classifies each pixel using TOA reflectance thresholds "
          "(cloud: blue>0.25 AND NDVI<0.2; shadow: VIS+NIR<0.04; water: NIR<0.05; "
          "snow: NDSI>0.4). "
          "Output written to quality= map. "
          "DDV and H₂O retrievals automatically exclude flagged pixels. "
          "Requires input= with wavelength metadata.");
    flag_m->guisection = _("Retrieval");

    struct Flag *flag_P = G_define_flag();
    flag_P->key = 'P';
    flag_P->label = _("Enable vector (Stokes I,Q,U) radiative transfer");
    flag_P->description =
        _("Use sixs_ospol() instead of sixs_os() for the atmospheric RT. "
          "Propagates all three Stokes components simultaneously, improving "
          "the atmospheric path reflectance R_atm by 1–5% in blue bands "
          "(Rayleigh polarisation feedback). "
          "Approximately 3× slower than scalar RT. "
          "Aerosol is treated as spherical (simplified Müller matrix).");
    flag_P->guisection = _("LUT");

    struct Flag *flag_e = G_define_flag();
    flag_e->key = 'e';
    flag_e->label = _("Joint AOD + H₂O optimal-estimation retrieval");
    flag_e->description =
        _("Per-pixel MAP grid-search inversion of AOD and column water vapour "
          "using spectral smoothness (VIS) and H₂O band-depth (NIR) constraints. "
          "Supersedes independent -a and -w retrievals when used together. "
          "Requires input= with wavelength metadata and a pre-computed LUT.");
    flag_e->guisection = _("Retrieval");

    struct Option *opt_oe_sigma_aod = G_define_option();
    opt_oe_sigma_aod->key         = "oe_sigma_aod";
    opt_oe_sigma_aod->type        = TYPE_DOUBLE;
    opt_oe_sigma_aod->required    = NO;
    opt_oe_sigma_aod->answer      = "0.5";
    opt_oe_sigma_aod->label       = _("OE prior uncertainty for log(AOD)");
    opt_oe_sigma_aod->description =
        _("Controls how strongly the OE solution is pulled toward aod_val=. "
          "0.5 = broad prior (±50% in log-AOD space); 0.2 = tight constraint.");
    opt_oe_sigma_aod->guisection  = _("Retrieval");

    struct Option *opt_oe_sigma_h2o = G_define_option();
    opt_oe_sigma_h2o->key         = "oe_sigma_h2o";
    opt_oe_sigma_h2o->type        = TYPE_DOUBLE;
    opt_oe_sigma_h2o->required    = NO;
    opt_oe_sigma_h2o->answer      = "1.0";
    opt_oe_sigma_h2o->label       = _("OE prior uncertainty for H₂O [g/cm²]");
    opt_oe_sigma_h2o->description =
        _("Controls H₂O prior strength. 1.0 = broad (±1 g/cm²); 0.5 = tight.");
    opt_oe_sigma_h2o->guisection  = _("Retrieval");

    struct Option *opt_maiac_patch = G_define_option();
    opt_maiac_patch->key         = "maiac_patch";
    opt_maiac_patch->type        = TYPE_INTEGER;
    opt_maiac_patch->required    = NO;
    opt_maiac_patch->answer      = "0";
    opt_maiac_patch->label       = _("MAIAC patch size for AOD spatial regularization (pixels; 0=disabled)");
    opt_maiac_patch->description =
        _("After DDV retrieval (-a), divides the image into non-overlapping "
          "patches of this size and replaces each patch AOD with the patch median. "
          "Non-DDV patches are filled by inverse-distance weighting. "
          "Typical: 32 pixels for 30 m imagery; 16 for 5 m imagery.");
    opt_maiac_patch->guisection  = _("Retrieval");

    struct Option *opt_quality = G_define_standard_option(G_OPT_R_OUTPUT);
    opt_quality->key      = "quality";
    opt_quality->required = NO;
    opt_quality->label    = _("Output 2-D quality bitmask raster (requires -m flag)");
    opt_quality->description =
        _("Per-pixel quality bitmask: "
          "bit 0=cloud, bit 1=shadow, bit 2=water, bit 3=snow/ice. "
          "Written as integer raster.");
    opt_quality->guisection = _("Retrieval");

    struct Option *opt_dem = G_define_standard_option(G_OPT_R_INPUT);
    opt_dem->key      = "dem";
    opt_dem->required = NO;
    opt_dem->label    = _("DEM raster for surface pressure retrieval");
    opt_dem->description =
        _("2-D elevation raster [m above sea level]. "
          "Scene-mean elevation → ISA pressure, overriding standard-atmosphere "
          "sea-level pressure in LUT computation.");
    opt_dem->guisection = _("Retrieval");

    /* ── Terrain illumination correction ── */
    struct Option *opt_slope = G_define_standard_option(G_OPT_R_INPUT);
    opt_slope->key      = "slope";
    opt_slope->required = NO;
    opt_slope->label    = _("Terrain slope raster [degrees]");
    opt_slope->description =
        _("2-D raster of terrain slope in degrees. "
          "When combined with aspect=, enables per-pixel terrain illumination "
          "correction (Cosine model: direct irradiance scaled by cos_i/cos_sza, "
          "diffuse by the skyview factor).");
    opt_slope->guisection = _("Terrain");

    struct Option *opt_aspect = G_define_standard_option(G_OPT_R_INPUT);
    opt_aspect->key      = "aspect";
    opt_aspect->required = NO;
    opt_aspect->label    = _("Terrain aspect raster [degrees, CW from North]");
    opt_aspect->description =
        _("2-D raster of terrain aspect in degrees clockwise from North. "
          "Must be provided together with slope=.");
    opt_aspect->guisection = _("Terrain");

    struct Option *opt_sun_az = G_define_option();
    opt_sun_az->key         = "sun_azimuth";
    opt_sun_az->type        = TYPE_DOUBLE;
    opt_sun_az->required    = NO;
    opt_sun_az->answer      = "180";
    opt_sun_az->label       = _("Solar azimuth angle [degrees, CW from North] (overrides metadata)");
    opt_sun_az->description =
        _("Used for terrain illumination (cos_incidence) and NBAR relative "
          "azimuth computation. Typically from r.sunmask or scene metadata.");
    opt_sun_az->guisection  = _("Terrain");

    struct Option *opt_vza_map = G_define_standard_option(G_OPT_R_INPUT);
    opt_vza_map->key      = "view_zenith";
    opt_vza_map->required = NO;
    opt_vza_map->label    = _("Per-pixel view zenith angle raster [degrees]");
    opt_vza_map->description =
        _("2-D raster of per-pixel view zenith angles. "
          "Used for T_up Beer-Lambert path-length scaling in terrain correction. "
          "Falls back to scalar vza= when not provided.");
    opt_vza_map->guisection = _("Terrain");

    struct Option *opt_vaa_map = G_define_standard_option(G_OPT_R_INPUT);
    opt_vaa_map->key      = "view_azimuth";
    opt_vaa_map->required = NO;
    opt_vaa_map->label    = _("Per-pixel view azimuth angle raster [degrees, CW from North]");
    opt_vaa_map->description =
        _("2-D raster of per-pixel view azimuth angles. "
          "Used to compute relative azimuth for NBAR normalization.");
    opt_vaa_map->guisection = _("Terrain");

    /* ── NBAR normalization (MCD43 Ross-Li kernel weights) ── */
    struct Option *opt_fiso = G_define_standard_option(G_OPT_R_INPUT);
    opt_fiso->key      = "brdf_fiso";
    opt_fiso->required = NO;
    opt_fiso->label    = _("MCD43 f_iso kernel weight raster");
    opt_fiso->description =
        _("Ross-Li isotropic kernel weight from MODIS MCD43A1. "
          "When all three kernel weights (brdf_fiso=, brdf_fvol=, brdf_fgeo=) "
          "are provided, output reflectance is NBAR-normalized to nadir view "
          "using standard MODIS Ross-Thick + Li-Sparse kernels.");
    opt_fiso->guisection = _("BRDF");

    struct Option *opt_fvol = G_define_standard_option(G_OPT_R_INPUT);
    opt_fvol->key      = "brdf_fvol";
    opt_fvol->required = NO;
    opt_fvol->label    = _("MCD43 f_vol kernel weight raster");
    opt_fvol->description =
        _("Ross-Thick volumetric kernel weight from MODIS MCD43A1.");
    opt_fvol->guisection = _("BRDF");

    struct Option *opt_fgeo = G_define_standard_option(G_OPT_R_INPUT);
    opt_fgeo->key      = "brdf_fgeo";
    opt_fgeo->required = NO;
    opt_fgeo->label    = _("MCD43 f_geo kernel weight raster");
    opt_fgeo->description =
        _("Li-Sparse geometric kernel weight from MODIS MCD43A1.");
    opt_fgeo->guisection = _("BRDF");

    /* ── FlexBRDF: spectral disaggregation of 7-band MCD43 ── */
    struct Option *opt_mcd43_fiso = G_define_option();
    opt_mcd43_fiso->key         = "mcd43_fiso";
    opt_mcd43_fiso->type        = TYPE_STRING;
    opt_mcd43_fiso->required    = NO;
    opt_mcd43_fiso->answer      = NULL;
    opt_mcd43_fiso->label       = _("MCD43 f_iso at 7 MODIS bands (469,555,645,858,1240,1640,2130 nm)");
    opt_mcd43_fiso->description =
        _("Seven comma-separated f_iso kernel weights from MCD43A1 "
          "at the 7 MODIS bands. Used to disaggregate the isotropic kernel "
          "weight to the full hyperspectral range via piecewise-linear "
          "interpolation + Tikhonov smoothing (FlexBRDF).");
    opt_mcd43_fiso->guisection  = _("BRDF");

    struct Option *opt_mcd43_fvol = G_define_option();
    opt_mcd43_fvol->key         = "mcd43_fvol";
    opt_mcd43_fvol->type        = TYPE_STRING;
    opt_mcd43_fvol->required    = NO;
    opt_mcd43_fvol->answer      = NULL;
    opt_mcd43_fvol->label       = _("MCD43 f_vol at 7 MODIS bands");
    opt_mcd43_fvol->description =
        _("Seven comma-separated f_vol (RossThick volumetric) kernel weights.");
    opt_mcd43_fvol->guisection  = _("BRDF");

    struct Option *opt_mcd43_fgeo = G_define_option();
    opt_mcd43_fgeo->key         = "mcd43_fgeo";
    opt_mcd43_fgeo->type        = TYPE_STRING;
    opt_mcd43_fgeo->required    = NO;
    opt_mcd43_fgeo->answer      = NULL;
    opt_mcd43_fgeo->label       = _("MCD43 f_geo at 7 MODIS bands");
    opt_mcd43_fgeo->description =
        _("Seven comma-separated f_geo (LiSparse geometric) kernel weights.");
    opt_mcd43_fgeo->guisection  = _("BRDF");

    struct Option *opt_mcd43_alpha = G_define_option();
    opt_mcd43_alpha->key         = "mcd43_alpha";
    opt_mcd43_alpha->type        = TYPE_DOUBLE;
    opt_mcd43_alpha->required    = NO;
    opt_mcd43_alpha->answer      = "0.10";
    opt_mcd43_alpha->label       = _("Tikhonov smoothing strength for MCD43 disaggregation");
    opt_mcd43_alpha->description =
        _("Controls spectral smoothness of the disaggregated kernel weights. "
          "0.0 = no smoothing (piecewise-linear only); ~0.1 = gentle smoothing "
          "(recommended). Larger values increase spectral smoothness.");
    opt_mcd43_alpha->guisection  = _("BRDF");

    /* ── DASF retrieval ── */
    struct Option *opt_dasf = G_define_standard_option(G_OPT_R_OUTPUT);
    opt_dasf->key      = "dasf";
    opt_dasf->required = NO;
    opt_dasf->label    = _("Output 2-D DASF raster (requires -D flag)");
    opt_dasf->description =
        _("Directional Area Scattering Factor: regresses per-pixel corrected BRF "
          "against PROSPECT-D leaf albedo over 710–790 nm. "
          "Output range [0.01, 1.0]; NaN for non-vegetation (NDVI < 0.2). "
          "Knyazikhin et al. (2013) PNAS 110, E185-E192.");
    opt_dasf->guisection = _("Retrieval");

    struct Flag *flag_D = G_define_flag();
    flag_D->key = 'D';
    flag_D->label = _("Retrieve DASF (canopy angular structure) to dasf= raster");
    flag_D->description =
        _("Accumulates per-pixel Directional Area Scattering Factor from corrected "
          "surface reflectance in the 710–790 nm NIR plateau. "
          "Output is written to the dasf= 2-D raster. "
          "Requires output= for per-pixel corrected BRF. "
          "Non-vegetation pixels (NDVI < 0.2) are masked to NaN.");
    flag_D->guisection = _("Retrieval");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* ── Validate mode ── */
    if (!opt_lut->answer && !opt_output->answer)
        G_fatal_error(_("Specify at least one output: lut= or output="));
    if (opt_output->answer && !opt_input->answer)
        G_fatal_error(_("output= requires input="));
    if (opt_uncertainty->answer && !flag_u->answer)
        G_warning(_("uncertainty= output ignored without -u flag"));
    if (flag_u->answer && !opt_output->answer)
        G_fatal_error(_("-u requires output= (needs correction to run first)"));
    if ((flag_a->answer || flag_w->answer || flag_z->answer ||
         flag_p->answer || flag_m->answer || flag_e->answer) && !opt_input->answer)
        G_fatal_error(_("Flags -a, -w, -z, -p, -m, -e require input="));
    if (flag_m->answer && !opt_quality->answer)
        G_warning(_("-m flag has no effect without quality= output option"));
    if (opt_quality->answer && !flag_m->answer)
        G_warning(_("quality= output requires -m flag"));
    if (flag_D->answer && !opt_output->answer)
        G_fatal_error(_("-D flag requires output= (corrected reflectance needed for DASF)"));
    if (flag_D->answer && !opt_dasf->answer)
        G_warning(_("-D flag has no effect without dasf= output option"));
    if (opt_dasf->answer && !flag_D->answer)
        G_warning(_("dasf= output requires -D flag"));
    {   /* FlexBRDF: all three MCD43 spectral options must be provided together */
        int mcd43_count = (!!opt_mcd43_fiso->answer + !!opt_mcd43_fvol->answer
                           + !!opt_mcd43_fgeo->answer);
        if (mcd43_count > 0 && mcd43_count < 3)
            G_fatal_error(_("mcd43_fiso=, mcd43_fvol=, and mcd43_fgeo= must all be "
                            "provided for FlexBRDF spectral disaggregation"));
    }

    /* ── Read metadata (i.hyper.metadata / hyper.json) ── */
    HyperMeta meta;
    float *meta_wl   = NULL;
    float *meta_fwhm = NULL;
    {
        /* Use max 2048 bands for metadata extraction; proper arrays are
         * allocated inside correct_raster3d() once ndepths is known. */
        const int meta_nmax = 2048;
        meta_wl   = G_malloc(meta_nmax * sizeof(float));
        meta_fwhm = G_malloc(meta_nmax * sizeof(float));
        (void)read_hyperjson_meta(opt_input->answer, meta_wl, meta_fwhm,
                                   meta_nmax, &meta);
    }

    /* ── Parse scalar parameters (CLI → metadata → hardcoded default) ── */
    float sza      = resolve_float_opt(opt_sza,
                        meta.sun_zenith_deg, meta.has_sun_zenith,
                        0.0f, 1);
    float vza      = resolve_float_opt(opt_vza,
                        meta.view_zenith_deg, meta.has_view_zenith,
                        0.0f, 0);
    float raa      = resolve_float_opt(opt_raa,
                        meta.relative_azimuth_deg, meta.has_relative_azimuth,
                        0.0f, 0);
    float altitude = resolve_float_opt(opt_altitude,
                        meta.altitude_km, meta.has_altitude,
                        1000.0f, 0);
    float ozone    = resolve_float_opt(opt_ozone,
                        meta.ozone_du, meta.has_ozone,
                        300.0f, 0);
    float aod_val  = resolve_float_opt(opt_aod_val,
                        meta.aod_550, meta.has_aod,
                        0.1f, 0);
    float h2o_val  = resolve_float_opt(opt_h2o_val,
                        meta.h2o_g_cm2, meta.has_h2o,
                        2.0f, 0);
    int   doy      = (int)resolve_float_opt(opt_doy,
                        (float)meta.day_of_year, meta.has_doy,
                        180.0f, 0);
    float wl_min   = (float)atof(opt_wl_min->answer);
    float wl_max   = (float)atof(opt_wl_max->answer);
    float wl_step  = (float)atof(opt_wl_step->answer);

    if (sza < 0.0f || sza >= 90.0f)
        G_fatal_error(_("sza must be in [0, 90)"));
    if (vza < 0.0f || vza > 60.0f)
        G_fatal_error(_("vza must be in [0, 60]"));
    if (wl_step <= 0.0f || wl_min >= wl_max)
        G_fatal_error(_("Invalid wavelength range or step"));
    if (doy < 1 || doy > 365)
        G_fatal_error(_("doy must be in [1, 365]"));

    float sun_azimuth = resolve_float_opt(opt_sun_az,
                            meta.sun_azimuth_deg, meta.has_sun_azimuth,
                            180.0f, 0);

    /* Terrain: slope= and aspect= must be specified together */
    if ((opt_slope->answer && !opt_aspect->answer) ||
        (!opt_slope->answer && opt_aspect->answer))
        G_fatal_error(_("slope= and aspect= must both be provided for "
                        "terrain illumination correction"));
    int do_terrain = (opt_slope->answer && opt_aspect->answer);

    /* NBAR: all three kernel-weight rasters must be provided */
    int nbar_count = (!!opt_fiso->answer + !!opt_fvol->answer + !!opt_fgeo->answer);
    if (nbar_count > 0 && nbar_count < 3)
        G_fatal_error(_("brdf_fiso=, brdf_fvol=, and brdf_fgeo= must all be "
                        "provided for NBAR normalization"));
    int do_nbar = (nbar_count == 3);

    int atmo_model, aerosol_model;
    const char *atmo_str, *aero_str;

    atmo_str = resolve_str_opt(
        opt_atmo, meta.atmosphere_model, meta.has_atmo_model, "us62");
    {
        if      (!strcmp(atmo_str, "us62"))     atmo_model = ATMO_US62;
        else if (!strcmp(atmo_str, "midsum"))   atmo_model = ATMO_MIDSUM;
        else if (!strcmp(atmo_str, "midwin"))   atmo_model = ATMO_MIDWIN;
        else if (!strcmp(atmo_str, "tropical")) atmo_model = ATMO_TROPICAL;
        else if (!strcmp(atmo_str, "subsum"))   atmo_model = ATMO_SUBSUM;
        else if (!strcmp(atmo_str, "subwin"))   atmo_model = ATMO_SUBWIN;
        else G_fatal_error(_("Unknown atmosphere model: %s"), atmo_str);
    }

    aero_str = resolve_str_opt(
        opt_aerosol, meta.aerosol_model, meta.has_aerosol_model, "continental");
    {
        if      (!strcmp(aero_str, "none"))        aerosol_model = AEROSOL_NONE;
        else if (!strcmp(aero_str, "continental")) aerosol_model = AEROSOL_CONTINENTAL;
        else if (!strcmp(aero_str, "maritime"))    aerosol_model = AEROSOL_MARITIME;
        else if (!strcmp(aero_str, "urban"))       aerosol_model = AEROSOL_URBAN;
        else if (!strcmp(aero_str, "desert"))      aerosol_model = AEROSOL_DESERT;
        else if (!strcmp(aero_str, "custom"))      aerosol_model = AEROSOL_CUSTOM;
        else G_fatal_error(_("Unknown aerosol model: %s"), aero_str);
    }

    if (aerosol_model == AEROSOL_CUSTOM) {
        double mie_r     = atof(opt_mie_r->answer);
        double mie_sigma = atof(opt_mie_sigma->answer);
        if (mie_r <= 0.0 || mie_sigma <= 1.0)
            G_fatal_error(_("aerosol=custom requires mie_r > 0 and mie_sigma > 1.0"));
    }

    /* BRDF type */
    static const struct { const char *name; BrdfType val; } brdf_map[] = {
        {"lambertian",    BRDF_LAMBERTIAN},  {"rahman",       BRDF_RAHMAN},
        {"roujean",       BRDF_ROUJEAN},     {"hapke",        BRDF_HAPKE},
        {"ocean",         BRDF_OCEAN},       {"walthall",     BRDF_WALTHALL},
        {"minnaert",      BRDF_MINNAERT},    {"rosslimaignan",BRDF_ROSSLIMAIGNAN},
        {NULL, 0}
    };
    BrdfType brdf_type = BRDF_LAMBERTIAN;
    for (int bi = 0; brdf_map[bi].name; bi++)
        if (strcmp(opt_brdf->answer, brdf_map[bi].name) == 0)
            { brdf_type = brdf_map[bi].val; break; }

    /* BRDF params: parse up to 5 comma-separated floats into the union */
    BrdfParams brdf_params;
    memset(&brdf_params, 0, sizeof(brdf_params));
    brdf_params.lambertian.rho0 = 1.0f;   /* safe default */
    if (opt_brdf_params->answer) {
        float pv[5] = {0};
        int np = 0;
        char *s = G_store(opt_brdf_params->answer), *tok;
        tok = strtok(s, ",");
        while (tok && np < 5) {
            pv[np++] = (float)atof(tok);
            tok = strtok(NULL, ",");
        }
        G_free(s);
        memcpy(&brdf_params, pv, (size_t)np * sizeof(float));
    }

    float aod_buf[64]; int n_aod = parse_csv_floats(opt_aod->answer, aod_buf, 64);
    if (n_aod <= 0) G_fatal_error(_("Cannot parse aod= values"));

    float h2o_buf[64]; int n_h2o = parse_csv_floats(opt_h2o->answer, h2o_buf, 64);
    if (n_h2o <= 0) G_fatal_error(_("Cannot parse h2o= values"));

    int n_wl = (int)((wl_max - wl_min) / wl_step) + 1;
    if (n_wl < 1 || n_wl > 10000)
        G_fatal_error(_("Wavelength grid size %d out of valid range"), n_wl);

    float *wl_buf = G_malloc(n_wl * sizeof(float));
    for (int i = 0; i < n_wl; i++) wl_buf[i] = wl_min + i * wl_step;

    /* ── FlexBRDF: disaggregate 7-band MCD43 to the LUT wavelength grid ── */
    float *flex_fiso_wl = NULL, *flex_fvol_wl = NULL, *flex_fgeo_wl = NULL;
    float  flex_fiso_ref = 1.0f, flex_fvol_ref = 0.0f, flex_fgeo_ref = 0.0f;
    int    have_flex_brdf = 0;

    if (opt_mcd43_fiso->answer && opt_mcd43_fvol->answer && opt_mcd43_fgeo->answer) {
        float fiso7[7], fvol7[7], fgeo7[7];
        int n7;
        n7 = parse_csv_floats(opt_mcd43_fiso->answer, fiso7, 7);
        if (n7 != 7) G_fatal_error(_("mcd43_fiso= requires exactly 7 values, got %d"), n7);
        n7 = parse_csv_floats(opt_mcd43_fvol->answer, fvol7, 7);
        if (n7 != 7) G_fatal_error(_("mcd43_fvol= requires exactly 7 values, got %d"), n7);
        n7 = parse_csv_floats(opt_mcd43_fgeo->answer, fgeo7, 7);
        if (n7 != 7) G_fatal_error(_("mcd43_fgeo= requires exactly 7 values, got %d"), n7);

        float alpha_mcd43 = (float)atof(opt_mcd43_alpha->answer);

        flex_fiso_wl = G_malloc(n_wl * sizeof(float));
        flex_fvol_wl = G_malloc(n_wl * sizeof(float));
        flex_fgeo_wl = G_malloc(n_wl * sizeof(float));
        mcd43_disaggregate(fiso7, fvol7, fgeo7, wl_buf, n_wl, alpha_mcd43,
                            flex_fiso_wl, flex_fvol_wl, flex_fgeo_wl);

        /* Reference values at 858 nm (MODIS NIR band B2) */
        int i858 = find_closest_band(wl_buf, n_wl, 0.858f);
        flex_fiso_ref = (flex_fiso_wl[i858] > 1e-6f) ? flex_fiso_wl[i858] : 1.0f;
        flex_fvol_ref = flex_fvol_wl[i858];
        flex_fgeo_ref = flex_fgeo_wl[i858];
        have_flex_brdf = 1;
        G_message(_("FlexBRDF: MCD43 disaggregated to %d LUT bands "
                    "(alpha=%.2f); f_iso_858=%.4f f_vol_858=%.4f f_geo_858=%.4f"),
                  n_wl, alpha_mcd43, flex_fiso_ref, flex_fvol_ref, flex_fgeo_ref);
    }

    G_free(meta_wl);
    G_free(meta_fwhm);

    /* ── Build LUT config ── */
    LutConfig cfg = {
        .wl = wl_buf, .n_wl = n_wl,
        .aod = aod_buf, .n_aod = n_aod,
        .h2o = h2o_buf, .n_h2o = n_h2o,
        .sza = sza, .vza = vza, .raa = raa,
        .altitude_km = altitude,
        .atmo_model = atmo_model, .aerosol_model = aerosol_model,
        .surface_pressure = 0.0f, .ozone_du = ozone,
        .brdf_type = brdf_type, .brdf_params = brdf_params,
        .enable_polar = flag_P->answer ? 1 : 0,
    };
    if (aerosol_model == AEROSOL_CUSTOM) {
        cfg.mie_r_mode  = (float)atof(opt_mie_r->answer);
        cfg.mie_sigma_g = (float)atof(opt_mie_sigma->answer);
        cfg.mie_m_real  = (float)atof(opt_mie_mr->answer);
        cfg.mie_m_imag  = (float)atof(opt_mie_mi->answer);
        G_message(_("Custom Mie aerosol: r_mode=%.3f µm  σ_g=%.2f  n_r=%.3f  n_i=%.4f"),
                  cfg.mie_r_mode, cfg.mie_sigma_g, cfg.mie_m_real, cfg.mie_m_imag);
    }

    /* ── Image-based atmospheric state retrievals ── *
     * Performed before atcorr_compute_lut() so that O3 and surface pressure
     * updates flow into the LUT.  AOD and H2O per-pixel maps are stored and
     * passed to correct_raster3d() via IsoFitParams.aod_data / .h2o_data. */
    float   *retrieved_aod      = NULL;
    float   *retrieved_h2o      = NULL;
    float   *retrieved_pressure = NULL;
    uint8_t *retrieved_quality  = NULL;

    if (opt_input->answer &&
        (flag_a->answer || flag_w->answer || flag_z->answer ||
         flag_p->answer || flag_m->answer || flag_e->answer)) {

        /* Open the input cube to get exact dims and band wavelengths */
        const char *ret_mapset = G_find_raster3d(opt_input->answer, "");
        if (!ret_mapset)
            G_fatal_error(_("Cannot find input cube <%s> for retrieval"),
                          opt_input->answer);

        RASTER3D_Region ret_reg;
        Rast3d_get_window(&ret_reg);
        RASTER3D_Map *ret_map = Rast3d_open_cell_old(
            opt_input->answer, ret_mapset, &ret_reg,
            RASTER3D_TILE_SAME_AS_FILE, RASTER3D_NO_CACHE);
        if (!ret_map)
            G_fatal_error(_("Cannot open input cube <%s> for retrieval"),
                          opt_input->answer);
        Rast3d_get_region_struct_map(ret_map, &ret_reg);

        int ret_nrows  = ret_reg.rows;
        int ret_ncols  = ret_reg.cols;
        int ret_nbands = ret_reg.depths;
        int ret_npix   = ret_nrows * ret_ncols;

        /* Parse band wavelengths from r3.info metadata */
        float *cube_wl    = G_malloc(ret_nbands * sizeof(float));
        float *cube_fwhm  = G_malloc(ret_nbands * sizeof(float));
        int    n_wl_parsed = parse_band_wl(opt_input->answer, cube_wl,
                                            cube_fwhm, ret_nbands);
        if (n_wl_parsed == 0) {
            G_warning(_("No wavelength metadata in <%s>; retrieval may be inaccurate"),
                      opt_input->answer);
            for (int b = 0; b < ret_nbands && b < n_wl; b++)
                cube_wl[b] = wl_buf[b];
        }

        /* ── O3 from Chappuis band (updates cfg.ozone_du) ── */
        if (flag_z->answer) {
            int b540 = find_closest_band(cube_wl, ret_nbands, 0.540f);
            int b600 = find_closest_band(cube_wl, ret_nbands, 0.600f);
            int b680 = find_closest_band(cube_wl, ret_nbands, 0.680f);
            G_message(_("Retrieving O3 from bands %.0f/%.0f/%.0f nm..."),
                      cube_wl[b540]*1000.0f, cube_wl[b600]*1000.0f,
                      cube_wl[b680]*1000.0f);

            float *L_540 = G_malloc(ret_npix * sizeof(float));
            float *L_600 = G_malloc(ret_npix * sizeof(float));
            float *L_680 = G_malloc(ret_npix * sizeof(float));
            int depths_o3[3]  = {b540, b600, b680};
            float *ptrs_o3[3] = {L_540, L_600, L_680};
            load_bands_from_cube(ret_map, depths_o3, 3,
                                 ret_nrows, ret_ncols, ptrs_o3);

            float o3_du = retrieve_o3_chappuis(L_540, L_600, L_680,
                                                ret_npix, sza, vza);
            G_free(L_540); G_free(L_600); G_free(L_680);
            G_message(_("O3 retrieved: %.1f DU (scene mean, Chappuis band)"),
                      o3_du);
            cfg.ozone_du = o3_du;
        }

        /* ── H2O per-pixel: multi-band triplet consensus ── */
        if (flag_w->answer) {
            /* Band indices for three H2O absorption features */
            int b700  = find_closest_band(cube_wl, ret_nbands, 0.700f);
            int b720  = find_closest_band(cube_wl, ret_nbands, 0.720f);
            int b740  = find_closest_band(cube_wl, ret_nbands, 0.740f);
            int b865  = find_closest_band(cube_wl, ret_nbands, 0.865f);
            int b940  = find_closest_band(cube_wl, ret_nbands, 0.940f);
            int b1040 = find_closest_band(cube_wl, ret_nbands, 1.040f);
            int b1100 = find_closest_band(cube_wl, ret_nbands, 1.100f);
            int b1135 = find_closest_band(cube_wl, ret_nbands, 1.135f);
            int b1175 = find_closest_band(cube_wl, ret_nbands, 1.175f);

            G_message(_("Retrieving H2O from triplets %.0f/%.0f/%.0f, "
                        "%.0f/%.0f/%.0f, %.0f/%.0f/%.0f nm..."),
                      cube_wl[b700]*1000.0f, cube_wl[b720]*1000.0f, cube_wl[b740]*1000.0f,
                      cube_wl[b865]*1000.0f, cube_wl[b940]*1000.0f, cube_wl[b1040]*1000.0f,
                      cube_wl[b1100]*1000.0f, cube_wl[b1135]*1000.0f, cube_wl[b1175]*1000.0f);

            /* Load 9 bands */
            float *L_700  = G_malloc(ret_npix * sizeof(float));
            float *L_720  = G_malloc(ret_npix * sizeof(float));
            float *L_740  = G_malloc(ret_npix * sizeof(float));
            float *L_865  = G_malloc(ret_npix * sizeof(float));
            float *L_940  = G_malloc(ret_npix * sizeof(float));
            float *L_1040 = G_malloc(ret_npix * sizeof(float));
            float *L_1100 = G_malloc(ret_npix * sizeof(float));
            float *L_1135 = G_malloc(ret_npix * sizeof(float));
            float *L_1175 = G_malloc(ret_npix * sizeof(float));
            int   depths9[9]  = {b700, b720, b740, b865, b940, b1040,
                                  b1100, b1135, b1175};
            float *ptrs9[9]   = {L_700, L_720, L_740, L_865, L_940, L_1040,
                                  L_1100, L_1135, L_1175};
            load_bands_from_cube(ret_map, depths9, 9,
                                 ret_nrows, ret_ncols, ptrs9);

            /* Sensor FWHM at each feature band */
            float fwhm720  = (n_wl_parsed > 0 && cube_fwhm[b720]  > 0.0f)
                             ? cube_fwhm[b720]  : 0.0f;
            float fwhm940  = (n_wl_parsed > 0 && cube_fwhm[b940]  > 0.0f)
                             ? cube_fwhm[b940]  : 0.0f;
            float fwhm1135 = (n_wl_parsed > 0 && cube_fwhm[b1135] > 0.0f)
                             ? cube_fwhm[b1135] : 0.0f;

            /* Per-pixel WVC and validity for each triplet */
            float   *wvc720  = G_malloc(ret_npix * sizeof(float));
            float   *wvc940  = G_malloc(ret_npix * sizeof(float));
            float   *wvc1135 = G_malloc(ret_npix * sizeof(float));
            uint8_t *val720  = G_malloc(ret_npix * sizeof(uint8_t));
            uint8_t *val940  = G_malloc(ret_npix * sizeof(uint8_t));
            uint8_t *val1135 = G_malloc(ret_npix * sizeof(uint8_t));

            /* 720 nm: K_ref=0.0077 cm²/g at fwhm_ref=60nm (Kanpur-calibrated;
             * gives K_5nm=0.0535 via (60/5)^0.78=6.946), D_min=0.02, D_max=0.60 */
            retrieve_h2o_triplet(L_700, L_720, L_740,
                                 0.700f, 0.720f, 0.740f,
                                 0.0077f, 0.060f, fwhm720,
                                 0.02f, 0.60f,
                                 ret_npix, sza, vza, wvc720, val720);

            /* 940 nm: K_ref=0.036, fwhm_ref=50nm, D_min=0.05, D_max=0.90 */
            retrieve_h2o_triplet(L_865, L_940, L_1040,
                                 0.865f, 0.940f, 1.040f,
                                 0.036f, 0.050f, fwhm940,
                                 0.05f, 0.90f,
                                 ret_npix, sza, vza, wvc940, val940);

            /* 1135 nm: K_ref=0.0376 cm²/g at fwhm_ref=45nm (Kanpur-calibrated;
             * gives K_5nm=0.2087 via (45/5)^0.78=5.550), D_min=0.05, D_max=0.85 */
            retrieve_h2o_triplet(L_1100, L_1135, L_1175,
                                 1.100f, 1.135f, 1.175f,
                                 0.0376f, 0.045f, fwhm1135,
                                 0.05f, 0.85f,
                                 ret_npix, sza, vza, wvc1135, val1135);

            /* Free the 9 radiance bands */
            G_free(L_700); G_free(L_720); G_free(L_740);
            G_free(L_865); G_free(L_940); G_free(L_1040);
            G_free(L_1100); G_free(L_1135); G_free(L_1175);

            /* Consensus */
            retrieved_h2o = G_malloc(ret_npix * sizeof(float));
            float   *wvc_arr[3]  = {wvc720,  wvc940,  wvc1135};
            uint8_t *val_arr[3]  = {val720,  val940,  val1135};
            retrieve_h2o_consensus(3, wvc_arr, val_arr, ret_npix, retrieved_h2o);

            /* Scene means per feature and consensus (valid pixels only) */
            double s720=0, s940=0, s1135=0, scons=0;
            int n720=0, n940=0, n1135=0, ncons=0;
            for (int i = 0; i < ret_npix; i++) {
                if (val720[i])  { s720  += wvc720[i];  n720++;  }
                if (val940[i])  { s940  += wvc940[i];  n940++;  }
                if (val1135[i]) { s1135 += wvc1135[i]; n1135++; }
                /* Count consensus only for pixels where ≥1 band was valid */
                if (val720[i] || val940[i] || val1135[i]) {
                    scons += retrieved_h2o[i]; ncons++;
                }
            }
            G_free(wvc720); G_free(wvc940); G_free(wvc1135);
            G_free(val720); G_free(val940); G_free(val1135);

            G_message(_("H2O retrieved:  720nm=%.2f  940nm=%.2f  1135nm=%.2f  "
                        "consensus=%.2f g/cm² (%.0f%% valid pixels)"),
                      n720  > 0 ? (float)(s720  / n720)  : -1.0f,
                      n940  > 0 ? (float)(s940  / n940)  : -1.0f,
                      n1135 > 0 ? (float)(s1135 / n1135) : -1.0f,
                      ncons > 0 ? (float)(scons / ncons) : -1.0f,
                      100.0f * ncons / ret_npix);

            if (ncons > 0)
                h2o_val = (float)(scons / ncons);
        }

        /* ── AOD per-pixel from DDV ── */
        if (flag_a->answer) {
            int b470  = find_closest_band(cube_wl, ret_nbands, 0.470f);
            int b660  = find_closest_band(cube_wl, ret_nbands, 0.660f);
            int b860  = find_closest_band(cube_wl, ret_nbands, 0.860f);
            int b2130 = find_closest_band(cube_wl, ret_nbands, 2.130f);
            G_message(_("Retrieving AOD (DDV) from bands %.0f/%.0f/%.0f/%.0f nm..."),
                      cube_wl[b470]*1000.0f,  cube_wl[b660]*1000.0f,
                      cube_wl[b860]*1000.0f,  cube_wl[b2130]*1000.0f);

            float *L_470  = G_malloc(ret_npix * sizeof(float));
            float *L_660  = G_malloc(ret_npix * sizeof(float));
            float *L_860  = G_malloc(ret_npix * sizeof(float));
            float *L_2130 = G_malloc(ret_npix * sizeof(float));
            int depths_aod[4]  = {b470, b660, b860, b2130};
            float *ptrs_aod[4] = {L_470, L_660, L_860, L_2130};
            load_bands_from_cube(ret_map, depths_aod, 4,
                                 ret_nrows, ret_ncols, ptrs_aod);

            retrieved_aod = G_malloc(ret_npix * sizeof(float));
            float aod_mean = retrieve_aod_ddv(L_470, L_660, L_860, L_2130,
                                               ret_npix, doy, sza, retrieved_aod);
            G_free(L_470); G_free(L_660); G_free(L_860); G_free(L_2130);
            aod_val = aod_mean;
            G_message(_("AOD retrieved (DDV): %.3f scene mean at 550 nm"), aod_mean);

            /* ── MAIAC patch AOD spatial regularization ── */
            int maiac_patch = atoi(opt_maiac_patch->answer);
            if (maiac_patch >= 2) {
                G_message(_("MAIAC patch regularization (patch_sz=%d px)..."),
                          maiac_patch);
                retrieve_aod_maiac(retrieved_aod, ret_nrows, ret_ncols, maiac_patch);
                /* Recompute scene-mean after patch regularization */
                double s2 = 0.0; int n2 = 0;
                for (int i = 0; i < ret_npix; i++)
                    if (isfinite(retrieved_aod[i]) && retrieved_aod[i] >= 0.0f)
                        { s2 += retrieved_aod[i]; n2++; }
                if (n2 > 0) {
                    aod_val = (float)(s2 / n2);
                    G_message(_("AOD after MAIAC patch: %.3f scene mean"), aod_val);
                }
            }
        }

        /* ── O₂-A per-pixel surface pressure ── */
        if (flag_p->answer) {
            int b740 = find_closest_band(cube_wl, ret_nbands, 0.740f);
            int b760 = find_closest_band(cube_wl, ret_nbands, 0.760f);
            int b780 = find_closest_band(cube_wl, ret_nbands, 0.780f);
            G_message(_("Retrieving surface pressure (O₂-A) from bands "
                        "%.0f/%.0f/%.0f nm..."),
                      cube_wl[b740]*1000.0f, cube_wl[b760]*1000.0f,
                      cube_wl[b780]*1000.0f);

            float *L_740 = G_malloc(ret_npix * sizeof(float));
            float *L_760 = G_malloc(ret_npix * sizeof(float));
            float *L_780 = G_malloc(ret_npix * sizeof(float));
            int   depths_p[3]  = {b740, b760, b780};
            float *ptrs_p[3]   = {L_740, L_760, L_780};
            load_bands_from_cube(ret_map, depths_p, 3,
                                 ret_nrows, ret_ncols, ptrs_p);

            retrieved_pressure = G_malloc(ret_npix * sizeof(float));
            retrieve_pressure_o2a(L_740, L_760, L_780,
                                   ret_npix, sza, vza, retrieved_pressure);
            G_free(L_740); G_free(L_760); G_free(L_780);

            /* Update cfg with scene-mean pressure (use for LUT if DEM not set) */
            if (cfg.surface_pressure <= 0.0f) {
                double sp = 0.0; int np = 0;
                for (int i = 0; i < ret_npix; i++)
                    if (isfinite(retrieved_pressure[i]))
                        { sp += retrieved_pressure[i]; np++; }
                if (np > 0) {
                    cfg.surface_pressure = (float)(sp / np);
                    G_message(_("O₂-A surface pressure: %.1f hPa (scene mean)"),
                              cfg.surface_pressure);
                }
            }
        }

        /* ── Cloud / shadow / water / snow bitmask ── */
        if (flag_m->answer) {
            int b470  = find_closest_band(cube_wl, ret_nbands, 0.470f);
            int b660  = find_closest_band(cube_wl, ret_nbands, 0.660f);
            int b860  = find_closest_band(cube_wl, ret_nbands, 0.860f);
            int b1600 = find_closest_band(cube_wl, ret_nbands, 1.600f);
            G_message(_("Computing quality bitmask (cloud/shadow/water/snow)..."));

            float *L_blue = G_malloc(ret_npix * sizeof(float));
            float *L_red  = G_malloc(ret_npix * sizeof(float));
            float *L_nir  = G_malloc(ret_npix * sizeof(float));
            float *L_swir = NULL;
            /* Load SWIR only if it's within the input cube wavelength range */
            if (cube_wl[b1600] > 1.55f && cube_wl[b1600] < 1.65f)
                L_swir = G_malloc(ret_npix * sizeof(float));
            int   depths_m[4]  = {b470, b660, b860, b1600};
            float *ptrs_m[4]   = {L_blue, L_red, L_nir,
                                   L_swir ? L_swir : L_nir};  /* fallback */
            int    n_m = L_swir ? 4 : 3;
            load_bands_from_cube(ret_map, depths_m, n_m,
                                 ret_nrows, ret_ncols, ptrs_m);

            retrieved_quality = G_malloc(ret_npix * sizeof(uint8_t));
            retrieve_quality_mask(L_blue, L_red, L_nir, L_swir,
                                   ret_npix, doy, sza, retrieved_quality);
            G_free(L_blue); G_free(L_red); G_free(L_nir); G_free(L_swir);

            /* Report fractions */
            int nc = 0, ns = 0, nw = 0, nsn = 0;
            for (int i = 0; i < ret_npix; i++) {
                if (retrieved_quality[i] & RETRIEVE_MASK_CLOUD)  nc++;
                if (retrieved_quality[i] & RETRIEVE_MASK_SHADOW) ns++;
                if (retrieved_quality[i] & RETRIEVE_MASK_WATER)  nw++;
                if (retrieved_quality[i] & RETRIEVE_MASK_SNOW)   nsn++;
            }
            G_message(_("Quality mask: cloud=%.1f%% shadow=%.1f%% water=%.1f%% snow=%.1f%%"),
                      100.0f * nc  / ret_npix,
                      100.0f * ns  / ret_npix,
                      100.0f * nw  / ret_npix,
                      100.0f * nsn / ret_npix);
        }

        Rast3d_close(ret_map);
        G_free(cube_wl);
        G_free(cube_fwhm);
    }

    /* ── Surface pressure from DEM ── */
    if (opt_dem->answer) {
        struct Cell_head win2d;
        G_get_window(&win2d);
        int dem_nrows = win2d.rows, dem_ncols = win2d.cols;
        float *dem_data = load_raster2d(opt_dem->answer,
                                         dem_nrows, dem_ncols, 0.0f);
        double sum_elev = 0.0; int n_elev = 0;
        for (int i = 0; i < dem_nrows * dem_ncols; i++)
            if (isfinite(dem_data[i])) { sum_elev += dem_data[i]; n_elev++; }
        G_free(dem_data);
        if (n_elev > 0) {
            float mean_elev = (float)(sum_elev / n_elev);
            cfg.surface_pressure = retrieve_pressure_isa(mean_elev);
            G_message(_("Surface pressure from DEM: %.1f hPa (mean elev %.0f m)"),
                      cfg.surface_pressure, mean_elev);
        } else {
            G_warning(_("DEM <%s> has no valid pixels; using standard atmosphere"),
                      opt_dem->answer);
        }
    }

    size_t n          = (size_t)n_aod * n_h2o * n_wl;
    float *R_atm      = G_malloc(n * sizeof(float));
    float *T_down     = G_malloc(n * sizeof(float));
    float *T_up       = G_malloc(n * sizeof(float));
    float *s_alb      = G_malloc(n * sizeof(float));
    float *T_down_dir = do_terrain ? G_malloc(n * sizeof(float)) : NULL;

    for (size_t i = 0; i < n; i++) {
        R_atm[i] = 0.f; T_down[i] = 1.f; T_up[i] = 1.f; s_alb[i] = 0.f;
    }
    LutArrays lut = { R_atm, T_down, T_up, s_alb, T_down_dir, NULL, NULL };

    /* ── Compute LUT ── */
    G_verbose_message(_("Computing LUT: %d AOD × %d H2O × %d wavelengths "
                        "(SZA=%.1f° VZA=%.1f° RAA=%.1f°)..."),
                      n_aod, n_h2o, n_wl, sza, vza, raa);

    int ret = atcorr_compute_lut(&cfg, &lut);
    if (ret != 0)
        G_fatal_error(_("atcorr_compute_lut failed (code %d)"), ret);

    /* Print 550 nm summary */
    if (G_verbose() >= G_verbose_std()) {
        int i550 = 0;
        float best = 1e9f;
        for (int i = 0; i < n_wl; i++) {
            float d = fabsf(wl_buf[i] - 0.55f);
            if (d < best) { best = d; i550 = i; }
        }
        int    ia  = (n_aod > 2 ? 2 : 0), ih = n_h2o / 2;
        size_t idx = ((size_t)ia * n_h2o + ih) * n_wl + i550;
        G_message(_("At %.3f µm, AOD=%.2f, H2O=%.1f g/cm²:  "
                    "R_atm=%.4f  T_down=%.4f  T_up=%.4f  s_alb=%.4f"),
                  wl_buf[i550], aod_buf[ia], h2o_buf[ih],
                  R_atm[idx], T_down[idx], T_up[idx], s_alb[idx]);
    }

    /* ── Joint OE retrieval of per-pixel AOD + H₂O (requires LUT) ── *
     * Runs after atcorr_compute_lut; supersedes independent -a/-w retrievals
     * when -e is active.  Uses the pre-loaded cube bands for VIS spectral
     * smoothness and NIR H₂O constraints. */
    if (opt_input->answer && flag_e->answer) {
        const char *oe_mapset = G_find_raster3d(opt_input->answer, "");
        if (!oe_mapset)
            G_fatal_error(_("Cannot find input cube <%s> for OE"), opt_input->answer);

        RASTER3D_Region oe_reg; Rast3d_get_window(&oe_reg);
        RASTER3D_Map *oe_map = Rast3d_open_cell_old(
            opt_input->answer, oe_mapset, &oe_reg,
            RASTER3D_TILE_SAME_AS_FILE, RASTER3D_NO_CACHE);
        if (!oe_map)
            G_fatal_error(_("Cannot open input cube <%s> for OE"), opt_input->answer);
        Rast3d_get_region_struct_map(oe_map, &oe_reg);

        int oe_nrows  = oe_reg.rows;
        int oe_ncols  = oe_reg.cols;
        int oe_nbands = oe_reg.depths;
        int oe_npix   = oe_nrows * oe_ncols;

        float *oe_wl   = G_malloc(oe_nbands * sizeof(float));
        float *oe_fwhm = G_malloc(oe_nbands * sizeof(float));
        int    n_oe_parsed = parse_band_wl(opt_input->answer, oe_wl, oe_fwhm,
                                            oe_nbands);
        if (n_oe_parsed == 0)
            for (int b = 0; b < oe_nbands && b < n_wl; b++)
                oe_wl[b] = wl_buf[b];

        /* Select VIS diagnostic bands: 470, 550, 660, 870 nm */
        static const float VIS_TARGETS[] = {0.470f, 0.550f, 0.660f, 0.870f};
        static const int   N_VIS = 4;
        int   vis_bands[4];
        float vis_wl[4];
        for (int b = 0; b < N_VIS; b++) {
            vis_bands[b] = find_closest_band(oe_wl, oe_nbands, VIS_TARGETS[b]);
            vis_wl[b]    = VIS_TARGETS[b];
        }

        /* NIR bands for H₂O constraint */
        int b865  = find_closest_band(oe_wl, oe_nbands, 0.865f);
        int b940  = find_closest_band(oe_wl, oe_nbands, 0.940f);
        int b1040 = find_closest_band(oe_wl, oe_nbands, 1.040f);
        float fwhm_oe_940 = (n_oe_parsed > 0 && oe_fwhm[b940] > 0.0f)
                            ? oe_fwhm[b940] : 0.0f;
        G_free(oe_fwhm);

        G_message(_("OE retrieval: VIS bands %.0f/%.0f/%.0f/%.0f nm; "
                    "H2O bands %.0f/%.0f/%.0f nm..."),
                  oe_wl[vis_bands[0]]*1000.f, oe_wl[vis_bands[1]]*1000.f,
                  oe_wl[vis_bands[2]]*1000.f, oe_wl[vis_bands[3]]*1000.f,
                  oe_wl[b865]*1000.f, oe_wl[b940]*1000.f, oe_wl[b1040]*1000.f);

        /* Load bands into [npix × N_VIS] interleaved array */
        float *oe_vis_buf[4];
        for (int b = 0; b < N_VIS; b++)
            oe_vis_buf[b] = G_malloc(oe_npix * sizeof(float));
        load_bands_from_cube(oe_map, vis_bands, N_VIS,
                             oe_nrows, oe_ncols, oe_vis_buf);

        float *rho_toa_vis = G_malloc((size_t)oe_npix * N_VIS * sizeof(float));
        double d2_oe = sixs_earth_sun_dist2(doy);
        float  cos_sza_oe = cosf(sza * (float)(M_PI / 180.0));
        if (cos_sza_oe < 0.05f) cos_sza_oe = 0.05f;
        for (int b = 0; b < N_VIS; b++) {
            float E0_b = sixs_E0(vis_wl[b]);
            for (int i = 0; i < oe_npix; i++) {
                float L = oe_vis_buf[b][i];
                rho_toa_vis[i * N_VIS + b] =
                    isfinite(L) ? (float)(M_PI * L * d2_oe) / (E0_b * cos_sza_oe)
                                : NAN;
            }
            G_free(oe_vis_buf[b]);
        }

        /* Load H₂O bands */
        float *L_865  = G_malloc(oe_npix * sizeof(float));
        float *L_940  = G_malloc(oe_npix * sizeof(float));
        float *L_1040 = G_malloc(oe_npix * sizeof(float));
        int   depths_oe_h2o[3]  = {b865, b940, b1040};
        float *ptrs_oe_h2o[3]   = {L_865, L_940, L_1040};
        load_bands_from_cube(oe_map, depths_oe_h2o, 3,
                             oe_nrows, oe_ncols, ptrs_oe_h2o);

        /* Allocate OE output (override any previous DDV/940nm retrievals) */
        G_free(retrieved_aod); G_free(retrieved_h2o);
        retrieved_aod = G_malloc(oe_npix * sizeof(float));
        retrieved_h2o = G_malloc(oe_npix * sizeof(float));

        float sigma_aod_oe  = (float)atof(opt_oe_sigma_aod->answer);
        float sigma_h2o_oe  = (float)atof(opt_oe_sigma_h2o->answer);

        oe_invert_aod_h2o(&cfg, &lut,
                           rho_toa_vis, oe_npix, N_VIS, vis_wl,
                           L_865, L_940, L_1040,
                           sza, vza,
                           aod_val, h2o_val,
                           sigma_aod_oe, sigma_h2o_oe,
                           0.01f,  /* sigma_spec = 1% reflectance */
                           fwhm_oe_940,
                           retrieved_aod, retrieved_h2o);

        G_free(rho_toa_vis);
        G_free(L_865); G_free(L_940); G_free(L_1040);
        Rast3d_close(oe_map);
        G_free(oe_wl);

        /* Update scene-mean AOD/H₂O from OE results */
        double sa = 0.0, sh = 0.0; int ne = 0;
        for (int i = 0; i < oe_npix; i++) {
            if (isfinite(retrieved_aod[i]) && isfinite(retrieved_h2o[i])) {
                sa += retrieved_aod[i]; sh += retrieved_h2o[i]; ne++;
            }
        }
        if (ne > 0) {
            aod_val = (float)(sa / ne);
            h2o_val = (float)(sh / ne);
            G_message(_("OE retrieval complete: AOD=%.3f H₂O=%.2f g/cm² (scene means)"),
                      aod_val, h2o_val);
        }
    }

    /* ── Write LUT file ── */
    if (opt_lut->answer) {
        FILE *fp = fopen(opt_lut->answer, "wb");
        if (!fp)
            G_fatal_error(_("Cannot open '%s': %s"),
                          opt_lut->answer, strerror(errno));
        write_u32(fp, LUT_MAGIC);  write_u32(fp, LUT_VERSION);
        write_i32(fp, n_aod);      write_i32(fp, n_h2o);  write_i32(fp, n_wl);
        write_f32a(fp, aod_buf, n_aod);
        write_f32a(fp, h2o_buf, n_h2o);
        write_f32a(fp, wl_buf,  n_wl);
        write_f32a(fp, R_atm,  n);
        write_f32a(fp, T_down, n);
        write_f32a(fp, T_up,   n);
        write_f32a(fp, s_alb,  n);
        if (fclose(fp) != 0)
            G_fatal_error(_("Error closing '%s'"), opt_lut->answer);
        G_message(_("LUT written to '%s' (%zu KB)"),
                  opt_lut->answer, (n * 4 * 4 + 256) / 1024);
    }

    /* ── Atmospheric correction ── */
    if (opt_input->answer) {
        /* Log enabled improvements */
        if (opt_aod_map->answer || opt_h2o_map->answer) {
            G_message(_("Per-pixel atmospheric maps enabled:"));
            if (opt_aod_map->answer)
                G_message(_("  AOD map: <%s>"), opt_aod_map->answer);
            if (opt_h2o_map->answer)
                G_message(_("  H2O map: <%s>"), opt_h2o_map->answer);
            float s = (float)atof(opt_smooth->answer);
            if (s > 0.0f) G_message(_("  Gaussian smooth σ=%.1f px"), s);
        }
        float adj = (float)atof(opt_adj_psf->answer);
        if (adj > 0.0f)
            G_message(_("Adjacency correction: PSF=%.2f km"), adj);
        if (do_terrain)
            G_message(_("Terrain illumination correction: ENABLED "
                        "(sun_azimuth=%.1f°)"), sun_azimuth);
        if (do_nbar)
            G_message(_("NBAR normalization: ENABLED (Ross-Li MCD43 kernels)"));
        if (have_flex_brdf)
            G_message(_("FlexBRDF: ENABLED (MCD43 spectral disaggregation)"));
        if (flag_r->answer)
            G_message(_("Surface prior MAP regularisation: ENABLED"));
        if (flag_u->answer)
            G_message(_("Reflectance uncertainty: ENABLED"));
        if (flag_D->answer && opt_dasf->answer)
            G_message(_("DASF retrieval: ENABLED → <%s>"), opt_dasf->answer);

        IsoFitParams iso = {
            .aod_map        = opt_aod_map->answer,
            .h2o_map        = opt_h2o_map->answer,
            .aod_data       = retrieved_aod,   /* pre-retrieved per-pixel AOD */
            .h2o_data       = retrieved_h2o,   /* pre-retrieved per-pixel H2O */
            .smooth_sigma   = (float)atof(opt_smooth->answer),
            .adj_psf_km     = adj,
            .pixel_size_m   = (float)atof(opt_pixel_size->answer),
            .do_surface_prior = flag_r->answer ? 1 : 0,
            .do_uncertainty = flag_u->answer ? 1 : 0,
            .unc_output     = (flag_u->answer && opt_uncertainty->answer)
                              ? opt_uncertainty->answer : NULL,
            .slope_map      = opt_slope->answer,
            .aspect_map     = opt_aspect->answer,
            .sun_azimuth    = sun_azimuth,
            .vza_map        = opt_vza_map->answer,
            .vaa_map        = opt_vaa_map->answer,
            .brdf_fiso_map  = do_nbar ? opt_fiso->answer : NULL,
            .brdf_fvol_map  = do_nbar ? opt_fvol->answer : NULL,
            .brdf_fgeo_map  = do_nbar ? opt_fgeo->answer : NULL,
            .pressure_data  = retrieved_pressure,
            .quality_data   = retrieved_quality,
            /* FlexBRDF spectral kernel weights */
            .flex_fiso_wl   = flex_fiso_wl,
            .flex_fvol_wl   = flex_fvol_wl,
            .flex_fgeo_wl   = flex_fgeo_wl,
            .flex_fiso_ref  = flex_fiso_ref,
            .flex_fvol_ref  = flex_fvol_ref,
            .flex_fgeo_ref  = flex_fgeo_ref,
            .have_flex_brdf = have_flex_brdf,
            /* DASF retrieval */
            .dasf_output    = (flag_D->answer && opt_dasf->answer)
                              ? opt_dasf->answer : NULL,
            .do_dasf        = (flag_D->answer && opt_dasf->answer) ? 1 : 0,
        };

        if (flag_p->answer && retrieved_pressure)
            G_message(_("Per-pixel O₂-A pressure correction: ENABLED"));
        if (flag_m->answer && retrieved_quality)
            G_message(_("Pre-correction quality bitmask: ENABLED"));

        correct_raster3d(opt_input->answer, opt_output->answer,
                         &cfg, &lut, aod_val, h2o_val, doy, sza, &iso);

        /* ── Derive output metadata (i.hyper.metadata operation=derive) ── */
        {
            char overrides[2048];
            snprintf(overrides, sizeof(overrides),
                     "{"
                     "\"radiometric_quantity\":\"surface_reflectance\","
                     "\"radiometric_units\":\"unitless\","
                     "\"extended_metadata\":{"
                     "\"radiometry\":{"
                     "\"quantity\":\"surface_reflectance\","
                     "\"units\":\"unitless\""
                     "},"
                     "\"processing\":{"
                     "\"atcorr\":{"
                     "\"source_radiance_map\":\"%s\","
                     "\"output_type\":\"boa_surface_reflectance\","
                     "\"output_units\":\"unitless\","
                     "\"output_valid_range\":\"unclipped\","
                     "\"geometry_used\":{"
                     "\"sza\":%.2f,\"vza\":%.2f,"
                     "\"raa\":%.2f,\"sun_azimuth\":%.2f,"
                     "\"altitude_km\":%.1f"
                     "},"
                     "\"atmosphere_used\":{"
                     "\"aod_550\":%.4f,\"h2o_g_cm2\":%.2f,"
                     "\"ozone_du\":%.1f,\"doy\":%d,"
                     "\"atmosphere_model\":\"%s\","
                     "\"aerosol_model\":\"%s\""
                     "},"
                     "\"spectral_response\":{"
                     "\"type\":\"gaussian\","
                     "\"source\":\"band_center_and_fwhm\""
                     "}"
                     "}"
                     "}"
                     "}"
                     "}",
                     opt_input->answer,
                     sza, vza, raa, sun_azimuth, altitude,
                     aod_val, h2o_val, ozone, doy,
                     atmo_str, aero_str);

            char maparg[GPATH_MAX], srcarg[GPATH_MAX], ovrarg[4096];
            snprintf(maparg, sizeof(maparg), "map=%s", opt_output->answer);
            snprintf(srcarg, sizeof(srcarg), "source_map=%s", opt_input->answer);
            snprintf(ovrarg, sizeof(ovrarg), "overrides=%s", overrides);

            const char *dargs[7];
            dargs[0] = "i.hyper.metadata";
            dargs[1] = maparg;
            dargs[2] = "operation=derive";
            dargs[3] = srcarg;
            dargs[4] = "command=i.hyper.atcorr";
            dargs[5] = ovrarg;
            dargs[6] = NULL;

            if (G_vspawn_ex("i.hyper.metadata", dargs) != 0)
                G_warning(_("Failed to derive output metadata for <%s>"),
                          opt_output->answer);
        }

        /* ── Write quality bitmask as 2-D GRASS raster ── */
        if (flag_m->answer && retrieved_quality && opt_quality->answer) {
            G_message(_("Writing quality bitmask to <%s>..."), opt_quality->answer);

            struct Cell_head win_q;
            G_get_window(&win_q);
            int q_nrows = win_q.rows, q_ncols = win_q.cols;

            int fd_q = Rast_open_new(opt_quality->answer, CELL_TYPE);
            CELL *q_row = Rast_allocate_c_buf();
            for (int r = 0; r < q_nrows; r++) {
                for (int c = 0; c < q_ncols; c++) {
                    int idx = r * q_ncols + c;
                    if (idx < q_nrows * q_ncols)
                        q_row[c] = (CELL)retrieved_quality[idx];
                    else
                        Rast_set_c_null_value(&q_row[c], 1);
                }
                Rast_put_c_row(fd_q, q_row);
            }
            G_free(q_row);
            Rast_close(fd_q);
            G_message(_("Quality bitmask written to <%s> "
                        "(bit 0=cloud, 1=shadow, 2=water, 3=snow)"),
                      opt_quality->answer);
        }
    }

    G_free(retrieved_aod);
    G_free(retrieved_h2o);
    G_free(retrieved_pressure);
    G_free(retrieved_quality);
    G_free(flex_fiso_wl); G_free(flex_fvol_wl); G_free(flex_fgeo_wl);
    G_free(wl_buf);
    G_free(R_atm); G_free(T_down); G_free(T_up); G_free(s_alb);
    G_free(T_down_dir);

    exit(EXIT_SUCCESS);
}
