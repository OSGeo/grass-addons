#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.technical
# AUTHOR(S):   Giulia Garegnani, Julie Gros, Pietro Zambelli
# PURPOSE:
#
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
############################################################################
#
#
# %module
# % description: Hydropower potential with technical constraints
# % keyword: raster
# % keyword: hydropower
# % keyword: renewable energy
# % overwrite: yes
# %end
# %option G_OPT_V_INPUT
# % key: plant
# % type: string
# % label: Name of input vector map with segments of potential plants
# % required: yes
# %end
# %option G_OPT_R_ELEV
# %  required: yes
# %end
# %option G_OPT_V_FIELD
# %  key: plant_layer
# %  label: Name of the vector map layer of the plants
# %  required: no
# %  answer: 1
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_plant_id
# %  type: string
# %  description: Column name with the plant id
# %  required: no
# %  answer: plant_id
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_point_id
# %  type: string
# %  description: Column name with the point id
# %  required: no
# %  answer: cat
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_elevup
# %  type: string
# %  description: Column name with the elevation value at the intake (upstream) [m]
# %  required: no
# %  answer: elev_up
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_elevdown
# %  type: string
# %  description: Column name with the elevation value at the restitution (downstream) [m]
# %  required: no
# %  answer: elev_down
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_discharge
# %  type: string
# %  description: Column name with the discharge values [m3/s]
# %  required: no
# %  answer: discharge
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_power
# %  type: string
# %  description: Column name with the potential power [kW]
# %  required: no
# %  answer: pot_power
# %  guisection: Input columns
# %end
# %flag
# % key: d
# % description: Debug with intermediate maps
# %end
# %flag
# % key: c
# % description: Clean vector lines
# %end
# %option G_OPT_V_OUTPUT
# % key: output_struct
# % label: Name of output vector with potential plants and their structure
# %end
# %option G_OPT_V_INPUT
# % key: input_struct
# % label: Name of input vector with potential plants and their structure
# % required: no
# %end
# %option G_OPT_V_OUTPUT
# % key: output_plant
# % label: Name of output vector map with segments of potential plants
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: output_point
# % label: Name of output vector map with potential intakes and restitution
# % required: no
# %end
# %option
# % key: ks_derivation
# % type: double
# % description: Strickler coefficient of the derivation [m^(1/3)/s]
# % required: no
# % answer: 75
# % guisection: Head losses
# %end
# %option
# % key: velocity_derivation
# % type: double
# % description: Flow velocity in the derivation pipe [m/s]
# % required: no
# % answer: 1.
# % guisection: Head losses
# %end
# %option
# % key: percentage_losses
# % type: double
# % description: Percentage of losses (/gross head), if the diameter is not defined [%]
# % required: no
# % answer: 4
# % guisection: Head losses
# %end
# %option
# % key: roughness_penstock
# % type: double
# % description: Roughness of the penstock [mm]
# % required: no
# % answer: 0.015
# % guisection: Head losses
# %end
# %option
# % key: turbine_folder
# % type: string
# % description: Path to the folder containing the text file with info about all kind of turbines
# % required: yes
# % answer:
# % guisection: Turbine
# %end
# %option
# % key: turbine_list
# % type: string
# % description: Path to the text file containing the list of the turbines considered
# % required: yes
# % answer:
# % guisection: Turbine
# %end
# %option
# % key: n
# % type: double
# % description: Number of operative hours per year [hours/year]
# % required: no
# % answer: 3392
# % guisection: Efficiency
# %end
# %option
# % key: efficiency_shaft
# % type: double
# % description: Efficiency of the shaft (bearings friction) [-]
# % required: no
# % answer: 1
# % guisection: Efficiency
# %end
# %option
# % key: efficiency_alt
# % type: double
# % description: Efficiency of the alternator [-]
# % required: no
# % answer: 0.96
# % guisection: Efficiency
# %end
# %option
# % key: efficiency_transf
# % type: double
# % description: Efficiency of the transformer (magnetic losses) [-]
# % required: no
# % answer: 0.99
# % guisection: Efficiency
# %end
# %option
# %  key: ndigits
# %  type: integer
# %  description: Number of digits to use for the elevation in the contour line vector map
# %  required: no
# %  answer: 0
# %  guisection: Contour
# %end
# %option
# %  key: resolution
# %  type: double
# %  description: Resolution use for the contour line vector map, if 0.25 approximate 703.31 tp 703.25
# %  required: no
# %  guisection: Contour
# %end
# %option G_OPT_V_OUTPUT
# %  key: contour
# %  description: Name of the contour line vector map
# %  required: no
# %  guisection: Contour
# %end

# %rules
# % exclusive: input_struct,output_struct
# %end

# import system libraries
from __future__ import print_function

import atexit
import os
import sys
from math import acos, asin, log10, pi, sin, sqrt

import numpy as np

from grass.pygrass.messages import get_msgr
from grass.pygrass.utils import set_path
from grass.pygrass.vector import VectorTopo
from grass.script import core as gcore

try:
    from scipy.optimize import fsolve
except ImportError:
    gcore.warning("You should install scipy to use this module: " "pip install scipy")


try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libhydro", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libgreen.utils import cleanup
    from libhydro.plant import power2energy
    from libhydro.optimal import conv_segpoints
except ImportError:
    try:
        set_path("r.green", "libhydro", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libgreen.utils import cleanup
        from libhydro.plant import power2energy
        from libhydro.optimal import conv_segpoints
    except ImportError:
        gcore.warning("libgreen and libhydro not in the python path!")


DEBUG = False
TMPRAST = []

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def add_columns(vector, cols):
    """Add new column if not already present in the vector table.
    columns is a list of tuple with the column name and the column type."""
    for cname, ctype in cols:
        if cname not in vector.table.columns:
            vector.table.columns.add(cname, ctype)


def diam_pen(discharge, length, gross_head, percentage, epsilon=0.015):
    def diam(x, *args):
        q, l, h, p, e = args
        return sqrt(
            (100 * 8 * l * q**2) / (p * h * pi**2 * 9.81 * x**5)
        ) + 2 * log10(
            (e * 0.001) / (3.71 * x)
            + (2.51 * 0.000001 * pi)
            / (4 * q * l)
            * sqrt((100 * 8 * l * q**2) / (p * h * pi**2 * 9.81 * x))
        )

    out = fsolve(diam, 0.1, args=(discharge, length, gross_head, percentage, epsilon))[
        0
    ]
    return out


def losses_Colebrooke(discharge, length, diameter, epsilon=0.015):
    """Return the Darcy-Weisbach losses with f computed with
    the Colebrook-White formula

    Parameters
    -----------
    discharge: float [m³/s]
        Design discharge
    length: float [m]
        Design length of the pipe/derivation
    diameter: float [m]
        Design diameter for the derivation pipe
    epsilon: [mm]
        Roughness

    Example
    -------

    >>> Q, d, l = 1., 2., 1000.
    >>> hc = losses_Colebrooke(discharge=Q, length=l, diameter=d)
    >>> hc == 0.032861244804694816 * 1000.0
    """

    def coeff_f(x, *args):
        """
        Solve the Colebrook-White formula and return 1/radq(f)
        Parameters
        -----------
        discharge: float [m³/s]
            Design discharge
        diameter: float [m]
            Design diameter for the derivation pipe
        epsilon: [mm]
            Roughness
        """
        # TODO epsilon coefficient from GUI
        q, d, e = args
        first_log_arg = (e * 0.001) / (3.71 * d)  # epsilon [mm]
        rho_water = 1000.0  # kg/m2
        mu_water = 0.001  # Pa
        vel = discharge / (pi * d**2.0 / 4.0)
        re_number = rho_water * vel * d / mu_water
        return x + 2 * log10(first_log_arg + 2.51 * x / re_number)

    out = fsolve(coeff_f, 0, args=(discharge, diameter, epsilon))
    f = 1 / out**2
    h_colebrooke = (f[0] * 8 * length * discharge**2) / (
        pi**2 * diameter**5 * 9.81
    )
    return h_colebrooke


def losses_Strickler(discharge, length, diameter, theta, velocity, ks=75):
    """Return Strickler losses.

    Parameters
    -----------

    discharge: float [m³/s]
        Design discharge
    length: float [m]
        Design length of the pipe/derivation
    diameter: float [m]
        Design diameter for the derivation pipe
    theta: [radians]
        Angle of the circular section not wet by the water
    velocity: [m/s]
        Water velocity
    ks: [m**(1/3)/s]
        Strickler coefficient of the pipe material


    Example
    -------

    >>> Q, d, ks = 1., 2., 75.
    >>> v = 4 * Q / (pi * d**2)
    >>> hs = losses_Strickler(discharge=Q, length=1., diameter=d,
    ...                       theta=0., velocity=v, ks=ks)
    >>> hs == 1. / (ks ** 2.)
    """
    # circolar section
    r = diameter * 0.5
    A = 0.5 * r**2 * (2 * pi - theta + sin(theta))
    pw = r * (2 * pi - theta)
    Rh = A / pw

    # if round(discharge / A, 5) == round(velocity, 5):
    #   import ipdb
    #   ipdb.set_trace()
    #
    #   i = v**2 / (ks**2 * Rh ** (4/3))
    #   hs = i * l

    return velocity**2 / (ks**2 * Rh ** (4.0 / 3.0)) * length


def singular_losses(gross_head, length, discharge, diameter_penstock):

    if diameter_penstock != 0 and gross_head != 0:

        h_sing = 1.0 / (2.0 * 9.81) + (
            0.5
            + (gross_head / length) ** 2
            + 2 * (sin(asin(min(1, gross_head / length)) / 2)) ** 4
        ) * ((8 * discharge**2) / (9.81 * pi**2 * diameter_penstock**4))
    else:
        h_sing = 0
    return h_sing


class Turbine(object):
    def __init__(self, name, flow_proportion, efficiency, q_max, q_min, alpha_c):
        self.name = name
        self.flow_proportion = np.array(flow_proportion)
        self.efficiency = np.array(efficiency)
        self.q_max = q_max
        self.q_min = q_min
        self.alpha_c = alpha_c


def compute_losses(
    struct, options, percentage_losses, roughness_penstock, ks_derivation
):
    # add necessary columns
    cols = [
        ("diameter", "DOUBLE"),
        ("losses", "DOUBLE"),
        ("sg_losses", "DOUBLE"),
        ("tot_losses", "DOUBLE"),
        ("net_head", "DOUBLE"),
    ]
    add_columns(struct, cols)
    # power column renamed?

    # extract intake id
    list_intakeid = list(
        set(
            struct.table.execute(
                "SELECT intake_id FROM %s" % struct.table.name
            ).fetchall()
        )
    )

    theta = acos(1.0 / 6.0) * 2
    velocity = float(options["velocity_derivation"])
    # compute structure losses
    for line in struct:
        gross_head = float(line.attrs["gross_head"])
        discharge = float(line.attrs["discharge"])
        if gross_head <= 0 or discharge <= 0:
            # FIXME: it is not physical possible that it is <0
            line.attrs["sg_losses"] = 0
            line.attrs["gross_head"] = 0
            line.attrs["losses"] = 0
        else:

            length = line.length()
            losses = 0
            if length > 0 and discharge > 0:
                if line.attrs["kind"] == "penstock":
                    diameter = line.attrs["diameter"]
                    if not diameter:
                        diameter = diam_pen(
                            discharge,
                            length,
                            gross_head,
                            percentage_losses,
                            roughness_penstock,
                        )
                        line.attrs["diameter"] = diameter
                    length = (length**2.0 + gross_head**2.0) ** 0.5
                    if gross_head > length:
                        msgr = get_msgr()
                        msgr.warning(
                            "To check length of penstock,"
                            "gross head greater than "
                            "length"
                        )
                        # import ipdb
                        # ipdb.set_trace()
                    losses = losses_Colebrooke(
                        discharge, length, diameter, roughness_penstock
                    )
                    # when you compute alpha (see manual) the lenght of the
                    # line is the real  length and not the projection
                    # for the blend we use the formula sen2(alpha)+sen4(alpha/2)
                    # TODO: add the possibility to insert the coefficient for the
                    # singolar losses in the table of the structure
                    # TODO: add singolar loss in function of thevelocity of
                    # derivation channel
                    line.attrs["sg_losses"] = singular_losses(
                        gross_head, length, discharge, diameter
                    )

            elif line.attrs["kind"] == "conduct":
                diameter = line.attrs["diameter"]
                if not diameter:
                    # diameter formula: d = sqrt(4 * Q / (v * pi))
                    # with:
                    # - d as diameter
                    # - Q as discharge
                    # - v as velocity (v == 1)
                    diameter = ((4 * discharge) / (velocity * pi)) ** (0.5)
                    line.attrs["diameter"] = diameter

                losses = losses_Strickler(
                    discharge, length, diameter, theta, velocity, ks_derivation
                )
            else:
                losses = 0

            line.attrs["losses"] = losses  # in [m]
            # TODO: fix as function of velocity
            # TODO: check when gross_head>length not physically
    # save the changes
    struct.table.conn.commit()

    # TODO: make it more readable/pythonic
    sql0 = "SELECT losses FROM %s WHERE (intake_id=%i AND side='option0');"
    sql1 = "SELECT losses FROM %s WHERE (intake_id=%i AND side='option1');"
    msgr = get_msgr()
    for i in list_intakeid:
        struct.rewind()
        totallosses0 = 0
        totallosses1 = 0

        bothlosses0 = list(
            struct.table.execute(sql0 % (struct.table.name, i[0])).fetchall()
        )
        if bothlosses0[0][0] and bothlosses0[1][0]:
            totallosses0 = bothlosses0[0][0] + bothlosses0[1][0]

        bothlosses1 = list(
            struct.table.execute(sql1 % (struct.table.name, i[0])).fetchall()
        )
        if bothlosses1[0][0] and bothlosses1[1][0]:
            totallosses1 = bothlosses1[0][0] + bothlosses1[1][0]

        for line in struct:
            sing_losses = line.attrs["sg_losses"]

            if (
                line.attrs["intake_id"] == i[0]
                and line.attrs["side"] == "option0"
                and line.attrs["kind"] == "penstock"
            ):
                line.attrs["tot_losses"] = totallosses0 + sing_losses
                tot_losses = float(line.attrs["tot_losses"])
                line.attrs["net_head"] = max(0.0, line.attrs["gross_head"] - tot_losses)
                # net_head = float(line.attrs['net_head'])
                if tot_losses > line.attrs["gross_head"]:

                    msgr.warning(("Losses greater than gross_head, %i" % (line.cat)))

            if (
                line.attrs["intake_id"] == i[0]
                and line.attrs["side"] == "option1"
                and line.attrs["kind"] == "penstock"
            ):
                line.attrs["tot_losses"] = totallosses1 + sing_losses
                tot_losses = float(line.attrs["tot_losses"])
                line.attrs["net_head"] = max(0.0, line.attrs["gross_head"] - tot_losses)
                if tot_losses > line.attrs["gross_head"]:

                    msgr.warning(("Losses greater than gross_head, %i" % (line.cat)))
                # net_head = float(line.attrs['net_head'])

            if line.attrs["kind"] == "conduct":
                line.attrs["tot_losses"] = line.attrs["net_head"] = 0

    struct.table.conn.commit()
    return list_intakeid


def compute_power(
    struct,
    list_intakeid,
    turbine_list,
    turbine_folder,
    efficiency_shaft,
    efficiency_alt,
    efficiency_transf,
):
    cols = [
        ("e_turbine", "DOUBLE"),
        ("turbine", "VARCHAR"),
        ("e_global", "DOUBLE"),
        ("power", "DOUBLE"),
        ("max_power", "VARCHAR(3)"),
    ]

    struct.rewind()
    add_columns(struct, cols)

    # TODO: make it more readable/pythonic
    for line in struct:
        # TODO: in one query
        net_head = float(line.attrs["net_head"])
        gross_head = float(line.attrs["gross_head"])
        discharge = float(line.attrs["discharge"])

        if net_head >= 0 and gross_head > 0 and discharge > 0:
            possible_turb = turb_char(net_head, discharge, turbine_list, turbine_folder)
            efficiency = np.zeros(len(possible_turb))

            for i in range(0, len(possible_turb)):
                file_in = open(
                    os.path.join(turbine_folder, "%s.txt" % (possible_turb[i]))
                )
                param = np.genfromtxt(file_in, dtype="f8")
                for j in range(7, len(param)):
                    if param[j, 0] == 1:
                        efficiency[i] = param[j, 1]

            if efficiency.any():
                eta = max(efficiency)
                for i in range(0, len(possible_turb)):
                    if efficiency[i] == eta:
                        kind_turbine = possible_turb[i]
            else:
                eta = 0.9
                kind_turbine = "not found"

            # TODO: names of the columns as inputs and check if already in the
            # shape file
            line.attrs["e_turbine"] = eta
            line.attrs["turbine"] = kind_turbine
            line.attrs["power"] = (
                9.81
                * net_head
                * discharge
                * eta
                * efficiency_shaft
                * efficiency_alt
                * efficiency_transf
            )
            # TODO: check with Julie results for the e_global
            line.attrs["e_global"] = (
                net_head * efficiency_alt * efficiency_transf / gross_head
            )
    struct.table.conn.commit()

    for i in range(0, len(list_intakeid)):
        struct.rewind()
        list_power = list(
            struct.table.execute(
                "SELECT power FROM %s WHERE intake_id=%i;"
                % (struct.table.name, list_intakeid[i][0])
            ).fetchall()
        )
        pmax = max(list_power)[0]
        for line in struct:
            if (
                line.attrs["intake_id"] == list_intakeid[i][0]
                and line.attrs["kind"] == "penstock"
            ):
                if line.attrs["power"] == pmax:
                    line.attrs["max_power"] = "yes"
                else:
                    line.attrs["max_power"] = "no"
    struct.table.conn.commit()


def load_turbines(
    list_turb,
    folder_turb,
    _cache=[
        None,
    ],
):
    def txt2py(txt):
        """Convert a text to an integer, float or string.

        >>> txt2py('a string')
        'a string'
        >>> txt2py('1234')
        1234
        >>> txt2py('12.34')
        12.34

        """
        if val.isdigit():
            # convert ot integer
            return int(txt)
        try:
            return float(val)
        except ValueError:
            return txt

    if _cache[0] is None:
        with open(list_turb) as tu:
            turbines = {turbine.strip(): None for turbine in tu.readlines()}

        for turb in turbines.keys():
            with open(os.path.join(folder_turb, "%s.txt" % (turb))) as file_in:
                params, append = {}, False
                for line in file_in:
                    key, val = line.strip().split()
                    if append:
                        params["qw/qd"].append(float(key))
                        params["eta"].append(float(val))
                    if key == "QW/Q_design":
                        params["qw/qd"] = []
                        params["eta"] = []
                        append = True
                    else:
                        params[key.lower()] = txt2py(val)
                turbines[turb] = params
        # add the parsed result to the function internal cache
        _cache[0] = turbines

    return _cache[0]


def turb_char(net_head, discharge, list_turb, folder_turb, ndigits=6):
    turbines_specifications = load_turbines(list_turb, folder_turb)
    turbines = {}
    for turb, spec in turbines_specifications.items():
        if (spec["q_min"] <= discharge <= spec["q_max"]) and (
            spec["dh_min"] <= net_head <= spec["dh_max"]
        ):
            flow = np.around(np.array(spec["qw/qd"]), ndigits)
            eta = np.around(np.array(spec["eta"]), ndigits)
            turbines[turb] = Turbine(
                name=turb,
                flow_proportion=flow,
                efficiency=eta,
                q_max=round(spec["q_max"], 3),
                q_min=round(spec["q_min"], 3),
                alpha_c=round(spec["alpha_c"], ndigits),
            )
    return list(turbines.keys())


def main(options, flags):
    TMPRAST = []
    DEBUG = True if flags["d"] else False
    atexit.register(cleanup, raster=TMPRAST, debug=DEBUG)

    elevation = options["elevation"]
    plant = options["plant"]
    output_struct = options["output_struct"]
    input_struct = options["input_struct"]
    output_plant = options["output_plant"]
    percentage_losses = float(options["percentage_losses"])
    roughness_penstock = float(options["roughness_penstock"])
    ks_derivation = float(options["ks_derivation"])
    turbine_folder = (
        options["turbine_folder"]
        if options["turbine_folder"]
        else os.path.join(os.path.abspath("."), "turbines")
    )
    turbine_list = (
        options["turbine_list"]
        if options["turbine_list"]
        else os.path.join(os.path.abspath("."), "turbines", "list.txt")
    )
    efficiency_shaft = float(options["efficiency_shaft"])
    efficiency_alt = float(options["efficiency_alt"])
    efficiency_transf = float(options["efficiency_transf"])

    # import ipdb; ipdb.set_trace()
    # c = flags['c']
    msgr = get_msgr()

    # import ipdb; ipdb.set_trace()

    TMPRAST.extend(["new_river", "buff_area"])
    if not gcore.overwrite():
        for m in TMPRAST:
            if gcore.find_file(m)["name"]:
                msgr.fatal(_("Temporary raster map %s exists") % (m))
                # FIXME:check if it works for vectors

    if options["output_point"]:
        conv_segpoints(plant, options["output_point"])

    # FIXME: gross_head coherent with plants
    # set the opions to execute the r.green.hydro.structure
    struct_opts = dict(
        elevation=elevation,
        plant=plant,
        output_struct=output_struct,
        ndigits=options["ndigits"],
        contour=options["contour"],
        overwrite=gcore.overwrite(),
    )
    if options["resolution"]:
        struct_opts["resolution"] = options["resolution"]
    ## --------------------------------------------------------------------------
    if output_struct:
        gcore.run_command("r.green.hydro.structure", **struct_opts)
        gcore.run_command("v.build", map=output_struct)
    else:
        output_struct = input_struct
        # FIXME: check the structure of the input file
    ## --------------------------------------------------------------------------
    gcore.run_command("g.copy", vector=(plant, output_plant))
    with VectorTopo(output_struct, mode="rw") as struct:
        list_intakeid = compute_losses(
            struct, options, percentage_losses, roughness_penstock, ks_derivation
        )

        compute_power(
            struct,
            list_intakeid,
            turbine_list,
            turbine_folder,
            efficiency_shaft,
            efficiency_alt,
            efficiency_transf,
        )

    with VectorTopo(output_plant, mode="rw") as out, VectorTopo(
        output_struct, mode="r"
    ) as struct:

        cols = [
            ("tot_losses", "DOUBLE"),
            ("net_head", "DOUBLE"),
            ("e_global", "DOUBLE"),
            ("power", "DOUBLE"),
        ]

        add_columns(out, cols)

        scols = "tot_losses", "net_head", "e_global", "power"
        wherecond = "plant_id={!r} AND kind LIKE {!r} AND max_power LIKE {!r}"
        for seg in out:
            where = wherecond.format(str(seg.attrs["plant_id"]), "penstock", "yes")
            sqlcode = (
                struct.table.filters.select(",".join(scols)).where(where).get_sql()
            )
            svalues = struct.table.execute(sqlcode).fetchone()
            if svalues:
                for col, value in zip(scols, svalues):
                    if value:
                        seg.attrs[col] = value
        out.table.conn.commit()

    power2energy(output_plant, "power", float(options["n"]))


if __name__ == "__main__":
    atexit.register(cleanup)
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
