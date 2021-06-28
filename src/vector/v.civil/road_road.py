# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 11:34:58 2014

@author: meskal
"""

# import math
import time

# import grass.script as grass
from grass.pygrass.vector import VectorTopo

# from grass.pygrass.vector.table import Link

# import road_base as Base
import road_plant as Plant
import road_vertical as Vert
import road_displ as Displ
import road_trans as Trans
import road_terr as Terr
import road_tables as Tables
import road_profiles as Profile
import road_marks as Marks

# import road_topotools as Topotools


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


class Road(object):
    """Instantiate a new road with a polygon map and instantiate. For run
    doctest you must to execute the example backup in the documentation
    >>> import road_road as Road
    >>> road = Road.Road('Circuit')
    >>> road
    Circuit
    """

    def __init__(self, mapa=None):

        self.mapa = mapa.split("@")[0]

        self.polygon = VectorTopo(self.mapa)

        #        super(Road, self).__init__(self.mapa, self.polygon)
        self.rtab = Tables.RoadTables(self.mapa, self.polygon)

        self.plant = None
        self.vert = None
        self.displ = None
        self.trans = None
        self.terr = None
        self.taludes = None
        self.long_prof = None
        self.trans_prof = None
        self.marks = None

    def __str__(self):
        return str(self.mapa)

    def __repr__(self):
        return str(self.mapa)

    # @time_func
    def plant_generate(self, table_to_plant=False, bombeo=0):
        """Set plant."""
        tabla = self.rtab.tables["_Plan"]
        tabla2 = list(tabla)
        print(tabla2)

        if table_to_plant:
            self.plant = Plant.Plant(
                self.rtab.polyline, tabla, table_to_plan=True, bombeo=bombeo
            )
            self.rtab.tables["first"].rewrite_obj(
                self.plant.polygon, self.rtab.tables["first"].rows[0]
            )
        else:
            self.plant = Plant.Plant(
                self.rtab.polyline, tabla, table_to_plan=False, bombeo=bombeo
            )
            tabla.update_plan_dists(self.plant)

    #        self.update_tables_pnts(self.plant)

    def plant_write(self):
        """Write axis road"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Plant"]

        objs, values = self.plant.get_segments_pnts(
            self.plant.roadline, self.vert, line=True
        )
        self.rtab.new_map(map_out, 1, "__Plant", objs, values)
        #        self.vert.set_lines_elev(segs)

        objs, values = self.plant.get_charact_pnts(lines=False)
        self.rtab.new_map(map_out, 2, "__Plant_PC", objs, values)

        objs, values = self.plant.get_curves_centers()
        self.rtab.new_map(map_out, 3, "__Plant_C", objs, values)

    # @time_func
    def elev_generate(self):
        """Return"""
        tabla = self.rtab.tables["_Vert"]
        self.vert = Vert.Vert(self.rtab.polyline, tabla, self.plant)

    def elev_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Vertical"]

        objs, values = self.vert.get_segments_pnts(self.plant.roadline, line=True)
        self.rtab.new_map(map_out, 1, "__Vertical", objs, values)

        objs, values = self.vert.get_charact_pnts()
        self.rtab.new_map(map_out, 2, "__Vertical_PC", objs, values)

    # @time_func
    def displ_generate(self, tab_subname=""):
        """Return"""
        tabla = self.rtab.tables["_Displ" + tab_subname]
        self.displ = Displ.Displaced(self.polygon, tabla, self.plant)

    def displ_write(self, tab_subname=""):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Displaced"] + tab_subname

        objs, values = self.displ.get_lines()
        self.rtab.new_map(map_out, 1, "__Displaced", objs, values, tab_subname)

        objs, values = self.displ.get_charact()
        self.rtab.new_map(map_out, 2, "__Displaced_PC", objs, values, tab_subname)

    def displ_areas_write(self, opts, tab_subname=""):
        """Return"""
        tab_sufix = "__Displaced_Areas"
        map_out = self.mapa + tab_sufix + tab_subname

        objs, values = self.displ.get_areas(opts)
        self.rtab.new_map(map_out, 1, tab_sufix, objs, values, tab_subname)

    # @time_func
    def terr_generate(self, dem_map):
        """Return"""
        self.terr = Terr.Terrain(dem_map)

    # @time_func
    def trans_generate(self):
        """Return"""
        tabla = self.rtab.tables["_Trans"]
        self.trans = Trans.Trans(self.polygon, tabla, self.plant, self.vert, self.terr)

    def trans_write_pks(self, startend, opts):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Pks"]

        objs, values = self.trans.generate_pks(
            startend[0], startend[1], opts[0], opts[1], opts[2], opts[3]
        )
        self.rtab.new_map(map_out, 1, "__Pks", objs, values)

    def trans_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Trans"]

        objs, values = self.trans.get_trans()
        self.rtab.new_map(map_out, 1, "__Trans", objs, values)

        objs, values = self.trans.get_pnts_trans(self.displ)
        self.rtab.new_map(map_out, 2, "__Trans_PC", objs, values)

        objs, values = self.trans.get_pnts_trans_terr(
            self.displ, self.taludes, self.terr
        )
        self.rtab.new_map(map_out, 3, "__Trans_PT", objs, values)

    # @time_func
    def taludes_generate(self):
        """Return"""
        tabla = self.rtab.tables["_Terr"]
        self.taludes = Terr.Taludes(self.polygon, tabla, self.terr)

    def taludes_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Slopes"]

        objs, values = self.taludes.get_lines()
        self.rtab.new_map(map_out, 1, "__Slopes", objs, values)

    def taludes_areas_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Slopes_Areas"]

        objs, values = self.taludes.get_areas(self.displ)
        self.rtab.new_map(map_out, 1, "__Slopes_Areas", objs, values)

    # @time_func
    def long_profile_generate(self, options, scale, offset):
        """Return"""
        self.long_prof = Profile.LongProfile(options, scale, offset)

    def long_profile_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__LongProfile"]

        #        self.terr.set_pnts_terr(puntos)
        self.long_prof.set_maxmin(self.plant.roadline)

        objs, vals = self.long_prof.get_ras_terr(self.plant.roadline, self.vert)
        self.rtab.new_map(map_out, 1, "__LongProfile", objs, vals)

        objs, vals = self.long_prof.charact_pnts(self.vert)
        self.rtab.new_map(map_out, 2, "__LProfile_PC", objs, vals)

        objs, vals = self.long_prof.get_axes(self.plant.roadline)
        self.rtab.new_map(map_out, 3, "__LProfile_Axis", objs, vals)

        objs, vals = self.long_prof.get_axes_marks(self.plant.roadline)
        self.rtab.new_map(map_out, 4, "__LProfile_Ticks", objs, vals)

    # @time_func
    def trans_profiles_generate(self, options1, options2, scale, offset):
        """Return"""
        self.trans_prof = Profile.TransProfiles(options1, options2, scale)

    def trans_profiles_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__TransProfiles"]

        if len(self.trans) == 0:
            return None

        self.trans_prof.set_maxmin(self.trans, self.terr)
        self.trans_prof.set_centers()

        objs, vals = self.trans_prof.get_ras_terr()
        self.rtab.new_map(map_out, 1, "__TransProfiles", objs, vals)

        objs, vals = self.trans_prof.ras_pnts()
        self.rtab.new_map(map_out, 2, "__TProfile_PC", objs, vals)

        objs, vals = self.trans_prof.get_axes()
        self.rtab.new_map(map_out, 3, "__TProfile_Axis", objs, vals)

        objs, vals = self.trans_prof.get_axes_marks()
        self.rtab.new_map(map_out, 4, "__TProfile_Ticks", objs, vals)

    # @time_func
    def marks_generate(self, tab_subname=""):
        """Return"""
        tabla = self.rtab.tables["_Marks" + tab_subname]
        self.marks = Marks.Marks(self.polygon, tabla, self.plant, self.vert)

    def marks_write(self, tab_subname=""):
        """Return"""
        tab_sufix = "__Marks"
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Marks"] + tab_subname

        objs, values = self.marks.get_pnts()
        self.rtab.new_map(map_out, 1, tab_sufix, objs, values, tab_subname)

    def tri_write(self):
        """Return"""
        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Topo"]

        objs, values = self.plant.roadline.get_pnts_attrs()

        for displ in self.displ.displines:
            objs2, values2 = displ.roadline.get_pnts_attrs()
            for i, obj in enumerate(objs2):
                values2[i][0] = obj.acum_pk

            objs.extend(objs2)
            values.extend(values2)

        for r_line in self.taludes.talud_left.roadlines:
            objs2, values2 = r_line.get_pnts_attrs()
            objs.extend(objs2)
            values.extend(values2)

        for r_line in self.taludes.talud_right.roadlines:
            objs2, values2 = r_line.get_pnts_attrs()
            objs.extend(objs2)
            values.extend(values2)

        self.rtab.new_map(map_out, 1, "__Topo", objs, values)

        objs, values = self.plant.roadline.get_line_attrs()

        objs2, values2 = self.displ.get_lines()
        objs.extend(objs2)
        values.extend(values2)

        objs2, values2 = self.taludes.get_lines()
        objs.extend(objs2)
        values.extend(values2)

        self.rtab.new_map(map_out, 2, "__Topo_BreakLines", objs, values)

        map_out = self.mapa + Tables.OUT_TABLES_NAMES["__Topo_Hull"]
        objs, values = self.taludes.get_hull(self.displ)
        self.rtab.new_map(map_out, 1, "__Topo_Hull", objs, values)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
