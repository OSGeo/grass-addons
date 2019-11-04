#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     Definition of the object basin and functions
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

import itertools
import math
# import system libraries
import os

import numpy as np

from grass.pygrass.messages import get_msgr
from grass.pygrass.vector import VectorTopo
from grass.script import core as gcore
from grass.script import mapcalc
from grass.script.utils import set_path
# finally import the module in the library
from libgreen.utils import (dissolve_lines, get_coo, raster2compressM,
                            raster2numpy)

#import pdb



try:
    from scipy import integrate
except ImportError:
    gcore.warning('You should install scipy to use this module: '
                  'pip install scipy')

set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))


def discharge_sum(list_basin, list_ID):
    """
    sum discharge of a list of basins
    :param list_basin: list of
    the object Basin
    :type list_basin: list
    :param list_ID: list of ID to sum the discharge
    :type list_ID: list
    """
    discharge_tot = 0
    for ID in list_ID:
        discharge_tot = discharge_tot + list_basin[ID].discharge_own
    return discharge_tot


def E_hydro(delta, Q):
    """
    compute the energy in kW
    :param Q
    discharge m3/s
    :param delta
    gross head m
    """
    if Q and delta:
            return max((delta * 9.81 * Q), 0)
    else:
        return 0.0


def check_new(b, lista, new):
    """
    add the ID of the upper basins with a recursive
    function in order to add the new ID upper to the added
    ID
    """
#    ID_basin = b.ID_all[indice]
#    for new in lista[ID_basin].up:
#            b.ID_all.add(new)
#    indice += 1
#    if (indice < len(b.ID_all)):
#        return check_new(b, lista, indice)
#    else:
#        return
    if not new:
        return
    else:
        b.ID_all = b.ID_all.union(new)
        for ID in new:
            check_new(b, lista, lista[ID].up)


class Basin(object):

    def __init__(self, ID, h_mean=None, h_closure=0, discharge_own=None,
                 discharge_tot=None, E_own=None, ID_all=None,
                 E_up=None, area=None, length=None, up=None):
        """Instantiate a Basin object.: Define the class Basin in order
        to create a list
        of object basins with own discharge, mean elevation, closure elevation,
        and the ID of the all the up basins
        usefull in order to evaluate the total discharge
        without running r.watershed twice. The aim os to have an object Basin
        and a dictionary of basins with key equal to ID in order to
        manage several operations with the basins.

        :param ID: specify the ID basin
        :type ID:
        :param h_mean: mean elevation of the basin
        :type h_mean: int or float
        :param h_closure: elevation at the closure point of the basin
        :type h_closure: int or float
        :param discharge_own: discharge of the single basin withot the
        share due to the upper basins
        :type discharge_own: int or float
        :param discharge_tot: total discharge coming from upper basins, can be
        computed thanks to ID_all and the method check_ID_up, plus the own
        discharge. It is the total outflow
        :type discharge_tot: int or float
        :param E_own: value of potential power in the basin
        :type E_own: int or float
        :param up: list of ID of the closest basins (maximum 3)
        :type up: list
        :param ID_all: list of ID of all the upper basins that generate
        the total inflow
        :type ID_all: list
        :param E_up: dict with key the ID of the upper basin and value the
        potential power computed as function of the total
        discharge and the difference between h_closure of
        the upper basin and h_closure of the current basin
        :type E_up: dict
        >>> B1=Basin(1,h_mean=20, h_closure=10,discharge_own=5)
        >>> B1.E_own
        0.49050000000000005
        >>> B2=Basin(2,h_mean=15, h_closure=10,discharge_own=7)
        >>> B3=Basin(3,h_mean=7, h_closure=5,discharge_own=10)
        >>> B3.add_E_up(B1.ID)
        >>> B3.E_up[1]=E_hydro(B1.h_closure-B3.h_closure, B1.discharge_own)
        >>> E2 = E_hydro(B2.h_closure-B3.h_closure, B2.discharge_own)
        >>> B3.add_E_up(B2.ID,E2)
        0.34335000000000004
        >>> B3.E_up
        {1: 0.24525000000000002, 2: 0.34335000000000004}
        >>> B3.E_up.keys()[0]
        1
        >>> B3.up = set([B1.ID, B2.ID])
        >>> B3.up
        set([1, 2])
        >>> B3.up.remove(2)
        >>> B3.up
        set([1])
        >>> B3.up.add(4)
        >>> B3.up
        set([1, 4])
        >>> B0 = Basin(ID=0, up=set([3, 1]), discharge_own=2)
        >>> B1 = Basin(ID=1, up=set([2, 6]), discharge_own=9)
        >>> B2 = Basin(ID=2, discharge_own=3)
        >>> B3 = Basin(ID=3, up=set([4, 5]), discharge_own=4)
        >>> B4 = Basin(ID=4, discharge_own=3)
        >>> B5 = Basin(ID=5, discharge_own=2)
        >>> B6 = Basin(ID=6, up=set([7, 8]), discharge_own=6)
        >>> B7 = Basin(ID=7, discharge_own=1)
        >>> B8 = Basin(ID=8, discharge_own=6)
        >>> B_tot = {0: B0, 1: B1,2: B2,3: B3,4: B4,5: B5,6: B6}
        >>> B_tot.update({7: B7, 8: B8})
        >>> B0.check_ID_up(B_tot)
        >>> set([3, 1, 4, 5, 2, 6, 7, 8]).difference(B_tot[0].ID_all)
        set([])
        >>> B5.check_ID_up(B_tot)
        >>> B3.check_ID_up(B_tot)
        >>> B3.ID_all
        set([4, 5])
        >>> discharge_sum(B_tot,B_tot[0].ID_all)
        34
        >>> temp=discharge_sum(B_tot,B_tot[0].ID_all)+B_tot[0].discharge_own
        >>> B_tot[0].discharge_tot=temp
        >>> B_tot[0].discharge_tot
        36

        @author: GGaregnani
        """
        self.ID = ID
        self.h_mean = h_mean
        self.h_closure = h_closure
        self.discharge_own = discharge_own
        self.discharge_tot = discharge_tot
        self.area = area
        self.length = length

        if ((E_own is None) and (h_mean is not None) and
           (h_closure is not None)):

            delta = (self.h_mean-self.h_closure)
            self.E_own = E_hydro(delta, self.discharge_own)
        else:
            self.E_own = E_own

        if up is None:
            self.up = set()
        elif isinstance(up, set):
            self.up = up
        else:
            raise TypeError("ID_all must be a set")

        if ID_all is None:
            self.ID_all = up
        elif isinstance(ID_all, set):
            self.ID_all = ID_all
        else:
            raise TypeError("ID_all must be a set")

        if E_up is None:
            self.E_up = {}
        elif isinstance(E_up, dict):
            self.E_up = E_up
        else:
            raise TypeError("E_up must be a dict")

#    # provo ad assegnare un magic method in modo che ID_up
#    # sia sempre un set
#    def _get_up(self):
#        return self.up
#
#    def _set_up(self, up):
#        if isinstance(up, set):
#            self.up = up
#        else:
#            raise TypeError("up must be a set")
#
#    up = property(fget=_get_up, fset=_set_up)

    def _get_E_up(self):
        return self._E_up

    def _set_E_up(self, E_up):
        if isinstance(E_up, dict):
            self._E_up = E_up
        else:
            raise TypeError("E_up must be a dict")

    E_up = property(fget=_get_E_up, fset=_set_E_up)

    def add_E_up(self, ID, E=None):
        self.E_up[ID] = E
        return self.E_up[ID]

    def check_ID_up(self, lista):
        """
        :param lista: dictionary of all the basins belong to the study area
                      with key the ID of the basin
        :type h_mean: dictionary of object Basin, key = ID basin, value =
                      object Basin
        """
        self.ID_all = self.up
        #self.ID_all.union(set([99]))
        # indice = 0
        if not self.ID_all:
            return
        else:
            for ID in self.up:
                new = lista[ID].up
                check_new(self, lista, new)

    def E_spec(self):
        """
        compute the specific energy for length unit of the basin
        TOFIX
        """
        #pdb.set_trace()
        E_spec = self.E_own/self.area  # kW/km2
        if self.up:
            for i in self.E_up:
                E_spec = E_spec + self.E_up[i]/(self.length/1000.0)
        return E_spec


class Station(object):

    def __init__(self, ID, ID_bas=None, days=None, discharge=None,
                 area=None, coord=None):
        """Instantiate a Basin object.: Define the class Station in order
        to create a list
        of object station with duration curve and point coordinates.

        :param ID: specify the ID of the station
        :type ID: string or int
        :param ID_bas: ID of the basins
        :type h_mean: string or int
        :param days: days of the duration curve [days]
        :type h_closure: int
        :param discharge: discharge realted to days [m3/s]
        :type discharge_own: float
        :param coord: coordinate of the station point
        :type discharge_tot: tuple
        >>> B0 = Station(ID=1, area=100, days=[1, 10, 365],
        ... discharge=[15, 4, 1])
        >>> B0.mean()
        2.6657534246575341

        @author: GGaregnani
        """
        self.ID = ID
        self.ID_bas = ID_bas
        self.days = days
        self.discharge = discharge
        self.coord = coord

    def mean(self):
        """Return the mean value of discharge in the duration curve
        """
        Q = integrate.trapz(self.discharge, self.days)/365
        return Q


def write_results2newvec(stream, E, basins_tot, inputs):
    """
    Create the stream vector and
    write the basins object in a vector with the same cat value
    of the ID basin
    """
    pid = os.getpid()
    tmp_thin = "tmprgreen_%i_thin" % pid
    tmp_clean = "tmprgreen_%i_clean" % pid
    gcore.run_command("r.thin", input=stream, output=tmp_thin)
    gcore.run_command("r.to.vect", input=tmp_thin,
                      flags='v',
                      output=tmp_clean, type="line")
    gcore.run_command("v.edit", map=tmp_clean, tool='delete', cats='0')
    #pdb.set_trace()
    gcore.run_command('v.build', map=tmp_clean)
    dissolve_lines(tmp_clean, E)
    # TODO: dissolve the areas with the same cat
    # adding columns
    gcore.run_command("v.db.addcolumn", map=E,
                      columns=
                      "Qown double precision,"
                      "Qtot double precision, Hmean double precision,"
                      "H0 double precision, Eown_kW double precision,"
                      "IDup1 int, Eup1_kW double precision,"
                      "IDup2 int, Eup2_kW double precision,"
                      "IDup3 int, Eup3_kW double precision,"
                      "Etot_kW double precision")
    gcore.run_command("db.dropcolumn", flags="f",
                      table=E, column="label")
    # Open database connection
    vec = VectorTopo(E)
    vec.open("rw")
    link = vec.dblinks[0]
    conn = link.connection()
    # prepare a cursor object using cursor() method
    cursor = conn.cursor()
    # I modify with specific power (kW/km) see
    # 4._Julio_Alterach_-_Evaluation_of_the_residual_potential_
    # hydropower_production_in_Italy
    # compute the lenght of the river in a basin
    #import ipdb; ipdb.set_trace()
    for ID in inputs:
        length = 0
        for l in vec.cat(ID, 'lines'):
            length += l.length()
        basins_tot[ID].length = length
        db = [basins_tot[ID].discharge_own,
              basins_tot[ID].discharge_tot,
              basins_tot[ID].h_mean,
              basins_tot[ID].h_closure,
              basins_tot[ID].E_own]
        if len(basins_tot[ID].E_up) == 0:
            db = db + [0, 0.0, 0, 0.0, 0, 0.0,
                       basins_tot[ID].E_own]
        elif len(basins_tot[ID].E_up) == 1:
            db = (db + [list(basins_tot[ID].E_up.keys())[0],
                  list(basins_tot[ID].E_up.values())[0],
                  0, 0.0, 0, 0.0, basins_tot[ID].E_own
                  + sum(basins_tot[ID].E_up.values())])
        elif len(basins_tot[ID].E_up) == 2:
            db = (db + [list(basins_tot[ID].E_up.keys())[0],
                  list(basins_tot[ID].E_up.values())[0],
                  list(basins_tot[ID].E_up.keys())[1],
                  list(basins_tot[ID].E_up.values())[1],
                  0, 0.0, basins_tot[ID].E_own
                  + sum(basins_tot[ID].E_up.values())])
        elif len(basins_tot[ID].E_up) == 3:
            #pdb.set_trace()
            db = (db + [list(basins_tot[ID].E_up.keys())[0],
                  list(basins_tot[ID].E_up.values())[0],
                  list(basins_tot[ID].E_up.keys())[1],
                  list(basins_tot[ID].E_up.values())[1],
                  list(basins_tot[ID].E_up.keys())[2],
                  list(basins_tot[ID].E_up.values())[2],
                  basins_tot[ID].E_own + sum(basins_tot[ID].E_up.values())])
        else:
            db = db + [0, 0.0, 0, 0.0, 0, 0.0, basins_tot[ID].E_own]
        db = [float(d) for d in db]
        # FIXME: numpy.float is not accepted
        # TODO: change values, give only key and vals without key
        vec.table.update(basins_tot[ID].ID, db, cursor)

    # disconnect from server
    conn.commit()
    conn.close()
    vec.close()


def add_results2shp(basins, rivers, basins_tot, E, inputs):
    """
    Add the attribute of the object basins to
    a vector with the category equal to the ID of the basin
    """
    gcore.run_command("r.to.vect", input=basins,
                      flags='v',
                      output='basins', type="area")
    gcore.run_command('v.overlay', overwrite=True,
                      ainput=rivers, binput=basins, operator='and',
                      output=E)
    gcore.run_command("v.db.addcolumn", map=E,
                      columns="E_spec double precision")
    for ID in inputs:
        #pdb.set_trace()
        E_spec = str(basins_tot[ID].E_spec())
        cond = 'b_cat=%i' % (ID)
        gcore.run_command('v.db.update', map=E,
                          layer=1, column='E_spec',
                          value=E_spec, where=cond)


def init_basins(basins):
    """
    Create a dictionary of Basin objects with the keys equal
    to the ID of each basins
    """
    # I use r.stats because of the case with MASK
    info = gcore.parse_command('r.stats', flags='n', input=basins)
    inputs = list(map(int, info.keys()))
    basins_tot = {}

    for count in inputs:
        basins_tot[count] = Basin(ID=count)  # discharge_own=Q_basin)
    return basins_tot, inputs


def check_compute_drain_stream(drain, stream, dtm, threshold=100000):
    """
    Compute the stream and drain map with r.watersheld
    """
    msgr = get_msgr()
    if (not(drain) or not(stream)):
        drain = 'drainage'
        stream = 'stream'
        gcore.run_command('r.watershed',
                          elevation=dtm,
                          threshold=threshold,
                          drainage=drain,
                          stream=stream)
    else:
        info1 = gcore.parse_command('r.info', flags='e', map=drain)
        info2 = gcore.parse_command('r.info', flags='e', map=stream)
        #pdb.set_trace()
        in1 = '\"%s\"' % (dtm)
        in2 = '\"%s\"' % (dtm)
        if ((in1 != info1['source1'] or (info1['description']
             != '\"generated by r.watershed\"'))):
            warn = ("%s map not generated "
                    "by r.watershed starting from %s") % (drain, dtm)
            msgr.warning(warn)
        if ((in2 != info2['source1'] or (info2['description']
             != '\"generated by r.watershed\"'))):
            warn = ("%s map not generated "
                    "by r.watershed starting from %s") % (stream, dtm)
            msgr.warning(warn)
    return drain, stream


def check_compute_basin_stream(basins, stream, dtm, threshold):
    """
    Compute the stream and basin map with r.watersheld
    """
    msgr = get_msgr()
    if (not(basins) or not(stream)):
        pid = os.getpid()
        basins = "tmprgreen_%i_basins" % pid
        stream = "tmprgreen_%i_stream" % pid
        gcore.run_command('r.watershed',
                          elevation=dtm,
                          threshold=threshold,
                          basin=basins,
                          stream=stream)
    else:
        info1 = gcore.parse_command('r.info', flags='e', map=basins)
        info2 = gcore.parse_command('r.info', flags='e', map=stream)
        #pdb.set_trace()
        in1 = '\"%s\"' % (dtm)
        if ((in1 != info1['source1'] or (info1['description']
             != '\"generated by r.watershed\"'))):
            warn = ("%s map not generated "
                    "by r.watershed starting from %s") % (basins, dtm)
            msgr.warning(warn)
        if ((in1 != info2['source1'] or (info2['description']
             != '\"generated by r.watershed\"'))):
            warn = ("%s map not generated "
                    "by r.watershed starting from %s") % (stream, dtm)
            msgr.warning(warn)
    return basins, stream


def build_network(stream, dtm, basins_tot):
    """
    Build the network of streams with the ID of all the basins
    in order to know the dependencies among basins
    """
    pid = os.getpid()
    tmp_neighbors = "tmprgreen_%i_neighbors" % pid
    tmp_closure = "tmprgreen_%i_closure" % pid
    tmp_down = "tmprgreen_%i_down" % pid

    river = raster2numpy(stream)
    river_comp = raster2compressM(stream).tocoo()
    gcore.run_command('r.neighbors', input=stream,
                      output=tmp_neighbors, method="minimum", size='5',
                      quantile='0.5')

    formula = '%s = %s-%s' % (tmp_closure, tmp_neighbors, stream)
    mapcalc(formula)
    # del the map down, it should be not necessary
    gcore.run_command('r.stats.zonal',
                      base=stream,
                      cover=tmp_closure,
                      output=tmp_down,
                      method='min')
    #pdb.set_trace()
    dtm_n = raster2numpy(dtm)
    clos = raster2numpy(tmp_closure)
    ID_down = raster2numpy(tmp_down)
    #pdb.set_trace()
    for i, j, v in zip(river_comp.row,
                       river_comp.col, river_comp.data):
        up = clos[i][j]
        if up < 0:
            ID = river[i, j]
            basins_tot[(ID+int(ID_down[i, j]))].up.add(ID)
            basins_tot[ID].h_closure = dtm_n[i, j]


def area_of_basins(basins, count, dtm):
    """
    By knowing the basin map compute the area of a given basin ID=count
    """
    #TODO: check the similar function in r.green.discharge
    command = 'area_stat=if(%s == %i, %s, null())' % ((basins, count, dtm))
    mapcalc(command, overwrite=True)
    return area_of_watershed('area_stat')


def area_of_watershed(watershed):
    info = gcore.parse_command('r.report', map=watershed, flags='hn',
                               units='k')
    temp = 0
    for somestring in info.keys():
        if ('TOTAL') in somestring:
            temp = float(somestring.split('|')[-2])
    return temp


def fill_energyown(bas):
    """
    Fill basins dictionary with discharge and compute the power
    """

    delta = bas.h_mean - bas.h_closure
    #TODO: modify power with potential
    bas.E_own = (E_hydro(delta, bas.discharge_own))
    #pdb.set_trace()


def fill_discharge_tot(bas, discharge_n, stream_n):
    """
    Fill the total discharge for the basin b by knowing
    the relation among basins
    thank to the ID_all attribute in the object Basin
    """
    msgr = get_msgr()
    warn = ("%i") % bas.ID
    ttt = discharge_n[stream_n == bas.ID]
    #import ipdb; ipdb.set_trace()
    # bas.discharge_tot = 0.0
    ttt.sort()
    ttt = ttt[~np.isnan(ttt)]
    #FIXME: take the second bgger value to avoid to take the value of
    # another catchment, it is not so elegant
    # the low value is the upper part of the basin and the greater
    # the closure point
    if len(ttt) > 1 and not(math.isnan(ttt[-2])):
        bas.discharge_tot = float(ttt[-2])
    else:
        bas.discharge_tot = 0.0
        warn = ("No value for the river ID %i, discharge set to 0") % bas.ID
        msgr.warning(warn)


def fill_discharge_own(basins_tot, b):
    """
    Fill the discharge_own with the run-off of the basin
    """
    basins_tot[b].discharge_own = basins_tot[b].discharge_tot
    #import pdb; pdb.set_trace()
    for idd in basins_tot[b].up:
        basins_tot[b].discharge_own = (basins_tot[b].discharge_own -
                                       basins_tot[idd].discharge_tot)


def fill_Eup(basins_tot, b):
    """
    Fill the energy coming from discharge in the upper basins
    """
    for ID in basins_tot[b].up:
        deltaH = basins_tot[ID].h_closure - basins_tot[b].h_closure
        power = E_hydro(deltaH, basins_tot[ID].discharge_tot)
        # if area > 1km2 I use the up-up basin
        #TODO: change the up basins for the energy, something
        # similar to an optimization problem
        if basins_tot[ID].area > 1:
            basins_tot[b].add_E_up(ID, power)
        else:
            if basins_tot[ID].up:
                for id_up in basins_tot[ID].up:
                    deltaH = (basins_tot[id_up].h_closure -
                              basins_tot[b].h_closure)
                    power = E_hydro(deltaH, basins_tot[id_up].discharge_tot)
                    basins_tot[b].add_E_up(id_up, power)
            else:
                basins_tot[b].add_E_up(ID, power)


def fill_basins(inputs, basins_tot, basins, dtm, discharge, stream):
    """
    Fill the dictionary with the basins attribute
    """
    pid = os.getpid()
    tmp_dtm_mean = "tmprgreen_%i_dtm_mean" % pid
    gcore.run_command('r.stats.zonal',
                      base=basins,
                      cover=dtm, flags='r',
                      output=tmp_dtm_mean,
                      method='average')
    info_h = gcore.parse_command('r.category', map=tmp_dtm_mean, separator='=')
    #pdb.set_trace()
    for count in inputs:
        if info_h[str(count)] != '':
            # area = area_of_basins(basins, count, dtm)
            # basins_tot[count].area = float(area)
            basins_tot[count].h_mean = float(info_h[str(count)])
            fill_discharge_tot(basins_tot[count], discharge, stream)

    for b in inputs:
        fill_discharge_own(basins_tot, b)
        fill_energyown(basins_tot[b])

    for b in inputs:
        fill_Eup(basins_tot, b)


def compute_river_discharge(drain, stream, string, **kwargs):
    """
    Given a stream network and drainage map
    it computes a rester with the
    the given resolution
    with the area in km2 of the upper basin
    for each pixel (bas_area)
    and a statistic  on the bas_area for another series of raster
    if q_spec string=sum
    if piedmont case kwargs-> a=a, dtm=dtm and string=mean
    """
    msgr = get_msgr()
    info = gcore.parse_command('r.info', flags='g', map=stream)
    raster_out = {}
    for name, value in kwargs.items():
        raster_out[name] = raster2numpy(stream)

    bas_area = raster2numpy(stream)
    river_comp = raster2compressM(stream).tocoo()
    count = 0
    for i, j in zip(river_comp.row, river_comp.col):
        count = count+1
        msgr.message("\n %i \n" % count)
        p_x, p_y = get_coo(stream, i, j)
        #pdb.set_trace()
        coo = '%f, %f' % (p_x, p_y)
        gcore.run_command('r.water.outlet', overwrite=True, input=drain,
                          output='area_temp',
                          coordinates=coo)
        for name, value in kwargs.items():
            formula = 'temp = if(not(area_temp),0, %s)' % (value)
            #pdb.set_trace()
            mapcalc(formula, overwrite=True)
            #pdb.set_trace()
            info = gcore.parse_command('r.univar', map='temp', flags='g')
            #pdb.set_trace()
            raster_out[name][i][j] = float(info[string])
        bas_area[i][j] = area_of_watershed('area_temp')
        #pdb.set_trace()
    return raster_out, bas_area


def dtm_corr(dtm, river, dtm_corr, lake=None):
    """ Compute a new DTM by applying a corrective factor
    close to the river network. Output of r.green.watershed
    will be coherent with the river network
    """
    pid = os.getpid()
    msgr = get_msgr()
    info = gcore.parse_command('g.region', flags='pgm')

    if lake:
        tmp_network = "tmprgreen_%i_network" % pid
        inputs = '%s,%s' % (lake, river)
        gcore.run_command('v.patch',
                          input=inputs,
                          output=tmp_network)
        river = tmp_network

    msgr.warning("The DTM will be temporarily modified")
    distance = [float(info['nsres']), float(info['nsres'])*1.5,
                float(info['nsres'])*3]
    pat = "tmprgreen_%i_" % pid
    for i, val in enumerate(distance):

        output = '%sbuff_%i' % (pat, i)
        gcore.run_command('v.buffer',
                          input=river,
                          output=output,
                          distance=val)
        gcore.run_command('v.to.rast',
                          input=output,
                          output=output,
                          use='val',
                          value=val,
                          overwrite=True)
        command = ('%s_c = if(isnull(%s),0,%s)') % (output, output,
                                                    output)
        mapcalc(command, overwrite=True)

    command = (('%s = if(%s,%s-%sbuff_0_c-%sbuff_1_c-%sbuff_2_c)')
               % (dtm_corr, dtm, dtm, pat, pat, pat))
    mapcalc(command, overwrite=True)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
