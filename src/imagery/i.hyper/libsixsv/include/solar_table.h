/* Auto-generated from 6SV2.1 SOLIRR.f */
#pragma once
/* Solar irradiance table: 1501 points from 0.25 to 4.0 µm at 0.0025 µm step.
 * Units: W/m²/µm  (same as Kurucz). Interpolation: nearest integer index. */
#define SOLAR_TABLE_N 1501
#define SOLAR_TABLE_WL_START 0.250  /* µm */
#define SOLAR_TABLE_STEP    0.0025  /* µm */
extern const float solar_si[1501];
