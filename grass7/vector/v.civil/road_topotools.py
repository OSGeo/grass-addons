#!/usr/bin/python

"""
Sample Python script to access vector data using GRASS Ctypes
interface
"""

# import os, sys

import grass.lib.gis as GrassGis
import grass.lib.vector as GrassVect
import time
import os
import sys
import math
import grass.script as grass
# from grass.pygrass.gis.region import Region

from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line
# from grass.pygrass.vector.geometry import Boundary
# from grass.pygrass.vector.geometry import GEOOBJ as _GEOOBJ

import road_base as Base


def time_func(funcion_f):
    """Return
    """
    def funcion_r(*arg):
        """Return
        """
        t_1 = time.clock()
        res = funcion_f(*arg)
        t_2 = time.clock()
        print('%s tarda %0.5f ms' % (funcion_f.__name__, (t_2 - t_1) * 1000.0))
        return res
    return funcion_r


#########################################################
class Topo(object):
    """ Return
    """
    def __init__(self, name_map=''):
        """ Return
        """
        self.name_map = name_map

    def uppoints(self):
        """ Return
        """
        name_map = self.name_map + '__Topo'
        topo = VectorTopo(name_map)
        topo.open('r', layer=1)

        pts_org = []
        pts_chg = []
        attrs = []
        for i in range(1, len(topo) + 1):
            act = topo.read(i).attrs['action']
            if act != '':
                cat = topo.read(i).attrs['cat']
                pto_org = topo.cat(cat, 'points', 1)[0]
                pto_chg = Point(pto_org.x, pto_org.y, pto_org.z)
                if topo.read(i).attrs['x'] is not None:
                    pto_chg.x = float(topo.read(i).attrs['x'])
                if topo.read(i).attrs['y'] is not None:
                    pto_chg.y = float(topo.read(i).attrs['y'])
                if topo.read(i).attrs['z'] is not None:
                    pto_chg.z = float(topo.read(i).attrs['z'])

                pts_org.append(pto_org)
                pts_chg.append(pto_chg)
                attrs.append([cat, topo.read(i).attrs['pk'],
                              topo.read(i).attrs['name'],
                              topo.read(i).attrs['azi'],
                              topo.read(i).attrs['p_type'],
                              topo.read(i).attrs['align'],
                              topo.read(i).attrs['vparam'],
                              topo.read(i).attrs['v_type'],
                              topo.read(i).attrs['terr'],
                              topo.read(i).attrs['t_type'],
                              topo.read(i).attrs['dist_d'],
                              pto_chg.x, pto_chg.y, pto_chg.z, ''])
        topo.close()
        if pts_org != []:
            topo.open('rw', 1, with_z=True)
            for i, pto in enumerate(pts_org):
                topo.rewrite(pto, pts_chg[i], attrs[i][1:])
            topo.table.conn.commit()
            topo.close()

    def pts_info(self, npk, road):
        """ Return
        """
        r_pnt = road.plant.get_roadpoint(float(npk))
        road.vert.set_elev(r_pnt)
        road.terr.set_pnt_terr(r_pnt)
        print('Axis point')
        print(r_pnt.get_info())
        r_pnts_d = road.displ.find_cutoff(r_pnt)

        for side in r_pnts_d:
            for pnt in side:
                if pnt is not None:
                    road.terr.set_pnt_terr(pnt)

        r_pnts_t = road.taludes.get_pnts(r_pnt, r_pnts_d) or []
        print('Slope points')
        for pnt in r_pnts_t:
            if pnt is not None:
                print(pnt.get_info())
        print('Displaced points')
        for side in r_pnts_d:
            for pnt in side:
                if pnt is not None:
                    print(pnt.get_info())

    def roundabout(self, radio, radio2, azimut, center):
        """ Return
        """
        center = [float(p) for p in center.split(',')]
        pto_c = Base.RoadPoint(Point(center[0], center[1], 0))
        radio = float(radio)
        radio2 = float(radio2)
        azi = float(azimut)

        pto_1 = pto_c.project(radio2, azi)
        pto_2 = pto_1.project(radio, azi + math.pi / 2)
        pto_3 = pto_2.project(radio2, azi + math.pi)
        pto_4 = pto_3.project(radio, azi + 3 * math.pi / 2)
        pto_5 = pto_4.project(radio2, azi)
        pto_6 = pto_5.project(radio, azi + math.pi / 2)

        sal = ''
        sal += "L   6  1\n"
        for pto in [pto_1, pto_2, pto_3, pto_4, pto_5, pto_6]:
            sal += ' ' + str(pto.x) + ' ' + str(pto.y) + ' ' + \
                   str(pto.z) + '\n'
        sal += "1  1\n"

        grass.write_command('v.in.ascii', flags='nz',
                            output=self.name_map, stdin=sal,
                            input='-', format='standard', quiet=True)
        grass.run_command('v.road', flags='r', name=self.name_map)

        sal = ""
        for i in range(1, 5):
            sal += "UPDATE " + self.name_map + "_Plan SET "
            sal += "radio=" + str(radio)
            sal += " WHERE cat2=" + str(i + 1) + " ;\n"
        grass.write_command('db.execute', stdin=sal, input='-', quiet=True)


#########################################################
class Triang(object):
    """ Return
    """
    def __init__(self, name_map):
        """ Return
        """
        self.name_map = name_map + '__Topo'
        self.ptosmap = self.name_map + '_pts'
        self.breakmap = self.name_map + '_blines'
        self.contornomap = self.name_map + '_Hull'

        self.nametin = self.name_map + '_Tin'
        self.namelines = self.name_map + '_lines'
        self.namecurved = self.name_map + '_Curves'

    def split_maps(self):
        """ Return
        """
        grass.message("Spliting in points and breaklines maps")

        topo = VectorTopo(self.name_map)
        topo.open('r')

        points = []
        lines = []
        for algo in range(1, topo.number_of("points") + 1):
            if isinstance(topo.read(algo), Point):
                points.append(topo.read(algo))
            if isinstance(topo.read(algo), Line):
                lines.append(topo.read(algo))
        topo.close()

        new1 = VectorTopo(self.ptosmap)
        new1.open('w', with_z=True)
        for pnt in points:
            new1.write(pnt)
        new1.close()

        new1 = VectorTopo(self.breakmap)
        new1.open('w', layer=1, with_z=True)
        for line in lines:
            new1.write(line)
        new1.close()

    def get_area_hull(self):
        """ Return
        """
        grass.run_command('v.centroids', input=self.contornomap,
                          output=self.contornomap + '_area',
                          overwrite=True, quiet=True)

    def cut_by_hull(self):
        """ Return
        """
        grass.run_command('v.category', input=self.namecurved,
                          output=self.namecurved + '_cat', option='add',
                          overwrite=True, quiet=True)

        grass.run_command('v.db.addtable', map=self.namecurved + '_cat',
                          columns="x double,y double,z double", quiet=True)

        grass.run_command('v.to.db', map=self.namecurved + '_cat',
                          option='start', columns='x,y,z', units='meters',
                          overwrite=True, quiet=True)

        grass.run_command('v.overlay', ainput=self.namecurved + '_cat',
                          atype='line', binput=self.contornomap + '_area',
                          operator='and', output=self.namecurved,
                          overwrite=True, quiet=True)

#    def tin_to_raster(self):
#        """ Return
#        """
#        grass.run_command('v.tin.to.raster', map=self.nametin,
#                          output=self.name_map+"_TinDem_borrar",
#                          overwrite=True, quiet=True)
#
#        grass.run_command('v.to.rast', input=self.contornomap + '_area',
#                          output=self.contornomap + '_area', use='val',
#                          overwrite=True, quiet=True)
#
#        os.system("r.mapcalc '" + self.name_map + "_TinDem" +
#                  " = if(" + self.contornomap + '_area' + "==1" + ", " +
#                  self.name_map + "_TinDem_borrar" + ", null())' --o --q")
#
#        grass.run_command('r.contour', input=self.name_map + "_TinDem",
#                          output=self.name_map + "_TinDemCurvas",
#                          step=1, overwrite=True, quiet=True)
#
#        grass.run_command('g.remove', flags='f', type='raster',
#                          name=self.name_map + "_TinDem_borrar")
#
#    def nnbathy(self):
#        """ Return
#        """
#        grass.run_command('v.to.rast', input=self.name_map,
#                          output=self.name_map, use='z',
#                          overwrite=True, quiet=True)
#
#        os.system('/mnt/trb/addons/r.surf.nnbathy/r.surf.nnbathy.sh input=' +
#                  self.name_map + ' output=' + self.name_map +
#                  "_NNbathyDem_borrar" + ' alg=l --o --q')
#
#        grass.run_command('v.to.rast', input=self.contornomap + '_area',
#                          output=self.contornomap + '_area', use='val',
#                          overwrite=True, quiet=True)
#
#        os.system("r.mapcalc '" + self.name_map + "_NNbathyDem" +
#                  " = if(" + self.contornomap + '_area' + "==1" + ", " +
#                  self.name_map + "_NNbathyDem_borrar" + ", null())' --o --q")
#
#        grass.run_command('r.contour', input=self.name_map + "_NNbathyDem",
#                          output=self.name_map + "_NNbathyDemCurvas",
#                          step=1, overwrite=True, quiet=True)
#
#        grass.run_command('g.remove', flags='f', type='raster',
#                          name=self.name_map+"_NNbathyDem_borrar")

    def triangle(self):
        """ Return
        """
        grass.message("Triangulating tin")
        cmd = '/mnt/trb/addons/v.triangle/v.triangle.v7 points=' + self.ptosmap
        if self.breakmap != "":
            cmd += ' lines=' + self.breakmap
        cmd += ' tin=' + self.nametin + ' --o --q'
        os.system(cmd)

    def delaunay(self):
        """ Return
        """
        grass.run_command('v.delaunay', input=self.name_map,
                          output=self.nametin,
                          overwrite=True, quiet=True)

    def curved(self):
        """ Return
        """
        mapset = GrassGis.G_find_vector2(self.nametin, "")
        if not mapset:
            sys.exit("Vector map <%s> not found" % self.nametin)

        # define map structure
        map_info = GrassGis.pointer(GrassVect.Map_info())

        # define open level (level 2: topology)
        GrassVect.Vect_set_open_level(2)

        # open existing vector map
        GrassVect.Vect_open_old(map_info, self.nametin, mapset)

        print('Calculating curves')

        allrectas = []
        rectas = self.get_rectas(map_info)

        for nivel in rectas:
            for recta in nivel:
                allrectas.append(recta)

        GrassVect.Vect_close(map_info)

        new = VectorTopo(self.namelines)
        new.open('w', with_z=True)

        for line in allrectas:
            new.write(Line(line))
        new.close()

        grass.run_command('v.build.polylines', input=self.namelines,
                          output=self.namecurved,
                          overwrite=True, quiet=True)

    # @time_func
    def get_tin_maxmin(self, map_info):
        """ Return
        """
        line1 = Line()
        num_areas = GrassVect.Vect_get_num_areas(map_info)
        max_z = 0
        min_z = 100000
        for area_id in range(1, num_areas + 1):

            GrassVect.Vect_get_area_points(map_info, area_id, line1.c_points)

            pto1_z = line1.c_points.contents.z[0]
            pto2_z = line1.c_points.contents.z[1]
            pto3_z = line1.c_points.contents.z[2]

            min_ptos = min(pto1_z, pto2_z, pto3_z)
            max_ptos = max(pto1_z, pto2_z, pto3_z)
            if min_ptos < min_z:
                min_z = min_ptos
            if max_ptos > max_z:
                max_z = max_ptos
        return [int(math.floor(min_z)), int(math.ceil(max_z))]

    # @time_func
    def get_rectas(self, map_info):
        """ Return
        """
        line1 = Line()

        max_min = self.get_tin_maxmin(map_info)
        rectas = [[] for p in range(max_min[0], max_min[1] + 1)]
        ptos = [[] for p in range(max_min[0], max_min[1] + 1)]

        num_areas = GrassVect.Vect_get_num_areas(map_info)
        for area_id in range(1, num_areas + 1):

            GrassVect.Vect_get_area_points(map_info, area_id, line1.c_points)

            pto1_x = line1.c_points.contents.x[0]
            pto1_y = line1.c_points.contents.y[0]
            pto1_z = line1.c_points.contents.z[0]
            pto2_x = line1.c_points.contents.x[1]
            pto2_y = line1.c_points.contents.y[1]
            pto2_z = line1.c_points.contents.z[1]
            pto3_x = line1.c_points.contents.x[2]
            pto3_y = line1.c_points.contents.y[2]
            pto3_z = line1.c_points.contents.z[2]

            for i, z_z in enumerate(range(max_min[0], max_min[1] + 1)):

                if pto1_z < z_z and pto2_z < z_z and pto3_z < z_z:
                    continue
                if pto1_z > z_z and pto2_z > z_z and pto3_z > z_z:
                    continue
                if pto1_z == z_z and pto2_z == z_z and pto3_z == z_z:
                    continue

                pts = [[pto1_x, pto1_y, pto1_z],
                       [pto2_x, pto2_y, pto2_z],
                       [pto3_x, pto3_y, pto3_z]]
                inf = [pto for pto in pts if pto[2] < z_z]
                equal = [pto for pto in pts if pto[2] == z_z]
                sup = [pto for pto in pts if pto[2] > z_z]

                if ((len(inf) == 0 and len(sup) == 2) or
                        (len(inf) == 2 and len(sup) == 0)):
                    continue

                if len(equal) == 2:
                    if equal[0] != equal[1]:
                        if equal not in ptos[i] and equal[::-1] not in ptos[i]:
                            rectas[i].append(equal)
                            ptos[i].append(equal)
                    continue

                if len(inf) <= len(sup):
                    inf.extend(equal)
                else:
                    sup.extend(equal)

                if len(inf) < len(sup):
                    pto_a = inf[0]
                    pto_b = sup[0]
                    pto_c = sup[1]
                else:
                    pto_a = sup[0]
                    pto_b = inf[0]
                    pto_c = inf[1]

                t_1 = (z_z - pto_a[2]) / (pto_b[2] - pto_a[2])
                xx1 = pto_a[0] + t_1 * (pto_b[0] - pto_a[0])
                yy1 = pto_a[1] + t_1 * (pto_b[1] - pto_a[1])
                pto_1 = Point(xx1, yy1, z_z)

                t_2 = (z_z - pto_a[2]) / (pto_c[2] - pto_a[2])
                xx2 = pto_a[0] + t_2 * (pto_c[0] - pto_a[0])
                yy2 = pto_a[1] + t_2 * (pto_c[1] - pto_a[1])
                pto_2 = Point(xx2, yy2, z_z)

                rectas[i].append([pto_1, pto_2])

        return rectas
####################################################
