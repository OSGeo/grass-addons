#!/usr/bin/env python3

"""
Validation of r.viewshed.exposure for Paper 3
"""
# python3 /home/NINA.NO/zofie.cimburova/PhD/Paper3/SRC/validate_r_viewshed_exposure.py

# import os
# import time
# import atexit
import sys
import csv

# import subprocess
import numpy as np
from subprocess import Popen, PIPE


from grass.pygrass.vector import VectorTopo
import grass.script as grass


def run_test_A(
    val_pts, dsm, source, memory, cores, density, radii, methods, elev, val_file
):
    """Test combination of parametrisation methods and exposure radii
    :val_pts: Validation points
    :param dsm: Input DSM
    :param source: Exposure source
    :param memory: Allocated memory [MB]
    :param cores: Number of cores
    :param density: Sampling density
    :param radii: List of radii to test
    :param methods: List of methods to test
    :param elev: Observer elevation
    :param val_file: File to store the validation results
    """

    nsres = grass.raster_info(dsm)["nsres"]
    ewres = grass.raster_info(dsm)["ewres"]

    # new VectorTopo object
    val_pts_topo = VectorTopo(val_pts)
    val_pts_topo.open("rw")

    no_points = val_pts_topo.number_of("points")
    counter = 0

    # open file where validation outputs will be written
    with open(val_file, "a") as outfile:
        fieldnames = [
            "pt_id",
            "method",
            "radius",
            "density",
            "gvi",
            "ela_t",
            "usr_t",
            "sys_t",
            "cpu",
            "mem",
            "exit",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # iterate over points
        for pt in val_pts_topo.viter("points"):

            grass.percent(counter, no_points, 1)
            counter += 1

            pt_id = pt.attrs["img_no"]
            pt_x = pt.x
            pt_y = pt.y

            # iterate over radii
            for r in radii:

                # set region around processed point
                grass.run_command(
                    "g.region",
                    align=dsm,
                    n=pt_y + (r + nsres / 2.0),
                    s=pt_y - (r + nsres / 2.0),
                    e=pt_x + (r + ewres / 2.0),
                    w=pt_x - (r + ewres / 2.0),
                )

                # iterate over parametrisation methods
                for m in methods:

                    # Calculate GVI
                    r_GVI = "tmp_GVI_{p}_{r}_{m}".format(p=pt_id, r=r, m=m)

                    r_viewshed_profile = Popen(
                        [
                            "/usr/bin/time",
                            "-v",
                            "r.viewshed.exposure",
                            "--o",
                            "input={}".format(dsm),
                            "output={}".format(r_GVI),
                            "source={}".format(source),
                            "observer_elevation={}".format(elev),
                            "range={}".format(r),
                            "function={}".format(m),
                            "sample_density={}".format(density),
                            "memory={}".format(memory),
                            "cores={}".format(cores),
                            "seed=1",
                        ],
                        stdout=PIPE,
                        stderr=PIPE,
                    ).communicate()

                    r_viewshed_profile = (
                        r_viewshed_profile[1]
                        .decode("utf8")
                        .strip()[
                            r_viewshed_profile[1]
                            .decode("utf8")
                            .find("Command being timed")
                            - 1 :
                        ]
                    )
                    r_viewshed_profile = dict(
                        item.split(": ")
                        for item in r_viewshed_profile.replace("\t", "").split("\n")
                    )

                    # check if r.viewshed.exposure finished sucessfuly
                    if r_viewshed_profile["Exit status"] == "0":
                        # extract GVI value at point
                        gvi = float(
                            grass.read_command(
                                "r.what",
                                map=r_GVI,
                                coordinates="{},{}".format(pt_x, pt_y),
                            ).split("|")[3]
                        )
                    else:
                        gvi = 0.0

                    # write profiling information
                    cpu = r_viewshed_profile["Percent of CPU this job got"].replace(
                        "%", ""
                    )
                    el_time_list = r_viewshed_profile[
                        "Elapsed (wall clock) time (h:mm:ss or m:ss)"
                    ].split(":")
                    el_time_s = (
                        float(el_time_list[-1])
                        + 60 * float(el_time_list[-2])
                        + (
                            3600 * float(el_time_list[-3])
                            if len(el_time_list) > 2
                            else 0
                        )
                    )

                    writer.writerow(
                        {
                            "pt_id": pt_id,
                            "method": m,
                            "radius": r,
                            "density": density,
                            "gvi": gvi,
                            "ela_t": el_time_s,
                            "usr_t": r_viewshed_profile["User time (seconds)"],
                            "sys_t": r_viewshed_profile["System time (seconds)"],
                            "cpu": cpu,
                            "mem": r_viewshed_profile[
                                "Maximum resident set size (kbytes)"
                            ],
                            "exit": r_viewshed_profile["Exit status"],
                        }
                    )
                    grass.message(
                        "{},{},{},{},{},{},{},{},{},{},{}".format(
                            pt_id,
                            m,
                            r,
                            density,
                            gvi,
                            el_time_s,
                            r_viewshed_profile["User time (seconds)"],
                            r_viewshed_profile["System time (seconds)"],
                            cpu,
                            r_viewshed_profile["Maximum resident set size (kbytes)"],
                            r_viewshed_profile["Exit status"],
                        )
                    )

    # Close vector access
    val_pts_topo.close()

    return


def run_test_A_no_viewshed(
    val_pts, dsm, source, memory, cores, density, radii, methods, elev, val_file
):
    """Test combination of parametrisation methods and exposure radii
    :val_pts: Validation points
    :param dsm: Input DSM
    :param source: Exposure source
    :param memory: Allocated memory [MB]
    :param cores: Number of cores
    :param density: Sampling density
    :param radii: List of radii to test
    :param methods: List of methods to test
    :param elev: Observer elevation
    :param val_file: File to store the validation results
    """

    nsres = grass.raster_info(dsm)["nsres"]
    ewres = grass.raster_info(dsm)["ewres"]

    # new VectorTopo object
    val_pts_topo = VectorTopo(val_pts)
    val_pts_topo.open("rw")

    no_points = val_pts_topo.number_of("points")
    counter = 0

    # open file where validation outputs will be written
    with open(val_file, "a") as outfile:
        fieldnames = [
            "pt_id",
            "method",
            "radius",
            "density",
            "gvi",
            "ela_t",
            "usr_t",
            "sys_t",
            "cpu",
            "mem",
            "exit",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # iterate over points
        for pt in val_pts_topo.viter("points"):

            grass.percent(counter, no_points, 1)
            counter += 1

            pt_id = pt.attrs["img_no"]
            pt_x = pt.x
            pt_y = pt.y

            # iterate over radii
            for r in radii:

                # set region around processed point
                grass.run_command(
                    "g.region",
                    align=dsm,
                    n=pt_y + (r + nsres / 2.0),
                    s=pt_y - (r + nsres / 2.0),
                    e=pt_x + (r + ewres / 2.0),
                    w=pt_x - (r + ewres / 2.0),
                )

                # iterate over parametrisation methods
                for m in methods:

                    # Calculate GVI
                    r_GVI = "tmp_GVI_{p}_{r}_{m}".format(p=pt_id, r=r, m=m)

                    r_viewshed_profile = Popen(
                        [
                            "/usr/bin/time",
                            "-v",
                            "r.exposure",
                            "--o",
                            "input={}".format(dsm),
                            "output={}".format(r_GVI),
                            "source={}".format(source),
                            "observer_elevation={}".format(elev),
                            "range={}".format(r),
                            "method={}".format(m),
                            "sample_density={}".format(density),
                            "memory={}".format(memory),
                            "cores={}".format(cores),
                        ],
                        stdout=PIPE,
                        stderr=PIPE,
                    ).communicate()

                    r_viewshed_profile = (
                        r_viewshed_profile[1]
                        .decode("utf8")
                        .strip()[
                            r_viewshed_profile[1]
                            .decode("utf8")
                            .find("Command being timed")
                            - 1 :
                        ]
                    )
                    r_viewshed_profile = dict(
                        item.split(": ")
                        for item in r_viewshed_profile.replace("\t", "").split("\n")
                    )

                    # check if r.viewshed.exposure finished sucessfuly
                    if r_viewshed_profile["Exit status"] == "0":
                        # extract GVI value at point
                        gvi = float(
                            grass.read_command(
                                "r.what",
                                map=r_GVI,
                                coordinates="{},{}".format(pt_x, pt_y),
                            ).split("|")[3]
                        )
                    else:
                        gvi = 0.0

                    # write profiling information
                    cpu = r_viewshed_profile["Percent of CPU this job got"].replace(
                        "%", ""
                    )
                    el_time_list = r_viewshed_profile[
                        "Elapsed (wall clock) time (h:mm:ss or m:ss)"
                    ].split(":")
                    el_time_s = (
                        float(el_time_list[-1])
                        + 60 * float(el_time_list[-2])
                        + (
                            3600 * float(el_time_list[-3])
                            if len(el_time_list) > 2
                            else 0
                        )
                    )

                    writer.writerow(
                        {
                            "pt_id": pt_id,
                            "method": m,
                            "radius": r,
                            "density": density,
                            "gvi": gvi,
                            "ela_t": el_time_s,
                            "usr_t": r_viewshed_profile["User time (seconds)"],
                            "sys_t": r_viewshed_profile["System time (seconds)"],
                            "cpu": cpu,
                            "mem": r_viewshed_profile[
                                "Maximum resident set size (kbytes)"
                            ],
                            "exit": r_viewshed_profile["Exit status"],
                        }
                    )
                    grass.message(
                        "{},{},{},{},{},{},{},{},{},{},{}".format(
                            pt_id,
                            m,
                            r,
                            density,
                            gvi,
                            el_time_s,
                            r_viewshed_profile["User time (seconds)"],
                            r_viewshed_profile["System time (seconds)"],
                            cpu,
                            r_viewshed_profile["Maximum resident set size (kbytes)"],
                            r_viewshed_profile["Exit status"],
                        )
                    )

    # Close vector access
    val_pts_topo.close()

    return


def run_test_B(
    val_pts, dsm, source, memory, cores, densities_reps, radii, method, elev, val_file
):
    """Test combination of parametrisation methods and exposure radii
    :val_pts: Validation points
    :param dsm: Input DSM
    :param source: Exposure source
    :param memory: Allocated memory [MB]
    :param cores: Number of cores
    :param densities_reps: Sampling densities+number of times the model will be repeated
    :param radii: List of radii to test
    :param methods: List of methods to test
    :param elev: Observer elevation
    :param val_file: File to store the validation results
    """
    nsres = grass.raster_info(dsm)["nsres"]
    ewres = grass.raster_info(dsm)["ewres"]

    # new VectorTopo object
    val_pts_topo = VectorTopo(val_pts)
    val_pts_topo.open("rw")

    no_points = val_pts_topo.number_of("points")

    # open file where validation outputs will be written
    with open(val_file, "a") as outfile:
        fieldnames = [
            "pt_id",
            "rep",
            "method",
            "radius",
            "density",
            "gvi",
            "ela_t",
            "usr_t",
            "sys_t",
            "cpu",
            "mem",
            "exit",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # iterate over sample densities
        for dr in densities_reps:

            d = dr[0]  # density
            reps = dr[1]  # repetitions
            counter = 0

            # iterate over points
            for pt in val_pts_topo.viter("points"):
                grass.percent(counter, no_points, 1)
                counter += 1

                pt_id = pt.attrs["img_no"]
                pt_x = pt.x
                pt_y = pt.y

                # if (
                #     pt_id == "P5260311" or pt_id == "P5310641" or pt_id == "P6010803"
                # ):
                #     continue

                # iterate over radii
                for radius in radii:

                    # set region around processed point
                    grass.run_command(
                        "g.region",
                        align=dsm,
                        n=pt_y + (radius + nsres / 2.0),
                        s=pt_y - (radius + nsres / 2.0),
                        e=pt_x + (radius + ewres / 2.0),
                        w=pt_x - (radius + ewres / 2.0),
                    )

                    # iterate over repetitions
                    for rep in range(reps):

                        # Calculate GVI
                        r_GVI = "tmp_GVI_{p}_{r}_{m}_{s}_m".format(
                            p=pt_id, s=d, r=radius, m=method
                        )

                        r_viewshed_profile = Popen(
                            [
                                "/usr/bin/time",
                                "-v",
                                "r.viewshed.exposure",
                                "--q",
                                "--o",
                                "input={}".format(dsm),
                                "output={}".format(r_GVI),
                                "source={}".format(source),
                                "observer_elevation={}".format(elev),
                                "range={}".format(radius),
                                "function={}".format(method),
                                "sample_density={}".format(d),
                                "memory={}".format(memory),
                                "cores={}".format(cores),
                                "seed={}".format(rep + 20),
                            ],
                            stdout=PIPE,
                            stderr=PIPE,
                        ).communicate()

                        r_viewshed_profile = (
                            r_viewshed_profile[1]
                            .decode("utf8")
                            .strip()[
                                r_viewshed_profile[1]
                                .decode("utf8")
                                .find("Command being timed")
                                - 1 :
                            ]
                        )
                        r_viewshed_profile = dict(
                            item.split(": ")
                            for item in r_viewshed_profile.replace("\t", "").split("\n")
                        )

                        # check if r.viewshed.exposure finished sucessfuly
                        if r_viewshed_profile["Exit status"] == "0":
                            # extract GVI value at point
                            gvi = grass.read_command(
                                "r.what",
                                map=r_GVI,
                                coordinates="{},{}".format(pt_x, pt_y),
                            ).split("|")[3]
                        else:
                            gvi = 0.0

                        # write profiling information
                        cpu = r_viewshed_profile["Percent of CPU this job got"].replace(
                            "%", ""
                        )
                        el_time_list = r_viewshed_profile[
                            "Elapsed (wall clock) time (h:mm:ss or m:ss)"
                        ].split(":")
                        el_time_s = (
                            float(el_time_list[-1])
                            + 60 * float(el_time_list[-2])
                            + (
                                3600 * float(el_time_list[-3])
                                if len(el_time_list) > 2
                                else 0
                            )
                        )

                        writer.writerow(
                            {
                                "pt_id": pt_id,
                                "rep": rep,
                                "method": method,
                                "radius": radius,
                                "density": d,
                                "gvi": gvi,
                                "ela_t": el_time_s,
                                "usr_t": r_viewshed_profile["User time (seconds)"],
                                "sys_t": r_viewshed_profile["System time (seconds)"],
                                "cpu": cpu,
                                "mem": r_viewshed_profile[
                                    "Maximum resident set size (kbytes)"
                                ],
                                "exit": r_viewshed_profile["Exit status"],
                            }
                        )
                        grass.message(
                            "{},{},{},{},{},{},{},{},{},{},{},{}".format(
                                pt_id,
                                rep,
                                method,
                                radius,
                                d,
                                gvi,
                                el_time_s,
                                r_viewshed_profile["User time (seconds)"],
                                r_viewshed_profile["System time (seconds)"],
                                cpu,
                                r_viewshed_profile[
                                    "Maximum resident set size (kbytes)"
                                ],
                                r_viewshed_profile["Exit status"],
                            )
                        )

    # Close vector access
    val_pts_topo.close()

    return


def run_test_C(
    val_pts, dsm, source, memory, cores, density, radius, method, elev, val_file
):
    """Test combination of parametrisation methods and exposure radii
    :val_pts: Validation points
    :param dsm: Input DSM
    :param source: Exposure source
    :param memory: Allocated memory [MB]
    :param cores: Number of cores
    :param density: Sampling density
    :param radius: Exposure range
    :param methods: Parametrisation method
    :param elev: Observer elevation
    :param val_file: File to store the validation results
    """
    nsres = grass.raster_info(dsm)["nsres"]
    ewres = grass.raster_info(dsm)["ewres"]

    # new VectorTopo object
    val_pts_topo = VectorTopo(val_pts)
    val_pts_topo.open("rw")

    no_points = val_pts_topo.number_of("points")
    counter = 0

    # open file where validation outputs will be written
    with open(val_file, "a") as outfile:
        fieldnames = [
            "pt_id",
            "method",
            "radius",
            "density",
            "gvi",
            "ela_t",
            "usr_t",
            "sys_t",
            "cpu",
            "mem",
            "exit",
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # iterate over points
        for pt in val_pts_topo.viter("points"):
            grass.percent(counter, no_points, 1)
            counter += 1

            pt_id = pt.attrs["img_no"]
            pt_x = pt.x
            pt_y = pt.y

            # set region around processed point
            grass.run_command(
                "g.region",
                align=dsm,
                n=pt_y + (radius + nsres / 2.0),
                s=pt_y - (radius + nsres / 2.0),
                e=pt_x + (radius + ewres / 2.0),
                w=pt_x - (radius + ewres / 2.0),
            )

            # Calculate GVI
            r_GVI = "tmp_GVI_{p}_{r}_{m}_{s}_m".format(
                p=pt_id, s=density, r=radius, m=method
            )

            r_viewshed_profile = Popen(
                [
                    "/usr/bin/time",
                    "-v",
                    "r.viewshed.exposure",
                    "--q",
                    "--o",
                    "input={}".format(dsm),
                    "output={}".format(r_GVI),
                    "source={}".format(source),
                    "observer_elevation={}".format(elev),
                    "range={}".format(radius),
                    "function={}".format(method),
                    "sample_density={}".format(density),
                    "memory={}".format(memory),
                    "cores={}".format(cores),
                ],
                stdout=PIPE,
                stderr=PIPE,
            ).communicate()

            r_viewshed_profile = (
                r_viewshed_profile[1]
                .decode("utf8")
                .strip()[
                    r_viewshed_profile[1].decode("utf8").find("Command being timed")
                    - 1 :
                ]
            )
            r_viewshed_profile = dict(
                item.split(": ")
                for item in r_viewshed_profile.replace("\t", "").split("\n")
            )

            # check if r.viewshed.exposure finished sucessfuly
            if r_viewshed_profile["Exit status"] == "0":
                # extract GVI value at point
                gvi = grass.read_command(
                    "r.what", map=r_GVI, coordinates="{},{}".format(pt_x, pt_y)
                ).split("|")[3]
            else:
                gvi = 0.0

            # write profiling information
            cpu = r_viewshed_profile["Percent of CPU this job got"].replace("%", "")
            el_time_list = r_viewshed_profile[
                "Elapsed (wall clock) time (h:mm:ss or m:ss)"
            ].split(":")
            el_time_s = (
                float(el_time_list[-1])
                + 60 * float(el_time_list[-2])
                + (3600 * float(el_time_list[-3]) if len(el_time_list) > 2 else 0)
            )

            writer.writerow(
                {
                    "pt_id": pt_id,
                    "method": method,
                    "radius": radius,
                    "density": density,
                    "gvi": gvi,
                    "ela_t": el_time_s,
                    "usr_t": r_viewshed_profile["User time (seconds)"],
                    "sys_t": r_viewshed_profile["System time (seconds)"],
                    "cpu": cpu,
                    "mem": r_viewshed_profile["Maximum resident set size (kbytes)"],
                    "exit": r_viewshed_profile["Exit status"],
                }
            )
            grass.message(
                "{},{},{},{},{},{},{},{},{},{},{}".format(
                    pt_id,
                    method,
                    radius,
                    density,
                    gvi,
                    el_time_s,
                    r_viewshed_profile["User time (seconds)"],
                    r_viewshed_profile["System time (seconds)"],
                    cpu,
                    r_viewshed_profile["Maximum resident set size (kbytes)"],
                    r_viewshed_profile["Exit status"],
                )
            )

    # Close vector access
    val_pts_topo.close()

    return


def main():

    # Set numpy printing options
    np.set_printoptions(formatter={"float": lambda x: "{0:0.2f}".format(x)})

    # Validation points
    v_points = "validation_points_update_20210326"
    grass.run_command("v.build", map=v_points, quiet=True)

    # Constant viewshed settings
    observer_elevation = 1.5

    # ==========================================================================
    # Test A
    # ==========================================================================
    # DSM
    r_dsm = "Hoydedata_DSM_OB_2019_1m@u_zofie.cimburova"

    # Exposure source
    r_source = "validation_canopy_200m_update_20210326@u_zofie.cimburova"

    # Module settings
    memory = 25000
    cores = 25

    # Viewshed settings
    radii = [50, 100, 150, 200, 250, 300]
    methods = [
        "Binary",
        "Distance_decay",
        "Visual_magnitude",
        "Solid_angle",
    ]
    sample_density = 100

    # Validation file
    val_file = "/home/NINA.NO/zofie.cimburova/PhD/Paper3/DATA/validation_test_A.csv"

    run_test_A(
        v_points,
        r_dsm,
        r_source,
        memory,
        cores,
        sample_density,
        radii,
        methods,
        observer_elevation,
        val_file,
    )

    # ==========================================================================
    # Test A - no viewshed
    # ==========================================================================
    # DSM
    r_dsm = "Hoydedata_DSM_OB_2019_1m@u_zofie.cimburova"

    # Exposure source
    r_source = "validation_canopy_200m_update_20210326@u_zofie.cimburova"

    # Module settings
    memory = 25000
    cores = 5

    # Viewshed settings
    radii = [200]
    methods = ["Distance_decay"]
    sample_density = 100

    # Validation file
    val_file = "/home/NINA.NO/zofie.cimburova/PhD/Paper3/DATA/validation_test_A_no_viewshed.csv"

    run_test_A_no_viewshed(
        v_points,
        r_dsm,
        r_source,
        memory,
        cores,
        sample_density,
        radii,
        methods,
        observer_elevation,
        val_file,
    )

    # ==========================================================================
    # Test B
    # ==========================================================================
    # DSM
    r_dsm = "Hoydedata_DSM_OB_2019_1m@u_zofie.cimburova"

    # Exposure source
    r_source = "validation_canopy_200m_update_20210326@u_zofie.cimburova"

    # Module settings
    memory = 25000
    cores = 25

    # Viewshed settings
    radii = [100]
    method = "Distance_decay"
    densities_reps = [[0.1, 50], [1, 50], [5, 50], [10, 50], [25, 50], [50, 50]]

    # Validation file
    val_file = "/home/NINA.NO/zofie.cimburova/PhD/Paper3/DATA/validation_test_B.csv"

    run_test_B(
        v_points,
        r_dsm,
        r_source,
        memory,
        cores,
        densities_reps,
        radii,
        method,
        observer_elevation,
        val_file,
    )

    # ==========================================================================
    # Test C - LC
    # ==========================================================================
    # DSM
    r_dsm = "Hoydedata_DSM_OB_2019_1m@u_zofie.cimburova"

    # Exposure source
    r_source = "woodland_oslo_ELC10_2018_10m@u_zofie.cimburova"

    # Module settings
    memory = 25000
    cores = 25

    # Viewshed settings
    radius = 100
    method = "Distance_decay"
    density = 100

    # Validation file
    val_file = "/home/NINA.NO/zofie.cimburova/PhD/Paper3/DATA/validation_test_C.csv"

    run_test_C(
        v_points,
        r_dsm,
        r_source,
        memory,
        cores,
        density,
        radius,
        method,
        observer_elevation,
        val_file,
    )

    return


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
