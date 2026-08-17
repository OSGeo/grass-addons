#!/usr/bin/env python

##############################################################################
# MODULE:    v.photo.geometry
#
# AUTHOR(S): Corey T. White <smortopahri@gmail.com>
#
# PURPOSE:   Recovers acquisition geometry from aerial photos with incomplete
#            flight metadata.
#
# COPYRIGHT: (C) 2025-2026 by Corey T. White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % label: Recovers acquisition geometry from aerial photos.
# % description: Derives camera pose, ground sample distance, image footprints, flight path, and overlap from a directory of aerial photos and an elevation model.
# % keyword: vector
# % keyword: photogrammetry
# % keyword: UAV
# % keyword: footprint
# %end
#
# %option G_OPT_F_INPUT
# % description: Directory of aerial photos
# % required: yes
# %end
#
# %option G_OPT_R_ELEV
# % key: elevation
# % required: no
# %end
#
# %option G_OPT_R_OUTPUT
# % key: overlap_raster
# % type: string
# % required: no
# % description: Output raster map showing percent overlap
# %end
#
# %option
# % key: overlap_stats
# % type: string
# % required: no
# % description: Output CSV file with overlap statistics
# %end
#
# %option G_OPT_V_OUTPUT
# % key: footprint_vector
# % type: string
# % required: no
# % description: Output vector map of image footprints
# %end
#
# %flag
# % key: c
# % description: Calculate overlaps between consecutive footprints
# %end

import sys
import os
import glob
import math
import csv
from datetime import datetime, timedelta

import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pyproj import CRS, Transformer

import grass.script as gs
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Boundary, Centroid, Point, Line
from grass.pygrass.modules import Module


def to_float_if_possible(val):
    # Try to convert to float, otherwise return original
    try:
        return float(val)
    except (TypeError, ValueError):
        return val


def get_exif(image_path):
    """Return EXIF data as dict."""

    # TODO: Use exiftools (https://exiftool.org/TagNames/EXIF.html)
    img = Image.open(image_path)
    exif_data = {}
    info = img._getexif()
    if not info:
        return exif_data
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                gps_data[sub_decoded] = value[t]
            exif_data["GPSInfo"] = gps_data
        else:
            exif_data[decoded] = value
    return exif_data


def dms_to_dd(dms, ref):
    d, m, s = dms
    gs.debug(_("GPS data found in %s %s %s with ref %s") % (d, m, s, ref))
    dd = d + (m / 60.0 + (s / 3600.0))
    if ref in ["S", "W"]:
        dd = -dd
    return dd


def get_coords(exif):
    """Return lon, lat, alt if available."""
    gps = exif.get("GPSInfo")
    if not gps:
        return None
    lat = dms_to_dd(gps["GPSLatitude"], gps["GPSLatitudeRef"])
    lon = dms_to_dd(gps["GPSLongitude"], gps["GPSLongitudeRef"])
    alt = gps.get("GPSAltitude")
    gs.debug(f"GPS altitude ref: {gps.get('GPSAltitudeRef', 'N/A')}")
    if not alt:
        return None
    return lon, lat, alt


def parse_exif_datetime(exif):
    """
    Parse DateTimeOriginal + SubSecTimeOriginal + OffsetTimeOriginal
    into a precise datetime object.
    """
    dt_str = exif.get("DateTimeOriginal")  # "YYYY:MM:DD HH:MM:SS"
    subsec_str = exif.get("SubsecTimeOriginal") or exif.get("SubSecTime") or "0"
    offset_str = exif.get("OffsetTimeOriginal")  # e.g. "-05:00"

    if not dt_str:
        return None

    # Convert main datetime
    dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")

    # Add subseconds
    try:
        subsec = int(subsec_str)
        # normalize length: "1"→100 ms, "254"→254 ms
        factor = 10 ** len(subsec_str)
        dt += timedelta(seconds=subsec / factor)
    except Exception:
        pass

    # Apply timezone offset if present
    if offset_str:
        sign = 1 if offset_str[0] == "+" else -1
        hours, mins = map(int, offset_str[1:].split(":"))
        offset = timedelta(hours=sign * hours, minutes=sign * mins)
        dt -= offset  # convert to UTC

    return dt


def haversine(lon1, lat1, lon2, lat2):
    R = 6371000  # Earth radius in m
    dlon, dlat = math.radians(lon2 - lon1), math.radians(lat2 - lat1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def is_duplicate(img1, img2, dist_thresh=0.2, time_thresh=0.5):
    """Return True if two images are near-duplicates in space & time."""
    d = haversine(img1["lon"], img1["lat"], img2["lon"], img2["lat"])
    dt = abs((img2["timestamp"] - img1["timestamp"]).total_seconds())
    return d < dist_thresh and dt < time_thresh


def bearing(lon1, lat1, lon2, lat2):
    """Bearing from (lon1,lat1) to (lon2,lat2) in degrees (0=N)."""
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )

    brng = math.atan2(x, y)
    brng_deg = (math.degrees(brng) + 360) % 360

    return brng_deg


def heading(prev_img, current_img):
    """
    Determining the angle between the current position and the previous position.
    """
    return bearing(
        prev_img["lon"], prev_img["lat"], current_img["lon"], current_img["lat"]
    )


def circular_mean(angles):
    """Mean of angles in degrees, safe across 0/360 wrap."""
    sin_sum = sum(math.sin(math.radians(a)) for a in angles)
    cos_sum = sum(math.cos(math.radians(a)) for a in angles)
    return (math.degrees(math.atan2(sin_sum, cos_sum)) + 360) % 360


def compute_headings_from_gps(images, dist_thresh=0.2, time_thresh=0.5):
    """
    Compute yaw for each image if EXIF yaw is missing.
    Uses GPS positions and timestamps to estimate heading, skipping near-duplicates.

    Args:
        images: list of dicts with keys:
            lon, lat, timestamp (datetime), yaw (optional EXIF)
        dist_thresh: minimum distance (meters) to consider images distinct
        time_thresh: minimum time difference (seconds) to consider images distinct

    Returns:
        images: list with "yaw" field populated where missing
    """
    images = sorted(images, key=lambda x: x["timestamp"])

    n = len(images)
    for i, img in enumerate(images):
        if img.get("yaw") is not None:
            continue  # keep EXIF yaw

        # Find previous non-duplicate image
        prev_img = None
        for j in range(i - 1, -1, -1):
            if not is_duplicate(images[j], img, dist_thresh, time_thresh):
                prev_img = images[j]
                break

        # Find next non-duplicate image
        next_img = None
        for j in range(i + 1, n):
            if not is_duplicate(img, images[j], dist_thresh, time_thresh):
                next_img = images[j]
                break

        # If previous image is duplicate
        prev_img_is_dup = (
            images[i - 1]
            if i > 0 and is_duplicate(images[i - 1], img, dist_thresh, time_thresh)
            else None
        )

        # If next image is duplicate
        next_img_is_dup = (
            images[i + 1]
            if i + 1 < n and is_duplicate(images[i + 1], img, dist_thresh, time_thresh)
            else None
        )

        if prev_img and next_img:
            # Average heading from previous and next
            h1 = heading(prev_img, img)
            h2 = heading(img, next_img)
            # Ensure the average is in the direction of h1
            avg_yaw = circular_mean([h1, h2])
            img["yaw"] = avg_yaw
        elif prev_img:
            img["yaw"] = heading(prev_img, img)
        elif next_img:
            img["yaw"] = heading(img, next_img)
        else:
            img["yaw"] = 0.0  # fallback if no neighbors

        # If plane is taking two photos in a row with adjusting roll to achieve NADIR camera orientation
        if prev_img_is_dup:
            img["roll"] = -45.0

        if next_img_is_dup:
            img["roll"] = 45.0
        # Rotate frame 90, so 0 is North
        # img["yaw"] = (img["yaw"] + 90) % 360

    return images


def get_focal_length(exif):
    """Return focal length in mm from EXIF data."""
    focal = exif.get("FocalLength")
    if not focal:
        return 0.1
    focal_mm = float(focal)
    return focal_mm


def compute_sensor_size(exif):
    """Estimate sensor size from EXIF data.

    The sensor width (mm) is calculated as:
        sensor_width_mm = (image_width_px / focal_plane_x_resolution) * conversion_factor

    where:
        image_width_px: EXIFImageWidth (pixels)
        focal_plane_x_resolution: FocalPlaneXResolution (pixels per unit)
        conversion_factor: 25.4 if ResolutionUnit is inches (2), otherwise 1.0

    The same formula applies for sensor height.
    """
    # image dimensions
    img_w = exif.get("ExifImageWidth")  # px
    img_h = exif.get("ExifImageHeight")  # px
    # 0.252 x 0.189 is the sensor size of the 1/2" CMOS sensor on the DJI Mavric Air 2 in inches
    # or 6.4mm x 4.8mm
    fp_x = exif.get("FocalPlaneXResolution", 0.252)  # pixels per unit (DPI)
    fp_y = exif.get("FocalPlaneYResolution", 0.189)  # pixels per unit (DPI)
    if not img_w or not img_h:
        gs.warning(_("Image dimensions not found in EXIF data"))
        return 0.1

    # resolution units: 2=inches, 3=cm, else assume inches
    unit = exif.get("FocalPlaneResolutionUnit", 2)

    if unit == 2:
        conv = 25.4  # mm/inch
    elif unit == 3:
        conv = 10.0  # mm/cm
    else:
        conv = 25.4

    gs.debug(_("Resolution unit conversion factor: %s") % conv)

    sensor_w_mm = 6.4  # (img_w / fp_x) * conv
    sensor_h_mm = 4.8  # (img_h / fp_y) * conv

    gs.debug(_("Sensor size: %smm x %smm") % (sensor_w_mm, sensor_h_mm))
    return (sensor_w_mm, sensor_h_mm)


def compute_gsd(exif, alt, focal_mm, sensor_size):
    """Estimate GSD (m/pixel) from EXIF and altitude."""
    # altitude in meters (if AGL, not AMSL!)
    if not alt:
        return 0.1  # fallback: 10 cm/px

    # image dimensions
    img_w = exif.get("ExifImageWidth")  # px
    img_h = exif.get("ExifImageHeight")  # px
    if not img_w or not img_h:
        return 0.1

    sensor_w, sensor_h = sensor_size
    gsd_w = float(alt * sensor_w) / float(focal_mm * img_w)
    gsd_h = float(alt * sensor_h) / float(focal_mm * img_h)
    gsd_avg = float(gsd_w + gsd_h) / 2.0  # average
    return (gsd_w, gsd_h, gsd_avg)


def calculate_overlaps(footprints_map, output_prefix):
    """
    Calculate overlaps between consecutive footprints using GRASS v.overlay.

    Args:
        footprints_map : name of vector map with all footprints
        output_prefix  : prefix for intermediate intersection maps

    Returns:
        list of overlap ratios
    """
    overlaps = []

    with VectorTopo(footprints_map) as vect:
        n = len(vect)

    # Loop over consecutive footprints
    for i in range(1, n + 1):
        # Select two consecutive areas by category
        sel1 = f"{footprints_map}_f1"
        sel2 = f"{footprints_map}_f2"

        gs.run_command(
            "v.extract",
            input=footprints_map,
            where=f"cat={i - 1}",
            output=sel1,
            overwrite=True,
        )
        gs.run_command(
            "v.extract",
            input=footprints_map,
            where=f"cat={i}",
            output=sel2,
            overwrite=True,
        )

        # Intersection
        inter = f"{output_prefix}_inter_{i}"
        gs.run_command(
            "v.overlay",
            ainput=sel1,
            binput=sel2,
            operator="and",
            output=inter,
            overwrite=True,
        )

        # Get areas
        a1 = float(
            Module("v.to.db", map=sel1, option="area", flags="p").outputs.stdout.strip()
        )
        inter_area = float(
            Module(
                "v.to.db", map=inter, option="area", flags="p"
            ).outputs.stdout.strip()
            or 0
        )

        overlap = inter_area / a1 if a1 > 0 else 0
        overlaps.append(overlap)

    return overlaps


def get_orientation(exif):
    """Extract yaw, pitch, roll; return defaults if not found."""
    # Do not set a Yaw default here, use EXIF value
    # if Yaw is not found it is calculated later
    # from GPS data.
    # Some cameras use MakerNotes instead of EXIF
    yaw = exif.get("FlightYawDegree")
    pitch = exif.get("GimbalPitchDegree", -90.0)  # Default: nadir
    roll = exif.get("GimbalRollDegree", 0.0)
    gs.debug(_("Orientation: yaw=%s, pitch=%s, roll=%s") % (yaw, pitch, roll))

    return yaw, pitch, roll


def get_footprint_dimensions(gsd_x, gsd_y, exif):
    """Calculate footprint dimensions based on EXIF data."""
    img_w = exif.get("ExifImageWidth")
    img_h = exif.get("ExifImageHeight")
    if not img_w or not img_h:
        gs.warning(_("Image dimensions not found in EXIF data"))
        return 0.1, 0.1
    footprint_w = gsd_x * img_w
    footprint_h = gsd_y * img_h
    gs.debug(
        _("Footprint dimensions from GSD: width=%s m, height=%s m")
        % (footprint_w, footprint_h)
    )
    return footprint_w, footprint_h


def intersect_ray_dem_fast(
    x0, y0, z0, dir_vec, dem_arr, region, step=None, max_dist=2000.0
):
    dir_vec = dir_vec / np.linalg.norm(dir_vec)
    if step is None:
        step = min(region["ewres"], region["nsres"])  # step at DEM resolution

    dist = 0.0
    while dist < max_dist:
        gx = x0 + dir_vec[0] * dist
        gy = y0 + dir_vec[1] * dist
        gz = z0 + dir_vec[2] * dist

        # Convert coordinates to row/col
        col = int((gx - region["w"]) / region["ewres"])
        row = int((region["n"] - gy) / region["nsres"])

        if 0 <= row < dem_arr.shape[0] and 0 <= col < dem_arr.shape[1]:
            ground_z = dem_arr[row, col]
            if gz <= ground_z:
                return gx, gy, ground_z
        else:
            break  # Out of bounds

        dist += step
    return None


def rotation_matrix_aircraft(yaw_deg, pitch_deg, roll_deg):
    yaw, pitch, roll = np.radians([yaw_deg, pitch_deg, roll_deg])

    Rz = np.array(
        [[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]
    )

    Ry = np.array(
        [
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)],
        ]
    )

    Rx = np.array(
        [[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]]
    )

    return Rz @ Ry @ Rx  # aircraft convention


def make_footprint(image_metadata, dem_arr, region):
    """Return rectangle footprint coords around image center."""
    # footprint size in meters
    e = image_metadata["easting"]
    n = image_metadata["northing"]
    alt = image_metadata["alt"]
    agl = image_metadata["agl"]
    focal_length = image_metadata["focal_length"]
    yaw = image_metadata["yaw"]
    pitch = image_metadata["pitch"]
    roll = image_metadata["roll"]
    sensor_w = image_metadata["sensor_size_w"]
    sensor_h = image_metadata["sensor_size_h"]

    x0, y0 = e, n
    z0 = alt  # camera height above reference plane

    corners = [
        (-sensor_w / 2, -sensor_h / 2),
        (sensor_w / 2, -sensor_h / 2),
        (sensor_w / 2, sensor_h / 2),
        (-sensor_w / 2, sensor_h / 2),
    ]

    gs.debug(f"Yaw: {yaw}, Pitch: {pitch}, Roll: {roll}")
    R = rotation_matrix_aircraft(yaw, pitch, roll)
    footprint = []
    for cx, cy in corners:
        # direction vector, Ray in camera coords (normalized by f)
        dir_vec = np.array([cx / focal_length, cy / focal_length, 1.0])
        dir_vec = R @ dir_vec
        hit = intersect_ray_dem_fast(
            x0, y0, z0, dir_vec, dem_arr, region, step=1.0, max_dist=2000.0
        )
        if hit:
            footprint.append(hit)

    if not footprint:
        gs.warning(_("No DEM intersections found, footprint empty"))
        return []

    footprint.append(footprint[0])  # close polygon
    gs.debug(f"Footprint corners after DEM intersection: {footprint}")
    return footprint


def make_footprint_basic(
    e, n, agl, ground_elev, focal_length, sensor_w, sensor_h, img_w, img_h, yaw_deg
):
    """
    Compute flat-ground footprint polygon (no DEM correction).

    e, n         : camera center (projected CRS, meters)
    agl          : altitude above ground (m)
    focal_length : focal length (mm)
    sensor_w,h   : sensor size (mm)
    img_w,h      : image size (pixels)
    yaw_deg      : heading (degrees, 0=N, clockwise)
    """

    # Ground field of view (footprint) in meters
    gfov_w = (sensor_w * agl) / focal_length
    gfov_h = (sensor_h * agl) / focal_length

    # Half dimensions
    dx = gfov_w / 2
    dy = gfov_h / 2

    # Rectangle corners centered at (0,0)
    corners = np.array(
        [
            [-dx, -dy],
            [dx, -dy],
            [dx, dy],
            [-dx, dy],
        ]
    )

    # Rotate by yaw (around origin)
    theta = math.radians(yaw_deg)
    R = np.array(
        [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
    )

    rotated = corners @ R.T

    # Translate to camera center
    footprint = [
        (round(e + x, 3), round(n + y, 3), round(ground_elev, 3)) for x, y in rotated
    ]
    footprint.append(footprint[0])  # close polygon
    return footprint


def get_camera_details(exif):
    """Extract camera details from EXIF data."""
    make = exif.get("Make", "Unknown")
    model = exif.get("Model", "Unknown")
    lens = exif.get("LensModel", "Unknown")
    gs.debug(_("Camera: %s %s, Lens: %s") % (make, model, lens))
    return make, model, lens


def get_photo_specs(exif):
    """Extract photo specifications from EXIF data."""
    iso = exif.get("ISOSpeedRatings")  # Default ISO
    shutter_speed = to_float_if_possible(exif.get("ShutterSpeedValue", 0.0))
    aperture = to_float_if_possible(exif.get("FNumber"))
    image_width = exif.get("ExifImageWidth")
    image_height = exif.get("ExifImageHeight")
    exposureTime = to_float_if_possible(exif.get("ExposureTime"))
    date_time = exif.get("DateTimeOriginal", "Unknown")
    gs.debug(
        _(
            "ISO: %s, Shutter Speed: %s, Aperture: %s, Image Size: %sx%s, Exposer Time: %s, Datetime: %s"
        )
        % (
            iso,
            shutter_speed,
            aperture,
            image_width,
            image_height,
            exposureTime,
            date_time,
        )
    )
    return (
        iso,
        shutter_speed,
        aperture,
        image_width,
        image_height,
        exposureTime,
        date_time,
    )


def create_vector_feature(image_metadata):
    """Create a vector feature from footprint points."""

    # Extract Attributes from image metadata
    e = image_metadata["easting"]
    n = image_metadata["northing"]
    lon = image_metadata["lon"]
    lat = image_metadata["lat"]
    alt = to_float_if_possible(image_metadata["alt"])
    agl_alt = image_metadata["agl"]
    yaw = image_metadata["yaw"]
    pitch = image_metadata["pitch"]
    roll = image_metadata["roll"]

    sensor_w = image_metadata["sensor_size_w"]
    sensor_h = image_metadata["sensor_size_h"]
    focal_length = image_metadata["focal_length"]

    gsd_w = image_metadata["gsd_w"]
    gsd_h = image_metadata["gsd_h"]
    gsd_avg = image_metadata["gsd_avg"]

    camera_make = image_metadata["camera_make"]
    camera_model = image_metadata["camera_model"]
    camera_lens = image_metadata["camera_lens"]
    filename = image_metadata["filename"]
    iso = image_metadata["iso"]
    shutter_speed = image_metadata["shutter_speed"]
    aperture = image_metadata["aperture"]
    image_width = image_metadata["iamge_width"]
    image_height = image_metadata["image_height"]
    exposure_time = image_metadata["exposure_time"]
    date_time = image_metadata["original_datetime"]

    attrs = (
        filename,
        focal_length,
        sensor_w,
        sensor_h,
        gsd_w,
        gsd_h,
        gsd_avg,
        yaw,
        pitch,
        roll,
        lon,
        lat,
        alt,
        agl_alt,
        iso,
        shutter_speed,
        aperture,
        image_width,
        image_height,
        exposure_time,
        date_time,
        camera_make,
        camera_model,
        camera_lens,
    )

    cat = image_metadata["category"]  # category ID
    # Generate boundary and centroid
    point = Point(x=e, y=n, z=alt)  # camera position
    footprint = image_metadata["footprint"]
    line = Line(points=[Point(x, y, z) for x, y, z in footprint])
    boundary = Boundary(points=[Point(x, y, z) for x, y, z in footprint])
    centroid = Centroid(x=e, y=n, z=alt)  # centroid at camera position

    return point, line, boundary, centroid, cat, attrs


def validate_vector_metadata(attrs, COLS_TYPES):
    if len(attrs) != len(COLS_TYPES) - 1:  # -1 for cat
        gs.fatal(
            ("Attribute count mismatch: expected %d, got %d")
            % (len(COLS_TYPES), len(attrs))
        )
    type_check = list(zip(attrs, [t[1] for t in COLS_TYPES[1:]]))
    for val, col_type in type_check:
        if col_type == "INTEGER" and not isinstance(val, int):
            gs.fatal(
                _("Attribute %s should be INTEGER, got %s") % (val, type(val).__name__)
            )
        elif col_type == "DOUBLE" and not isinstance(val, (float, int)):
            gs.fatal(
                _("Attribute %s should be DOUBLE, got %s") % (val, type(val).__name__)
            )
        elif col_type == "TEXT" and not isinstance(val, str):
            gs.fatal(
                _("Attribute %s should be TEXT, got %s") % (val, type(val).__name__)
            )


def write_vector(metadata, outmap):
    """Export footprint polygons to a GRASS vector map with pygrass."""
    COLS_TYPES = [
        ("cat", "INTEGER PRIMARY KEY"),
        ("filename", "TEXT"),
        ("focal_length", "DOUBLE"),
        ("sensor_size_w", "DOUBLE"),
        ("sensor_size_h", "DOUBLE"),
        ("gsd_w", "DOUBLE"),
        ("gsd_h", "DOUBLE"),
        ("gsd_avg", "DOUBLE"),
        ("yaw", "DOUBLE"),
        ("pitch", "DOUBLE"),
        ("roll", "DOUBLE"),
        ("lon", "DOUBLE"),
        ("lat", "DOUBLE"),
        ("alt", "DOUBLE"),
        ("agl_alt", "DOUBLE"),
        ("iso", "INTEGER"),
        ("shutter_speed", "DOUBLE"),
        ("aperture", "DOUBLE"),
        ("image_width", "INTEGER"),
        ("image_height", "INTEGER"),
        ("exposure_time", "DOUBLE"),
        ("date_time", "TEXT"),
        ("camera_make", "TEXT"),
        ("camera_model", "TEXT"),
        ("lens_model", "TEXT"),
    ]
    gs.verbose(
        _("Writing {} features to vector map <{}>...").format(len(metadata), outmap)
    )
    with VectorTopo(
        outmap, mode="w", with_z=False, tab_cols=COLS_TYPES, layer=1, overwrite=True
    ) as vect:
        for i, img in enumerate(metadata):
            feature = img["feature"]
            # Add area
            point, line, boundary, centroid, cat, attrs = feature
            gs.debug(f"Writing feature {attrs}")
            validate_vector_metadata(attrs, COLS_TYPES)
            vect.write(centroid)
            vect.write(geo_obj=point, cat=cat, attrs=attrs)
        vect.table.conn.commit()
        vect.build()


def create_transformer():
    """Reproject list of (lon,lat) coords from WGS84 to GRASS CRS."""
    grass_proj = gs.read_command("g.proj", flags="jf")  # PROJ JSON string
    grass_crs = CRS.from_string(grass_proj.strip())
    wgs84 = CRS.from_epsg(4326)

    # Build transformer (lon/lat WGS84 → GRASS CRS)
    transformer = Transformer.from_crs(wgs84, grass_crs, always_xy=True)
    return transformer


def get_above_ground_level_alt(e, n, alt, elevation) -> float:
    """
    Calculate Above Ground Level (AGL) altitude.

    e        : easting coordinate in GRASS CRS
    n        : northing coordinate in GRASS CRS
    alt      : EXIF altitude (ellipsoid or AMSL)
    elevation: DEM raster in GRASS
    """
    result = gs.raster_what(elevation, coord=[[e, n]])
    ground_elev = None
    alt = to_float_if_possible(alt)  # EXIF altitude
    alt = alt if alt is not None else 0.0
    if elevation in result[0]:
        val = result[0][elevation]["value"]
        if val not in (None, "null", "No data"):
            ground_elev = float(val)

    if ground_elev is None:
        gs.warning(
            _("Elevation raster %s not found at coordinates (%s, %s)")
            % (elevation, e, n)
        )
        return alt

    agl = float(alt - ground_elev)

    return agl


def report_overlap_stats(overlaps, photos, output_file):
    """Write overlap statistics to a CSV file."""
    headers = ["photo1", "photo2", "overlap"]
    if output_file:
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for i, ov in enumerate(overlaps):
                writer.writerow([photos[i], photos[i + 1], f"{ov:.2f}"])

    else:
        print(",".join(headers))
        for i, ov in enumerate(overlaps):
            print(f"{photos[i]},{photos[i + 1]},{ov:.2f}")


def main():
    options, flags = gs.parser()
    indir = options["input"]
    elevation = options["elevation"]
    overlap_raster = options["overlap_raster"]
    outcsv = options["overlap_stats"]
    footprint_vector = options["footprint_vector"]
    overlap = flags["c"]

    photos = sorted(glob.glob(os.path.join(indir, "*.[jJ][pP][gG]")))
    gs.message(_("Found {} photos in '{}'").format(len(photos), indir))

    coords = []
    metadata = []

    gs.verbose(_("Creating transformer for reprojection..."))
    transformer = create_transformer()

    gs.verbose(_("Gathering photo metadata and calculating GSD..."))
    for i, img in enumerate(photos):
        exif = get_exif(img)
        gs.verbose(_("Processing '{}'...").format(img))

        (
            iso,
            shutter_speed,
            aperture,
            image_width,
            image_height,
            exposure_time,
            original_datetime,
        ) = get_photo_specs(exif)
        camera_make, camera_model, camera_lens = get_camera_details(exif)

        gps = get_coords(exif)
        if not gps:
            continue
        lon, lat, alt = gps

        ts = parse_exif_datetime(exif)

        e, n = transformer.transform(lon, lat)  # reproject lon/lat
        coords.append((e, n))

        focal_length_mm = get_focal_length(exif)

        sensor_size = compute_sensor_size(exif)

        agl = get_above_ground_level_alt(e, n, alt, elevation)
        gsd_w, gsd_h, gsd_avg = compute_gsd(exif, agl, focal_length_mm, sensor_size)
        gs.debug(
            f"GSD: width={gsd_w:.2f} m/px, height={gsd_h:.2f} m/px, "
            f"average={gsd_avg:.2f} m/px"
        )
        ground_elev = alt - agl  # ground elevation in meters
        gs.debug(f"Altitude: {alt} m, AGL: {agl} m, ground elevation: {ground_elev} m")

        yaw, pitch, roll = get_orientation(exif)

        footprint_w, footprint_h = get_footprint_dimensions(gsd_w, gsd_h, exif)

        image_metadata = {
            "iso": iso,
            "shutter_speed": shutter_speed,
            "aperture": aperture,
            "iamge_width": image_width,
            "image_height": image_height,
            "exposure_time": exposure_time,
            "original_datetime": original_datetime,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "camera_lens": camera_lens,
            "width": footprint_w,
            "height": footprint_h,
            "focal_length": focal_length_mm,
            "sensor_size_w": sensor_size[0],
            "sensor_size_h": sensor_size[1],
            "gsd_w": gsd_w,
            "gsd_h": gsd_h,
            "gsd_avg": gsd_avg,
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "easting": e,
            "northing": n,
            "lon": lon,
            "lat": lat,
            "alt": alt,
            "agl": agl,
            "ground_elev": ground_elev,
            "exif": exif,
            "filename": os.path.basename(img),
            "timestamp": ts,
            "category": i + 1,  # category ID for vector feature
        }

        metadata.append(image_metadata)

    gs.verbose(_("Metadata collected for all photos"))

    photos_by_line_heading = compute_headings_from_gps(metadata)
    for img in photos_by_line_heading:
        footprint = make_footprint_basic(
            img["easting"],
            img["northing"],
            img["agl"],
            img["ground_elev"],
            img["focal_length"],
            img["sensor_size_w"],
            img["sensor_size_h"],
            img["iamge_width"],
            img["image_height"],
            img["yaw"],
        )
        img["footprint"] = footprint
        if not footprint:
            gs.warning(
                _("No footprint created for <{}>, skipping...").format(img["filename"])
            )

        feature = create_vector_feature(img)
        img["feature"] = feature

    if not coords:
        gs.fatal(_("No GPS data found"))

    if footprint_vector:
        gs.message(_("Writing footprint vector map <{}>...").format(footprint_vector))
        write_vector(photos_by_line_heading, footprint_vector)

    if overlap:
        gs.message(_("Calculating overlaps..."))
        overlaps = calculate_overlaps(coords, "tmp_overlaps")
        avg_overlap = sum(overlaps) / len(overlaps)
        gs.message(_("Average overlap: {:.2f}").format(avg_overlap))
        report_overlap_stats(overlaps, photos, outcsv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
