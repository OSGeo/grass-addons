#!/usr/bin/env python

import os
import sys

def get_list(addons):
    mlist = os.listdir(os.path.join(addons, 'bin')) + \
        os.listdir(os.path.join(addons, 'scripts'))
    mlist.sort()
    return mlist

def start_grass(mlist, g7 = True):
    if g7:
        ver = 'grass_trunk'
    else:
        ver = 'grass6_devel'
    gisbase = os.environ['GISBASE'] = os.path.join(os.getenv('HOME'),
                                                   "src/%s/dist.x86_64-unknown-linux-gnu" % ver)
    
    gisdbase = os.path.join(gisbase)
    location = "demolocation"
    mapset   = "PERMANENT"
 
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
    import grass.script as grass
    import grass.script.setup as gsetup

    gsetup.init(gisbase,
                gisdbase, location, mapset)
 
    os.environ['PATH'] += os.pathsep + os.path.join(sys.argv[1], 'bin') + os.pathsep + \
        os.path.join(sys.argv[1], 'scripts')

def parse_modules(fd, mlist):
    indent = 4
    for m in mlist:
        print "Parsing <%s>..." % m,
        desc, keyw = get_module_metadata(m)
        fd.write('%s<task name="%s">\n' % (' ' * indent, m))
        indent += 4
        fd.write('%s<description>%s</description>\n' % (' ' * indent, desc))
        fd.write('%s<keywords>%s</keywords>\n' % (' ' * indent, ','.join(keyw)))
        indent -= 4
        fd.write('%s</task>\n' % (' ' * indent))
        if desc:
            print " SUCCESS"
        else:
            print " FAILED"
    
def get_module_metadata(name):
    import grass.script.task as gtask
    try:
        task = gtask.parse_interface(name)
    except:
        return '', ''
    
    return task.get_description(full = True), \
        task.get_keywords()

def header(fd):
    import grass.script.core as grass
    fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    fd.write('<!DOCTYPE task SYSTEM "grass-addons.dtd">\n') # TODO
    fd.write('<modules version=%s>\n' % grass.version()['version'])

def footer(fd):
    fd.write('</modules>\n')

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: %s path_to_addons" % sys.argv[0])
        
    addons = sys.argv[1]
        
    path = os.path.join(addons, 'modules.xml')
    print "-----------------------------------------------------"
    print "Creating XML file '%s'..." % path
    print "-----------------------------------------------------"
    fd = open(path, 'w')
    start_grass(True)

    header(fd)
    parse_modules(fd, get_list(addons))
    footer(fd)

    fd.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
