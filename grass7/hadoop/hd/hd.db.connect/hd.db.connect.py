#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       hd.db.connect
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
#% description: Connection manager for Hive and Hadoop database
#% keyword: database
#% keyword: hdfs
#%end
#%option
#% key: driver
#% type: string
#% required: no
#% description: Type of database driver
#% options: hiveserver2, hdfs, webhdfs, hive_cli
#% guisection: Connection
#%end
#%option
#% key: conn_id
#% type: string
#% required: no
#% description: Identificator of connection(free string)
#% guisection: Connection
#%end
#%option
#% key: host
#% description: host
#% type: string
#% required: no
#% guisection: Connection
#%end
#%option
#% key: port
#% type: integer
#% required: no
#% description: Port of db
#% guisection: Connection
#%end
#%option
#% key: login
#% type: string
#% required: no
#% description: Login
#% guisection: Connection
#%end
#%option
#% key: passwd
#% type: string
#% required: no
#% description: Password
#% guisection: Connection
#%end
#%option
#% key: schema
#% type: string
#% required: no
#% description: schema
#% guisection: Connection
#%end
#%option
#% key: authmechanism
#% type: string
#% required: no
#% options: PLAIN
#% description: Authentification mechanism type
#% guisection: Connection
#%end
#%option
#% key: connectionuri
#% type: string
#% required: no
#% description: connection uri string of database
#% guisection: Connection uri
#%end
#%option
#% key: rmid
#% type: integer
#% required: no
#% description: Remove connection by id
#% guisection: manager
#%end
#%flag
#% key: c
#% description: Print table of connection
#% guisection: manager
#%end
#%flag
#% key: p
#% description: Print active connection
#% guisection: manager
#%end
#%flag
#% key: r
#% description: Remove all connections
#% guisection: manager
#%end
#%flag
#% key: t
#% description: Test connection by conn_type
#% guisection: manager
#%end
#%flag
#% key: a
#% description: Set active connection by conn_id and driver
#% guisection: manager
#%end

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    # add new connection
    conn = ConnectionManager()
    if options['connectionuri']:
        conn.set_connection_uri(options['connectionuri'])
        conn.add_connection()
        conn.test_connection()
        return

    if options['host'] and options['driver'] and options['conn_id']:
        conn.set_connection(conn_type=options['driver'],
                            conn_id=options['conn_id'],
                            host=options['host'],
                            port=options['port'],
                            login=options['login'],
                            password=options['passwd'],
                            schema=options['schema']
                            )
        conn.add_connection()
        conn.test_connection()
        return

    if options['rmid']:
        conn.remove_conn_Id(options['rmid'])
        return
    # print table of connection
    elif flags['c']:
        conn.show_connections()
        return
    # drop table with connections
    elif flags['r']:
        conn.drop_connection_table()
        conn.show_connections()
        return
    # print active connection
    elif flags['p']:
        conn.show_active_connections()
        return
    elif flags['t']:
        if options['driver']:
            conn.test_connection(options['driver'])
        else:
            print('< driver > is not set')
        return
    elif flags['a']:
        if not options['driver'] and options['conn_id']:
            conn.set_active_connection(options['driver'], options['conn_id'])
        else:
            grass.fatal("ERROR parameter < driver > and 'conn_id' must be set")


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
