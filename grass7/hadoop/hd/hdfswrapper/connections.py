from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future.standard_library import install_aliases

install_aliases()
from builtins import bytes
import json
import logging
from urlparse import urlparse
from sqlalchemy import (
    Column, Integer, String, Boolean)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
# from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import synonym
from hdfswrapper import settings

Base = declarative_base()
ID_LEN = 250
# SQL_ALCHEMY_CONN = configuration.get('core', 'SQL_ALCHEMY_CONN')
# SQL_ALCHEMY_CONN ='sqlite:////home/matt/Dropbox/DIPLOMKA/sqlitedb.db'

ENCRYPTION_ON = False


# try:
#     from cryptography.fernet import Fernet
#     FERNET = Fernet(configuration.get('core', 'FERNET_KEY').encode('utf-8'))
#     ENCRYPTION_ON = True
# except:
#     pass

class InitStorage:
    def __init__(self, connection):
        self.conn = connection
        self.engine = settings.engine
        Base.metadata.create_all(self.engine)


class Connection(Base):
    """
    Placeholder to store information about different database instances
    connection information. The idea here is that scripts use references to
    database instances (conn_id) instead of hard coding hostname, logins and
    passwords when using operators or hooks.
    """
    __tablename__ = "connection"

    id = Column(Integer(), primary_key=True)
    conn_id = Column(String(ID_LEN), unique=True)
    conn_type = Column(String(500))
    host = Column(String(500))
    schema = Column(String(500))
    login = Column(String(500))
    _password = Column('password', String(5000))
    port = Column(Integer())
    is_encrypted = Column(Boolean, unique=False, default=False)
    is_extra_encrypted = Column(Boolean, unique=False, default=False)
    _extra = Column('extra', String(5000))

    def __init__(self, conn_id=None,
                 conn_type=None,
                 host=None,
                 login=None,
                 password=None,
                 schema=None,
                 port=None,
                 extra=None,
                 uri=None):

        self.conn_id = conn_id
        if uri:
            self.parse_from_uri(uri)
        else:
            self.conn_type = conn_type
            self.host = host
            self.login = login
            self.password = password
            self.schema = schema
            self.port = port
            self.extra = extra
        self.init_connection_db()

    def init_connection_db(self):
        InitStorage(self)

    def parse_from_uriparse_from_uri(self, uri):
        temp_uri = urlparse(uri)
        hostname = temp_uri.hostname or ''
        if '%2f' in hostname:
            hostname = hostname.replace('%2f', '/').replace('%2F', '/')
        conn_type = temp_uri.scheme
        if conn_type == 'postgresql':
            conn_type = 'postgres'
        self.conn_type = conn_type
        self.host = hostname
        self.schema = temp_uri.path[1:]
        self.login = temp_uri.username
        self.password = temp_uri.password
        self.port = temp_uri.port

    def get_password(self):
        if self._password and self.is_encrypted:
            if not ENCRYPTION_ON:
                raise Exception(
                    "Can't decrypt, configuration is missing")
            return FERNET.decrypt(bytes(self._password, 'utf-8')).decode()
        else:
            return self._password

    def set_password(self, value):
        if value:
            try:
                self._password = FERNET.encrypt(bytes(value, 'utf-8')).decode()
                self.is_encrypted = True
            except NameError:
                self._password = value
                self.is_encrypted = False

    @declared_attr
    def password(cls):
        return synonym('_password',
                       descriptor=property(cls.get_password, cls.set_password))

    def get_extra(self):
        if self._extra and self.is_extra_encrypted:
            if not ENCRYPTION_ON:
                raise Exception(
                    "Can't decrypt `extra`, configuration is missing")
            return FERNET.decrypt(bytes(self._extra, 'utf-8')).decode()
        else:
            return self._extra

    def set_extra(self, value):
        if value:
            try:
                self._extra = FERNET.encrypt(bytes(value, 'utf-8')).decode()
                self.is_extra_encrypted = True
            except NameError:
                self._extra = value
                self.is_extra_encrypted = False

    @declared_attr
    def extra(cls):
        return synonym('_extra',
                       descriptor=property(cls.get_extra, cls.set_extra))

    def get_hook(self):
        from  hdfswrapper import hive_hook, webhdfs_hook, hdfs_hook

        if self.conn_type == 'hive_cli':
            return hive_hook.HiveCliHook(hive_cli_conn_id=self.conn_id)
        elif self.conn_type == 'hiveserver2':
            return hive_hook.HiveServer2Hook(hiveserver2_conn_id=self.conn_id)
        elif self.conn_type == 'webhdfs':
            return webhdfs_hook.WebHDFSHook(webhdfs_conn_id=self.conn_id)
        elif self.conn_type == 'hdfs':
            print(self.conn_id)
            return hdfs_hook.HDFSHook(hdfs_conn_id=self.conn_id)

    def __repr__(self):
        return self.conn_id

    @property
    def extra_dejson(self):
        """Returns the extra property by deserializing json"""
        obj = {}
        if self.extra:
            try:
                obj = json.loads(self.extra)
            except Exception as e:
                logging.exception(e)
                logging.error(
                    "Failed parsing the json for "
                    "conn_id {}".format(self.conn_id))
        return obj
