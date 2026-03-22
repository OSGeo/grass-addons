# Extended Metadata Unification (EnMAP / PRISMA / Tanager)

## Scope
This document is the implementation spec for `hyper.json` `extended_metadata` unification.

Reference basis:
- EnMAP, PRISMA, and Tanager product metadata schemas
- Product specification documentation for PRISMA and Tanager

## Unification Rules
- Use common keys for the same physical quantity under:
  - `extended_metadata.acquisition`
  - `extended_metadata.geometry`
  - `extended_metadata.radiometry`
  - `extended_metadata.atmosphere`
  - `extended_metadata.quality`
  - `extended_metadata.processing`
  - `extended_metadata.uncertainty`
- Keep product-native values under namespaces when needed for provenance:
  - `extended_metadata.enmap.*`
  - `extended_metadata.prisma.*`
  - `extended_metadata.tanager.*`
- For map-vs-scalar quantities, store value + form metadata (`scalar`, `map_mean`, `map_name`).

## A. i.hyper.atcorr Unified Keys

| Unified key | EnMAP | PRISMA | Tanager | Product availability | Notes |
|---|---|---|---|---|---|
| `acquisition.start_time_utc` | `specific/datatakeStart` | `Product_StartTime` | `min(Time/time)` | all products | ISO-8601 UTC |
| `acquisition.end_time_utc` | `base/temporalCoverage/stopTime` | `Product_StopTime` | `max(Time/time)` | all products | supplementary |
| `acquisition.center_latitude_deg` | center point latitude | `Product_center_lat` | mean/center latitude map | all products | decimal degrees |
| `acquisition.center_longitude_deg` | center point longitude | `Product_center_long` | mean/center longitude map | all products | decimal degrees |
| `acquisition.day_of_year` | derived | derived | derived | all products | integer 1..366 |
| `geometry.sun_zenith_deg` | `90 - sunElevationAngle/center` | `Sun_zenith_angle` or map mean | map mean `sun_zenith` | all products | core |
| `geometry.sun_azimuth_deg` | `sunAzimuthAngle/center` | `Sun_azimuth_angle` | map mean `sun_azimuth` | all products | core |
| `geometry.view_zenith_deg` | `sqrt(acrossOffNadir^2+alongOffNadir^2)` | map mean `.../Observing_Angle` | map mean `sensor_zenith` | all products | core |
| `geometry.view_azimuth_deg` | `sceneAzimuthAngle/center` | nullable/derived | map mean `sensor_azimuth` | multiple products | supplementary |
| `geometry.relative_azimuth_deg` | derived from SAA/VAA | map mean `.../Rel_Azimuth_Angle` | derived from SAA/VAA | all products | supplementary |
| `geometry.sensor_altitude_m` | `base/altitudeCoverage` (interpretation-dependent) | not found | not found | single product | nullable where unavailable |
| `radiometry.quantity` | L2A reflectance | L2D reflectance | TOA radiance or SR | all products | core |
| `radiometry.units` | derived (dimensionless for SR) | derived (dimensionless for SR) | dataset `Unit` | all products | core |
| `radiometry.scale` | `GainOfBand` | `L2Scale*`-derived | none in float products | two products | supplementary |
| `radiometry.offset` | `OffsetOfBand` | `L2Scale*Min` | none in float products | two products | supplementary |
| `radiometry.wavelengths_nm` | `wavelengthCenterOfBand` | `List_Cw_*` | dataset attr `wavelengths` | all products | core for spectral processing |
| `radiometry.fwhm_nm` | `FWHMOfBand` | `List_Fwhm_*` | dataset attr `fwhm` | all products | recommended |
| `atmosphere.aod_550` | not found | not found in L2D | `aerosol_optical_depth` map | single product | map-derived value (form tag mandatory) |
| `atmosphere.h2o_g_cm2` | not found | not found in L2D | `column_water_vapour` map | single product | map-derived value (form tag mandatory) |
| `atmosphere.ozone_du` | `processing/ozoneValue` | not found | not found | single product | keep nullable |
| `atmosphere.surface_pressure_hpa` | not found | not found | not found | not available in current products | schema-reserved key |
| `atmosphere.atmosphere_model` | not found | `Atmo_profile_info` | not found | single product | keep nullable |
| `atmosphere.aerosol_model` | not found | not found | not found | not available in current products | schema-reserved key |

## B. Additional Unified Keys Present In >=2 Products

| Unified key | EnMAP | PRISMA | Tanager | Product availability | Notes |
|---|---|---|---|---|---|
| `quality.cloudy_pixels_percent` | `qualityFlag/cloudCover` | `Cloudy_pixels_percentage` | not found | two products | unified cloud fraction metric |
| `quality.quality_atmosphere_flag` | `qualityFlag/qualityAtmosphere` | `L2d_Quality_flags` | not found | two products | semantics differ by product |
| `uncertainty.reflectance_uncertainty_present` | not found | `*_PIXEL_L2_ERR_MATRIX` datasets | `surface_reflectance_uncertainty` | two products | boolean capability flag |
| `processing.processing_datetime_utc` | `specific/processingDateTime` | `Processing_Time` | `created_at` | all products | provenance |

## C. Product-Specific Keys Kept For Provenance
Keep only keys that support derivation/provenance for A+B. Avoid dumping full engineering trees.

### `extended_metadata.enmap`
- `processing.cirrusHazeRemoval` (source for unified `processing.cirrus_haze_removal`)
- `processing.waterType` (source for unified `quality.water_type`)
- supporting quality fields used in derivations (`cloudCover`, etc.)

### `extended_metadata.prisma`
- `Atm_LutGeomInfo_RelativeAzimuth`
- `Atm_LutGeomInfo_SunZenith`
- `Atm_LutGeomInfo_ViewZenith`
- `Atmo_profile_info`
- `Atm_Lut_version`
- `Processor_Name`, `Processor_Version`, `Processing_Time`
- `Sun_azimuth_angle`, `Sun_zenith_angle`
- `Product_StartTime`, `Product_StopTime`, `Product_center_lat`, `Product_center_long`
- `Cloudy_pixels_percentage`, `L2d_Quality_flags`

### `extended_metadata.tanager`
- map names/refs for: `sun_zenith`, `sun_azimuth`, `sensor_zenith`, `sensor_azimuth`
- map names/refs for: `aerosol_optical_depth`, `column_water_vapour`
- map names/refs for: `surface_reflectance_uncertainty`
- quality masks present flags: `beta_cloud_mask`, `beta_cirrus_mask`, `nodata_pixels`
- provenance attrs: `created_at`, `strip_id`, `epsg_code`

## D. Recommended `hyper.json` Representation Notes
- Geometry keys are scalar scene summaries in degrees.
- Atmospheric keys that come from maps should include:
  - `<key>.value`
  - `<key>.form` in `{scalar,map_mean,map_name}`
  - `<key>.source` (product-native key/dataset)
- `radiometry.scale` / `radiometry.offset` may be scalar or per-band arrays.
- Keep all timestamps in ISO-8601 UTC.

## E. Explicitly Out Of Scope For This Spec
- Full raw metadata inventories (all XML/HDF paths and all engineering telemetry keys).
- Internal discovery-only path templates such as `level_X/...`.

Those can be maintained in a separate technical appendix if needed, but should not drive the operational `hyper.json` schema.

## F. Atmospheric-Correction Metadata Mapping

This section defines unified keys for atmospheric-correction metadata.

### F1. Keys Available from Input Metadata

| Concept | Unified key | Product availability | Source examples |
|---|---|---|---|
| Acquisition time | `acquisition.start_time_utc` | all products | EnMAP `datatakeStart`, PRISMA `Product_StartTime`, Tanager `Time/time` |
| Scene center lat/lon | `acquisition.center_latitude_deg`, `acquisition.center_longitude_deg` | all products | EnMAP spatial center, PRISMA `Product_center_*`, Tanager lat/lon maps |
| Day of year | `acquisition.day_of_year` | all products (derived) | derived from acquisition time |
| Sun zenith / azimuth | `geometry.sun_zenith_deg`, `geometry.sun_azimuth_deg` | all products | product geometry fields/maps |
| View zenith / azimuth | `geometry.view_zenith_deg`, `geometry.view_azimuth_deg` | all products (azimuth may be derived) | EnMAP scene angle, PRISMA geometric maps, Tanager sensor maps |
| Relative azimuth | `geometry.relative_azimuth_deg` | all products (derived or map) | PRISMA `Rel_Azimuth_Angle` map or derived |
| Sensor altitude | `geometry.sensor_altitude_m` | single product | EnMAP `base/altitudeCoverage` (interpretation-dependent) |
| Radiance units | `radiometry.units` | single product explicit | explicit in Tanager `Unit`; reflectance products are unitless |
| Radiance scale | `radiometry.scale` | two products | EnMAP `GainOfBand`, PRISMA `L2Scale*` |
| Radiance offset | `radiometry.offset` | two products | EnMAP `OffsetOfBand`, PRISMA `L2Scale*Min` |
| AOD | `atmosphere.aod_550` | single product | Tanager `aerosol_optical_depth` map (550 proxy) |
| Column H2O | `atmosphere.h2o_g_cm2` | single product | Tanager `column_water_vapour` map |
| Ozone | `atmosphere.ozone_du` | single product | EnMAP `processing/ozoneValue` |
| Atmosphere model | `atmosphere.atmosphere_model` | single product | PRISMA `Atmo_profile_info` |
| Processing datetime | `processing.processing_datetime_utc` | all products | EnMAP `processingDateTime`, PRISMA `Processing_Time`, Tanager `created_at` |
| Software/version | `processing.software` | single product | PRISMA `Processor_Name` + `Processor_Version` |
| LUT version | `processing.lut_version` | single product | PRISMA `Atm_Lut_version` |
| cirrusHazeRemoval | `processing.cirrus_haze_removal` | single product | EnMAP `processing/cirrusHazeRemoval` |
| Reflectance uncertainty present | `uncertainty.reflectance_uncertainty_present` | two products | PRISMA `*_PIXEL_L2_ERR_MATRIX`, Tanager `surface_reflectance_uncertainty` |

### F2. Keys Defined for i.hyper.atcorr Output Metadata

These keys are written by `i.hyper.atcorr` to record correction configuration, runtime flags, and produced outputs.

| Concept | Recommended unified key |
|---|---|
| Source radiance map | `processing.atcorr.source_radiance_map` |
| LUT file/path | `processing.atcorr.lut_file` |
| Physical output type (BOA / TOA / NBAR) | `processing.atcorr.output_type` |
| Output units | `processing.atcorr.output_units` |
| Output valid range | `processing.atcorr.output_valid_range` |
| BRDF normalization mode | `processing.atcorr.brdf_normalization` |
| 6SV used: sun/view/relative azimuth, DOY, sensor altitude | `processing.atcorr.geometry_used.*` |
| 6SV used: atmosphere/aerosol model, AOD/H2O/O3/pressure | `processing.atcorr.atmosphere_used.*` |
| AOD retrieval flag/method | `processing.atcorr.flags.aod_retrieval` |
| H2O retrieval flag/method | `processing.atcorr.flags.h2o_retrieval` |
| O3 retrieval flag/method | `processing.atcorr.flags.o3_retrieval` |
| Pressure retrieval flag/method | `processing.atcorr.flags.pressure_retrieval` |
| Quality mask flag | `processing.atcorr.flags.quality_mask` |
| OE retrieval flag | `processing.atcorr.flags.oe_retrieval` |
| MAP regularisation flag | `processing.atcorr.flags.map_regularisation` |
| Adjacency correction config | `processing.atcorr.flags.adjacency_correction` |
| Spatial smoothing sigma/config | `processing.atcorr.flags.spatial_smoothing` |
| Vector RT (Stokes/scalar) | `processing.atcorr.flags.vector_rt` |
| SRF gas correction mode | `processing.atcorr.flags.srf_gas_correction` |
| FlexBRDF mode | `processing.atcorr.flags.flexbrdf` |
| Gas-masked bands | `quality.gas_masked_bands` |
| Masked pixel count | `quality.masked_pixel_count` |
| DASF output map | `quality.dasf_output_map` |
| Uncertainty output data type/units/model/source map | `uncertainty.output.*` |

### F3. Form requirements for scalar vs map atmospheric values

For `atmosphere.aod_550` and `atmosphere.h2o_g_cm2`, include:
- `value`
- `form` in `{scalar,map_mean,map_name}`
- `source` (native key/dataset name)

This allows downstream tools to distinguish scene-uniform assumptions from spatially varying corrections.
