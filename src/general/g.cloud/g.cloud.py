#!/usr/bin/env python


############################################################################
#
# MODULE:       g.cloud
# AUTHOR(S):    Luca Delucchi, Markus Neteler
# PURPOSE:      g.cloud give the possibility to connect a local GRASS session with
#               another one in a cluster system (it use qsub)
#
# COPYRIGHT:    (C) 2011 by Luca Delucchi
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#%module
#% description: Connects a local GRASS GIS session to another one in a cluster system.
#% keyword: general
#% keyword: cloud computing
#%end
#%flag
#% key: c
#% description: Cycle through all variables
#%end
#%flag
#% key: k
#% description: Keep temporal files and mapsets
#%end
#%flag
#% key: a
#% description: Use ssh-add for faster access (requires to launch ssh-agent beforehand)
#%end
#%option
#% key: config
#% type: string
#% gisprompt: old,file,input
#% label: Path to ASCII file containing authentication parameters
#% description: "-" to pass the parameters interactively
#% required: yes
#% guisection: Define
#%end
#%option
#% key: server
#% type: string
#% key_desc: name
#% description: Name or IP of server to be connected
#% required: yes
#%end
#%option
#% key: grass_script
#% type: string
#% key_desc: name
#% description: Path to the input GRASS script
#% required: no
#% gisprompt: old,file,input
#%end
#%option
#% key: qsub_script
#% type: string
#% key_desc: name
#% description: Path to the input qsub script
#% required: no
#% gisprompt: old,file,input
#%end
#%option
#% key: variables
#% type: string
#% key_desc: name
#% label: Python dictionary with the variables to pass to the GRASS script via qsub
#% description: Example: "{'year':[2010,2011]}" will call 'qsub -v year=2010 ...' and 'qsub -v year=2011 ...'
#% required: no
#%end
#%option G_OPT_R_INPUTS
#% key: raster
#% description: Name of input raster map(s) used by GRASS script
#% required: no
#%end
#%option G_OPT_V_INPUTS
#% key: vector
#% label: {NULL}
#% description: Name of input vector map(s) used by GRASS script
#% required: no
#%end
#%option
#% key: mail
#% type: string
#% required: no
#% key_desc: name
#% description: Mail address to send emails at the end of jobs
#%end
#%option
#% key: reconnect
#% type: string
#% required: no
#% key_desc: name
#% description: Reconnect with old job to see if it is finished
#%end
#%option
#% key: path
#% type: string
#% key_desc: name
#% label: Path for temporal for g.cloud operations
#% description: The directory must be visible on the network to the blades
#% required: no
#% answer: $HOME
#%end

# import library
import os
import sys
import tarfile
import ast
import tempfile
import getpass
import itertools
import collections
import stat
from types import *
import grass.script as grass

# add the folder containing libraries to python path
cloudpath = None
if os.path.isdir(os.path.join(os.getenv("GISBASE"), "etc", "g.cloud", os.sep)):
    cloudpath = os.path.join(os.getenv("GISBASE"), "etc", "g.cloud")
elif os.path.isdir(
    os.path.join(os.getenv("GRASS_ADDON_BASE"), "etc", "g.cloud", os.sep)
):
    cloudpath = os.path.join(os.getenv("GRASS_ADDON_BASE"), "etc", "g.cloud")
elif os.path.isdir(
    os.path.join(os.getenv("GRASS_ADDON_PATH"), "etc", "g.cloud", os.sep)
):
    cloudpath = os.path.join(os.getenv("GRASS_ADDON_PATH"), "etc", "g.cloud")

# search python environment
python = os.getenv("GRASS_PYTHON", "python")
if cloudpath:
    sys.path.append(cloudpath)


# lazy imports cloud_ssh


def transposed(lists):
    """Function to transpose list of variables"""
    if not lists:
        return []
    return map(lambda *row: list(row), *lists)


def _iteration(lis):
    """Interation inside the lists of values"""
    if len(lis) == 1:
        return lis[0]
    else:
        out = [i for i in itertools.product(lis[0], _iteration(lis[1:]))]
    return out


def _flatten(lis):
    """Used after iteration to create a good list"""
    for el in lis:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in _flatten(el):
                # return but keep the state of the function
                yield sub
        else:
            yield el


def serverCheck(conn, grassV):
    """Function to check if the server has GRASS installed and return the home
    of user used to connect to the server
    """
    test_grass = conn.ssh("which %s" % grassV)
    test_qsub = conn.ssh("which %s" % "qsub")
    if test_qsub == "" or test_qsub.find("no %s in" % "qsub") != -1:
        grass.fatal(
            _("On the server '%s' is not installed. Please install it first." % "qsub")
        )
    if test_grass == "" or test_grass.find("no %s in" % grassV) != -1:
        grass.warning(
            _("On the server '%s' is not installed. Please install it first" % grassV)
        )
    # return the home path of the user on the cluster
    loc = conn.ssh("pwd")
    return loc.strip()


def copyMaps(conn, infiles, typ, home):
    """Function to copy maps to the cluster server using r.pack or v.pack"""
    if typ == "raster":
        ele = "cell"
        com = "r.pack"
    elif typ == "vector":
        ele = "vector"
        com = "v.pack"
    tar = tarfile.TarFile.open(name=typ + "tarpack", mode="w")
    for i in infiles:
        gfile = grass.find_file(name=i, element=ele)
        if not gfile["name"]:
            grass.fatal(_("%s map <%s> not found") % (typ, i))
        else:
            outputpack = "%s.%spack" % (i, typ)
            grass.run_command(com, input=i, output=outputpack, overwrite=True)
            tar.add(outputpack)
    tar.close()
    conn.scp(typ + "tarpack", home)
    for i in infiles:
        os.remove("%s.%spack" % (i, typ))
    os.remove(typ + "tarpack")


def variablesCheck(listValue):
    """Function to check if all variables as the same length and
    return the values in a useful list"""
    if isinstance(listValue[0], ListType):
        oldlen = len(listValue[0])
    else:
        grass.fatal(_("Values must be a Python list"))
    # check if all variables have the same lenght
    for i in listValue:
        if oldlen != len(i):
            grass.fatal(
                _(
                    "Attention: the lists of values have different length\n"
                    "All the variables have to have the same number of values"
                )
            )
    return transposed(listValue)


def variablesCheckCicle(listValue):
    """Return the values in a useful list"""
    vals = _iteration(listValue)
    out = []
    for v in vals:
        v = list(_flatten(v))
        out.append(v)
    return out


def reconnect(conn, pid, path, vari, home):
    collect_file_name = "cloud_finish_%s" % pid
    gcloud_home = os.path.join(home, "gcloud%s" % pid)
    collect_file = conn.ssh('"cd %s; ls %s"' % (gcloud_home, collect_file_name))
    output_file = os.path.join(home, "gcloud_result_%s.tar.gz" % pid)
    if collect_file.strip() == collect_file_name:
        location_name = conn.ssh(
            '"cd %s; ls"' % os.path.join(home, "grassdata%s" % pid)
        )
        location_name = location_name.strip()
        mapset_name = os.path.join(
            home, "grassdata%s" % pid, location_name, "PERMANENT"
        )
        grass.message(_("Job %s terminated, now coping the result data..." % pid))
        conn.ssh(
            '"cd %s; tar --exclude=DEFAULT_WIND --exclude=PROJ_INFO --exclude=PROJ_UNITS --exclude=PROJ_EPSG -czf %s *;"'
            % (mapset_name, output_file)
        )
        conn.pcs(output_file, path)
        new_mapset = os.path.join(
            vari["GISDBASE"], vari["LOCATION_NAME"], "gcloud%s" % pid
        )
        # os.mkdir(new_mapset)
        outtar = tarfile.open(
            os.path.join(path, "gcloud_result_%s.tar.gz" % pid), "r:gz"
        )
        outtar.extractall(path=new_mapset)
        grass.message(
            _(
                "To see the new data launch\n g.mapsets mapset=gcloud operation=add%s"
                % pid
            )
        )
    else:
        grass.message(_("Job %s not yet completed..." % pid))
    return


# main function
def main():
    # set the home path
    home = os.path.expanduser("~")
    # check if user is in GRASS
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        grass.fatal(_("$GISBASE not defined"))
        return 0
    # check ssh
    if not grass.find_program("ssh", "-V"):
        grass.fatal(_("%s required. Please install '%s' first.") % ("ssh", "ssh"))
        return 0
    # parse the grassdata, location e mapset
    variables = grass.core.gisenv()
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version["version"].find("7.") != -1:
        grassVersion = "grass%s%s" % (version["version"][0], version["version"][2])
        session_path = ".grass%s" % version["version"][0]
    else:
        grass.fatal(_("You are not in a GRASS GIS version 7 session"))
        return 0
    # set the path of grassdata/location/mapset
    # set to .grass8 folder
    path = os.path.join(home, session_path, "g.cloud")
    if not os.path.exists(path):
        os.makedirs(path)
    # set username, password and folder if settings are inserted by stdin
    if options["config"] == "-":
        user = raw_input(_("Insert username: "))
        passwd = getpass.getpass()
    # set username, password and folder by file
    else:
        # open the file and read the the user and password:
        # first line is username
        # second line is password
        if not os.path.exists(options["config"]):
            grass.fatal(_("The file %s doesn't exist" % options["config"]))
        if stat.S_IMODE(os.stat(options["config"]).st_mode) == int("0600", 8):
            filesett = open(options["config"], "r")
            fileread = filesett.readlines()
            user = fileread[0].strip()
            passwd = fileread[1].strip()
            filesett.close()
        else:
            err = (
                "The file permissions of %s are considered insecure.\n"
                % options["config"]
            )
            err = "Please correct permissions to read/write only for user (mode 600)"
            grass.fatal(_(err))
            return 0
    # server option
    server = options["server"]
    # lazy import
    import cloud_ssh as sshs

    # create the sshs session
    ssh_conn = sshs.ssh_session(user, server, session_path, passwd)
    if flags["a"]:
        ssh_conn.add()
    # check if the server has grass and qsub installed, and return the home
    if options["path"] == "$HOME":
        serverHome = serverCheck(ssh_conn, grassVersion)
    else:
        serverHome = options["path"]
    if options["reconnect"]:
        reconnect(ssh_conn, options["reconnect"], path, variables, serverHome)
    else:
        if options["grass_script"]:
            if not os.path.exists(options["grass_script"]):
                grass.fatal(_("File %s does not exists" % options["grass_script"]))
            else:
                grassScript = options["grass_script"]
                nameGrassScript = os.path.split(grassScript)[-1]
        else:
            grass.fatal(_("You have to set %s option") % "grass_script")
        if options["qsub_script"]:
            if not os.path.exists(options["qsub_script"]):
                grass.fatal(_("File %s does not exists" % options["qsub_script"]))
            else:
                qsubScript = options["qsub_script"]
                nameQsubScript = os.path.split(qsubScript)[-1]
        else:
            grass.fatal(_("You have to set %s option") % "qsub_script")
        # the pid of process to have unique value
        pid = os.path.split(tempfile.mkstemp()[1])[-1]
        # name for the unique folder
        serverFolder = os.path.join(serverHome, "gcloud%s" % pid)
        ssh_conn.ssh("mkdir %s" % serverFolder)
        serverGISDBASE = os.path.split(variables["GISDBASE"])[-1] + str(pid)
        permanent = os.path.join(
            variables["GISDBASE"], variables["LOCATION_NAME"], "PERMANENT"
        )
        # create the new path for $home/GRASSDATA/LOCATION/PERMANENT on the server
        new_perm = os.path.join(
            serverHome, serverGISDBASE, variables["LOCATION_NAME"], "PERMANENT"
        )
        ssh_conn.ssh("mkdir -p %s" % new_perm)
        tar = tarfile.open("PERMANENT.tar.gz", "w:gz")
        tar.add(os.path.join(permanent, "PROJ_INFO"), "PROJ_INFO")
        tar.add(os.path.join(permanent, "PROJ_UNITS"), "PROJ_UNITS")
        tar.add(os.path.join(permanent, "PROJ_EPSG"), "PROJ_EPSG")
        tar.add(os.path.join(permanent, "DEFAULT_WIND"), "DEFAULT_WIND")
        tar.add(os.path.join(permanent, "WIND"), "WIND")
        if os.path.isfile(os.path.join(permanent, "VAR")):
            tar.add(os.path.join(permanent, "VAR"), "VAR")
        tar.close()
        ssh_conn.scp("PERMANENT.tar.gz", serverHome)
        ssh_conn.ssh("tar -C %s -xzf PERMANENT.tar.gz" % new_perm)
        ssh_conn.ssh("rm -f PERMANENT.tar.gz")
        os.remove("PERMANENT.tar.gz")

        if options["raster"] != "":
            rasters = options["raster"].split(",")
            copyMaps(ssh_conn, rasters, "raster", serverFolder)
        if options["vector"] != "":
            rasters = options["vector"].split(",")
            copyMaps(ssh_conn, rasters, "vector", serverFolder)
        # copy the scripts to the server
        tar = tarfile.open("script_gcloud.tar.gz", "w:gz")
        if options["raster"] != "" or options["vector"] != "":
            tar.add(os.path.join(cloudpath, "cloud_unpack.py"), "cloud_unpack.py")
            tar.add(os.path.join(cloudpath, "cloud_which.py"), "cloud_which.py")
        tar.add(os.path.join(cloudpath, "cloud_collect.sh"), "cloud_collect.sh")
        tar.add(os.path.join(cloudpath, "cloud_mail.sh"), "cloud_mail.sh")
        tar.add(grassScript, nameGrassScript)
        tar.add(qsubScript, nameQsubScript)
        tar.close()
        ssh_conn.scp("script_gcloud.tar.gz", serverHome)
        ssh_conn.ssh("tar -C %s -xzf script_gcloud.tar.gz" % serverFolder)
        ssh_conn.ssh("rm -f script_gcloud.tar.gz")
        os.remove("script_gcloud.tar.gz")
        if options["raster"] != "" or options["vector"] != "":
            grass.debug(
                "Launching cloud_unpack.py with this parameters: %s, %s, %s"
                % (serverFolder, python, new_perm),
                debug=2,
            )
            ssh_conn.ssh(
                '"cd %s ; %s cloud_unpack.py %s"' % (serverFolder, python, new_perm)
            )
        qsubid = os.path.join(serverFolder, "tmpqsub")
        grass.debug("The pid of job is %s" % (str(pid)), debug=2)
        if options["variables"] != "":
            vari = ast.literal_eval(options["variables"])
            values = vari.values()
            keys = vari.keys()
            if flags["c"]:
                values = variablesCheckCicle(values)
            else:
                values = variablesCheck(values)
            njobs = 0
            for val in range(len(values)):
                launchstr = (
                    '"cd %s ; qsub -v MYPID=%s -v MYLD_LIBRARY_PATH=$LD_LIBRARY_PATH '
                    "-v GRASSDBASE=%s -v MYLOC=%s -v GRASSCRIPT=%s"
                    % (
                        serverFolder,
                        pid,
                        os.path.join(serverHome, serverGISDBASE),
                        variables["LOCATION_NAME"],
                        os.path.join(serverFolder, nameGrassScript),
                    )
                )
                for k in range(len(keys)):
                    launchstr += " -v %s=%s" % (str(keys[k]), str(values[val][k]))
                launchstr += " %s >> %s" % (
                    os.path.join(serverFolder, nameQsubScript),
                    qsubid,
                )
                ssh_conn.ssh(launchstr)
                njobs += 1
            grass.message(_("Launching %i jobs..." % njobs))
        else:
            launchstr = (
                "cd %s ; qsub -v MYPID=%s -v MYLD_LIBRARY_PATH=$LD_LIBRARY_PATH "
                "-v GRASSDBASE=%s -v MYLOC=%s -v GRASSCRIPT=%s %s > %s"
                % (
                    serverFolder,
                    pid,
                    os.path.join(serverHome, serverGISDBASE),
                    variables["LOCATION_NAME"],
                    os.path.join(serverFolder, nameGrassScript),
                    os.path.join(serverFolder, nameQsubScript),
                    qsubid,
                )
            )
            ssh_conn.ssh(launchstr)
            grass.message(_("Launching a single job..."))

        # if options['mail']:
        # strin = "\"cd %s ; qsub -v MYPID=%s -v MYLD_LIBRARY_PATH=$LD_LIBRARY_PATH -hold_jid "
        # strin += "-hold_jid `cat %s | tr '\n' ',' | sed 's+,$++g'` %s %s %s %s\""
        # ssh_conn.ssh(strin % ( serverFolder, pid, qsubid,
        # os.path.join(serverFolder, 'cloud_collect.sh'),
        # os.path.join(serverHome, serverGISDBASE),
        # variables['LOCATION_NAME'], options['mail'])
        # )
        # else:
        # strin = "\"cd %s ; qsub -v MYPID=%s -v MYLD_LIBRARY_PATH=$LD_LIBRARY_PATH -hold_jid "
        # strin += "-hold_jid `cat %s | tr '\n' ',' | sed 's+,$++g'` %s %s %s\""
        # ssh_conn.ssh(strin % ( serverFolder, pid, qsubid,
        # os.path.join(serverFolder, 'cloud_collect.sh'),
        # os.path.join(serverHome, serverGISDBASE),
        # variables['LOCATION_NAME'])
        # )
        if options["mail"]:
            mail = options["mail"]
        else:
            mail = "NOOO"
        if flags["k"]:
            remove = "NOOO"
        else:
            remove = "yes"
        ids = ssh_conn.ssh(
            "cat %s | cut -d' ' -f3 | tr '\n' ',' | sed 's+,$++g'" % qsubid
        )
        # 'string %(s)s' % {'s':1}
        collectstr = (
            '"cd %s ; qsub -v MYPID=%s -v MYLD_LIBRARY_PATH=$LD_LIBRARY_PATH '
            % (serverFolder, pid)
        )
        collectstr += '-hold_jid %s %s %s %s %s %s %s"' % (
            ids,
            os.path.join(serverFolder, "cloud_collect.sh"),
            os.path.join(serverHome, serverGISDBASE),
            variables["LOCATION_NAME"],
            mail,
            remove,
            pid,
        )
        ssh_conn.ssh(collectstr)
        grass.message(
            _(
                "If you want to reconnect to this job to see its status please use the reconnect options with this value: %s"
                % pid
            )
        )
        grass.message(_("   g.cloud config=path|- server=host reconnect=%s" % pid))
    ssh_conn.close()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
