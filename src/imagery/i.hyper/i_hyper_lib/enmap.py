#!/usr/bin/env python3
import sys
import os
import xml.etree.ElementTree as ET
import math
import shlex
import tempfile
import subprocess
import shutil
from datetime import datetime, timezone
import rasterio
import grass.script as gs
from grass.pygrass.modules import Module
import contextlib
from statistics import mean

from hyper_meta import HyperMetadata

COMPOSITES = {
    "rgb": [660, 572, 478],
    "cir": [848, 660, 572],
    "swir_agriculture": [848, 1653, 660],
    "swir_geology": [2200, 848, 572],
}


def _to_float(value):
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _first_nonempty_text(root, paths):
    for path in paths:
        text = root.findtext(path)
        if text is None:
            continue
        text = text.strip()
        if text:
            return text
    return None


def _first_float(root, paths):
    return _to_float(_first_nonempty_text(root, paths))


def _enmap_sun_zenith(root):
    """Return solar zenith angle in degrees from EnMAP XML variants."""
    sun_zenith = _first_float(
        root,
        [
            ".//illuminationZenithAngle/center",
            ".//illuminationZenithAngle",
            ".//sunZenithAngle/center",
            ".//sunZenithAngle",
        ],
    )
    if sun_zenith is not None:
        return sun_zenith

    sun_elevation = _first_float(
        root,
        [
            ".//sunElevationAngle/center",
            ".//sunElevationAngle",
        ],
    )
    return 90.0 - sun_elevation if sun_elevation is not None else None


def _enmap_sun_azimuth(root):
    """Return solar azimuth angle in degrees from EnMAP XML variants."""
    return _first_float(
        root,
        [
            ".//sunAzimuthAngle/center",
            ".//sunAzimuthAngle",
            ".//illuminationAzimuthAngle/center",
            ".//illuminationAzimuthAngle",
        ],
    )


def _to_int(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_iso_utc(text):
    if text is None:
        return None
    value = str(text).strip()
    if not value:
        return None
    if value.endswith("Z"):
        return value
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _day_of_year(iso_text):
    if not iso_text:
        return None
    text = str(iso_text).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timetuple().tm_yday)


def _relative_azimuth(sun_azimuth, view_azimuth):
    if sun_azimuth is None or view_azimuth is None:
        return None
    diff = abs((float(view_azimuth) - float(sun_azimuth) + 180.0) % 360.0 - 180.0)
    return diff


def _to_int_list(text):
    if text is None:
        return []
    out = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        try:
            out.append(int(item))
        except ValueError:
            continue
    return out


def _enmap_center_latlon(root):
    point_paths = [
        ".//specific/spatialCoverageOfOrthoScene/boundingPolygon/point",
        ".//base/spatialCoverage/boundingPolygon/point",
        ".//specific/spatialCoverageOfDatatake/boundingPolygon/point",
    ]
    for ppath in point_paths:
        points = root.findall(ppath)
        coords = []
        for point in points:
            lat = _to_float(point.findtext("latitude"))
            lon = _to_float(point.findtext("longitude"))
            if lat is not None and lon is not None:
                coords.append((lat, lon))
        if not coords:
            continue
        # Prefer first four polygon corners; this avoids closure and auxiliary points.
        sample = coords[:4] if len(coords) >= 4 else coords
        lats = [c[0] for c in sample]
        lons = [c[1] for c in sample]
        return mean(lats), mean(lons)
    return None, None


def _enmap_line_time_summary(root):
    vals = []
    for node in root.findall(".//product/time//frameTime"):
        iso = _to_iso_utc(node.text)
        if not iso:
            continue
        txt = iso[:-1] + "+00:00" if iso.endswith("Z") else iso
        try:
            vals.append(datetime.fromisoformat(txt).astimezone(timezone.utc))
        except ValueError:
            continue
    if not vals:
        return None
    vals.sort()
    steps = []
    for a, b in zip(vals, vals[1:]):
        delta = (b - a).total_seconds()
        if delta >= 0:
            steps.append(delta)
    return {
        "count": len(vals),
        "min": vals[0].isoformat().replace("+00:00", "Z"),
        "max": vals[-1].isoformat().replace("+00:00", "Z"),
        "step_seconds": (sum(steps) / len(steps)) if steps else None,
    }


def _enmap_jitter_summary(root):
    vals = []
    for node in root.findall(".//product/time//jitter"):
        val = _to_float(node.text)
        if val is not None:
            vals.append(val)
    if not vals:
        return None
    return {
        "count": len(vals),
        "min": min(vals),
        "max": max(vals),
        "mean": sum(vals) / float(len(vals)),
    }


@contextlib.contextmanager
def suppress_stderr():
    fd, old = sys.stderr.fileno(), os.dup(sys.stderr.fileno())
    with open(os.devnull, "w") as null:
        os.dup2(null.fileno(), fd)
    try:
        yield
    finally:
        os.dup2(old, fd)
        os.close(old)


def _enmap_product_level(root):
    text = _first_nonempty_text(
        root, [".//processingLevel", ".//base/level", ".//level"]
    )
    if text is None:
        return None
    return str(text).strip().upper()


def _enmap_radiometry_from_metadata(root, level):
    """Return the physical quantity declared by the EnMAP product XML."""
    level = str(level or "").upper()
    format_paths = {
        "L1B": [
            ".//product/image/vnir/format",
            ".//product/image/swir/format",
        ],
        "L1C": [".//product/image/merge/format"],
        "L2A": [".//product/image/merge/format"],
    }
    declared_formats = [root.findtext(path) for path in format_paths.get(level, [])]
    formats = [text.strip().lower() for text in declared_formats if text and text.strip()]

    quantities = []
    for text in formats:
        if "radiance" in text:
            quantities.append(("toa_radiance", "W/m^2/sr/nm"))
        elif "reflectance" in text:
            quantities.append(("surface_reflectance", "unitless"))

    if formats and len(formats) != len(declared_formats):
        raise ValueError("EnMAP metadata has incomplete radiometric format declarations.")
    if formats and len(quantities) != len(formats):
        raise ValueError("EnMAP metadata has an unrecognized radiometric format.")

    if quantities:
        if any(quantity != quantities[0] for quantity in quantities[1:]):
            raise ValueError("EnMAP metadata contains inconsistent radiometric formats.")
        quantity, units = quantities[0]
    else:
        # Older metadata may omit the product image format. Keep a safe,
        # explicit fallback while making the missing declaration visible.
        fallback = {
            "L1B": ("toa_radiance", "W/m^2/sr/nm"),
            "L1C": ("toa_radiance", "W/m^2/sr/nm"),
            "L2A": ("surface_reflectance", "unitless"),
        }
        if level not in fallback:
            raise ValueError(
                "Cannot determine EnMAP radiometry: unsupported or missing processing level."
            )
        gs.warning(
            "EnMAP radiometric format is missing from metadata; using the processing-level fallback."
        )
        quantity, units = fallback[level]

    expected = {
        "L1B": "toa_radiance",
        "L1C": "toa_radiance",
        "L2A": "surface_reflectance",
    }
    if level in expected and quantity != expected[level]:
        raise ValueError(
            f"EnMAP metadata conflicts with processing level {level}: "
            f"declares {quantity}."
        )
    return quantity, units


def parse_band_metadata(meta_xml_path, spectral_sources):
    tree = ET.parse(meta_xml_path)
    root = tree.getroot()
    band_data = {}

    for band in root.findall(".//bandCharacterisation/bandID"):
        idx = int(band.attrib["number"])
        wl = band.findtext("wavelengthCenterOfBand")
        fwhm = band.findtext("FWHMOfBand")
        gain = band.findtext("GainOfBand")
        off = band.findtext("OffsetOfBand")
        band_data[idx] = {
            "wavelength": float(wl) if wl is not None else None,
            "fwhm": float(fwhm) if fwhm is not None else None,
            "gain": float(gain) if gain is not None else None,
            "offset": float(off) if off is not None else 0.0,
            "valid": 0,
        }

    expected_vnir = _to_int_list(
        root.findtext(".//vnirProductQuality/expectedChannelsList")
    )
    expected_swir = _to_int_list(
        root.findtext(".//swirProductQuality/expectedChannelsList")
    )
    expected = set(expected_vnir) | set(expected_swir)

    band_entries = []
    for source in spectral_sources:
        tif_path = source["path"]
        source_type = source.get("type", "single")
        with rasterio.open(tif_path) as src:
            if source_type == "vnir":
                global_ids = expected_vnir
            elif source_type == "swir":
                global_ids = expected_swir
            else:
                global_ids = list(range(1, src.count + 1))

            if source_type in ("vnir", "swir") and len(global_ids) != src.count:
                gs.fatal(
                    "EnMAP L1B metadata mismatch: expectedChannelsList length does not match detector band count."
                )
            if source_type in ("vnir", "swir"):
                declared_channels = _to_int(
                    root.findtext(f".//product/image/{source_type}/channels")
                )
                if declared_channels is not None and declared_channels != src.count:
                    gs.fatal(
                        f"EnMAP {source_type.upper()} metadata mismatch: "
                        f"declares {declared_channels} bands but the image contains {src.count}."
                    )
            elif source_type == "single":
                declared_channels = _to_int(
                    root.findtext(".//product/image/merge/channels")
                )
                if declared_channels is not None and declared_channels != src.count:
                    gs.fatal(
                        "EnMAP merged-image metadata mismatch: "
                        f"declares {declared_channels} bands but the image contains {src.count}."
                    )

            for local_band in range(1, src.count + 1):
                global_band = global_ids[local_band - 1]
                valid = (
                    1
                    if (
                        source_type != "single"
                        or not expected
                        or global_band in expected
                    )
                    else 0
                )
                sv = src.tags(local_band).get("STATISTICS_VALID_PERCENT")
                if sv is not None:
                    try:
                        if float(sv) <= 0:
                            valid = 0
                    except Exception:
                        pass

                band_data.setdefault(
                    global_band,
                    {"wavelength": None, "fwhm": None, "gain": None, "offset": 0.0},
                )
                band_data[global_band]["valid"] = valid
                band_entries.append(
                    {
                        "global_band": global_band,
                        "source_path": tif_path,
                        "source_band": local_band,
                    }
                )

    band_entries.sort(key=lambda item: item["global_band"])
    seen_global = set()
    for entry in band_entries:
        gid = entry["global_band"]
        if gid in seen_global:
            gs.fatal(f"EnMAP band mapping produced duplicate global band id: {gid}")
        seen_global.add(gid)

    for b in band_data:
        if band_data[b]["gain"] is None:
            band_data[b]["gain"] = 0.0001
        if band_data[b]["offset"] is None:
            band_data[b]["offset"] = 0.0

    return band_data, band_entries


def parse_dataset_metadata(meta_xml_path):
    """Read dataset-level acquisition and geometry metadata from EnMAP XML."""
    tree = ET.parse(meta_xml_path)
    root = tree.getroot()

    product_level = _enmap_product_level(root)
    radiometric_quantity, radiometric_units = _enmap_radiometry_from_metadata(
        root, product_level
    )

    acquisition_datetime = _to_iso_utc(
        _first_nonempty_text(
            root,
            [
                ".//datatakeStart",
                ".//temporalCoverage/startTime",
                ".//startTime",
            ],
        )
    )

    solar_zenith_angle = _enmap_sun_zenith(root)
    solar_azimuth_angle = _enmap_sun_azimuth(root)

    satellite_azimuth_angle = _first_float(
        root,
        [
            ".//sceneAzimuthAngle/center",
            ".//sceneAzimuthAngle",
            ".//satelliteAzimuthAngle/center",
            ".//satelliteAzimuthAngle",
            ".//viewAzimuthAngle/center",
            ".//viewAzimuthAngle",
        ],
    )

    satellite_zenith_angle = _first_float(
        root,
        [
            ".//satelliteZenithAngle/center",
            ".//satelliteZenithAngle",
            ".//viewZenithAngle/center",
            ".//viewZenithAngle",
            ".//offNadirAngle/center",
            ".//offNadirAngle",
        ],
    )
    if satellite_zenith_angle is None:
        across = _first_float(
            root,
            [
                ".//acrossOffNadirAngle/center",
                ".//acrossOffNadirAngle",
            ],
        )
        along = _first_float(
            root,
            [
                ".//alongOffNadirAngle/center",
                ".//alongOffNadirAngle",
            ],
        )
        if across is not None and along is not None:
            satellite_zenith_angle = math.hypot(across, along)
        elif across is not None:
            satellite_zenith_angle = abs(across)
        elif along is not None:
            satellite_zenith_angle = abs(along)

    return {
        "acquisition_datetime": acquisition_datetime,
        "solar_zenith_angle": solar_zenith_angle,
        "solar_azimuth_angle": solar_azimuth_angle,
        "satellite_zenith_angle": satellite_zenith_angle,
        "satellite_azimuth_angle": satellite_azimuth_angle,
        "product_level": product_level,
        "radiometric_quantity": radiometric_quantity,
        "radiometric_units": radiometric_units,
    }


def _populate_enmap_extended_metadata(
    meta,
    meta_xml_path,
    band_meta,
    band_indices,
    validity_mask,
):
    tree = ET.parse(meta_xml_path)
    root = tree.getroot()

    start_time = _to_iso_utc(
        _first_nonempty_text(
            root,
            [
                ".//specific/datatakeStart",
                ".//datatakeStart",
                ".//base/temporalCoverage/startTime",
                ".//temporalCoverage/startTime",
                ".//startTime",
            ],
        )
    )
    end_time = _to_iso_utc(
        _first_nonempty_text(
            root,
            [
                ".//specific/datatakeStop",
                ".//datatakeStop",
                ".//base/temporalCoverage/stopTime",
                ".//temporalCoverage/stopTime",
                ".//stopTime",
            ],
        )
    )

    center_lat, center_lon = _enmap_center_latlon(root)

    sun_zenith = _enmap_sun_zenith(root)
    sun_azimuth = _enmap_sun_azimuth(root)

    view_azimuth = _first_float(
        root,
        [
            ".//sceneAzimuthAngle/center",
            ".//sceneAzimuthAngle",
            ".//satelliteAzimuthAngle/center",
            ".//satelliteAzimuthAngle",
            ".//viewAzimuthAngle/center",
            ".//viewAzimuthAngle",
        ],
    )

    view_zenith = _first_float(
        root,
        [
            ".//satelliteZenithAngle/center",
            ".//satelliteZenithAngle",
            ".//viewZenithAngle/center",
            ".//viewZenithAngle",
            ".//offNadirAngle/center",
            ".//offNadirAngle",
        ],
    )
    if view_zenith is None:
        across = _first_float(
            root, [".//acrossOffNadirAngle/center", ".//acrossOffNadirAngle"]
        )
        along = _first_float(
            root, [".//alongOffNadirAngle/center", ".//alongOffNadirAngle"]
        )
        if across is not None and along is not None:
            view_zenith = math.hypot(across, along)
        elif across is not None:
            view_zenith = abs(across)
        elif along is not None:
            view_zenith = abs(along)

    relative_azimuth = _relative_azimuth(sun_azimuth, view_azimuth)
    sensor_altitude = _first_float(
        root, [".//base/altitudeCoverage", ".//altitudeCoverage"]
    )

    processing_dt = _to_iso_utc(
        _first_nonempty_text(
            root, [".//specific/processingDateTime", ".//processingDateTime"]
        )
    )
    archived_version = _first_nonempty_text(
        root, [".//base/archivedVersion", ".//archivedVersion"]
    )

    scene_aot = _first_float(
        root,
        [".//specific/qualityFlag/sceneAOT", ".//qualityFlag/sceneAOT", ".//sceneAOT"],
    )
    scene_wv = _first_float(
        root,
        [".//specific/qualityFlag/sceneWV", ".//qualityFlag/sceneWV", ".//sceneWV"],
    )
    ozone_du = _first_float(root, [".//processing/ozoneValue", ".//ozoneValue"])

    cloud_cover = _first_float(
        root,
        [
            ".//specific/qualityFlag/cloudCover",
            ".//qualityFlag/cloudCover",
            ".//cloudCover",
        ],
    )
    cirrus_cover = _first_float(
        root,
        [
            ".//specific/qualityFlag/cirrusCover",
            ".//qualityFlag/cirrusCover",
            ".//cirrusCover",
        ],
    )
    haze_cover = _first_float(
        root,
        [
            ".//specific/qualityFlag/hazeCover",
            ".//qualityFlag/hazeCover",
            ".//hazeCover",
        ],
    )
    snow_cover = _first_float(
        root,
        [
            ".//specific/qualityFlag/snowCover",
            ".//qualityFlag/snowCover",
            ".//snowCover",
        ],
    )
    water_cover = _first_float(
        root,
        [
            ".//specific/qualityFlag/waterCover",
            ".//qualityFlag/waterCover",
            ".//waterCover",
        ],
    )
    cloud_shadow = _first_float(
        root,
        [
            ".//specific/qualityFlag/cloudShadow",
            ".//qualityFlag/cloudShadow",
            ".//cloudShadow",
        ],
    )
    noncloud_shadow = _first_float(
        root,
        [
            ".//specific/qualityFlag/noncloudShadow",
            ".//qualityFlag/noncloudShadow",
            ".//noncloudShadow",
        ],
    )
    sunglint = _first_float(
        root,
        [
            ".//specific/qualityFlag/sceneSunglint",
            ".//qualityFlag/sceneSunglint",
            ".//sceneSunglint",
        ],
    )

    quality_atm_text = _first_nonempty_text(
        root,
        [
            ".//specific/qualityFlag/qualityAtmosphere",
            ".//qualityFlag/qualityAtmosphere",
            ".//qualityAtmosphere",
        ],
    )
    quality_atm = _to_int(quality_atm_text)
    if quality_atm is None:
        quality_atm = quality_atm_text

    cirrus_haze_removal = _first_nonempty_text(
        root, [".//processing/cirrusHazeRemoval", ".//cirrusHazeRemoval"]
    )
    water_type = _first_nonempty_text(root, [".//processing/waterType", ".//waterType"])

    expected_vnir = _to_int_list(
        root.findtext(".//vnirProductQuality/expectedChannelsList")
    )
    expected_swir = _to_int_list(
        root.findtext(".//swirProductQuality/expectedChannelsList")
    )
    missing_vnir = _to_int_list(
        root.findtext(".//vnirProductQuality/missingChannelsList")
    )
    missing_swir = _to_int_list(
        root.findtext(".//swirProductQuality/missingChannelsList")
    )

    line_time_summary = _enmap_line_time_summary(root)
    jitter_summary = _enmap_jitter_summary(root)

    product_level = _enmap_product_level(root)
    product_format = _first_nonempty_text(root, [".//base/format", ".//format"])
    radiometry_quantity, radiometry_units = _enmap_radiometry_from_metadata(
        root, product_level
    )

    orbit_no = _to_int(
        _first_nonempty_text(root, [".//specific/orbitNo", ".//orbitNo"])
    )
    orbit_direction = _first_nonempty_text(
        root, [".//specific/orbitDirection", ".//orbitDirection"]
    )
    orbit_type = _first_nonempty_text(root, [".//specific/orbitType", ".//orbitType"])
    mission_phase = _first_nonempty_text(
        root, [".//specific/missionPhase", ".//missionPhase"]
    )
    acquisition_mode = _first_nonempty_text(
        root, [".//specific/acquisitionMode", ".//acquisitionMode"]
    )
    biome_type = _first_nonempty_text(root, [".//specific/biomeType", ".//biomeType"])

    mean_ground_elevation = _first_float(
        root, [".//specific/meanGroundElevation", ".//meanGroundElevation"]
    )
    mean_slope = _first_float(root, [".//specific/meanSlope", ".//meanSlope"])
    dem_database = _first_nonempty_text(
        root,
        [
            ".//specific/digitalElevationModelDatabase",
            ".//digitalElevationModelDatabase",
        ],
    )
    dem_accuracy = _first_float(
        root,
        [
            ".//specific/digitalElevationModelDatabaseAccuracy",
            ".//digitalElevationModelDatabaseAccuracy",
        ],
    )
    reference_database = _first_nonempty_text(
        root, [".//specific/referenceDatabase", ".//referenceDatabase"]
    )
    reference_accuracy = _first_float(
        root,
        [
            ".//specific/referenceImageDatabaseAccuracy",
            ".//referenceImageDatabaseAccuracy",
        ],
    )

    processing_center = _first_nonempty_text(
        root, [".//specific/processingCenter", ".//processingCenter"]
    )
    receiving_stations = _first_nonempty_text(
        root, [".//specific/receivingStations", ".//receivingStations"]
    )
    receiving_datetime = _to_iso_utc(
        _first_nonempty_text(
            root, [".//specific/receivingDateTime", ".//receivingDateTime"]
        )
    )

    overall_quality = _to_int(
        _first_nonempty_text(
            root,
            [".//specific/qualityFlag/overallQuality", ".//qualityFlag/overallQuality"],
        )
    )
    overall_quality_vnir = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/qualityFlag/overallQualityVNIR",
                ".//qualityFlag/overallQualityVNIR",
            ],
        )
    )
    overall_quality_swir = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/qualityFlag/overallQualitySWIR",
                ".//qualityFlag/overallQualitySWIR",
            ],
        )
    )
    quality_radiometry_vnir = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/qualityFlag/qualityRadiometryVNIR",
                ".//qualityFlag/qualityRadiometryVNIR",
            ],
        )
    )
    quality_radiometry_swir = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/qualityFlag/qualityRadiometrySWIR",
                ".//qualityFlag/qualityRadiometrySWIR",
            ],
        )
    )
    dead_pixels_vnir = _to_int(
        _first_nonempty_text(
            root,
            [".//specific/qualityFlag/deadPixelsVNIR", ".//qualityFlag/deadPixelsVNIR"],
        )
    )
    dead_pixels_swir = _to_int(
        _first_nonempty_text(
            root,
            [".//specific/qualityFlag/deadPixelsSWIR", ".//qualityFlag/deadPixelsSWIR"],
        )
    )
    defective_pixels_vnir = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/qualityFlag/defectivePixelsVNIR",
                ".//qualityFlag/defectivePixelsVNIR",
            ],
        )
    )
    defective_pixels_swir = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/qualityFlag/defectivePixelsSWIR",
                ".//qualityFlag/defectivePixelsSWIR",
            ],
        )
    )
    num_points_gcp = _to_int(
        _first_nonempty_text(
            root,
            [".//specific/qualityFlag/numPointsGCP", ".//qualityFlag/numPointsGCP"],
        )
    )
    num_points_icp = _to_int(
        _first_nonempty_text(
            root,
            [".//specific/qualityFlag/numPointsICP", ".//qualityFlag/numPointsICP"],
        )
    )
    ortho_residual = _first_float(
        root, [".//specific/qualityFlag/orthoResidual", ".//qualityFlag/orthoResidual"]
    )
    ortho_rmse = _first_float(
        root, [".//specific/qualityFlag/orthoRMSE", ".//qualityFlag/orthoRMSE"]
    )

    status_ok = _first_nonempty_text(
        root, [".//specific/instrumentStatus/statusOK", ".//instrumentStatus/statusOK"]
    )
    status_vnir = _first_nonempty_text(
        root,
        [".//specific/instrumentStatus/statusVNIR", ".//instrumentStatus/statusVNIR"],
    )
    status_swir = _first_nonempty_text(
        root,
        [".//specific/instrumentStatus/statusSWIR", ".//instrumentStatus/statusSWIR"],
    )
    swir_selector = _first_nonempty_text(
        root,
        [
            ".//specific/instrumentStatus/SWIRAOrSWIRBSelected",
            ".//instrumentStatus/SWIRAOrSWIRBSelected",
        ],
    )

    vnir_product_status = _first_nonempty_text(
        root,
        [
            ".//specific/vnirProductQuality/vnirProductStatus",
            ".//vnirProductQuality/vnirProductStatus",
        ],
    )
    swir_product_status = _first_nonempty_text(
        root,
        [
            ".//specific/swirProductQuality/swirProductStatus",
            ".//swirProductQuality/swirProductStatus",
        ],
    )
    vnir_channels_expected = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/vnirProductQuality/numChannelsExpected",
                ".//vnirProductQuality/numChannelsExpected",
            ],
        )
    )
    vnir_channels_missing = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/vnirProductQuality/numChannelsMissing",
                ".//vnirProductQuality/numChannelsMissing",
            ],
        )
    )
    swir_channels_expected = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/swirProductQuality/numChannelsExpected",
                ".//swirProductQuality/numChannelsExpected",
            ],
        )
    )
    swir_channels_missing = _to_int(
        _first_nonempty_text(
            root,
            [
                ".//specific/swirProductQuality/numChannelsMissing",
                ".//swirProductQuality/numChannelsMissing",
            ],
        )
    )

    band_indices = list(band_indices or [])
    validity_mask = [bool(v) for v in (validity_mask or [])]
    radiometry_scale = [band_meta[b].get("gain") for b in band_indices]
    radiometry_offset = [band_meta[b].get("offset") for b in band_indices]
    radiometry_wl = [band_meta[b].get("wavelength") for b in band_indices]
    radiometry_fwhm = [band_meta[b].get("fwhm") for b in band_indices]

    meta.set_extended_value("acquisition.start_time_utc", start_time)
    meta.set_extended_value("acquisition.end_time_utc", end_time)
    meta.set_extended_value("acquisition.center_latitude_deg", center_lat)
    meta.set_extended_value("acquisition.center_longitude_deg", center_lon)
    meta.set_extended_value("acquisition.day_of_year", _day_of_year(start_time))
    meta.set_extended_value("acquisition.line_time_summary", line_time_summary)

    meta.set_extended_value("geometry.sun_zenith_deg", sun_zenith)
    meta.set_extended_value("geometry.sun_azimuth_deg", sun_azimuth)
    meta.set_extended_value("geometry.view_zenith_deg", view_zenith)
    meta.set_extended_value("geometry.view_azimuth_deg", view_azimuth)
    meta.set_extended_value("geometry.relative_azimuth_deg", relative_azimuth)
    meta.set_extended_value("geometry.sensor_altitude_m", sensor_altitude)
    meta.set_extended_value("geometry.jitter_summary", jitter_summary)

    meta.set_extended_value("radiometry.quantity", radiometry_quantity)
    meta.set_extended_value("radiometry.units", radiometry_units)
    meta.set_extended_value("radiometry.scale", radiometry_scale)
    meta.set_extended_value("radiometry.offset", radiometry_offset)
    meta.set_extended_value("radiometry.wavelengths_nm", radiometry_wl)
    meta.set_extended_value("radiometry.fwhm_nm", radiometry_fwhm)
    meta.set_extended_value(
        "radiometry.valid_band_mask", [1 if v else 0 for v in validity_mask]
    )
    meta.set_extended_value("radiometry.valid_band_count", int(sum(validity_mask)))

    if scene_aot is not None:
        meta.set_extended_form_value(
            "atmosphere.aod_550",
            value=float(scene_aot) / 1000.0,
            form="scalar",
            source="qualityFlag/sceneAOT",
        )
    if scene_wv is not None:
        meta.set_extended_form_value(
            "atmosphere.h2o_g_cm2",
            value=float(scene_wv) / 1000.0,
            form="scalar",
            source="qualityFlag/sceneWV",
        )
    meta.set_extended_value("atmosphere.ozone_du", ozone_du)

    meta.set_extended_value("quality.cloudy_pixels_percent", cloud_cover)
    meta.set_extended_value("quality.quality_atmosphere_flag", quality_atm)
    meta.set_extended_value("quality.coverage_percent.cloud", cloud_cover)
    meta.set_extended_value("quality.coverage_percent.cirrus", cirrus_cover)
    meta.set_extended_value("quality.coverage_percent.haze", haze_cover)
    meta.set_extended_value("quality.coverage_percent.snow", snow_cover)
    meta.set_extended_value("quality.coverage_percent.water", water_cover)
    meta.set_extended_value("quality.coverage_percent.cloud_shadow", cloud_shadow)
    meta.set_extended_value("quality.coverage_percent.noncloud_shadow", noncloud_shadow)
    meta.set_extended_value("quality.coverage_percent.sunglint", sunglint)
    if root.find(".//product/quicklook") is not None:
        meta.set_extended_value("quality.mask_layers", {"quicklook": True})

    meta.set_extended_value("processing.processor_version", archived_version)
    meta.set_extended_value("processing.processing_datetime_utc", processing_dt)
    meta.set_extended_value("processing.cirrus_haze_removal", cirrus_haze_removal)

    if water_type is not None:
        meta.set_extended_value("quality.water_type", water_type)

    meta.set_extended_value("uncertainty.reflectance_uncertainty_present", False)

    meta.set_extended_value("enmap.processing.cirrusHazeRemoval", cirrus_haze_removal)
    meta.set_extended_value("enmap.processing.waterType", water_type)
    meta.set_extended_value("enmap.qualityFlag.cloudCover", cloud_cover)
    meta.set_extended_value("enmap.qualityFlag.cirrusCover", cirrus_cover)
    meta.set_extended_value("enmap.qualityFlag.hazeCover", haze_cover)
    meta.set_extended_value("enmap.qualityFlag.snowCover", snow_cover)
    meta.set_extended_value("enmap.qualityFlag.waterCover", water_cover)
    meta.set_extended_value("enmap.qualityFlag.cloudShadow", cloud_shadow)
    meta.set_extended_value("enmap.qualityFlag.noncloudShadow", noncloud_shadow)
    meta.set_extended_value("enmap.qualityFlag.sceneSunglint", sunglint)
    meta.set_extended_value("enmap.qualityFlag.qualityAtmosphere", quality_atm)
    meta.set_extended_value("enmap.qualityFlag.sceneAOT", scene_aot)
    meta.set_extended_value("enmap.qualityFlag.sceneWV", scene_wv)
    meta.set_extended_value("enmap.qualityFlag.overallQuality", overall_quality)
    meta.set_extended_value(
        "enmap.qualityFlag.overallQualityVNIR", overall_quality_vnir
    )
    meta.set_extended_value(
        "enmap.qualityFlag.overallQualitySWIR", overall_quality_swir
    )
    meta.set_extended_value(
        "enmap.qualityFlag.qualityRadiometryVNIR", quality_radiometry_vnir
    )
    meta.set_extended_value(
        "enmap.qualityFlag.qualityRadiometrySWIR", quality_radiometry_swir
    )
    meta.set_extended_value("enmap.qualityFlag.deadPixelsVNIR", dead_pixels_vnir)
    meta.set_extended_value("enmap.qualityFlag.deadPixelsSWIR", dead_pixels_swir)
    meta.set_extended_value(
        "enmap.qualityFlag.defectivePixelsVNIR", defective_pixels_vnir
    )
    meta.set_extended_value(
        "enmap.qualityFlag.defectivePixelsSWIR", defective_pixels_swir
    )
    meta.set_extended_value("enmap.qualityFlag.numPointsGCP", num_points_gcp)
    meta.set_extended_value("enmap.qualityFlag.numPointsICP", num_points_icp)
    meta.set_extended_value("enmap.qualityFlag.orthoResidual", ortho_residual)
    meta.set_extended_value("enmap.qualityFlag.orthoRMSE", ortho_rmse)
    meta.set_extended_value("enmap.base.level", product_level)
    meta.set_extended_value("enmap.base.format", product_format)
    meta.set_extended_value("enmap.base.archivedVersion", archived_version)
    meta.set_extended_value("enmap.specific.processingDateTime", processing_dt)
    meta.set_extended_value("enmap.specific.processingCenter", processing_center)
    meta.set_extended_value("enmap.specific.receivingStations", receiving_stations)
    meta.set_extended_value("enmap.specific.receivingDateTime", receiving_datetime)
    meta.set_extended_value("enmap.specific.orbitNo", orbit_no)
    meta.set_extended_value("enmap.specific.orbitDirection", orbit_direction)
    meta.set_extended_value("enmap.specific.orbitType", orbit_type)
    meta.set_extended_value("enmap.specific.missionPhase", mission_phase)
    meta.set_extended_value("enmap.specific.acquisitionMode", acquisition_mode)
    meta.set_extended_value("enmap.specific.biomeType", biome_type)
    meta.set_extended_value("enmap.specific.meanGroundElevation", mean_ground_elevation)
    meta.set_extended_value("enmap.specific.meanSlope", mean_slope)
    meta.set_extended_value(
        "enmap.specific.digitalElevationModelDatabase", dem_database
    )
    meta.set_extended_value(
        "enmap.specific.digitalElevationModelDatabaseAccuracy", dem_accuracy
    )
    meta.set_extended_value("enmap.specific.referenceDatabase", reference_database)
    meta.set_extended_value(
        "enmap.specific.referenceImageDatabaseAccuracy", reference_accuracy
    )
    meta.set_extended_value("enmap.instrumentStatus.statusOK", status_ok)
    meta.set_extended_value("enmap.instrumentStatus.statusVNIR", status_vnir)
    meta.set_extended_value("enmap.instrumentStatus.statusSWIR", status_swir)
    meta.set_extended_value(
        "enmap.instrumentStatus.SWIRAOrSWIRBSelected", swir_selector
    )
    meta.set_extended_value(
        "enmap.vnirProductQuality.vnirProductStatus", vnir_product_status
    )
    meta.set_extended_value(
        "enmap.swirProductQuality.swirProductStatus", swir_product_status
    )
    meta.set_extended_value(
        "enmap.vnirProductQuality.numChannelsExpected", vnir_channels_expected
    )
    meta.set_extended_value(
        "enmap.vnirProductQuality.numChannelsMissing", vnir_channels_missing
    )
    meta.set_extended_value(
        "enmap.swirProductQuality.numChannelsExpected", swir_channels_expected
    )
    meta.set_extended_value(
        "enmap.swirProductQuality.numChannelsMissing", swir_channels_missing
    )

    aux_node = root.find(".//specific/auxDataVersion")
    if aux_node is not None:
        for child in list(aux_node):
            if child.text is not None and child.text.strip() != "":
                meta.set_extended_value(
                    f"enmap.auxDataVersion.{child.tag}", child.text.strip()
                )

    meta.set_extended_value(
        "enmap.vnirProductQuality.expectedChannelsList", expected_vnir
    )
    meta.set_extended_value(
        "enmap.vnirProductQuality.missingChannelsList", missing_vnir
    )
    meta.set_extended_value(
        "enmap.swirProductQuality.expectedChannelsList", expected_swir
    )
    meta.set_extended_value(
        "enmap.swirProductQuality.missingChannelsList", missing_swir
    )


def _find_optional_file(folder, suffix):
    """Return first file (sorted) in folder ending with suffix, or None."""
    try:
        matches = sorted(
            [
                f
                for f in os.listdir(folder)
                if f.endswith(suffix) and os.path.isfile(os.path.join(folder, f))
            ]
        )
    except Exception as e:
        gs.fatal(f"Cannot read EnMAP folder '{folder}': {e}")

    return os.path.join(folder, matches[0]) if matches else None


def _find_required_file(folder, suffix):
    """Return first file (sorted) in folder ending with suffix, or fatal."""
    try:
        matches = sorted(
            [
                f
                for f in os.listdir(folder)
                if f.endswith(suffix) and os.path.isfile(os.path.join(folder, f))
            ]
        )
    except Exception as e:
        gs.fatal(f"Cannot read EnMAP folder '{folder}': {e}")

    if not matches:
        gs.fatal(f"Required EnMAP file '*{suffix}' not found in folder: {folder}")

    return os.path.join(folder, matches[0])


def _find_product_image(folder, root, path, suffixes, description):
    """Find an image named by metadata, with a suffix fallback for old products."""
    declared = root.findtext(path)
    if declared:
        declared = os.path.basename(declared.strip())
        candidate = os.path.join(folder, declared)
        if os.path.isfile(candidate):
            return candidate

    for suffix in suffixes:
        candidate = _find_optional_file(folder, suffix)
        if candidate:
            return candidate

    expected = " or ".join(f"*{suffix}" for suffix in suffixes)
    gs.fatal(
        f"Required EnMAP {description} image not found. Expected {expected} "
        f"in product folder: {folder}"
    )


def _enmap_spectral_sources(meta_xml_path, folder):
    """Return spectral source descriptors for the product processing level."""
    tree = ET.parse(meta_xml_path)
    root = tree.getroot()
    level = _enmap_product_level(root)

    if level == "L1B":
        return [
            {
                "type": "vnir",
                "path": _find_product_image(
                    folder,
                    root,
                    ".//product/image/vnir/name",
                    ("SPECTRAL_IMAGE_VNIR.TIF", "SPECTRAL_IMAGE_VNIR.BSQ"),
                    "VNIR",
                ),
            },
            {
                "type": "swir",
                "path": _find_product_image(
                    folder,
                    root,
                    ".//product/image/swir/name",
                    ("SPECTRAL_IMAGE_SWIR.TIF", "SPECTRAL_IMAGE_SWIR.BSQ"),
                    "SWIR",
                ),
            },
        ]

    if level in ("L1C", "L2A"):
        return [
            {
                "type": "single",
                "path": _find_product_image(
                    folder,
                    root,
                    ".//product/image/merge/name",
                    ("SPECTRAL_IMAGE.TIF", "SPECTRAL_IMAGE.BSQ"),
                    "merged spectral",
                ),
            }
        ]

    gs.fatal(
        f"Unsupported or missing EnMAP processing level '{level}'. "
        "Supported levels are L1B, L1C, and L2A."
    )


def find_nearest_band(wavelength, wavelengths):
    return (
        min(range(len(wavelengths)), key=lambda i: abs(wavelengths[i] - wavelength)) + 1
    )


def _warp_to_northup_tif(input_path, workdir):
    base = os.path.basename(input_path)
    out_tif = os.path.join(workdir, f"{base}.northup.tif")
    cmd = [
        "gdalwarp",
        "-q",
        "-overwrite",
        "-of",
        "GTiff",
        "-r",
        "near",
        "-multi",
        "-wo",
        "NUM_THREADS=ALL_CPUS",
        "-co",
        "TILED=YES",
        "-co",
        "COMPRESS=NONE",
        "-co",
        "BIGTIFF=IF_SAFER",
        input_path,
        out_tif,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        gs.fatal("gdalwarp not found. Please install GDAL command line tools.")
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        gs.fatal(f"Failed to warp rotated EnMAP L1B image to north-up: {err}")
    return out_tif


def import_enmap(
    folder,
    output,
    composites=None,
    custom_wavelengths=None,
    strength_val=96,
    import_null=False,
):
    meta_path = _find_required_file(folder, "METADATA.XML")
    spectral_sources = _enmap_spectral_sources(meta_path, folder)
    warp_tmpdir = None
    if len(spectral_sources) > 1:
        warp_tmpdir = tempfile.mkdtemp(prefix="ihyper_enmap_l1b_")
        spectral_sources = [
            {
                "type": source["type"],
                "path": _warp_to_northup_tif(source["path"], warp_tmpdir),
            }
            for source in spectral_sources
        ]

    try:
        dataset_meta = parse_dataset_metadata(meta_path)
    except ValueError as error:
        gs.fatal(str(error))

    try:
        band_meta, band_entries = parse_band_metadata(meta_path, spectral_sources)
    except ValueError as error:
        gs.fatal(f"Invalid EnMAP spectral metadata: {error}")

    source_entries = [
        entry
        for entry in band_entries
        if band_meta.get(entry["global_band"], {}).get("wavelength") is not None
    ]
    valid_entries = [
        entry
        for entry in source_entries
        if band_meta.get(entry["global_band"], {}).get("valid", 0) == 1
    ]
    if not valid_entries:
        gs.fatal("No valid bands after XML-based selection.")

    wavelengths = []
    band_names = []
    for entry in valid_entries:
        b = entry["global_band"]
        bname = f"{output}_b{b:03d}"
        with suppress_stderr():
            Module(
                "r.external",
                input=entry["source_path"],
                output=bname,
                band=entry["source_band"],
                flags="o",
                quiet=True,
                overwrite=True,
            )
        wavelengths.append(band_meta[b]["wavelength"])
        band_names.append(bname)
        Module("r.colors", map=bname, color="grey.eq", quiet=True)

    # per-band metadata before any cleanup
    for idx, entry in enumerate(valid_entries, 1):
        b = entry["global_band"]
        meta = band_meta[b]
        Module(
            "r.support",
            map=band_names[idx - 1],
            title=f"Band {b}",
            units="nm",
            source1=f"Wavelength: {meta['wavelength']} nm",
            source2=f"FWHM: {meta['fwhm']} nm",
            description="Validated band",
            quiet=True,
        )

    # composites
    rgb_target = COMPOSITES["rgb"]
    rgb_indices = [find_nearest_band(wl, wavelengths) for wl in rgb_target]
    rgb_enhanced = {i: band_names[i - 1] for i in rgb_indices}

    gs.use_temp_region()
    Module("g.region", raster=band_names[0], quiet=True)

    if composites:
        for comp in composites:
            if comp not in COMPOSITES:
                continue
            bands = [find_nearest_band(wl, wavelengths) for wl in COMPOSITES[comp]]
            rgb_maps = [rgb_enhanced.get(b, band_names[b - 1]) for b in bands]
            if comp.upper() == "RGB":
                Module(
                    "i.colors.enhance",
                    red=rgb_maps[0],
                    green=rgb_maps[1],
                    blue=rgb_maps[2],
                    strength=str(strength_val),
                    flags="p",
                    quiet=True,
                )
            else:
                Module(
                    "i.colors.enhance",
                    red=rgb_maps[0],
                    green=rgb_maps[1],
                    blue=rgb_maps[2],
                    strength=str(strength_val),
                    quiet=True,
                )
            outname = f"{output}_{comp.lower().replace('-', '_')}"
            Module(
                "r.composite",
                red=rgb_maps[0],
                green=rgb_maps[1],
                blue=rgb_maps[2],
                output=outname,
                quiet=True,
                overwrite=True,
            )
            gs.info(f"Generated composite raster: {outname}")

    if custom_wavelengths:
        custom_indices = [
            find_nearest_band(wl, wavelengths) for wl in custom_wavelengths
        ]
        custom_maps = [rgb_enhanced.get(b, band_names[b - 1]) for b in custom_indices]
        Module(
            "i.colors.enhance",
            red=custom_maps[0],
            green=custom_maps[1],
            blue=custom_maps[2],
            strength=str(strength_val),
            quiet=True,
        )
        Module(
            "r.composite",
            red=custom_maps[0],
            green=custom_maps[1],
            blue=custom_maps[2],
            output=f"{output}_custom",
            quiet=True,
            overwrite=True,
        )
        gs.info(f"Generated custom composite raster: {output}_custom")

    # Use band-index Z axis to keep depth exactly equal to number of imported bands.
    bands_total = len(band_names)
    Module(
        "g.region",
        raster=band_names[0],
        b=0,
        t=bands_total,
        tbres=1,
        quiet=True,
    )

    # gain/offset + FCELL
    gains = [band_meta[entry["global_band"]]["gain"] for entry in valid_entries]
    offs = [band_meta[entry["global_band"]]["offset"] for entry in valid_entries]
    same_gain = all(g == gains[0] for g in gains)
    same_offset = all(o == offs[0] for o in offs)

    float_names = []
    try:
        if same_gain and same_offset:
            Module(
                "r.to.rast3",
                input=band_names,
                output=output,
                quiet=True,
                overwrite=True,
            )
            Module("g.region", raster_3d=output, quiet=True)
            g0, o0 = gains[0], offs[0]
            Module(
                "r3.mapcalc",
                expression=f"{output}_scaled = float({output} * {g0} + {o0})",
                quiet=True,
                overwrite=True,
            )
            Module("g.remove", type="raster_3d", name=output, flags="f", quiet=True)
            Module("g.rename", raster_3d=(f"{output}_scaled", output), quiet=True)
        else:
            for idx, bname in enumerate(band_names):
                g = gains[idx]
                o = offs[idx]
                fout = f"{bname}_f"
                Module(
                    "r.mapcalc",
                    expression=f"{fout} = float({bname} * {g} + {o})",
                    quiet=True,
                    overwrite=True,
                )
                float_names.append(fout)
            Module(
                "r.to.rast3",
                input=float_names,
                output=output,
                quiet=True,
                overwrite=True,
            )
    finally:
        if float_names:
            Module("g.remove", type="raster", name=float_names, flags="f", quiet=True)
        Module("g.remove", type="raster", name=band_names, flags="f", quiet=True)

    # hyperspectral metadata (JSON)
    try:
        if import_null:
            source_bands = [entry["global_band"] for entry in source_entries]
            wavelengths_meta = [band_meta[b]["wavelength"] for b in source_bands]
            fwhm_meta = [band_meta[b]["fwhm"] for b in source_bands]
            validity_meta = [bool(band_meta[b].get("valid", 0)) for b in source_bands]
            selected_bands = source_bands
        else:
            valid_bands = [entry["global_band"] for entry in valid_entries]
            wavelengths_meta = [band_meta[b]["wavelength"] for b in valid_bands]
            fwhm_meta = [band_meta[b]["fwhm"] for b in valid_bands]
            validity_meta = [True] * len(valid_bands)
            selected_bands = valid_bands

        meta = HyperMetadata.for_spectral_data(
            wavelengths=wavelengths_meta,
            fwhm=fwhm_meta,
            sensor="EnMAP",
            radiometric_quantity=dataset_meta.get("radiometric_quantity"),
            radiometric_units=dataset_meta.get("radiometric_units"),
            acquisition_datetime=dataset_meta.get("acquisition_datetime"),
            solar_zenith_angle=dataset_meta.get("solar_zenith_angle"),
            solar_azimuth_angle=dataset_meta.get("solar_azimuth_angle"),
            satellite_zenith_angle=dataset_meta.get("satellite_zenith_angle"),
            satellite_azimuth_angle=dataset_meta.get("satellite_azimuth_angle"),
        )
        meta.set_validity(validity_meta)

        _populate_enmap_extended_metadata(
            meta=meta,
            meta_xml_path=meta_path,
            band_meta=band_meta,
            band_indices=selected_bands,
            validity_mask=validity_meta,
        )

        mapset = gs.gisenv().get("MAPSET", "")
        out_full = f"{output}@{mapset}" if mapset and "@" not in output else output

        cmd = [
            "i.hyper.import",
            f"input={shlex.quote(folder)}",
            "product=enmap",
            f"output={output}",
            f"strength={strength_val}",
        ]
        if composites:
            cmd.append(f"composites={','.join(composites)}")
        if custom_wavelengths:
            cmd.append(
                "composites_custom=" + ",".join(str(v) for v in custom_wavelengths)
            )
        if import_null:
            cmd.append("-n")

        meta.add_history_entry(
            command=" ".join(cmd),
            inputs=[],
            outputs=[{"id": meta.dataset_id, "map_name": out_full}],
        )
        meta.save(output, save_region=True)
    except Exception as e_meta:
        gs.warning(f"Failed to write r3 metadata: {e_meta}")

    gs.del_temp_region()

    if warp_tmpdir:
        shutil.rmtree(warp_tmpdir, ignore_errors=True)


def _resolve_enmap_dir(path_like):
    """Accept either a folder or any file in the EnMAP product folder."""
    if os.path.isdir(path_like):
        return path_like
    return os.path.dirname(path_like)


def run_import(options, flags):
    custom = None
    if options.get("composites_custom"):
        try:
            custom = [float(x.strip()) for x in options["composites_custom"].split(",")]
            if len(custom) != 3:
                raise ValueError
        except Exception:
            gs.fatal(
                "Invalid format for composites_custom. Usage example: 850,1650,660"
            )
    strength_opt = options.get("strength")
    if strength_opt is None or str(strength_opt).strip() == "":
        strength_val = 96
    else:
        try:
            strength_val = int(str(strength_opt).strip())
        except Exception:
            gs.fatal("Invalid strength. Provide an integer 0-100.")
        if not (0 <= strength_val <= 100):
            gs.fatal("Invalid strength. Provide an integer 0-100.")

    # directory from a file-or-folder input
    folder = _resolve_enmap_dir(options["input"])

    import_enmap(
        folder,
        options["output"],
        composites=[c.strip() for c in options["composites"].split(",")]
        if options.get("composites")
        else None,
        custom_wavelengths=custom,
        strength_val=strength_val,
        import_null=bool(flags.get("n")),
    )
