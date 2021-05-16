#!/usr/bin/env python

############################################################################
#
# MODULE:       v.in.gns
#
# AUTHOR(S):    Markus Neteler, neteler itc it
#               Converted to Python by Glynn Clements
#
# PURPOSE:      Import GEOnet Names Server (GNS) country files into a GRASS vector map
#               http://earth-info.nga.mil/gns/html/
#                -> Download Names Files for Countries and Territories (FTP)
#
#               Column names: http://earth-info.nga.mil/gns/html/help.htm
#
# COPYRIGHT:    (c) 2005 GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# TODO:         - see below in the code
#               - add extra columns explaining some column acronyms,
#                 e.g. FC (Feature Classification)
#############################################################################

#%module
#% description: Imports US-NGA GEOnet Names Server (GNS) country files into a GRASS vector points map.
#% keyword: vector
#% keyword: import
#% keyword: gazetteer
#%end
#%option G_OPT_F_INPUT
#% description: Name of input uncompressed GNS file from NGA (with .txt extension)
#%end
#%option G_OPT_V_OUTPUT
#% required: no
#%end

from grass.script.utils import try_remove, basename, parse_key_val
from grass.script import core as grass
from grass.script import vector as vgrass


def main():
    fileorig = options['input']
    filevect = options['output']

    if not filevect:
        filevect = basename(fileorig, 'txt')

    #are we in LatLong location?
    s = grass.read_command("g.proj", flags='j')
    kv = parse_key_val(s)
    if kv['+proj'] != 'longlat':
        grass.fatal(_("This module only operates in LatLong/WGS84 locations"))

    #### setup temporary file
    tmpfile = grass.tempfile()

    coldescs = [("RC", "rc integer"),
                ("UFI", "uf1 integer"),
                ("UNI", "uni integer"),
                ("LAT", "lat double precision"),
                ("LONG", "lon double precision"),
                ("DMS_LAT", "dms_lat integer"),
                ("DMS_LONG", "dms_long integer"),
                ("MGRS", "mgrs varchar(15)"),
                ("JOG", "jog varchar(7)"),
                ("FC", "fc varchar(1)"),
                ("DSG", "dsg varchar(6)"),
                ("PC", "pc integer"),
                ("CC1", "cci varchar(255)"),
                ("ADM1", "adm1 varchar(2)"),
                ("POP", "pop integer"),
                ("ELEV", "elev double precision"),
                ("CC2", "cc2 varchar(255)"),
                ("NT", "nt varchar(2)"),
                ("LC", "lc varchar(3)"),
                ("SHORT_FORM", "shortform varchar(128)"),
                ("GENERIC", "generic varchar(128)"),
                ("SORT_NAME_RO", "sortnamero varchar(255)"),
                ("FULL_NAME_RO", "fullnamero varchar(255)"),
                ("FULL_NAME_ND_RO", "funamesdro varchar(255)"),
                ("SORT_NAME_RG", "sortnamerg varchar(255)"),
                ("FULL_NAME_RG", "fullnamerg varchar(255)"),
                ("FULL_NAME_ND_RG", "funamesdrg varchar(255)"),
                ("NOTE", "note varchar(4000)"),
                ("MODIFY_DATE", "mod_date date"),
                ("DISPLAY", "display varchar(255)"),
                ("NAME_RANK", "namerank integer"),
                ("NAME_LINK", "namelink integer"),
                ("TRANSL_CD", "translcd varchar(32)"),
                ("NM_MODIFY_DATE", "nmmodifydate varchar(10)")]

    colnames = [desc[0] for desc in coldescs]
    coltypes = dict([(desc[0], 'integer' in desc[1]) for desc in coldescs])

    header = None
    num_places = 0
    inf = open(fileorig)
    outf = open(tmpfile, "wb")
    for line in inf:
        fields = line.rstrip('\r\n').split('\t')
        if not header:
            header = fields
            continue
        vars = dict(zip(header, fields))
        fields2 = []
        for col in colnames:
            if col in vars:
                if coltypes[col] and vars[col] == '':
                    fields2.append('0')
                else:
                    fields2.append(vars[col])
            else:
                if coltypes[col]:
                    fields2.append('0')
                else:
                    fields2.append('')
        line2 = ';'.join(fields2) + '\n'
        outf.write(line2)
        num_places += 1
    outf.close()
    inf.close()

    grass.message(_("Converted %d place names.") % num_places)

    #TODO: fix dms_lat,dms_long DDMMSS -> DD:MM:SS
    # Solution:
    # IN=DDMMSS
    # DEG=`echo $IN | cut -b1,2`
    # MIN=`echo $IN | cut -b3,4`
    # SEC=`echo $IN | cut -b5,6`
    # DEG_STR="$DEG:$MIN:$SEC"

    #modifications (to match DBF 10 char column name limit):
    # short_form   -> shortform
    # sort_name    -> sortname
    # full_name    -> fullname
    # full_name_sd -> funamesd

    # pump data into GRASS:

    columns = [desc[1] for desc in coldescs]

    grass.run_command('v.in.ascii', cat=0, x=5, y=4, sep=';',
                      input=tmpfile, output=filevect, columns=columns)

    try_remove(tmpfile)

    # write cmd history:
    vgrass.vector_history(filevect)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
