#!/usr/bin/env python

#%module
#% label: Extracts specified categories of the integer input map
#% keyword: raster
#% keyword: extract
#% keyword: extent
#%end
#%option G_OPT_R_INPUT
#%end
#%option G_OPT_R_OUTPUT
#%end
#%option
#% key: cats
#% type: string
#% required: yes
#% multiple: no
#% key_desc: range
#% label: Category values
#% description: Example: 1,3,7-9,13
#% gisprompt: old,cats,cats
#%end


import sys
import atexit

import grass.script as gs


TMP = []


def cleanup():
    if TMP:
        gs.run_command('g.remove', type='raster', name=TMP, flags='f', quiet=True)


def parse(raster, values):
    info = gs.raster_info(raster)
    if info['datatype'] != 'CELL':
        gs.fatal(_("Input raster map must be of type CELL"))
    rules = []
    vals = values.split(',')
    for val in vals:
        if '-' in val:
            a, b = val.split('-')
            if not a:
                a = info['min']
            if not b:
                b = info['max']
            for i in range(int(a), int(b) + 1):
                rules.append("{v} = {v}".format(v=i))
        else:
            rules.append("{v} = {v}".format(v=val))
    return rules


def main():
    options, flags = gs.parser()

    original = options['input']
    output = options['output']
    cats = options['cats']

    output_tmp = gs.append_random('tmp', 8)
    rules = parse(original, cats)
    TMP.append(output_tmp)
    gs.write_command('r.reclass', input=original, output=output_tmp,
                     rules='-', stdin='\n'.join(rules))
    gs.use_temp_region()
    gs.run_command('g.region', zoom=output_tmp)
    gs.mapcalc(output + " = " + output_tmp)
    gs.run_command('r.colors', map=output, raster=original)
    gs.del_temp_region()


if __name__ == '__main__':
    atexit.register(cleanup)
    sys.exit(main())
