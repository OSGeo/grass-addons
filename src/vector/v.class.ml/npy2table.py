# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 17:00:13 2013

@author: pietro
"""
from __future__ import print_function, division

import pickle
import numpy as np
from grass.pygrass.vector import Vector
from grass.pygrass.vector.table import Link, Table

COLS = [
    ("cat", "INTEGER PRIMARY KEY"),
    ("class", "INTEGER"),
    ("color", "VARCHAR(11)"),
]


def export2sqlite(table, cats, clsses, training=None):
    cur = table.conn.cursor()
    if training:
        colors = np.zeros(clsses.shape, dtype=np.dtype(np.str))
        cur = training.execute("SELECT cat, color FROM %s;" % training.name, cursor=cur)
        trndict = dict([c for c in cur.fetchall()])
        for key in trndict:
            colors[clsses == key] = trndict[key]
    print("Insert data")
    table.insert(
        zip(cats, clsses, colors) if training else zip(cats, clsses),
        cursor=cur,
        many=True,
    )
    cur.close()
    table.conn.commit()


def export2onesqlite(table, cats, update="", *clsses):
    cur = table.conn.cursor()
    if update:
        print("Update table inserting classification data")
        print(update)
        clsses.append(cats)
        table.execute(update, many=True, values=zip(*clsses))
    else:
        print("Insert data")
        table.insert(zip(cats, *clsses), cursor=cur, many=True)
        cur.close()
    table.conn.commit()


def create_tab(vect, tab_name, cats, clsses, cols, training=None):
    cur = vect.table.conn.cursor()
    table = Table(tab_name, vect.table.conn)
    add_link = True
    if table.exist():
        print("Table <%s> already exist, will be removed." % tab_name)
        table.drop(cursor=cur)
        add_link = False
    print("Ceating a new table <%s>." % tab_name)
    table.create(cols, cursor=cur)
    export2sqlite(
        table, cats, clsses, Table(training, vect.table.conn) if training else None
    )
    cur.close()
    if add_link:
        vect.dblinks.add(
            Link(layer=len(vect.dblinks) + 1, name=tab_name, table=tab_name)
        )


def export_results(
    vect_name,
    results,
    cats,
    rlayer,
    training=None,
    cols=None,
    overwrite=False,
    append=False,
    pkl=None,
):
    if pkl:
        res = open(pkl, "w")
        pickle.dump(results, res)
        res.close()

    # check if the link already exist
    with Vector(vect_name, mode="r") as vct:
        link = vct.dblinks.by_name(rlayer)
        mode = "r" if link else "w"

    print("Opening vector <%s>" % vect_name)
    with Vector(vect_name, mode=mode) as vect:
        if cols:
            cols.insert(0, COLS[0])
            tab = link.table() if link else Table(rlayer, vect.table.conn)
            if tab.exist() and append:
                columns_to_up = []
                # add the column to the table
                for cname, ctype in cols:
                    columns_to_up.append("%s=?" % cname)
                    if cname not in tab.columns:
                        tab.columns.add(cname, ctype)
                upsql = "UPDATE %s SET %s WHERE %s=%s"
                up = upsql % (tab.name, ",".join(columns_to_up), tab.key, "?")
            else:
                if tab.exist():
                    print("Table <%s> already exist, will be removed." % tab.name)
                    tab.drop(force=True)
                print("Ceating a new table <%s>." % rlayer)
                tab.create(cols)
                up = ""

            export2onesqlite(
                tab,
                cats.astype(int),
                up,
                *[cls["predict"].astype(int) for cls in results],
            )
            if mode == "w":
                nlyr = len(vect.dblinks) + 1
                link = Link(nlyr, tab.name, tab.name)
                vect.dblinks.add(link)
                vect.build()
        else:
            for cls in results:
                create_tab(
                    vect,
                    cls["name"],
                    cats,
                    cls["predict"],
                    training,
                    COLS if training else COLS[:2],
                )


# create_tab(VECT, B1[:-4], cats, b1, TRAINING, COLS)
