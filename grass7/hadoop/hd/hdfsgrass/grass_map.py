import os
import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.pygrass.modules import Module
from grass.script import parse_key_val
from subprocess import PIPE

class VectorDBInfo:
    """Class providing information about attribute tables
    linked to a vector map"""
    def __init__(self, map):
        self.map = map

        # dictionary of layer number and associated (driver, database, table)
        self.layers = {}
         # dictionary of table and associated columns (type, length, values, ids)
        self.tables = {}

        if not self._CheckDBConnection(): # -> self.layers
            return

        self._DescribeTables() # -> self.tables

    def _CheckDBConnection(self):
        """Check DB connection"""
        nuldev = file(os.devnull, 'w+')
        # if map is not defined (happens with vnet initialization) or it doesn't exist
        try:
            self.layers = grass.vector_db(map=self.map, stderr=nuldev)
        except CalledModuleError:
            return False
        finally:  # always close nuldev
            nuldev.close()

        return bool(len(self.layers.keys()) > 0)

    def _DescribeTables(self):
        """Describe linked tables"""
        for layer in self.layers.keys():
            # determine column names and types
            table = self.layers[layer]["table"]
            columns = {} # {name: {type, length, [values], [ids]}}
            i = 0
            for item in grass.db_describe(table = self.layers[layer]["table"],
                                          driver = self.layers[layer]["driver"],
                                          database = self.layers[layer]["database"])['cols']:
                name, type, length = item
                # FIXME: support more datatypes
                if type.lower() == "integer":
                    ctype = int
                elif type.lower() == "double precision":
                    ctype = float
                else:
                    ctype = str

                columns[name.strip()] = { 'index'  : i,
                                          'type'   : type.lower(),
                                          'ctype'  : ctype,
                                          'length' : int(length),
                                          'values' : [],
                                          'ids'    : []}
                i += 1

            # check for key column
            # v.db.connect -g/p returns always key column name lowercase
            if self.layers[layer]["key"] not in columns.keys():
                for col in columns.keys():
                    if col.lower() == self.layers[layer]["key"]:
                        self.layers[layer]["key"] = col.upper()
                        break

            self.tables[table] = columns

        return True

    def Reset(self):
        """Reset"""
        for layer in self.layers:
            table = self.layers[layer]["table"] # get table desc
            for name in self.tables[table].keys():
                self.tables[table][name]['values'] = []
                self.tables[table][name]['ids']    = []

    def GetName(self):
        """Get vector name"""
        return self.map

    def GetKeyColumn(self, layer):
        """Get key column of given layer

        :param layer: vector layer number
        """
        return str(self.layers[layer]['key'])

    def GetTable(self, layer):
        """Get table name of given layer

        :param layer: vector layer number
        """
        return self.layers[layer]['table']

    def GetDbSettings(self, layer):
        """Get database settins

        :param layer: layer number

        :return: (driver, database)
        """
        return self.layers[layer]['driver'], self.layers[layer]['database']

    def GetTableDesc(self, table):
        """Get table columns

        :param table: table name
        """
        return self.tables[table]


class GrassMap(object):
    def __init__(self,map):
       self.map=map

    def get_topology(self,map):
        vinfo = Module('v.info',
                        self.map,
                        flags='t',
                        quiet=True,
                        stdout_=PIPE)

        features = parse_key_val(vinfo.outputs.stdout)

