#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.install
# AUTHOR(S):   Pietro Zambelli
# PURPOSE:     Check missing python libraries and wrong paths and fix them
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

# %module
# % description: Check if everything of r.green is correctly installed and configured
# % keyword: raster
# % keyword: renewable energy
# %end
# %flag
# % key: i
# % description: Install missing libraries
# %end
# %flag
# % key: x
# % description: Add r.green menu to the GRASS GUI
# %end

# import system libraries
from __future__ import print_function

import imp
import os
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import namedtuple
from os.path import join
from tempfile import gettempdir

try:
    # Python2 imports
    import urllib2
    from htmlentitydefs import name2codepoint
    from HTMLParser import HTMLParser
    from urllib2 import build_opener
except ImportError:
    # Python3 imports
    import urllib.request
    import urllib.error
    import urllib.parse
    from html.entities import name2codepoint
    from html.parser import HTMLParser
    from urllib.request import build_opener

    unichr = chr


from grass.script import core as gcore

Pkg = namedtuple("Pkg", ["name", "version", "py", "un", "platform"])


# list packages required by the module
CHECK_LIBRARIES = ["scipy", "numexpr"]
CHECK_RGREENLIB = [
    ("libgreen", ".."),
    ("libhydro", os.path.join("..", "r.green.hydro")),
]

UAGENT = "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:44.0) " "Gecko/20100101 Firefox/44.0"

PATHSYSXML = []
PATHLOCXML = []

XMLMAINMENU = "Energy"

XMLENERGYTOOLBOX = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE toolboxes SYSTEM "toolboxes.dtd">
<toolboxes>
  <toolbox name="{XMLMAINMENU}">
    <label>&amp;Energy</label>
    <items>
      <subtoolbox name="Biomass"/>
      <subtoolbox name="Hydro"/>
    </items>
  </toolbox>
  <toolbox name="Biomass">
    <label>Biomass</label>
    <items>
      <subtoolbox name="Forestry"/>
    </items>
  </toolbox>
  <toolbox name="Forestry">
    <label>Forestry biomass potential</label>
    <items>
      <module-item name="r.green.biomassfor.theoretical">
        <label>Theoretical potential</label>
      </module-item>
      <module-item name="r.green.biomassfor.legal">
        <label>Legal constraints</label>
      </module-item>
      <module-item name="r.green.biomassfor.technical">
        <label>Technical constraints</label>
      </module-item>
      <module-item name="r.green.biomassfor.recommended">
        <label>Extra constraints</label>
      </module-item>
      <module-item name="r.green.biomassfor.economic">
        <label>Financial constraints</label>
      </module-item>
      <separator/>
      <module-item name="r.green.biomassfor.impact">
        <label>Impact on Ecosystem Services</label>
      </module-item>
      <module-item name="r.green.biomassfor.co2">
        <label>CO2 balance</label>
      </module-item>
    </items>
  </toolbox>
  <toolbox name="Hydro">
    <label>Hydro-power potential</label>
    <items>
      <module-item name="r.green.hydro.theoretical">
        <label>Theoretical potential</label>
      </module-item>
      <module-item name="r.green.hydro.recommended">
        <label>Legal and extra constraints</label>
      </module-item>
      <module-item name="r.green.hydro.technical">
        <label>Technical constraints</label>
      </module-item>
      <module-item name="r.green.hydro.financial">
        <label>Financial constraints</label>
      </module-item>
      <separator/>
      <module-item name="r.green.hydro.closest">
        <label>Move power plants to the closest river's point</label>
      </module-item>
      <module-item name="r.green.hydro.discharge">
        <label>Compute natural discharge and minimal flow</label>
      </module-item>
      <module-item name="r.green.hydro.optimal">
        <label>Identify optimal river segment</label>
      </module-item>
      <module-item name="r.green.hydro.structure">
        <label>Compute channels and penstocks</label>
      </module-item>
      <module-item name="r.green.hydro.delplants">
        <label>Delete segments where there is an existing plant</label>
      </module-item>
    </items>
  </toolbox>
</toolboxes>
""".format(
    XMLMAINMENU=XMLMAINMENU
)


def value_not_none(method):
    """Check if the attribute 'value' of the instance is not null before call
    the instance method"""

    def decorator(*args, **kwargs):
        """If the value is not null call the method"""
        self = args[0]
        if self.value is not None:
            method(*args, **kwargs)
        else:
            return

    return decorator


def get_vals(string):
    """Extract values to decript url from a string

    >>> string = ('javascript:dl([105,121,76,112,51,111,45,50,108,99,104,'
    ...           '101,116,46,122,110,87,47,114,55,73,52,119,67,48,69,72]'
    ...           ', "BD@C>2IJAG1<:5?6H=74=E6937C6?5?;6F0?47=F:8")')
    >>> get_vals(string)
    ([105,121,76,112,51,111,45,50,108,99,104,101,116,46,122,110,87,47,114,55,73,52,119,67,48,69,72],
     'BD@C>2IJAG1<:5?6H=74=E6937C6?5?;6F0?47=F:8')
    """
    nums, chars = string[string.find("(") + 1 : string.find(")")].split(", ")
    return [int(n) for n in nums[1:-1].split(",")], chars.strip('"')


class PkgHTMLParser(HTMLParser):
    """Extract all the <li> ... </li> elements from a webpage"""

    tag = "a"
    values = []
    value = None
    packages = {}

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            self.value = dict(
                attrs=attrs, data=[], comment=[], entityref={}, charref={}, decl=[]
            )

    def handle_endtag(self, tag):
        if tag == self.tag:
            if self.value is not None and len(self.value["data"]) > 1:
                pname = "".join(self.value["data"])
                pkey = pname.split("-")[0]
                pdict = self.packages.get(pkey, {})

                dval = dict(self.value["attrs"])
                # save only if onclick is in the attrs
                if "onclick" in dval:
                    nums, chars = get_vals(dval["onclick"])
                    self.value["url"] = get_decripted_url(nums, chars)
                    pdict[pname] = self.value["url"]
                    self.values.append(self.value)
                    self.packages[pkey] = pdict
            self.value = None

    @value_not_none
    def handle_data(self, data):
        self.value["data"].append(data)

    @value_not_none
    def handle_comment(self, data):
        self.value["comment"].append(data)

    @value_not_none
    def handle_entityref(self, name):
        nlist = self.value["entityref"].get(name, [])
        nlist.append(unichr(name2codepoint[name]))
        self.value["entityref"][name] = nlist

    @value_not_none
    def handle_charref(self, name):
        self.value["data"].append(
            unichr(int(name[1:], 16)) if name.startswith("x") else unichr(int(name))
        )

    @value_not_none
    def handle_decl(self, data):
        self.value["decl"].append(data)


def get_settings_path():
    """Get full path to the settings directory"""
    # TODO: remove this function once the GetSettingsPath function is moved in
    # grass.script.utils or similia
    return (
        join(os.getenv("APPDATA"), "GRASS%d" % 7)
        if sys.platform.startswith("win")
        else join(os.getenv("HOME"), ".grass%d" % 7)
    )


def download(url, filepath, overwrite=False):
    """Download a pkg from URLWHL"""
    if os.path.exists(filepath):
        print("The file: %s already exist!" % filepath)
        if overwrite:
            print("Removing previous downloaded version")
            os.remove(filepath)
        else:
            return filepath
    print("Downloading from:", url)
    print("Saving to:", filepath)
    opener = build_opener()
    opener.addheaders = [("User-agent", UAGENT)]
    response = opener.open(url)
    with open(filepath, mode="wb") as fpath:
        fpath.write(response.read())
    print("Done!")
    return filepath


def get_decripted_url(nums, chars):
    """Return the decripted url

    Example
    --------

    >>> nums = [50, 99, 108, 117, 101, 106, 51, 109, 45, 121, 103,
    ...         113, 114, 47, 110, 56, 116, 55, 115, 46, 112, 111,
    ...         105, 119, 104]
    >>> chars = ("@3:9&lt;H;E=BF7D245BE&#62;86C?C081D"
    ...          "0A81D0A78GF&#62;60CGH2")
    >>> get_decripted_url(nums, chars)
    "tugyrhqo/simplejson-3.8.2-cp27-cp27m-win32.whl"

    Javascript code
    ----------------

    function dl(ml,mi){
        mi=mi.replace('&lt;','<');
        mi=mi.replace('&#62;','>');
        mi=mi.replace('&#38;','&')
    setTimeout(function(){dl1(ml,mi)},1500);
    }

    function dl1(ml,mi){
        var ot="";
        for(var j=0;j<mi.length;j++)
            ot+=String.fromCharCode(ml[mi.charCodeAt(j)-48]);
        location.href=ot;
    }

    javascript:dl([99,113,118,117,116,52,51,121,46,103,114,
                   119,110,97,105,45,47,101,108,49,112,109,111,104,50],
                  "4397:G1F@D7E2D=H?H858C?0D65?&lt;F&lt;A?;&#62;&lt;6H8;GB")

    """

    def transform(chars):
        chars = chars.replace("&lt;", "<")
        chars = chars.replace("&#62;", ">")
        return chars.replace("&#38;", "&")

    return "".join([chr(nums[ord(c) - 48]) for c in transform(chars)])


def get_url(
    lib,
    _parser=[
        None,
    ],
):
    """Return the complete url to download the wheel file for windows"""

    urlwin = "http://www.lfd.uci.edu/~gohlke/pythonlibs/"

    def match():
        """Match platform with available wheel files on the web page"""
        pkgs = sorted(parser.packages[lib].keys())
        cppy = "cp%d%d" % (sys.version_info.major, sys.version_info.minor)
        pltf = "win_amd64.whl" if platform.architecture()[0] == "64bit" else "win32.whl"
        result = None
        for pki in pkgs[::-1]:
            pkk = Pkg(*pki.split("-"))
            if pkk.py == cppy and pkk.platform == pltf:
                result = pki
                break
        if result is None:
            print("=> Library not found for your system", cppy, pltf[:-4])
            sys.exit(1)
        return result, parser.packages[lib][result]

    # check the cache
    if _parser[0] is None:
        # read and parse the HTML page
        opener = build_opener()
        opener.addheaders = [("User-agent", UAGENT)]
        response = opener.open(urlwin)
        parser = PkgHTMLParser()
        parser.feed(response.read())
        # save the instance to the cache
        _parser[0] = parser
    else:
        # load the instance from the cache
        parser = _parser[0]

    if lib not in parser.packages:
        print(lib, "not in the package list:")
        from pprint import pprint

        pprint(sorted(parser.packages))
        sys.exit(1)

    pkg, pkgurl = match()
    return (urlwin + pkgurl, pkg)


def get_pip_win_env():
    """Add pip path to the windows environmental variable"""
    os_pth = os.__file__.split(os.path.sep)
    script_pth = os.sep.join(
        os_pth[:-2]
        + [
            "Scripts",
        ]
    )
    if not os.path.exists(script_pth):
        msg = "The directory containing python scripts does not exist!"
        raise Exception(msg)

    env = os.environ.copy()
    path = env["PATH"].split(";")
    if script_pth not in path:
        path.append(script_pth)
        env["PATH"] = ";".join(path)

    return env


def pip_install(whl, *pipargs):
    """Install a whl using pip"""
    cmd = ["pip", "install", whl]
    cmd.extend(pipargs)
    popen_pip = subprocess.Popen(cmd, shell=True, env=get_pip_win_env())
    if popen_pip.wait():
        print(
            (
                "Something went wrong during the installation, "
                "of {whl} please fix this "
                "manually. Running: "
            ).format(whl=whl)
        )
        print(" ".join(cmd))
        sys.exit(1)


def check_install_pip(install=False):
    """Check if pip is available"""
    env = get_pip_win_env() if "win" in sys.platform else {}
    # run pip and check return code
    popen_pip = subprocess.Popen(
        ["pip", "--help"], stdout=subprocess.PIPE, shell=True, env=env
    )
    if popen_pip.wait():
        print("pip is not available")
        if install:
            print("Downloading pip")
            # download get_pip.py
            dst = download(
                "https://bootstrap.pypa.io/get-pip.py",
                os.path.join(gettempdir(), "get_pip.py"),
            )
            # install pip
            print("Installing pip")
            popen_py = subprocess.Popen([sys.executable, dst])
            if popen_py.returncode:
                print(
                    "Something wrong during the installation of pip,"
                    " perhaps permissions"
                )
    else:
        print("pip is available on the sys path")


def win_install(libs):
    """Download and install missing libraries under windows"""
    dlibs = {lib: get_url(lib) for lib in libs}
    msg = "- {lib}: {pkg}\n  from: {urlwhl}"
    print("Downloading:")
    for lib in libs:
        print(msg.format(lib=lib, urlwhl=dlibs[lib][0], pkg=dlibs[lib][1]))

    for lib in libs:
        urlwhl, pkg = dlibs[lib]
        # download wheel file
        whlpath = download(urlwhl, os.path.join(gettempdir(), pkg))
        pip_install(whlpath, "--user", "--upgrade")

    print("\n\nMissiging libreries %s installed!\n" % ", ".join(libs))


def fix_missing_libraries(install=False):
    """Check if the external libraries used by r.green are
    available in the current path."""
    to_be_installed = []
    for lib in CHECK_LIBRARIES:
        try:
            imp.find_module(lib)
            print(lib, "available in the sys path")
        except ImportError:
            to_be_installed.append(lib)

    if to_be_installed:
        print("the following libraries are missing:")
        for lib in to_be_installed:
            print("- ", lib)

        if install:
            if "win" in sys.platform:
                # download precompiled wheel and install them
                print("Download the wheel file for your platform from:")
                # add numpy+mkl
                to_be_installed.insert(0, "numpy")
                win_install(to_be_installed)
                # win_install(lib)
            else:
                cmd = ["pip", "install"].extend(to_be_installed)
                cmd.append("--user")
                popen_pip = subprocess.Popen(cmd)
                if popen_pip.wait():
                    print(
                        "Something went wrong during the installation, "
                        "please fix this manually"
                    )
                    print(cmd)
                    sys.exit(1)


def add_rgreen_menu():
    """Add/Update the xml used to define the GRASS GUI"""

    def toolboxes2dict(toolboxes):
        """Trnsform a list of toolbox elements into a dictionary"""
        return {toolbox.find("label").text: toolbox for toolbox in toolboxes}

    def get_or_create(xmlfile, sysdir, usrdir):
        """Check if XML files already exist"""
        xml_path = join(usrdir, xmlfile)

        if not os.path.exists(xml_path):
            print("Copying %s to %s" % (join(sysdir, xmlfile), xml_path))
            shutil.copyfile(join(sysdir, xmlfile), xml_path)
        return xml_path

    def read_update_xml(main_path, tool_path):
        """Read XML files and update toolboxes acordingly"""
        main_tree = ET.parse(main_path)
        main_root = main_tree.getroot()
        tool_tree = ET.parse(tool_path)
        tool_root = tool_tree.getroot()

        # check if the update of the main xml it is necessary
        main_items = main_root.find("items")
        update_main = True
        for item in main_items:
            if item.attrib["name"] == XMLMAINMENU:
                update_main = False

        if update_main:
            print("Updating", main_path)
            menrg = main_items[0].copy()
            menrg.attrib["name"] = XMLMAINMENU
            main_items.insert(-1, menrg)
            main_tree.write(main_path)

        toolboxes = toolboxes2dict(tool_root.findall("toolbox"))
        enrg_tools = toolboxes2dict(ET.fromstring(XMLENERGYTOOLBOX))

        # update the energy toolboxes
        print("Updating", tool_path)
        for key in enrg_tools:
            if key in toolboxes:
                tool_root.remove(toolboxes[key])
            tool_root.append(enrg_tools[key])
        tool_tree.write(tool_path)

    grass_tool_path = join(os.getenv("GISBASE"), "gui", "wxpython", "xml")
    user_tool_path = join(get_settings_path(), "toolboxes")

    # read XML input files
    main_path = get_or_create("main_menu.xml", grass_tool_path, user_tool_path)
    tool_path = get_or_create("toolboxes.xml", grass_tool_path, user_tool_path)

    read_update_xml(main_path, tool_path)


if __name__ == "__main__":
    opts, flgs = gcore.parser()

    check_install_pip(flgs["i"])
    fix_missing_libraries(flgs["i"])

    if flgs["x"]:
        add_rgreen_menu()
