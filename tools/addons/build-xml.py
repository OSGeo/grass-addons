#!/usr/bin/env python

# Support Python script used by compile-xml.sh

import os
import sys
import glob
from   datetime import datetime

ADDON_PATH = os.path.join(os.getenv('HOME'), 'src', 'grass-addons')
DIST = 'dist.x86_64-pc-linux-gnu'

def get_list(addons):
    mlist = [d for d in os.listdir(os.path.join(addons)) if os.path.isdir(os.path.join(addons, d))]
    if 'logs' in mlist:
        mlist.remove('logs')
    mlist.sort()
    return mlist

def get_gui_list(g7 = True):
    mlist = list()
    for m in os.listdir(os.path.join(ADDON_PATH, 'grass%s' % ('7' if g7 else '6'),
                                     'gui', 'wxpython')):
        if len(m) > 3 and m[:3] == 'wx.':
            mlist.append(m)
    
    return mlist
                      
def start_grass(g7 = True):
    if g7:
        ver = '78'
    else:
        ver = '64'
    gisbase = os.environ['GISBASE'] = os.path.join(os.getenv('HOME'),
                                                   "src/grass%s/%s" % (ver, DIST))
    
    gisdbase = os.path.join(gisbase)
    location = "demolocation"
    mapset   = "PERMANENT"
 
    sys.path.insert(0, os.path.join(os.environ['GISBASE'], "etc", "python"))
    import grass.script as grass
    import grass.script.setup as gsetup
    
    gsetup.init(gisbase,
                gisdbase, location, mapset)
 
def parse_modules(fd, mlist):
    indent = 4
    blacklist = ['v.feature.algebra', 'm.eigensystem']
    for m in mlist:
        if m in blacklist:
            continue # skip blacklisted modules
        print "Parsing <%s>..." % m,
        desc, keyw = get_module_metadata(m)
        fd.write('%s<task name="%s">\n' % (' ' * indent, m))
        indent += 4
        fd.write('%s<description>%s</description>\n' % (' ' * indent, desc))
        fd.write('%s<keywords>%s</keywords>\n' % (' ' * indent, ','.join(keyw)))
        fd.write('%s<binary>\n' % (' ' * indent))
        indent += 4
        for f in get_module_files(m):
            fd.write('%s<file>%s</file>\n' % (' ' * indent, f))
        indent -= 4
        fd.write('%s</binary>\n' % (' ' * indent))
        indent -= 4
        fd.write('%s</task>\n' % (' ' * indent))
        if desc:
            print " SUCCESS"
        else:
            print " FAILED"
  
def parse_gui_modules(fd, mlist):
    indent = 4
    for m in mlist:
        print "Parsing <%s>..." % m
        fd.write('%s<task name="%s">\n' % (' ' * indent, m))
        fd.write('%s</task>\n' % (' ' * indent))
    
def scandirs(path):
    flist = list()
    for f in glob.glob(os.path.join(path, '*') ):
        if os.path.isdir(f):
            flist += scandirs(f)
        else:
            flist.append(f)
    
    return flist

def get_module_files(name):
    os.chdir(os.path.join(sys.argv[1], name))
    return scandirs('*')
                    
def get_module_metadata(name):
    import grass.script.task as gtask
    path = os.environ['PATH']
    os.environ['PATH'] += os.pathsep + os.path.join(sys.argv[1], name, 'bin') + os.pathsep + \
        os.path.join(sys.argv[1], name, 'scripts')
    try:
        task = gtask.parse_interface(name)
    except:
        task = None

    os.environ['PATH'] = path
    if not task:
        return '', ''
    
    return task.get_description(full = True), \
        task.get_keywords()

def header(fd):
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


def footer(fd):
    fd.write('</addons>\n')

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: %s path_to_addons" % sys.argv[0])
        
    addons = sys.argv[1]
    try:
        version = os.path.split(addons)[-2][-1]
        g7 = version == '7'
    except:
        g7 = True
    
    path = os.path.join(addons, 'modules.xml')
    print "-----------------------------------------------------"
    print "Creating XML file '%s'..." % path
    print "-----------------------------------------------------"
    fd = open(path, 'w')
    start_grass(g7)

    header(fd)
    parse_modules(fd, get_list(addons))
    # parse_gui_modules(fd, get_gui_list(g7))
    footer(fd)

    fd.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
