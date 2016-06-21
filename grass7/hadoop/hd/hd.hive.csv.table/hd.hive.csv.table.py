#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       hd.hive.csv.table
# AUTHOR(S):    Matej Krejci (matejkrejci@gmail.com
#
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Hive table creator
#% keyword: database
#% keyword: hdfs
#% keyword: hive
#%end

#%option
#% key: driver
#% type: string
#% required: yes
#% answer: hiveserver2
#% description: Type of database driver
#% options: hiveserver2
#%end
#%option
#% key: table
#% type: string
#% required: yes
#% description: name of table
#% guisection: table
#%end
#%option
#% key: columns
#% type: string
#% required: yes
#% description: python dictionary {attribute:datatype}
#% guisection: table
#%end
#%option
#% key: stored
#% type: string
#% required: no
#% answer: textfile
#% description: output
#% guisection: table
#%end
#%option
#% key: outputformat
#% type: string
#% required: no
#% description: output
#% guisection: table
#%end
#%option
#% key: csvpath
#% type: string
#% required: no
#% description: hdfs path specifying input data
#% guisection: data
#%end
#%option
#% key: partition
#% type: string
#% required: no
#% description: arget partition as a dict of partition columns and values
#% guisection: data
#%end
#%option
#% key: serde
#% type: string
#% description: java class for serialization of json
#% guisection: table
#%end
#%option
#% key: delimeter
#% type: string
#% required: yes
#% answer: ,
#% description: csv delimeter of fields
#% guisection: data
#%end
#%flag
#% key: o
#% description: Optional if csvpath for loading data is delcared. overwrite all data in table.
#% guisection: data
#%end
#%flag
#% key: d
#% description: Firstly drop table if exists
#% guisection: table
#%end
#%flag
#% key: e
#% description: the EXTERNAL keyword lets you create a table and provide a LOCATION so that Hive does not use a default location for this table. This comes in handy if you already have data generated. When dropping an EXTERNAL table, data in the table is NOT deleted from the file system.
#% guisection: table

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    conn = ConnectionManager()

    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()
    hive.create_csv_table(table=options['table'],
                          field=options['columns'],
                          partition=options['partition'],
                          delimiter=options['delimeter'],
                          stored=options['stored'],
                          serde=options['serde'],
                          outputformat=options['outputformat'],
                          external=flags['e'],
                          recreate=flags['d'],
                          filepath=options['csvpath'],
                          overwrite=flags['o'])


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
