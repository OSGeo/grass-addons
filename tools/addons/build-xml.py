#!/usr/bin/env python

# Support Python script used by compile-xml.sh

import os
import sys
import glob
import tempfile
import argparse
from   datetime import datetime

def get_list(addons):
    mlist = [d for d in os.listdir(os.path.join(addons)) if os.path.isdir(os.path.join(addons, d))]
    if 'logs' in mlist:
        mlist.remove('logs')
    mlist.sort()
    return mlist

# def get_gui_list(g7 = True):
#     mlist = list()
#     for m in os.listdir(os.path.join(ADDON_PATH, 'grass%s' % ('7' if g7 else '6'),
#                                      'gui', 'wxpython')):
#         if len(m) > 3 and m[:3] == 'wx.':
#             mlist.append(m)
    
#     return mlist
                      
def start_grass():
    gisdbase = tempfile.gettempdir()
    location = "demolocation"
    mapset   = "PERMANENT"
 
    sys.path.insert(0, os.path.join(os.environ['GISBASE'], "etc", "python"))
    import grass.script as grass
    import grass.script.setup as gsetup
    
    gsetup.init(os.environ['GISBASE'],
                gisdbase, location, mapset)
    grass.create_location(gisdbase,
                          location, overwrite=True)

class BuildXML:
    def __init__(self, build_path):
        self.build_path = build_path

    def run(self):
        with open(os.path.join(self.build_path, 'modules.xml'), 'w') as fd:
            self._header(fd)
            self._parse_modules(fd, get_list(self.build_path))
            # self._parse_gui_modules(fd, get_gui_list(g7))
            self._footer(fd)

    def _parse_modules(self, fd, mlist):
        indent = 4
        blacklist = ['v.feature.algebra', 'm.eigensystem']
        for m in mlist:
            if m in blacklist:
                continue # skip blacklisted modules
            print("Parsing <{}>...".format(m), end='')
            desc, keyw = self._get_module_metadata(m)
            fd.write('%s<task name="%s">\n' % (' ' * indent, m))
            indent += 4
            fd.write('%s<description>%s</description>\n' % (' ' * indent, desc))
            fd.write('%s<keywords>%s</keywords>\n' % (' ' * indent, ','.join(keyw)))
            fd.write('%s<binary>\n' % (' ' * indent))
            indent += 4
            for f in self._get_module_files(m):
                fd.write('%s<file>%s</file>\n' % (' ' * indent, f))
            indent -= 4
            fd.write('%s</binary>\n' % (' ' * indent))
            indent -= 4
            fd.write('%s</task>\n' % (' ' * indent))
            if desc:
                print(" SUCCESS")
            else:
                print(" FAILED")

    @staticmethod
    def parse_gui_modules(fd, mlist):
        indent = 4
        for m in mlist:
            print("Parsing <{}>...".format(m))
            fd.write('%s<task name="%s">\n' % (' ' * indent, m))
            fd.write('%s</task>\n' % (' ' * indent))

    def _scandirs(self, path):
        flist = list()
        for f in glob.glob(os.path.join(path, '*') ):
            if os.path.isdir(f):
                flist += self._scandirs(f)
            else:
                flist.append(f)

        return flist

    def _get_module_files(self, name):
        os.chdir(os.path.join(self.build_path, name))
        return self._scandirs('*')

    def _get_module_metadata(self, name):
        import grass.script.task as gtask
        path = os.environ['PATH']
        os.environ['PATH'] += os.pathsep + os.path.join(self.build_path, name, 'bin') + os.pathsep + \
            os.path.join(self.build_path, name, 'scripts')
        try:
            task = gtask.parse_interface(name)
        except:
            task = None

        os.environ['PATH'] = path
        if not task:
            return '', ''

        return task.get_description(full = True), \
            task.get_keywords()

    @staticmethod
    def _header(fd):
        import grass.script.core as grass
        fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fd.write('<!DOCTYPE task SYSTEM "grass-addons.dtd">\n') # TODO
        # doesn't work in GRASS 6
        # vInfo = grass.version()
        vInfo = grass.parse_command('g.version', flags='g')
        fd.write('<addons version="%s" revision="%s" date="%s">\n' % \
                     (vInfo['version'].split('.')[0],
                      vInfo['revision'],
                      datetime.now()))

    @staticmethod
    def _footer(fd):
        fd.write('</addons>\n')

def main(build_path):
    start_grass()

    builder = BuildXML(build_path)
    builder.run()

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build",
                        help="Path to GRASS Addons build",
                        required=True)
    parser.add_argument("--gisbase",
                        help="Path to GRASS installation",
                        required=True)
    args = parser.parse_args()

    # set up GRASS gisbase
    os.environ['GISBASE'] = args.gisbase

    sys.exit(main(args.build))
