# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 13:30:33 2013

@author: pietro

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from gettext import lgettext as _
import numpy as np

from grass.script.core import overwrite
from grass.pygrass.vector import VectorTopo, Vector
from grass.pygrass.vector.table import Link, Table
from grass.pygrass.vector.geometry import Area, intersects
from grass.pygrass.vector.basic import Bbox, BoxList
from grass.pygrass.messages import Messenger


COLS = [('cat', 'INTEGER PRIMARY KEY'),
        ('class', 'INTEGER'), ]

UPDATE = "UPDATE {tname} SET class=? WHERE {cat}=?;"


def update_lines(line, alist, cur=None, sql=None):
    """Update lines using only the boundary
    """
    to_up = []
    bbox = Bbox()
    for area in alist:
        bbox = area.bbox(bbox)
        if ((intersects(area.boundary, line)) or
                (area.contain_pnt(line[0], bbox))):
            to_up.append((line.cat, area.cat))
    if (cur is not None) and (sql is not None):
        cur.executemany(sql, to_up)
    return to_up


def update_areas(trn_area, seg_area, ids, cur=None, sql=None):
    """Update the table with the areas that contained/are contained or
    intersect the training areas.
    """
    to_up = []
    bbox = trn_area.bbox()
    for s_id in ids:
        seg_area.id = s_id
        seg_area.read()
        if ((intersects(seg_area.boundary, trn_area.boundary)) or
                (trn_area.contain_pnt(seg_area.boundary[0], bbox)) or
                (seg_area.contain_pnt(trn_area.boundary[0]))):
            to_up.append((trn_area.cat, seg_area.cat))
    if (cur is not None) and (sql is not None):
        cur.executemany(sql, to_up)
    return to_up


def find_lines(table, trn, seg, msgr):
    """Update the lines' table using the boundaries of the training areas"""
    sql = UPDATE.format(tname=table.name, cat=table.key)
    boxlist = BoxList()
    n_bounds = len(trn)
    cur = table.conn.cursor()
    for i, bound in enumerate(trn):
        msgr.percent(i, n_bounds, 1)
        alist = seg.find['by_box'].areas(bound.bbox(), boxlist)
        update_lines(bound, alist, cur, sql)
    table.conn.commit()


def find_area(table, trn_ids, trn_area, seg_area, n_areas, seg, msgr):
    """Update the lines' table using the training areas"""
    cur = table.conn.cursor()
    msgr.message(_("Finding areas..."))
    sql = UPDATE.format(tname=table.name, cat=table.key)
    boxlist = BoxList()
    for i, trn_id in enumerate(trn_ids):
        msgr.percent(i, n_areas, 1)
        trn_area.id = trn_id
        trn_area.read()
        bblist = seg.find['by_box'].areas(trn_area.boundary.bbox(), boxlist,
                                          bboxlist_only=True)
        update_areas(trn_area, seg_area, bblist.ids, cur, sql)
    table.conn.commit()


def make_new_table(vct, msgr, tname, cols=COLS, force=overwrite()):
    """Check/remove/create a new table"""
    create_link = True
    # make a new table
    table = Table(tname, vct.table.conn)
    if table.exist():
        if any([table.name == l.table_name for l in vct.dblinks]):
            create_link = False
        msg = _("Table <%s> already exist and will be removed.")
        msgr.warning(msg % table.name)
        table.drop(force=force)
    table.create(cols)
    # fill the new table with the segment cats
    slct = vct.table.filters.select(vct.table.key)
    cur = vct.table.execute(slct.get_sql())
    table.insert(((cat[0], None) for cat in cur), many=True)
    table.conn.commit()
    return table, create_link


def check_balance(table, trntab, msgr):
    """Checking the balance between different training classes."""
    msg = _('Checking the balance between different training classes.')
    msgr.message(msg)
    chk_balance = ("SELECT class, count(*) as num_of_segments "
                   "FROM {tname} "
                   "GROUP BY class ORDER BY num_of_segments;")
    res = table.execute(chk_balance.format(tname=table.name))
    cl_sql = "SELECT cat, class FROM {tname} ORDER BY cat;"
    clss = dict(trntab.execute(cl_sql.format(tname=trntab.name)))
    for cls, num in res.fetchall():
        clname = clss.get(cls, str(cls))
        msgr.message("    - %s (%d): %d" % (clname if clname else repr(clname),
                                            cls if cls else 0, num))


def extract_training_array(table):
    """Return a numpy array with the class id or nan if not define"""
    cur = table.execute("SELECT class FROM {tname}".format(tname=table.name))
    return np.array([np.isnan if c is None else c[0] for c in cur])


def get_layer_num_name(vect, tlayer):
    layer_num = len(vect.dblinks)+1
    layer_name = vect.name + '_training'
    if '/' in tlayer:
        layer_num, layer_name = tlayer.split('/')
        layer_num = int(layer_num)
    elif tlayer.isdigit():
        layer_num = int(tlayer)
    elif tlayer:
        layer_name = tlayer
    return layer_num, layer_name


def extract_training(vect, tvect, tlayer):
    """Assign a class to all the areas that contained, are contained
    or intersect a training vector"""
    msgr = Messenger()
    with VectorTopo(tvect, mode='r') as trn:
        with VectorTopo(vect, mode='r') as vct:
            layer_num, layer_name = get_layer_num_name(vct, tlayer)
            # instantiate the area objects
            trn_area = Area(c_mapinfo=trn.c_mapinfo)
            seg_area = Area(c_mapinfo=vct.c_mapinfo)
            n_areas = trn.number_of('areas')
            # check/remove/create a new table
            table, create_link = make_new_table(vct, msgr, layer_name)
            # find and save all the segments
            find_area(table, trn.viter('areas', idonly=True),
                      trn_area, seg_area, n_areas, vct, msgr)
            check_balance(table, trn.table, msgr)

    if create_link:
        msgr.message(_("Connect the new table to the vector map..."))
        with Vector(vect, mode='rw') as seg:
            link = Link(layer_num, name=layer_name, table=table.name)
            seg.dblinks.add(link)
            seg.build()
