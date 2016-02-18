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

#%module
#% description: Check if evrything is corectly installed and configured
#% keywords: raster
#%end
#%flag
#% key: i
#% description: Install missing libraries
#%end
#%flag
#% key: x
#% description: Add r.green menu to the GRASS GUI
#%end

# import system libraries
from __future__ import print_function
import os
from os.path import join
import sys
import imp
import tempfile
import subprocess
import shutil

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
import urllib2
import xml.etree.ElementTree as ET

from collections import namedtuple
import platform


# import grass libraries
from grass.script import core as gcore


Pkg = namedtuple('Pkg', ['name', 'version', 'py', 'un', 'platform'])


# list packages required by the module
CHECK_LIBRARIES = ['scipy', 'numexpr']
CHECK_RGREENLIB = [('libgreen', '..'),
                   ('libhydro', os.path.join('..', 'r.green.hydro'))]


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
""".format(XMLMAINMENU=XMLMAINMENU)


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


class PkgHTMLParser(HTMLParser):
    """Extract all the <li> ... </li> elements from a webpage"""
    tag = 'li'
    values = []
    value = None
    packages = {}

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            self.value = dict(attrs=attrs, data=[], comment=[],
                              entityref={}, charref={}, decl=[])

    def handle_endtag(self, tag):
        if tag == self.tag:
            if self.value is not None and len(self.value['data']) > 1:
                pname = ''.join(self.value['data'])
                pkey = pname.split('-')[0]
                plist = self.packages.get(pkey, [])
                plist.append(pname)
                self.values.append(self.value)
                self.packages[pkey] = plist
            self.value = None

    @value_not_none
    def handle_data(self, data):
        self.value['data'].append(data)

    @value_not_none
    def handle_comment(self, data):
        self.value['comment'].append(data)

    @value_not_none
    def handle_entityref(self, name):
        nlist = self.value['entityref'].get(name, [])
        nlist.append(unichr(name2codepoint[name]))
        self.value['entityref'][name] = nlist

    @value_not_none
    def handle_charref(self, name):
        self.value['data'].append(unichr(int(name[1:], 16))
                                  if name.startswith('x') else
                                  unichr(int(name)))

    @value_not_none
    def handle_decl(self, data):
        self.value['decl'].append(data)


def get_settings_path():
    """Get full path to the settings directory
    """
    # TODO: remove this function once the GetSettingsPath function is moved in
    # grass.script.utils or similia
    return (join(os.getenv('APPDATA'), 'GRASS%d' % 7)
            if sys.platform.startswith('win') else
            join(os.getenv('HOME'), '.grass%d' % 7))


def check_install_pip(install=False):
    """Check if pip is available"""
    # run pip and check return code
    popen_pip = subprocess.Popen(['pip', '--help'],
                                 stdout=subprocess.PIPE, shell=True)
    if popen_pip.wait():
        print('pip is not available')
        if install:
            print('Downloading pip')
            # download get_pip.py
            response = urllib2.urlopen('https://bootstrap.pypa.io/get-pip.py')
            dst = os.path.join(tempfile.gettempdir(), 'get_pip.py')
            with open(dst, mode='w') as getpip:
                getpip.write(response.read())

            # install pip
            print('Installing pip')
            popen_py = subprocess.Popen([sys.executable, dst])
            if popen_py.returncode:
                print('Something wrong during the installation of pip,'
                      ' perhaps permissions')
    else:
        print('pip is available on the sys path')


def fix_missing_libraries(install=False):
    """Check if the external libraries used by r.green are
    available in the current path."""

    urlwin = 'http://www.lfd.uci.edu/~gohlke/pythonlibs'
    urlwhl = 'http://www.lfd.uci.edu/~gohlke/pythonlibs/bofhrmxk/'

    def get_url(lib, _parser=[None, ]):
        """Return the complete url to download the wheel file for windows"""

        def match():
            """Match platform with available wheel files on the web page"""
            pkgs = parser.packages[lib]
            cppy = 'cp%d%d' % (sys.version_info.major, sys.version_info.minor)
            pltf = ('win_amd64.whl'
                    if platform.architecture()[0] == '64bit' else 'win32.whl')
            result = None
            for pki in pkgs[::-1]:
                pkk = Pkg(*pki.split('-'))
                if pkk.py == cppy and pkk.platform == pltf:
                    result = pki
                    break
            if result is None:
                print('=> Library not found for your system', cppy, pltf[:-4])
                sys.exit(1)
            return result

        # check the cache
        if _parser[0] is None:
            # read and parse the HTML page
            response = urllib2.urlopen(urlwin)
            parser = PkgHTMLParser()
            parser.feed(response.read())
            # save the instance to the cache
            _parser[0] = parser
        else:
            # load the instance from the cache
            parser = _parser[0]

        if lib not in parser.packages:
            print(lib, 'not in the package list:')
            from pprint import pprint
            pprint(sorted(parser.packages))
            sys.exit(1)

        pkg = match()
        return (urlwhl + pkg, pkg)

    def win_install(libs):
        """Download and install missing libraries under windows"""
        def get_user_input():
            """Ask what to do to the user"""
            key = raw_input("press ENTER to continue or q to exit.\n")
            if key in ('', 'q'):
                return key
            else:
                print("{key} is not supported!\n".format(key=key))
                return get_user_input()

        def pip_install(whl, *pipargs):
            """Install a whl using pip"""
            cmd = ['pip', 'install', whl]
            cmd.extend(pipargs)
            popen_pip = subprocess.Popen(cmd, shell=True)
            if popen_pip.wait():
                print(('Something went wrong during the installation, '
                       'of {whl} please fix this '
                       'manually. Running: ').format(whl=whl))
                print(' '.join(cmd))
                sys.exit(1)

        # dst = os.path.join(tempfile.gettempdir(), pkg)
        dst = os.environ['GISBASE']
        print("Please download:")
        dlibs = {lib: get_url(lib) for lib in libs}

        get_url('numpy')
        msg = """- {lib}: {pkg}
  from: {urlwhl}"""
        for lib in dlibs:
            print(msg.format(lib=lib, urlwhl=dlibs[lib][1], pkg=dlibs[lib][0]))

        print(('\nDownload the aforementioned files with your browser'
               ' and save them in the following directory:\n  '
               '{dst}\n').format(dst=dst))

        print("\nOnce you have done ", end='')
        key = get_user_input()

        if key == 'q':
            sys.exit()

        for lib in libs:
            whlpath = join(dst, dlibs[lib][1])
            if not os.path.exists(whlpath):
                print("Wheel file: {whl} not found! Exit.".format(whl=whlpath))
                sys.exit(1)
            pip_install(whlpath, '--user', '--upgrade')

    to_be_installed = []
    for lib in CHECK_LIBRARIES:
        try:
            imp.find_module(lib)
            print(lib, 'available in the sys path')
        except ImportError:
            to_be_installed.append(lib)

    if to_be_installed:
        print('the following libraries are missing:')
        for lib in to_be_installed:
            print('- ', lib)

        if install:
            if 'win' in sys.platform:
                # download precompiled wheel and install them
                print('Download the wheel file manually for your platform from:')
                # add numpy+mkl
                to_be_installed.insert(0, 'numpy')
                win_install(to_be_installed)
                # win_install(lib)
            else:
                cmd = ['pip', 'install'].extend(to_be_installed)
                cmd.append('--user')
                popen_pip = subprocess.Popen(cmd)
                if popen_pip.wait():
                    print('Something went wrong during the installation, '
                          'please fix this manually')
                    print(cmd)
                    sys.exit(1)


def add_rgreen_menu():
    """Add/Update the xml used to define the GRASS GUI"""

    def toolboxes2dict(toolboxes):
        """Trnsform a list of toolbox elements into a dictionary"""
        return {toolbox.find('label').text: toolbox for toolbox in toolboxes}

    def get_or_create(xmlfile, sysdir, usrdir):
        """Check if XML files already exist"""
        xml_path = join(usrdir, xmlfile)

        if not os.path.exists(xml_path):
            print('Copying %s to %s' % (join(sysdir, xmlfile),
                                        xml_path))
            shutil.copyfile(join(sysdir, xmlfile), xml_path)
        return xml_path

    def read_update_xml(main_path, tool_path):
        """Read XML files and update toolboxes acordingly"""
        main_tree = ET.parse(main_path)
        main_root = main_tree.getroot()
        tool_tree = ET.parse(tool_path)
        tool_root = tool_tree.getroot()

        # check if the update of the main xml it is necessary
        main_items = main_root.find('items')
        update_main = True
        for item in main_items:
            if item.attrib['name'] == XMLMAINMENU:
                update_main = False

        if update_main:
            print("Updating", main_path)
            menrg = main_items[0].copy()
            menrg.attrib['name'] = XMLMAINMENU
            main_items.insert(-1, menrg)
            main_tree.write(main_path)

        toolboxes = toolboxes2dict(tool_root.findall('toolbox'))
        enrg_tools = toolboxes2dict(ET.fromstring(XMLENERGYTOOLBOX))

        # update the energy toolboxes
        print("Updating", tool_path)
        for key in enrg_tools:
            if key in toolboxes:
                tool_root.remove(toolboxes[key])
            tool_root.append(enrg_tools[key])
        tool_tree.write(tool_path)

    grass_tool_path = join(os.getenv('GISBASE'), 'gui', 'wxpython', 'xml')
    user_tool_path = join(get_settings_path(), 'toolboxes')

    # read XML input files
    main_path = get_or_create('main_menu.xml', grass_tool_path, user_tool_path)
    tool_path = get_or_create('toolboxes.xml', grass_tool_path, user_tool_path)

    read_update_xml(main_path, tool_path)


if __name__ == "__main__":
    opts, flgs = gcore.parser()

    check_install_pip(flgs['i'])
    fix_missing_libraries(flgs['i'])

    if flgs['x']:
        add_rgreen_menu()
