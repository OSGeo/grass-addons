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
#% key: m
#% description: Move r.green libraries in the right place
#%end


# import system libraries
from __future__ import print_function
import os
import sys
import imp
import tempfile
import subprocess
import shutil

from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
import urllib2

from collections import namedtuple
import platform


# import grass libraries
from grass.script import core as gcore
from grass.pygrass.utils import set_path


Pkg = namedtuple('Pkg', ['name', 'version', 'py', 'un', 'platform'])


CHECK_LIBRARIES = ['scipy', 'numexpr']
CHECK_RGREENLIB = [('libgreen', '..'),
                   ('libhydro', os.path.join('..', 'r.green.hydro'))]


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


def check_install_pip(install=False):
    """Check if pip is available"""
    # run pip and check return code
    popen_pip = subprocess.Popen(['pip', '--help'], stdout=subprocess.PIPE)
    if popen_pip.wait():
        print('pip is not available')
        if install:
            print('Downloading pip')
            # download get_pip.py
            response = urllib2.urlopen('https://bootstrap.pypa.io/get-pip.py')
            with open('get_pip.py', mode='w') as getpip:
                getpip.write(response.read())

            # install pip
            print('Installing pip')
            popen_py = subprocess.Popen([sys.executable, 'get_pip.py'])
            if popen_py.returncode:
                print('Something wrong during the installation of pip,'
                      ' perhaps permissions')
    else:
        print('pip is available on the sys path')


def fix_missing_libraries(install=False):
    """Check if the external libraries used by r.green are
    available in the current path."""

    urlwin = 'http://www.lfd.uci.edu/~gohlke/pythonlibs'

    def get_url(lib, _parser=[None, ]):
        """Return the complete url to download the wheel file for windows"""

        def match():
            """Match platform with available wheel files on the web page"""
            pkgs = parser.packages[lib]
            cppy = 'cp' + str(sys.version_info.major) + str(sys.version_info.minor)
            pltf = 'win_amd64.whl' if platform.architecture() == '64bit' else 'win32.whl'
            result = None
            for pki in pkgs[::-1]:
                pkk = Pkg(*pkg.split('-'))
                if pkk.py == cppy and pkk.platform == pltf:
                    result = pki
                    break
            if result is None:
                print('=> Library not found for your system', cppy, pltf[:-4])
                sys.exit()
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
            sys.exit()

        pkg = match()
        return ('http://www.lfd.uci.edu/~gohlke/pythonlibs/bofhrmxk/' + pkg,
                pkg)

    def win_install(lib):
        """Download and install missing libraries under windows"""
        # get wheel url
        urlwhl, pkg = get_url(lib)
        dst = os.path.join(tempfile.gettempdir(), pkg)
        print('Downloading:', urlwhl, 'file in:', dst)
        response = urllib2.urlopen(urlwhl)
        with open(dst, mode='w') as getwhl:
            getwhl.write(response.read())
        cmd = ['pip', 'install', dst, '--user']
        popen_pip = subprocess.Popen(cmd)
        if popen_pip.wait():
            print('Something went wrong during the installation, '
                  'please fix this manually')
            print(cmd)
            sys.exit()

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
            if sys.platform.startswith('win') or sys.platform.startswith('cyg'):
                # download precompiled wheel and install them
                print('Download the wheel file manually for your platform from:')
                # http://www.lfd.uci.edu/~gohlke/pythonlibs/bofhrmxk/numexpr-2.4.6-cp27-none-win_amd64.whl
                for lib in to_be_installed:
                    win_install(lib)
            else:
                cmd = ['pip', 'install'].extend(to_be_installed)
                cmd.append('--user')
                popen_pip = subprocess.Popen(cmd)
                if popen_pip.wait():
                    print('Something went wrong during the installation, '
                          'please fix this manually')
                    print(cmd)
                    sys.exit()


def fix_rgreen_libraries(move=False):
    """Check if r.green libraries are correctly positioned

    move from addos into etc/r.green directory:
    ~/.grass7/addons/libgreen => ~/.grass7/addons/etc/r.green/libgreen
    ~/.grass7/addons/libhydro => ~/.grass7/addons/etc/r.green/libhydro
    """
    gaddons = os.environ['GRASS_ADDON_BASE']
    if not gaddons:
        print('Environmental variable GRASS_ADDON_BASE not set!')
        return

    def mvlibs(lib):
        """Move r.green libraries directories into the GRASS addons
        standard directory"""
        wrongpath = os.path.join(gaddons, lib)
        greendir = os.path.join(gaddons, 'etc', 'r.green')
        if os.path.exists(wrongpath):
            if not os.path.exists(greendir):
                os.makedirs(greendir)

            msg = 'Moving r.green library (%s) from: %s to: %s'
            print(msg % (lib, wrongpath, greendir))
            if move:
                shutil.move(wrongpath, greendir)
        else:
            if os.path.exists(greendir):
                print(lib, 'already in the right place:', greendir)

    mvlibs('libgreen')
    mvlibs('libhydro')

    path_problems = False
    # finally import the module in the library
    for lib, relativepath in CHECK_RGREENLIB:
        set_path('r.green', lib, relativepath)
        try:
            imp.find_module(lib)
        except ImportError:
            print('Not able to import %s' % lib)
            path_problems = True

    if path_problems:
        print('Some libraries seem not available in the current path:')
        for path in sys.path:
            print('- ', path)


if __name__ == "__main__":
    opts, flgs = gcore.parser()

    check_install_pip(flgs['i'])
    fix_missing_libraries(flgs['i'])
    fix_rgreen_libraries(flgs['m'])
