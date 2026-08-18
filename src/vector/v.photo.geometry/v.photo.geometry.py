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
# %option
# % key: sensor
# % type: double
# % required: no
# % multiple: yes
# % key_desc: width,height
# % label: Camera sensor dimensions in mm (width,height)
# % description: Overrides the sensor size estimated from image metadata
# %end
#
# %option
# % key: time_gap
# % type: double
# % required: no
# % answer: 30.0
# % label: Time gap in seconds that splits a flight into separate segments
# % description: Images separated by more than this gap do not inform each other's estimated heading
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
# % key: footprints
# % required: no
# % description: Output vector map of image footprint areas
# %end
#
# %option G_OPT_V_OUTPUT
# % key: stations
# % required: no
# % description: Output 3D vector map of camera station points
# %end
#
# %rules
# % required: footprints,stations
# %end
#
# %flag
# % key: c
# % description: Calculate overlaps between consecutive footprints
# %end

import sys
import os
import math
import csv
import json
import shutil
import subprocess
from datetime import datetime

import numpy as np

import grass.script as gs
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Boundary, Centroid, Point
from grass.pygrass.modules import Module

EXIFTOOL_MIN_VERSION = 12.0
IMAGE_EXTENSIONS = ("jpg", "jpeg", "tif", "tiff", "dng")


def find_exiftool():
    """Return the ExifTool executable path, aborting if unusable."""
    exe = shutil.which("exiftool")
    if not exe:
        gs.fatal(
            _(
                "ExifTool is required but was not found on PATH. "
                "Install it from https://exiftool.org/ "
                "(Debian/Ubuntu: apt install libimage-exiftool-perl, "
                "Fedora: dnf install perl-Image-ExifTool, "
                "macOS: brew install exiftool)."
            )
        )
    version = subprocess.run(
        [exe, "-ver"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if float(version) < EXIFTOOL_MIN_VERSION:
        gs.fatal(
            _("ExifTool >= {} is required, found version {}").format(
                EXIFTOOL_MIN_VERSION, version
            )
        )
    gs.debug(f"Using ExifTool {version} at {exe}")
    return exe


def read_metadata(exiftool, directory):
    """Read metadata for all images under a directory with one ExifTool call.

    Returns a list of tag dictionaries sorted by source path. Numeric tags
    are returned unformatted (-n): GPS as signed decimal degrees, rationals
    as floats.
    """
    cmd = [exiftool, "-json", "-n", "-q", "-fast2", "-r"]
    for ext in IMAGE_EXTENSIONS:
        cmd += ["-ext", ext]
    cmd.append(directory)
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Exit code 1 means some files could not be read; usable output remains.
    if result.returncode not in (0, 1):
        gs.fatal(
            _("ExifTool failed reading '{}': {}").format(
                directory, result.stderr.strip()
            )
        )
    if not result.stdout.strip():
        return []
    records = json.loads(result.stdout)
    records.sort(key=lambda r: r["SourceFile"])
    return records


def as_float(value, default=None):
    """Coerce an ExifTool value to float; some tags arrive as strings."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_coords(exif):
    """Return lon, lat, alt if available."""
    lat = exif.get("GPSLatitude")
    lon = exif.get("GPSLongitude")
    alt = exif.get("GPSAltitude")
    gs.debug(f"GPS altitude ref: {exif.get('GPSAltitudeRef', 'N/A')}")
    if lat is None or lon is None or not alt:
        return None
    return lon, lat, alt


def parse_exif_datetime(exif):
    """Return the exposure time as a datetime, preferring subsecond
    precision and timezone offset when present."""
    value = None
    for key in ("SubSecDateTimeOriginal", "DateTimeOriginal", "CreateDate"):
        value = exif.get(key)
        if value:
            break
    if not value:
        return None
    value = str(value)
    for fmt in (
        "%Y:%m:%d %H:%M:%S.%f%z",
        "%Y:%m:%d %H:%M:%S%z",
        "%Y:%m:%d %H:%M:%S.%f",
        "%Y:%m:%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    gs.warning(_("Could not parse timestamp '{}'").format(value))
    return None


def get_camera_serial(exif):
    """Return an identifier for the camera body.

    Multi-camera rigs (e.g. paired obliques) fire simultaneously against a
    single GPS record, so images must be grouped per body before track
    analysis. Falls back to the camera model when no serial is recorded.
    """
    serial = exif.get("SerialNumber") or exif.get("BodySerialNumber")
    return str(serial) if serial else exif.get("Model", "unknown")


def group_by_camera(images):
    """Group images by camera body identifier."""
    groups = {}
    for img in images:
        groups.setdefault(img["camera_serial"], []).append(img)
    return groups


def split_on_time_gaps(images, gap_threshold=30.0):
    """Split a chronologically sorted image list at large time gaps.

    A gap larger than gap_threshold seconds between consecutive exposures
    is treated as a break between flight segments (turnaround, repositioning,
    or a separate sortie), so track analysis does not connect across it.
    """
    if not images:
        return []
    segments = [[images[0]]]
    for img in images[1:]:
        previous = segments[-1][-1]
        if (img["timestamp"] - previous["timestamp"]).total_seconds() > gap_threshold:
            segments.append([])
        segments[-1].append(img)
    return segments


# Neighbors closer than this (meters) give no usable heading baseline
MIN_HEADING_BASELINE = 0.05


def planar_distance(img1, img2):
    """Distance between two camera positions in the projected CRS (m)."""
    return math.hypot(
        img2["easting"] - img1["easting"], img2["northing"] - img1["northing"]
    )


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


def compute_headings_from_gps(images, time_gap=30.0):
    """Estimate yaw from the GPS track where the metadata has none.

    Images are grouped per camera body, split into flight segments at time
    gaps, and walked chronologically. Yaw for interior images is the circular
    mean of the headings from the previous and to the next position with a
    usable baseline. Each image is tagged with its segment index.
    """
    for group in group_by_camera(images).values():
        group.sort(key=lambda img: img["timestamp"])
        for seg_index, segment in enumerate(split_on_time_gaps(group, time_gap)):
            _estimate_segment_headings(segment, seg_index)
    return images


def _estimate_segment_headings(segment, seg_index):
    n = len(segment)
    for i, img in enumerate(segment):
        img["segment"] = seg_index
        if img.get("yaw") is not None:
            continue  # keep yaw recorded by the camera

        prev_img = next(
            (
                segment[j]
                for j in range(i - 1, -1, -1)
                if planar_distance(segment[j], img) > MIN_HEADING_BASELINE
            ),
            None,
        )
        next_img = next(
            (
                segment[j]
                for j in range(i + 1, n)
                if planar_distance(img, segment[j]) > MIN_HEADING_BASELINE
            ),
            None,
        )

        if prev_img and next_img:
            img["yaw"] = circular_mean([heading(prev_img, img), heading(img, next_img)])
        elif prev_img:
            img["yaw"] = heading(prev_img, img)
        elif next_img:
            img["yaw"] = heading(img, next_img)
        else:
            img["yaw"] = 0.0  # single stationary camera, no track


def get_focal_length(exif):
    """Return focal length in mm from EXIF data."""
    focal = exif.get("FocalLength")
    if not focal:
        return 0.1
    focal_mm = float(focal)
    return focal_mm


# Diagonal of a full-frame 36 x 24 mm sensor, the 35 mm equivalence reference
FULL_FRAME_DIAGONAL_MM = 43.26661

# FocalPlaneResolutionUnit codes to mm per unit (EXIF 2.32, table 6)
RESOLUTION_UNIT_TO_MM = {2: 25.4, 3: 10.0, 4: 1.0, 5: 0.001}


def compute_sensor_size(exif, override=None):
    """Estimate the physical sensor size in mm.

    Resolution order: user override, focal plane resolution tags, sensor
    diagonal implied by the 35 mm equivalence scale factor. Returns
    (width_mm, height_mm, source), or None when nothing is available.
    Estimates inherit the precision of the source tags; FocalPlane tags
    are commonly a few percent off the true sensor dimensions.
    """
    if override:
        return override[0], override[1], "user"

    img_w = exif.get("ExifImageWidth") or exif.get("ImageWidth")
    img_h = exif.get("ExifImageHeight") or exif.get("ImageHeight")
    if not img_w or not img_h:
        return None

    fp_x = as_float(exif.get("FocalPlaneXResolution"))
    fp_y = as_float(exif.get("FocalPlaneYResolution"))
    if fp_x and fp_y:
        unit = exif.get("FocalPlaneResolutionUnit", 2)
        conv = RESOLUTION_UNIT_TO_MM.get(unit, 25.4)
        return (img_w / fp_x) * conv, (img_h / fp_y) * conv, "focal plane resolution"

    # ExifTool derives the scale factor from its camera database when the
    # focal plane tags are absent, which is the common case for drones.
    scale = as_float(exif.get("ScaleFactor35efl"))
    if scale:
        diagonal = FULL_FRAME_DIAGONAL_MM / scale
        pixel_diagonal = math.hypot(img_w, img_h)
        return (
            diagonal * img_w / pixel_diagonal,
            diagonal * img_h / pixel_diagonal,
            "35 mm scale factor",
        )

    return None


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
    yaw = (
        exif.get("FlightYawDegree")
        or exif.get("GimbalYawDegree")
        or exif.get("GPSImgDirection")
    )
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
    lens = exif.get("LensModel") or str(exif.get("LensID", "Unknown"))
    gs.debug(_("Camera: %s %s, Lens: %s") % (make, model, lens))
    return make, model, lens


def get_photo_specs(exif):
    """Extract photo specifications from EXIF data."""
    iso = exif.get("ISO")
    shutter_speed = as_float(exif.get("ShutterSpeedValue"), 0.0)
    aperture = as_float(exif.get("FNumber"))
    image_width = exif.get("ExifImageWidth") or exif.get("ImageWidth")
    image_height = exif.get("ExifImageHeight") or exif.get("ImageHeight")
    exposureTime = as_float(exif.get("ExposureTime"))
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


ATTR_COLUMNS = [
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
    ("camera_serial", "TEXT"),
]

# Metadata keys in ATTR_COLUMNS order (after cat)
ATTR_KEYS = [
    "filename",
    "focal_length",
    "sensor_size_w",
    "sensor_size_h",
    "gsd_w",
    "gsd_h",
    "gsd_avg",
    "yaw",
    "pitch",
    "roll",
    "lon",
    "lat",
    "alt",
    "agl",
    "iso",
    "shutter_speed",
    "aperture",
    "iamge_width",
    "image_height",
    "exposure_time",
    "original_datetime",
    "camera_make",
    "camera_model",
    "camera_lens",
    "camera_serial",
]


def build_attrs(image_metadata):
    """Return the attribute tuple for one image in column order."""
    return tuple(image_metadata[key] for key in ATTR_KEYS)


def validate_attrs(attrs):
    """Check attribute count and types against ATTR_COLUMNS; None is a NULL."""
    expected = len(ATTR_COLUMNS) - 1  # cat is assigned by the writer
    if len(attrs) != expected:
        gs.fatal(
            _("Attribute count mismatch: expected {}, got {}").format(
                expected, len(attrs)
            )
        )
    for value, (name, col_type) in zip(attrs, ATTR_COLUMNS[1:]):
        if value is None:
            continue
        if col_type == "INTEGER" and not isinstance(value, int):
            gs.fatal(
                _("Attribute {} should be INTEGER, got {}").format(
                    name, type(value).__name__
                )
            )
        elif col_type == "DOUBLE" and not isinstance(value, (float, int)):
            gs.fatal(
                _("Attribute {} should be DOUBLE, got {}").format(
                    name, type(value).__name__
                )
            )
        elif col_type == "TEXT" and not isinstance(value, str):
            gs.fatal(
                _("Attribute {} should be TEXT, got {}").format(
                    name, type(value).__name__
                )
            )


def write_footprints(metadata, outmap):
    """Write image footprints as 3D areas with per-image attributes."""
    gs.verbose(
        _("Writing {} footprints to vector map <{}>...").format(len(metadata), outmap)
    )
    with VectorTopo(
        outmap,
        mode="w",
        with_z=True,
        tab_cols=ATTR_COLUMNS,
        layer=1,
        overwrite=True,  # output existence is enforced by the parser
    ) as vect:
        for img in metadata:
            if not img["footprint"]:
                continue
            attrs = build_attrs(img)
            validate_attrs(attrs)
            boundary = Boundary(points=[Point(x, y, z) for x, y, z in img["footprint"]])
            vect.write(boundary)
            centroid = Centroid(
                x=img["easting"], y=img["northing"], z=img["ground_elev"]
            )
            vect.write(centroid, cat=img["category"], attrs=attrs)
        vect.table.conn.commit()
        vect.build()
    gs.vector_history(outmap)


def write_stations(metadata, outmap):
    """Write camera positions as 3D points with per-image attributes."""
    gs.verbose(
        _("Writing {} camera stations to vector map <{}>...").format(
            len(metadata), outmap
        )
    )
    with VectorTopo(
        outmap,
        mode="w",
        with_z=True,
        tab_cols=ATTR_COLUMNS,
        layer=1,
        overwrite=True,  # output existence is enforced by the parser
    ) as vect:
        for img in metadata:
            attrs = build_attrs(img)
            validate_attrs(attrs)
            point = Point(x=img["easting"], y=img["northing"], z=img["alt"])
            vect.write(point, cat=img["category"], attrs=attrs)
        vect.table.conn.commit()
        vect.build()
    gs.vector_history(outmap)


def create_transformer():
    """Reproject list of (lon,lat) coords from WGS84 to GRASS CRS."""
    try:
        from pyproj import CRS, Transformer
    except ImportError:
        gs.fatal(_("pyproj is required, install it with: pip install pyproj"))
    grass_proj = gs.read_command("g.proj", flags="jf")  # PROJ string
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
    alt = float(alt) if alt is not None else 0.0
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
    footprints = options["footprints"]
    stations = options["stations"]
    overlap = flags["c"]

    exiftool = find_exiftool()
    gs.verbose(_("Reading image metadata with ExifTool..."))
    records = read_metadata(exiftool, indir)
    if not records:
        gs.fatal(_("No images found in '{}'").format(indir))
    photos = [record["SourceFile"] for record in records]
    gs.message(_("Found {} photos in '{}'").format(len(photos), indir))

    sensor_override = None
    if options["sensor"]:
        values = [float(value) for value in options["sensor"].split(",")]
        if len(values) != 2 or values[0] <= 0 or values[1] <= 0:
            gs.fatal(_("sensor= requires two positive values: width,height"))
        sensor_override = (values[0], values[1])
    reported_sensors = set()

    coords = []
    metadata = []

    gs.verbose(_("Creating transformer for reprojection..."))
    transformer = create_transformer()

    gs.verbose(_("Gathering photo metadata and calculating GSD..."))
    for i, exif in enumerate(records):
        img = exif["SourceFile"]
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
        camera_serial = get_camera_serial(exif)

        gps = get_coords(exif)
        if not gps:
            continue
        lon, lat, alt = gps

        ts = parse_exif_datetime(exif)

        e, n = transformer.transform(lon, lat)  # reproject lon/lat
        coords.append((e, n))

        focal_length_mm = get_focal_length(exif)

        sensor = compute_sensor_size(exif, sensor_override)
        if sensor is None:
            gs.fatal(
                _(
                    "Cannot determine sensor size for <{}>; "
                    "provide it with sensor=width,height"
                ).format(os.path.basename(img))
            )
        sensor_size = sensor[:2]
        if camera_model not in reported_sensors:
            reported_sensors.add(camera_model)
            gs.message(
                _("Sensor size for {}: {:.2f} x {:.2f} mm ({})").format(
                    camera_model, sensor_size[0], sensor_size[1], sensor[2]
                )
            )

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
            "camera_serial": camera_serial,
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

    photos_by_line_heading = compute_headings_from_gps(
        metadata, time_gap=float(options["time_gap"])
    )
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

    if not coords:
        gs.fatal(_("No GPS data found"))

    if footprints:
        gs.message(_("Writing footprint vector map <{}>...").format(footprints))
        write_footprints(photos_by_line_heading, footprints)

    if stations:
        gs.message(_("Writing camera station map <{}>...").format(stations))
        write_stations(photos_by_line_heading, stations)

    if overlap:
        gs.message(_("Calculating overlaps..."))
        overlaps = calculate_overlaps(coords, "tmp_overlaps")
        avg_overlap = sum(overlaps) / len(overlaps)
        gs.message(_("Average overlap: {:.2f}").format(avg_overlap))
        report_overlap_stats(overlaps, photos, outcsv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
