#!/usr/bin/env python

"""
@module  db.csw.admin
@brief   Module for creating metadata based on ISO for vector maps

(C) 2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
used and modified original pycsw-admin.py from pycsw lib(
https://github.com/geopython/pycsw/blob/master/bin/pycsw-admin.py)
"""


# %module
# % description: CSW database manager
# % keyword: csw
# % keyword: metadata
# %end

# %option G_OPT_F_INPUT
# % key: configure
# % description: path to configure file (default.cfg)
# % required : yes
# % answer : /var/www/html/pycsw/default.cfg
# %end

# %option
# % key: load_records
# % label: Load metadata(folder)
# % description: Loads metadata records from directory into repository
# % guisection: Records
# %end

# %flag
# % key: r
# % label: Load records recursively
# % description: Load records from directory recursively
# % guisection: Records
# %end

# %flag
# % key: s
# % label: Setup database
# % description: Creates repository tables and indexes
# % guisection: Commands
# %end

# %option
# % key: export_records
# % label: Create db dump(folder)
# % description: Dump metadata records from repository into directory
# % guisection: Commands
# %end

# %flag
# % key: i
# % label: Database indexes
# % description: Rebuild repository database indexes
# % guisection: Commands
# %end

# %flag
# % key: o
# % label: Optimize db
# % description: Optimize repository database
# % guisection: Commands
# %end

# %flag
# % key: h
# % label: Refresh harvested records
# % description: Optimize repository database
# % guisection: Commands
# %end

# %option G_OPT_F_OUTPUT
# % key: gen_sitemap
# % label: Sitemap
# % description: Generate XML Sitemap
# % guisection: Commands
# % required: NO
# %end

# %flag
# % key: d
# % label: Delete all records(!!)
# % description: Delete all records without prompting
# % guisection: Commands
# %end

# %flag
# % key: f
# % label: Force confirmation
# % description: Force confirmation of task
# % guisection: Commands
# %end

# %option
# % key: url_csw
# % label: Url of CSW
# % description: Execute a CSW request via HTTP POST: URL of CSW
# % guisection: Execute request
# %end

# %option G_OPT_F_INPUT
# % key: file_xml
# % label: XML file
# % description: Execute a CSW request via HTTP POST: XML FILE
# % guisection: Execute request
# % required: NO
# %end

import configparser
import getopt
import importlib
import sys

from grass.script import core as grass
from grass.script.utils import set_path

set_path(modulename="wx.metadata", dirname="mdlib", path="..")

from mdlib import globalvar


class CswAdmin:
    def __init__(self):
        try:
            pycsw = "pycsw"
            self.pycsw_config = importlib.import_module(".core.config", pycsw)
            self.pycsw_admin = importlib.import_module(".core.admin", pycsw)
        except ModuleNotFoundError as e:
            msg = e.msg
            grass.fatal(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.COMMAND = None
        self.XML_DIRPATH = None
        self.CFG = None
        self.RECURSIVE = False
        self.OUTPUT_FILE = None
        self.CSW_URL = None
        self.XML = None
        self.XSD = None
        self.TIMEOUT = 30
        self.FORCE_CONFIRM = False
        self.METADATA = None
        self.DATABASE = None
        self.URL = None
        self.HOME = None
        self.TABLE = None
        self.CONTEXT = self.pycsw_config.StaticContext()

    def argParser(
        self,
        defaultConf,
        load_records,
        loadRecurs,
        setupDB,
        exportRecord,
        indexes,
        optimize,
        harvest,
        siteOut,
        deleteAll,
        cswURL,
        cswXML,
        force,
    ):
        if defaultConf is None:
            grass.error("Configure file is not exist")
        args = []
        args.append("-c")

        if load_records:
            args.append("load_records")
            args.append("-p")
            args.append(load_records)
            if loadRecurs:
                args.append("-r")
            if force:
                args.append("y")
            return args

        if setupDB:
            args.append("setup_db")
            args.append("-f")
            args.append(defaultConf)
            return args

        if exportRecord:
            args.append("export_records")
            args.append("-p")
            args.append(exportRecord)
            args.append("-f")
            args.append(defaultConf)
            return args

        if indexes:
            args.append("rebuild_db_indexes")
            args.append("-f")
            args.append(defaultConf)
            return args

        if optimize:
            args.append("optimize_db")
            args.append("-f")
            args.append(defaultConf)
            return args

        if harvest:
            args.append("refresh_harvested_records")
            args.append("-f")
            args.append(defaultConf)
            return args

        if siteOut:
            args.append("gen_sitemaps")
            args.append("-o")
            args.append(siteOut)
            args.append("-f")
            args.append(defaultConf)
            return args

        if deleteAll:
            args.append("delete_records")
            args.append("-f")
            args.append(defaultConf)
            if force:
                args.append("y")
            return args

        if cswURL and cswXML:
            args.append("post_xml")
            args.append("-u")
            args.append(cswURL)
            args.append("-x")
            args.append(cswXML)
            args.append("-f")
            args.append(defaultConf)
            return args

        return False

    def run(self, argv):

        if len(argv) == 0:
            grass.error("Nothing to do. Set args")
            return
        try:
            OPTS, ARGS = getopt.getopt(argv, "c:f:ho:p:ru:x:s:t:y")
        except getopt.GetoptError as err:
            grass.error("\nERROR: %s" % err)

        for o, a in OPTS:
            if o == "-c":
                self.COMMAND = a
            if o == "-f":
                self.CFG = a
            if o == "-o":
                self.OUTPUT_FILE = a
            if o == "-p":
                self.XML_DIRPATH = a
            if o == "-r":
                self.RECURSIVE = True
            if o == "-u":
                self.CSW_URL = a
            if o == "-x":
                self.XML = a
            if o == "-t":
                self.TIMEOUT = int(a)
            if o == "-y":
                self.FORCE_CONFIRM = True

        if self.CFG is None and self.COMMAND not in ["post_xml"]:
            print("ERROR: -f <cfg> is a required argument")

        if self.COMMAND not in ["post_xml"]:
            SCP = configparser.ConfigParser()
            SCP.readfp(open(self.CFG))

            self.DATABASE = SCP.get("repository", "database")
            self.URL = SCP.get("server", "url")
            self.HOME = SCP.get("server", "home")
            self.METADATA = dict(SCP.items("metadata:main"))
            try:
                self.TABLE = SCP.get("repository", "table")
            except configparser.NoOptionError:
                self.TABLE = "records"

        if self.COMMAND == "setup_db":
            try:
                self.pycsw_admin.setup_db(self.DATABASE, self.TABLE, self.HOME)
            except Exception as err:
                print(err)
                print("ERROR: DB creation error.  Database tables already exist")
                print("Delete tables or database to reinitialize")

        elif self.COMMAND == "load_records":
            self.pycsw_admin.load_records(
                self.CONTEXT,
                self.DATABASE,
                self.TABLE,
                self.XML_DIRPATH,
                self.RECURSIVE,
                self.FORCE_CONFIRM,
            )
        elif self.COMMAND == "export_records":
            self.pycsw_admin.export_records(
                self.CONTEXT, self.DATABASE, self.TABLE, self.XML_DIRPATH
            )
        elif self.COMMAND == "rebuild_db_indexes":
            self.pycsw_admin.rebuild_db_indexes(self.DATABASE, self.TABLE)
        elif self.COMMAND == "optimize_db":
            self.pycsw_admin.optimize_db(self.CONTEXT, self.DATABASE, self.TABLE)
        elif self.COMMAND == "refresh_harvested_records":
            self.pycsw_admin.refresh_harvested_records(
                self.CONTEXT, self.DATABASE, self.TABLE, self.URL
            )
        elif self.COMMAND == "gen_sitemap":
            self.pycsw_admin.gen_sitemap(
                self.CONTEXT, self.DATABASE, self.TABLE, self.URL, self.OUTPUT_FILE
            )
        elif self.COMMAND == "post_xml":
            grass.message(
                self.pycsw.core.admin.post_xml(self.CSW_URL, self.XML, self.TIMEOUT)
            )

        elif self.COMMAND == "delete_records":
            self.pycsw_admin.delete_records(self.CONTEXT, self.DATABASE, self.TABLE)


"""#TODO
    def initDatabase(self):
        driverDB = Module('db.connect',
                          flags='pg',
                          quiet=True,
                          stdout_=PIPE)
        self.database = parse_key_val(driverDB.outputs.stdout, sep=': ')
        conf = 'default.cfg'
        modif = os.path.join(os.getenv('GRASS_ADDON_BASE') ,'wx.metadata','etc','config','default.cfg')
        defaultConf = os.path.join(os.getenv('GRASS_ADDON_BASE'),'wx.metadata' ,'etc','config','default-sample.cfg')
        print self.database

        SCP = configparser.ConfigParser()
        try:
            SCP.readfp(open(conf))
        except:
            shutil.copy2(defaultConf, conf)
            SCP.readfp(open(conf))

        DATABASE = SCP.get('repository', 'database')
        #URL = SCP.get('server', 'url')
        HOME = SCP.get('server', 'home')


        #currPython=os.path.dirname(os.path.realpath(__file__))
        if not os.path.isdir(HOME):
            grass.message('Cannot find server home folder < %s >' % HOME)
            grass.error('Move pycsw(install foder) to <%s> or set server.home in <default.cfg >'%HOME)

        if not os.access(defaultConf, os.W_OK):
            try:
                shutil.copy2(defaultConf, HOME)
                grass.message('Configure file created in < %s/default.cfg >' % HOME)
            except:
                grass.error('Cannot duplicate <default-sample.cfg> to <default.cfg> ' )
                return

        if not os.access(defaultConf, os.W_OK):
            grass.error('Cannot acces configure file < %s >' % defaultConf)
            return

        if self.database['driver'] == 'sqlite':
            if not os.access(DATABASE, os.W_OK):
                grass.error('Cannot acces databaase < %s >'%DATABASE)
"""
"""
# %flag
# % key: a
# % label: Automatic configuration
# % description: Set database according GRASS default and confugure server
# % guisection: Auto Config
# %end
"""


def main():
    defaultConf = options["configure"]
    load_records = options["load_records"]
    loadRecurs = flags["r"]
    setupDB = flags["s"]
    exportRecord = options["export_records"]
    indexes = flags["i"]
    optimize = flags["o"]
    harvest = flags["h"]
    siteOut = options["gen_sitemap"]
    deleteAll = flags["d"]
    cswURL = options["url_csw"]
    cswXML = options["file_xml"]
    force = flags["f"]

    csw = CswAdmin()
    # if flags['a']:
    # csw.initDatabase()
    args = csw.argParser(
        defaultConf,
        load_records,
        loadRecurs,
        setupDB,
        exportRecord,
        indexes,
        optimize,
        harvest,
        siteOut,
        deleteAll,
        cswURL,
        cswXML,
        force,
    )
    if args:
        csw.run(args)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
