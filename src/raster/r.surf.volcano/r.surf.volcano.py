#!/usr/bin/env python3
############################################################################
#
# MODULE:       r.surf.volcano
#
# AUTHOR:       M. Hamish Bowman, Dept. of Geology, University of Otago
#                        Dunedin, New Zealand
#               Ported to Python from GRASS 6 addons shell script 8/2024
#
# PURPOSE:      Create an artificial surface resembling a seamount or cone volcano
#
# COPYRIGHT:    (c) 2009-2024 Hamish Bowman, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#                This program is distributed in the hope that it will be useful,
#                but WITHOUT ANY WARRANTY; without even the implied warranty of
#                MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#                GNU General Public License for more details.
#
#############################################################################

# %Module
# % description: Creates an artificial surface resembling a seamount or cone volcano.
# % keyword: raster
# %End
# %Option G_OPT_R_OUTPUT
# %End
# %Option
# % key: peak
# % type: double
# % required: no
# % description: Height of cone
# % answer: 1000.0
# %End
# %Option
# % key: crater
# % type: double
# % required: no
# % label: Depth of crater below the cone
# % description: A larger (deeper) value here also means a wider crater.
# % answer: 0.0
# %End
# %Option
# % key: method
# % type: string
# % required: no
# % description: Mathematical function for creating the mountain
# % answer: polynomial
# % options: polynomial,gaussian,lorentzian,logarithmic,exponential
# % descriptions: polynomial;1/distance^n;gaussian;Gaussian function;lorentzian;Cauchy-Lorentz distribution;logarithmic;Logarithmic decay;exponential;Exponential decay
# %End
# %Option
# % key: friction
# % type: integer
# % required: no
# % options: 1-25
# % label: Polynomial friction of distance, (the 'n' in 1/d^n)
# % description: Higher values generate steeper slopes. (only used with the polynomial method)
# % answer: 6
# %End
# # FIXME: ok, it isn't really kurtosis but it's similar and I couldn't
# #        think of a better name.
# %Option
# % key: kurtosis
# % type: double
# % required: no
# % label: Slope steepness (used with all methods except polynomial)
# % description: For Gaussian: nearer to 0 is flatter, higher values generate steeper slopes. For Lorentzian, logarithmic, and exponential the opposite is true.
# % answer: 1.0
# %End
# %Option
# % key: sigma
# % type: double
# % required: no
# % label: Surface roughness factor
# % description: Nearer to 0 is smoother, higher values make a rougher surface.
# % answer: 1.0
# %End
# %Flag
# % key: r
# % description: Roughen the surface
# %End

import os
import sys
from math import pi
from grass.script import core as gc
from grass.script import raster as gr

# from grass.exceptions import CalledModuleError


def remove_rast(maps):
    """Remove raster maps"""
    gc.run_command("g.remove", flags="f", quiet=True, type="rast", name=maps)


def main():
    outmap = options["output"]
    method = options["method"]
    friction = options["friction"]
    peak = options["peak"]
    crater = options["crater"]
    sigma = options["sigma"]
    kurtosis = options["kurtosis"]

    tmp_base = "tmp__rsv_%d" % os.getpid()
    map_dist_units = "%s_dist_units" % tmp_base
    map_dist_norm = "%s_dist_norm" % tmp_base
    map_peak = "%s_peak" % tmp_base
    map_surf = "%s_surf" % tmp_base

    gc.verbose(_("Finding cost from center of current region ..."))

    region = gc.region(complete=True)

    gr.mapcalc(
        "$mdu = sqrt( (x() - $ce)^2 + (y() - $cn)^2 )",
        mdu=map_dist_units,
        ce=region["center_easting"],
        cn=region["center_northing"],
    )

    gc.verbose(_("Normalizing cost map ..."))
    rinfo = gr.raster_info(map_dist_units)

    if method == "polynomial":
        # Normalize with 1 in the center and 0 at outer edge
        # r.mapcalc "volc.dist_norm.$$ = ($max - volc.dist_units.$$) / $max"
        gr.mapcalc(
            "$mdn = ($max - $mdu) / $max",
            max=rinfo["max"],
            mdn=map_dist_norm,
            mdu=map_dist_units,
        )
    else:
        # Normalize with 0 in the center and 1 at outer edge
        # r.mapcalc "volc.dist_norm.$$ = volc.dist_units.$$ / $max"
        gr.mapcalc(
            "$mdn = $mdu / $max",
            max=rinfo["max"],
            mdn=map_dist_norm,
            mdu=map_dist_units,
        )

    ##               ##
    # create peak map #
    ##               ##

    if method == "polynomial":
        gc.verbose(_("Creating IDW surface ..."))
        # r.mapcalc "volc.peak.$$ = ($PEAK + abs($CRATER) ) \
        #    * pow( volc.dist_norm.$$, $FRICTION )"
        gr.mapcalc(
            "$mp = ($pk + abs($crat)) * pow($mdn, $fric)",
            mp=map_peak,
            pk=peak,
            crat=crater,
            mdn=map_dist_norm,
            fric=friction,
        )
    elif method == "gaussian":
        gc.verbose(_("Creating Gaussian surface ..."))
        # % description: Use a Gaussian curve instead of 1/(d^n) for radial basis function
        # normalized Gaussian curve:  f(x) = a * e^( (x-b)^2 / 2*(c^2) )
        #  parameters: a = 1/(sigma*sqrt(2pi)), b = mu, c = sigma
        #  mu is mean value and sigma^2 is variance.
        #  so we only need b,c. and b can be locked at 0 here. so user only needs
        #  to give sigma (width)
        #  thus r.mapcalc expr could look like
        #   f(distance) = ( 1 / ($SIGMA*sqrt(2*$PI)) ) * exp( -1* $DIST^2 / (2 * $SIGMA^2) )

        map_gauss = "%s_gauss" % tmp_base
        SIGMA_C = 1.0

        ## FIXME: the 10*kurtosis stuff is a completely bogus hack!
        # r.mapcalc "volc.gauss.$$ = \
        #   ( 1 / ( $SIGMA_C * sqrt(2 * $PI) ) ) \
        #   * exp( -1* (10 * $KURTOSIS * volc.dist_norm.$$)^2 / (2 * $SIGMA_C^2) )"
        gr.mapcalc(
            "$mg = ( 1 / ( $sigC * sqrt(2 * $pi) ) ) \
                    * exp( -1* (10 * $kt * $mdn)^2 / (2 * $sigC^2) )",
            mg=map_gauss,
            sigC=SIGMA_C,
            pi=pi,
            kt=kurtosis,
            mdn=map_dist_norm,
        )

        rinfo = gr.raster_info(map_gauss)
        gc.verbose(_("Normalizing Gaussian surface ..."))
        # r.mapcalc "volc.peak.$$ = \
        #     ( ($PEAK + abs($CRATER) ) / $max ) * volc.gauss.$$"
        gr.mapcalc(
            "$mp = ( ($pk + abs($crat) ) / $max ) * $mg",
            mp=map_peak,
            pk=peak,
            crat=crater,
            max=rinfo["max"],
            mg=map_gauss,
        )

        remove_rast(map_gauss)
    elif method == "lorentzian":
        # Cauchy-Lorentz fn: f(distance, gamma, height) =
        #     height_of_peak * ( gamma^2 / ( distance^2 + gamma^2) )
        #  where gamma is the scale parameter giving half-width at half-maximum.
        gc.verbose(_("Creating Lorentzian surface ..."))
        # r.mapcalc "volc.peak.$$ = ($PEAK + abs($CRATER) ) \
        #    * ( ($KURTOSIS * 0.1)^2 / ( volc.dist_norm.$$ ^2 + ($KURTOSIS * 0.1)^2) )"
        gr.mapcalc(
            "$mp = ($pk + abs($crat) ) * ( ($kt * 0.1)^2 / ($mdn^2 + ($kt * 0.1)^2) )",
            mp=map_peak,
            pk=peak,
            crat=crater,
            kt=kurtosis,
            mdn=map_dist_norm,
        )
    elif method == "exponential":
        # exponential:  1 / ((e^distance) -1)
        gc.verbose(_("Creating exponential decay surface ..."))
        map_exp = "%s_exp" % tmp_base

        # r.mapcalc "volc.exp.$$ = 1 / (exp(volc.dist_norm.$$ / $KURTOSIS) - 0.9)"
        gr.mapcalc(
            "$me = 1 / ( exp($mdn / $kt)  ) - 0.9",
            me=map_exp,
            mdn=map_dist_norm,
            kt=kurtosis,
        )
        rinfo = gr.raster_info(map_exp)

        gc.verbose(_("Normalizing exponential surface ..."))
        # r.mapcalc "volc.peak.$$ = \
        #     ( ($PEAK + abs($CRATER) ) / $max ) * volc.exp.$$"
        gr.mapcalc(
            "$mp = ( ($pk + abs($crat) ) / $max ) * $me",
            mp=map_peak,
            pk=peak,
            crat=crater,
            max=rinfo["max"],
            me=map_exp,
        )

        remove_rast(map_exp)
    elif method == "logarithmic":
        # logarithmic:  1 / ( (d+1)^2 * log(d+1) )
        gc.verbose(_("Creating logarithmic decay surface ..."))
        map_log = "%s_log" % tmp_base

        # r.mapcalc "volc.log.$$ = 1 /  \
        #   ( (volc.dist_norm.$$ + pow(1.15,$KURTOSIS))^2 \
        #     * log((volc.dist_norm.$$) + pow(1.15,$KURTOSIS)) )"
        gr.mapcalc(
            "$ml = 1 / ( ($mdn + pow(1.15, $kt))^2 * log(($mdn) + pow(1.15, $kt)) )",
            ml=map_log,
            mdn=map_dist_norm,
            kt=kurtosis,
        )

        rinfo = gr.raster_info(map_log)
        gc.verbose(_("Normalizing logarithmic surface ..."))
        # r.mapcalc "volc.peak.$$ = \
        #     ( ($PEAK + abs($CRATER) ) / $max ) * volc.log.$$"
        gr.mapcalc(
            "$mp = ( ($pk + abs($crat) ) / $max ) * $ml",
            mp=map_peak,
            pk=peak,
            crat=crater,
            max=rinfo["max"],
            ml=map_log,
        )

        remove_rast(map_log)
    else:
        gc.error("Programmer error, method = <%s>" % method)
        sys.exit(1)

    if flags["r"]:
        # roughen it up a bit
        gc.verbose(_("Creating random Gaussian mottle ..."))
        map_surf_gauss = "%s_surf_gauss" % tmp_base
        map_peak_rough = "%s_peak_rough" % tmp_base

        gc.run_command("r.surf.gauss", output=map_surf_gauss, sigma=sigma)

        gc.verbose(_("Applying Gaussian mottle ..."))
        # r.mapcalc "volc.peak_rough.$$ = \
        #     volc.peak.$$ + (volc.surf_gauss.$$ * $PEAK/400 )"
        gr.mapcalc(
            "$vpr = $vp + ($vsg * $pk/400)",
            vpr=map_peak_rough,
            vp=map_peak,
            vsg=map_surf_gauss,
            pk=peak,
        )

        gc.run_command("g.rename", raster=(map_peak_rough, map_surf), quiet=True)
        remove_rast([map_surf_gauss, map_peak])

    else:  # no '-r'
        gc.run_command("g.rename", raster=(map_peak, map_surf), quiet=True)

    remove_rast([map_dist_units, map_dist_norm])

    if float(crater) != 0:
        gc.verbose(_("Creating crater ..."))
        map_combo = "%s_full" % tmp_base
        # r.mapcalc "volc.full.$$ = if( volc.surf.$$ > $PEAK, \
        #     2*$PEAK - volc.surf.$$, volc.surf.$$ )"
        gr.mapcalc(
            "$vc = if($vs > $pk, 2*$pk - $vs, $vs)", vc=map_combo, vs=map_surf, pk=peak
        )

        gc.run_command("g.rename", raster=(map_combo, outmap), quiet=True)
        remove_rast(map_surf)

    else:
        gc.run_command("g.rename", raster=(map_surf, outmap), quiet=True)

    # DCELL is overkill here, convert what we made into FCELL
    outmapD = "%s_DCELL" % tmp_base
    gc.run_command("g.rename", raster=(outmap, outmapD), quiet=True)
    gr.mapcalc("$out = float($outD)", out=outmap, outD=outmapD, quiet=True)
    remove_rast(outmapD)

    # test if it worked
    if not gc.find_file(outmap, mapset=".")["name"]:
        gc.error(_("Surface creation failed"))
        sys.exit(1)

    # write metadata
    gc.run_command(
        "r.support",
        map=outmap,
        description="generated by r.surf.volcano",
        source1="Peak height = %s" % peak,
        title="Artificial surface resembling a seamount or cone volcano",
    )

    if flags["r"]:
        gc.run_command(
            "r.support",
            map=outmap,
            history="Surface roughness used a Gaussian deviate with sigma of %s."
            % sigma,
        )

    if float(crater) != 0:
        gc.run_command("r.support", map=outmap, history="Crater depth %s." % crater)

    if method == "polynomial":
        s2msg = "Polynomial surface with friction of distance = %s" % friction
    elif method == "gaussian":
        s2msg = "Gaussian surface with pseudo-kurtosis factor = %s" % kurtosis
    elif method == "lorentzian":
        s2msg = "Lorentzian surface with pseudo-kurtosis factor = %s" % kurtosis
    elif method == "exponential":
        s2msg = "Exponential decay surface with pseudo-kurtosis factor = %s" % kurtosis
    elif method == "logarithmic":
        s2msg = "Logarithmic decay surface with pseudo-kurtosis factor = %s" % kurtosis
    else:
        gc.error("Programmer error, method = <%s>" % method)
        sys.exit(1)

    gc.run_command("r.support", map=outmap, source2=s2msg)

    # perhaps,
    # r.colors map=output color=srtm --quiet

    # cleanup on abort/cancel
    # FIXME: superquiet isn't
    # TODO: make tmp_base global and move into cleanup_rast() error fn
    # gc.run_command(
    #    "g.remove", flags="f", superquiet=True, type="rast", patt="%s_*" % tmp_base
    # )

    gc.verbose(_("Done."))


if __name__ == "__main__":
    options, flags = gc.parser()
    main()
