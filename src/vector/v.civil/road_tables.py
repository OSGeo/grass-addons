# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 18:24:22 2014

@author: meskal
"""

# from grass.pygrass.vector.table import Link
import time
import grass.script as grass
import grass.lib.vector as libvect
from grass.pygrass.errors import GrassError
from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector import sql
from grass.pygrass.vector.table import Link
from grass.pygrass.vector import VectorTopo

# from grass.pygrass.vector.geometry import Line


def time_func(funcion_f):
    """Return"""

    def funcion_r(*arg):
        """Return"""
        t_1 = time.clock()
        res = funcion_f(*arg)
        t_2 = time.clock()
        print("%s tarda %0.5f ms" % (funcion_f.__name__, (t_2 - t_1) * 1000.0))
        return res

    return funcion_r


# =============================================
# PLANT
# =============================================

# TABLES_NAMES
TABLES_NAMES = ("first", "_Plan", "_Vert", "_Displ", "_Terr", "_Trans", "_Marks")

# OUT_TABLES_NAMES
OUT_TABLES_NAMES = {
    "__Plant": "__Plant",
    "__Plant_PC": "__Plant_PC",
    "__Plant_C": "__Plant_C",
    "__Vertical": "__Vertical",
    "__Vertical_PC": "__Vertical_PC",
    "__Displaced": "__Displaced",
    "__Displaced_PC": "__Displaced_PC",
    "__Displaced_Areas": "__Displaced_Areas",
    "__Pks": "__Pks",
    "__Trans": "__Trans",
    "__Trans_PC": "__Trans_PC",
    "__Trans_PT": "__Trans_PT",
    "__Slopes": "__Slopes",
    "__Marks": "__Marks",
    "__Slopes_Areas": "__Slopes_Areas",
    "__LongProfile": "__LongProfile",
    "__LProfile_PC": "__LProfile_PC",
    "__LProfile_Axis": "__LProfile_Axis",
    "__LProfile_Ticks": "__LProfile_Ticks",
    "__TransProfiles": "__TransProfiles",
    "__TProfile_PC": "__TProfile_PC",
    "__TProfile_Axis": "__TProfile_Axis",
    "__TProfile_Ticks": "__TProfile_Ticks",
    "__Topo": "__Topo",
    "__Topo_BreakLines": "__Topo_BreakLines",
    "__Topo_Hull": "__Topo_Hull",
}

# TABLES
TABLES = {
    "first": [("cat", "INTEGER PRIMARY KEY"), ("name", "TEXT")],
    "_Plan": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("pk_eje", "DOUBLE PRECISION"),
        ("radio", "DOUBLE PRECISION"),
        ("a_in", "DOUBLE PRECISION"),
        ("a_out", "DOUBLE PRECISION"),
        ("widening", "DOUBLE PRECISION"),
        ("superelev", "TEXT"),
        ("dc_", "DOUBLE PRECISION"),
        ("lr_", "DOUBLE PRECISION"),
    ],
    "_Vert": [
        ("cat3", "INTEGER PRIMARY KEY"),
        ("pk", "DOUBLE PRECISION"),
        ("elev", "DOUBLE PRECISION"),
        ("kv", "DOUBLE PRECISION"),
        ("l", "DOUBLE PRECISION"),
        ("b", "DOUBLE PRECISION"),
    ],
    "_Displ": [
        ("cat4", "INTEGER PRIMARY KEY"),
        ("pk", "DOUBLE PRECISION"),
        ("sec_left", "TEXT"),
        ("sec_right", "TEXT"),
        ("type_left", "TEXT"),
        ("type_right", "TEXT"),
    ],
    "_Terr": [
        ("cat5", "INTEGER PRIMARY KEY"),
        ("pk", "DOUBLE PRECISION"),
        ("cut_left", "DOUBLE PRECISION"),
        ("cut_right", "DOUBLE PRECISION"),
        ("fill_left", "DOUBLE PRECISION"),
        ("fill_right", "DOUBLE PRECISION"),
        ("height", "DOUBLE PRECISION"),
        ("leng", "DOUBLE PRECISION"),
    ],
    "_Trans": [
        ("cat6", "INTEGER PRIMARY KEY"),
        ("pk", "DOUBLE PRECISION"),
        ("dist_left", "DOUBLE PRECISION"),
        ("dist_right", "DOUBLE PRECISION"),
        ("npk", "DOUBLE PRECISION"),
    ],
    "_Marks": [
        ("cat7", "INTEGER PRIMARY KEY"),
        ("pk", "DOUBLE PRECISION"),
        ("dist", "TEXT"),
        ("elev", "TEXT"),
        ("azi", "TEXT"),
        ("name", "TEXT"),
        ("cod", "TEXT"),
    ],
}


OUT_TABLES = {
    # Plant
    "__Plant": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("type", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("param", "TEXT"),
        ("GRASSRGB", "TEXT"),
    ],
    "__Plant_PC": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("param", "TEXT"),
    ],
    "__Plant_C": [("cat3", "INTEGER PRIMARY KEY"), ("param", "TEXT")],
    # Vertical
    "__Vertical": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("type", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("param", "TEXT"),
        ("GRASSRGB", "TEXT"),
    ],
    "__Vertical_PC": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("type", "TEXT"),
        ("param", "TEXT"),
    ],
    # Displaced
    "__Displaced": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("param", "DOUBLE PRECISIO"),
        ("GRASSRGB", "TEXT"),
    ],
    "__Displaced_PC": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("param", "TEXT"),
        ("displ", "TEXT"),
    ],
    "__Displaced_Areas": [("cat", "INTEGER PRIMARY KEY"), ("num", "TEXT")],
    # Trans
    "__Pks": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("GRASSRGB", "TEXT"),
    ],
    "__Trans": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("dist_left", "DOUBLE PRECISION"),
        ("dist_right", "DOUBLE PRECISION"),
        ("GRASSRGB", "TEXT"),
    ],
    "__Trans_PC": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("trans", "TEXT"),
        ("param", "TEXT"),
        ("type", "TEXT"),
    ],
    "__Trans_PT": [
        ("cat3", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("trans", "TEXT"),
        ("param", "TEXT"),
        ("type", "TEXT"),
    ],
    # Taludes
    "__Slopes": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("param", "DOUBLE PRECISION"),
        ("GRASSRGB", "TEXT"),
    ],
    # Marks
    "__Marks": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("azimut", "DOUBLE PRECISION"),
        ("name", "TEXT"),
        ("cod", "TEXT"),
        ("dist", "DOUBLE PRECISION"),
        ("elev", "DOUBLE PRECISION"),
    ],
    # Taludes
    "__Slopes_Areas": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("param", "TEXT"),
        ("GRASSRGB", "TEXT"),
    ],
    # LongProfile
    "__LongProfile": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("type", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("param", "TEXT"),
        ("GRASSRGB", "TEXT"),
    ],
    "__LProfile_PC": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("type", "TEXT"),
        ("param", "TEXT"),
    ],
    "__LProfile_Axis": [
        ("cat3", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("type", "TEXT"),
        ("param", "TEXT"),
    ],
    "__LProfile_Ticks": [("cat4", "INTEGER PRIMARY KEY"), ("param", "TEXT")],
    # TransProfiles
    "__TransProfiles": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "TEXT"),
        ("type", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("param", "TEXT"),
        ("GRASSRGB", "TEXT"),
    ],
    "__TProfile_PC": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("dist", "TEXT"),
        ("elev", "TEXT"),
        ("rel_elev", "TEXT"),
    ],
    "__TProfile_Axis": [
        ("cat3", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("type", "TEXT"),
        ("param", "TEXT"),
    ],
    "__TProfile_Ticks": [("cat4", "INTEGER PRIMARY KEY"), ("param", "TEXT")],
    # Tri
    "__Topo": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("pk", "DOUBLE PRECISION"),
        ("name", "TEXT"),
        ("azi", "DOUBLE PRECISION"),
        ("p_type", "TEXT"),
        ("align", "INTEGER"),
        ("vparam", "DOUBLE PRECISION"),
        ("v_type", "TEXT"),
        ("terr", "DOUBLE PRECISION"),
        ("t_type", "TEXT"),
        ("dist_d", "DOUBLE PRECISION"),
        ("x", "DOUBLE PRECISION"),
        ("y", "DOUBLE PRECISION"),
        ("z", "DOUBLE PRECISION"),
        ("action", "TEXT"),
    ],
    "__Topo_BreakLines": [
        ("cat2", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("long", "DOUBLE PRECISION"),
        ("type", "TEXT"),
        ("param", "DOUBLE PRECISION"),
        ("GRASSRGB", "TEXT"),
    ],
    "__Topo_Hull": [
        ("cat", "INTEGER PRIMARY KEY"),
        ("name", "TEXT"),
        ("long", "DOUBLE PRECISION"),
    ],
}

INIT_VALUES = {
    "first": ["name_road"],
    "_Plan": [0, 0, 0, 0, 0, "", 0, 0],
    "_Vert": [0, 0, 0, 0, 0],
    "_Displ": [0, "", "", "", ""],
    "_Trans": [0, 0, 0, 0],
    "_Marks": [0, "", "", "", "", ""],
    "_Terr": [0, 1, 1, 1, 1, 0, 0],
}


class RoadTable(object):
    """Return"""

    def __init__(self, polygon, polyline, layer, map_name, tab_sufix):
        """Return"""
        self.polygon = polygon
        self.tab_name = map_name
        self.name = tab_sufix
        #        self.tab_sufix2 = tab_sufix2

        self.polyline = polyline
        self.layer = layer
        self.cols_names = None
        self.rows = None

        self._init_table()

    def __getitem__(self, index):
        return dict(zip(self.cols_names, self.rows[index]))

    def __setitem__(self, index, value):
        ind1, name = index
        ind2 = self.cols_names.index(name)
        self.rows[ind1][ind2] = value

    def __delitem__(self, index):
        del self.rows[index]

    def __len__(self):
        return len(self.rows)

    # @time_func
    def _init_table(self):
        """Return"""
        link = self.polygon.dblinks.by_name(self.tab_name)

        if link is None:
            self.polygon.open("rw")
            print("creating table")
            self._create_table()
            self.polygon.close()

            self.polygon.open("rw", self.layer, with_z=True)
            if self.name == "_Plan":
                self._set_default(map_plant=True)
            else:
                self._set_default()
            self.polygon.close()

        self.polygon.open("r")
        link = self.polygon.dblinks.by_name(self.tab_name)
        self.layer = link.layer
        self.cols_names = link.table().columns.names()
        self.polygon.close()

        self._check_columns()

        self.polygon.open("r")
        tabla_sql = "SELECT * FROM {name};".format(name=self.tab_name)
        self.rows = link.table().execute(tabla_sql).fetchall()
        self.rows = [list(row) for row in self.rows]
        self.polygon.close()

    def _create_table(self):
        """Return"""
        link = Link(self.layer, self.tab_name, self.tab_name, "cat" + str(self.layer))
        self.polygon.dblinks.add(link)
        table = link.table()

        tab_sufix = self.name
        if self.name == "":
            tab_sufix = "first"
        TABLES[tab_sufix][0] = ("cat" + str(self.layer), "INTEGER PRIMARY KEY")
        if not table.exist():
            table.create(TABLES[tab_sufix])
            table.conn.commit()

    def _set_default(self, map_plant=False):
        """Return"""
        tab_sufix = self.name
        if self.name == "":
            tab_sufix = "first"
            values = INIT_VALUES[tab_sufix]
            self.polygon.write(self.polyline[0], cat=1, attrs=values)
            self.polygon.table.conn.commit()
            self.polygon._cats = []
            return 0
        values = INIT_VALUES[tab_sufix]
        values[0] = 0
        dist2 = self.polyline[0].distance(self.polyline[1])
        if map_plant:
            values[-1] = dist2

        self.polygon.write(self.polyline[0], cat=1, attrs=values)
        dist = dist2

        ult_i = 1
        for i in range(1, len(self.polyline[:-1])):

            dist2 = self.polyline[i].distance(self.polyline[i + 1])
            if map_plant:
                values[-1] = dist2
                values[0] = dist
                ult_i = i + 1
                self.polygon.write(self.polyline[i], i + 1, values)
            dist += dist2

        if map_plant:
            values[-1] = 0
        values[0] = dist

        self.polygon.write(self.polyline[-1], ult_i + 1, values)
        self.polygon.table.conn.commit()
        self.polygon._cats = []

    def get_column(self, name):
        """Return"""
        index = self.cols_names.index(name)
        return [row[index] for row in self.rows]

    def _check_columns(self):
        """Return"""
        cols_out = []
        tab_sufix = self.name
        if self.name == "":
            tab_sufix = "first"
        for col in TABLES[tab_sufix][1:]:
            if col[0] not in self.cols_names:
                cols_out.append(col)
        if cols_out != []:
            grass.warning("adding columns " + ",".join([p[0] for p in cols_out]))
            self._add_columns(cols_out)

    def _add_columns(self, columns):
        """Return"""
        self.polygon.open("rw")

        table = self.polygon.dblinks.by_name(self.tab_name).table()

        for col in columns:
            table.execute(
                sql.ADD_COL.format(tname=self.tab_name, cname=col[0], ctype=col[1])
            )
        table.conn.commit()
        self.polygon.close()

    # @time_func
    def rewrite_obj(self, obj, attrs):
        """Return"""
        self.polygon.open("rw", self.layer, with_z=True)
        cat = attrs[0]

        if obj.gtype == 1:
            vtype = "points"
        elif obj.gtype == 2:
            vtype = "lines"
        elif obj.gtype == 3:
            vtype = "boundary"
        elif obj.gtype == 4:
            vtype = "centroid"

        line = self.polygon.cat(cat, vtype, self.layer)[0]

        if self.polygon.table is not None and attrs:
            self.polygon.table.update(key=line.cat, values=attrs[1:])
        elif self.polygon.table is None and attrs:
            print(
                "Table for vector {name} does not exist, attributes not"
                " loaded".format(name=self.name)
            )
        # libvect.Vect_cat_set(obj.c_cats, self.layer, line.cat)

        result = libvect.Vect_rewrite_line(
            self.polygon.c_mapinfo, line.id, obj.gtype, obj.c_points, line.c_cats
        )
        if result == -1:
            raise GrassError("Not able to write the vector feature.")

        # return offset into file where the feature starts
        obj.offset = result

        self.polygon.table.conn.commit()
        self.polygon.close()

    def rewrite_new(self, obj, attrs, cat_ind):
        """Return"""
        self.polygon.open("rw", self.layer, with_z=True)

        tabla_sql = (
            "DELETE FROM "
            + self.tab_name
            + " WHERE cat"
            + str(self.layer)
            + "="
            + str(attrs[0])
            + ";"
        )
        self.polygon.table.execute(tabla_sql)

        if isinstance(obj, Point):
            type_obj = "points"
        else:
            type_obj = "lines"

        obj_org = self.polygon.cat(attrs[0], type_obj, self.layer)

        if obj_org:
            obj_org = obj_org[0]
            self.polygon.delete(obj_org.id)

        self.polygon.write(obj, cat_ind, attrs[1:])

        self.polygon.table.conn.commit()
        self.polygon.close()

    def _execute_update(self):
        """Return"""
        self.polygon.open("r")
        tabla = self.polygon.dblinks.by_name(self.tab_name).table()

        for row in self.rows:
            vals = ",".join(
                ["%s='%s'" % (k, v) for k, v in zip(self.cols_names[1:], row[1:])]
            )
            cond = "%s=%s" % (self.cols_names[0], row[0])

            sql1 = "UPDATE {tname} SET {values} WHERE {condition};"
            tabla_sql = sql1.format(tname=self.tab_name, values=vals, condition=cond)
            tabla.execute(tabla_sql)
        tabla.conn.commit()
        self.polygon.close()

    def update_plan_dists(self, plant):
        """Return"""
        num = 0
        for i in range(0, len(plant.straight_curve_lengs[:-1]), 2):
            index = self.cols_names.index("dc_")
            self.rows[num][index] = plant.straight_curve_lengs[i]
            index = self.cols_names.index("lr_")
            self.rows[num][index] = plant.straight_curve_lengs[i + 1]
            num += 1
        self._execute_update()

    #    def write_obj(self, objs, values):
    #        """Return
    #        """
    #        self.polygon.open('rw', self.layer, with_z=True,
    #                          tab_name=self.tab_name, tab_cols=self.cols_names)
    #        for obj, val in (objs, values):
    #            self.polygon.write(obj, val)
    #        self.polygon.table.conn.commit()
    #        self.polygon.close()

    def displ_add_del_col(self, num_col, side, values, add):
        """Return"""
        num_col = int(num_col)
        values = values.split(";")
        if side == "left":
            name_sec = "sec_left"
            type_sec = "type_left"
        elif side == "right":
            name_sec = "sec_right"
            type_sec = "type_right"

        self._displ_check_type_col(name_sec, type_sec)

        ind = self.cols_names.index(name_sec)
        ind2 = self.cols_names.index(type_sec)
        self.rows[0][ind] = self._displ_add_del_sec(
            self[0][name_sec], num_col, values[0], side, add
        )
        self.rows[0][ind2] = self._displ_add_del_sec(
            self[0][type_sec], num_col, "l", side, add
        )

        self.rows[-1][ind] = self._displ_add_del_sec(
            self[-1][name_sec], num_col, values[1], side, add
        )
        self.rows[-1][ind2] = self._displ_add_del_sec(
            self[-1][type_sec], num_col, "l", side, add
        )
        for i in range(1, len(self.rows) - 1):
            self.rows[i][ind] = self._displ_add_del_sec(
                self[i][name_sec], num_col, "-1 0", side, add
            )
            self.rows[i][ind2] = self._displ_add_del_sec(
                self[i][type_sec], num_col, "l", side, add
            )
        self._execute_update()

    def _displ_check_type_col(self, name_sec, type_sec):
        """Return"""
        ind = self.cols_names.index(name_sec)
        ind2 = self.cols_names.index(type_sec)
        if self.rows[0][ind] != "":
            if ";" in self.rows[0][ind]:
                len_secc = len(self.rows[0][ind].split(";"))
            else:
                len_secc = 1
        else:
            return None

        for i in range(len(self.rows)):
            if self.rows[i][ind2] == "":
                type_secc = ""
                for _ in range(len_secc):
                    type_secc += "l;"
                self.rows[i][ind2] = type_secc[:-1]

    def _displ_add_del_sec(self, sec, index, values, side, add):
        """Return"""
        if sec != "":
            if ";" in sec:
                sec_out = sec.split(";")
            else:
                sec_out = [sec]
            if index > len(sec_out):
                index = len(sec_out)
            if side == "left":
                index = len(sec_out) - index
            if add:
                sec_out.insert(index, values)
                return ";".join(sec_out)
            else:
                if index > len(sec_out) - 1:
                    index = len(sec_out) - 1
                del sec_out[index]
                return ";".join(sec_out)
        else:
            if add:
                return values
            else:
                return ""

    def _displ_init_vals(self):
        """Return"""
        values = INIT_VALUES[self.name]
        if self[0]["sec_left"] != "":
            num = "-1 0"
            typ = "l"
            if ";" in self[0]["sec_left"]:
                for _ in range(len(self[0]["sec_left"].split(";")) - 1):
                    num += ";-1 0"
                    typ += ";l"
            INIT_VALUES[self.name][1] = num
            INIT_VALUES[self.name][3] = typ

        if self[0]["sec_right"] != "":
            num = "-1 0"
            typ = "l"
            if ";" in self[0]["sec_right"]:
                for _ in range(len(self[0]["sec_right"].split(";")) - 1):
                    num += ";-1 0"
                    typ += ";l"
            INIT_VALUES[self.name][2] = num
            INIT_VALUES[self.name][4] = typ
        return values

    def add_row(self, list_pks, plant):
        """Return"""
        col_pks = self.get_column("pk")

        list_pks2 = []
        for npk in list_pks:
            if float(npk) not in col_pks:
                list_pks2.append(npk)

        if list_pks2 == []:
            return None

        self.polygon.open("rw", self.layer, with_z=True, tab_name=self.tab_name)
        if self.name == "_Displ":
            self._displ_init_vals()

        for npk in list_pks2:
            INIT_VALUES[self.name][0] = float(npk)
            r_pnt = plant.get_roadpoint(float(npk))
            cat = len(self.rows) + 1
            self.rows.append([cat] + INIT_VALUES[self.name])

            self.polygon.write(r_pnt, cat, INIT_VALUES[self.name])
        self.polygon.table.conn.commit()
        self.polygon.close()

        self.update_table(plant)

    # Rewrite other tables
    def update_table(self, plant=None):
        """Return"""
        self.rows.sort(key=lambda x: float(x[1]))
        self.rows[0][1] = 0
        cats = [row[0] for row in self.rows]

        if plant:
            self.rows[-1][1] = plant.length()  # set real length
            for i, row in enumerate(self.rows):  # sort if new line is inserted
                r_pnt = plant.get_roadpoint(row[1])
                if row[0] > i + 1 and i + 1 not in cats:
                    self.rewrite_new(r_pnt, row, i + 1)
                    del cats[cats.index(row[0])]
                # elif row[0] == i + 1:
                else:
                    row[0] = i + 1
                    self.rewrite_obj(r_pnt, row)
        else:
            self.rows[-1][1] = self.polyline.length()
            self.rewrite_obj(self.polyline[0], self.rows[0])
            self.rewrite_obj(self.polyline[-1], self.rows[-1])

    def update_table_plan(self):
        """Return None
        Polygon to table plant
        """
        self._plan_set_dist_accum()
        poly_dist = [
            self.polyline[i].distance(self.polyline[i + 1])
            for i in range(len(self.polyline) - 1)
        ]

        for i, row in enumerate(self.rows):

            self.rewrite_obj(self.polyline[i], row)

        if len(self.rows) < len(self.polyline):

            self.polygon.open("rw", self.layer, with_z=True)

            for i in range(len(self), len(self.polyline)):
                self.rows.append(INIT_VALUES["_Plan"])
                self.rows[i][0] = poly_dist[-1] + self.rows[i - 1][1]
                self.polygon.write(self.polyline[i], i + 1, self.rows[i])

            self.polygon.table.conn.commit()
            self.polygon.close()

    def _plan_set_dist_accum(self):
        """Return"""
        dist = 0
        for i in range(0, len(self.rows) - 1):
            self.rows[i][1] = dist
            dist += self.polyline[i].distance(self.polyline[i + 1])
        self.rows[-1][1] = dist


# =============================================
# PLANT
# =============================================


class RoadTables(object):
    """Return"""

    def __init__(self, road_name, polygon=None):
        """Return"""
        self.road_name = road_name
        self.polygon = polygon

        self.polygon.open("r")
        self.polyline = self.polygon.cat(1, "lines", 1)[0]
        self.polygon.close()

        self.tables = dict()

        self.gen_tables()

    #        self.update_tables()

    def get_tables_names(self):
        """Return"""
        names = []
        for tab_name in TABLES_NAMES:
            exist = 0
            if tab_name == "first":
                names.insert(0, [self.road_name, "", ""])
                continue
            for tab in [link.table_name for link in self.polygon.dblinks]:

                if tab_name in tab:
                    names.append(tab.split(tab_name))
                    names[-1].insert(1, tab_name)
                    exist = 1
            if not exist:
                names.append([self.road_name, tab_name, ""])
        return names

    # @time_func
    def new_map(self, mapa, layer, tab_sufix, objs, values, tab_subname=""):
        """Return"""
        map_out = VectorTopo(mapa)
        if objs == [] or objs is None:
            return None

        tab_sufix_out = OUT_TABLES_NAMES[tab_sufix]
        tab_name = self.road_name + tab_sufix_out + tab_subname

        columns = OUT_TABLES[tab_sufix]
        if layer == 1:
            map_out.open(
                "w", layer=layer, with_z=True, tab_name=tab_name, tab_cols=columns
            )
        else:
            map_out.open("rw")
            link = Link(layer, tab_name, tab_name, "cat" + str(layer))
            map_out.dblinks.add(link)
            table = link.table()
            if not table.exist():
                table.create(columns)
            table.conn.commit()
            map_out.close()

            map_out.open("rw", layer=layer, with_z=True)
        for i, obj in enumerate(objs):
            map_out.write(obj, i + 1, values[i])
        map_out.table.conn.commit()
        map_out.close()

    # @time_func
    def gen_tables(self):
        """Return None"""
        for i, name in enumerate(self.get_tables_names()):

            namedic = name[1] + name[2]
            if name[1] == "":
                namedic = "first"

            self.tables[namedic] = RoadTable(
                self.polygon, self.polyline, i + 1, name[0] + name[1] + name[2], name[1]
            )

    # @time_func
    def update_tables(self, plant):
        """Return None"""
        for name, tab in self.tables.items():
            if name == "_Plan":
                tab.update_table_plan()
            elif name != "first":
                tab.update_table(plant)

    # @time_func
    #    def update_tables_pnts(self, plant):
    #        """Return None
    #        """
    #        for tab in self.tables.values():
    #            if tab.name not in ['', '_Plan']:
    #                tab.update_table(plant)

    def add_table(self, tab_sufix, tab_subname):
        """Return"""
        if tab_sufix not in ["_Displ", "_Marks"]:
            grass.warning("Only Displ or Marks tables can be used")
            return None
        tab_name = self.road_name + tab_sufix + tab_subname
        n_layer = self.polygon.dblinks.num_dblinks()
        if tab_name in [link.table_name for link in self.polygon.dblinks]:
            grass.warning("table exist")
        else:
            self.tables[tab_sufix + tab_subname] = RoadTable(
                self.polygon, self.polyline, n_layer + 1, tab_name, tab_sufix
            )

    def add_row(self, list_pks, plant, tab_sufix, tab_subname):
        """Return"""
        self.tables[tab_sufix + tab_subname].add_row(list_pks, plant)

    def get_tables_pks(self):
        """Return"""
        list_pks = []
        for tab in self.tables.values():
            if tab.name in ["_Displ", "_Terr"]:
                pks = tab.get_column("pk")[1:-1]
                for npk in pks:
                    if npk not in list_pks:
                        list_pks.append(npk)
        return list_pks

    def create_backup(self, filename):
        """Return"""
        sal = 'echo "'
        sal += "L " + str(len(self.polyline)) + " 1\n"
        for pnt in self.polyline:
            sal += " " + str(pnt.x) + " " + str(pnt.y) + "\n"
        sal += " 1  1\n"

        self.polygon.open("r")
        for table in self.tables.values():
            if table.name != "":
                for row in table.rows:
                    sal += "P  1 1\n"
                    pnt = self.polygon.cat(row[0], "points", table.layer)[0]
                    sal += " " + str(pnt.x) + " " + str(pnt.y) + "\n"
                    sal += " " + str(table.layer) + "    " + str(row[0]) + "\n"
        self.polygon.close()

        sal += '" | v.in.ascii -n input=- output=' + self.road_name
        sal += " format=standard --o \n\n"

        for table in self.tables.values():
            tab_name = table.name
            cat = str(table.layer)
            if tab_name == "":
                tab_name = "first"
                cat = ""

            cols = []
            for key1, val1 in TABLES[tab_name][1:]:
                if "INTEGER" in val1:
                    val1 = "INT"
                if "TEXT" in val1:
                    val1 = "VARCHAR(25)"
                cols.append((key1, val1))

            sal += (
                "v.db.addtable map="
                + self.road_name
                + " table="
                + self.road_name
                + table.name
                + " layer="
                + str(table.layer)
                + " key=cat"
                + cat
                + ' columns="'
                + ",".join(["%s %s" % (key, str(val).lower()) for key, val in cols])
                + '"\n'
            )

        sal += "\n" + 'echo "'
        for table in self.tables.values():
            for row in table.rows:
                vals = ",".join(
                    [
                        "%s='%s'" % (key, val)
                        for key, val in zip(table.cols_names[1:], row[1:])
                    ]
                )
                cond = "%s=%s" % (table.cols_names[0], row[0])
                sal += (
                    "UPDATE "
                    + self.road_name
                    + table.name
                    + " SET "
                    + vals
                    + " WHERE "
                    + cond
                    + ";\n"
                )
        sal += '" | db.execute input=- \n'

        with open(filename, "w") as file:
            file.write(sal)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
