# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 14:29:46 2015

@author: ggaregnani
"""
# import system libraries
from __future__ import print_function

import math
import os
import sys

import numpy as np

# from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.gis.region import Region
from grass.pygrass.messages import get_msgr
from grass.pygrass.raster import RasterRow
from grass.pygrass.vector import VectorTopo
from grass.script import core as gcore

# from grass.pygrass.raster.buffer import Buffer
from grass.script.utils import set_path
from libhydro.plant import COLS, COLS_points, Intake, Plant, Restitution

# from grass.script import mapcalc
version = 70  # 71


# import scientific libraries
try:
    from scipy import optimize
    from scipy import interpolate
    from scipy.optimize import fsolve
except ImportError:
    gcore.warning("You should install scipy to use this module: " "pip install scipy")


set_path("r.green", "libhydro", "..")
set_path("r.green", "libgreen", os.path.join("..", ".."))


def f(x, *params):
    # msgr = get_msgr()
    prog, h, q = params
    # msgr.message("\%f, %f\n" % (x[0], x[1]))
    # msgr.message("\init int\n")
    fun_h = interpolate.interp1d(prog, h)
    fun_q = interpolate.interp1d(prog, q)
    # msgr.message("\end int\n")
    dh = fun_h(x[0]) - fun_h(x[0] + x[1])
    # pdb.set_trace()
    return -dh * fun_q(x[0])


def find_s_z(s, *params):
    # msgr = get_msgr()
    x0, prog, h, l_max = params
    fun_h = interpolate.interp1d(prog, h, bounds_error=False, fill_value=0)
    delta_h = abs(fun_h(x0 + s) - fun_h(x0))
    theta = math.atan(delta_h / s)
    return l_max - abs(s / math.cos(theta))


def min_len_plant_z(prog, h, l_max, range_plant, range_line, tol=10.0):
    start, end = range_line
    len_plant = []
    if end - start > tol:
        num = int((end - start - tol) / tol)
        for x0 in np.linspace(start, end - 1, num=num):
            sol, infodict, ier, mesg = fsolve(
                find_s_z, [0], args=(x0, prog, h, l_max), full_output=True
            )
            if ier == 1:
                # import pdb; pdb.set_trace()
                len_plant.append(sol[0])
            else:
                len_plant.append(0)

        len_plant = np.array(len_plant)
        order = np.argsort(len_plant)
        x_ink = np.linspace(start, end - tol, num=num)[order]
        x_rest = x_ink + len_plant[order]
        s = len_plant[order]
        aaa = x_rest < end
        bbb = s > 0
        ccc = aaa * bbb
        if ccc.any():
            if len_plant.sum() == 0:
                return (start, end - start)
            else:
                return (x_ink[ccc][0], s[ccc][0])
        else:
            return (start, end - start)
    else:
        return (start, end - start)


def find_s(s, *params):
    # msgr = get_msgr()
    x0, prog, h, q, p_max = params
    fun_h = interpolate.interp1d(prog, h, bounds_error=False, fill_value=0)
    fun_q = interpolate.interp1d(prog, q, bounds_error=False, fill_value=0)
    if fun_q(x0) == 0:
        # import pdb; pdb.set_trace()
        return 99999
    else:
        return p_max - (fun_q(x0) * 9.81) * (fun_h(x0) - fun_h(x0 + s))


def min_len_plant(prog, h, q, p_max, range_plant, range_line, tol=10.0):
    start, end = range_line
    q = np.array(q)
    q[np.isnan(q)] = 0
    #    if q.sum() == 0:
    #        return (0, 0)
    len_plant = []
    fun_q = interpolate.interp1d(prog, q, bounds_error=False, fill_value=0)
    if end - start > tol:
        num = int((end - start - tol) / tol)
        for x0 in np.linspace(start, end - 1, num=num):
            # import pdb; pdb.set_trace()
            if fun_q(x0) == 0:
                # import pdb; pdb.set_trace()
                len_plant.append(0)
            else:
                # import pdb; pdb.set_trace()
                sol, infodict, ier, mesg = fsolve(
                    find_s, [0], args=(x0, prog, h, q, p_max), full_output=True
                )
                if ier == 1:
                    # import pdb; pdb.set_trace()
                    len_plant.append(sol[0])
                else:
                    len_plant.append(0)

        len_plant = np.array(len_plant)
        order = np.argsort(len_plant)
        x_ink = np.linspace(start, end - tol, num=num)[order]
        x_rest = x_ink + len_plant[order]
        s = len_plant[order]
        aaa = x_rest < end
        bbb = s > 0
        ccc = aaa * bbb
        if ccc.any():
            if len_plant.sum() == 0:
                return (start, end - start)
            else:
                return (x_ink[ccc][0], s[ccc][0])
        else:
            return (start, end - start)
    else:
        return (start, end - start)


# TODO: to move in another lib
def check_multilines(vector):
    vector, mset = vector.split("@") if "@" in vector else (vector, "")
    msgr = get_msgr()
    vec = VectorTopo(vector, mapset=mset, mode="r")
    vec.open("r")
    info = gcore.parse_command("v.category", input=vector, option="print")
    for i in info.keys():
        vec.cat(int(i), "lines", 1)
        #        if i == '28':
        #            import ipdb; ipdb.set_trace()
        if len(vec.cat(int(i), "lines", 1)) > 1:
            # import ipdb; ipdb.set_trace()
            warn = "Multilines for the same category %s" % i
            msgr.warning(warn)
    vec.close()


def build_array(line, raster_q, raster_dtm):
    """
    build arrays with discharge, elevation and
    coordinate + order the line according to dtm and discharge
    """
    prog = []
    h = []
    q = []
    coordinate = []

    for point in line:
        coordinate.append(point)
        q.append(raster_q.get_value(point))
        h.append(raster_dtm.get_value(point))
    # FIXME: the second and the second to last because
    # we should avoid to take discharge in another branch
    # import ipdb; ipdb.set_trace()
    if len(h) > 3:
        h_diff = np.array(h[0:-2]) - np.array(h[1:-1])
        if h_diff.sum() < 0:
            q = q[::-1]
            h = h[::-1]
            coordinate = coordinate[::-1]
            line.reverse()

    prog.append(0)
    # note that i is i-1
    for i, point in enumerate(coordinate[1::]):
        dist = point.distance(coordinate[i])
        # pdb.set_trace()
        prog.append(prog[i] + dist)
    return line, prog, h, q


def find_optimal(args, range_plant, ranges):

    eps = 0.5  # for the grid
    rranges = ((ranges[0], ranges[1] - range_plant[1] - eps), range_plant)
    x_min = optimize.brute(f, rranges, args=args, finish=None)
    return x_min


def recursive_plant(
    args,
    range_plant,
    distance,
    start,
    end,
    rank,
    cat,
    line,
    plants,
    count,
    p_max,
):
    msgr = get_msgr()
    count = count + 1
    # import ipdb; ipdb.set_trace()
    msgr.message("\n%i\n" % cat)
    # import pdb; pdb.set_trace()
    res = check_plant(
        args, range_plant, distance, start, end, rank, cat, line, count, p_max
    )
    if res:
        plants.append(res[0])
        plants = check_segments(
            args,
            range_plant,
            distance,
            res[1],
            start,
            end,
            rank,
            cat,
            line,
            plants,
            count,
            p_max,
        )
    return plants


def check_plant(args, range_plant, distance, start, end, rank, cat, line, count, p_max):
    # import pdb; pdb.set_trace()
    prog, h, q = args
    fun_h = interpolate.interp1d(prog, h, bounds_error=False, fill_value=0)
    fun_q = interpolate.interp1d(prog, q, bounds_error=False, fill_value=0)
    delta_h = fun_h(end) - fun_h(start)
    theta = math.atan(delta_h / (end - start))
    len_p = end - start
    dis = abs(distance * math.cos(theta))
    len_plant = range_plant[1] * math.cos(theta)
    len_min = range_plant[0] * math.cos(theta)
    if count < 100:
        if len_p > len_plant + 2 * dis:
            # if (end-start) > len_plant + 2*distance:
            if not (p_max):
                x_min = find_optimal(
                    args, (len_min, len_plant), (start + dis, end - dis)
                )
            else:
                x_min = min_len_plant(
                    prog, h, q, p_max, (len_min, len_plant), (start + dis, end - dis)
                )
            seg = line.segment(x_min[0], x_min[0] + x_min[1])
            if seg:
                ink = Intake(
                    id_point=str(1),
                    id_plants=rank,
                    id_stream=cat,
                    point=x_min[0],
                    discharge=fun_q(x_min[0]),
                    elevation=fun_h(x_min[0]),
                )
                res = Restitution(
                    id_point=str(2),
                    id_plants=rank,
                    id_stream=cat,
                    point=x_min[0] + x_min[1],
                    discharge=fun_q(x_min[0]),
                    elevation=fun_h(x_min[0] + x_min[1]),
                )
                p = Plant(
                    id_plant=rank,
                    id_stream=cat,
                    restitution=res,
                    intakes=(ink,),
                    line=seg,
                )
                return p, x_min
        elif (len_p - 2 * dis) > len_min and (len_p < len_plant + 2 * dis):
            len_plant = end - start - 2 * dis
            range_plant = (range_plant[0], len_plant / math.cos(theta))
            if not (p_max):
                x_min = find_optimal(args, range_plant, (start + dis, end - dis))
            #                x_min = min_len_plant_z(prog, h, l_max, range_plant,
            #                                        (start+distance, end-distance))
            else:
                x_min = min_len_plant(
                    prog, h, q, p_max, range_plant, (start + dis, end - dis)
                )
            seg = line.segment(x_min[0], x_min[0] + x_min[1])
            if seg:
                ink = Intake(
                    id_point=str(1),
                    id_plants=rank,
                    id_stream=cat,
                    point=x_min[0],
                    discharge=fun_q(x_min[0]),
                    elevation=fun_h(x_min[0]),
                )
                # import pdb; pdb.set_trace()
                res = Restitution(
                    id_point=str(2),
                    id_plants=rank,
                    id_stream=cat,
                    point=x_min[0] + x_min[1],
                    discharge=fun_q(x_min[0]),
                    elevation=fun_h(x_min[0] + x_min[1]),
                )
                p = Plant(
                    id_plant=rank,
                    id_stream=cat,
                    restitution=res,
                    intakes=(ink,),
                    line=seg,
                )
                return p, x_min
        # FIXME: check the minimum segment for hydroplants,
        # perhaps it is better a minimum gross head
        # return
        # pdb.set_trace()


#            seg1 = line.segment(start, x_min[0])
#            check_plant(seg1, args, len_plant, new_vec, start, x_min[0],
#                        rank+1)
#            seg2 = line.segment(x_min[0]+x_min[1], end)
#            check_plant(seg2, args, len_plant, new_vec, start, x_min[0],
#                        rank+1)


def check_segments(
    args,
    range_plant,
    distance,
    x_min,
    start_old,
    end_old,
    rank,
    cat,
    line,
    plants,
    count,
    p_max,
):
    # seg1 = line.segment(start_old, x_min[0])
    rank = rank + ".1"
    plants = recursive_plant(
        args,
        range_plant,
        distance,
        start_old,
        x_min[0],
        rank,
        cat,
        line,
        plants,
        count,
        p_max,
    )
    # seg2 = line.segment(x_min[0]+x_min[1], end_old)
    rank = rank + ".2"
    plants = recursive_plant(
        args,
        range_plant,
        distance,
        x_min[0] + x_min[1],
        end_old,
        rank,
        cat,
        line,
        plants,
        count,
        p_max,
    )
    return plants


#    else:
#        return
# def find_residual(line, prog, h, q, x_min):
#    rest = []
#    rest[1] = line.segment(prog)


def find_segments(river, discharge, dtm, range_plant, distance, p_max):
    check_multilines(river)
    # pdb.set_trace()
    river, mset = river.split("@") if "@" in river else (river, "")
    vec = VectorTopo(river, mapset=mset, mode="r")
    vec.open("r")
    raster_q = RasterRow(discharge)
    raster_dtm = RasterRow(dtm)
    raster_q.open("r")
    raster_dtm.open("r")
    reg = Region()
    plants = []
    for line in vec:
        count = 0
        # args is prog, h,  q
        line, prog, h, q = build_array(line, raster_q, raster_dtm)
        # pdb.set_trace()
        if len(line) > 2:
            #            import ipdb; ipdb.set_trace()
            #        else:
            # import pdb; pdb.set_trace()
            plants = recursive_plant(
                (prog, h, q),
                range_plant,
                distance,
                prog[0],
                prog[-1],
                str(line.cat),
                line.cat,
                line,
                plants,
                count,
                p_max,
            )
    # pdb.set_trace()
    vec.close()
    raster_q.close()
    raster_dtm.close()
    return plants


def write_plants(plants, output, efficiency, min_power):
    # create vetor segment
    new_vec = VectorTopo(output)
    # TODO:  check if the vector already exists
    new_vec.layer = 1
    new_vec.open("w", tab_cols=COLS)
    reg = Region()
    for pla in plants:
        power = pla.potential_power(efficiency=efficiency)
        if power > min_power:
            for cat, ink in enumerate(pla.intakes):
                if version == 70:
                    new_vec.write(
                        pla.line,
                        (
                            pla.id,
                            pla.id_stream,
                            power,
                            float(pla.restitution.discharge),
                            float(ink.elevation),
                            float(pla.restitution.elevation),
                        ),
                    )
                else:
                    new_vec.write(
                        pla.line,
                        cat=cat,
                        attrs=(
                            pla.id,
                            pla.id_stream,
                            power,
                            float(pla.restitution.discharge),
                            float(ink.elevation),
                            float(pla.restitution.elevation),
                        ),
                    )

    new_vec.table.conn.commit()
    new_vec.comment = " ".join(sys.argv)
    # pdb.set_trace()
    new_vec.close()


def write_points(plants, output, efficiency, min_power):
    # create vetor segment
    new_vec = VectorTopo(output)
    # TODO:  check if the vector already exists
    new_vec.layer = 1
    new_vec.open("w", tab_cols=COLS_points)
    reg = Region()

    # import ipdb; ipdb.set_trace()
    for pla in plants:
        power = pla.potential_power(efficiency=efficiency)
        if power > min_power:
            new_vec.write(
                pla.line[-1],
                (
                    pla.restitution.id,
                    pla.id,
                    "restitution",
                    pla.id_stream,
                    float(pla.restitution.elevation),
                    float(pla.restitution.discharge),
                    power,
                ),
            )
            for ink in pla.intakes:
                new_vec.write(
                    pla.line[0],
                    (
                        ink.id,
                        pla.id,
                        "intake",
                        pla.id_stream,
                        float(ink.elevation),
                        float(ink.discharge),
                        power,
                    ),
                )

    new_vec.table.conn.commit()
    new_vec.comment = " ".join(sys.argv)
    new_vec.write_header()
    # pdb.set_trace()
    new_vec.close()


def conv_segpoints(seg, output):

    segments, mset = seg.split("@") if "@" in seg else (seg, "")
    # convert the map with segments in a map with intakes and restitution
    new_vec = VectorTopo(output)
    # TODO:  check if the vector already exists
    new_vec.layer = 1
    new_vec.open("w", tab_cols=COLS_points)
    reg = Region()

    seg = VectorTopo(segments, mapset=mset)
    seg.layer = 1
    seg.open("r")

    for pla in seg:
        # import ipdb; ipdb.set_trace()
        new_vec.write(
            pla[-1],
            (
                2,
                pla.attrs["plant_id"],
                "restitution",
                pla.attrs["stream_id"],
                pla.attrs["elev_down"],
                pla.attrs["discharge"],
                pla.attrs["pot_power"],
            ),
        )
        # import ipdb; ipdb.set_trace()
        new_vec.write(
            pla[0],
            (
                1,
                pla.attrs["plant_id"],
                "intake",
                pla.attrs["stream_id"],
                pla.attrs["elev_up"],
                pla.attrs["discharge"],
                pla.attrs["pot_power"],
            ),
        )

    new_vec.table.conn.commit()
    new_vec.comment = " ".join(sys.argv)
    new_vec.write_header()
    # pdb.set_trace()
    new_vec.close()

    return new_vec
