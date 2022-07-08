#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MODULE:   	r.soillossbare.py

AUTHOR(S):  Martin Zbinden

PURPOSE:  	Calculate annual soil loss [t/(ha*a)] for bare croplands.
			Also use r.soillosscropland.py afterwards for grown soil.
			Source: Mitasova H, Mitas L, 1999. Modeling soil detachment
			with RUSLE 3d using GIS.
			http://skagit.meas.ncsu.edu/~helena/gmslab/erosion/usle.html

			@return out_soillossbare raster map and intermediate results


VERSION:  	0.2 (corrected flowacc calculation, added tempdir handling)

DATE:     	Mon Jun 16 21:00:00 CET 2014

COPYRIGHT:  (C) 2014 Martin Zbinden and by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

# %Module
# % description: Calculates annual soil loss [t/(ha*a)] for bare soil. Use r.soillosscropland.py afterwards for grown soil.
# % keyword: erosion
# % keyword: raster
# % keyword: bare soil
# % keyword: potential soilloss
# %end

# %option
# %  key: soillossbare
# %  type: string
# %  key_desc: name
# %  gisprompt: new,cell,raster
# %  description:  Output map (soilloss for ungrown soil)
# %  required: yes
# %end

# %option
# %  key: flowaccmethod
# %  key_desc: name
# %  description: Module for flowaccumulation calculation
# %  options: r.terraflow,r.flow,r.watershed
# %  answer: r.terraflow
# %  required: yes
# %  multiple:no
# %end

# %option
# %  key: elevation
# %  type: string
# %  key_desc: name
# %  gisprompt: old,cell,raster
# %  description: Digital Elevation Model
# %  required: yes
# %end

# %option
# %  key: resolution
# %  key_desc: float
# %  type: string
# %  description: Resolution of Digital Elevation Model (x y)
# %  required: yes
# %  answer: 2
# %end

# %option
# %  key: kfactor
# %  type: string
# %  key_desc: name
# %  gisprompt: old,cell,raster
# %  description: K-Factor (soil erodibility factor)
# %  required: yes
# %end

# %option
# %  key: rfactor
# %  key_desc: name
# %  type: string
# %  gisprompt: old,cell,raster
# %  description: R-Factor (rain erosivity factor)
# %  required: yes
# %end

# %option
# %  key: fieldblock
# %  key_desc: name
# %  type: string
# %  gisprompt: old,cell,raster
# %  description: Fieldblock raster map with NULL/0-values as barrier
# %  required: no
# %end

# %option
# %  key: map
# %  key_desc: name
# %  type: string
# %  gisprompt: old,vector,vector
# %  description: Fieldblock vector map
# %  required: no
# %end


# %option
# %  key: flowacc
# %  type: string
# %  key_desc: name
# %  gisprompt: old,cell,raster
# %  description: Flowaccumulation raster map (instead of calculation)
# %  required: no
# %end

# %option
# %  key: constant_m
# %  key_desc: float
# %  type: string
# %  description: RUSLE3D exponential m (0.2..0.6)
# %  answer: 0.4
# %  required: no
# %end

# %option
# %  key: constant_n
# %  key_desc: float
# %  type: string
# %  description: RUSLE3D exponential n (1.2..1.6)
# %  answer: 1.3
# %  required: no
# %end

# %flag
# %  key: r
# %  description: Remove intermediate results
# %end


import sys
import os
import grass.script as g
from grass.exceptions import CalledModuleError


class rusle_base(object):
    def __init__(self):

        # these variables are information for destructor
        self.temp_files_to_cleanup = []
        self.temp_dirs_to_cleanup = []

        self.params = {}
        self.tmp_rast = []

    def _debug(self, fn, msg):
        g.debug("%s.%s: %s" % (self.__class__.__name__, fn, msg))

    def __del__(self):
        # tries to remove temporary files, all files should be
        # removed before, implemented just in case of unexpected
        # stop of module
        for temp_file in self.temp_files_to_cleanup:
            g.try_remove(temp_file)
        pass

        for temp_dir in self.temp_dirs_to_cleanup:
            g.try_remove(temp_dir)
        pass

        if flag_r:
            self.removeTempRasters()

    def _tempfile(self):
        """!Create temp_file and append list self.temp_files_to_cleanup
            with path of file

        @return string path to temp_file
        """
        self._debug("_tempfile", "started")
        temp_file = g.tempfile()
        if temp_file is None:
            g.fatal(_("Unable to create temporary files"))

        # list of created tempfiles for destructor
        self.temp_files_to_cleanup.append(temp_file)
        self._debug("_tempfile", "finished")

        return temp_file

    def _tempdir(self):
        """!Create temp_dir and append list self.temp_dirs_to_cleanup
            with path of file

        @return string path to temp_dir
        """
        self._debug("_tempdir", "started")
        temp_dir = g.tempdir()
        if temp_dir is None:
            g.fatal(_("Unable to create temporary directory"))

        # list of created tempfiles for destructor
        self.temp_dirs_to_cleanup.append(temp_dir)
        self._debug("_tempdir", "finished")

        return temp_dir

    def removeTempRasters(self):
        for tmprast in self.tmp_rast:
            g.message('Removing "%s"' % tmprast)
            try:
                g.run_command(
                    "g.remove", flags="f", type="raster", name=tmprast, quiet=True
                )
            except CalledModuleError:
                g.warning(_("Removing temporary raster maps failed"))

    def rusle(self):
        """!main method in rusle_base
        controlling the whole process, once called by main()

        @return soillossbare name of output raster map
        """

        flowacc = outprefix + "flowacc"
        slope = outprefix + "slope"
        lsfactor = outprefix + "lsfactor"

        self.tmp_rast.append(flowacc)
        self.tmp_rast.append(slope)
        self.tmp_rast.append(lsfactor)

        global fieldblock
        if not fieldblock:
            if fieldblockvect:
                fieldblock = outprefix + "fieldblock"
                g.run_command(
                    "v.to.rast",
                    input=fieldblockvect,
                    output=fieldblock,
                    use="val",
                    value="1",
                    quiet=quiet,
                )
        if fieldblock:
            g.verbose('Raster map fieldblock is in "%s"' % fieldblock)
        else:
            fieldblock = ""

        if not options["flowacc"]:
            self._getFlowacc(elevation, flowacc, fieldblock)
            g.verbose('Raster map flowacc is in "%s".' % flowacc)
        else:
            g.verbose('Raster map flowacc taken from "%s".' % flowacc)

        self._getSlope(elevation, slope)
        g.verbose('Raster map slope is in  "%s"' % slope)

        self._getLsfac(flowacc, slope, lsfactor)
        g.verbose('Raster map lsfactor is in  "%s"' % lsfactor)

        self._getSoillossbare(lsfactor, kfactor, rfactor, soillossbare)
        g.message('Soilloss for bare soil in map "%s".' % soillossbare)

        stats = g.parse_command("r.univar", flags="g", map=soillossbare, delimiter="=")
        g.message(
            "mean = %s \n stddev = %s \n min = %s \n max = %s"
            % (stats["mean"], stats["stddev"], stats["min"], stats["max"])
        )

        return soillossbare

    def _getBarrier(self, fieldblock, barrier):
        formula = "$barrier = if(isnull($fieldblock),1,0)"
        g.mapcalc(formula, barrier=barrier, fieldblock=fieldblock, quiet=quiet)
        g.verbose('Raster map barrier is in "%s"' % barrier)
        return barrier

    def _getElevationFieldblock(self, elevation, fieldblock, elevationfieldblock):
        formula = "$elevationfieldblock = if(isnull($fieldblock),null(),$elevation)"
        g.mapcalc(
            formula,
            elevationfieldblock=elevationfieldblock,
            elevation=elevation,
            fieldblock=fieldblock,
            quiet=quiet,
        )
        g.verbose('Raster map elevationfieldblock is in "%s"' % elevationfieldblock)
        return elevationfieldblock

    def _getSlope(self, elevation, slope):
        """Hangneigung berechnen

        @return raster map name with slope
        """
        # Slope and aspect were computed using GRASS GIS 6.4.1 r.slope.aspect using a 2FD
        # algorithm (Zhou, 2004) and 3x3 pixels neighborhood, which is suitable for smoothed DEMs.

        g.run_command("r.slope.aspect", elevation=elevation, slope=slope, quiet=quiet)

        return slope

    def _getLsfac(self, flowacc, slope, lsfactor):
        """! Calculate LS factor
        flowaccumulation and slope are combined to LS-factor

        flowacc is uplslope area per unit width (measure of water flow, m²/m2),
        slope in degrees,
        22.1m is the length of standard USLE plot,
        0.09 = 9% = 5.15° ist slope of standard USLE plot,
        m and n are empirical constants

        Bemerkung zur Formel: gemäss Mitasova (1999) könnten die Exponenten m=0.2..0.6
        und n=1.0..1.3 an die Gegebenheiten angepasst werden.
        default: m=0.4, n=1.3 (Mitasova)

        @return raster map name with lsfac
        """

        constant_m = options["constant_m"]  # default 0.4
        constant_n = options["constant_n"]  # default 1.3
        resolution = options["resolution"]  # default 2

        # formula_lsfactor = "$lsfactor = 1.4*exp($flowacc* $resolution /22.1,$m)*exp(sin($slope)/0.09,$n)"
        # /22.13 nach Renard et al. 1997

        formula_lsfactor = "$lsfactor = (1+$m)*exp($flowacc * $resolution /22.1,$m)*exp(sin($slope)/0.09,$n)"

        g.mapcalc(
            formula_lsfactor,
            lsfactor=lsfactor,
            flowacc=flowacc,
            slope=slope,
            resolution=resolution,
            m=constant_m,
            n=constant_n,
            quiet=quiet,
        )

        return lsfactor

    def _getSoillossbare(self, lsfactor, kfactor, rfactor, soillossbare):
        """!Calculate soilloss on bare soil
        A = R * K * LS
        A potential soil loss t/(ha*a) for bare soil
        LS LS-factor
        R rain erosivity factor
        K soil erodibility factor

        @return
        """
        formula_soillossbare = "$soillossbare = $lsfactor * $kfactor * $rfactor"
        g.mapcalc(
            formula_soillossbare,
            soillossbare=soillossbare,
            lsfactor=lsfactor,
            kfactor=kfactor,
            rfactor=rfactor,
            quiet=quiet,
        )

        rules = "\n ".join(
            [
                "0.0000    37:114:0",
                "20.0000   88:169:1",
                "30.0000   207:229:3",
                "40.0000   254:254:0",
                "55.0000   240:60:1",
                "100.0000  254:0:2",
                "150.0000  169:0:1",
                "250.0000  115:0:0",
                "500.0000  87:0:0",
                "50000.0000  87:0:0",
            ]
        )

        g.write_command(
            "r.colors", map=soillossbare, rules="-", stdin=rules, quiet=quiet
        )

        return soillossbare


class rusle_flow(rusle_base):
    def _getFlowacc(self, elevation, flowacc, fieldblock):
        """!Flowaccumulation by module r.flow using SFD-algorithm

        @return flowacc raster map with upslope contributing area per cell width
        """
        if fieldblock:
            barrier = outprefix + "barrier"
            self.tmp_rast.append(barrier)
            barrier = self._getBarrier(fieldblock, barrier)
            g.run_command(
                "r.flow",
                elevation=elevation,
                barrier=barrier,
                flowaccumulation=flowacc,
                quiet=quiet,
            )

        else:
            g.run_command(
                "r.flow", elevation=elevation, flowaccumulation=flowacc, quiet=quiet
            )

        return flowacc


class rusle_watershed(rusle_base):
    def _getFlowacc(self, elevation, flowacc, fieldblock):
        """!Flowaccumulation by module r.watershed

        @return flowacc raster map with upslope contributing area per cell width
        """
        self._debug("_getFlowacc", "started")
        if fieldblock:
            elevationfieldblock = outprefix + "elevationfieldblock"
            self.tmp_rast.append(elevationfieldblock)
            self._getElevationFieldblock(elevation, fieldblock, elevationfieldblock)
            elevation = elevationfieldblock

        g.run_command(
            "r.watershed",
            flags="a",
            elevation=elevation,
            accumulation=flowacc,
            # threshold=10,
            # convergence = 10,
            quiet=quiet,
        )
        self._debug("_getFlowacc", "finished")
        return flowacc


class rusle_terraflow(rusle_base):
    def _getFlowacc(self, elevation, flowacc, fieldblock):
        """!Flowaccumulation by module r.terraflow using MFD-algorithm

        @return flowacc raster map with upslope contributing area per cell width
        """
        self._debug("_getFlowacc", "started")
        if fieldblock:
            elevationfieldblock = outprefix + "elevationfieldblock"
            self.tmp_rast.append(elevationfieldblock)
            self._getElevationFieldblock(elevation, fieldblock, elevationfieldblock)
            elevation = elevationfieldblock

        raster = {}
        for map in ["filled", "direction", "swatershed", "tci"]:
            raster[map] = outprefix + map
            self.tmp_rast.append(raster[map])

        statsfile = self._tempfile()
        streamdir = self._tempdir()

        g.run_command(
            "r.terraflow",
            elevation=elevation,
            filled=raster["filled"],
            direction=raster["direction"],
            swatershed=raster["swatershed"],
            accumulation=flowacc,
            tci=raster["tci"],
            stats=statsfile,
            stream_dir=streamdir,
            quiet=quiet,
        )

        g.mapcalc(
            "$flowacc = $flowacc / $resolution",
            overwrite=True,
            flowacc=flowacc,
            resolution=resolution,
        )
        self._debug("_getFlowacc", "finished")
        return flowacc


def main():
    """
    begin main

    """

    global soillossbare
    global outprefix
    global flowaccmethod
    global elevation
    global kfactor
    global rfactor
    global resolution

    global flowacc
    global fieldblock
    global fieldblockvect

    global flag_r
    global quiet
    global options
    global flags

    soillossbare = options["soillossbare"]
    outprefix = soillossbare + "_"
    flowaccmethod = options["flowaccmethod"]
    flowacc = options["flowacc"]
    elevation = options["elevation"]
    kfactor = options["kfactor"]
    rfactor = options["rfactor"]
    resolution = options["resolution"]
    # fieldblock = None
    fieldblock = options["fieldblock"]
    fieldblockvect = options["map"]

    flag_r = flags["r"]  # remove temp maps

    quiet = True
    if g.verbosity() > 2:
        quiet = False

    g.run_command("g.region", flags="a", res=resolution)

    if flowacc:
        g.info("Using flowaccumulation from input raster map %s ..." % flowacc)
        ruslealg = rusle_base()

    elif flowaccmethod == "r.terraflow":
        g.info("Using flowaccumulation from module r.terraflow (MFD) ...")
        ruslealg = rusle_terraflow()

    elif flowaccmethod == "r.flow":
        g.info("Using flowaccumulation from module r.flow (SFD) ...")
        ruslealg = rusle_flow()

    elif flowaccmethod == "r.watershed":
        g.info("Using flowaccumulation from module r.watershed (MFD) ...")
        ruslealg = rusle_watershed()

    p = ruslealg.rusle()

    if flag_r:
        remove = ruslealg.removeTempRasters()

    return


if __name__ == "__main__":
    options, flags = g.parser()
    sys.exit(main())
