#!/usr/bin/env python

############################################################################
#
# MODULE: i.image.bathymetry
# AUTHOR(S): Vinayaraj Poliyapram <vinay223333@gmail.com> and Luca Delulucchi
#
# PURPOSE:   Script for estimating bathymetry from optical satellite images
# COPYRIGHT: (C) Vinayaraj Poliyapram and by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Estimates Satellite Derived Bathymetry (SDB) from multispectral images.
# % keyword: imagery
# % keyword: bathymetry
# % keyword: satellite
# %end
# %option G_OPT_R_INPUT
# % key: blue_band
# %required: no
# %end
# %option G_OPT_R_INPUT
# % key: green_band
# %required: yes
# %end
# %option G_OPT_R_INPUT
# % key: red_band
# %required: yes
# %end
# %option G_OPT_R_INPUT
# % key: nir_band
# %required: yes
# %end
# %option G_OPT_R_INPUT
# % key: band_for_correction
# %required: yes
# %end
# %option G_OPT_V_INPUT
# % key: calibration_points
# %required: yes
# %end
# %option G_OPT_V_INPUT
# % key: area_of_interest
# %required: no
# %end
# %option G_OPT_R_INPUT
# % key: additional_band1
# %required: no
# %end
# %option G_OPT_R_INPUT
# % key: additional_band2
# %required: no
# %end
# %option G_OPT_R_INPUT
# % key: additional_band3
# %required: no
# %end
# %option G_OPT_R_INPUT
# % key: additional_band4
# %required: no
# %end
# %option G_OPT_R_OUTPUT
# % key: depth_estimate
# %required: yes
# %end
# %option
# % key: tide_height
# %type: double
# %multiple: no
# %required: no
# %description: Tide correction to the time of satellite image capture
# %end
# %option G_OPT_DB_COLUMN
# % key: calibration_column
# %required: yes
# %description: Name of the column which stores depth values
# %end
# %flag
# %key: f
# %description: select if only want to run Fixed-GWR model
# %end
# %flag
# %key: b
# %description: select kernel function as bi-square
# %end

import atexit
import grass.script as g
from grass.pygrass.raster import RasterRow
import subprocess
import os

crctd_lst = []


def main():
    options, flags = g.parser()
    Blue = options["blue_band"]
    Green = options["green_band"]
    Red = options["red_band"]
    NIR = options["nir_band"]
    SWIR = options["band_for_correction"]
    Calibration_points = options["calibration_points"]
    Area_of_interest = options["area_of_interest"]
    Additional_band1 = options["additional_band1"]
    Additional_band2 = options["additional_band2"]
    Additional_band3 = options["additional_band3"]
    Additional_band4 = options["additional_band4"]
    bathymetry = options["depth_estimate"]
    tide_height = options["tide_height"]
    calibration_column = options["calibration_column"]
    bisquare = flags["b"]
    fixed_GWR = flags["f"]

    res = g.parse_command("g.region", raster=Green, flags="g")
    g.run_command(
        "v.to.rast",
        input=Calibration_points,
        type="point",
        use="attr",
        attribute_column=calibration_column,
        output="tmp_Calibration_points",
    )
    # hull generation from calibration depth points
    g.run_command("v.hull", input=Calibration_points, output="tmp_hull", overwrite=True)
    # buffer the hull to ceate a region for including all calibration points
    g.run_command(
        "v.buffer",
        input="tmp_hull",
        output="tmp_buffer",
        distance=float(res["nsres"]),
        overwrite=True,
    )
    if tide_height:
        cal = g.parse_command("r.univar", map="tmp_Calibration_points", flags="g")
        if float(cal["min"]) >= 0:
            t = float(tide_height)
            g.mapcalc(
                exp="{d}=({d}+float({t}))".format(d="tmp_Calibration_points", t=t),
                overwrite=True,
            )
        if float(cal["min"]) < 0:
            t = float(tide_height) * -1
            g.mapcalc(
                exp="{d}=({d}+float({t}))".format(d="tmp_Calibration_points", t=t),
                overwrite=True,
            )
    g.mapcalc(
        exp="{tmp_ratio}=({Green}/{SWIR})".format(
            tmp_ratio="tmp_ratio", Green=Green, SWIR=SWIR
        )
    )
    g.mapcalc(
        exp="{tmp_NDVI}=float({NIR}-{Red})/float({NIR}+{Red})".format(
            tmp_NDVI="tmp_NDVI", NIR=NIR, Red=Red
        )
    )
    g.mapcalc(
        exp="{tmp_water}=if({tmp_ratio} < 1, null(), if({tmp_NDVI} <"
        "0, {tmp_ratio}, null()))".format(
            tmp_NDVI="tmp_NDVI", tmp_water="tmp_water", tmp_ratio="tmp_ratio"
        )
    )
    g.run_command("r.mask", raster="tmp_water", overwrite=True)
    li = [
        Green,
        Additional_band1,
        Additional_band2,
        Additional_band3,
        Additional_band4,
        Blue,
        Red,
    ]
    for i in li:
        j, sep, tail = i.partition("@")
        tmp_ = RasterRow(str(i))
        if tmp_.exist() is False:
            continue
        g.message("Ditermining minimum value for %s" % i)
        g.run_command("g.region", vector=Calibration_points)
        # To ignore zero values
        g.mapcalc(
            exp="{tmp_b}=if({x}>1, {x},null())".format(tmp_b="tmp_b", x=str(i)),
            overwrite=True,
        )
        tmp_AOI = g.parse_command("r.univar", map="tmp_b", flags="g")
        tmp_AOI_min = float(tmp_AOI["min"])
        g.run_command("g.region", raster=Green)
        try:
            g.mapcalc(
                exp="{tmp_deep}=if({tmp_band}<{band_min}, {tmp_band},"
                "null())".format(
                    tmp_deep="tmp_deep", band_min=tmp_AOI_min, tmp_band=str(i)
                ),
                overwrite=True,
            )
            g.run_command("r.mask", raster="tmp_deep", overwrite=True)
            tmp_coe = g.parse_command(
                "r.regression.line", mapx=SWIR, mapy=str(i), flags="g"
            )
            g.message("Deep water ditermination for %s" % i)
            if Area_of_interest:
                g.run_command("r.mask", vector=Area_of_interest, overwrite=True)
                g.run_command("g.region", vector=Area_of_interest)
            else:
                g.run_command("r.mask", vector="tmp_buffer", overwrite=True)
                g.run_command("g.region", vector=Calibration_points)
            g.mapcalc(
                exp="{tmp_crct}=log({tmp_band}-{a}-{b}*{SWIR})".format(
                    tmp_crct="tmp_crct" + str(j),
                    tmp_band=str(i),
                    a=float(tmp_coe["a"]),
                    b=float(tmp_coe["b"]),
                    SWIR=SWIR,
                ),
                overwrite=True,
            )
            g.run_command("r.mask", raster="tmp_water", overwrite=True)
            g.mapcalc(
                "{tmp_crctd} = ({tmp_crct} * 1)".format(
                    tmp_crct="tmp_crct" + str(j), tmp_crctd="tmp_crctd" + str(j)
                )
            )
        except:
            g.message("Cannot find deep water pixels")
            if Area_of_interest:
                g.run_command("r.mask", vector=Area_of_interest, overwrite=True)
                g.run_command("g.region", vector=Area_of_interest)
            else:
                g.run_command("r.mask", vector="tmp_buffer", overwrite=True)
                g.run_command("g.region", vector=Calibration_points)
            g.mapcalc(
                exp="{tmp_crct}=log({tmp_band}-{a}-{b}*{SWIR})".format(
                    tmp_crct="tmp_crct" + str(j),
                    tmp_band=str(i),
                    a=float(tmp_coe["a"]),
                    b=float(tmp_coe["b"]),
                    SWIR=SWIR,
                ),
                overwrite=True,
            )
            g.run_command("r.mask", raster="tmp_water", overwrite=True)
            g.mapcalc(
                "{tmp_crctd} = ({tmp_crct} * 1)".format(
                    tmp_crct="tmp_crct" + str(j), tmp_crctd="tmp_crctd" + str(j)
                )
            )
        crctd_lst.append("tmp_crctd" + str(j))
    if fixed_GWR:
        if not g.find_program("r.gwr", "--help"):
            g.run_command("g.extension", extension="r.gwr")
        if bisquare:
            g.message("Calculating optimal bandwidth using bisqare kernel...")
            bw = g.parse_command(
                "r.gwr",
                mapx=crctd_lst,
                mapy="tmp_Calibration_points",
                kernel="bisquare",
                flags="ge",
            )
            g.message("Running Fixed-GWR using bisqare kernel...")
            g.run_command(
                "r.gwr",
                mapx=crctd_lst,
                mapy="tmp_Calibration_points",
                estimates="tmp_bathymetry",
                kernel="bisquare",
                bandwidth=int(bw["estimate"]),
            )
        else:
            g.message("Calculating optimal bandwidth using gaussian kernel...")
            bw = g.parse_command(
                "r.gwr", mapx=crctd_lst, mapy="tmp_Calibration_points", flags="ge"
            )
            g.message("Running Fixed-GWR using gaussian kernel...")
            g.run_command(
                "r.gwr",
                mapx=crctd_lst,
                mapy="tmp_Calibration_points",
                estimates="tmp_bathymetry",
                bandwidth=int(bw["estimate"]),
            )
    else:
        global r
        global predict
        try:
            # For GWmodel in R
            r = g.tempfile()
            r_file = open(r, "w")
            libs = ["GWmodel", "data.table", "rgrass7", "rgdal", "raster"]
            for i in libs:
                install = 'if(!is.element("%s", installed.packages()[,1])){\n' % i
                install += "cat('\\n\\nInstalling %s package from CRAN\n')\n" % i
                install += "if(!file.exists(Sys.getenv('R_LIBS_USER'))){\n"
                install += "dir.create(Sys.getenv('R_LIBS_USER'), recursive=TRUE)\n"
                install += ".libPaths(Sys.getenv('R_LIBS_USER'))}\n"
                install += (
                    'install.packages("%s", repos="http://cran.us.r-'
                    'project.org")}\n' % i
                )
                r_file.write(install)
                libraries = "library(%s)\n" % i
                r_file.write(libraries)
            Green_new, sep, tail = Green.partition("@")
            r_file.write('grass_file = readRAST("tmp_crctd%s")\n' % Green_new)
            r_file.write("raster_file = raster(grass_file)\n")
            frame_file = "pred = as.data.frame(raster_file,na.rm = TRUE,xy = TRUE)\n"
            r_file.write(frame_file)
            for i in li:
                j, sep, tail = i.partition("@")
                Green_new, sep, tail = Green.partition("@")
                tmp_ = RasterRow(str(i))
                if tmp_.exist() is False:
                    continue
                r_file.write('grass_file = readRAST("tmp_crctd%s")\n' % j)
                r_file.write("raster_file = raster(grass_file)\n")
                r_file.write(
                    "frame_pred%s = as.data.frame(raster_file, na.rm = TRUE,"
                    "xy = TRUE)\n" % j
                )
                pred_file = "frame_pred_green=data.frame(frame_pred%s)\n" % Green_new
                pred_file += "pred=merge(pred, frame_pred%s)\n" % j
                r_file.write(pred_file)
                # For reference_file repeat with MASK
                g.run_command("r.mask", raster="tmp_Calibration_points", overwrite=True)
                r_file.write('grass_file=readRAST("%s")\n' % "tmp_Calibration_points")
                r_file.write("raster_file = raster(grass_file)\n")
                frame_file = (
                    "calib = as.data.frame(raster_file,na.rm = TRUE ," "xy = TRUE)\n"
                )
                r_file.write(frame_file)
            for i in li:
                j, sep, tail = i.partition("@")
                tmp_ = RasterRow(str(i))
                if tmp_.exist() is False:
                    continue
                r_file.write('grass_file = readRAST("tmp_crctd%s")\n' % j)
                r_file.write("raster_file = raster(grass_file)\n")
                r_file.write(
                    "frame_ref%s = as.data.frame(raster_file,na.rm = TRUE,"
                    "xy = TRUE)\n" % j
                )
                ref_file = "calib = merge(calib, frame_ref%s)\n" % j
                r_file.write(ref_file)
            g.run_command("g.remove", type="raster", pattern="MASK", flags="f")
            ref_file = "Rapid_ref.sdf=SpatialPointsDataFrame(calib[,1:2],calib)\n"
            ref_file += "Rapid_pred.sdf=SpatialPointsDataFrame(pred[,1:2]," "pred)\n"
            ref_file += (
                "DM_Rapid_ref.sdf=gw.dist(dp.locat=coordinates" "(Rapid_ref.sdf))\n"
            )
            r_file.write(ref_file)
            l = []
            predict = g.read_command("g.tempfile", pid=os.getpid()).strip() + ".txt"
            # Join the corrected bands in to a string
            le = len(crctd_lst)
            for i in crctd_lst:
                l.append(i)
                k = "+".join(l)
            if bisquare:
                ref_flag = (
                    "cat('\nCalculating optimal bandwidth using "
                    "bisquare kernel..\n')\n"
                )
                ref_flag += (
                    "BW_Rapid_ref.sdf=bw.gwr(tmp_Calibration_points~%s,"
                    'data=Rapid_ref.sdf, kernel="bisquare",'
                    "adaptive=TRUE, dMat=DM_Rapid_ref.sdf)\n" % k
                )
                ref_flag += "cat('\nCalculating euclidean distance\n')\n"
                ref_flag += (
                    "DM_Rapid_pred.sdf=gw.dist(dp.locat=coordinates"
                    "(Rapid_ref.sdf), rp.locat=coordinates"
                    "(Rapid_pred.sdf))\n"
                )
                ref_flag += "cat('\nRunning A-GWR using bisquare kernel\n')\n"
                ref_flag += (
                    "GWR_Rapid_pred.sdf=gwr.predict(tmp_Calibration_poi"
                    "nts~%s,data=Rapid_ref.sdf, bw = BW_Rapid_ref.sdf,"
                    'predictdata = Rapid_pred.sdf, kernel = "bisquare",'
                    "adaptive = TRUE, dMat1 = DM_Rapid_pred.sdf,"
                    "dMat2 = DM_Rapid_ref.sdf)\n" % k
                )
                r_file.write(ref_flag)
            if not bisquare:
                ref_fla = (
                    "cat('\nCalculating optimal bandwidth using "
                    "gaussian kernel..\n')\n"
                )
                ref_fla += (
                    "BW_Rapid_ref.sdf=bw.gwr(tmp_Calibration_points~%s,"
                    'data=Rapid_ref.sdf, kernel="gaussian",'
                    "adaptive=TRUE, dMat= DM_Rapid_ref.sdf)\n" % k
                )
                ref_fla += "cat('\nCalculating euclidean distance\n')\n"
                ref_fla += (
                    "DM_Rapid_pred.sdf=gw.dist(dp.locat=coordinates"
                    "(Rapid_ref.sdf), rp.locat=coordinates"
                    "(Rapid_pred.sdf))\n"
                )
                ref_fla += "cat('\nRunning A-GWR using gaussian kernel\n')\n"
                ref_fla += (
                    "GWR_Rapid_pred.sdf = gwr.predict(tmp_Calibration_poi"
                    "nts~%s,data=Rapid_ref.sdf, bw=BW_Rapid_ref.sdf,"
                    'predictdata = Rapid_pred.sdf, kernel = "gaussian",'
                    "adaptive = TRUE, dMat1 = DM_Rapid_pred.sdf,"
                    "dMat2 = DM_Rapid_ref.sdf)\n" % k
                )
                r_file.write(ref_fla)
            ref_fil = "Sp_frame = as.data.frame(GWR_Rapid_pred.sdf$SDF)\n"
            r_file.write(ref_fil)
            export = 'write.table(Sp_frame, quote=FALSE, sep=",",' '"%s")\n' % predict
            r_file.write(export)
            r_file.close()
            subprocess.check_call(["Rscript", r], shell=False)
            g.run_command(
                "r.in.xyz",
                input=predict,
                output="tmp_bathymetry",
                skip=1,
                separator=",",
                x=(int(le) + 5),
                y=(int(le) + 6),
                z=(int(le) + 3),
                overwrite=True,
            )
        except subprocess.CalledProcessError:
            g.message("Integer outflow... ")
            if not g.find_program("r.gwr", "--help"):
                g.run_command("g.extension", extension="r.gwr")
            if bisquare:
                g.message("Running Fixed-GWR using bisqare kernel...")
                bw = g.parse_command(
                    "r.gwr",
                    mapx=crctd_lst,
                    mapy="tmp_Calibration_points",
                    kernel="bisquare",
                    flags="ge",
                )
                g.run_command(
                    "r.gwr",
                    mapx=crctd_lst,
                    mapy="tmp_Calibration_points",
                    estimates="tmp_bathymetry",
                    kernel="bisquare",
                    bandwidth=int(bw["estimate"]),
                )
            else:
                g.message("Running Fixed-GWR using gaussian kernel...")
                bw = g.parse_command(
                    "r.gwr", mapx=crctd_lst, mapy="tmp_Calibration_points", flags="ge"
                )
                g.run_command(
                    "r.gwr",
                    mapx=crctd_lst,
                    mapy="tmp_Calibration_points",
                    estimates="tmp_bathymetry",
                    bandwidth=int(bw["estimate"]),
                )
    tmp_rslt_ext = g.parse_command("r.univar", map="tmp_Calibration_points", flags="g")
    g.mapcalc(
        exp="{bathymetry}=if({tmp_SDB}>{max_}, null(),"
        "if({tmp_SDB}<{min_}, null(), {tmp_SDB}))".format(
            tmp_SDB="tmp_bathymetry",
            bathymetry=bathymetry,
            max_=float(tmp_rslt_ext["max"]),
            min_=float(tmp_rslt_ext["min"]),
        )
    )


def cleanup():
    g.run_command("g.remove", type="raster", name="MASK", flags="f")
    g.run_command("g.remove", type="all", pattern="*tmp*", flags="f")
    try:
        g.try_remove(predict)
        g.try_remove(r)
    except:
        pass


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
