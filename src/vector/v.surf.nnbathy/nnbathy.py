import grass.script as grass
import os


class Nnbathy:
    # base class
    def __init__(self, options):
        self._tmpxyz = grass.tempfile()
        self._xyzout = grass.tempfile()
        self._tmp = grass.tempfile()
        self._tmpcat = grass.tempfile()
        self.options = options
        self.region()
        pass

    def region(self):
        # set the computive region
        # reg = grass.read_command("g.region", flags='p')
        # kv = grass.parse_key_val(reg, sep=':')
        kv = grass.region()
        # reg_N = float(kv['north'])
        # reg_W = float(kv['west'])
        # reg_S = float(kv['south'])
        # reg_E = float(kv['east'])
        # nsres = float(kv['nsres'])
        # ewres = float(kv['ewres'])
        reg_N = float(kv["n"])
        reg_W = float(kv["w"])
        reg_S = float(kv["s"])
        reg_E = float(kv["e"])
        nsres = float(kv["nsres"])
        ewres = float(kv["ewres"])

        # set variables
        self.cols = int(kv["cols"])
        self.rows = int(kv["rows"])
        self.area = (reg_N - reg_S) * (reg_E - reg_W)
        self.ALG = "nn"

        # set the working region for nnbathy (it's cell-center oriented)
        self.nn_n = reg_N - nsres / 2
        self.nn_s = reg_S + nsres / 2
        self.nn_w = reg_W + ewres / 2
        self.nn_e = reg_E - ewres / 2
        self.null = "NaN"
        self.ctype = "double"

    def compute(self):
        # computing
        grass.message(
            '"nnbathy" is performing the interpolation now. \
                      This may take some time...'
        )
        grass.verbose(
            "Once it completes an 'All done.' \
                      message will be printed."
        )

        # nnbathy calling
        fsock = open(self._xyzout, "w")
        grass.call(
            [
                "nnbathy",
                "-W",
                "%d" % 0,
                "-i",
                "%s" % self._tmpxyz,
                "-x",
                "%f" % self.nn_w,
                "%f" % self.nn_e,
                "-y",
                "%f" % self.nn_n,
                "%f" % self.nn_s,
                "-P",
                "%s" % self.ALG,
                "-n",
                "%dx%d" % (self.cols, self.rows),
            ],
            stdout=fsock,
        )
        fsock.close()

    def create_output(self):
        # create the output raster map
        # convert the X,Y,Z nnbathy output into a GRASS ASCII grid
        # then import with r.in.ascii
        # 1 create header
        header = open(self._tmp, "w")
        header.write(
            "north: %s\nsouth: %s\neast: %s\nwest: %s\nrows: %s\ncols: %s\ntype: %s\nnull: %s\n\n"
            % (
                self.nn_n,
                self.nn_s,
                self.nn_e,
                self.nn_w,
                self.rows,
                self.cols,
                self.ctype,
                self.null,
            )
        )
        header.close()

        # 2 do the conversion
        grass.message("Converting nnbathy output to GRASS raster ...")
        fin = open(self._xyzout, "r")
        fout = open(self._tmp, "a")
        cur_col = 1
        for line in fin:
            parts = line.split(" ")
            if cur_col == self.cols:
                cur_col = 0
                fout.write(str(parts[2]))
            else:
                fout.write(str(parts[2]).rstrip("\n") + " ")
            cur_col += 1
        fin.close()
        fout.close()

        # 3 import to raster
        grass.run_command(
            "r.in.ascii", input=self._tmp, output=self.options["output"], quiet=True
        )
        grass.message("All done. Raster map <%s> created." % self.options["output"])

    def __del__(self):
        # cleanup
        if self._tmp:
            os.remove(self._tmp)
        if self._tmpxyz:
            os.remove(self._tmpxyz)
        if self._xyzout:
            os.remove(self._xyzout)
        if self._tmpcat:
            os.remove(self._tmpcat)


class Nnbathy_raster(Nnbathy):
    # class for raster input
    def __init__(self, options):
        Nnbathy.__init__(self, options)
        self._load(options)

    def _load(self, options):
        # load input raster
        grass.run_command(
            "r.stats",
            flags="1gn",
            input=options["input"],
            output=self._tmpxyz,
            quiet=True,
            overwrite=True,
        )


class Nnbathy_vector(Nnbathy):
    # class for vector input
    def __init__(self, options):
        Nnbathy.__init__(self, options)
        self._load(options)

    def _load(self, options):
        # load input vector, initial controls
        if int(options["layer"]) == 0:
            _layer = ""
            _column = ""
        else:
            _layer = int(options["layer"])
            if options["column"]:
                _column = options["column"]
            else:
                grass.message("Name of z column required for 2D vector maps.")
        # convert vector to ASCII
        grass.run_command(
            "v.out.ascii",
            overwrite=1,
            input=options["input"].split("@")[0],
            output=self._tmpcat,
            format="point",
            separator="space",
            precision=15,
            where=options["where"],
            layer=_layer,
            columns=_column,
        )
        #        grass.run_command("v.out.ascii", flags='r', overwrite=1,
        #                          input=options['input'], output=self._tmpcat,
        #                          format="point", separator="space", precision=15,
        #                          where=options['where'], layer=_layer,
        #                          columns=_column
        # edit ASCII file, crop out one column
        if int(options["layer"]) > 0:
            fin = open(self._tmpcat, "r")
            fout = open(self._tmpxyz, "w")
            try:
                for line in fin:
                    parts = line.split(" ")
                    from grass.pygrass.vector import VectorTopo

                    pnt = VectorTopo(options["input"].split("@")[0])
                    pnt.open(mode="r")
                    check = pnt.read(1)
                    if check.is2D:
                        # fout.write(parts[0]+' '+parts[1]+' '+parts[3])
                        fout.write("{} {} {}".format(parts[0], parts[1], parts[3]))
                    else:
                        # fout.write(parts[0]+' '+parts[1]+' '+parts[4])
                        fout.write("{} {} {}".format(parts[0], parts[1], parts[4]))
                    pnt.close()
            except (Exception, OSError) as e:
                grass.fatal_error("Invalid input: %s" % e)
            fin.close()
            fout.close()
        else:
            grass.message("Z coordinates are used.")


class Nnbathy_file:
    # class for file input
    def __init__(self, options):
        self.options = options
        self._load(options)

    def _load(self, options):
        # load input file
        self._tmpxyz = options["file"]
