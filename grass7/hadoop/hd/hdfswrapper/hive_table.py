import logging
from utils import string2dict, find_ST_fnc
import sys
import os

class HiveBaseTable(object):
    """
    Base class for creating Hive tables - table factory
    """
    def __init__(self,
                name,
                col,
                temporary = False,
                external = False,
                exists = True,
                db_name = None,
                comment = None,
                partitioned= None,
                clustered = None,
                sorted = None,
                skewed = None,
                row_format=None,
                stored=None,
                outputformat=None,
                location = None,
                tbl_properties = None):

        self.db_name = db_name
        self.name = name
        self.temporary = temporary
        self.external = external
        self.exists = exists
        self.col = col
        self.comment = comment
        self.partitioned= partitioned
        self.clustered = clustered
        self.sorted = sorted
        self.skewed = skewed
        self.row_format=row_format
        self.stored=stored
        self.outputformat=outputformat
        self.location = location
        self.tbl_properties = tbl_properties

        self.hql = ''

    def get_table(self):
        self._base()
        self._col()
        self._partitioned()
        self._cluster()
        self._row_format()
        self._stored()
        self._location()
        self._tbl_prop()

        return self.hql

    def _base(self):
        self.hql = 'CREATE'
        if self.temporary:
            self.hql+= ' TEMPORARY'
        if self.external:
            self.hql+= ' EXTERNAL'
        self.hql += ' TABLE'
        if self.exists:
            self.hql+= ' IF NOT EXISTS'
        if self.db_name:
            self.hql+= " %s.%s"%(self.db_name,self.name)
        else:
            self.hql+= " %s"%self.name

    def _col(self):

        self.hql+=' (%s)'%self.col

    def _partitioned(self):
        if self.partitioned:
            self.hql+=' PARTITIONED BY (%s)'%self.partitioned

    def _cluster(self):
        if self.clustered:
            self.hql+=' CLUSTERED BY (%s)'%self.clustered

    #def _skewed(self):
    #    if self.skewed:
    #        self.hql+=' SKEWED BY (%s)'%self.skewed
    def _row_format(self):
        if self.row_format:
            self.hql+=" ROW FORMAT '%s'"%self.row_format

    def _stored(self):
        #hint
        # STORED AS INPUTFORMAT 'com.esri.json.hadoop.UnenclosedJsonInputFormat'
        # OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat';
        if self.stored:
            self.hql+=" STORED AS INPUTFORMAT %s"%self.stored
            if self.outputformat:
                self.hql+=" OUTPUTFORMAT '%s'"%self.outputformat
        else:
            self.hql+=" STORED AS TEXTFILE"

    def _location(self):
        if self.location:
            self.hql+=' LOCATION %s'%self.location

    def _tbl_prop(self):
        if self.tbl_properties:
            self.hql+=' TBLPROPERTIES (%s)'%self.tbl_properties


class HiveJsonTable(HiveBaseTable):
    """
    Table factory for Json tables
    """
    def __init__(self,
                name,
                col ,
                db_name = None,
                temporary = False,
                external = False,
                exists = True,
                comment = None,
                partitioned= None,
                clustered = None,
                sorted = None,
                skewed = None,
                row_format=None,
                stored=None,
                location = None,
                outputformat=None,
                tbl_properties = None):

        super(HiveJsonTable,self).__init__(name=name,
                                      col=col,
                                      db_name=db_name,
                                      temporary=temporary,
                                      external=external,
                                      exists=exists,
                                      comment=comment,
                                      partitioned=partitioned,
                                      clustered=clustered,
                                      stored=sorted,
                                      skewed=skewed,
                                      row_format=row_format,
                                      location=location,
                                      sorted=sorted,
                                      outputformat=outputformat,

                                      tbl_properties=tbl_properties)
        self.outputformat=outputformat

    def get_table(self):
        self._base()
        self._col()
        self._partitioned()
        self._row_format()
        self._stored()
        self._location()

        return self.hql

    def _row_format(self):
        if self.row_format:
            self.hql+=" ROW FORMAT SERDE '%s'"%self.row_format

class HiveCsvTable(HiveBaseTable):
    """
    Table factory for CSV tables
    """
    def __init__(self,
                name,
                col ,
                db_name = None,
                temporary = False,
                external = False,
                exists = True,
                comment = None,
                partitioned= None,
                clustered = None,
                sorted = None,
                skewed = None,
                row_format=None,
                stored=None,
                outputformat=None,
                location = None,
                delimeter=',',
                tbl_properties = None):

        super(HiveCsvTable,self).__init__(name=name,
                                      col=col,
                                      db_name=db_name,
                                      temporary=temporary,
                                      external=external,
                                      exists=exists,
                                      comment=comment,
                                      partitioned=partitioned,
                                      clustered=clustered,
                                      outputformat=outputformat,
                                      stored=sorted,
                                      skewed=skewed,
                                      row_format=row_format,
                                      location=location,
                                      sorted=sorted,
                                      tbl_properties=tbl_properties)
        self.delimeter=delimeter

    def get_table(self):
        self._base()
        self._col()
        self._partitioned()
        self._row_format()
        self._stored()
        self._location()
        self._tbl_prop()

        return self.hql

    def _row_format(self):
        if not self.row_format:
            self.hql+=(" ROW FORMAT DELIMITED FIELDS TERMINATED"
                       " BY '%s'"%self.delimeter)
        else:
             self.hql+=' ROW FORMAT %s'%self.row_format

class HiveSpatial(object):
    """
    Factory for spatial queries
    """
    def execute(self, hql):
        NotImplementedError()

    def show_tables(self):
        hql = 'show tables'
        res = self.execute(hql, True)
        if res:
            print('***' * 30)
            print('   show tables:')
            for i in res:
                print('         %s' % i[0])
            print('***' * 30)

    def add_functions(self, fce_dict, temporary=False):
        """
        :param fce_dict:
        :type fce_dict:
        :param temporary:
        :type temporary:
        :return:
        :rtype:
        """
        hql = ''
        for key, val in fce_dict.iteritems():
            if temporary:
                hql += "CREATE TEMPORARY FUNCTION %s as '%s'\n" % (key, val)
            else:
                hql += "CREATE FUNCTION %s as '%s'\n" % (key, val)
        self.execute(hql)

    def describe_table(self, table, show=False):
        hql = "DESCRIBE formatted %s" % table
        out = self.execute(hql, True)
        if show:
            for i in out:
                print(i)
        return out

    def find_table_location(self, table):

        out = self.describe_table(table)
        #print out
        if out:
            for cell in out:
                if 'Location:' in cell[0]:
                    logging.info("Location of file in hdfs:  %s" % cell[1])
                    path = cell[1].split('/')
                    #print path

                    path = '/'+'/'.join(path[3:]) #todo windows
                    logging.info("path to table {} ".format(path))
                    return path
        return None

    def esri_query(self, hsql, temporary=True):
        STfce = ''
        ST = find_ST_fnc(hsql)
        tmp = ''
        if temporary:
            tmp = 'temporary'

        for key, vals in ST.iteritems():
            STfce += "create {tmp} function {key} as '{vals}' \n"

        hql = STfce.format(**locals())
        logging.info(hql)

        hsqlexe = '%s\n%s' % (STfce, hsql)

        self.execute(hsqlexe)

    def test(self):
        hql = 'show databases'
        try:
            print('***' * 30)
            res = self.execute(hql, True)
            print("\n     Test connection (show databases;) \n       %s\n" % res)
            print('***' * 30)
            return True
        except Exception, e:
            print("     EROOR: connection can not be established:\n       %s\n" % e)
            print('***' * 30)
            return False

    def add_jar(self, jar_list, path=False):
        """
        Function for adding jars to the hive path.
        :param jar_list: list of jars
        :type jar_list: list
        :param path: if true , jar_list must incliudes path \
                 to jar, else by default jars must be in ${env:HIVE_HOME}
        :type path: bool
        :return:
        :rtype:
        """
        hql = ''
        for jar in jar_list:
            if jar:

                if not path:
                    hql += 'ADD JAR /usr/local/spatial/jar/%s ' % jar
                else:
                    hql += 'ADD JAR %s ' % jar
                logging.info(hql)
        hql += '\n'
        return hql

    def create_geom_table(self,
                          table,
                          field=None,
                          serde='org.openx.data.jsonserde.JsonSerDe',
                          outputformat=None,
                          stored=None,
                          external=False,
                          recreate=False,
                          filepath=None,
                          overwrite=None,
                          partitioned=None,
                          ):

        tbl = HiveJsonTable(name=table,
                          col=field,
                          row_format=serde,
                          stored=stored,
                          exists=recreate,
                          external=external,
                          partitioned=partitioned,
                          outputformat=outputformat
                          )

        hql= tbl.get_table()

        if recreate:
            self.drop_table(table)

        if filepath:
            self.data2table(filepath, table, overwrite)

        logging.info(hql)
        self.execute(hql)


    def data2table(self, filepath, table, overwrite, partition=False):
        """

        :param filepath: path to hdfs data
        :type filepath: string
        :param table: name of table
        :type table: string
        :param overwrite: if overwrite data in table
        :type overwrite: bool;
        :param partition: target partition as a dict of partition columns and values
        :type partition: dict;
        :return:
        :rtype:
        """

        hql = "LOAD DATA INPATH '{filepath}' "
        if overwrite:
            hql += "OVERWRITE "
        hql += "INTO TABLE {table} "

        if partition:
            pvals = ", ".join(
                ["{0}='{1}'".format(k, v) for k, v in partition.items()])
            hql += "PARTITION ({pvals})"
        hql = hql.format(**locals())
        logging.info(hql)
        self.execute(hql)

    def create_csv_table(
            self,
            filepath,
            table,
            delimiter=",",
            field=None,
            stored=None,
            outputformat=None,
            create=True,
            serde=None,
            external=False,
            overwrite=True,
            partition=None,
            tblproperties=None,
            recreate=False):
        """
        Loads a local file into Hive

        Note that the table generated in Hive uses ``STORED AS textfile``
        which isn't the most efficient serialization format. If a
        large amount of data is loaded and/or if the tables gets
        queried considerably, you may want to use this operator only to
        stage the data into a temporary table before loading it into its
        final destination using a ``HiveOperator``.
        """
        tbl=HiveCsvTable(name=table,
                          col=field,
                          row_format=serde,
                          stored=stored,
                          exists=recreate,
                          external=external,
                          outputformat=outputformat,
                          partitioned=partition,
                          delimeter=delimiter,
                          tbl_properties = tblproperties
                          )

        hql= tbl.get_table()

        if recreate:
            self.drop_table(table)

        if filepath:
            self.data2table(filepath, table, overwrite)

        logging.info(hql)
        self.execute(hql)


    def drop_table(self, name):
        self.execute('DROP TABLE IF EXISTS %s' % name)

