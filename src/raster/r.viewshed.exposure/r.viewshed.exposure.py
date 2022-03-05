#!/usr/bin/env python3

"""
MODULE:       r.viewshed.exposure

AUTHOR(S):    Zofie Cimburova, Stefan Blumentrath

PURPOSE:      Computes visual exposure to defined exposure source using
              weighted parametrised cummulative viewshed analysis

COPYRIGHT:    (C) 2022 by Zofie Cimburova, Stefan Blumentrath, and the GRASS
              GIS Development Team

REFERENCES:   Cimburova, Z., Blumentrath, S., 2022. Viewshed-based modelling of
              visual exposure to urban greenery - an efficient GIS tool for
              practical appliactions (in press). Landscape and Urban Planning.

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

# %module
# % label: Visual exposure to defined exposure source.
# % description: Computes visual exposure to defined exposure source using weighted parametrised cummulative viewshed analysis.
# % keyword: raster
# % keyword: viewshed
# % keyword: line of sight
# % keyword: LOS
# % keyword: visual exposure
# %end

# %option G_OPT_R_INPUT
# % label: Name of input digital surface raster map
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Name of output raster map of visual exposure
# %end

# %option G_OPT_R_INPUT
# % key: source
# % required: no
# % label: Name of input raster map of exposure source
# % guisection: Exposure source
# %end

# %option
# % key: sourcecat
# % type: string
# % key_desc: value
# % label: Raster values to use as exposure source
# % description: 1-
# % answer: *
# % guisection: Exposure source
# %end

# %option G_OPT_V_INPUT
# % key: sampling_points
# % required: no
# % label: Name of input vector map of sampling points
# % guisection: Exposure source
# %end

# %rules
# % required: sampling_points,source
# %end

# %rules
# % exclusive: sampling_points,source
# %end

# %option G_OPT_R_INPUT
# % key: weights
# % required: no
# % label: Name of input raster map of viewshed weights
# % guisection: Exposure source
# %end

# %flag
# % key: c
# % label: Consider the curvature of the earth (current ellipsoid)
# % guisection: Viewshed
# %end

# %option
# % key: observer_elevation
# % type: double
# % required: no
# % key_desc: value
# % label: Observer elevation above the ground
# % description: 0.0-
# % options: 0.0-
# % answer: 1.5
# % guisection: Viewshed
# %end

# %option
# % key: range
# % type: double
# % required: no
# % key_desc: value
# % label: Exposure range
# % description: 0.0- , -1 for infinity
# % options: 0.0-
# % answer: 100
# % guisection: Viewshed
# %end

# %option
# % key: function
# % type: string
# % required: no
# % key_desc: name
# % label: Viewshed parametrisation function
# % description: Binary, Distance_decay, Fuzzy_viewshed, Visual_magnitude, Solid_angle
# % options: Binary, Distance_decay, Fuzzy_viewshed, Visual_magnitude, Solid_angle
# % answer: Distance_decay
# % guisection: Viewshed
# %end

# %option
# % key: b1_distance
# % type: double
# % required: no
# % key_desc: value
# % label: Radius around the observer where clarity is perfect. Used in fuzzy viewshed function.
# % guisection: Viewshed
# % answer: 10
# %end

# %option
# % key: sample_density
# % type: double
# % required: no
# % key_desc: value
# % label: Density of sampling points
# % options: 0.0-100.0
# % description: 0.0-100.0
# % answer: 25
# % guisection: Sampling
# %end

# %option
# % key: seed
# % type: integer
# % required: no
# % key_desc: value
# % label: Random seed, default [random]
# % options: 0-
# % description: 0-
# % guisection: Sampling
# %end

# %flag
# % key: r
# % label: Consider the effect of atmospheric refraction
# % guisection: Refraction
# %end

# %option
# % key: refraction_coeff
# % type: double
# % required: no
# % key_desc: value
# % label: Refraction coefficient
# % options: 0.0-1.0
# % description: 0.0-1.0
# % answer: 0.14286
# % guisection: Refraction
# %end

# %option G_OPT_M_MEMORY
# %end

# %option G_OPT_M_NPROCS
# %end

import os
import math
import atexit
import sys
import subprocess
from multiprocessing import Pool
from copy import deepcopy
import numpy as np
import itertools

from grass.pygrass.gis import Mapset
from grass.pygrass.raster import RasterRow
from grass.pygrass.raster import raster2numpy
from grass.pygrass.raster import numpy2raster

from grass.pygrass.gis.region import Region
from grass.pygrass.vector.basic import Bbox

import grass.script as grass
from grass.script import utils as grassutils


# Declare global variables
# random name of binary viewshed
TEMPNAME = grass.tempname(12)


def cleanup():
    """Remove raster and vector maps stored in a list"""
    grass.run_command(
        "g.remove",
        flags="f",
        type="raster,vector",
        pattern="{}_*".format(TEMPNAME),
        quiet=True,
        stderr=subprocess.PIPE,
    )

    # Reset mask if user MASK was present
    if (
        RasterRow("MASK", Mapset().name).exist()
        and RasterRow("MASK_{}".format(TEMPNAME)).exist()
    ):
        grass.run_command("r.mask", flags="r", quiet=True)
    reset_mask()


def unset_mask():
    """Deactivate user mask"""
    if RasterRow("MASK", Mapset().name).exist():
        grass.run_command(
            "g.copy",
            quiet=True,
            raster="MASK,MASK_{}".format(TEMPNAME),
            stderr=subprocess.DEVNULL,
            errors="ignore",
        )
        grass.run_command(
            "g.remove",
            quiet=True,
            type="raster",
            name="MASK",
            stderr=subprocess.DEVNULL,
            flags="f",
            errors="ignore",
        )


def reset_mask():
    """Re-activate user mask"""
    if RasterRow("MASK_{}".format(TEMPNAME)).exist():
        grass.warning("Reseting mask")
        grass.run_command(
            "g.copy",
            quiet=True,
            raster="MASK_{},MASK".format(TEMPNAME),
            stderr=subprocess.DEVNULL,
            errors="ignore",
        )
        grass.run_command(
            "g.remove",
            quiet=True,
            type="raster",
            name="MASK_{}".format(TEMPNAME),
            stderr=subprocess.DEVNULL,
            flags="f",
            errors="ignore",
        )


def clean_temp(pid):
    """Remove temporary files of the current processes
    :param pid: Process ID whos tempfiles to remove
    :type pid: int
    """
    from pathlib import Path
    from shutil import rmtree

    tempfile = Path(grass.tempfile(create=False))
    for path in tempfile.parent.glob(str(pid) + ".*"):
        if path.is_file():
            grassutils.try_rmdir(path)
        else:
            rmtree(path)


def do_it_all(global_vars, target_pts_np):
    """Conduct weighted and parametrised partial viewshed and cummulate it with
    the previous partial viewsheds
    :param target_pts_np: Array of target points in global coordinate system
    :type target_pts_np: ndarray
    :return: 2D array of weighted parametrised cummulative viewshed
    :rtype: ndarray
    """
    # Set counter
    counter = 1

    # Get variables out of global_vars dictionary
    reg = global_vars["region"]
    exp_range = global_vars["range"]
    flagstring = global_vars["flagstring"]
    r_dsm = global_vars["r_dsm"]
    v_elevation = global_vars["observer_elevation"]
    refr_coeff = global_vars["refr_coeff"]
    memory = global_vars["memory"]
    parametrise_viewshed = global_vars["param_viewshed"]
    dsm_type = global_vars["dsm_type"]
    b_1 = global_vars["b_1"]
    cores = global_vars["cores"]
    tempname = global_vars["tempname"]

    # Create empty viewshed
    np_cum = np.empty((reg.rows, reg.cols), dtype=np.single)
    np_cum[:] = np.nan
    tmp_vs = "{}_{}".format(tempname, os.getpid())

    for target_pnt in target_pts_np:

        # Display a progress info message
        grass.percent(counter, len(target_pts_np), 1)
        grass.verbose(
            "Processing point {i} ({p:.1%})".format(
                i=int(target_pnt[0]), p=counter / len(target_pts_np)
            )
        )

        # Global coordinates and attributes of target point T
        t_glob = target_pnt[1:]

        # ======================================================================
        # 1. Set local computational region: +/- exp_range from target point
        # ======================================================================
        # ensure that local region doesn't exceed global region
        loc_reg_n = min(t_glob[1] + exp_range + reg.nsres / 2, reg.north)
        loc_reg_s = max(t_glob[1] - exp_range - reg.nsres / 2, reg.south)
        loc_reg_e = min(t_glob[0] + exp_range + reg.ewres / 2, reg.east)
        loc_reg_w = max(t_glob[0] - exp_range - reg.ewres / 2, reg.west)

        # pygrass sets region for pygrass tasks
        lreg = deepcopy(reg)
        lreg.set_bbox(Bbox(loc_reg_n, loc_reg_s, loc_reg_e, loc_reg_w))
        lreg.set_raster_region()

        # Create processing environment with region information
        c_env = os.environ.copy()
        c_env["GRASS_REGION"] = grass.region_env(
            n=loc_reg_n, s=loc_reg_s, e=loc_reg_e, w=loc_reg_w
        )

        lreg_shape = [lreg.rows, lreg.cols]

        # ======================================================================
        # 2. Calculate binary viewshed and convert to numpy
        # ======================================================================
        vs = grass.pipe_command(
            "r.viewshed",
            flags="b" + flagstring,
            input=r_dsm,
            output=tmp_vs,
            coordinates="{},{}".format(t_glob[0], t_glob[1]),
            observer_elevation=0.0,
            target_elevation=v_elevation,
            max_distance=exp_range,
            refraction_coeff=refr_coeff,
            memory=int(round(memory / cores)),
            quiet=True,
            overwrite=True,
            env=c_env,
        )
        vs.communicate()
        # Workaround for https://github.com/OSGeo/grass/issues/1436
        clean_temp(vs.pid)

        # Read viewshed into numpy with single precision and replace NoData
        np_viewshed = raster2numpy(tmp_vs).astype(np.single)
        np_viewshed[np_viewshed == -2147483648] = np.nan

        # ======================================================================
        # 3. Prepare local coordinates and attributes of target point T
        # ======================================================================
        # Calculate how much of rows/cols of local region lies
        # outside global region
        o_1 = [
            max(t_glob[1] + exp_range + reg.nsres / 2 - reg.north, 0),
            max(reg.west - (t_glob[0] - exp_range - reg.ewres / 2), 0),
        ]

        t_loc = np.append(
            np.array(
                [
                    exp_range / reg.nsres + 0.5 - o_1[0] / reg.nsres,
                    exp_range / reg.ewres + 0.5 - o_1[1] / reg.ewres,
                ]
            ),
            t_glob[2:],
        )

        # ======================================================================
        # 4. Parametrise viewshed
        # ======================================================================
        np_viewshed = parametrise_viewshed(
            lreg_shape,
            t_loc,
            np_viewshed,
            reg,
            exp_range,
            r_dsm,
            dsm_type,
            v_elevation,
            b_1,
        ).astype(np.single)

        # ======================================================================
        # 5. Cummulate viewsheds
        # ======================================================================
        # Determine position of local parametrised viewshed within
        # global cummulative viewshed
        o_2 = [
            int(round((reg.north - loc_reg_n) / reg.nsres)),  # NS (rows)
            int(round((loc_reg_w - reg.west) / reg.ewres)),  # EW (cols)
        ]

        # Add local parametrised viewshed to global cummulative viewshed
        # replace nans with 0 in processed regions, keep nan where both are nan
        all_nan = np.all(
            np.isnan(
                [
                    np_cum[
                        o_2[0] : o_2[0] + lreg_shape[0], o_2[1] : o_2[1] + lreg_shape[1]
                    ],
                    np_viewshed,
                ]
            ),
            axis=0,
        )

        np_cum[
            o_2[0] : o_2[0] + lreg_shape[0], o_2[1] : o_2[1] + lreg_shape[1]
        ] = np.nansum(
            [
                np_cum[
                    o_2[0] : o_2[0] + lreg_shape[0], o_2[1] : o_2[1] + lreg_shape[1]
                ],
                np_viewshed,
            ],
            axis=0,
        )

        np_cum[o_2[0] : o_2[0] + lreg_shape[0], o_2[1] : o_2[1] + lreg_shape[1]][
            all_nan
        ] = np.nan

        counter += 1

    return np_cum


def binary(
    lreg_shape, t_loc, np_viewshed, reg, exp_range, r_dsm, dsm_type, v_elevation, b_1
):
    """Weight binary viewshed by constant weight
    :param lreg_shape: Dimensions of local computational region
    :type lreg_shape: list
    :param t_loc: Array of target point coordinates in local coordinate system
    :type t_loc: ndarray
    :param np_viewshed: 2D array of binary viewshed
    :type np_viewshed: ndarray
    :param reg: computational region
    :type reg: Region()
    :param exp_range: exposure range
    :type reg: float
    :param r_dsm: Name of digital surface model raster
    :type r_dsm: string
    :param dsm_type: Raster map precision type
    :type dsm_type: string
    :param v_elevation: Observer height
    :type v_elevation: float
    :param b_1: radius in fuzzy viewshed parametrisation
    :type b_1: float
    :return: 2D array of weighted viewshed
    :rtype: ndarray
    """

    return np_viewshed * t_loc[-1]


def solid_angle_reverse(
    lreg_shape, t_loc, np_viewshed, reg, exp_range, r_dsm, dsm_type, v_elevation, b_1
):
    """Calculate solid angle from viewpoints to target based on
    Domingo-Santos et al. (2011) and use it to parametrise binary viewshed
    :param lreg_shape: Dimensions of local computational region
    :type lreg_shape: list
    :param t_loc: Array of target point coordinates in local coordinate system
    :type t_loc: ndarray
    :param np_viewshed: 2D array of binary viewshed
    :type np_viewshed: ndarray
    :param reg: computational region
    :type reg: Region()
    :param exp_range: exposure range
    :type reg: float
    :param r_dsm: Name of digital surface model raster
    :type r_dsm: string
    :param dsm_type: Raster map precision type
    :type dsm_type: string
    :param v_elevation: Observer height
    :type v_elevation: float
    :param b_1: radius in fuzzy viewshed parametrisation
    :type b_1: float
    :return: 2D array of weighted parametrised viewshed
    :rtype: ndarray
    """
    # 1. Convert DSM to numpy
    np_dsm = raster2numpy(r_dsm)

    # Ensure that values are represented as float (in case of CELL
    # data type) and replace integer NaN with numpy NaN
    if dsm_type == "CELL":
        np_dsm = np_dsm.astype(np.float32)
        np_dsm[np_dsm == -2147483648] = np.nan

    # 2. local row, col coordinates and global Z coordinate of observer points V
    #    3D array (lreg_shape[0] x lreg_shape[1] x 3)
    v_loc = np.array(
        [
            np.tile(
                np.arange(0.5, lreg_shape[0] + 0.5).reshape(-1, 1), (1, lreg_shape[1])
            ),
            np.tile(
                np.arange(0.5, lreg_shape[1] + 0.5).reshape(-1, 1).transpose(),
                (lreg_shape[0], 1),
            ),
            np_dsm + v_elevation,
        ]
    )

    # 3. local row, col coordinates and global Z coordinate of points A, B, C, D
    #    1D array [row, col, Z]
    a_loc = np.array([t_loc[0] + 0.5, t_loc[1] - 0.5, t_loc[3]])

    b_loc = np.array([t_loc[0] - 0.5, t_loc[1] - 0.5, t_loc[4]])

    c_loc = np.array([t_loc[0] - 0.5, t_loc[1] + 0.5, t_loc[5]])

    d_loc = np.array([t_loc[0] + 0.5, t_loc[1] + 0.5, t_loc[6]])

    # 4. vectors a, b, c, d, adjusted for cell size
    #    3D array (lreg_shape[0] x lreg_shape[1] x 3)
    a_vect = np.array(
        [
            (v_loc[0] - a_loc[0]) * reg.nsres,
            (v_loc[1] - a_loc[1]) * reg.ewres,
            (v_loc[2] - a_loc[2]),
        ]
    )

    b_vect = np.array(
        [
            (v_loc[0] - b_loc[0]) * reg.nsres,
            (v_loc[1] - b_loc[1]) * reg.ewres,
            (v_loc[2] - b_loc[2]),
        ]
    )

    c_vect = np.array(
        [
            (v_loc[0] - c_loc[0]) * reg.nsres,
            (v_loc[1] - c_loc[1]) * reg.ewres,
            (v_loc[2] - c_loc[2]),
        ]
    )

    d_vect = np.array(
        [
            (v_loc[0] - d_loc[0]) * reg.nsres,
            (v_loc[1] - d_loc[1]) * reg.ewres,
            (v_loc[2] - d_loc[2]),
        ]
    )

    # 5. sizes of vectors a, b, c, d
    #    2D array (lreg_shape[0] x lreg_shape[1])
    a_scal = np.sqrt(a_vect[0] ** 2 + a_vect[1] ** 2 + a_vect[2] ** 2)
    b_scal = np.sqrt(b_vect[0] ** 2 + b_vect[1] ** 2 + b_vect[2] ** 2)
    c_scal = np.sqrt(c_vect[0] ** 2 + c_vect[1] ** 2 + c_vect[2] ** 2)
    d_scal = np.sqrt(d_vect[0] ** 2 + d_vect[1] ** 2 + d_vect[2] ** 2)

    # 6. scalar products ab, ac, bc, ad, dc
    #    2D arrays (lreg_shape[0] x lreg_shape[1])
    ab_scal = sum(a_vect * b_vect)
    ac_scal = sum(a_vect * c_vect)
    bc_scal = sum(b_vect * c_vect)
    ad_scal = sum(a_vect * d_vect)
    dc_scal = sum(d_vect * c_vect)

    # 7. determinants of matrix abc, adc
    #    2D arrays (lreg_shape[0] x lreg_shape[1])
    det_abc = (
        a_vect[0] * (b_vect[1] * c_vect[2] - b_vect[2] * c_vect[1])
        - b_vect[0] * (a_vect[1] * c_vect[2] - a_vect[2] * c_vect[1])
        + c_vect[0] * (a_vect[1] * b_vect[2] - a_vect[2] * b_vect[1])
    )

    det_adc = (
        a_vect[0] * (d_vect[1] * c_vect[2] - d_vect[2] * c_vect[1])
        - d_vect[0] * (a_vect[1] * c_vect[2] - a_vect[2] * c_vect[1])
        + c_vect[0] * (a_vect[1] * d_vect[2] - a_vect[2] * d_vect[1])
    )

    # 8. solid angle
    solid_angle_1 = np.arctan2(
        det_abc,
        a_scal * b_scal * c_scal
        + ab_scal * c_scal
        + ac_scal * b_scal
        + bc_scal * a_scal,
    )

    solid_angle_2 = np.arctan2(
        det_adc,
        a_scal * d_scal * c_scal
        + ad_scal * c_scal
        + ac_scal * d_scal
        + dc_scal * a_scal,
    )

    solid_angle = np.absolute(solid_angle_1) + np.absolute(solid_angle_2)

    # 9. Multiply solid angle by binary viewshed and weight
    return solid_angle * np_viewshed * t_loc[-1]


def distance_decay_reverse(
    lreg_shape, t_loc, np_viewshed, reg, exp_range, r_dsm, dsm_type, v_elevation, b_1
):
    """Calculates distance decay weights to target based on
    Gret-Regamey et al. (2007) and Chamberlain & Meitner (2013) and use these
    to parametrise binary viewshed
    :param lreg_shape: Dimensions of local computational region
    :type lreg_shape: list
    :param t_loc: Array of target point coordinates in local coordinate system
    :type t_loc: ndarray
    :param np_viewshed: 2D array of binary viewshed
    :type np_viewshed: ndarray
    :param reg: computational region
    :type reg: Region()
    :param exp_range: exposure range
    :type reg: float
    :param r_dsm: Name of digital surface model raster
    :type r_dsm: string
    :param dsm_type: Raster map precision type
    :type dsm_type: string
    :param v_elevation: Observer height
    :type v_elevation: float
    :param b_1: radius in fuzzy viewshed parametrisation
    :type b_1: float
    :return: 2D array of weighted parametrised viewshed
    :rtype: ndarray
    """
    # 1. local row, col coordinates of observer points V
    #    2D array (lreg_shape[0] x lreg_shape[1] x 2)
    v_loc = np.array(
        [
            np.tile(
                np.arange(0.5, lreg_shape[0] + 0.5).reshape(-1, 1), (1, lreg_shape[1])
            ),
            np.tile(
                np.arange(0.5, lreg_shape[1] + 0.5).reshape(-1, 1).transpose(),
                (lreg_shape[0], 1),
            ),
        ]
    )

    # 2. vector VT, adjusted for cell size
    #    2D array (lreg_shape[0] x lreg_shape[1])
    v_vect = np.array(
        [(v_loc[0] - t_loc[0]) * reg.nsres, (v_loc[1] - t_loc[1]) * reg.ewres]
    )

    # 3. size of vector VT
    #    2D array (lreg_shape[0] x lreg_shape[1])
    v_scal = np.sqrt(v_vect[0] ** 2 + v_vect[1] ** 2)

    # replace 0 distance for central pixel by resolution to avoid division by 0
    v_scal = np.where(abs(v_scal) < 1e-6, (reg.nsres + reg.ewres) / 2, v_scal)

    # 4. distance decay function
    distance_decay = (reg.nsres * reg.ewres) / (v_scal ** 2)

    # 5. multiply distance decay by binary viewshed and weight
    return distance_decay * np_viewshed * t_loc[-1]


def fuzzy_viewshed_reverse(
    lreg_shape, t_loc, np_viewshed, reg, exp_range, r_dsm, dsm_type, v_elevation, b_1
):
    """Calculates fuzzy viewshed weights from viewpoints to target based on
    Fisher (1994) and use these to parametrise binary viewshed
    :param lreg_shape: Dimensions of local computational region
    :type lreg_shape: list
    :param t_loc: Array of target point coordinates in local coordinate system
    :type t_loc: ndarray
    :param np_viewshed: 2D array of binary viewshed
    :type np_viewshed: ndarray
    :param reg: computational region
    :type reg: Region()
    :param exp_range: exposure range
    :type reg: float
    :param r_dsm: Name of digital surface model raster
    :type r_dsm: string
    :param dsm_type: Raster map precision type
    :type dsm_type: string
    :param v_elevation: Observer height
    :type v_elevation: float
    :param b_1: radius in fuzzy viewshed parametrisation
    :type b_1: float
    :return: 2D array of weighted parametrised viewshed
    :rtype: ndarray
    """
    # 1. local row, col coordinates of observer points V
    #    2D array (lreg_shape[0] x lreg_shape[1] x 2)
    v_loc = np.array(
        [
            np.tile(
                np.arange(0.5, lreg_shape[0] + 0.5).reshape(-1, 1), (1, lreg_shape[1])
            ),
            np.tile(
                np.arange(0.5, lreg_shape[1] + 0.5).reshape(-1, 1).transpose(),
                (lreg_shape[0], 1),
            ),
        ]
    )

    # 2. vector VT, adjusted for cell size
    #    2D array (lreg_shape[0] x lreg_shape[1])
    v_vect = np.array(
        [(v_loc[0] - t_loc[0]) * reg.nsres, (v_loc[1] - t_loc[1]) * reg.ewres]
    )

    # 3. size of vector VT
    #    2D array (lreg_shape[0] x lreg_shape[1])
    v_scal = np.sqrt(v_vect[0] ** 2 + v_vect[1] ** 2)

    # replace 0 distance for central pixel by resolution to avoid division by 0
    v_scal = np.where(abs(v_scal) < 1e-6, (reg.nsres + reg.ewres) / 2, v_scal)

    # 4. fuzzy viewshed function
    fuzzy_viewshed = np.where(
        v_scal <= b_1, 1, 1 / (1 + ((v_scal - b_1) / (exp_range - b_1)) ** 2)
    )

    # 5. Multiply fuzzy viewshed by binary viewshed and weight
    return fuzzy_viewshed * np_viewshed * t_loc[-1]


def visual_magnitude_reverse(
    lreg_shape, t_loc, np_viewshed, reg, exp_range, r_dsm, dsm_type, v_elevation, b_1
):
    """Calculate visual magnitude from viewpoints to target based on
    Chamberlain (2011) and Chamberlain & Meither (2013) and use it to
    parametrise binary viewshed
    :param lreg_shape: Dimensions of local computational region
    :type lreg_shape: list
    :param t_loc: Array of target point coordinates in local coordinate system
    :type t_loc: ndarray
    :param np_viewshed: 2D array of binary viewshed
    :type np_viewshed: ndarray
    :param reg: computational region
    :type reg: Region()
    :param exp_range: exposure range
    :type reg: float
    :param r_dsm: Name of digital surface model raster
    :type r_dsm: string
    :param dsm_type: Raster map precision type
    :type dsm_type: string
    :param v_elevation: Observer height
    :type v_elevation: float
    :param b_1: radius in fuzzy viewshed parametrisation
    :type b_1: float
    :return: 2D array of weighted parametrised viewshed
    :rtype: ndarray
    """
    # 1. Convert DSM to numpy
    np_dsm = raster2numpy(r_dsm)

    # Ensure that values are represented as float (in case of CELL
    # data type) and replace integer NaN with numpy NaN
    dsm_type = grass.parse_command("r.info", map=r_dsm, flags="g")["datatype"]

    if dsm_type == "CELL":
        np_dsm = np_dsm.astype(np.float32)
        np_dsm[np_dsm == -2147483648] = np.nan

    # 2. local row, col coordinates and global Z coordinate of observer points V
    #    3D array (lreg_shape[0] x lreg_shape[1] x 3)
    v_loc = np.array(
        [
            np.tile(
                np.arange(0.5, lreg_shape[0] + 0.5).reshape(-1, 1), (1, lreg_shape[1])
            ),
            np.tile(
                np.arange(0.5, lreg_shape[1] + 0.5).reshape(-1, 1).transpose(),
                (lreg_shape[0], 1),
            ),
            np_dsm + v_elevation,
        ]
    )

    # 3. vector VT, adjusted for cell size
    #    3D array (lreg_shape[0] x lreg_shape[1] x 3)
    v_vect = np.array(
        [
            (v_loc[0] - t_loc[0]) * reg.nsres,
            (v_loc[1] - t_loc[1]) * reg.ewres,
            (v_loc[2] - t_loc[2]),
        ]
    )

    # 4. projection of vector VT to XZ and YZ plane, adjusted for cell size
    v_vect_ns = np.array([(v_loc[0] - t_loc[0]) * reg.nsres, v_loc[2] - t_loc[2]])

    v_vect_ew = np.array([(v_loc[1] - t_loc[1]) * reg.ewres, v_loc[2] - t_loc[2]])

    v_vect_ns_unit = v_vect_ns / np.linalg.norm(v_vect_ns, axis=0)
    v_vect_ew_unit = v_vect_ew / np.linalg.norm(v_vect_ew, axis=0)

    # 5. size of vector VT
    #    2D array (lreg_shape[0] x lreg_shape[1])
    v_scal = np.sqrt(v_vect[0] ** 2 + v_vect[1] ** 2 + v_vect[2] ** 2)
    # replace 0 distance for central pixel by resolution to avoid division by 0
    # v_scal = np.where(abs(v_scal) < 1e-6, (reg.nsres + reg.ewres) / 2, v_scal)
    # grass.verbose(v_scal)

    # 6. vector n, its projection to XZ, YZ plane
    #   1D array [X, Z], [Y, Z]
    #   already unit vector
    n_vect_ns_unit = [np.sin(np.radians(t_loc[4])), np.cos(np.radians(t_loc[4]))]
    n_vect_ew_unit = [np.sin(np.radians(t_loc[3])), np.cos(np.radians(t_loc[3]))]

    # 7. angles beta (ns), theta (ew) (0-90 degrees)
    #    2D array (lreg_shape[0] x lreg_shape[1])
    beta = np.arccos(
        n_vect_ns_unit[0] * v_vect_ns_unit[:][0]
        + n_vect_ns_unit[1] * v_vect_ns_unit[:][1]
    )
    beta = np.where(beta > math.pi / 2, beta - math.pi / 2, beta)

    theta = np.arccos(
        n_vect_ew_unit[0] * v_vect_ew_unit[:][0]
        + n_vect_ew_unit[1] * v_vect_ew_unit[:][1]
    )
    theta = np.where(theta > math.pi / 2, theta - math.pi / 2, theta)

    # 8. visual magnitude adjusted for distance weight
    visual_magnitude = (
        np.cos(beta) * np.cos(theta) * ((reg.nsres * reg.ewres) / (v_scal ** 2))
    )
    sys.stderr.flush()

    # 9. Multiply visual magnitude by binary viewshed and weight
    return visual_magnitude * np_viewshed * t_loc[-1]


def sample_raster_with_points(r_map, cat, density, min_d, v_sample, seed):
    """Random sample exposure source by vector points
    :param r_map: Raster map to be sampled from
    :type r_map: string
    :param cat: Category of raster map to be sampled from
    :type cat: string
    :param density: Sampling density
    :type density: float
    :param min_d: Minimum distance between sampling points
    :type min_d: float
    :param v_sample: Name of output vector map of sampling points
    :type v_sample: string
    :param seed: Random seed
    :param seed: int
    :return: Name of output vector map of sampling points
    :rtype: string
    """
    # mask categories of raster map to be sampled from
    grass.run_command(
        "r.mask",
        raster=r_map,
        maskcats=cat,
        overwrite=True,
        quiet=True,
    )

    # number of non-null cells in map (cells to sample from)
    source_ncells = int(
        grass.parse_command("r.univar", map=r_map, flags="g", quiet=True)["n"]
    )

    # check that input map is not empty
    if source_ncells == 0:
        grass.fatal("The analysis cannot be conducted for 0 sampling points.")

    if density == 100:
        # vectorize source cells directly - no sampling
        grass.verbose("Distributing {} sampling points...".format(source_ncells))

        # vectorize source cells
        v_source_sample = "{}_rand_pts_vect".format(TEMPNAME)
        grass.run_command(
            "r.to.vect",
            flags="b",
            input=r_map,
            output=v_source_sample,
            type="point",
            overwrite=True,
            quiet=True,
            stderr=subprocess.PIPE,
        )

    else:
        # number of cells in sample
        nsample = int(density * source_ncells / 100)

        if nsample == 0:
            grass.fatal("The analysis cannot be conducted for 0 sampling points.")
        else:
            grass.verbose("Distributing {} sampling points...".format(nsample))

        # random sample points - raster
        r_sample = "{}_rand_pts_rast".format(TEMPNAME)
        grass.run_command(
            "r.random.cells",
            output=r_sample,
            ncells=nsample,
            distance=min_d,
            overwrite=True,
            quiet=True,
            seed=seed,
        )

        # vectorize raster of random sample points
        grass.run_command(
            "r.to.vect",
            flags="b",
            input=r_sample,
            output=v_sample,
            type="point",
            overwrite=True,
            quiet=True,
            stderr=subprocess.PIPE,
        )

        # remove random sample points - raster
        grass.run_command(
            "g.remove", flags="f", type="raster", name=r_sample, quiet=True
        )

    # remove mask
    grass.run_command("r.mask", flags="r", quiet=True)

    return v_sample


def txt2numpy(
    tablestring,
    sep=",",
    names=None,
    null_value=None,
    fill_value=None,
    comments="#",
    usecols=None,
    encoding=None,
    structured=True,
):
    """
    Can be removed when the function is included in grass core.
    Read table-like output from grass modules as Numpy array;
    format instructions are handed down to Numpys genfromtxt function
    :param stdout: tabular stdout from GRASS GIS module call
    :type stdout: str|byte
    :param sep: Separator delimiting columns
    :type sep: str
    :param names: List of strings with names for columns
    :type names: list
    :param null_value: Characters representing the no-data value
    :type null_value: str
    :param fill_value: Value to fill no-data with
    :type fill_value: str
    :param comments: Character that identifies comments in the input string
    :type comments: str
    :param usecols: List of columns to import
    :type usecols: list
    :param structured: return structured array if True, un-structured otherwise
    :type structured: bool
    :return: numpy.ndarray
    """

    from io import BytesIO

    if not encoding:
        encoding = grassutils._get_encoding()

    if type(tablestring).__name__ == "str":
        tablestring = grass.encode(tablestring, encoding=encoding)
    elif type(tablestring).__name__ != "bytes":
        grass.fatal("Unsupported data type")

    kwargs = {
        "missing_values": null_value,
        "filling_values": fill_value,
        "usecols": usecols,
        "names": names,
        "delimiter": sep,
        "comments": comments,
    }

    if np.version.version >= "1.14":
        kwargs["encoding"] = encoding

    if structured:
        kwargs["dtype"] = None

    np_array = np.genfromtxt(BytesIO(tablestring), **kwargs)
    return np_array


def main():
    """Do the main work"""

    # set numpy printing options
    np.set_printoptions(formatter={"float": lambda x: "{0:0.2f}".format(x)})

    # ==========================================================================
    # Input data
    # ==========================================================================
    # Required
    r_output = options["output"]
    r_dsm = options["input"]
    dsm_type = grass.parse_command("r.info", map=r_dsm, flags="g")["datatype"]

    # Test if DSM exist
    gfile_dsm = grass.find_file(name=r_dsm, element="cell")
    if not gfile_dsm["file"]:
        grass.fatal("Raster map <{}> not found".format(r_dsm))

    # Exposure settings
    v_source = options["sampling_points"]
    r_source = options["source"]
    source_cat = options["sourcecat"]
    r_weights = options["weights"]

    # test if source vector map exist and contains points
    if v_source:
        gfile_vsource = grass.find_file(name=v_source, element="vector")
        if not gfile_vsource["file"]:
            grass.fatal("Vector map <{}> not found".format(v_source))
        if not grass.vector.vector_info_topo(v_source, layer=1)["points"] > 0:
            grass.fatal("Vector map <{}> does not contain any points.".format(v_source))

    if r_source:
        gfile_rsource = grass.find_file(name=r_source, element="cell")
        if not gfile_rsource["file"]:
            grass.fatal("Raster map <{}> not found".format(r_source))

        # if source_cat is set, check that r_source is CELL
        source_datatype = grass.parse_command("r.info", map=r_source, flags="g")[
            "datatype"
        ]

        if source_cat != "*" and source_datatype != "CELL":
            grass.fatal(
                "The raster map <%s> must be integer (CELL type) in order to \
                use the 'sourcecat' parameter"
                % r_source
            )

    if r_weights:
        gfile_weights = grass.find_file(name=r_weights, element="cell")
        if not gfile_weights["file"]:
            grass.fatal("Raster map <{}> not found".format(r_weights))

    # Viewshed settings
    range_inp = float(options["range"])
    v_elevation = float(options["observer_elevation"])
    b_1 = float(options["b1_distance"])
    pfunction = options["function"]
    refr_coeff = float(options["refraction_coeff"])
    flagstring = ""
    if flags["r"]:
        flagstring += "r"
    if flags["c"]:
        flagstring += "c"

    # test values
    if v_elevation < 0.0:
        grass.fatal("Observer elevation must be larger than or equal to 0.0.")

    if range_inp <= 0.0 and range_inp != -1:
        grass.fatal("Exposure range must be larger than 0.0.")

    if pfunction == "Fuzzy_viewshed" and range_inp == -1:
        grass.fatal(
            "Exposure range cannot be \
            infinity for fuzzy viewshed approch."
        )

    if pfunction == "Fuzzy_viewshed" and b_1 > range_inp:
        grass.fatal(
            "Exposure range must be larger than radius around \
            the viewpoint where clarity is perfect."
        )

    # Sampling settings
    source_sample_density = float(options["sample_density"])
    seed = options["seed"]

    if not seed:  # if seed is not set, set it to process number
        seed = os.getpid()

    # Optional
    cores = int(options["cores"])
    memory = int(options["memory"])

    # ==========================================================================
    # Region settings
    # ==========================================================================
    # check that location is not in lat/long
    if grass.locn_is_latlong():
        grass.fatal("The analysis is not available for lat/long coordinates.")

    # get comp. region parameters
    reg = Region()

    # check that NSRES equals EWRES
    if abs(reg.ewres - reg.nsres) > 1e-6:
        grass.fatal(
            "Variable north-south and east-west 2D grid resolution \
            is not supported"
        )

    # adjust exposure range as a multiplicate of region resolution
    # if infinite, set exposure range to the max of region size
    if range_inp != -1:
        multiplicate = math.floor(range_inp / reg.nsres)
        exp_range = multiplicate * reg.nsres
    else:
        range_inf = max(reg.north - reg.south, reg.east - reg.west)
        multiplicate = math.floor(range_inf / reg.nsres)
        exp_range = multiplicate * reg.nsres

    if RasterRow("MASK", Mapset().name).exist():
        grass.warning("Current MASK is temporarily renamed.")
        unset_mask()

    # ==========================================================================
    # Random sample exposure source with target points T
    # ==========================================================================
    if v_source:
        # go for using input vector map as sampling points
        v_source_sample = v_source
        grass.verbose("Using sampling points from input vector map")

    else:
        # go for sampling

        # min. distance between samples set to half of region resolution
        # (issue in r.random.cells)
        sample_distance = reg.nsres / 2
        v_source_sample = sample_raster_with_points(
            r_source,
            source_cat,
            source_sample_density,
            sample_distance,
            "{}_rand_pts_vect".format(TEMPNAME),
            seed,
        )

    # ==========================================================================
    # Get coordinates and attributes of target points T
    # ==========================================================================
    # Prepare a list of maps to extract attributes from
    # DSM values
    attr_map_list = [r_dsm]

    if pfunction in ["Solid_angle", "Visual_magnitude"]:
        grass.verbose("Precomputing parameter maps...")

    # Precompute values A, B, C, D for solid angle function
    # using moving window [row, col]
    if pfunction == "Solid_angle":
        r_a_z = "{}_A_z".format(TEMPNAME)
        r_b_z = "{}_B_z".format(TEMPNAME)
        r_c_z = "{}_C_z".format(TEMPNAME)
        r_d_z = "{}_D_z".format(TEMPNAME)

        expr = ";".join(
            [
                "$outmap_A = ($inmap[0, 0] + \
                          $inmap[0, -1] + \
                          $inmap[1, -1] + \
                          $inmap[1, 0]) / 4",
                "$outmap_B = ($inmap[-1, 0] + \
                          $inmap[-1, -1] + \
                          $inmap[0, -1] + \
                          $inmap[0, 0]) / 4",
                "$outmap_C = ($inmap[-1, 1] + \
                          $inmap[-1, 0] + \
                          $inmap[0, 0] + \
                          $inmap[0, 1]) / 4",
                "$outmap_D = ($inmap[0, 1] + \
                          $inmap[0, 0] + \
                          $inmap[1, 0] + \
                          $inmap[1, 1]) / 4",
            ]
        )
        grass.mapcalc(
            expr,
            inmap=r_dsm,
            outmap_A=r_a_z,
            outmap_B=r_b_z,
            outmap_C=r_c_z,
            outmap_D=r_d_z,
            overwrite=True,
            quiet=grass.verbosity() <= 1,
        )

        attr_map_list.extend([r_a_z, r_b_z, r_c_z, r_d_z])

    # Precompute values slopes in e-w direction, n-s direction
    # as atan(dz/dx) (e-w direction), atan(dz/dy) (n-s direction)
    # using moving window [row, col]
    elif pfunction == "Visual_magnitude":

        r_slope_ew = "{}_slope_ew".format(TEMPNAME)
        r_slope_ns = "{}_slope_ns".format(TEMPNAME)

        expr = ";".join(
            [
                "$outmap_ew = atan((sqrt(2) * $inmap[-1, 1] + \
                          2 * $inmap[0, 1] + \
                          sqrt(2) * $inmap[1, 1] - \
                          sqrt(2) * $inmap[-1, -1] - \
                          2 * $inmap[0, -1] - \
                          sqrt(2) * $inmap[1, -1]) / \
                          (8 * $w_ew))",
                "$outmap_ns = atan((sqrt(2) * $inmap[-1, -1] + \
                          2 * $inmap[-1, 0] + \
                          sqrt(2) * $inmap[-1, 1] - \
                          sqrt(2) * $inmap[1, -1] - \
                          2 * $inmap[1, 0] - \
                          sqrt(2) * $inmap[1, 1]) / \
                          (8 * $w_ns))",
            ]
        )

        grass.mapcalc(
            expr,
            inmap=r_dsm,
            outmap_ew=r_slope_ew,
            outmap_ns=r_slope_ns,
            w_ew=reg.ewres,
            w_ns=reg.nsres,
            overwrite=True,
            quiet=grass.verbosity() <= 1,
        )

        attr_map_list.extend([r_slope_ew, r_slope_ns])

    # Use viewshed weights if provided
    if r_weights:
        attr_map_list.append(r_weights)

    # Extract attribute values
    target_pts_grass = grass.read_command(
        "r.what",
        flags="v",
        map=attr_map_list,
        points=v_source_sample,
        separator="|",
        null_value="*",
        quiet=True,
    )

    # columns to use depending on parametrization function
    usecols = list(range(0, 4 + len(attr_map_list)))
    usecols.remove(3)  # skip 3rd column - site_name

    # convert coordinates and attributes of target points T to numpy array
    target_pts_np = txt2numpy(
        target_pts_grass,
        sep="|",
        names=None,
        null_value="*",
        usecols=usecols,
        structured=False,
    )

    # if one point only - 0D array which cannot be used in iteration
    if target_pts_np.ndim == 1:
        target_pts_np = target_pts_np.reshape(1, -1)

    target_pts_np = target_pts_np[~np.isnan(target_pts_np).any(axis=1)]

    no_points = target_pts_np.shape[0]

    # if viewshed weights not set by flag - set weight to 1 for all pts
    if not r_weights:
        weights_np = np.ones((no_points, 1))
        target_pts_np = np.hstack((target_pts_np, weights_np))

    grass.debug("target_pts_np: {}".format(target_pts_np))

    # ==========================================================================
    # Calculate weighted parametrised cummulative viewshed
    # by iterating over target points T
    # ==========================================================================
    grass.verbose("Calculating partial viewsheds...")

    # Parametrisation function
    if pfunction == "Solid_angle":
        parametrise_viewshed = solid_angle_reverse

    elif pfunction == "Distance_decay":
        parametrise_viewshed = distance_decay_reverse

    elif pfunction == "Fuzzy_viewshed":
        parametrise_viewshed = fuzzy_viewshed_reverse

    elif pfunction == "Visual_magnitude":
        parametrise_viewshed = visual_magnitude_reverse

    else:
        parametrise_viewshed = binary

    # Collect variables that will be used in do_it_all() into a dictionary
    global_vars = {
        "region": reg,
        "range": exp_range,
        "param_viewshed": parametrise_viewshed,
        "observer_elevation": v_elevation,
        "b_1": b_1,
        "memory": memory,
        "refr_coeff": refr_coeff,
        "flagstring": flagstring,
        "r_dsm": r_dsm,
        "dsm_type": dsm_type,
        "cores": cores,
        "tempname": TEMPNAME,
    }

    # Split target points to chunks for each core
    target_pnts = np.array_split(target_pts_np, cores)

    # Combine each chunk with dictionary
    combo = list(zip(itertools.repeat(global_vars), target_pnts))

    # Calculate partial cummulative viewshed
    pool = Pool(cores)
    np_sum = pool.starmap(do_it_all, combo)
    pool.close()
    pool.join()

    # We should probably use nansum here?
    all_nan = np.all(np.isnan(np_sum), axis=0)
    np_sum = np.nansum(np_sum, axis=0, dtype=np.single)
    np_sum[all_nan] = np.nan

    grass.verbose("Writing final result and cleaning up...")

    # Restore original computational region
    reg.read()
    reg.set_current()
    reg.set_raster_region()

    # Convert numpy array of cummulative viewshed to raster
    numpy2raster(np_sum, mtype="FCELL", rastname=r_output, overwrite=True)

    # Remove temporary files and reset mask if needed
    cleanup()

    # Set raster history to output raster
    grass.raster_history(r_output, overwrite=True)
    grass.run_command(
        "r.support",
        overwrite=True,
        map=r_output,
        title="Visual exposure index as {}".format(pfunction.replace("_", " ")),
        description="generated by r.viewshed.exposure",
        units="Index value",
        quiet=True,
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
