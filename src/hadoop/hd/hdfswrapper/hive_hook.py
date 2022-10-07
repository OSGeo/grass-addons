from __future__ import print_function

import sys
import csv
import logging
import re
import subprocess

import pyhs2
from builtins import zip
from past.builtins import basestring
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport

import security_utils as utils
from base_hook import BaseHook


from hdfswrapper.hive_table import HiveSpatial


class HiveCliHook(BaseHook, HiveSpatial):
    """
    Simple wrapper around the hive CLI.

    It also supports the ``beeline``
    a lighter CLI that runs JDBC and is replacing the heavier
    traditional CLI. To enable ``beeline``, set the use_beeline param in the
    extra field of your connection as in ``{ "use_beeline": true }``

    Note that you can also set default hive CLI parameters using the
    ``hive_cli_params`` to be used in your connection as in
    ``{"hive_cli_params": "-hiveconf mapred.job.tracker=some.jobtracker:444"}``

    The extra connection parameter ``auth`` gets passed as in the ``jdbc``
    connection string as is.

    """

    def __init__(self, hive_cli_conn_id="hive_cli_default", run_as=None):
        conn = self.get_connection(hive_cli_conn_id)
        self.hive_cli_params = conn.extra_dejson.get("hive_cli_params", "")
        self.use_beeline = conn.extra_dejson.get("use_beeline", True)
        self.auth = conn.extra_dejson.get("auth", "noSasl")
        self.conn = conn
        self.run_as = run_as

    def execute(self, hql, schema=None, verbose=True):
        """
        Run an hql statement using the hive cli

        >>> hh = HiveCliHook()
        >>> result = hh.execute("USE default;")
        >>> ("OK" in result)
        True
        """

        conn = self.conn
        schema = schema or conn.schema
        if schema:
            hql = "USE {schema};\n{hql}".format(**locals())
        import tempfile
        import os

        tmp_dir = tempfile.gettempdir()
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)

        tmp_file = os.path.join(tmp_dir, "tmpfile.hql")
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

        with open(tmp_file, "a") as f:
            f.write(hql)
            f.flush()
            fname = f.name
            hive_bin = "hive"
            cmd_extra = []

            if self.use_beeline:
                hive_bin = "beeline"
                jdbc_url = "jdbc:hive2://{conn.host}:{conn.port}/{conn.schema}"
                securityConfig = None
                if securityConfig == "kerberos":  # TODO make confugration file for thiw
                    template = conn.extra_dejson.get(
                        "principal", "hive/_HOST@EXAMPLE.COM"
                    )
                    if "_HOST" in template:
                        template = utils.replace_hostname_pattern(
                            utils.get_components(template)
                        )

                    proxy_user = ""
                    if conn.extra_dejson.get("proxy_user") == "login" and conn.login:
                        proxy_user = "hive.server2.proxy.user={0}".format(conn.login)
                    elif conn.extra_dejson.get("proxy_user") == "owner" and self.run_as:
                        proxy_user = "hive.server2.proxy.user={0}".format(self.run_as)

                    jdbc_url += ";principal={template};{proxy_user}"
                elif self.auth:
                    jdbc_url += ";auth=" + self.auth

                jdbc_url = jdbc_url.format(**locals())

                cmd_extra += ["-u", jdbc_url]
                if conn.login:
                    cmd_extra += ["-n", conn.login]
                if conn.password:
                    cmd_extra += ["-p", conn.password]

            hive_cmd = [hive_bin, "-f", fname] + cmd_extra
            hive_cmd = [hive_bin, "-e", hql] + cmd_extra

            if self.hive_cli_params:
                hive_params_list = self.hive_cli_params.split()
                hive_cmd.extend(hive_params_list)
            if verbose:
                logging.info(" ".join(hive_cmd))

            logging.info("hive_cmd= %s\ntmp_dir= %s" % (hive_cmd, tmp_dir))

            sp = subprocess.Popen(
                hive_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=tmp_dir
            )
            self.sp = sp
            stdout = ""
            for line in iter(sp.stdout.readline, ""):
                stdout += line
                if verbose:
                    logging.info(line.strip())
            sp.wait()

            if sp.returncode:
                raise Exception(stdout)

            return stdout

    def show_tables(self):
        return self.execute("show tables")

    def test(self):
        out = self.show_tables()
        try:
            print("\n     Test connection (show databases;)\n        %s\n" % out)
            print("***" * 30)

            return True
        except Exception as e:
            print("      ERROR: connection can not be established:\n      %s\n" % e)
            print("***" * 30)
            return False

    def test_hql(self, hql):
        """
        Test an hql statement using the hive cli and EXPLAIN
        """
        create, insert, other = [], [], []
        for query in hql.split(";"):  # naive
            query_original = query
            query = query.lower().strip()

            if query.startswith("create table"):
                create.append(query_original)
            elif query.startswith(("set ", "add jar ", "create temporary function")):
                other.append(query_original)
            elif query.startswith("insert"):
                insert.append(query_original)
        other = ";".join(other)
        for query_set in [create, insert]:
            for query in query_set:

                query_preview = " ".join(query.split())[:50]
                logging.info("Testing HQL [{0} (...)]".format(query_preview))
                if query_set == insert:
                    query = other + "; explain " + query
                else:
                    query = "explain " + query
                try:
                    self.execute(query, verbose=False)
                except Exception as e:
                    message = e.args[0].split("\n")[-2]
                    logging.info(message)
                    error_loc = re.search("(\d+):(\d+)", message)
                    if error_loc and error_loc.group(1).isdigit():
                        l = int(error_loc.group(1))
                        begin = max(l - 2, 0)
                        end = min(l + 3, len(query.split("\n")))
                        context = "\n".join(query.split("\n")[begin:end])
                        logging.info("Context :\n {0}".format(context))
                else:
                    logging.info("SUCCESS")

    def kill(self):
        if hasattr(self, "sp"):
            if self.sp.poll() is None:
                print("Killing the Hive job")
                self.sp.kill()

    def drop_table(self, name):
        self.execute("DROP TABLE IF EXISTS %s" % name)


class HiveMetastoreHook(BaseHook):
    """
    Wrapper to interact with the Hive Metastore
    """

    def __init__(self, metastore_conn_id="metastore_default"):
        self.metastore_conn = self.get_connection(metastore_conn_id)
        self.metastore = self.get_metastore_client()

    def __getstate__(self):
        # This is for pickling to work despite the thirft hive client not
        # being pickable
        d = dict(self.__dict__)
        del d["metastore"]
        return d

    def __setstate__(self, d):
        self.__dict__.update(d)
        self.__dict__["metastore"] = self.get_metastore_client()

    def get_metastore_client(self):
        """
        Returns a Hive thrift client.
        """
        from hive_service import ThriftHive

        ms = self.metastore_conn
        transport = TSocket.TSocket(ms.host, ms.port)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        return ThriftHive.Client(protocol)

    def get_conn(self):
        return self.metastore

    def check_for_partition(self, schema, table, partition):
        """
        Checks whether a partition exists

        >>> hh = HiveMetastoreHook()
        >>> t = 'streets'
        >>> hh.check_for_partition('default', t, "ds='2015-01-01'")
        True
        """
        self.metastore._oprot.trans.open()
        partitions = self.metastore.get_partitions_by_filter(
            schema, table, partition, 1
        )
        self.metastore._oprot.trans.close()
        if partitions:
            return True
        else:
            return False

    def get_table(self, table_name, db="default"):
        """
        Get a metastore table object

        >>> hh = HiveMetastoreHook()
        >>> t = hh.get_table(db='default', table_name='streets')
        >>> t.tableName
        'static_babynames'
        >>> [col.name for col in t.sd.cols]
        ['state', 'year', 'name', 'gender', 'num']
        """
        self.metastore._oprot.trans.open()
        if db == "default" and "." in table_name:
            db, table_name = table_name.split(".")[:2]
        table = self.metastore.get_table(dbname=db, tbl_name=table_name)
        self.metastore._oprot.trans.close()
        return table

    def get_tables(self, db, pattern="*"):
        """
        Get a metastore table object
        """
        self.metastore._oprot.trans.open()
        tables = self.metastore.get_tables(db_name=db, pattern=pattern)
        objs = self.metastore.get_table_objects_by_name(db, tables)
        self.metastore._oprot.trans.close()
        return objs

    def get_databases(self, pattern="*"):
        """
        Get a metastore table object
        """
        self.metastore._oprot.trans.open()
        dbs = self.metastore.get_databases(pattern)
        self.metastore._oprot.trans.close()
        return dbs

    def get_partitions(self, schema, table_name, filter=None):
        """
        Returns a list of all partitions in a table. Works only
        for tables with less than 32767 (java short max val).
        For subpartitioned table, the number might easily exceed this.

        >>> hh = HiveMetastoreHook()
        >>> t = 'dmt30'
        >>> parts = hh.get_partitions(schema='grassdb', table_name=t)
        >>> len(parts)
        1
        >>> parts
        [{'ds': '2015-01-01'}]
        """
        self.metastore._oprot.trans.open()
        table = self.metastore.get_table(dbname=schema, tbl_name=table_name)
        if len(table.partitionKeys) == 0:
            raise Exception("The table isn't partitioned")
        else:
            if filter:
                parts = self.metastore.get_partitions_by_filter(
                    db_name=schema, tbl_name=table_name, filter=filter, max_parts=32767
                )
            else:
                parts = self.metastore.get_partitions(
                    db_name=schema, tbl_name=table_name, max_parts=32767
                )

            self.metastore._oprot.trans.close()
            pnames = [p.name for p in table.partitionKeys]
            return [dict(zip(pnames, p.values)) for p in parts]

    def max_partition(self, schema, table_name, field=None, filter=None):
        """
        Returns the maximum value for all partitions in a table. Works only
        for tables that have a single partition key. For subpartitioned
        table, we recommend using signal tables.

        >>> hh = HiveMetastoreHook()
        >>> t = 'static_babynames_partitioned'
        >>> hh.max_partition(schema='default', table_name=t)
        '2015-01-01'
        """
        parts = self.get_partitions(schema, table_name, filter)
        if not parts:
            return None
        elif len(parts[0]) == 1:
            field = list(parts[0].keys())[0]
        elif not field:
            raise Exception("Please specify the field you want the max " "value for")

        return max([p[field] for p in parts])

    def table_exists(self, table_name, db="default"):
        """
        Check if table exists

        >>> hh = HiveMetastoreHook()
        >>> hh.table_exists(db='hivedb', table_name='static_babynames')
        True
        >>> hh.table_exists(db='hivedb', table_name='does_not_exist')
        False
        """
        try:
            t = self.get_table(table_name, db)
            return True
        except Exception as e:
            return False


class HiveServer2Hook(BaseHook, HiveSpatial):
    """
    Wrapper around the pyhs2 library

    Note that the default authMechanism is NOSASL, to override it you
    can specify it in the ``extra`` of your connection in the UI as in
    ``{"authMechanism": "PLAIN"}``. Refer to the pyhs2 for more details.
    """

    def __init__(self, hiveserver2_conn_id="hiveserver2_default"):
        self.hiveserver2_conn_id = hiveserver2_conn_id

    def get_conn(self):
        db = self.get_connection(self.hiveserver2_conn_id)
        # auth_mechanism = db.extra_dejson.get('authMechanism', 'SASL')
        auth_mechanism = "PLAIN"  # TODO

        securityConfig = None
        if securityConfig == "kerberos":  # TODO make confugration file for this
            auth_mechanism = db.extra_dejson.get("authMechanism", "KERBEROS")

        return pyhs2.connect(
            host=str(db.host),
            port=int(db.port),
            authMechanism=str(auth_mechanism),
            user=str(db.login),
            password=str(db.password),
            database=str(db.schema),
        )

    def get_results(self, hql, schema="default", arraysize=1000):

        with self.get_conn() as conn:
            if isinstance(hql, basestring):
                hql = [hql]
            results = {
                "data": [],
                "header": [],
            }
            for statement in hql:
                with conn.cursor() as cur:
                    cur.execute(statement)
                    records = cur.fetchall()
                    if records:
                        results = {
                            "data": records,
                            "header": cur.getSchema(),
                        }
            return results

    def to_csv(
        self,
        hql,
        csv_filepath,
        schema="default",
        delimiter=",",
        lineterminator="\r\n",
        output_header=True,
    ):

        schema = schema or "default"
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                logging.info("Running query: " + hql)
                cur.execute(hql)
                schema = cur.getSchema()
                with open(csv_filepath, "w") as f:
                    writer = csv.writer(
                        f, delimiter=delimiter, lineterminator=lineterminator
                    )
                    if output_header:
                        writer.writerow([c["columnName"] for c in cur.getSchema()])
                    i = 0
                    while cur.hasMoreRows:
                        rows = [row for row in cur.fetchmany() if row]
                        writer.writerows(rows)
                        i += len(rows)
                        logging.info("Written {0} rows so far.".format(i))
                    logging.info("Done. Loaded a total of {0} rows.".format(i))

    def get_records(self, hql, schema="default"):
        """
        Get a set of records from a Hive query.

        >>> hh = HiveServer2Hook()
        >>> sql = "SELECT * FROM default.static_babynames LIMIT 100"
        >>> len(hh.get_records(sql))
        100
        """
        return self.get_results(hql, schema=schema)["data"]

    def get_cursor(self):
        conn = self.get_conn()
        return conn.cursor()

    def execute(self, hql, fatch=False):
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                logging.info("Running query: " + hql)
                try:
                    cur.execute(hql)

                except Exception as e:
                    print("Execute error: %s" % e)
                    return None
                if fatch:
                    return cur.fetchall()
